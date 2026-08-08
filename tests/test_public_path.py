import unittest

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import OutboxEvent, Submission, Widget
from app.db.session import Base, SessionLocal, engine
from app.integrations.geo import GeoResult
from app.main import app
from app.services.submission import limiter, accept_submission
from app.workers.outbox import process_pending_events
from scripts.seed_demo import seed


class WorkingGeo:
    name = "backup"
    def lookup(self, ip): return GeoResult(country="Pakistan", city="Karachi", provider=self.name)


class FailingGeo:
    name = "primary"
    def lookup(self, ip): raise RuntimeError("provider down")


class FailingNotifier:
    def send_submission_accepted(self, submission, event_id): raise RuntimeError("down")


class PublicPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine); seed()
        cls.client = TestClient(app)

    def setUp(self):
        limiter.requests.clear()
        with SessionLocal() as db:
            self.widget = db.scalar(select(Widget).where(Widget.widget_type == "signup"))

    def payload(self, key="00000000-0000-0000-0000-000000000010"):
        return {"widget_id": self.widget.public_id, "fields": {"email": "lead@example.com", "name": "Lead"}, "website": ""}, {"Origin": "http://localhost:8080", "Idempotency-Key": key}

    def test_config_cors_cache_and_submission_replay(self):
        config = self.client.get(f"/public/v1/widgets/{self.widget.public_id}/config", headers={"Origin": "http://localhost:8080"})
        self.assertEqual(config.status_code, 200); self.assertIn("max-age=300", config.headers["cache-control"])
        self.assertEqual(config.headers["access-control-allow-origin"], "http://localhost:8080")
        bundle = self.client.get("/widget.v1.js")
        self.assertEqual(bundle.status_code, 200)
        self.assertEqual(bundle.headers["cache-control"], "public, max-age=31536000, immutable")
        self.assertEqual(self.client.get(f"/public/v1/widgets/{self.widget.public_id}/config", headers={"If-None-Match": config.headers["etag"]}).status_code, 304)
        payload, headers = self.payload()
        first = self.client.post("/public/v1/submissions", json=payload, headers=headers)
        replay = self.client.post("/public/v1/submissions", json=payload, headers=headers)
        self.assertEqual(first.status_code, 201); self.assertFalse(first.json()["replayed"])
        self.assertEqual(replay.json()["id"], first.json()["id"]); self.assertTrue(replay.json()["replayed"])

    def test_oversized_submission_returns_413(self):
        payload, headers = self.payload("00000000-0000-0000-0000-000000000050")
        payload["fields"]["name"] = "x" * 20_000
        response = self.client.post("/public/v1/submissions", json=payload, headers=headers)
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["error"]["code"], "payload_too_large")

    def test_preflight_and_both_geo_providers_down(self):
        preflight = self.client.options("/public/v1/submissions", headers={"Origin": "http://localhost:8080", "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "content-type,idempotency-key"})
        self.assertEqual(preflight.status_code, 200)
        with SessionLocal() as db:
            submission, _ = accept_submission(db, public_id=self.widget.public_id, fields={"email": "nogeo@example.com", "name": "No Geo"}, honeypot="", idempotency_key="00000000-0000-0000-0000-000000000040", ip="127.0.0.1", origin=None, geo_providers=[FailingGeo(), FailingGeo()])
            self.assertIsNone(submission.geo_country)
            self.assertIsNone(submission.geo_provider)

    def test_honeypot_validation_and_rate_limit(self):
        payload, headers = self.payload("00000000-0000-0000-0000-000000000020")
        payload["website"] = "bot"
        with SessionLocal() as db:
            before = len(list(db.scalars(select(Submission))))
        self.assertEqual(self.client.post("/public/v1/submissions", json=payload, headers=headers).status_code, 201)
        with SessionLocal() as db:
            self.assertEqual(len(list(db.scalars(select(Submission)))), before)
        limiter.requests.clear(); payload["website"] = ""; payload["fields"] = {"unknown": "x"}
        self.assertEqual(self.client.post("/public/v1/submissions", json=payload, headers=headers).status_code, 422)
        limiter.requests.clear(); payload["fields"] = {"email": "fresh@example.com", "name": "Fresh"}
        for index in range(5):
            headers["Idempotency-Key"] = f"00000000-0000-0000-0000-{index:012d}"
            self.assertEqual(self.client.post("/public/v1/submissions", json=payload, headers=headers).status_code, 201)
        headers["Idempotency-Key"] = "00000000-0000-0000-0000-999999999999"
        self.assertEqual(self.client.post("/public/v1/submissions", json=payload, headers=headers).status_code, 429)

    def test_geo_fallback_and_failed_notification_preserve_submission(self):
        with SessionLocal() as db:
            submission, replayed = accept_submission(db, public_id=self.widget.public_id, fields={"email": "geo@example.com", "name": "Geo"}, honeypot="", idempotency_key="00000000-0000-0000-0000-000000000030", ip="127.0.0.1", origin=None, geo_providers=[FailingGeo(), WorkingGeo()])
            self.assertFalse(replayed); self.assertEqual(submission.geo_provider, "backup")
            self.assertGreaterEqual(process_pending_events(db, FailingNotifier()), 1)
            event = db.scalar(select(OutboxEvent).where(OutboxEvent.submission_id == submission.id))
            self.assertEqual(event.status, "pending"); self.assertEqual(event.attempt_count, 1)


if __name__ == "__main__": unittest.main()
