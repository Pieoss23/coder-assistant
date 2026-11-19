# Contributing

## Workflow

1. Create or update a plan.
2. Declare complexity, risk and involved files.
3. Generate and review the sandbox manifest.
4. Keep changes within the approved scope.
5. Add or update tests.
6. Run both harness and example test suites.
7. Update decisions, memory or limitations when the change affects project policy.

## Local checks

```powershell
python -m unittest discover -s tests -v
Push-Location examples\flask-login
try { .\.venv\Scripts\python.exe -m unittest discover -s tests -v }
finally { Pop-Location }
```

Never commit `.env`, credentials, virtual environments, generated caches or local provider paths.
