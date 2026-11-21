"""
Grafici dell'app, costruiti con Altair.

Regole di disegno seguite:
- linee sottili (2 px), un colore per curva, legenda quando le curve sono due;
- soglia tratteggiata, con l'etichetta scritta direttamente sul grafico;
- valli sotto soglia nel colore di allarme, sempre insieme a un'etichetta
  (legenda e tabella), mai con il solo colore;
- al passaggio del dito o del mouse, un mirino verticale con i valori di
  tutte le curve in quel momento;
- griglia e assi discreti (li gestisce il tema di Streamlit, chiaro o scuro).
I colori delle due curve del confronto (blu e arancione) sono stati
verificati per la leggibilità, anche per chi non distingue bene i colori.
"""

import altair as alt
import numpy as np
import pandas as pd

from gemello.modello import LLOQ

COLORI = {
    "chiaro": dict(curva="#2a78d6", alternativo="#eb6834", allarme="#d03b3b",
                   testo="#52514e", tenue="#898781", inchiostro="#0b0b0b",
                   sfondo="#ffffff"),
    "scuro": dict(curva="#3987e5", alternativo="#d95926", allarme="#d03b3b",
                  testo="#c3c2b7", tenue="#898781", inchiostro="#f0efec",
                  sfondo="#0e1117"),
}

# Numeri con la virgola decimale nel grafico.
LOCALE_ITALIANO = {"number": {"decimal": ",", "thousands": ".", "grouping": [3],
                              "currency": ["", " €"]}}

ETICHETTA_PRIMA = "Prima delle misure"
ETICHETTA_DOPO = "Dopo le misure (stima bayesiana)"
ETICHETTA_SOLO_MODELLO = "Modello di popolazione"
ETICHETTA_MISURATO = "Livello misurato"
ETICHETTA_NON_DOSABILE = "Non dosabile (sotto 0,1)"


def _numero(x: float) -> str:
    return f"{x:g}".replace(".", ",")


def _assi(valori_bassi, massimo: float, scala_log: bool, durata: float):
    """Assi del grafico. In scala logaritmica usa tacche fisse e leggibili."""
    if scala_log:
        minimo = max(min(v for v in valori_bassi if v > 0) / 2, 0.01)
        tacche = [t for t in (0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000, 3000)
                  if minimo <= t <= massimo]
        scala = alt.Scale(type="log", domain=[minimo, massimo])
        asse = alt.Axis(format="~g", values=tacche)
    else:
        scala, asse = alt.Scale(domain=[0, massimo]), alt.Axis(format="~g")
    x = alt.X("Settimana:Q", title="Settimane dalla prima infusione",
              scale=alt.Scale(domain=[0, durata], nice=False),
              axis=alt.Axis(values=list(range(0, int(durata) + 1, 6))))
    y_titolo, y_scala, y_asse = "Infliximab nel sangue (µg/mL)", scala, asse
    return x, (y_titolo, y_scala, y_asse)


def _y(campo: str, assi_y):
    titolo, scala, asse = assi_y
    return alt.Y(f"{campo}:Q", title=titolo, scale=scala, axis=asse)


def _soglia(soglia: float, c: dict) -> list:
    """Linea tratteggiata della soglia, con etichetta a sinistra (lì la curva è alta)."""
    linea = alt.Chart(pd.DataFrame({"Soglia": [soglia]})).mark_rule(
        color=c["testo"], strokeWidth=1.5, strokeDash=[6, 4]).encode(y="Soglia:Q")
    etichetta = alt.Chart(pd.DataFrame({
        "x": [0.0], "Soglia": [soglia], "testo": [f"Soglia {_numero(soglia)} µg/mL"]})).mark_text(
        align="left", baseline="bottom", dx=4, dy=-4, fontSize=12,
        color=c["testo"]).encode(x="x:Q", y="Soglia:Q", text="testo:N")
    return [linea, etichetta]


