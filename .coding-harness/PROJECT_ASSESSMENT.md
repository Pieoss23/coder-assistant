# Valutazione tecnica del progetto

Data: 2026-09-04  
Ambito: versione corrente del Coding Harness dopo la prova Flask e la collaborazione OpenRouter → Codex → Claude.

## Verdetto sintetico

Il progetto è un buon prototipo funzionante di workflow multi-agente, ma non è ancora un orchestratore affidabile da usare senza supervisione. La prova ha dimostrato che il nucleo è utile: piano approvabile, task persistente, agenti diversi e test automatici. Ha anche evidenziato che oggi la parte più fragile non è la velocità del linguaggio, ma il contratto tra agenti, la gestione dei permessi, la raccolta degli output e l’isolamento delle modifiche.

Valutazione attuale: **prototipo avanzato / pre-alpha**, non ancora production-ready.

## Cosa funziona

- Piano Markdown modificabile e protetto da hash dopo l’approvazione.
- Task e sotto-task persistenti con output, stato, eventi e report test.
- Esecuzione di provider diversi nello stesso progetto.
- OpenRouter free verificato con chiamata reale.
- Codex ha modificato realmente il progetto Flask e ha creato/aggiornato test.
- Claude ha svolto una revisione e ha individuato difetti tecnici reali.
- I test vengono eseguiti dall’harness e salvati in `TEST-REPORT.md`.
- Il comando test può essere specifico per ambiente/task.
- Memoria, decision log, regole e system prompt sono separati.
- Il caricamento della chiave da `.env` evita di inserirla nella configurazione versionabile.

## Miglioramenti appena introdotti

- Timestamp con fuso configurabile in `config.json`, predefinito `Europe/Rome`.
- Identità dell’agente derivata da progetto, ruolo e provider.
- Permesso dichiarato per agente: `read-only`, `modify` o `both`.
- Condivisione esplicita dei Markdown del task padre e degli output/report dei sotto-task fratelli.
- Ruoli persistenti nei sotto-task.
- README con mappa precisa dei documenti e procedura a tre agenti.

## Limiti attuali

### 1. Permessi non ancora realmente applicati

Il permesso è oggi metadato, prompt e tracciamento. Un agente con una CLI autorizzata può ancora tentare di modificare file anche se dichiarato `read-only`. Serve enforcement reale tramite sandbox per provider, policy sui path e controllo dei comandi.

La stessa limitazione vale per l’ownership dei file: oggi non esiste ancora un lock esclusivo. La regola progettuale da introdurre è “un solo agente writer per file”; il parallelismo sullo stesso file deve passare da copia/worktree e merge tracciato.

### 2. OpenRouter non è ancora un coding agent completo

L’adapter OpenRouter invia una richiesta HTTP e salva testo. Non offre al modello strumenti per leggere file, applicare patch, eseguire test o osservare il diff. Il modello può proporre modifiche ma non può dimostrare di averle applicate.

### 3. Condivisione Markdown ancora non strutturata abbastanza

Ora vengono inclusi piano padre, output e report dei fratelli, con un limite di 12.000 caratteri per file. Mancano:

- un handoff strutturato con input/output/decisioni;
- riferimenti espliciti all’ultima versione di ogni file;
- deduplicazione e priorità del contesto;
- verifica che un agente abbia letto davvero il materiale;
- redazione automatica di segreti e dati sensibili.

### 4. Adattatori eterogenei

Ogni CLI ha argomenti, modalità di approvazione, encoding, trust del repository e gestione sessione differenti. L’adapter attuale è sufficiente per prove locali ma non ha ancora:

- interfaccia comune per streaming e progress;
- parsing degli eventi strutturati;
- retry/backoff e rate limit;
- timeout differenziati;
- resume delle sessioni;
- gestione uniforme dei permessi;
- raccolta costante di stdout/stderr/metadati.

### 5. Parallelismo rischioso sullo stesso workspace

I sotto-task possono essere eseguiti in parallelo, ma non esiste ancora un file ownership lock, un worktree isolato o un merge controllato. Due agenti possono sovrascrivere lo stesso file o produrre test incompatibili.

### 6. Audit incompleto

Esiste `events.jsonl`, ma non c’è ancora un’identità forte della sessione, hash del diff prima/dopo, elenco preciso dei comandi eseguiti, file toccati o firma dell’approvazione dello sviluppatore. Senza Git il recupero e la responsabilità sulle modifiche sono più deboli.

Una firma digitale per blocco Markdown risolverà l’attribuzione e l’integrità dei documenti, ma non sostituirà ownership, sandbox o audit del filesystem.

### 7. Memoria aggiornata manualmente

La memoria viene inclusa nei prompt e può essere modificata via CLI, ma l’harness non distingue ancora automaticamente fatti verificati, proposte, correzioni e decisioni confermate. Un agente può dichiarare di aver aggiornato la memoria senza averlo fatto realmente.

### 8. Test del test runner incompleti

Mancano test dedicati per timezone, provider failure, timeout, output Unicode, permessi, condivisione Markdown, collisioni tra sotto-task e assenza di comandi test.

Gli errori vengono ora conservati in `ERRORS.md` e `errors.jsonl`; manca ancora il collegamento automatico tra errore e regression test/soluzione chiusa.

## Valutazione C vs Python

Risposta schietta: **non conviene riscrivere ora l’harness in C per risparmiare risorse o token**.

Il consumo di token dipende soprattutto da quantità e qualità del contesto inviato al modello, non dal linguaggio del wrapper. La latenza osservata è dominata da rete, provider e modello free. Python offre invece sviluppo più rapido, integrazione CLI migliore, parsing Markdown/JSON semplice e maggiore facilità di evoluzione.

C potrebbe avere senso solo per un componente molto specifico: sandbox, file watcher, gestione processi o servizio a lunga esecuzione con requisiti stretti di memoria. Anche in quel caso è più prudente valutare prima Rust, Go o un piccolo helper nativo, mantenendo Python come control plane.

## Pro

- Idea architetturale valida e verificata con tre agenti reali.
- Workflow comprensibile e già utilizzabile.
- Persistenza dei task superiore a una semplice chat.
- Provider intercambiabili.
- Buona separazione tra regole, memoria e decisioni.
- Test automatici e report già operativi.

## Contro

- Nessun vero sistema di autorizzazione.
- Nessuna sandbox uniforme tra provider.
- Nessun isolamento Git/worktree.
- OpenRouter ancora text-only.
- Adattatori troppo permissivi e poco standardizzati.
- Audit non sufficiente per attribuire ogni modifica con certezza.
- Mancano CLI per lista, stato, review, resume e approvazione dei risultati.
- Mancano test di integrazione dell’orchestratore.

## Priorità consigliate

1. Definire un manifest di progetto con timezone, identità, ruoli, permessi e ownership dei path.
2. Implementare lease e code per risorsa prima di aumentare il parallelismo.
3. Introdurre session ID, file hash e diff audit per ogni agente.
4. Implementare handoff Markdown strutturati tra sotto-task.
5. Separare workspace read-only, workspace-write e worktree per agente.
6. Standardizzare gli adapter su un protocollo interno a eventi.
7. Creare tool OpenRouter con allowlist, sandbox, approval gate e logging.
8. Aggiungere test di integrazione e failure injection.
9. Solo dopo misurare se serve un helper nativo per prestazioni.

## Conclusione

Il progetto ha superato la fase di idea e ha dimostrato un valore pratico. Non è però ancora abbastanza controllato per lasciare agenti autonomi modificare liberamente una repository importante. La direzione corretta è consolidare governance, handoff e permessi prima di aumentare il grado di autonomia dei modelli.
