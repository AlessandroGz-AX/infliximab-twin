"""
Test 4: simulazione e stima.

1. Creiamo 100 pazienti virtuali con parametri "veri" noti (popolazione
   simile alla Tabella 2, variabilità della decisione A).
2. Per ognuno generiamo le misure con il rumore del modello:
       misura = concentrazione_vera * (1 + eps1) + eps2
   con le deviazioni standard dell'errore residuo (Tabella 3).
3. Diamo le misure alla stima bayesiana, che non conosce i parametri veri.
4. Confrontiamo i parametri stimati con quelli veri, e con quello che si
   otterrebbe senza misure (solo i valori tipici del paziente).

Proviamo tre modi di fare i prelievi:
  - una sola valle (prima dell'infusione della settimana 14);
  - due valli (settimane 14 e 22);
  - i prelievi dello studio ACT 1 (p. 1212): prima e 1 ora dopo
    l'infusione alle settimane 0, 2, 6, 14 e 46 (alla settimana 0 solo
    dopo), prima alle settimane 30 e 38, più le settimane 8 e 54.
    "1 ora dopo l'infusione" lo intendiamo come 1 ora dopo la fine.

Uso, dalla cartella del progetto:
    python -m gemello.verifica_stima
"""

from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from gemello import modello as m
from gemello import popolazione
from gemello import simulazione as sim
from gemello.stima import Misura, stima_map

N_PAZIENTI = 100
SEME_POPOLAZIONE = 4   # semi fissi: risultati ripetibili
SEME_RUMORE = 44
SCHEMA = sim.Schema()  # 5 mg/kg alle settimane 0, 2, 6, poi ogni 8
SETTIMANA_PREVISIONE = 54


def _valle(settimana: float) -> float:
    """Giorno del prelievo subito prima dell'infusione."""
    return settimana * 7.0


def _dopo(settimana: float) -> float:
    """Giorno del prelievo 1 ora dopo la fine dell'infusione."""
    return settimana * 7.0 + m.DURATA_INFUSIONE_GIORNI + 1 / 24


DISEGNI = {
    "Una valle (settimana 14)": [_valle(14)],
    "Due valli (settimane 14 e 22)": [_valle(14), _valle(22)],
    "Prelievi dello studio ACT 1 (13)": [
        _dopo(0), _valle(2), _dopo(2), _valle(6), _dopo(6), 8 * 7.0,
        _valle(14), _dopo(14), _valle(30), _valle(38), _valle(46), _dopo(46), 54 * 7.0],
}


SOGLIA = 3.0  # µg/mL, soglia di default dell'app


@dataclass(frozen=True)
class Risultato:
    """Errori in percentuale sui pazienti virtuali."""

    disegno: str
    cl_popolazione: float  # errore medio assoluto senza misure (solo valori tipici)
    cl_stima: float        # errore medio assoluto della stima bayesiana
    cl_distorsione: float  # errore sistematico della stima (media geometrica dei rapporti - 1)
    v1_popolazione: float
    v1_stima: float
    v1_distorsione: float
    valle_popolazione: float  # errore mediano assoluto sulla valle della settimana 54
    valle_stima: float
    soglia_popolazione: float  # % di pazienti messi dal lato giusto della soglia di 3 µg/mL
    soglia_stima: float
    misure_totali: int
    misure_sotto_limite: int  # "sotto 0,1 µg/mL", usate con il metodo M3


