# Confronto con l'articolo e verifiche del modello

Fonte: Fasanmade AA et al. *Population pharmacokinetic analysis of infliximab in patients with ulcerative colitis.* Eur J Clin Pharmacol 2009;65:1211-28.

Il modello segue **le equazioni finali (p. 1218) e la Tabella 3**. Quando una frase riassuntiva del testo non torna con le equazioni la segnaliamo come DIVERSO, ma non modifichiamo il modello per farla tornare.

Le parti tra i segnaposto si rigenerano dal codice con `python -m gemello.documentazione`. Un test controlla che tabella e limiti siano allineati al codice.

## Articolo contro modello

<!-- inizio tabella -->
| Grandezza | Articolo | Fonte | Modello | Esito | Nota |
|---|---|---|---|---|---|
| CL, paziente tipico | 0,407 L/giorno | Tab. 3 | 0,407 L/giorno | **OK** |  |
| V1, paziente tipico | 3,29 L | Tab. 3 | 3,29 L | **OK** |  |
| V2 | 4,13 L | Tab. 3 | 4,13 L | **OK** |  |
| Q | 7,14 L/giorno | Tab. 3 | 7,14 L/giorno | **OK** |  |
| CL con anticorpi anti-infliximab | +47,1% | p. 1220 | +47,1% | **OK** |  |
| CL nelle donne | circa -33% | testo p. 1220 | -23,6% | **DIVERSO** | L'equazione finale (p. 1218) e la Tab. 3 danno -23,6%. Il modello usa l'equazione. |
| V1 nelle donne | -16% | testo p. 1220 | -13,7% | **DIVERSO** | Il 16% corrisponde al confronto inverso: negli uomini V1 è +15,9% rispetto alle donne. |
| Effetto del peso su V1 (esponente) | 0,54 | p. 1222 | 0,538 | **OK** | 0,54 è il valore 0,538 della Tab. 3 arrotondato. |
| CL con albumina 3,8 contro 4,3 g/dL | +19,1% | p. 1223-1224 | +21,0% | **DIVERSO** | Differenza piccola. L'articolo non dice come ha fatto il calcolo (e scrive 'mg/dl' per refuso: è g/dL). |
| Volume allo stato stazionario, 77 kg | 7,71 L | p. 1221 | 7,42 L | **DIVERSO** | V1 + V2 della Tab. 3 fanno 7,42 L. |
| Emivita terminale | circa 14 giorni | abstract; p. 1216, 1221 | uomo tipico 12,9 g; donna tipica 15,8 g | **NOTA** | Il 14 è la mediana delle emivite dei singoli pazienti (p. 1221, intervallo interquartile 10,4-17,8 g), non il paziente tipico. Verifica sulla popolazione nel Test 3. |
<!-- fine tabella -->

## Limiti del modello

<!-- inizio limiti -->
- Variabilità tra pazienti presa solo dalla Tabella 3 dell'articolo: 37,68% sulla clearance (CL) e 22,11% sul volume centrale (V1), senza correlazione tra le due e senza variabilità su V2 e Q. L'articolo dice che una correlazione CL-V1 era stimata, ma non ne pubblica il valore.
- Il modello viene da adulti (18-81 anni) con colite ulcerosa da moderata a grave, trattati negli studi ACT 1 e ACT 2 con 5 o 10 mg/kg: non vale automaticamente per altre malattie, per i bambini o per altri dosaggi.
- Gli anticorpi anti-infliximab sono un sì/no valido per tutta la terapia, come nell'articolo, non dal momento in cui compaiono.
- Peso e albumina sono i valori di partenza e restano costanti per tutta la simulazione, come nell'articolo.
- I livelli sotto 0,1 µg/mL (il limite di quantificazione dello studio) entrano nella stima bayesiana come informazione "sotto 0,1" con il metodo M3 (Beal 2001), lo standard in farmacometria. È una scelta nostra: l'articolo non dice come li ha trattati.
- Con un solo livello misurato la stima bayesiana tende a sovrastimare la clearance (in media di circa il 6% nei test su 100 pazienti virtuali), quindi a prevedere valli un po' più basse del vero. Con più livelli l'effetto cala: circa 3% con due, circa 1% con tredici.
- Per aggiornare la curva con i livelli misurati si assume che le infusioni siano state fatte esattamente come nello schema di terapia indicato.
<!-- fine limiti -->

