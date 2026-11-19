import sqlite3
import unittest
from datetime import datetime, timezone
from pathlib import Path

from app import create_app


class LoginTests(unittest.TestCase):
    def setUp(self):
        test_root = Path(__file__).parents[1] / ".test-tmp"
        test_root.mkdir(exist_ok=True)
        self.database = test_root / "users.sqlite3"
        self.app = create_app({"TESTING": True, "SECRET_KEY": "test-secret", "DATABASE": str(self.database)})
        with sqlite3.connect(self.database) as connection:
            connection.execute("DELETE FROM users")
        self.client = self.app.test_client()

    def tearDown(self):
        with sqlite3.connect(self.database) as connection:
            connection.execute("DELETE FROM users")

    def test_register_login_and_logout(self):
        response = self.client.post("/register", data={"email": "user@example.com", "password": "password123"})
        self.assertEqual(response.status_code, 302)
        response = self.client.post("/login", data={"email": "user@example.com", "password": "password123"})
        self.assertEqual(response.status_code, 302)
        self.assertIn("Dashboard privata", self.client.get("/dashboard").text)
        self.client.post("/logout")
        self.assertEqual(self.client.get("/dashboard").status_code, 302)

    def test_invalid_password_is_rejected(self):
        self.client.post("/register", data={"email": "user@example.com", "password": "password123"})
        response = self.client.post("/login", data={"email": "user@example.com", "password": "wrongpass"})
        self.assertEqual(response.status_code, 200)
        self.assertIn("Credenziali non valide.", response.text)
        self.assertIn('aria-live="polite"', response.text)
        with self.client.session_transaction() as stored_session:
            self.assertNotIn("user_id", stored_session)

    def test_auth_pages_expose_ui_feedback(self):
        login = self.client.get("/login")
        self.assertEqual(login.status_code, 200)
        self.assertIn('data-auth-form', login.text)
        self.assertIn("Accesso in corso", login.text)
        self.assertIn('required', login.text)
        self.assertIn("styles.css", login.text)
        self.assertIn("auth.js", login.text)

    def test_splash_and_main_pages_expose_shared_navigation(self):
        splash = self.client.get("/")
        self.assertEqual(splash.status_code, 200)
        self.assertIn('data-splash', splash.text)
        self.assertIn("splash.js", splash.text)
        self.assertIn("/home", splash.text)

        pages = (("/home", "Home", "home"), ("/about", "About", "about"), ("/contact", "Contact", "contact"), ("/portfolio", "Portfolio", "portfolio"))
        for path, label, endpoint in pages:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn('<nav class="site-nav"', response.text)
                for target, target_label, _ in pages:
                    self.assertIn(f'href="{target}"', response.text)
                    self.assertIn(f">{target_label}</a>", response.text)
                self.assertIn(f'href="{path}" aria-current="page">{label}</a>', response.text)
                self.assertEqual(response.text.count('class="site-nav"'), 1)

    def test_portfolio_is_public_and_renders_projects(self):
        response = self.client.get("/portfolio")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Portfolio", response.text)
        self.assertIn("Flask Login", response.text)
        self.assertIn("Parliamone", response.text)

    def test_navigation_has_responsive_layout_styles(self):
        stylesheet = (Path(__file__).parents[1] / "static" / "styles.css").read_text(encoding="utf-8")
        self.assertIn("@media (max-width: 30rem)", stylesheet)
        self.assertIn("flex-direction: column", stylesheet)

    def test_health_returns_stable_json_with_utc_timestamp(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "application/json")
        self.assertEqual(set(response.json), {"status", "timestamp"})
        self.assertEqual(response.json["status"], "ok")
        timestamp = datetime.fromisoformat(response.json["timestamp"])
        self.assertEqual(timestamp.tzinfo, timezone.utc)

    def test_logout_shows_success_feedback(self):
        response = self.client.post("/logout", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Disconnessione completata.", response.text)
        self.assertIn("flash-success", response.text)


if __name__ == "__main__":
    unittest.main()