@lru_cache(maxsize=8)  # i test e il rapporto riusano gli stessi risultati
def esegui(disegno: str, n: int = N_PAZIENTI) -> Risultato:
    rng = np.random.default_rng(SEME_RUMORE)
    giorni = np.array(DISEGNI[disegno])
    giorno_previsione = SETTIMANA_PREVISIONE * 7.0
    err = {k: [] for k in ("cl_pop", "cl", "v1_pop", "v1", "valle_pop", "valle")}
    lato_giusto = {"pop": [], "stima": []}
    totali = sotto_limite = 0

    for paziente, eta_cl, eta_v1 in popolazione.genera(n, SEME_POPOLAZIONE):
        veri = m.parametri_individuali(paziente, eta_cl, eta_v1)
        tipici = m.parametri_tipici(paziente)
        dosi = SCHEMA.dosi(paziente.peso_kg)

        senza_rumore = sim.concentrazione(giorni, veri, dosi)
        misurati = (senza_rumore * (1 + rng.normal(0, m.SIGMA_PROPORZIONALE, len(giorni)))
                    + rng.normal(0, m.SIGMA_ADDITIVO, len(giorni)))
        stima = stima_map(paziente, dosi, [Misura(g, v) for g, v in zip(giorni, misurati)])
        totali += len(giorni)
        sotto_limite += len(stima.sotto_limite)

        def valle(parametri):
            return sim.concentrazione(giorno_previsione, parametri, dosi)[0]

        err["cl_pop"].append(tipici.CL / veri.CL - 1)
        err["cl"].append(stima.parametri.CL / veri.CL - 1)
        err["v1_pop"].append(tipici.V1 / veri.V1 - 1)
        err["v1"].append(stima.parametri.V1 / veri.V1 - 1)
        err["valle_pop"].append(valle(tipici) / valle(veri) - 1)
        err["valle"].append(valle(stima.parametri) / valle(veri) - 1)
        sotto_vera = valle(veri) < SOGLIA
        lato_giusto["pop"].append((valle(tipici) < SOGLIA) == sotto_vera)
        lato_giusto["stima"].append((valle(stima.parametri) < SOGLIA) == sotto_vera)

    def medio(k):
        return float(np.mean(np.abs(err[k])) * 100)

    def mediano(k):
        # Per la valle usiamo la mediana: quando la valle vera è quasi zero,
        # pochi pazienti darebbero errori percentuali enormi e falserebbero la media.
        return float(np.median(np.abs(err[k])) * 100)

    def sistematico(k):
        # Media geometrica dei rapporti stimato/vero, meno 1: non pesa in modo
        # diverso le sovrastime e le sottostime (la media aritmetica sì).
        return float((np.exp(np.mean(np.log1p(err[k]))) - 1) * 100)

    def percentuale(k):
        return float(np.mean(lato_giusto[k]) * 100)

    return Risultato(disegno, medio("cl_pop"), medio("cl"), sistematico("cl"),
                     medio("v1_pop"), medio("v1"), sistematico("v1"),
                     mediano("valle_pop"), mediano("valle"),
                     percentuale("pop"), percentuale("stima"), totali, sotto_limite)


def rapporto() -> str:
    """Tabella dei risultati in formato Markdown."""
    def p(x: float) -> str:
        return f"{x:.0f}%"

    righe = [
        f"{N_PAZIENTI} pazienti virtuali, schema 5 mg/kg alle settimane 0, 2, 6 e poi ogni 8. "
        "\"Senza misure\" = solo i valori tipici del paziente; \"con stima\" = dopo la "
        "stima bayesiana.",
        "",
        "| Prelievi | Errore medio su CL | Errore medio su V1 | Errore mediano sulla valle "
        "della settimana 54 | Pazienti messi dal lato giusto della soglia di 3 µg/mL "
        "| Livelli sotto 0,1 µg/mL (usati con il metodo M3) |",
        "|---|---|---|---|---|---|",
    ]
    def segno(x: float) -> str:
        return f"{x:+.1f}%".replace(".", ",")

    risultati = [esegui(disegno) for disegno in DISEGNI]
    for r in risultati:
        righe.append(
            f"| {r.disegno} | {p(r.cl_popolazione)} → **{p(r.cl_stima)}** "
            f"| {p(r.v1_popolazione)} → **{p(r.v1_stima)}** "
            f"| {p(r.valle_popolazione)} → **{p(r.valle_stima)}** "
            f"| {p(r.soglia_popolazione)} → **{p(r.soglia_stima)}** "
            f"| {r.misure_sotto_limite} su {r.misure_totali} |")
    righe += [
        "",
        "Errore sistematico della stima (media geometrica dei rapporti stimato/vero): "
        + "; ".join(f"{r.disegno}: CL {segno(r.cl_distorsione)}, V1 {segno(r.v1_distorsione)}"
                    for r in risultati) + ".",
    ]
    return "\n".join(righe)


if __name__ == "__main__":
    print(rapporto())
