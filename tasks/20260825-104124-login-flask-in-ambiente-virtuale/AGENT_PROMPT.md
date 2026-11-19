
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


Sei l'agente incaricato di questo task. Rispetta integralmente SYSTEM_PROMPT, PROJECT_RULES e memoria. Prima riepiloga il piano e le assunzioni; poi sviluppa in modo incrementale. Devi creare o aggiornare test pertinenti, eseguirli e riportare file modificati, test eseguiti, rischi e decisioni. Se una richiesta contraddice le regole, fermati e segnalalo.

## Piano del task

# Piano: Login Flask in ambiente virtuale

## Obiettivo

Creare un esempio Flask isolato con login, logout, sessione, password hashate, SQLite e configurazione tramite `.env`.

## Contesto

L’esempio serve a verificare il ciclo dell’harness su un’applicazione reale senza modificare il core dell’harness.

## Attività atomiche

- [ ] 
- [ ] Creare ambiente virtuale e dipendenze dichiarate
- [ ] Implementare registrazione, login, logout e pagina protetta
- [ ] Usare `SECRET_KEY` e configurazione dal file `.env`
- [ ] Aggiungere test Flask per flussi positivi e negativi
- [ ] Eseguire i test e salvare l’esito nel report del task

## File coinvolti

- `examples/flask-login/`

## Criteri di accettazione

- Password memorizzate solo tramite hash
- Login corretto porta alla pagina protetta
- Credenziali errate vengono rifiutate
- Logout invalida la sessione
- I test passano in ambiente virtuale

## Rischi e rollback

Esempio dimostrativo, non pronto per produzione senza CSRF, rate limiting, gestione utenti più completa e hardening della sessione.

