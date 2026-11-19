# Error catalog

Catalogo persistente degli errori incontrati durante piani, agenti, test, lock e terminali.

Ogni errore operativo viene registrato anche in `errors.jsonl` con fingerprint, fase, task, provider e sessione. Quando l'errore viene risolto, aggiornare la voce con causa, soluzione, workaround e test di regressione.

## Stati

- `open`: non ancora risolto o da riprodurre.
- `mitigated`: presente un workaround, ma la causa non è stata eliminata.
- `resolved`: fix verificato da un test o da una riproduzione documentata.

## 84ecaa8437d33e7e — RuntimeError

- Data: 2026-09-04T17:18:02.755140+02:00
- Fase: `tests-failed`
- Task: `C:\Progetti\SVILUPPO\coder-assistant\tasks\20260904-171716-refactor-flask-login-portfolio-splash\subtasks\001-analisi-architetturale-ui`
- Provider: `openrouter`
- Messaggio: suite fallita con return code 1
- Stato: open

## 84ecaa8437d33e7e — RuntimeError

- Data: 2026-09-04T17:22:21.014019+02:00
- Fase: `tests-failed`
- Task: `C:\Progetti\SVILUPPO\coder-assistant\tasks\20260904-171716-refactor-flask-login-portfolio-splash\subtasks\002-implementazione-refactor-completo`
- Provider: `codex`
- Messaggio: suite fallita con return code 1
- Stato: open