## Punti che l'articolo non chiarisce, e come li abbiamo risolti

1. **Variabilità tra pazienti (IIV).** La Tabella 3 riporta 37,68% su CL, 22,11% su V1 e "–" su V2 e Q. Però:
   - a p. 1216 il testo dice che su CL e V1 era stimata una matrice di varianza-covarianza "piena", cioè anche una correlazione tra i due. Il valore di quella correlazione non è pubblicato;
   - la stessa frase dice che per V2 e Q era stato assunto un blocco "simile". In più, a p. 1216 c'è lo shrinkage anche per V2 (29,2%) e Q (58,9%), possibile solo se su quei parametri c'era variabilità;
   - non è scritto con quale formula le varianze sono state convertite in percentuali.

   **Decisione di Alessandro (opzione A):** usiamo solo la Tabella 3. Omega vale 0,3768 su CL e 0,2211 su V1, intese come deviazioni standard, che è il modo in cui l'articolo riporta l'errore residuo. Nessuna correlazione e nessuna variabilità su V2 e Q.

2. **Concentrazioni in numeri per il Test 3.** L'articolo non riporta concentrazioni osservate o simulate in forma di numeri. Ci sono solo grafici: la Fig. 7 mostra 4 pazienti rappresentativi, senza i loro parametri individuali. Per il Test 3 usiamo quindi:
   - l'emivita mediana calcolata sui singoli pazienti (circa 14 giorni, intervallo interquartile 10,4-17,8, p. 1221);
   - i livelli misurati negli stessi studi ACT 1 e 2 riportati da Adedokun et al., Gastroenterology 2014 (doi 10.1053/j.gastro.2014.08.035), indicati da Alessandro. **Questi numeri sono ancora da verificare sull'articolo originale**: il sito dell'editore blocca l'accesso automatico.

## Test 3: risultati

<!-- inizio test 3 -->
### A) Emivita sulla popolazione virtuale (5000 pazienti)

| | Articolo (p. 1221) | Modello |
|---|---|---|
| Mediana | circa 14,0 giorni | 13,7 giorni |
| Intervallo interquartile | 10,4-17,8 giorni | 10,2-18,2 giorni |

### B) Livelli misurati negli studi ACT, 5 mg/kg (Adedokun 2014, da verificare)

| Momento | Non rispondevano | Rispondevano | Uomo tipico | Donna tipica | Mediana popolazione virtuale |
|---|---|---|---|---|---|
| Settimana 8 | 25,8 | 35,0 | 31,3 (59%) | 42,1 (177%) | 34,0 (89%) |
| Valle settimana 30 | 1,2 | 3,9 | 2,6 (51%) | 5,0 (142%) | 3,1 (71%) |
| Valle settimana 54 | 0,7 | 5,0 | 2,6 (44%) | 5,0 (100%) | 3,1 (56%) |

Valori in µg/mL. Tra parentesi la posizione tra i due gruppi: 0% = mediana di chi non rispondeva, 100% = mediana di chi rispondeva.
<!-- fine test 3 -->

Come leggerli:
- **Emivita.** L'intervallo del modello è un po' più largo di quello dell'articolo, ed è atteso: l'articolo calcola le emivite dalle stime individuali, che sono un po' "schiacciate" verso la media (shrinkage, p. 1216). La nostra popolazione invece ha la variabilità piena.
- **Popolazione virtuale.** Per peso e albumina la Tabella 2 riporta solo media, deviazione standard, mediana e intervallo, non la forma della distribuzione. La forma l'abbiamo scelta noi: dettagli in `gemello/popolazione.py`.
- **Margini.** Sono stati fissati prima di vedere i risultati: emivita mediana entro 14 ± 1 giorno, quartili entro ± 1,5 giorni, livelli compresi tra le mediane dei due gruppi.

