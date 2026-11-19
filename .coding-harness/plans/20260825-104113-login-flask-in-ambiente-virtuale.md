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

