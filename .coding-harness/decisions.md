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
- Algoritmo e formato delle firme per Markdown e blocchi di modifica.
- Gestione delle chiavi agente: keyring del sistema, SSH signing o provider crittografico dedicato.
- Politica di revoca e rotazione delle chiavi.
- Modello definitivo di lease, coda per risorsa e dipendenze tra worker e subagent.