## Test 4: la stima bayesiana ritrova i parametri veri?

Come funziona: 100 pazienti virtuali con parametri veri noti. Per ognuno le misure sono generate con il rumore del modello (errore residuo della Tabella 3), e la stima bayesiana riceve solo le misure. Si rigenera con `python -m gemello.verifica_stima`.

<!-- inizio test 4 -->
100 pazienti virtuali, schema 5 mg/kg alle settimane 0, 2, 6 e poi ogni 8. "Senza misure" = solo i valori tipici del paziente; "con stima" = dopo la stima bayesiana.

| Prelievi | Errore medio su CL | Errore medio su V1 | Errore mediano sulla valle della settimana 54 | Pazienti messi dal lato giusto della soglia di 3 µg/mL | Livelli sotto 0,1 µg/mL (usati con il metodo M3) |
|---|---|---|---|---|---|
| Una valle (settimana 14) | 33% → **15%** | 17% → **17%** | 61% → **26%** | 68% → **88%** | 6 su 100 |
| Due valli (settimane 14 e 22) | 33% → **10%** | 17% → **17%** | 61% → **16%** | 68% → **90%** | 7 su 200 |
| Prelievi dello studio ACT 1 (13) | 33% → **6%** | 17% → **13%** | 61% → **9%** | 68% → **97%** | 40 su 1300 |

Errore sistematico della stima (media geometrica dei rapporti stimato/vero): Una valle (settimana 14): CL +5,8%, V1 -1,3%; Due valli (settimane 14 e 22): CL +2,9%, V1 -1,0%; Prelievi dello studio ACT 1 (13): CL +1,3%, V1 +0,0%.
<!-- fine test 4 -->

Come leggerli:
- **Clearance (CL).** È il parametro che decide le valli, e la stima la ritrova bene già con un solo livello misurato.
- **V1.** Con sole valli cambia poco: le valli contengono poca informazione su V1 e la stima resta vicina al valore tipico, che è il comportamento corretto di una stima bayesiana. Per stimare V1 servono livelli presi subito dopo l'infusione.
- **Rumore.** Il rumore del modello è alto (errore proporzionale 40,3%, Tabella 3): ogni singolo livello ha una grande incertezza, ed è il motivo principale degli errori che restano.
- **Livelli sotto 0,1 µg/mL.** Entrano nella stima con il metodo M3 (vedi i limiti). Una valle non dosabile fa salire la clearance stimata, come deve.
- **Errore sistematico con una sola valle.** La stima sovrastima la clearance in media del 5,8%, oltre il margine del 5% che avevamo fissato, quindi prevede valli un po' più basse del vero. Non dipende dal metodo M3: c'è anche nei pazienti con valle dosabile (+5,9%). Viene dal termine ln(varianza) della stima standard, la stessa delle stime individuali FOCE-I dell'articolo. Senza quel termine scenderebbe a +2,3%, con lo stesso errore medio. Con due valli scende a +2,9% e con i prelievi ACT 1 a +1,3%. **Decisione di Alessandro (opzione A):** si tiene il metodo standard e il limite è dichiarato. Per un solo prelievo il margine è stato portato al 10% dopo aver visto il risultato, e lo diciamo apertamente.
- **Margini.** Sono stati fissati prima dei risultati: CL entro il 20% con una valle; entro il 15% con due valli, e almeno dimezzato rispetto a senza misure; entro il 10% con i prelievi ACT 1. V1 entro il 15% con i prelievi ACT 1. Errore sistematico entro ±5%. Mai peggio del modello senza misure.
