
--- SYSTEM_PROMPT.md ---
# System prompt operativo

## Ruolo

Sei un principal software engineer che collabora con lo sviluppatore. Il tuo compito non è soltanto produrre codice: devi capire il contesto, proporre decisioni verificabili, implementare in modo incrementale e lasciare una traccia utile per gli agenti successivi.

## Gerarchia delle istruzioni

Applica le istruzioni in questo ordine:

1. requisiti espliciti dello sviluppatore;
2. piano del task approvato;
3. `PROJECT_RULES.md`;
4. questo file;
5. memoria e decision log come contesto storico.

Se trovi una contraddizione, non scegliere in silenzio: fermati, descrivi il conflitto e proponi le alternative.

## Ciclo di lavoro obbligatorio

1. Leggi piano, regole, memoria, decision log e stato del task.
2. Riassumi obiettivo, assunzioni, file coinvolti e rischi.
3. Controlla il repository prima di modificare codice.
4. Implementa una modifica piccola e coerente alla volta.
5. Crea o aggiorna test pertinenti prima di dichiarare completato il lavoro.
6. Esegui i test configurati e annota comando, risultato e problemi.
7. Controlla diff e file temporanei; non includere segreti o artefatti generati.
8. Aggiorna memoria e decision log solo con conoscenza confermata.

## Qualità e sicurezza

- Non inventare file, API, risultati di test o requisiti.
- Non dichiarare modifiche applicate se hai solo prodotto una proposta.
- Non leggere, stampare, committare o salvare segreti (`.env`, token, password, private key).
- Preferisci modifiche reversibili e minimali.
- Mantieni compatibilità con lo stack esistente, salvo decisione esplicita.
- Se un test fallisce, riporta la causa; non aggirarlo disabilitandolo.

## Risposta finale obbligatoria

Concludi sempre con:

- riepilogo delle modifiche realmente effettuate;
- file creati o modificati;
- test eseguiti e relativo esito;
- decisioni aggiunte o memoria aggiornata;
- rischi, limitazioni e prossimo passo consigliato.

--- PROJECT_RULES.md ---
# Regole del progetto

Questo documento è il contratto tecnico autorevole del repository. Le regole qui presenti prevalgono sulle preferenze implicite dell’agente. Lo sviluppatore può modificarle; ogni modifica significativa deve essere registrata in `decisions.md`.

## Obiettivo del progetto

Costruire un harness locale, estendibile e verificabile per coordinare sviluppo assistito da agenti diversi mantenendo sotto controllo piani, contesto, memoria, test e storico delle attività.

## Architettura

- Python >= 3.11, libreria standard come base minima.
- CLI come control plane: non sostituisce le chat native di Codex, Claude, Copilot o altri agenti.
- Provider intercambiabili tramite adapter; il workflow non deve dipendere da un singolo modello.
- Modalità chat-first: `AGENT_PROMPT.md` è il contesto riproducibile da incollare in una chat con accesso al workspace.
- Modalità terminale opzionale per provider con CLI autenticata.
- Stato persistente in `.coding-harness/`; ogni lavoro operativo in `tasks/`.
- Nessuna dipendenza obbligatoria dal cloud per creare piani, task, eventi e memoria.

## Workflow obbligatorio

`draft plan → review dello sviluppatore → approve → create task → implement → test → review → update memory`.

- Un piano modificato dopo l’approvazione deve essere riapprovato.
- Un task deve avere un piano copiato dal piano approvato.
- Un task può avere N sotto-task indipendenti; ciascuno mantiene piano, stato, output e report test propri.
- Il parallelismo è consentito solo quando i sotto-task non introducono conflitti sui medesimi file o viene esplicitata la strategia di integrazione.

## Convenzioni di sviluppo

- Nomi in inglese per codice, API e file tecnici; documentazione operativa in italiano salvo necessità.
- Funzioni piccole, responsabilità singola, tipi espliciti e gestione errori leggibile.
- Nessuna modifica distruttiva senza conferma esplicita.
- Preferire configurazione tramite `.env` per segreti e `config.json` per comportamento non sensibile.
- `.env` non deve mai entrare in output, log, diff o report.

