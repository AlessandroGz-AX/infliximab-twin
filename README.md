# Gemello digitale dell'infliximab (prototipo)

> ⚠️ **PROTOTIPO DIMOSTRATIVO.** Non è un dispositivo medico e non deve mai essere usato per decidere la terapia di pazienti reali.

Un paziente virtuale in cui si vede nel tempo la concentrazione di infliximab nel sangue, calcolata con un modello farmacocinetico pubblicato. Il modello si aggiorna quando si inserisce un livello di farmaco misurato.

**Modello (unica fonte):** Fasanmade AA et al. *Population pharmacokinetic analysis of infliximab in patients with ulcerative colitis.* Eur J Clin Pharmacol 2009;65:1211-28 ([articolo gratuito](https://pmc.ncbi.nlm.nih.gov/articles/PMC2778780/)).

**Dati usati solo per il controllo (test 3):** Adedokun OJ et al., Gastroenterology 2014 (doi 10.1053/j.gastro.2014.08.035), livelli misurati negli studi ACT 1 e 2. Numeri ancora da verificare sull'articolo originale.

## A che punto siamo

| Passo | Contenuto | Stato |
|---|---|---|
| 0 | Preparazione | fatto |
| 1 | Modello dell'articolo + test 1 e 2 | fatto |
| 2 | Simulatore a 54 settimane + test 3 | fatto |
| 3 | Stima bayesiana + test 4 | fatto |
| 4 | App Streamlit | fatto |
| 5 | Misure del paziente e schema alternativo | da fare |
| 6 | README finale e bilancio | da fare |

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

Le discrepanze trovate dentro l'articolo e i risultati dei controlli sono in [docs/confronto_articolo.md](docs/confronto_articolo.md).

## Aprire l'app dall'iPad (senza computer)

Si pubblica l'app in privato su **Streamlit Community Cloud**, gratis e collegata a questo repository. Si fa una volta sola, da Safari:

1. Vai su [share.streamlit.io](https://share.streamlit.io) e accedi con **GitHub**, autorizzando anche l'accesso ai repository privati.
2. Crea una nuova app da GitHub e indica:
   - repository `AlessandroGz-AX/infliximab-twin`;
   - ramo `main`;
   - file principale `app.py`.
3. Se ti viene chiesta la versione di Python, scegli la 3.13 (va bene anche la 3.12).
4. Premi **Deploy**. Dopo qualche minuto ottieni un indirizzo `…streamlit.app`, che puoi aggiungere alla schermata Home dell'iPad.

L'app resta privata perché il repository è privato: per farla vedere a qualcuno usa il pulsante **Share** e inserisci la sua email. Il piano gratuito consente una sola app privata alla volta. A ogni modifica di `main` l'app si aggiorna da sola.

## I test girano anche da soli su GitHub

A ogni modifica di `main`, GitHub fa girare tutti i test. Sulla pagina del repository, accanto all'ultima modifica, compare un segno verde se è tutto a posto e una croce rossa se qualcosa non va. I dettagli sono nella scheda **Actions**, visibile anche da iPad o telefono.

## Come provarlo sul tuo computer

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

2. Fai girare tutti i test:

   ```bash
   python -m pytest
   ```

   Devi vedere `passed` e nessun `failed`.

3. Guarda il confronto tra modello e articolo:

   ```bash
   python -m gemello.confronto_articolo
   ```

4. Guarda il confronto con i livelli osservati negli studi (test 3):

   ```bash
   python -m gemello.validazione
   ```

5. Guarda quanto sbaglia la stima bayesiana su 100 pazienti virtuali (test 4):

   ```bash
   python -m gemello.verifica_stima
   ```

6. Apri l'app (si apre nel browser):

   ```bash
   streamlit run app.py
   ```

## Cosa c'è dentro

- `app.py`: l'app (dati del paziente, schema di terapia, curva, soglia, valli, limiti).
- `gemello/grafici.py`: il grafico della concentrazione.
- `.streamlit/config.toml`: impostazioni dell'app.
- `gemello/modello.py`: parametri ed equazioni dell'articolo. Ogni numero ha accanto la pagina o la tabella da cui viene.
- `gemello/simulazione.py`: concentrazione nel tempo per uno schema di terapia, valli, periodi sotto soglia.
- `gemello/popolazione.py`: popolazione virtuale simile a quella degli studi (serve per i controlli).
- `gemello/validazione.py`: confronto con i valori osservati (test 3).
- `gemello/stima.py`: stima bayesiana (massima a posteriori) dei parametri di un paziente dai suoi livelli misurati.
- `gemello/verifica_stima.py`: simulazione e stima su 100 pazienti virtuali (test 4).
- `gemello/confronto_articolo.py`: tabella "articolo contro modello".
- `gemello/documentazione.py`: rigenera le tabelle dei documenti dal codice.
- `docs/confronto_articolo.md`: discrepanze, punti non chiari e risultati dei controlli.
- `tests/`: i test.
- `.github/workflows/test.yml`: fa girare i test su GitHub a ogni modifica.
- `CLAUDE.md`: obiettivo e regole del progetto, per le prossime sessioni di lavoro.
