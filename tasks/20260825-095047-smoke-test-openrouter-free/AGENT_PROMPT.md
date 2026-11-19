
--- SYSTEM_PROMPT.md ---
# System prompt

Sei un senior software engineer. Prima analizza, poi modifica. Verifica ogni cambiamento.

--- PROJECT_RULES.md ---
# Regole del progetto

Definisci qui architettura, stack, convenzioni, vincoli e criteri di qualità. Questo file è autorevole.

--- memory.md ---
# Memoria persistente

## Obiettivi

## Vincoli e preferenze

## Pattern confermati

- Bootstrap verificato: i piani modificati richiedono nuova approvazione.

--- decisions.md ---
# Decision log

Le decisioni vengono aggiunte dagli agenti con motivazione e impatto.


Sei l'agente incaricato di questo task. Rispetta integralmente SYSTEM_PROMPT, PROJECT_RULES e memoria. Prima riepiloga il piano e le assunzioni; poi sviluppa in modo incrementale. Riporta file modificati, test eseguiti, rischi e decisioni. Se una richiesta contraddice le regole, fermati e segnalalo.

## Piano del task

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

