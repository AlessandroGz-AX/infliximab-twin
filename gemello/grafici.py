"""
Grafici dell'app, costruiti con Altair.

Regole di disegno seguite:
- linea sottile (2 px) e un solo colore per curva;
- soglia tratteggiata, con l'etichetta scritta direttamente sul grafico;
- valli sotto soglia nel colore di allarme, sempre insieme a un'etichetta
  (legenda e tabella), mai con il solo colore;
- al passaggio del dito o del mouse, un mirino verticale con i valori;
- griglia e assi discreti (li gestisce il tema di Streamlit, chiaro o scuro).
"""

import altair as alt
import numpy as np
import pandas as pd

# Colori: blu per la curva, rosso solo per lo stato "sotto soglia",
# grigi per testo e mirino. Valori diversi per il tema chiaro e quello scuro.
COLORI = {
    "chiaro": dict(curva="#2a78d6", allarme="#d03b3b", testo="#52514e",
                   tenue="#898781", sfondo="#ffffff"),
    "scuro": dict(curva="#3987e5", allarme="#d03b3b", testo="#c3c2b7",
                  tenue="#898781", sfondo="#0e1117"),
}

# Numeri con la virgola decimale nel grafico.
LOCALE_ITALIANO = {"number": {"decimal": ",", "thousands": ".", "grouping": [3],
                              "currency": ["", " €"]}}


def _numero(x: float) -> str:
    return f"{x:g}".replace(".", ",")


def grafico_concentrazione(settimane, concentrazioni, valli, soglia: float,
                           scala_log: bool = True, tema: str = "chiaro",
                           durata_settimane: float = 54.0) -> alt.LayerChart:
    """Curva della concentrazione nel tempo, con soglia e valli evidenziate."""
    c = COLORI[tema]
    dati = pd.DataFrame({"Settimana": settimane, "Concentrazione": concentrazioni})
    if scala_log:  # in scala logaritmica lo zero non esiste
        dati = dati[dati["Concentrazione"] > 0]
    dati_valli = pd.DataFrame(valli, columns=["Settimana", "Concentrazione"])
    dati_valli["Valle"] = np.where(dati_valli["Concentrazione"] < soglia,
                                   "Sotto soglia", "Sopra soglia")

    massimo = float(np.max(concentrazioni)) * 1.3
    if scala_log:
        piu_bassi = [v for v in list(dati_valli["Concentrazione"]) + [soglia] if v > 0]
        minimo = max(min(piu_bassi) / 2, 0.01)
        scala_y = alt.Scale(type="log", domain=[minimo, massimo])
        # Tacche fisse e leggibili (1, 3, 10, 30, ...) al posto di quelle automatiche.
        tacche = [t for t in (0.01, 0.03, 0.1, 0.3, 1, 3, 10, 30, 100, 300, 1000, 3000)
                  if minimo <= t <= massimo]
        asse_y_formato = alt.Axis(format="~g", values=tacche)
    else:
        scala_y = alt.Scale(domain=[0, massimo])
        asse_y_formato = alt.Axis(format="~g")

    asse_x = alt.X("Settimana:Q", title="Settimane dalla prima infusione",
                   scale=alt.Scale(domain=[0, durata_settimane], nice=False),
                   axis=alt.Axis(values=list(range(0, int(durata_settimane) + 1, 6))))
    asse_y = alt.Y("Concentrazione:Q", title="Infliximab nel sangue (µg/mL)",
                   scale=scala_y, axis=asse_y_formato)
    base = alt.Chart(dati).encode(x=asse_x, y=asse_y)

    curva = base.mark_line(strokeWidth=2, color=c["curva"],
                           strokeCap="round", strokeJoin="round")

    linea_soglia = alt.Chart(pd.DataFrame({"Soglia": [soglia]})).mark_rule(
        color=c["testo"], strokeWidth=1.5, strokeDash=[6, 4]).encode(y="Soglia:Q")
    # Etichetta a sinistra: lì la curva è alta (infusioni iniziali) e non la copre.
    etichetta_soglia = alt.Chart(pd.DataFrame({
        "x": [0.0], "Soglia": [soglia],
        "testo": [f"Soglia {_numero(soglia)} µg/mL"]})).mark_text(
        align="left", baseline="bottom", dx=4, dy=-4, fontSize=12,
        color=c["testo"]).encode(x="x:Q", y="Soglia:Q", text="testo:N")

    punti_valli = alt.Chart(dati_valli).mark_point(
        filled=True, size=90, opacity=1, stroke=c["sfondo"], strokeWidth=2).encode(
        x="Settimana:Q", y="Concentrazione:Q",
        color=alt.Color("Valle:N",
                        scale=alt.Scale(domain=["Sopra soglia", "Sotto soglia"],
                                        range=[c["curva"], c["allarme"]]),
                        legend=alt.Legend(title="Concentrazione minima (valle)", orient="top")),
        tooltip=[alt.Tooltip("Settimana:Q", title="Settimana", format=".0f"),
                 alt.Tooltip("Concentrazione:Q", title="Valle (µg/mL)", format=".2f"),
                 alt.Tooltip("Valle:N", title="Rispetto alla soglia")])

    # Mirino: segue il dito o il mouse e si aggancia al punto più vicino della curva.
    vicino = alt.selection_point(nearest=True, on="pointerover", fields=["Settimana"],
                                 empty=False)
    mirino = base.mark_rule(color=c["tenue"], strokeWidth=1).encode(
        opacity=alt.condition(vicino, alt.value(1), alt.value(0)),
        tooltip=[alt.Tooltip("Settimana:Q", title="Settimana", format=".1f"),
                 alt.Tooltip("Concentrazione:Q", title="Concentrazione (µg/mL)", format=".2f")],
    ).add_params(vicino)
    punto_mirino = base.mark_point(filled=True, size=70, color=c["curva"], stroke=c["sfondo"],
                                   strokeWidth=2).encode(
        opacity=alt.condition(vicino, alt.value(1), alt.value(0)))

    return (alt.layer(curva, linea_soglia, etichetta_soglia, punti_valli, mirino, punto_mirino)
            .properties(height=420)
            .configure(locale=LOCALE_ITALIANO))