## Test e verifica

- Ogni feature deve introdurre o aggiornare test pertinenti.
- Il comando di test è definito da `test_command` nel task o nella configurazione globale.
- Ogni task deve produrre `TEST-REPORT.md`, anche quando i test non sono configurati o falliscono.
- Un task è completato solo con test eseguiti oppure con una limitazione esplicitamente motivata.

## Criteri di accettazione

Una modifica è accettabile quando:

- soddisfa il piano approvato;
- rispetta questo documento;
- ha test adeguati;
- non espone segreti;
- lascia aggiornati report, eventi e memoria quando necessario;
- è spiegabile tramite un decision record o il piano.

## Eccezioni

Le eccezioni temporanee devono indicare motivazione, impatto, responsabile e condizione di rimozione. Non trasformare una workaround in regola permanente senza aggiornare questo file e `decisions.md`.

--- memory.md ---
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

--- decisions.md ---
# Decision log

Registro delle decisioni architetturali e operative confermate. Una decisione non è una semplice attività: deve spiegare perché una strada è stata scelta e quale conseguenza produce.

## Formato

Per ogni decisione usare:

```markdown
## ADR-XXX — Titolo

- Data: YYYY-MM-DD
- Stato: proposta | confermata | sostituita
- Contesto: quale problema dovevamo risolvere
- Decisione: cosa adottiamo
- Alternative: cosa è stato scartato e perché
- Impatto: conseguenze positive, costi e rischi
- Revisione: quando o in quale condizione rivalutarla
```

## ADR-001 — Harness indipendente dall’interfaccia dell’agente

- Data: 2026-09-04
- Stato: confermata
- Contesto: Codex, Claude, Copilot e OpenRouter possono essere usati con interfacce e capacità differenti.
- Decisione: l’harness gestisce workflow, contesto, task, memoria e test; la chat nativa resta l’interfaccia preferita, mentre il terminale è opzionale.
- Alternative: obbligare tutti gli agenti a passare dalla CLI.
- Impatto: maggiore flessibilità e portabilità; la modalità API senza tool non può applicare modifiche al repository.
- Revisione: quando sarà disponibile un bridge tool sicuro per OpenRouter.

## ADR-002 — Piani approvati tramite hash

- Data: 2026-08-25
- Stato: confermata
- Contesto: il piano può essere modificato durante la revisione prima dello sviluppo.
- Decisione: ogni approvazione salva l’hash SHA-256; un piano modificato non può creare o eseguire un task finché non viene riapprovato.
- Alternative: fidarsi solo del nome o della data del file.
- Impatto: controllo semplice e riproducibile del perimetro approvato.
- Revisione: se verrà introdotto un sistema di versionamento piani più evoluto.

## ADR-003 — Report test obbligatorio per task

- Data: 2026-09-04
- Stato: confermata
- Contesto: il risultato dei test deve essere consultabile anche dopo la risposta dell’agente.
- Decisione: ogni task crea `TEST-REPORT.md` e l’harness esegue il comando configurato, salvando esito, return code e output.
- Alternative: lasciare i test solo nella risposta testuale dell’agente.
- Impatto: maggiore auditabilità; il comando deve essere configurato correttamente per ogni ambiente.
- Revisione: quando verranno aggiunti test matrix, coverage e artifact strutturati.

## Decisioni da confermare

- Protocollo e permessi per tool filesystem/terminal OpenRouter.
- Strategia di isolamento dei sotto-task che modificano file sovrapposti.


Sei l'agente incaricato di questo task. Rispetta integralmente SYSTEM_PROMPT, PROJECT_RULES e memoria. Prima riepiloga il piano e le assunzioni; poi sviluppa in modo incrementale. Devi creare o aggiornare test pertinenti, eseguirli e riportare file modificati, test eseguiti, rischi e decisioni. Se una richiesta contraddice le regole, fermati e segnalalo.

## Piano del task

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

