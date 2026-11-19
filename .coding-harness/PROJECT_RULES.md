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
- L’ownership di un file modificabile è esclusiva: un solo agente può modificarlo in una sessione.
- Un agente `read-only` può leggere e produrre analisi, ma non può scrivere nel repository o nel Markdown autorevole.
- Un agente con permesso `both` può leggere e modificare solo i path assegnati nella propria sessione.
- Se due agenti necessitano dello stesso file, il secondo resta in attesa oppure lavora su una copia/worktree; il merge deve essere un’operazione separata e tracciata.

## Convenzioni di sviluppo

- Nomi in inglese per codice, API e file tecnici; documentazione operativa in italiano salvo necessità.
- Funzioni piccole, responsabilità singola, tipi espliciti e gestione errori leggibile.
- Nessuna modifica distruttiva senza conferma esplicita.
- Preferire configurazione tramite `.env` per segreti e `config.json` per comportamento non sensibile.
- `.env` non deve mai entrare in output, log, diff o report.

## Integrità e firma dei documenti

- Ogni modifica a un Markdown autorevole deve essere rappresentata da un record append-only con session ID, agente, ruolo, timestamp, hash precedente, hash successivo e firma.
- L’hash dimostra l’integrità del contenuto; la firma dimostra l’identità della chiave agente. Non confondere i due concetti.
- La chiave privata non va mai salvata nel repository, nei task o nei prompt.
- Una firma non verificabile rende il passaggio non approvato e richiede revisione.
- Le modifiche manuali dello sviluppatore devono essere registrabili come identità `developer` con lo stesso formato.

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

## Confine del task

Ogni agente lavora esclusivamente sui file e sui criteri indicati nel piano approvato. Non deve fare over-effort, cleanup o refactor laterali. Un problema non necessario al task va documentato e non corretto autonomamente. Una modifica fuori perimetro invalida il risultato e deve essere segnalata nel report.

Il contratto operativo completo è in `SANDBOX.md`.
