# CLAUDE.md: gemello digitale dell'infliximab

## Chi decide cosa
- Alessandro è il founder clinico (osteopata) di una startup biotech in-silico. Non è un programmatore.
- Claude scrive il codice; Alessandro decide cosa costruire.
- Spiega ogni passo in italiano semplice.
- Chiedi conferma prima di installare qualsiasi cosa.
- Lavora solo in questo repository (`AlessandroGz-AX/infliximab-twin`).

## Obiettivo
Prototipo dimostrativo del "gemello digitale dell'infliximab": un paziente virtuale in cui si vede nel tempo la concentrazione di infliximab nel sangue, calcolata con un modello pubblicato, che si aggiorna quando si inserisce un esame del sangue con il livello del farmaco.

**È solo una dimostrazione: non va mai usato per decidere la terapia di pazienti reali.** L'interfaccia deve dirlo in modo chiaro e ben visibile (testo pronto in `gemello.AVVERTENZA`).

## Il modello: unica fonte
Fasanmade AA et al. *Population pharmacokinetic analysis of infliximab in patients with ulcerative colitis.* Eur J Clin Pharmacol 2009;65:1211-28. https://pmc.ncbi.nlm.nih.gov/articles/PMC2778780/

Regole:
- Implementa il modello finale esattamente come è scritto: due compartimenti, equazioni delle covariate, variabilità tra pazienti, errore residuo.
- Non inventare e non approssimare valori. Se qualcosa non è chiaro o manca, fermati e chiedi ad Alessandro.
- Se l'articolo dice qualcosa di diverso dai valori di controllo di Alessandro, vale l'articolo: segnalalo.
- Ogni numero nel codice riporta la pagina o la tabella dell'articolo.
- Dentro l'articolo, le equazioni finali (p. 1218) e la Tabella 3 prevalgono sulle frasi riassuntive del testo. Non "correggere" il modello per farlo tornare con il testo (es. "33% più bassa nelle donne"). Le discrepanze sono in `docs/confronto_articolo.md`.

Valori di controllo dati da Alessandro: CL 0,407 L/giorno, V1 3,29 L, V2 4,13 L, Q 7,14 L/giorno, emivita terminale circa 14 giorni; CL circa +47% con anticorpi anti-infliximab, circa 33% più bassa nelle donne, più bassa con albumina più alta; il peso agisce su V1.

## Cosa deve fare l'app (Python + Streamlit, in locale)
1. Dati del paziente: peso, sesso, albumina, anticorpi anti-infliximab sì/no.
2. Schema di terapia: di default 5 mg/kg alle settimane 0, 2 e 6, poi ogni 8 settimane; modificabile.
3. Curva della concentrazione per 54 settimane, linea di soglia modificabile (default 3 µg/mL) e indicazione di quando la concentrazione minima scende sotto la soglia.
4. Uno o più livelli misurati (data e valore): ricalibrazione bayesiana (massima a posteriori) con la variabilità e l'errore del modello pubblicato; curva prima e dopo l'aggiornamento.
5. Confronto con uno schema alternativo ("cosa succederebbe se...").

## Test obbligatori (un solo comando: `python -m pytest`)
1. Paziente tipico: parametri uguali all'articolo; emivita.
2. Effetti delle covariate uguali alle equazioni dell'articolo.
3. Concentrazioni osservate o simulate riportate nell'articolo, riprodotte entro un margine ragionevole. Dire quali valori si sono confrontati.
4. Simulazione e stima: 100 pazienti virtuali con parametri noti, misure generate con il rumore del modello; la stima bayesiana deve ritrovare parametri vicini a quelli veri. Riportare l'errore medio.

## Come lavoriamo
- Prima del codice, un piano breve a passi.
- Un passo alla volta. Alla fine di ognuno: cosa si dovrebbe vedere e come provarlo.
- Codice semplice e commentato in italiano. README in italiano che spiega come avviare l'app.
- Alla fine: 5 righe su cosa funziona, cosa no e quali limiti ha il prototipo.

## Stato del progetto (aggiornare a ogni passo)
- [x] Passo 0: preparazione (repository, ambiente, CLAUDE.md, README)
- [x] Passo 1: modello (`gemello/modello.py`) + test 1 e 2 (`tests/test_modello.py`)
- [ ] Passo 2: simulatore 54 settimane + test 3
- [ ] Passo 3: stima bayesiana (massima a posteriori) + test 4
- [ ] Passo 4: app Streamlit
- [ ] Passo 5: misure del paziente e schema alternativo
- [ ] Passo 6: README finale e bilancio in 5 righe

## Domande aperte
1. **Variabilità tra pazienti** (serve dal passo 2). La Tabella 3 dà 37,68% su CL e 22,11% su V1, nessuna IIV su V2 e Q. Il testo (p. 1216) dice però che c'era una correlazione CL-V1 di cui non pubblica il valore, e che V2 e Q avevano un blocco "simile". Proposta: usare solo la Tabella 3 (ω = 0,3768 e 0,2211 come deviazioni standard, come l'articolo fa per l'errore residuo), correlazione zero, nessuna IIV su V2 e Q, e dichiararlo come limite. In attesa di risposta.

## Decisioni prese
- Repository dedicato `AlessandroGz-AX/infliximab-twin`, separato dai progetti personali.
- Ramo di lavoro: `claude/prototipo`.
- Ambiente Python isolato in `.venv` (installazioni approvate da Alessandro: streamlit, scipy e dipendenze).
- Le equazioni finali e la Tabella 3 prevalgono sul testo (vedi sopra).
- Albumina in g/dL, come nell'articolo (41 g/L = 4,1 g/dL).

## Mappa del codice
- `gemello/modello.py`: parametri ed equazioni dell'articolo, emivita, avvisi di estrapolazione.
- `gemello/confronto_articolo.py`: tabella articolo contro modello (`python -m gemello.confronto_articolo`).
- `docs/confronto_articolo.md`: discrepanze e punti non chiari dell'articolo.
- `tests/`: test (`python -m pytest`).
