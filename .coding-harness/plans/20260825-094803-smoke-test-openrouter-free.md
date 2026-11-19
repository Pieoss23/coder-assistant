# Piano: Smoke test OpenRouter free

## Obiettivo

Verificare il ciclo completo dell’harness usando OpenRouter con il router gratuito.

## Contesto

Il progetto usa provider intercambiabili. La chiave viene caricata dal file `.env` e non deve essere scritta nei log.

## Attività atomiche

- [x] Caricare `OPENROUTER_API_KEY` da `.env`
- [x] Inviare una richiesta tramite `openrouter/free`
- [ ] Eseguire un task tramite il workflow approvato
- [ ] Salvare risposta ed eventi del task

## File coinvolti

- `.coding-harness/config.json`
- `harness/core.py`

## Criteri di accettazione

- Il provider risponde senza esporre la chiave
- Il task viene creato solo da piano approvato
- La risposta viene salvata in `agent-output.md`
- Gli eventi del task vengono registrati in `events.jsonl`

## Rischi e rollback

Il modello free può essere soggetto a rate limit o indisponibilità temporanea. In caso di errore si può cambiare provider senza modificare il piano.

