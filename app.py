"""
Gemello digitale dell'infliximab: app dimostrativa.

Avvio, dalla cartella del progetto:
    streamlit run app.py

PROTOTIPO DIMOSTRATIVO: non usare per decidere la terapia di pazienti reali.
"""

import re
from datetime import date, timedelta

import numpy as np
import pandas as pd
import streamlit as st

from gemello import AVVERTENZA, LIMITI
from gemello import modello as m
from gemello import simulazione as sim
from gemello.grafici import grafico_concentrazione, grafico_confronto
from gemello.stima import Misura, stima_map

DURATA_SETTIMANE = 54.0
# Esempio dimostrativo: una valle più bassa del previsto alla settimana 14.
SETTIMANA_ESEMPIO, LIVELLO_ESEMPIO = 14, 1.2

st.set_page_config(page_title="Gemello digitale dell'infliximab", page_icon="💉",
                   layout="wide")


def numero(x: float, decimali: int = 1) -> str:
    """Numero con la virgola decimale all'italiana."""
    return f"{x:.{decimali}f}".replace(".", ",")


def variazione(rapporto: float, maschile: bool = False) -> str:
    """Da un rapporto (es. 1,45) a una frase (es. "più alta del 45%")."""
    percento = (rapporto - 1) * 100
    if abs(percento) < 0.5:
        return "praticamente uguale"
    alta, bassa = ("alto", "basso") if maschile else ("alta", "bassa")
    return f"più {alta if percento > 0 else bassa} del {abs(percento):.0f}%"


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


def riassunto(parametri: m.ParametriPK, piano, peso: float, soglia: float) -> dict:
    """Numeri chiave di uno schema di terapia per un paziente."""
    valli = sim.concentrazioni_minime(parametri, piano, peso)
    periodi = sim.periodi_sotto_soglia(parametri, piano, peso, soglia)
    return dict(valli=valli, prima_sotto=sim.primo_minimo_sotto_soglia(valli, soglia),
                giorni_sotto=sum(fine - inizio for inizio, fine in periodi) * 7,
                dose_totale=sim.dose_totale_mg(piano, peso))


st.session_state.setdefault("livelli", [])  # livelli misurati inseriti dall'utente
oggi = date.today()

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

    st.header("Livelli misurati")
    st.caption("Esami del sangue con il livello di infliximab. Si assume che le infusioni "
               "siano state fatte come nello schema qui sopra.")
    data_prima = st.date_input("Data della prima infusione", value=oggi - timedelta(weeks=24),
                               format="DD/MM/YYYY", key="data_prima")
    data_prelievo = st.date_input(
        "Data del prelievo", value=oggi - timedelta(weeks=10), format="DD/MM/YYYY",
        key="data_prelievo",
        help="Un prelievo fatto il giorno di un'infusione vale come fatto prima "
             "dell'infusione (concentrazione minima).")
    valore = st.number_input("Livello misurato (µg/mL)", min_value=0.0, max_value=1000.0,
                             value=1.0, step=0.1, format="%.2f", key="valore_livello")
    non_dosabile = st.checkbox("Non dosabile (sotto 0,1 µg/mL)", key="non_dosabile")
    colonna_a, colonna_b = st.columns(2)
    if colonna_a.button("Aggiungi", key="aggiungi", type="primary", width="stretch"):
        giorno = (data_prelievo - data_prima).days
        if giorno <= 0:
            st.error("Il prelievo deve essere successivo alla prima infusione.")
        elif giorno > DURATA_SETTIMANE * 7:
            st.error(f"Il prelievo deve cadere entro {DURATA_SETTIMANE:g} settimane "
                     "dalla prima infusione.")
        else:
            sotto = non_dosabile or valore < m.LLOQ
            st.session_state.livelli.append(dict(data=data_prelievo,
                                                 valore=0.0 if sotto else valore,
                                                 non_dosabile=sotto))
    if colonna_b.button("Esempio", key="esempio", width="stretch",
                        help=f"Aggiunge una valle di {numero(LIVELLO_ESEMPIO)} µg/mL alla "
                             f"settimana {SETTIMANA_ESEMPIO}."):
        st.session_state.livelli.append(dict(
            data=data_prima + timedelta(weeks=SETTIMANA_ESEMPIO),
            valore=LIVELLO_ESEMPIO, non_dosabile=False))

    for i, livello in enumerate(list(st.session_state.livelli)):
        settimana = (livello["data"] - data_prima).days / 7
        testo = "non dosabile" if livello["non_dosabile"] else f"{numero(livello['valore'], 2)} µg/mL"
        riga_testo, riga_pulsante = st.columns([5, 1], vertical_alignment="center")
        riga_testo.markdown(f"{livello['data']:%d/%m/%Y} · sett. {numero(settimana)} · {testo}")
        if riga_pulsante.button("✕", key=f"rimuovi_{i}", help="Togli questo livello"):
            st.session_state.livelli.pop(i)
            st.rerun()
    if st.session_state.livelli and st.button("Togli tutti i livelli", key="togli_tutti"):
        st.session_state.livelli = []
        st.rerun()

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

