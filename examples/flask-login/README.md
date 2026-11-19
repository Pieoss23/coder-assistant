# Flask Login Demo

Esempio isolato per il test dell’harness. Usa SQLite, sessioni Flask e password hashate.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```

Test:

```powershell
python -m unittest discover -s tests -v
```

Impostare `FLASK_SECRET_KEY` in `.env` con un valore casuale prima di un uso reale.
