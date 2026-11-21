# Gemello digitale dell'infliximab (prototipo)

> ⚠️ **PROTOTIPO DIMOSTRATIVO.** Non è un dispositivo medico e non deve mai essere usato per decidere la terapia di pazienti reali.

Un paziente virtuale in cui si vede nel tempo la concentrazione di infliximab nel sangue, calcolata con un modello farmacocinetico pubblicato. Il modello si aggiorna quando si inserisce un livello di farmaco misurato.

**Modello (unica fonte):** Fasanmade AA et al. *Population pharmacokinetic analysis of infliximab in patients with ulcerative colitis.* Eur J Clin Pharmacol 2009;65:1211-28 ([articolo gratuito](https://pmc.ncbi.nlm.nih.gov/articles/PMC2778780/)).

## A che punto siamo

| Passo | Contenuto | Stato |
|---|---|---|
| 0 | Preparazione | fatto |
| 1 | Modello dell'articolo + test 1 e 2 | fatto |
| 2 | Simulatore a 54 settimane + test 3 | da fare |
| 3 | Stima bayesiana + test 4 | da fare |
| 4 | App Streamlit | da fare |
| 5 | Misure del paziente e schema alternativo | da fare |
| 6 | README finale e bilancio | da fare |

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

4. L'app arriverà al passo 4 e si aprirà con `streamlit run app.py`.

## Cosa c'è dentro

- `gemello/modello.py`: parametri ed equazioni dell'articolo. Ogni numero ha accanto la pagina o la tabella da cui viene.
- `gemello/confronto_articolo.py`: tabella "articolo contro modello".
- `docs/confronto_articolo.md`: discrepanze e punti non chiari trovati nell'articolo.
- `tests/`: i test.
- `CLAUDE.md`: obiettivo e regole del progetto, per le prossime sessioni di lavoro.