schema = sim.Schema(mg_per_kg=mg_per_kg, settimane_induzione=tuple(settimane_induzione),
                    intervallo_mantenimento_settimane=float(intervallo),
                    durata_settimane=DURATA_SETTIMANE)
parametri_prima = m.parametri_tipici(paziente)

# Livelli misurati -> stima bayesiana (massima a posteriori)
misure, punti_misurati, fuori = [], [], 0
for livello in st.session_state.livelli:
    giorno = (livello["data"] - data_prima).days
    if 0 < giorno <= DURATA_SETTIMANE * 7:
        misure.append(Misura(giorno, livello["valore"]))
        punti_misurati.append((giorno / 7, livello["valore"], livello["non_dosabile"]))
    else:
        fuori += 1
if fuori:
    st.warning(f"{fuori} livelli cadono fuori dalle {DURATA_SETTIMANE:g} settimane dalla prima "
               "infusione e non vengono usati.", icon="⚠️")

if misure:
    stima = stima_map(paziente, schema.dosi(peso), misure)
    parametri = stima.parametri
else:
    stima, parametri = None, parametri_prima

settimane, concentrazioni = sim.curva(parametri, schema, peso)
curva_prima = sim.curva(parametri_prima, schema, peso)[1] if misure else None
attuale = riassunto(parametri, schema, peso, soglia)
valli, prima_sotto, giorni_sotto = attuale["valli"], attuale["prima_sotto"], attuale["giorni_sotto"]

# ---------------------------------------------------------------------
# Risultato principale, in parole
# ---------------------------------------------------------------------
if misure:
    st.info(f"Curva aggiornata con {len(misure)} "
            f"{'livello misurato' if len(misure) == 1 else 'livelli misurati'} (stima bayesiana). "
            f"Rispetto a quanto previsto per questo paziente, la clearance stimata è "
            f"{variazione(parametri.CL / parametri_prima.CL)} e il volume centrale "
            f"{variazione(parametri.V1 / parametri_prima.V1, maschile=True)}.",
            icon="🩸")
    if stima.sotto_limite:
        st.caption("I livelli non dosabili sono usati come informazione \"sotto 0,1 µg/mL\" "
                   "(metodo M3).")

if prima_sotto is None:
    st.success(f"Con questo schema la concentrazione minima resta sempre sopra la soglia "
               f"di {numero(soglia)} µg/mL.", icon="✅")
else:
    settimana, valore_valle = prima_sotto
    st.warning(f"La concentrazione minima scende sotto la soglia di {numero(soglia)} µg/mL "
               f"alla settimana {settimana:g} ({numero(valore_valle, 2)} µg/mL). In "
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
                                       durata_settimane=DURATA_SETTIMANE,
                                       curva_prima=curva_prima, misure=punti_misurati),
                width="stretch")
st.caption("Ogni dente della curva è un'infusione di 2 ore. I punti tondi sono le "
           "concentrazioni minime (valli), subito prima dell'infusione successiva."
           + (" I rombi sono i livelli misurati; in grigio la previsione prima delle misure "
              "(modello di popolazione)." if misure else ""))

with st.expander("Tabella delle concentrazioni minime (valli)"):
    st.dataframe(pd.DataFrame({
        "Settimana": [f"{s:g}" for s, _ in valli],
        "Concentrazione minima (µg/mL)": [numero(v, 2) for _, v in valli],
        "Rispetto alla soglia": ["sotto soglia" if v < soglia else "sopra soglia"
                                 for _, v in valli],
    }), hide_index=True)

# ---------------------------------------------------------------------
# Cosa succederebbe se...
# ---------------------------------------------------------------------
st.subheader("Cosa succederebbe se...")
st.caption("Confronta lo schema attuale con un'alternativa che parte da una certa settimana. "
           "Il confronto usa la curva "
           + ("aggiornata con i livelli misurati." if misure else "del modello di popolazione."))
