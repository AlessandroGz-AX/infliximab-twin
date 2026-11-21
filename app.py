"""
Gemello digitale dell'infliximab: app dimostrativa.

Avvio, dalla cartella del progetto:
    streamlit run app.py

PROTOTIPO DIMOSTRATIVO: non usare per decidere la terapia di pazienti reali.
"""

import re

import pandas as pd
import streamlit as st

from gemello import AVVERTENZA, LIMITI
from gemello import modello as m
from gemello import simulazione as sim
from gemello.grafici import grafico_concentrazione

DURATA_SETTIMANE = 54.0

st.set_page_config(page_title="Gemello digitale dell'infliximab", page_icon="💉",
                   layout="wide")


def numero(x: float, decimali: int = 1) -> str:
    """Numero con la virgola decimale all'italiana."""
    return f"{x:.{decimali}f}".replace(".", ",")


def leggi_settimane(testo: str) -> list[float]:
    """Da "0, 2, 6" a [0, 2, 6]; controlla che i valori abbiano senso."""
    parti = [p for p in re.split(r"[,;\s]+", testo.strip()) if p]
    try:
        settimane = sorted({float(p) for p in parti})
    except ValueError:
        raise ValueError("Scrivi le settimane come numeri separati da virgole, "
                         "per esempio: 0, 2, 6") from None
    if not settimane or settimane[0] != 0:
        raise ValueError("La prima infusione deve essere alla settimana 0.")
    if settimane[-1] >= DURATA_SETTIMANE:
        raise ValueError(f"Le settimane iniziali devono essere prima della {DURATA_SETTIMANE:g}.")
    return settimane


def tema_attuale() -> str:
    try:
        return "scuro" if st.context.theme.type == "dark" else "chiaro"
    except Exception:  # in alcuni contesti (es. test) il tema non è disponibile
        return "chiaro"


# ---------------------------------------------------------------------
# Intestazione e avvertenza, sempre in vista
# ---------------------------------------------------------------------
st.title("Gemello digitale dell'infliximab")
st.error(f"**{AVVERTENZA}**", icon="⚠️")
st.caption("Paziente virtuale: concentrazione di infliximab nel sangue calcolata con il "
           "modello di popolazione di Fasanmade et al., Eur J Clin Pharmacol 2009 "
           "(adulti con colite ulcerosa). I limiti del modello sono in fondo alla pagina.")

# ---------------------------------------------------------------------
# Dati inseriti dall'utente (barra laterale)
# ---------------------------------------------------------------------
with st.sidebar:
    st.header("Paziente")
    peso = st.number_input("Peso (kg)", min_value=20.0, max_value=250.0, value=77.0, step=1.0,
                           format="%.0f")
    sesso = st.radio("Sesso", ["Uomo", "Donna"], horizontal=True)
    albumina = st.number_input("Albumina (g/dL)", min_value=1.0, max_value=6.5, value=4.1,
                               step=0.1, format="%.1f",
                               help="Albumina nel sangue prima della terapia. "
                                    "41 g/L corrispondono a 4,1 g/dL.")
    anticorpi = st.toggle("Anticorpi anti-infliximab positivi")

    st.header("Schema di terapia")
    mg_per_kg = st.number_input("Dose per infusione (mg/kg)", min_value=1.0, max_value=20.0,
                                value=5.0, step=0.5, format="%.1f")
    testo_induzione = st.text_input("Settimane delle infusioni iniziali", value="0, 2, 6")
    intervallo = st.number_input("Poi un'infusione ogni (settimane)", min_value=1, max_value=16,
                                 value=8, step=1)

    st.header("Soglia")
    soglia = st.number_input("Soglia della concentrazione minima (µg/mL)", min_value=0.1,
                             max_value=50.0, value=3.0, step=0.5, format="%.1f")

    st.header("Grafico")
    scala_log = st.toggle("Scala logaritmica", value=True,
                          help="Fa vedere bene sia i picchi dopo l'infusione sia i valori "
                               "minimi vicino alla soglia.")

try:
    settimane_induzione = leggi_settimane(testo_induzione)
except ValueError as errore:
    st.error(str(errore))
    st.stop()

# ---------------------------------------------------------------------
# Calcoli (tutto il modello sta in gemello/)
# ---------------------------------------------------------------------
paziente = m.Paziente(peso_kg=peso, donna=(sesso == "Donna"), albumina_g_dl=albumina,
                      anticorpi=anticorpi)
for avviso in m.avvisi_estrapolazione(paziente):
    st.warning(avviso, icon="⚠️")

parametri = m.parametri_tipici(paziente)
schema = sim.Schema(mg_per_kg=mg_per_kg, settimane_induzione=tuple(settimane_induzione),
                    intervallo_mantenimento_settimane=float(intervallo),
                    durata_settimane=DURATA_SETTIMANE)
