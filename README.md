# Coding Harness

Middleware locale per coordinare attività di sviluppo assistite da agenti AI in modo pianificato, delimitato e verificabile.

> Stato: **prototipo avanzato / pre-alpha**. Il progetto è adatto a sperimentazione e sviluppo locale supervisionato; non è ancora una sandbox OS completa né un sistema production-ready.

## Perché esiste

Un agente che riceve soltanto “sistema questa applicazione” può modificare file non richiesti, correggere problemi fuori ambito, esporre dati sensibili o lasciare risultati difficili da verificare.

Coding Harness trasforma l’attività in un task con:

- piano Markdown modificabile e approvabile;
- complessità e workflow dichiarati;
- inventory deterministico del progetto;
- manifest dei file autorizzati;
- ruoli, provider e permessi espliciti;
- output, test, errori e audit persistenti;
- memoria e decisioni riutilizzabili;
- pipeline eseguibile con un solo comando e gate umano.

Il principio centrale è:

```text
obiettivo approvato
    → perimetro deterministico
    → agente con permessi limitati
    → diff e test
    → risultato verificabile
```

## Funzionalità

### Pianificazione e controllo

- piani di sviluppo in Markdown;
- approvazione tramite SHA-256;
- obbligo di dichiarare la complessità `C0–C5`;
- manifest sandbox generato da piano e inventory;
- blocco dell’esecuzione con manifest non approvato o modificato;
- sotto-task con ruoli, provider, dipendenze e path assegnati.

### Inventory locale a token zero

Il progetto viene analizzato localmente, senza inviare la struttura al modello:

- directory e file;
- estensioni, dimensioni e hash dei file non sensibili;
- file sensibili e segreti;
- import Python;
- route Flask;
- riferimenti tra template;
- test presenti.

```powershell
python -m harness.cli inventory
```

Output:

```text
.coding-harness/inventory/project-inventory.json
.coding-harness/inventory/project-inventory.md
```

I file classificati come segreti non vengono letti né esportati nel dossier.

### Sandbox logica

Il manifest descrive il perimetro del task:

```json
{
  "read": ["examples/flask-login/templates/base.html"],
  "write": ["examples/flask-login/static/styles.css"],
  "create": ["examples/flask-login/templates/portfolio.html"],
  "deny": [".env", ".coding-harness/*"],
  "commands": ["python -m unittest"],
  "network": false
}
```

Il manifest distingue i file leggibili, modificabili e creabili. È una barriera di policy e viene verificato contro il diff finale. La sandbox preventiva a livello di sistema operativo, con isolamento filesystem/processi/rete, è ancora una funzionalità futura.

È disponibile anche la preparazione esplicita di un Git worktree isolato:

```powershell
python -m harness.cli workspace create tasks/<task>
python -m harness.cli workspace status tasks/<task>
python -m harness.cli workspace remove tasks/<task>
```

Il worktree è una copia Git separata e reversibile; questa prima versione non lo attiva automaticamente per i task esistenti. Il collegamento alla pipeline e l’integrazione controllata nel branch principale sono il passaggio successivo.

### Provider

Gli adapter possono utilizzare:

- OpenRouter via API;
- Codex CLI;
- Claude CLI;
- Copilot CLI;
- altri provider compatibili da aggiungere.

Il provider può cambiare per task o sotto-task. OpenRouter è principalmente text-only: senza tool autorizzati può analizzare e proporre codice, ma non applicarlo direttamente alla repository.

## Quickstart

Requisiti:

- Python 3.11 o superiore;
- un provider configurato, se si vuole eseguire un agente reale;
- PowerShell su Windows oppure una shell supportata su altri sistemi.

```powershell
git clone https://github.com/<utente>/harness-studio.git
cd harness-studio
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m harness.cli init
```

Se PowerShell blocca gli script di attivazione, usare direttamente l’interprete:

```powershell
.\.venv\Scripts\python.exe -m harness.cli init
```

Configurare le chiavi solamente in `.env`, mai in `config.json`:

```text
OPENROUTER_API_KEY=...
```

È disponibile un modello in [`.env.example`](.env.example). Per impostazioni dipendenti dalla macchina usare `.coding-harness/config.local.json`, ignorato da Git; il file [`config.local.json.example`](.coding-harness/config.local.json.example) mostra la struttura.

## Creare ed eseguire un task

Creare il piano:

```powershell
python -m harness.cli plan create "Aggiunta pagina Portfolio"
```

Compilare almeno:

```markdown
## Valutazione del task

- Complessità: C2
- Workflow proposto: single-agent-review-optional
- Motivazione: nuova funzione su template, routing e test
- Rischio: low

## File coinvolti

- `examples/flask-login/app.py`
- `examples/flask-login/templates/`
- `examples/flask-login/static/`
- `examples/flask-login/tests/`
```

Approvare il piano:

```powershell
python -m harness.cli plan approve .coding-harness/plans/<piano>.md
```

## Pipeline a comando unico

```powershell
python -m harness.cli task pipeline `
  .coding-harness/plans/<piano>.md `
  "Aggiunta pagina Portfolio" `
  --provider codex `
  --working-directory examples/flask-login `
  --test-command ".venv\Scripts\python.exe -m unittest discover -s tests -v"
```

La pipeline esegue:

```text
start task
  → genera inventory/manifest
  → pausa per la revisione del manifest
  → approva il manifest
  → avvia l’agente
  → valida i file modificati
  → esegue i test
  → produce audit, handoff e report
```

La pausa è intenzionale: il comando riduce il lavoro manuale, ma non elimina l’approvazione dello sviluppatore. `CTRL+C` lascia il manifest in stato `draft`.

Per eseguire il task in un worktree separato:

```powershell
python -m harness.cli task pipeline `
  .coding-harness/plans/<piano>.md `
  "Task isolato" `
  --provider codex `
  --isolated