if st.toggle("Confronta con uno schema alternativo", key="confronta"):
    a, b, c = st.columns(3)
    settimana_cambio = a.number_input("Dalla settimana", min_value=1,
                                      max_value=int(DURATA_SETTIMANE) - 1, value=14, step=1,
                                      key="settimana_cambio")
    nuova_dose = b.number_input("Nuova dose (mg/kg)", min_value=1.0, max_value=20.0,
                                value=10.0, step=0.5, format="%.1f", key="nuova_dose")
    nuovo_intervallo = c.number_input("Un'infusione ogni (settimane)", min_value=1,
                                      max_value=16, value=8, step=1, key="nuovo_intervallo")
    alternativo = sim.SchemaConCambio(base=schema, settimana_cambio=float(settimana_cambio),
                                      mg_per_kg=nuova_dose,
                                      intervallo_settimane=float(nuovo_intervallo))
    altro = riassunto(parametri, alternativo, peso, soglia)

    # Stessa griglia di tempi per le due curve (servono gli istanti di entrambi gli schemi).
    tempi = np.union1d(sim.curva(parametri, schema, peso)[0],
                       sim.curva(parametri, alternativo, peso)[0])
    giorni = tempi * sim.GIORNI_PER_SETTIMANA
    conc_attuale = sim.concentrazione(giorni, parametri, schema.dosi(peso))
    conc_alternativo = sim.concentrazione(giorni, parametri, alternativo.dosi(peso))

    def colonna(r) -> list[str]:
        ultima = (f"{numero(r['valli'][-1][1], 2)} µg/mL (sett. {r['valli'][-1][0]:g})"
                  if r["valli"] else "-")
        return ["Nessuna" if r["prima_sotto"] is None else f"Settimana {r['prima_sotto'][0]:g}",
                f"{r['giorni_sotto']:.0f}", ultima,
                f"{r['dose_totale']:,.0f} mg".replace(",", ".")]

    st.dataframe(pd.DataFrame({
        "": ["Prima valle sotto soglia", "Giorni sotto soglia", "Ultima valle",
             f"Farmaco totale in {DURATA_SETTIMANE:g} settimane"],
        "Schema attuale": colonna(attuale),
        "Schema alternativo": colonna(altro),
    }), hide_index=True)
    st.altair_chart(grafico_confronto(tempi, conc_attuale, conc_alternativo, soglia,
                                      scala_log=scala_log, tema=tema_attuale(),
                                      durata_settimane=DURATA_SETTIMANE),
                    width="stretch")

# ---------------------------------------------------------------------
# Parametri del paziente e limiti
# ---------------------------------------------------------------------
st.subheader("Parametri di questo paziente secondo il modello")


def formatta(p: m.ParametriPK) -> list[str]:
    return [f"{numero(p.CL, 3)} L/giorno", f"{numero(p.V1, 2)} L", f"{numero(p.V2, 2)} L",
            f"{numero(p.Q, 2)} L/giorno"]


tabella = {"Parametro": ["Clearance (CL)", "Volume centrale (V1)", "Volume periferico (V2)",
                         "Clearance intercompartimentale (Q)"],
           "Prima dei livelli misurati": formatta(parametri_prima)}
if misure:
    tabella["Dopo i livelli misurati"] = formatta(parametri)
tabella["Paziente tipico dell'articolo"] = formatta(m.parametri_tipici(m.PAZIENTE_TIPICO))
st.dataframe(pd.DataFrame(tabella), hide_index=True)
st.caption("\"Prima\" = valori attesi per un paziente con queste caratteristiche. \"Dopo\" = "
           "stima bayesiana che tiene conto dei livelli misurati (cambiano solo CL e V1, gli "
           "unici con variabilità tra pazienti). Paziente tipico: uomo, 77 kg, albumina "
           "4,1 g/dL, senza anticorpi.")

st.subheader("Limiti del modello")
st.markdown("\n".join(f"- {limite}" for limite in LIMITI))

with st.expander("Il modello e la fonte"):
    st.markdown(
        "Modello a due compartimenti con infusione endovenosa di 2 ore ed eliminazione del "
        "primo ordine. Equazioni del modello finale (p. 1218 dell'articolo):\n\n"
        "- CL = 0,407 × (albumina/4,1)^−1,54 × 1,471 se anticorpi positivi × 0,764 se donna\n"
        "- V1 = 3,29 × (peso/77)^0,538 × 0,863 se donna\n"
        "- Q = 7,14 L/giorno; V2 = 4,13 L\n\n"
        "Stima bayesiana (massima a posteriori) con la variabilità tra pazienti e l'errore di "
        "misura della Tabella 3.\n\n"
        "Fonte: Fasanmade AA et al. *Population pharmacokinetic analysis of infliximab in "
        "patients with ulcerative colitis.* Eur J Clin Pharmacol 2009;65:1211-28 "
        "([articolo gratuito](https://pmc.ncbi.nlm.nih.gov/articles/PMC2778780/)).")
