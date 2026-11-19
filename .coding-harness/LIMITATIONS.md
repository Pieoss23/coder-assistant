# Limiti, rischi e problemi aperti

Questo registro raccoglie i limiti conosciuti del Coding Harness. Non è una lista generica: ogni voce deve descrivere una situazione osservata o plausibile, il rischio prodotto e una possibile soluzione verificabile.

## Stati

- `open`: problema noto, senza soluzione implementata
- `designing`: soluzione in progettazione
- `implemented`: soluzione presente ma da consolidare
- `verified`: soluzione verificata con test o prova reale
- `accepted`: limite noto e accettato consapevolmente

## Registro

| ID | Area | Limite | Impatto | Stato | Soluzione candidata | Priorità |
|---|---|---|---|---|---|---|
| LIM-001 | Permessi | `read-only`, `modify` e `both` sono oggi metadati/prompt, non enforcement OS | Un agente potrebbe modificare oltre il proprio perimetro | open | Sandbox per processo, allowlist path e policy comandi | P0 |
| LIM-002 | Ownership | Esiste ora un lock conservativo, ma senza TTL/heartbeat | Un processo interrotto può lasciare ownership da recuperare | implemented | Lease con TTL, heartbeat e recovery command | P0 |
| LIM-003 | Coda | Esiste una coda FIFO persistente con dispatcher manuale e priorità, ma senza retry automatico | Il task accodato non riparte da solo | implemented | Dispatcher persistente per risorsa, retry e retry policy | P0 |
| LIM-004 | Gerarchia | Worker e subagent non hanno ancora un DAG di dipendenze | Un subagent può lavorare su input vecchi o non approvati | open | Parent session, task graph, barrier e handoff obbligatorio | P0 |
| LIM-005 | Reviewer | Il reviewer non ha potere formale di approve/reject/rollback | Un risultato difettoso può essere marcato completato | open | Stati `proposed`, `reviewing`, `approved`, `rejected`, `needs-changes` | P0 |
| LIM-006 | Condivisione | I Markdown sono condivisi per testo concatenato e troncato | Token sprecati e rischio di perdere decisioni importanti | designing | Handoff strutturato, riferimenti a file/versioni e contesto selettivo | P1 |
| LIM-007 | Firma | Non esiste firma o catena di integrità dei Markdown | Attribuzione e rilevazione manomissioni deboli | designing | Firma digitale per record/blocco e hash del contenuto | P1 |
| LIM-008 | Audit | Non sono sempre registrati file modificati, diff e comandi completi | Risalire al responsabile di una modifica è difficile | open | Snapshot hash, diff manifest, comando normalizzato e session ID | P0 |
| LIM-009 | Adapter | Provider diversi hanno trust, stdin, encoding e approvazioni differenti | Un adapter può fallire o comportarsi in modo inatteso | designing | Protocollo interno a eventi, capability declaration e test per adapter | P1 |
| LIM-010 | OpenRouter | API text-only senza filesystem/terminal tool | Il modello propone codice ma non può applicarlo o verificarlo | accepted | Tool bridge sandboxato con approval gate | P1 |
| LIM-011 | Parallelismo | Due task possono modificare file correlati senza saperlo | Test verdi localmente ma integrazione rotta | open | Ownership per path + dependency graph + integration queue | P0 |
| LIM-012 | Memoria | Un agente può dichiarare un aggiornamento senza produrlo davvero | La memoria può divergere dalla repository | open | Memory patch firmata, validazione e reviewer approval | P1 |
| LIM-013 | Recupero | Un processo interrotto può lasciare lease e stato `running` | Risorse bloccate e task difficili da riprendere | open | Lease expiration, recovery command e resume sessione | P1 |
| LIM-014 | Segreti | La redazione è basata soprattutto su regole del prompt | Un token può finire in output o report | open | Secret scanner pre-write e pre-report, fail closed | P0 |
| LIM-015 | Errori | Gli errori sono ora raccolti, ma non chiusi automaticamente con test o fix | Il catalogo può crescere senza ridurre le regressioni | implemented | Error lifecycle con owner, fix, regression test e stato verified | P1 |
| LIM-016 | Terminali | Il core funziona su Windows ma i test command sono ancora shell-specific | Bash/cmd/zsh possono differire per quoting e path | open | Adapter per terminale e comandi argv portabili | P1 |

## Modello di collaborazione da valutare

```text
Project coordinator
├── Worker A
│   ├── Subagent A1 → subtask e file assegnati
│   └── Subagent A2 → subtask e file assegnati
├── Worker B
│   └── Subagent B1 → subtask e file assegnati
└── Reviewer → legge risultati, esegue test, approva o respinge
```

Regole candidate:

1. Il reviewer non modifica durante la fase di osservazione; modifica solo in una fase separata `fixing` autorizzata.
2. Ogni worker dichiara i path che intende modificare prima di partire.
3. Un subagent eredita il contesto del parent ma non automaticamente i suoi permessi di scrittura.
4. Un file richiesto da più writer entra in coda; il secondo riceve un handoff aggiornato quando il primo rilascia il lease.
5. Il completamento del parent richiede la chiusura dei figli e l’approvazione del reviewer.

## Coda: quando è necessaria

La coda è necessaria quando due attività hanno almeno un path in comune o una dipendenza semantica non rappresentabile dal solo path. Non è necessaria per file realmente indipendenti.

La coda non deve essere un semplice elenco globale: deve essere per risorsa o gruppo di risorse, con priorità, dipendenze, timeout e proprietario. Un lease scaduto deve rendere il lavoro recuperabile senza lasciare il file bloccato indefinitamente.

## Firma: quando è necessaria

La firma è utile per:

- dimostrare chi ha prodotto un handoff o una decisione;
- rilevare modifiche successive non autorizzate;
- collegare un record a sessione, ruolo e provider;
- supportare audit e rollback.

La firma non risolve conflitti, non impedisce scritture e non sostituisce lock o sandbox. La priorità corretta è: enforcement → ownership/coda → audit → firme crittografiche.

## Come usare questo registro

Quando emerge un nuovo problema, aggiungere una riga con ID, scenario riproducibile, impatto e soluzione candidata. Quando viene implementata una soluzione, collegare task, test e decisione ADR. Non cancellare i limiti risolti: portarli a `verified` mantiene la storia del progetto.

## Aggiornamento implementativo 2026-11-16

- Il test runner supporta una `working_directory` validata dentro il workspace.
- I risultati dei test non verdi portano il task a `needs-review` invece di `completed`.
- I processi CLI vengono terminati dopo un timeout.
- Le modifiche fuori dai path assegnati vengono rilevate a fine agente; questo non è ancora una sandbox OS preventiva.
- Il comando `queue dispatch` è disponibile anche dalla CLI.
