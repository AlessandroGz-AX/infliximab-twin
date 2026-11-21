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
| 3 | Stima bayesiana + test 4 | da fare |
| 4 | App Streamlit | da fare |
| 5 | Misure del paziente e schema alternativo | da fare |
| 6 | README finale e bilancio | da fare |

## Limiti del modello

<!-- inizio limiti -->
- Variabilità tra pazienti presa solo dalla Tabella 3 dell'articolo: 37,68% sulla clearance (CL) e 22,11% sul volume centrale (V1), senza correlazione tra le due e senza variabilità su V2 e Q. L'articolo dice che una correlazione CL-V1 era stimata, ma non ne pubblica il valore.
- Il modello viene da adulti (18-81 anni) con colite ulcerosa da moderata a grave, trattati negli studi ACT 1 e ACT 2 con 5 o 10 mg/kg: non vale automaticamente per altre malattie, per i bambini o per altri dosaggi.
- Gli anticorpi anti-infliximab sono un sì/no valido per tutta la terapia, come nell'articolo, non dal momento in cui compaiono.
- Peso e albumina sono i valori di partenza e restano costanti per tutta la simulazione, come nell'articolo.
<!-- fine limiti -->

Le discrepanze trovate dentro l'articolo e i risultati dei controlli sono in [docs/confronto_articolo.md](docs/confronto_articolo.md).

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

5. L'app arriverà al passo 4 e si aprirà con `streamlit run app.py`.

## Cosa c'è dentro

- `gemello/modello.py`: parametri ed equazioni dell'articolo. Ogni numero ha accanto la pagina o la tabella da cui viene.
- `gemello/simulazione.py`: concentrazione nel tempo per uno schema di terapia, valli, periodi sotto soglia.
- `gemello/popolazione.py`: popolazione virtuale simile a quella degli studi (serve per i controlli).
- `gemello/validazione.py`: confronto con i valori osservati (test 3).
- `gemello/confronto_articolo.py`: tabella "articolo contro modello".
- `gemello/documentazione.py`: rigenera le tabelle dei documenti dal codice.
- `docs/confronto_articolo.md`: discrepanze, punti non chiari e risultati dei controlli.
- `tests/`: i test.
- `CLAUDE.md`: obiettivo e regole del progetto, per le prossime sessioni di lavoro.
