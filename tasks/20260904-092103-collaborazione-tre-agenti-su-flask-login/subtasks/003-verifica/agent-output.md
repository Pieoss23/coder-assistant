I've reviewed the harness code but I'm blocked from running tests and applying fixes without your approval. Here's what I found.

## Note sul sotto-task

Il PLAN del sotto-task è vuoto (nessuna attività né criteri di accettazione definiti). Non esiste un repository git, quindi non c'è un "diff" da verificare: ho revisionato lo stato corrente di `harness/core.py` e `harness/cli.py`.

## Difetti individuati

**1. `harness/core.py:66` — precedenza operatori in `test_command()`**
```python
if (ROOT / "pytest.ini").exists() or (ROOT / "pyproject.toml").exists() and (ROOT / "tests").exists():
    return "python -m pytest"
```
`and` ha precedenza su `or`, quindi la condizione è `pytest.ini OR (pyproject.toml AND tests)`. In questo progetto (pyproject.toml + `tests/` presenti, pytest **non** installato — vincolo "solo stdlib" di PROJECT_RULES), un task senza `test_command` configurato riceverebbe `python -m pytest` che fallirebbe con *No module named pytest*. Il fallback dovrebbe usare `unittest`.
Fix proposto: pytest solo se esiste `pytest.ini`; con `pyproject.toml` + `tests/` usare `python -m unittest discover -s tests -v`.

**2. `harness/core.py:45-48` — `slug()` usa la global `fifty` definita dopo la funzione**
Funziona solo per late binding; fragile e poco leggibile. Fix proposto: costante `SLUG_MAX_LENGTH = 50` prima della funzione.

**3. Minore** — `run_subtask()` non registra `event()` (a differenza di `run_task()`); `run_tests()` non gestisce eccezioni diverse da `TimeoutExpired` (es. `FileNotFoundError` sul comando). Non li toccherei senza tua indicazione.

## Cosa mi serve da te

- Approvi l'applicazione dei fix 1 e 2?
- Approvi l'esecuzione di `python -m unittest discover -s tests -v` (prima e dopo le modifiche) per popolare il `TEST-REPORT.md`?

Nessuna modifica è stata applicata finora.
