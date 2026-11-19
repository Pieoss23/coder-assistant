# \# Piano: Refactor totale Flask Login con Portfolio e Splash

# 

# \## Obiettivo

# 

# Rifattorizzare completamente l’interfaccia dell’app Flask Login Demo.

# 

# Aggiungere:

# 

# \- una nuova pagina Portfolio;

# \- una splash screen iniziale;

# \- animazione di caricamento;

# \- navbar coerente tra tutte le pagine;

# \- layout responsive;

# \- mantenimento delle funzionalità login esistenti.

# 

# \## Attività atomiche

# 

# \- \[ ] Analizzare struttura attuale e proporre architettura UI

# \- \[ ] Rifattorizzare layout, navbar e stile globale

# \- \[ ] Creare pagina Portfolio

# \- \[ ] Creare splash screen con caricamento

# \- \[ ] Aggiornare routing Flask

# \- \[ ] Aggiornare o creare i template

# \- \[ ] Aggiornare CSS e JavaScript

# \- \[ ] Creare test per le nuove route

# \- \[ ] Eseguire tutti i test

# \- \[ ] Effettuare revisione finale

# 

# \## File coinvolti

# 

# \- `examples/flask-login/app.py`

# \- `examples/flask-login/templates/`

# \- `examples/flask-login/static/`

# \- `examples/flask-login/tests/`

# 

# \## Criteri di accettazione

# 

# \- La home mostra inizialmente la splash screen.

# \- La splash screen termina automaticamente e mostra la home.

# \- La navbar contiene Home, About, Contact e Portfolio.

# \- La pagina Portfolio è raggiungibile dalla navbar.

# \- Le pagine funzionano anche da utenti non autenticati, dove previsto.

# \- Login, logout e registrazione continuano a funzionare.

# \- I test esistenti continuano a passare.

# \- Sono presenti test per Portfolio e splash.

# \- L’interfaccia è responsive su desktop e mobile.

# 

# \## Rischi e rollback

# 

# \- Conservare il comportamento delle route esistenti.

# \- Non eliminare dati SQLite.

# \- In caso di problemi, ripristinare i template precedenti mantenendo i test.