def _mirino(dati_larghi: pd.DataFrame, x, colonne: dict[str, str], c: dict) -> list:
    """
    Mirino verticale che segue il dito o il mouse: il riquadro mostra il
    valore di tutte le curve in quella settimana.
    `colonne` = {nome della colonna nei dati: titolo nel riquadro}.
    """
    vicino = alt.selection_point(nearest=True, on="pointerover", fields=["Settimana"],
                                 empty=False)
    riquadro = [alt.Tooltip("Settimana:Q", title="Settimana", format=".1f")]
    riquadro += [alt.Tooltip(f"{col}:Q", title=titolo, format=".2f")
                 for col, titolo in colonne.items()]
    regola = alt.Chart(dati_larghi).mark_rule(color=c["tenue"], strokeWidth=1).encode(
        x=x, opacity=alt.condition(vicino, alt.value(1), alt.value(0)),
        tooltip=riquadro).add_params(vicino)
    return [regola]


def grafico_concentrazione(settimane, concentrazioni, valli, soglia: float,
                           scala_log: bool = True, tema: str = "chiaro",
                           durata_settimane: float = 54.0, curva_prima=None,
                           misure=None) -> alt.LayerChart:
    """
    Curva della concentrazione nel tempo, con soglia e valli evidenziate.
    Se ci sono livelli misurati: `curva_prima` è la curva del modello di
    popolazione (in grigio) e `misure` è un elenco di
    (settimana, valore, non_dosabile) disegnato come punti.
    """
    c = COLORI[tema]
    misure = misure or []
    con_misure = curva_prima is not None

    larghi = pd.DataFrame({"Settimana": settimane, "Attuale": concentrazioni})
    if con_misure:
        larghi["Prima"] = curva_prima
    if scala_log:  # in scala logaritmica lo zero non esiste
        larghi = larghi[larghi["Attuale"] > 0]

    dati_valli = pd.DataFrame(valli, columns=["Settimana", "Concentrazione"])
    dati_valli["Valle"] = np.where(dati_valli["Concentrazione"] < soglia,
                                   "Sotto soglia", "Sopra soglia")
    dati_misure = pd.DataFrame(misure, columns=["Settimana", "Valore", "Non dosabile"])
    dati_misure["Mostrato"] = np.where(dati_misure["Non dosabile"], LLOQ, dati_misure["Valore"])
    dati_misure["Tipo"] = np.where(dati_misure["Non dosabile"], ETICHETTA_NON_DOSABILE,
                                   ETICHETTA_MISURATO)
    dati_misure["Testo"] = [("sotto 0,1" if nd else f"{v:.2f}".replace(".", ",")) + " µg/mL"
                            for v, nd in zip(dati_misure["Valore"], dati_misure["Non dosabile"])]

    valori_bassi = list(dati_valli["Concentrazione"]) + [soglia] + list(dati_misure["Mostrato"])
    massimo = max([float(np.max(concentrazioni))] + list(dati_misure["Mostrato"])) * 1.3
    x, assi_y = _assi(valori_bassi, massimo, scala_log, durata_settimane)

    # Curve: in grigio la previsione prima delle misure, in blu quella attuale.
    nomi = [ETICHETTA_PRIMA, ETICHETTA_DOPO] if con_misure else [ETICHETTA_SOLO_MODELLO]
    colori = [c["tenue"], c["curva"]] if con_misure else [c["curva"]]
    scala_colori = alt.Scale(domain=nomi, range=colori)
    legenda = (alt.Legend(title=None, orient="top", direction="vertical", labelLimit=260)
               if con_misure else None)
    strati = []
    if con_misure:
        strati.append(alt.Chart(larghi.assign(Curva=ETICHETTA_PRIMA)).mark_line(
            strokeWidth=2, strokeCap="round", strokeJoin="round").encode(
            x=x, y=_y("Prima", assi_y),
            color=alt.Color("Curva:N", scale=scala_colori, legend=legenda)))
    strati.append(alt.Chart(larghi.assign(Curva=nomi[-1])).mark_line(
        strokeWidth=2, strokeCap="round", strokeJoin="round").encode(
        x=x, y=_y("Attuale", assi_y),
        color=alt.Color("Curva:N", scale=scala_colori, legend=legenda)))

    strati += _soglia(soglia, c)

    strati.append(alt.Chart(dati_valli).mark_point(
        filled=True, size=90, opacity=1, stroke=c["sfondo"], strokeWidth=2).encode(
        x="Settimana:Q", y=_y("Concentrazione", assi_y),
        fill=alt.Fill("Valle:N", scale=alt.Scale(domain=["Sopra soglia", "Sotto soglia"],
                                                 range=[c["curva"], c["allarme"]]),
                      legend=alt.Legend(title="Valle", orient="top", direction="vertical")),
        tooltip=[alt.Tooltip("Settimana:Q", title="Settimana", format=".0f"),
                 alt.Tooltip("Concentrazione:Q", title="Valle (µg/mL)", format=".2f"),
                 alt.Tooltip("Valle:N", title="Rispetto alla soglia")]))

    if len(dati_misure):
        strati.append(alt.Chart(dati_misure).mark_point(
            filled=True, size=130, opacity=1, color=c["inchiostro"], stroke=c["sfondo"],
            strokeWidth=2).encode(
            x="Settimana:Q", y=_y("Mostrato", assi_y),
            shape=alt.Shape("Tipo:N", scale=alt.Scale(
                domain=[ETICHETTA_MISURATO, ETICHETTA_NON_DOSABILE],
                range=["diamond", "triangle-down"]),
                legend=alt.Legend(title=None, orient="top", direction="vertical",
                                  symbolSize=110, symbolFillColor=c["inchiostro"])),
            tooltip=[alt.Tooltip("Settimana:Q", title="Settimana", format=".1f"),
                     alt.Tooltip("Testo:N", title="Livello misurato")]))

    colonne = ({"Attuale": "Dopo le misure (µg/mL)", "Prima": "Prima delle misure (µg/mL)"}
               if con_misure else {"Attuale": "Concentrazione (µg/mL)"})
    strati += _mirino(larghi, x, colonne, c)

    return alt.layer(*strati).properties(height=420).configure(locale=LOCALE_ITALIANO)


