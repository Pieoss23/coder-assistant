# Memoria persistente del progetto

Questa memoria contiene fatti, preferenze e conoscenze confermate. Non è un diario completo: gli eventi dettagliati restano nei task. Ogni voce deve essere breve, verificabile e utile a un agente futuro.

## Obiettivi correnti

- Costruire un ambiente di sviluppo orchestrato da agenti, utilizzabile sia dalle chat native sia dal terminale.
- Rendere ogni attività riproducibile tramite piano Markdown, task isolato, test e report.
- Permettere di cambiare provider senza perdere contesto, decisioni e apprendimento del progetto.
- Sperimentare tool filesystem/terminal per rendere operativi anche modelli API senza strumenti nativi.

## Preferenze dello sviluppatore

- Lo sviluppatore decide architettura, stack, convenzioni e vincoli tramite `PROJECT_RULES.md`.
- La chat dell’agente resta l’interfaccia preferita; il terminale è un’accelerazione opzionale.
- I piani devono poter essere modificati e verificati prima dello sviluppo.
- L’agente deve creare ed eseguire test e lasciare sempre l’esito nella cartella del task.
- È importante conservare memoria e decisioni aggiornate dopo correzioni successive.

## Stato tecnico confermato

- Harness implementato in Python con CLI e sola libreria standard per il core.
- Provider attivi: OpenRouter, Claude CLI, Codex CLI e Copilot CLI configurabile.
- OpenRouter è stato provato con `openrouter/free` e ha risposto correttamente.
- La chiave OpenRouter viene caricata da `.env` senza essere stampata nei log.
- La modalità OpenRouter API attuale produce testo ma non modifica autonomamente il repository.
- Il router free può essere lento o soggetto a rate limit; non va assunto come provider sempre disponibile.
- Esempio Flask in `examples/flask-login` con ambiente virtuale, `.env`, SQLite, login/logout e test: verificato con 2 test superati.

## Pattern confermati

- Un piano alterato dopo l’approvazione deve essere approvato nuovamente tramite hash.
- Ogni task contiene prompt, piano, stato, eventi, output agente e report test.
- I sotto-task vivono in `tasks/<task>/subtasks/` e possono essere eseguiti in parallelo.
- Il test command può essere specifico per task per supportare ambienti virtuali diversi.

## Questioni aperte

- Definire un protocollo sicuro per tool filesystem e terminale del provider OpenRouter.
- Decidere sandbox, permessi, approvazione dei comandi e gestione dei conflitti tra sotto-task.
- Valutare integrazione con chat native senza duplicare le loro funzionalità.
