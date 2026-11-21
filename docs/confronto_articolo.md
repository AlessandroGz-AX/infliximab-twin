# Confronto tra modello e articolo

Fonte: Fasanmade AA et al. *Population pharmacokinetic analysis of infliximab in patients with ulcerative colitis.* Eur J Clin Pharmacol 2009;65:1211-28.

Il modello segue **le equazioni finali (p. 1218) e la Tabella 3**. Quando una frase riassuntiva del testo non torna con le equazioni la segnaliamo come DIVERSO, ma non modifichiamo il modello per farla tornare.

La tabella si rigenera con `python -m gemello.confronto_articolo`. Un test controlla che questa pagina sia allineata al codice.

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

## Punti che l'articolo non chiarisce

1. **Variabilità tra pazienti (IIV).** La Tabella 3 riporta 37,68% su CL, 22,11% su V1 e "–" su V2 e Q. Però:
   - a p. 1216 il testo dice che su CL e V1 era stimata una matrice di varianza-covarianza "piena", cioè anche una correlazione tra i due. Il valore di quella correlazione non è pubblicato;
   - la stessa frase dice che per V2 e Q era stato assunto un blocco "simile". In più, a p. 1216 c'è lo shrinkage anche per V2 (29,2%) e Q (58,9%), possibile solo se su quei parametri c'era variabilità;
   - non è scritto con quale formula le varianze sono state convertite in percentuali.

   Decisione chiesta ad Alessandro: vedi "Domande aperte" in `CLAUDE.md`.

2. **Concentrazioni numeriche per il Test 3.** L'articolo non riporta concentrazioni osservate o simulate in forma di numeri, per esempio la mediana delle concentrazioni minime a una certa settimana. Ci sono solo grafici: la Fig. 7 mostra 4 pazienti rappresentativi, ma non i loro parametri individuali. Gli unici valori quantitativi confrontabili sono l'emivita mediana (circa 14 giorni, intervallo interquartile 10,4-17,8, p. 1221) e il volume allo stato stazionario (7,71 L, p. 1221).
