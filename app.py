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
from gemello.verifica_stima import DISEGNI, ERRORE_CL_DICHIARATO

DURATA_SETTIMANE = 54.0
OGGI = date.today()

# Valori di partenza di tutti i campi dell'app (chiave del campo -> valore).
PARTENZA = dict(
    peso=77.0, sesso="Uomo", albumina=4.1, anticorpi=False,
    mg_per_kg=5.0, induzione="0, 2, 6", intervallo=8, soglia=3.0,
    data_prima=OGGI - timedelta(weeks=24), data_prelievo=OGGI - timedelta(weeks=10),
    valore_livello=1.0, non_dosabile=False, scala_log=True,
    confronta=False, settimana_cambio=14,
    dose_a=10.0, intervallo_a=8, dose_b=5.0, intervallo_b=4,
)

# Caso dimostrativo: paziente tipico con una valle di 1,2 µg/mL alla settimana 14
# (il modello se ne aspetta circa 3,25), poi confronto dalla settimana 14 tra
# 10 mg/kg ogni 8 settimane e 5 mg/kg ogni 4 (stessa quantità totale di farmaco).
SETTIMANA_DEMO, LIVELLO_DEMO = 14, 1.2
CASO_DIMOSTRATIVO = dict(PARTENZA, confronta=True)
CHIAVI_CHE_CONTANO = ["peso", "sesso", "albumina", "anticorpi", "mg_per_kg", "induzione",
                      "intervallo", "soglia", "confronta", "settimana_cambio", "dose_a",
                      "intervallo_a", "dose_b", "intervallo_b"]

st.set_page_config(page_title="Gemello digitale dell'infliximab", page_icon="💉",
                   layout="wide")
for chiave, valore in PARTENZA.items():
    st.session_state.setdefault(chiave, valore)
st.session_state.setdefault("livelli", [])  # livelli misurati inseriti dall'utente


def numero(x: float, decimali: int = 1) -> str:
    """Numero con la virgola decimale all'italiana."""
    return f"{x:.{decimali}f}".replace(".", ",")


def dose_testo(mg_per_kg: float, ogni: float) -> str:
    """Es. "7,5 mg/kg ogni 6 sett." (virgola decimale solo nei numeri)."""
    def g(x: float) -> str:
        return f"{x:g}".replace(".", ",")
    return f"{g(mg_per_kg)} mg/kg ogni {g(ogni)} sett."


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


def riassunto(parametri: m.ParametriPK, piano, peso: float, soglia: float,
              dopo_settimana: float | None = None) -> dict:
    """Numeri chiave di uno schema; con `dopo_settimana` conta solo il tempo successivo."""
    valli = sim.concentrazioni_minime(parametri, piano, peso)
    periodi = sim.periodi_sotto_soglia(parametri, piano, peso, soglia)
    return dict(valli=valli,
                prima_sotto=sim.primo_minimo_sotto_soglia(valli, soglia, dopo_settimana),
                giorni_sotto=sim.giorni_sotto_soglia(periodi, dopo_settimana or 0.0),
                dose_totale=sim.dose_totale_mg(piano, peso))


def carica_caso_dimostrativo() -> None:
    """Riporta tutti i campi ai valori del caso dimostrativo."""
    for chiave, valore in CASO_DIMOSTRATIVO.items():
        st.session_state[chiave] = valore
    st.session_state.livelli = [dict(
        data=CASO_DIMOSTRATIVO["data_prima"] + timedelta(weeks=SETTIMANA_DEMO),
        valore=LIVELLO_DEMO, non_dosabile=False)]


def caso_dimostrativo_attivo() -> bool:
    """Vero solo se i campi sono ancora quelli del caso dimostrativo."""
    if any(st.session_state.get(k) != CASO_DIMOSTRATIVO[k] for k in CHIAVI_CHE_CONTANO):
        return False
    livelli = st.session_state.livelli
    return (len(livelli) == 1 and not livelli[0]["non_dosabile"]
            and livelli[0]["valore"] == LIVELLO_DEMO
            and (livelli[0]["data"] - st.session_state.data_prima).days == SETTIMANA_DEMO * 7)


# ---------------------------------------------------------------------
# Intestazione e avvertenza, sempre in vista
# ---------------------------------------------------------------------
st.title("Gemello digitale dell'infliximab")
st.error(f"**{AVVERTENZA}**", icon="⚠️")
st.caption("Paziente virtuale: concentrazione di infliximab nel sangue calcolata con il "
           "modello di popolazione di Fasanmade et al., Eur J Clin Pharmacol 2009 "
           "(adulti con colite ulcerosa). I limiti del modello sono in fondo alla pagina.")
