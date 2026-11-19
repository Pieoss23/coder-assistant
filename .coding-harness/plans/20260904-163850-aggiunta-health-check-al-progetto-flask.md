# Piano: Aggiunta health check al progetto Flask

## Obiettivo

Aggiungere all’app Flask un endpoint `GET /health` che restituisca JSON con stato applicativo e timestamp UTC.

## Contesto

Il progetto di test è `examples/flask-login`. La nuova funzione non deve modificare login, logout, sessione, database o interfaccia esistente.

## Attività atomiche

- [ ] 
- [ ] Implementare `GET /health`
- [ ] Restituire status HTTP 200 e JSON stabile
- [ ] Aggiungere test automatico per risposta e contenuto
- [ ] Eseguire la suite Flask nell’ambiente virtuale
- [ ] Verificare audit e report del task

## File coinvolti

- `examples/flask-login/app.py`
- `examples/flask-login/tests/test_app.py`

## Criteri di accettazione

- `GET /health` restituisce HTTP 200
- Il body contiene `status: ok`
- Il body contiene un timestamp valido
- I test esistenti restano verdi
- Nessuna credenziale viene restituita

## Rischi e rollback

Funzione diagnostica senza accesso a dati utente. In caso di problemi rimuovere endpoint e test aggiunti.

