# Gemello digitale dell'infliximab (prototipo)

> ⚠️ **PROTOTIPO DIMOSTRATIVO.** Non è un dispositivo medico e non deve mai essere usato per decidere la terapia di pazienti reali.

Un paziente virtuale in cui si vede nel tempo la concentrazione di infliximab nel sangue, calcolata con un modello farmacocinetico pubblicato. Quando inserisci un esame del sangue con il livello del farmaco, il modello si ricalibra su quel paziente (stima bayesiana). Poi puoi confrontare schemi di terapia alternativi ("cosa succederebbe se...").

- **Modello (unica fonte):** Fasanmade AA et al. *Population pharmacokinetic analysis of infliximab in patients with ulcerative colitis.* Eur J Clin Pharmacol 2009;65:1211-28 ([articolo gratuito](https://pmc.ncbi.nlm.nih.gov/articles/PMC2778780/)). È implementato come scritto nelle equazioni finali (p. 1218) e nella Tabella 3.
- **Dati usati solo per il controllo (test 3):** Adedokun OJ et al., Gastroenterology 2014 (doi 10.1053/j.gastro.2014.08.035), livelli misurati negli stessi studi ACT 1 e 2. Questi numeri sono ancora da verificare sull'articolo originale.
- **Controlli:** 178 test automatici (177 superati e 1 difetto noto dichiarato), che girano anche su GitHub a ogni modifica.

## Provarlo

### Dall'iPad, senza computer

Si pubblica l'app in privato su **Streamlit Community Cloud**, gratis e collegata a questo repository. Si fa una volta sola, da Safari:

1. Vai su [share.streamlit.io](https://share.streamlit.io) e accedi con **GitHub**, autorizzando anche l'accesso ai repository privati.
2. Crea una nuova app da GitHub e indica:
   - repository `AlessandroGz-AX/infliximab-twin`;
   - ramo `main`;
   - file principale `app.py`.
3. Se ti viene chiesta la versione di Python, scegli la 3.13 (va bene anche la 3.12).
4. Premi **Deploy**. Dopo qualche minuto ottieni un indirizzo `…streamlit.app`, che puoi aggiungere alla schermata Home dell'iPad.

L'app resta privata perché il repository è privato: per farla vedere a qualcuno usa il pulsante **Share** e inserisci la sua email. Il piano gratuito consente una sola app privata alla volta. A ogni modifica di `main` l'app si aggiorna da sola.

### Sul computer

Serve Python 3.12 o più recente (provato con 3.13). Apri il Terminale nella cartella del progetto.

1. Crea l'ambiente e installa le librerie (solo la prima volta):

   ```bash
   python3 -m venv .venv
   ```

   ```bash
   source .venv/bin/activate
   ```

   Su Windows il secondo comando è `.venv\Scripts\activate`.

   ```bash
   pip install -r requirements.txt
   ```

2. Apri l'app (si apre nel browser):

   ```bash
   streamlit run app.py
   ```

3. Fai girare tutti i test con un solo comando:

   ```bash
   python -m pytest
   ```

   Devi vedere `177 passed, 1 xfailed`: lo `xfailed` è il difetto noto descritto più sotto.

4. Per vedere i risultati dei controlli:
   - `python -m gemello.confronto_articolo`: articolo contro modello;
   - `python -m gemello.validazione`: valori osservati (test 3);
   - `python -m gemello.verifica_stima`: 100 pazienti virtuali (test 4).

## Come si usa l'app

1. **Caso dimostrativo.** Il pulsante in cima alla pagina carica un esempio completo:
   - il paziente tipico, con una valle di 1,2 µg/mL alla settimana 14, dove il modello se ne aspetta circa 3,25;
   - il confronto dalla settimana 14 tra 10 mg/kg ogni 8 settimane e 5 mg/kg ogni 4, con la stessa quantità totale di farmaco.

   Una frase spiega cosa si vede.
2. **Paziente e schema.** Nella barra laterale inserisci peso, sesso, albumina e anticorpi anti-infliximab, poi lo schema di terapia e la soglia (di default 3 µg/mL). La curva mostra le 54 settimane, le concentrazioni minime (valli) e quando scendono sotto la soglia.
3. **Livelli misurati.** Sempre nella barra laterale indica la data della prima infusione, poi data e valore del prelievo, e premi **Aggiungi livello**. Se il referto dice "non dosabile", spunta la casella. La curva si ricalibra sul paziente: in grigio la previsione di partenza, in blu quella aggiornata, e i rombi sono i livelli misurati.
4. **Cosa succederebbe se...** Sotto il grafico attiva il confronto e scegli da quale settimana partono le due alternative, con dose e intervallo di ciascuna. Una tabella confronta lo schema attuale e le due alternative: prima valle sotto soglia e giorni sotto soglia dopo il cambio, ultima valle e farmaco totale.

## Il modello in breve

- **Struttura:** due compartimenti, infusione endovenosa di 2 ore, eliminazione del primo ordine.
- **Equazioni finali (p. 1218):**
  - CL = 0,407 × (albumina/4,1)^−1,54 × 1,471 se anticorpi positivi × 0,764 se donna (L/giorno);
  - V1 = 3,29 × (peso/77)^0,538 × 0,863 se donna (L);
  - V2 = 4,13 L e Q = 7,14 L/giorno.
- **Variabilità tra pazienti:** solo quella della Tabella 3, cioè 37,68% su CL e 22,11% su V1, senza correlazione (l'articolo non ne pubblica il valore).
- **Errore di misura:** combinato, 40,3% proporzionale più 0,0413 µg/mL additivo (Tabella 3).
- **Stima bayesiana:** massima a posteriori su CL e V1. I livelli non dosabili entrano con il metodo M3 (Beal 2001).

## Quanto ci si può fidare: i quattro test

| Test | Cosa controlla | Risultato |
|---|---|---|
| 1 | Paziente tipico | Parametri identici alla Tabella 3. Emivita terminale del paziente tipico 12,9 giorni (la donna tipica 15,8). |
| 2 | Effetti delle covariate | 120 combinazioni di peso, albumina, sesso e anticorpi identiche alle equazioni di p. 1218. |
| 3 | Valori osservati | Emivita mediana su 5.000 pazienti virtuali: 13,7 giorni contro "circa 14" dell'articolo, intervallo 10,2-18,2 contro 10,4-17,8. Il paziente tipico cade tra le mediane di chi rispondeva e di chi non rispondeva negli studi ACT (Adedokun 2014, da verificare). |
| 4 | Stima su 100 pazienti virtuali | Errore medio sulla clearance: dal 33% senza misure al 15% con una valle, al 10% con due, al 6% con i 13 prelievi dello studio ACT 1. Pazienti messi dal lato giusto della soglia di 3 µg/mL: dal 68% all'88% con una sola valle. |

Tutti i dettagli, con le tabelle rigenerate dal codice, sono in [docs/confronto_articolo.md](docs/confronto_articolo.md).

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

## Difetti noti e punti aperti

- **Test 4 con un solo prelievo:** la stima sovrastima la clearance in media del 5,8%, oltre il margine del 5% fissato prima dei risultati. Il test è segnato come difetto noto (`xfail strict`) e il margine non è stato spostato. La causa è il metodo di stima standard, lo stesso delle stime individuali dell'articolo; con due prelievi l'errore scende a +2,9%.
- **Adedokun 2014:** i numeri usati nel test 3 non sono ancora verificati sull'articolo originale.
- **Discrepanze dentro l'articolo:** il testo dice "circa −33%" sulla clearance nelle donne, l'equazione −23,6%; volume allo stato stazionario 7,71 L contro i 7,42 delle tabelle; effetto dell'albumina 19,1% contro 21,0%. Vale l'equazione.
- **Nessuna validazione su pazienti reali:** tutte le verifiche sono su pazienti virtuali o su valori riassuntivi pubblicati.

## Cosa c'è dentro

- `app.py`: l'app.
- `gemello/modello.py`: parametri ed equazioni dell'articolo. Ogni numero ha accanto la pagina o la tabella da cui viene.
- `gemello/simulazione.py`: schema di terapia (anche con cambio da una certa settimana), concentrazione con la formula esatta, valli, periodi sotto soglia.
- `gemello/stima.py`: stima bayesiana dai livelli misurati.
- `gemello/grafici.py`: i grafici.
- `gemello/popolazione.py`, `gemello/validazione.py`, `gemello/verifica_stima.py`: popolazione virtuale e controlli (test 3 e 4).
- `gemello/confronto_articolo.py`, `gemello/documentazione.py`: tabella articolo contro modello, e rigenerazione dei documenti dal codice.
- `docs/confronto_articolo.md`: discrepanze, punti non chiari e risultati dei controlli.
- `tests/`: i test.
- `.github/workflows/test.yml`: i test su GitHub a ogni modifica.
- `.streamlit/config.toml`: impostazioni dell'app.
- `CLAUDE.md`: obiettivo, regole e decisioni del progetto, per le prossime sessioni di lavoro.

## Stato del progetto

Passi 0-6 completati: modello, simulatore, stima bayesiana, app, livelli misurati, schemi alternativi, documentazione.
