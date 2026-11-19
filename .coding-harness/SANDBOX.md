# Task Sandbox Contract

## Scopo

La sandbox del Coding Harness delimita una singola funzione di sviluppo. Un agente riceve un ingresso controllato, opera solo nel perimetro assegnato e produce una sola uscita verificabile.

La sandbox non significa soltanto “cartella temporanea”. È un middleware di controllo tra agente e repository.

```text
Piano approvato
    ↓
Ingresso controllato
    ↓
Agente con ruolo, provider, permessi e path assegnati
    ↓
Diff osservato + test + audit
    ↓
Uscita validata oppure rifiutata
```

## Ingresso

L’agente riceve esclusivamente:

- piano approvato e non modificato dopo l’approvazione;
- regole tecniche e system prompt del progetto;
- memoria e decisioni confermate;
- handoff dei task precedenti autorizzati;
- ruolo e identità del progetto;
- permesso (`read-only`, `modify`, `both`);
- elenco dei path assegnati;
- comando di test e directory di lavoro;
- criteri di accettazione.
- livello di complessità `C0–C5` e workflow approvato.

Il contesto non deve includere automaticamente task non correlati, segreti, credenziali o contenuti oltre il limite necessario.

## Perimetro chirurgico

Un agente deve svolgere solo ciò che è indicato nel proprio piano.

È vietato:

- rifattorizzare file non coinvolti;
- correggere problemi non necessari al criterio di accettazione;
- cambiare dipendenze, architettura o stile senza decisione approvata;
- modificare configurazioni globali per comodità;
- creare cleanup non richiesti;
- alterare test per nascondere un fallimento;
- aggiornare memoria o decisioni senza una motivazione verificabile.

Se trova un problema fuori perimetro, l’agente deve registrarlo in `agent-output.md` o `.coding-harness/ERRORS.md` e fermarsi, salvo autorizzazione esplicita.

## Uscita unica

Un task è accettabile solo se produce il pacchetto coerente:

- diff dei file autorizzati;
- `agent-output.md` con riepilogo e decisioni;
- `TEST-REPORT.md` con comando, directory, output ed esito;
- `AUDIT.md` con file creati, modificati ed eliminati;
- `HANDOFF.md` per il passaggio al task successivo;
- evento in `events.jsonl`;
- stato finale coerente (`completed`, `needs-review` o `failed`).

Una scrittura fuori perimetro deve invalidare l’uscita. La validazione attuale avviene a fine esecuzione tramite snapshot; la futura sandbox preventiva dovrà bloccare la scrittura prima che raggiunga il filesystem.

## Livelli di protezione

1. **Prompt contract**: l’agente conosce il proprio perimetro.
2. **Ownership**: i path assegnati vengono prenotati.
3. **Post-run validation**: il diff viene confrontato con i path autorizzati.
4. **Test gate**: test falliti portano a `needs-review`.
5. **Sandbox preventiva**: filesystem, processi e rete limitati prima dell’avvio dell’agente. È il livello ancora da implementare.

## Non è una garanzia assoluta, per ora

La versione corrente rileva le modifiche fuori perimetro dopo l’esecuzione, ma non impedisce ancora a un processo autorizzato di scrivere prima del controllo. Per una protezione forte serviranno processi isolati, worktree Git o filesystem overlay, allowlist dei comandi e policy di rete.

## Complessità e proporzionalità

La sandbox e il numero di agenti devono essere proporzionati al task. `C0` e `C1` usano normalmente un solo agente; `C2` può aggiungere un reviewer; `C3` richiede normalmente implementazione e review; `C4` e `C5` possono richiedere architettura, worktree isolati e più gate. Il piano può scegliere un livello di protezione superiore, mai inferiore a quello imposto da rischio e sensibilità.
