# Piano: Hardening governance e handoff del Coding Harness

## Obiettivo

Rendere l’harness più controllabile e affidabile quando più agenti collaborano sullo stesso progetto, senza modificare l’app Flask di test.

## Contesto

La prova OpenRouter → Codex → Claude ha funzionato, ma ha evidenziato contesto condiviso implicito, permessi solo dichiarativi, audit incompleto e adapter differenti.

## Attività atomiche

- [ ] 
- [ ] Introdurre un manifest di progetto persistente con nome, timezone, identità e ruoli agenti
- [ ] Definire permessi `read-only`, `modify` e `both` con tracciamento per sessione
- [ ] Creare un handoff Markdown strutturato per ogni passaggio tra agenti
- [ ] Includere nel contesto solo documenti pertinenti, versionati e non duplicati
- [ ] Registrare session ID, provider, ruolo, permesso, file modificati e comandi/test eseguiti
- [ ] Introdurre firma e catena di integrità per file Markdown e blocchi di modifica
- [ ] Associare ogni firma a identità agente, sessione, ruolo e permesso verificabili
- [ ] Definire ownership esclusiva dei file modificabili e bloccare sovrapposizioni concorrenti
- [ ] Supportare merge esplicito tramite agente integratore quando due lavori riguardano lo stesso file
- [ ] Uniformare gli adapter su un risultato comune con stdout/stderr, errori, timeout e metadati
- [ ] Aggiungere test di integrazione per handoff, timezone, encoding, fallimenti e permessi
- [ ] Documentare i limiti residui e il percorso per tool filesystem/terminal OpenRouter

## File coinvolti

- `harness/core.py`
- `harness/cli.py`
- `.coding-harness/config.json`
- `.coding-harness/PROJECT_RULES.md`
- `tests/`
- `README.md`

## Criteri di accettazione

- Ogni agente è identificabile senza ambiguità nel task e negli eventi
- Il ruolo e il permesso sono esplicitati prima dell’esecuzione
- Ogni modifica Markdown produce un record firmato con hash precedente e successivo
- Una firma non valida o una catena interrotta blocca l’avanzamento del task
- Un file con ownership attiva non può essere modificato da un secondo agente
- Le eccezioni di modifica condivisa richiedono release dell’ownership e merge tracciato
- Ogni sotto-task riceve l’handoff del padre e dei predecessori in formato leggibile
- Un errore dell’adapter lascia sempre output e stato diagnosticabili
- I timestamp rispettano il timezone configurato
- I test dell’harness verificano i nuovi contratti
- Nessuna modifica viene effettuata in `examples/flask-login`, salvo test di compatibilità necessari

## Rischi e rollback

La dichiarazione dei permessi non equivale ancora a enforcement OS. Il parallelismo sullo stesso workspace resta rischioso finché non vengono introdotti worktree/sandbox e ownership dei path. Il rollback consiste nel mantenere compatibilità con il formato task esistente e migrare i metadati in modo retrocompatibile.

