from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "dev-only-change-me"),
        DATABASE=os.getenv("DATABASE_PATH", str(Path(app.instance_path) / "users.sqlite3")),
    )
    if test_config:
        app.config.update(test_config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def db():
        connection = sqlite3.connect(app.config["DATABASE"])
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    with db() as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL)")

    @app.get("/")
    def index():
        return render_template("splash.html")

    @app.get("/home")
    def home():
        return render_template("index.html")

    @app.get("/about")
    def about():
        return render_template("about.html")

    @app.get("/contact")
    def contact():
        return render_template("contact.html")

    @app.get("/portfolio")
    def portfolio():
        projects = (
            {"title": "Flask Login", "description": "Autenticazione sicura con sessioni e SQLite.", "tag": "Web app"},
            {"title": "Design system", "description": "Componenti accessibili e responsive per interfacce moderne.", "tag": "UI / UX"},
            {"title": "Data dashboard", "description": "Informazioni operative organizzate in viste semplici e leggibili.", "tag": "Product"},
        )
        return render_template("portfolio.html", projects=projects)

    @app.get("/health")
    def health():
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

    @app.route("/register", methods=("GET", "POST"))
    def register():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            if not email or len(password) < 8:
                flash("Email e password di almeno 8 caratteri sono obbligatori.")
            else:
                try:
                    with db() as connection:
                        connection.execute("INSERT INTO users(email, password_hash) VALUES (?, ?)", (email, generate_password_hash(password)))
                    return redirect(url_for("login"))
                except sqlite3.IntegrityError:
                    flash("Email già registrata.")
        return render_template("register.html")

    @app.route("/login", methods=("GET", "POST"))
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            with db() as connection:
                user = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
            if user and check_password_hash(user["password_hash"], request.form.get("password", "")):
                session.clear()
                session["user_id"] = user["id"]
                return redirect(url_for("dashboard"))
            flash("Credenziali non valide.")
        return render_template("login.html")

    @app.get("/dashboard")
    def dashboard():
        if "user_id" not in session:
            return redirect(url_for("login"))
        return render_template("dashboard.html")

    @app.post("/logout")
    def logout():
        session.clear()
        flash("Disconnessione completata.", "success")
        return redirect(url_for("login"))

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")
