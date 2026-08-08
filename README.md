# WidgetForge API

Implementation of the parent capstone documentation. Phase 0–1 is complete: FastAPI/PostgreSQL foundation, JWT owner authentication, deterministic demo data, tenant-isolated widget CRUD, generated embed snippets, and repeatable owner-path tests.

## Local development

```powershell
Copy-Item .env.example .env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/seed_demo.py
uvicorn app.main:app --reload
```

For the intended PostgreSQL path use `docker compose up --build`, then run `docker compose exec api python scripts/seed_demo.py`. PostgreSQL is intentionally available only to containers on the Compose network, so it cannot conflict with another local service on port 5432.

Demo users: `alice@acme.test` and `bob@beta.test`; password: `DemoPass123!`.

## Current endpoints

- `GET /health`
- `POST /api/v1/auth/login`
- `POST/GET /api/v1/widgets`
- `GET/PATCH/DELETE /api/v1/widgets/{id}`
- `GET /api/v1/widgets/{id}/embed`
- `GET /widget.v1.js`
- `GET /public/v1/widgets/{public_id}/config`
- `POST /public/v1/submissions`
- `GET /api/v1/submissions`
- `GET /api/v1/dashboard/summary`

## Verify Phase 1

```powershell
python -m unittest discover -s tests
```

See [DEMO.md](DEMO.md) for evaluator commands and the six-minute walkthrough.

The core capstone implementation is complete: public config delivery, explicit CORS, body-size guard, honeypot, per-IP/widget in-memory rate-limit adapter, idempotent submission persistence, deterministic geo-provider fallback, a durable outbox notification worker, owner dashboard APIs, and automated proof.

## Live proof

The following screenshots capture the browser-facing installation flow. Token-bearing screenshots are deliberately excluded from version control.

| Evidence | Proof |
|---|---|
| Widget configuration API | The authenticated owner can retrieve a configured widget and its opaque public ID. |
| Cross-origin delivery | The embeddable widget loads on a customer page served from a different origin. |
| Visitor interaction | The configured email/name form renders and accepts input. |
| Successful capture | The visitor receives confirmation after the submission API accepts the lead. |

<p align="center">
  <img src="docs/screenshots/widget-api-response.png" alt="Widget configuration API response" width="700">
</p>

<p align="center">
  <img src="docs/screenshots/cross-origin-widget-loaded.png" alt="Widget rendered on a second-origin customer page" width="700">
</p>

<p align="center">
  <img src="docs/screenshots/submission-success.png" alt="Successful embeddable widget submission" width="700">
</p>

`python scripts/process_outbox.py` processes durable notification events with bounded retries. Geo fallback and outbox worker tests are now included; dashboard work remains.
