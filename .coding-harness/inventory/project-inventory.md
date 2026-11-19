# Project inventory

- File analizzati: `30`
- Generato: `2026-11-17T09:40:45.164050+01:00`

## Estensioni

- `.css`: 1
- `.example`: 1
- `.html`: 11
- `.js`: 2
- `.md`: 2
- `.py`: 7
- `.toml`: 1
- `.txt`: 1
- `[none]`: 4

## File

| Path | Tipo | Sensibilità | Dimensione | Metadati |
|---|---|---|---:|---|
| `.env` | `file` | `secret` | redacted |  |
| `.gitignore` | `file` | `public` | 64 |  |
| `examples/flask-login/.env` | `file` | `secret` | redacted |  |
| `examples/flask-login/.env.example` | `example` | `public` | 93 |  |
| `examples/flask-login/.gitignore` | `file` | `public` | 74 |  |
| `examples/flask-login/app.py` | `python` | `public` | 4299 | imports=__future__, contextlib, datetime, dotenv, flask, os, pathlib, sqlite3, werkzeug; routes=/, /about, /contact, /dashboard, /health, /home, /login, /logout, /portfolio, /register |
| `examples/flask-login/README.md` | `markdown` | `public` | 405 |  |
| `examples/flask-login/requirements.txt` | `txt` | `public` | 36 |  |
| `examples/flask-login/static/auth.js` | `javascript` | `public` | 310 |  |
| `examples/flask-login/static/splash.js` | `javascript` | `public` | 173 |  |
| `examples/flask-login/static/styles.css` | `css` | `public` | 3344 |  |
| `examples/flask-login/templates/about.html` | `html` | `public` | 297 | refs=base.html |
| `examples/flask-login/templates/auth_form.html` | `html` | `public` | 666 | refs=base.html |
| `examples/flask-login/templates/base.html` | `html` | `public` | 987 | refs=navbar.html |
| `examples/flask-login/templates/contact.html` | `html` | `public` | 320 | refs=base.html, mailto:demo@example.com |
| `examples/flask-login/templates/dashboard.html` | `html` | `public` | 410 | refs=base.html |
| `examples/flask-login/templates/index.html` | `html` | `public` | 510 | refs=base.html |
| `examples/flask-login/templates/login.html` | `html` | `public` | 369 | refs=auth_form.html |
| `examples/flask-login/templates/navbar.html` | `html` | `public` | 860 |  |
| `examples/flask-login/templates/portfolio.html` | `html` | `public` | 734 | refs=base.html |
| `examples/flask-login/templates/register.html` | `html` | `public` | 383 | refs=auth_form.html |
| `examples/flask-login/templates/splash.html` | `html` | `public` | 544 | refs=base.html |
| `examples/flask-login/tests/test_app.py` | `python` | `public` | 4757 | imports=app, datetime, pathlib, sqlite3, unittest |
| `harness/__init__.py` | `python` | `public` | 93 |  |
| `harness/cli.py` | `python` | `public` | 5047 | imports=__future__, argparse, core, inventory, json, pathlib |
| `harness/core.py` | `python` | `public` | 35584 | imports=__future__, concurrent, dataclasses, datetime, fnmatch, hashlib, json, os, pathlib, re, subprocess, sys, threading, typing, urllib, uuid, zoneinfo |
| `harness/inventory.py` | `python` | `public` | 5584 | imports=__future__, ast, datetime, hashlib, json, pathlib, re, typing |
| `pyproject.toml` | `toml` | `public` | 388 |  |
| `README.md` | `markdown` | `public` | 12097 |  |
| `tests/test_core.py` | `python` | `public` | 8041 | imports=harness, tempfile, unittest |