def grafico_confronto(settimane, concentrazioni_attuale, concentrazioni_alternativo,
                      soglia: float, scala_log: bool = True, tema: str = "chiaro",
                      durata_settimane: float = 54.0) -> alt.LayerChart:
    """Schema attuale (blu) contro schema alternativo (arancione), stessa soglia."""
    c = COLORI[tema]
    larghi = pd.DataFrame({"Settimana": settimane, "Attuale": concentrazioni_attuale,
                           "Alternativo": concentrazioni_alternativo})
    if scala_log:
        larghi = larghi[(larghi["Attuale"] > 0) & (larghi["Alternativo"] > 0)]

    positivi = np.concatenate([larghi["Attuale"], larghi["Alternativo"]])
    # Il minimo delle curve, a parte i primi istanti, è vicino alle valli.
    dopo_inizio = larghi[larghi["Settimana"] > 1]
    valori_bassi = [float(dopo_inizio["Attuale"].min()), float(dopo_inizio["Alternativo"].min()),
                    soglia]
    x, assi_y = _assi(valori_bassi, float(positivi.max()) * 1.3, scala_log, durata_settimane)

    nomi = ["Schema attuale", "Schema alternativo"]
    scala_colori = alt.Scale(domain=nomi, range=[c["curva"], c["alternativo"]])
    legenda = alt.Legend(title=None, orient="top")
    # Prima l'alternativo, poi l'attuale sopra: fino al cambio le curve coincidono
    # e il tratto comune resta del colore dello schema attuale.
    strati = [
        alt.Chart(larghi.assign(Curva=nome)).mark_line(
            strokeWidth=2, strokeCap="round", strokeJoin="round").encode(
            x=x, y=_y(colonna, assi_y),
            color=alt.Color("Curva:N", scale=scala_colori, legend=legenda))
        for nome, colonna in [("Schema alternativo", "Alternativo"), ("Schema attuale", "Attuale")]
    ]
    strati += _soglia(soglia, c)
    strati += _mirino(larghi, x, {"Attuale": "Schema attuale (µg/mL)",
                                  "Alternativo": "Schema alternativo (µg/mL)"}, c)
    return alt.layer(*strati).properties(height=380).configure(locale=LOCALE_ITALIANO)
