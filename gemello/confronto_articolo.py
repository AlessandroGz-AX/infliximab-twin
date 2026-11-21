"""
Confronto tra i numeri scritti nell'articolo e quelli prodotti dal modello.

Uso, dalla cartella del progetto:
    python -m gemello.confronto_articolo

Regola: il modello segue le equazioni finali (p. 1218) e la Tabella 3.
Quando una frase del testo non torna con le equazioni, la segnaliamo
come DIVERSO e NON modifichiamo il modello per farla tornare.
"""

from gemello import modello as m


def _num(x: float, decimali: int) -> str:
    """Numero con la virgola decimale all'italiana."""
    return f"{x:.{decimali}f}".replace(".", ",")


def _variazione(rapporto: float) -> str:
    """Da un rapporto (es. 1,471) a una variazione percentuale (es. +47,1%)."""
    return f"{(rapporto - 1) * 100:+.1f}%".replace(".", ",")


def righe_confronto() -> list[dict]:
    """Restituisce le righe del confronto (usabili anche nell'app)."""
    def par(**kw):
        valori = dict(peso_kg=77.0, donna=False, albumina_g_dl=4.1, anticorpi=False)
        valori.update(kw)
        return m.parametri_tipici(m.Paziente(**valori))

    uomo, donna, ati = par(), par(donna=True), par(anticorpi=True)
    alb_38, alb_43 = par(albumina_g_dl=3.8), par(albumina_g_dl=4.3)
    t_uomo = m.emivita_terminale_giorni(uomo)
    t_donna = m.emivita_terminale_giorni(donna)

    return [
        dict(grandezza="CL, paziente tipico", articolo="0,407 L/giorno", fonte="Tab. 3",
             modello=_num(uomo.CL, 3) + " L/giorno", esito="OK", nota=""),
        dict(grandezza="V1, paziente tipico", articolo="3,29 L", fonte="Tab. 3",
             modello=_num(uomo.V1, 2) + " L", esito="OK", nota=""),
        dict(grandezza="V2", articolo="4,13 L", fonte="Tab. 3",
             modello=_num(uomo.V2, 2) + " L", esito="OK", nota=""),
        dict(grandezza="Q", articolo="7,14 L/giorno", fonte="Tab. 3",
             modello=_num(uomo.Q, 2) + " L/giorno", esito="OK", nota=""),
        dict(grandezza="CL con anticorpi anti-infliximab", articolo="+47,1%", fonte="p. 1220",
             modello=_variazione(ati.CL / uomo.CL), esito="OK", nota=""),
        dict(grandezza="CL nelle donne", articolo="circa -33%", fonte="testo p. 1220",
             modello=_variazione(donna.CL / uomo.CL), esito="DIVERSO",
             nota="L'equazione finale (p. 1218) e la Tab. 3 danno -23,6%. "
                  "Il modello usa l'equazione."),
        dict(grandezza="V1 nelle donne", articolo="-16%", fonte="testo p. 1220",
             modello=_variazione(donna.V1 / uomo.V1), esito="DIVERSO",
             nota="Il 16% corrisponde al confronto inverso: negli uomini V1 è "
                  + _variazione(uomo.V1 / donna.V1) + " rispetto alle donne."),
        dict(grandezza="Effetto del peso su V1 (esponente)", articolo="0,54", fonte="p. 1222",
             modello=_num(m.THETA_WGT_V1, 3), esito="OK",
             nota="0,54 è il valore 0,538 della Tab. 3 arrotondato."),
        dict(grandezza="CL con albumina 3,8 contro 4,3 g/dL", articolo="+19,1%",
             fonte="p. 1223-1224", modello=_variazione(alb_38.CL / alb_43.CL), esito="DIVERSO",
             nota="Differenza piccola. L'articolo non dice come ha fatto il calcolo "
                  "(e scrive 'mg/dl' per refuso: è g/dL)."),
        dict(grandezza="Volume allo stato stazionario, 77 kg", articolo="7,71 L",
             fonte="p. 1221", modello=_num(m.volume_stato_stazionario(uomo), 2) + " L",
             esito="DIVERSO", nota="V1 + V2 della Tab. 3 fanno 7,42 L."),
        dict(grandezza="Emivita terminale", articolo="circa 14 giorni",
             fonte="abstract; p. 1216, 1221",
             modello=f"uomo tipico {_num(t_uomo, 1)} g; donna tipica {_num(t_donna, 1)} g",
             esito="NOTA",
             nota="Il 14 è la mediana delle emivite dei singoli pazienti (p. 1221, "
                  "intervallo interquartile 10,4-17,8 g), non il paziente tipico. "
                  "Verifica sulla popolazione nel Test 3."),
    ]


def tabella_markdown() -> str:
    righe = ["| Grandezza | Articolo | Fonte | Modello | Esito | Nota |",
             "|---|---|---|---|---|---|"]
    for r in righe_confronto():
        righe.append(f"| {r['grandezza']} | {r['articolo']} | {r['fonte']} | "
                     f"{r['modello']} | **{r['esito']}** | {r['nota']} |")
    return "\n".join(righe)


if __name__ == "__main__":
    print("Confronto modello - articolo (Fasanmade 2009)\n")
    print(tabella_markdown())