st.button("Caso dimostrativo", key="caso_dimostrativo", icon="▶️",
          on_click=carica_caso_dimostrativo,
          help=f"Paziente tipico con una valle di {numero(LIVELLO_DEMO)} µg/mL alla settimana "
               f"{SETTIMANA_DEMO}, e confronto tra due schemi alternativi.")

# ---------------------------------------------------------------------
# Dati inseriti dall'utente (barra laterale)
# ---------------------------------------------------------------------
with st.sidebar:
    st.header("Paziente")
    peso = st.number_input("Peso (kg)", min_value=20.0, max_value=250.0, step=1.0,
                           format="%.0f", key="peso")
    sesso = st.radio("Sesso", ["Uomo", "Donna"], horizontal=True, key="sesso")
    albumina = st.number_input("Albumina (g/dL)", min_value=1.0, max_value=6.5, step=0.1,
                               format="%.1f", key="albumina",
                               help="Albumina nel sangue prima della terapia. "
                                    "41 g/L corrispondono a 4,1 g/dL.")
    anticorpi = st.toggle("Anticorpi anti-infliximab positivi", key="anticorpi")

    st.header("Schema di terapia")
    mg_per_kg = st.number_input("Dose per infusione (mg/kg)", min_value=1.0, max_value=20.0,
                                step=0.5, format="%.1f", key="mg_per_kg")
    testo_induzione = st.text_input("Settimane delle infusioni iniziali", key="induzione")
    intervallo = st.number_input("Poi un'infusione ogni (settimane)", min_value=1, max_value=16,
                                 step=1, key="intervallo")

    st.header("Soglia")
    soglia = st.number_input("Soglia della concentrazione minima (µg/mL)", min_value=0.1,
                             max_value=50.0, step=0.5, format="%.1f", key="soglia")

    st.header("Livelli misurati")
    st.caption("Esami del sangue con il livello di infliximab. Si assume che le infusioni "
               "siano state fatte come nello schema qui sopra.")
    data_prima = st.date_input("Data della prima infusione", format="DD/MM/YYYY",
                               key="data_prima")
    data_prelievo = st.date_input(
        "Data del prelievo", format="DD/MM/YYYY", key="data_prelievo",
        help="Un prelievo fatto il giorno di un'infusione vale come fatto prima "
             "dell'infusione (concentrazione minima).")
    valore = st.number_input("Livello misurato (µg/mL)", min_value=0.0, max_value=1000.0,
                             step=0.1, format="%.2f", key="valore_livello")
    non_dosabile = st.checkbox("Non dosabile (sotto 0,1 µg/mL)", key="non_dosabile")
    if st.button("Aggiungi livello", key="aggiungi", type="primary", width="stretch"):
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
    scala_log = st.toggle("Scala logaritmica", key="scala_log",
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
    una_valle, due_valli = list(DISEGNI)[:2]
    st.info(f"Curva aggiornata con {len(misure)} "
            f"{'livello misurato' if len(misure) == 1 else 'livelli misurati'} (stima bayesiana). "
            f"Rispetto a quanto previsto per questo paziente, la clearance stimata è "
            f"{variazione(parametri.CL / parametri_prima.CL)} e il volume centrale "
            f"{variazione(parametri.V1 / parametri_prima.V1, maschile=True)}.",
            icon="🩸")
    st.caption("La stima bayesiana è stata verificata solo su pazienti virtuali (100 pazienti "
               "simulati, test 4), non su pazienti reali: errore medio sulla clearance circa "
               f"{ERRORE_CL_DICHIARATO[una_valle]}% con un livello misurato e "
               f"{ERRORE_CL_DICHIARATO[due_valli]}% con due.")
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
st.caption("Confronta lo schema attuale con due alternative che partono dalla stessa "
           "settimana. Il confronto usa la curva "
           + ("aggiornata con i livelli misurati." if misure else "del modello di popolazione."))
if st.toggle("Confronta con schemi alternativi", key="confronta"):
    settimana_cambio = st.number_input("Le alternative partono dalla settimana", min_value=1,
                                       max_value=int(DURATA_SETTIMANE) - 1, step=1,
                                       key="settimana_cambio")
    colonna_a, colonna_b = st.columns(2)
    with colonna_a:
        st.markdown("**Alternativa A**")
        dose_a = st.number_input("Dose (mg/kg)", min_value=1.0, max_value=20.0, step=0.5,
                                 format="%.1f", key="dose_a")
        intervallo_a = st.number_input("Un'infusione ogni (settimane)", min_value=1,
                                       max_value=16, step=1, key="intervallo_a")
    with colonna_b:
        st.markdown("**Alternativa B**")
        dose_b = st.number_input("Dose (mg/kg)", min_value=1.0, max_value=20.0, step=0.5,
                                 format="%.1f", key="dose_b")
        intervallo_b = st.number_input("Un'infusione ogni (settimane)", min_value=1,
                                       max_value=16, step=1, key="intervallo_b")

    cambio = float(settimana_cambio)
    piani = {  # nome nella tabella -> (descrizione dello schema, piano di dosi)
        "Schema attuale": (dose_testo(mg_per_kg, intervallo), schema),
        "Alternativa A": (dose_testo(dose_a, intervallo_a),
                          sim.SchemaConCambio(schema, cambio, dose_a, float(intervallo_a))),
        "Alternativa B": (dose_testo(dose_b, intervallo_b),
                          sim.SchemaConCambio(schema, cambio, dose_b, float(intervallo_b))),
    }
    riassunti = {nome: riassunto(parametri, piano, peso, soglia, dopo_settimana=cambio)
                 for nome, (_, piano) in piani.items()}

    def colonna(descrizione: str, r: dict) -> list[str]:
        ultima = (f"{numero(r['valli'][-1][1], 2)} µg/mL (sett. {r['valli'][-1][0]:g})"
                  if r["valli"] else "-")
        return [descrizione,
                "Nessuna" if r["prima_sotto"] is None else f"Settimana {r['prima_sotto'][0]:g}",
                f"{r['giorni_sotto']:.0f}", ultima,
                f"{r['dose_totale']:,.0f} mg".replace(",", ".")]

    tabella = {"": [f"Schema dalla settimana {cambio:g}",
                    "Prima valle sotto soglia dopo il cambio",
                    "Giorni sotto soglia dopo il cambio", "Ultima valle",
                    f"Farmaco totale in {DURATA_SETTIMANE:g} settimane"]}
    for nome, (descrizione, _) in piani.items():
        tabella[nome] = colonna(descrizione, riassunti[nome])
    st.dataframe(pd.DataFrame(tabella), hide_index=True)

    # Stessa griglia di tempi per le tre curve (servono gli istanti di tutti gli schemi).
    tempi = np.unique(np.concatenate([sim.curva(parametri, piano, peso)[0]
                                      for _, piano in piani.values()]))
    giorni = tempi * sim.GIORNI_PER_SETTIMANA
    curve = {f"{nome}: {descrizione}": sim.concentrazione(giorni, parametri, piano.dosi(peso))
             for nome, (descrizione, piano) in piani.items()}
    st.altair_chart(grafico_confronto(tempi, curve, soglia, scala_log=scala_log,
                                      tema=tema_attuale(), durata_settimane=DURATA_SETTIMANE),
                    width="stretch")

    if caso_dimostrativo_attivo():
        farmaco = f"{riassunti['Alternativa A']['dose_totale']:,.0f} mg".replace(",", ".")
        st.info(f"Caso dimostrativo: a parità di farmaco totale ({farmaco} in "
                f"{DURATA_SETTIMANE:g} settimane), raddoppiare la dose ogni 8 settimane lascia "
                "ancora il paziente sotto soglia prima di ogni infusione, mentre 5 mg/kg ogni "
                "4 settimane lo mantiene sopra soglia dopo il cambio: è un paziente virtuale, "
                "non un consiglio di terapia.", icon="💡")

# ---------------------------------------------------------------------
# Parametri del paziente e limiti
# ---------------------------------------------------------------------
st.subheader("Parametri di questo paziente secondo il modello")


def formatta(p: m.ParametriPK) -> list[str]:
    return [f"{numero(p.CL, 3)} L/giorno", f"{numero(p.V1, 2)} L", f"{numero(p.V2, 2)} L",
            f"{numero(p.Q, 2)} L/giorno"]


tabella_parametri = {"Parametro": ["Clearance (CL)", "Volume centrale (V1)",
                                   "Volume periferico (V2)",
                                   "Clearance intercompartimentale (Q)"],
                     "Prima dei livelli misurati": formatta(parametri_prima)}
if misure:
    tabella_parametri["Dopo i livelli misurati"] = formatta(parametri)
tabella_parametri["Paziente tipico dell'articolo"] = formatta(m.parametri_tipici(m.PAZIENTE_TIPICO))
st.dataframe(pd.DataFrame(tabella_parametri), hide_index=True)
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