settimane, concentrazioni = sim.curva(parametri, schema, peso)
valli = sim.concentrazioni_minime(parametri, schema, peso)
prima_sotto = sim.primo_minimo_sotto_soglia(valli, soglia)
periodi_sotto = sim.periodi_sotto_soglia(parametri, schema, peso, soglia)
giorni_sotto = sum(fine - inizio for inizio, fine in periodi_sotto) * 7

# ---------------------------------------------------------------------
# Risultato principale, in parole
# ---------------------------------------------------------------------
if prima_sotto is None:
    st.success(f"Con questo schema la concentrazione minima resta sempre sopra la soglia "
               f"di {numero(soglia)} µg/mL.", icon="✅")
else:
    settimana, valore = prima_sotto
    st.warning(f"La concentrazione minima scende sotto la soglia di {numero(soglia)} µg/mL "
               f"alla settimana {settimana:g} ({numero(valore, 2)} µg/mL). In "
               f"{DURATA_SETTIMANE:g} settimane resta sotto soglia per circa "
               f"{giorni_sotto:.0f} giorni in tutto.", icon="⚠️")

colonne = st.columns(4)
colonne[0].metric("Prima valle sotto soglia",
                  "Nessuna" if prima_sotto is None else f"Sett. {prima_sotto[0]:g}")
if valli:
    colonne[1].metric(f"Valle alla settimana {valli[-1][0]:g}",
                      f"{numero(valli[-1][1], 2)} µg/mL")
colonne[2].metric("Giorni sotto soglia", f"{giorni_sotto:.0f}",
                  help=f"Totale nelle {DURATA_SETTIMANE:g} settimane simulate.")
colonne[3].metric("Emivita terminale", f"{numero(m.emivita_terminale_giorni(parametri))} giorni")

st.subheader("Concentrazione nel sangue, prime 54 settimane")
st.altair_chart(grafico_concentrazione(settimane, concentrazioni, valli, soglia,
                                       scala_log=scala_log, tema=tema_attuale(),
                                       durata_settimane=DURATA_SETTIMANE),
                width="stretch")
st.caption("Ogni dente della curva è un'infusione di 2 ore. I punti sono le concentrazioni "
           "minime (valli), subito prima dell'infusione successiva.")

with st.expander("Tabella delle concentrazioni minime (valli)"):
    st.dataframe(pd.DataFrame({
        "Settimana": [f"{s:g}" for s, _ in valli],
        "Concentrazione minima (µg/mL)": [numero(v, 2) for _, v in valli],
        "Rispetto alla soglia": ["sotto soglia" if v < soglia else "sopra soglia"
                                 for _, v in valli],
    }), hide_index=True)

# ---------------------------------------------------------------------
# Parametri del paziente e limiti
# ---------------------------------------------------------------------
st.subheader("Parametri di questo paziente secondo il modello")
tipici = m.parametri_tipici(m.PAZIENTE_TIPICO)
st.dataframe(pd.DataFrame({
    "Parametro": ["Clearance (CL)", "Volume centrale (V1)", "Volume periferico (V2)",
                  "Clearance intercompartimentale (Q)"],
    "Questo paziente": [f"{numero(parametri.CL, 3)} L/giorno", f"{numero(parametri.V1, 2)} L",
                        f"{numero(parametri.V2, 2)} L", f"{numero(parametri.Q, 2)} L/giorno"],
    "Paziente tipico dell'articolo": [f"{numero(tipici.CL, 3)} L/giorno",
                                      f"{numero(tipici.V1, 2)} L", f"{numero(tipici.V2, 2)} L",
                                      f"{numero(tipici.Q, 2)} L/giorno"],
}), hide_index=True)
st.caption("Valori attesi per un paziente con queste caratteristiche, prima di conoscere i suoi "
           "livelli di farmaco. Paziente tipico: uomo, 77 kg, albumina 4,1 g/dL, senza "
           "anticorpi.")

st.subheader("Limiti del modello")
st.markdown("\n".join(f"- {limite}" for limite in LIMITI))

with st.expander("Il modello e la fonte"):
    st.markdown(
        "Modello a due compartimenti con infusione endovenosa di 2 ore ed eliminazione del "
        "primo ordine. Equazioni del modello finale (p. 1218 dell'articolo):\n\n"
        "- CL = 0,407 × (albumina/4,1)^−1,54 × 1,471 se anticorpi positivi × 0,764 se donna\n"
        "- V1 = 3,29 × (peso/77)^0,538 × 0,863 se donna\n"
        "- Q = 7,14 L/giorno; V2 = 4,13 L\n\n"
        "Fonte: Fasanmade AA et al. *Population pharmacokinetic analysis of infliximab in "
        "patients with ulcerative colitis.* Eur J Clin Pharmacol 2009;65:1211-28 "
        "([articolo gratuito](https://pmc.ncbi.nlm.nih.gov/articles/PMC2778780/)).")
