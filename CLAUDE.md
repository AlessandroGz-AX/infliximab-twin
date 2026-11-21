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

Dati per il solo controllo (test 3), non per i parametri del modello: Adedokun OJ et al., Gastroenterology 2014 (doi 10.1053/j.gastro.2014.08.035), livelli misurati negli studi ACT 1 e 2 con 5 mg/kg (numeri forniti da Alessandro, in `gemello/validazione.py`).

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
- [x] Passo 2: simulatore 54 settimane (`gemello/simulazione.py`) + test 3 (`tests/test_validazione.py`)
- [x] Passo 3: stima bayesiana (`gemello/stima.py`) + test 4 (`gemello/verifica_stima.py`, `tests/test_stima.py`)
- [ ] Passo 4: app Streamlit
- [ ] Passo 5: misure del paziente e schema alternativo
- [ ] Passo 6: README finale e bilancio in 5 righe

## Domande aperte
1. **Numeri di Adedokun 2014 da verificare** sull'articolo originale. Il sito dell'editore blocca l'accesso automatico (controllo anti-robot): serve il PDF da Alessandro. Non aggirare i controlli anti-robot.
2. **Errore sistematico con una sola valle (test 4).** Con un solo prelievo la stima sovrastima la clearance in media del 5,8%, oltre il margine del 5% fissato prima dei risultati. La causa è il termine ln(varianza) della massima a posteriori standard, la stessa delle stime FOCE-I dell'articolo (senza quel termine: +2,3%). Il test è segnato `xfail(strict=True)` come fallimento noto. Proposta ad Alessandro: tenere il metodo standard e dichiarare l'errore (+6% con una valle, che va nella direzione prudente), invece di cambiare metodo per far passare il test. In attesa di risposta.

## Come Alessandro prova il prototipo
- Lavora da iPad. Le parti senza interfaccia le vede su GitHub (pagina `docs/confronto_articolo.md` e segno verde dei test nella scheda Actions).
- Per l'app (passo 4) il piano è pubblicarla in privato su Streamlit Community Cloud, collegata al repository, e aprirla da Safari. Verifica le condizioni attuali del servizio prima di proporlo. Intanto mandagli screenshot.

## Decisioni prese
- Repository dedicato `AlessandroGz-AX/infliximab-twin`, separato dai progetti personali. Si lavora direttamente su `main` (autorizzato da Alessandro).
- Ambiente Python isolato in `.venv` (installazioni approvate da Alessandro: streamlit, scipy e dipendenze).
- Le equazioni finali e la Tabella 3 prevalgono sul testo (vedi sopra). Alessandro ha confermato: per le donne vale l'equazione (-23,6% su CL), non il "-33%" del testo.
- **Variabilità tra pazienti, opzione A:** solo Tabella 3, omega = 0,3768 (CL) e 0,2211 (V1) come deviazioni standard, nessuna correlazione CL-V1, nessuna variabilità su V2 e Q. È un limite dichiarato: i limiti stanno in `gemello.LIMITI` e vanno mostrati in README, `docs/confronto_articolo.md` e app.
- Test 3: emivita mediana sulla popolazione virtuale (articolo p. 1221) + livelli di Adedokun 2014. Margini fissati prima dei risultati: mediana 14 ± 1 giorno, quartili ± 1,5 giorni, livelli tra le mediane dei due gruppi.
- Albumina in g/dL, come nell'articolo (41 g/L = 4,1 g/dL).
- Stima bayesiana: massima a posteriori su eta_CL ed eta_V1. La funzione obiettivo comprende il termine ln(varianza), perché con l'errore combinato la varianza dipende dalla previsione. Ricerca con Nelder-Mead da 3 punti di partenza.
- **Livelli sotto 0,1 µg/mL: metodo M3** (Beal 2001), scelto da Alessandro (opzione A). È dichiarato in `gemello.LIMITI` perché non viene dall'articolo.
- Test 4: 100 pazienti virtuali, tre modi di fare i prelievi (una valle, due valli, prelievi ACT 1). Misure: errore medio assoluto su CL e V1, errore mediano sulla valle della settimana 54 (la media è falsata dalle valli quasi a zero), errore sistematico come media geometrica dei rapporti, % di pazienti dal lato giusto della soglia di 3 µg/mL. Margini fissati prima dei risultati (vedi `tests/test_stima.py`).
- I test girano su GitHub Actions a ogni modifica di `main` (`.github/workflows/test.yml`).

## Mappa del codice
- `gemello/__init__.py`: testo dell'avvertenza (`AVVERTENZA`) e dei limiti (`LIMITI`).
- `gemello/modello.py`: parametri ed equazioni dell'articolo, variabilità, emivita, avvisi di estrapolazione.
- `gemello/simulazione.py`: schema di terapia, concentrazione con la formula esatta, valli, periodi sotto soglia.
- `gemello/popolazione.py`: popolazione virtuale simile alla Tabella 2 (solo per i controlli).
- `gemello/validazione.py`: test 3, confronto con valori osservati (`python -m gemello.validazione`).
- `gemello/stima.py`: stima bayesiana (massima a posteriori) dai livelli misurati.
- `gemello/verifica_stima.py`: test 4, simulazione e stima (`python -m gemello.verifica_stima`).
- `gemello/confronto_articolo.py`: tabella articolo contro modello (`python -m gemello.confronto_articolo`).
- `gemello/documentazione.py`: rigenera le parti automatiche di README e docs (`python -m gemello.documentazione`).
- `docs/confronto_articolo.md`: discrepanze, punti non chiari e risultati dei controlli.
- `tests/`: test (`python -m pytest`).
