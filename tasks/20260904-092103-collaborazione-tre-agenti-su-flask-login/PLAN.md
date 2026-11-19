# Piano: Collaborazione tre agenti su Flask login

## Obiettivo

Verificare la collaborazione sequenziale di tre agenti con ruoli diversi sul progetto condiviso `examples/flask-login`.

## Contesto

L’applicazione è un esempio Flask con registrazione, login, logout, SQLite, `.env` e test automatici. Non introdurre dipendenze o funzionalità non necessarie alla prova.

## Attività atomiche

- [ ] 
- [ ] L’architect analizza il progetto e produce raccomandazioni senza modificare codice
- [ ] L’implementer applica una piccola miglioria UI seguendo il piano dell’architect
- [ ] Il tester-reviewer esegue la suite, verifica il diff e corregge eventuali difetti
- [ ] Ogni ruolo lascia output e test report nel proprio sotto-task
- [ ] Aggiornare memoria e decision log solo dopo revisione dello sviluppatore

## File coinvolti

- `examples/flask-login/`
- `tasks/<task>/subtasks/`

## Criteri di accettazione

- I tre ruoli usano lo stesso progetto e condividono il contesto persistente
- I passaggi avvengono in sequenza e ogni agente vede l’esito del precedente
- I test Flask restano verdi
- Nessun segreto viene incluso nei prompt o negli output
- Le modifiche estetiche sono separate dalla logica di autenticazione

## Rischi e rollback

I provider CLI potrebbero non essere installati o autenticati. In tal caso usare `AGENT_PROMPT.md` nella chat corrispondente. Se un agente modifica file fuori dal perimetro, fermare il flusso e revisionare il diff.

