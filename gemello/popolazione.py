"""
Popolazione virtuale simile a quella degli studi ACT 1 e 2 (Tabella 2).

Serve per i controlli: l'articolo riporta l'emivita mediana calcolata sui
singoli pazienti, quindi per confrontarci dobbiamo simulare molti pazienti
con caratteristiche distribuite come nello studio.

ATTENZIONE: la Tabella 2 (p. 1217) riporta media, deviazione standard,
mediana, minimo e massimo, ma non la forma delle distribuzioni. Le forme
qui sotto sono una nostra scelta di simulazione, NON parametri del modello:
    - peso: log-normale con mediana 77 kg; la larghezza (0,23 in scala
      logaritmica) dà una deviazione standard di circa 18,4 kg come nella
      Tabella 2. Tagliata tra 40 e 177,3 kg;
    - albumina: normale con media 4,1 e deviazione standard 0,4 g/dL,
      tagliata tra 2,4 e 5,2 g/dL;
    - donne: 189 su 482. Anticorpi positivi: 33 su 482 (i pazienti senza
      dato sono considerati non positivi, come fa l'articolo a p. 1213);
    - nessuna correlazione tra le caratteristiche (non riportata).
La variabilità individuale (eta) segue la decisione A (vedi modello.py).
"""

from functools import lru_cache

import numpy as np

from gemello import modello as m

FRAZIONE_DONNE = 189 / 482
FRAZIONE_ANTICORPI = 33 / 482
PESO_SIGMA_LOG = 0.23  # con mediana 77 kg dà deviazione standard ≈ 18,4 kg
ALBUMINA_MEDIA, ALBUMINA_DS = 4.1, 0.4


def _tagliata(estrai, minimo: float, massimo: float, n: int) -> np.ndarray:
    """Estrae n valori e ri-estrae quelli fuori da [minimo, massimo]."""
    valori = estrai(n)
    fuori = (valori < minimo) | (valori > massimo)
    while fuori.any():
        valori[fuori] = estrai(int(fuori.sum()))
        fuori = (valori < minimo) | (valori > massimo)
    return valori


@lru_cache(maxsize=4)  # stessa richiesta -> stessa popolazione, senza ricalcolarla
def genera(n: int, seme: int = 2009) -> tuple[tuple[m.Paziente, float, float], ...]:
    """n pazienti virtuali: (caratteristiche, eta_CL, eta_V1) per ciascuno."""
    rng = np.random.default_rng(seme)
    pesi = _tagliata(lambda k: m.PESO_RIFERIMENTO * np.exp(rng.normal(0, PESO_SIGMA_LOG, k)),
                     m.PESO_MIN_STUDIO, m.PESO_MAX_STUDIO, n)
    albumine = _tagliata(lambda k: rng.normal(ALBUMINA_MEDIA, ALBUMINA_DS, k),
                         m.ALBUMINA_MIN_STUDIO, m.ALBUMINA_MAX_STUDIO, n)
    donne = rng.random(n) < FRAZIONE_DONNE
    anticorpi = rng.random(n) < FRAZIONE_ANTICORPI
    eta_cl = rng.normal(0.0, m.OMEGA_CL, n)
    eta_v1 = rng.normal(0.0, m.OMEGA_V1, n)
    return tuple((m.Paziente(peso_kg=float(p), donna=bool(d), albumina_g_dl=float(a),
                             anticorpi=bool(x)), float(e1), float(e2))
                 for p, d, a, x, e1, e2 in zip(pesi, donne, albumine, anticorpi, eta_cl, eta_v1))