```

In modalità isolata l’agente e i test lavorano in `.coding-harness/worktrees/<task>`. Il risultato non viene integrato automaticamente in `main`: il merge controllato è ancora una fase manuale.

## Complessità e numero di agenti

La complessità viene stabilita nella fase di piano. Non è obbligatorio usare più agenti: si usa il numero minimo necessario.

| Livello | Tipo di attività | Workflow indicativo |
|---|---|---|
| `C0` | Documentazione o configurazione isolata | Un agente |
| `C1` | Modifica locale a basso rischio | Un agente |
| `C2` | Funzione su più file con test | Un agente, review opzionale |
| `C3` | Refactor multi-livello | Implementatore + reviewer |
| `C4` | Architettura, sicurezza, dati o API | Architect + implementatore + reviewer |
| `C5` | Intervento ampio o parallelizzabile | Più agenti con isolamento |

Rischio, dati sensibili e operazioni distruttive possono imporre un livello di protezione maggiore rispetto alla complessità apparente.

## Chat e terminale

È possibile usare l’harness senza eseguire direttamente l’agente:

```powershell
python -m harness.cli task prompt tasks/<task>
```

Con provider CLI autenticati:

```powershell
python -m harness.cli task run tasks/<task> --provider codex
```

Durante l’esecuzione vengono mostrati sessione, ruolo, provider, permessi, workspace, destinazione e streaming dell’output.

## Sub-task e collaborazione

Un task può avere N sotto-task:

```powershell
python -m harness.cli task add-subtask tasks/<task> "Analisi API" `
  --role architect `
  --provider openrouter

python -m harness.cli task run-subtask tasks/<task>/subtasks/001-analisi-api
```

Usare più agenti solo quando portano un vantaggio reale. Task che condividono file devono essere eseguiti in sequenza oppure in ambienti isolati.

## Artefatti di un task

```text
tasks/<task>/
├── PLAN.md
├── AGENT_PROMPT.md
├── SANDBOX-MANIFEST.json
├── SANDBOX-MANIFEST.approved.json
├── agent-output.md
├── TEST-REPORT.md
├── AUDIT.md
├── HANDOFF.md
├── status.json
├── events.jsonl
└── subtasks/
```

Gli errori operativi vengono raccolti in `.coding-harness/errors.jsonl` e `.coding-harness/ERRORS.md`.

## Documenti di progetto

| File | Responsabilità |
|---|---|
| `.coding-harness/SYSTEM_PROMPT.md` | Metodo di lavoro e comportamento comune |
| `.coding-harness/PROJECT_RULES.md` | Architettura, stack, convenzioni e vincoli |
| `.coding-harness/SANDBOX.md` | Contratto di ingresso, perimetro e uscita |
| `.coding-harness/memory.md` | Conoscenze confermate e preferenze persistenti |
| `.coding-harness/decisions.md` | Decisioni architetturali e motivazioni |
| `.coding-harness/config.json` | Provider, terminale, timezone e test |
| `.coding-harness/LIMITATIONS.md` | Limiti conosciuti e soluzioni candidate |
| `.coding-harness/ERRORS.md` | Catalogo degli errori ricorrenti |

## Verifica locale

Test dell’harness:

```powershell
python -m unittest discover -s tests -v
```

Test dell’esempio Flask:

```powershell
Push-Location examples\flask-login
try { .\.venv\Scripts\python.exe -m unittest discover -s tests -v }
finally { Pop-Location }
```

La stessa verifica viene eseguita automaticamente da GitHub Actions su push e pull request.

## Esempio incluso

`examples/flask-login` contiene un’app Flask dimostrativa con registrazione, login, logout, sessioni, password hashate, pagine informative, portfolio, splash screen e test automatici.

```powershell
cd examples\flask-login
.\.venv\Scripts\python.exe app.py
```

Aprire <http://127.0.0.1:5000>.

## Limiti attuali

Il progetto non offre ancora:

- sandbox preventiva OS-level;
- Git worktree isolato automatico per ogni agente;
- enforcement completo dei permessi a livello filesystem;
- lock multiprocesso completamente atomici;
- resume automatico di processi interrotti;
- reviewer con approvazione formale completa;
- tool filesystem/terminal sicuri per OpenRouter;
- CI GitHub già configurata;
- gestione completa dei segreti negli output di tutti i provider.

I limiti sono tracciati in [`LIMITATIONS.md`](.coding-harness/LIMITATIONS.md) e non vengono nascosti dietro descrizioni generiche di “sandbox”.

## Roadmap

1. Pipeline dichiarative con workflow proporzionato a `C0–C5`.
2. Manifest con permessi distinti di lettura, scrittura e creazione.
3. Git worktree isolati per task e integrazione controllata.
4. Sandbox preventiva per filesystem, processi, comandi e rete.
5. Stati formali di review, rifiuto, correzione e resume.
6. Handoff compatti e contesto selettivo per ridurre i token.
7. GitHub Actions, documentazione di contributo e release riproducibili.

## Contribuire

Prima di proporre modifiche:

1. creare o aggiornare un piano;
2. dichiarare complessità, rischio e file coinvolti;
3. aggiornare il manifest sandbox;
4. aggiungere test o motivare l’assenza;
5. aggiornare memoria, decisioni o limiti quando necessario.

Le modifiche che ampliano il perimetro del task devono essere esplicite e approvate.

La procedura completa è in [`CONTRIBUTING.md`](CONTRIBUTING.md). Per problemi di sicurezza consultare [`SECURITY.md`](SECURITY.md).

## Licenza

La licenza del repository deve essere definita prima della pubblicazione su GitHub.
