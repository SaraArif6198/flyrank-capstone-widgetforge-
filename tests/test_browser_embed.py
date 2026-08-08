"""Cross-origin browser proof. CI runs this after Docker Compose is seeded."""
import http.server
import json
import socketserver
import tempfile
import threading
import time
import unittest
from pathlib import Path
from urllib.request import Request, urlopen

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # The normal backend unit suite remains dependency-light.
    sync_playwright = None


API = "http://127.0.0.1:8000"


@unittest.skipUnless(sync_playwright, "Install requirements-dev.txt to run browser proof")
class BrowserEmbedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            with urlopen(f"{API}/health", timeout=3) as response:
                if response.status != 200:
                    raise RuntimeError("API is not healthy")
        except Exception as exc:
            raise unittest.SkipTest(f"Browser proof needs the Compose API: {exc}")
        login = Request(f"{API}/api/v1/auth/login", data=json.dumps({"email": "alice@acme.test", "password": "DemoPass123!"}).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(login, timeout=5) as response:
            token = json.load(response)["access_token"]
        widgets = Request(f"{API}/api/v1/widgets", headers={"Authorization": f"Bearer {token}"})
        with urlopen(widgets, timeout=5) as response:
            public_id = json.load(response)[0]["public_id"]
        cls.directory = tempfile.TemporaryDirectory()
        Path(cls.directory.name, "index.html").write_text(f'<!doctype html><title>Customer site</title><script src="{API}/widget.v1.js?id={public_id}"></script>', encoding="utf-8")
        handler = http.server.SimpleHTTPRequestHandler
        cls.server = socketserver.TCPServer(("127.0.0.1", 8080), lambda *args, **kwargs: handler(*args, directory=cls.directory.name, **kwargs))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.directory.cleanup()

    def test_widget_renders_and_submits_on_second_origin(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.goto("http://localhost:8080", wait_until="networkidle")
            self.assertTrue(page.locator(".wf-card").is_visible())
            page.locator('input[name="name"]').fill("Browser Lead")
            page.locator('input[name="email"]').fill("browser@example.com")
            page.locator(".wf-button").click()
            self.assertTrue(page.get_by_text("Your submission was received.").is_visible())
            browser.close()
