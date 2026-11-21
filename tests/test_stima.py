"""
Stima bayesiana (massima a posteriori) e TEST 4 (simulazione e stima).

Per farli girare, dalla cartella del progetto:   python -m pytest
"""

import numpy as np
import pytest

from gemello import modello as m
from gemello import simulazione as sim
from gemello import verifica_stima as vs
from gemello.stima import Misura, funzione_obiettivo, stima_map

PAZIENTE = m.PAZIENTE_TIPICO
DOSI = sim.Schema().dosi(PAZIENTE.peso_kg)
GIORNO_VALLE_14 = 14 * 7.0


def valle_tipica_14():
    return sim.concentrazione(GIORNO_VALLE_14, m.parametri_tipici(PAZIENTE), DOSI)[0]


# =====================================================================
# Comportamento della stima
# =====================================================================

def test_senza_misure_resta_il_paziente_tipico():
    stima = stima_map(PAZIENTE, DOSI, [])
    assert (stima.eta_cl, stima.eta_v1) == (0.0, 0.0)
    assert stima.parametri == m.parametri_tipici(PAZIENTE)


def test_livelli_sotto_il_limite_di_quantificazione_esclusi_e_segnalati():
    misure = [Misura(GIORNO_VALLE_14, 0.05), Misura(GIORNO_VALLE_14 + 1, -0.01)]
    stima = stima_map(PAZIENTE, DOSI, misure)
    assert len(stima.misure_escluse) == 2 and stima.misure_usate == ()
    assert stima.parametri == m.parametri_tipici(PAZIENTE)


def test_valle_bassa_alza_la_clearance_valle_alta_la_abbassa():
    attesa = valle_tipica_14()
    bassa = stima_map(PAZIENTE, DOSI, [Misura(GIORNO_VALLE_14, attesa / 3)])
    alta = stima_map(PAZIENTE, DOSI, [Misura(GIORNO_VALLE_14, attesa * 3)])
    assert bassa.parametri.CL > 0.407 > alta.parametri.CL


def test_la_stima_trova_il_vero_minimo():
    """Confronto con una ricerca a griglia fitta: nessun punto fa meglio della stima."""
    misure = [Misura(GIORNO_VALLE_14, 1.2), Misura(22 * 7.0, 0.9)]
    stima = stima_map(PAZIENTE, DOSI, misure)
    migliore = funzione_obiettivo((stima.eta_cl, stima.eta_v1), PAZIENTE, DOSI, misure)
    griglia = min(funzione_obiettivo((a, b), PAZIENTE, DOSI, misure)
                  for a in np.arange(-1.5, 1.51, 0.02) for b in np.arange(-1.0, 1.01, 0.02))
    assert migliore <= griglia + 1e-6


def test_misure_non_valide_rifiutate():
    for sbagliata in (Misura(0.0, 5.0), Misura(-3.0, 5.0), Misura(10.0, float("nan"))):
        with pytest.raises(ValueError):
            stima_map(PAZIENTE, DOSI, [sbagliata])
    with pytest.raises(ValueError):
        stima_map(PAZIENTE, [], [Misura(10.0, 5.0)])


# =====================================================================
# TEST 4 - 100 pazienti virtuali: la stima ritrova i parametri veri?
# Margini fissati prima di vedere i risultati.
# =====================================================================

UNA_VALLE, DUE_VALLI, ACT1 = vs.DISEGNI


def test_4_una_valle_dimezza_quasi_l_errore_sulla_clearance():
    r = vs.esegui(UNA_VALLE)
    assert r.cl_stima <= 20 and r.cl_stima < r.cl_popolazione


def test_4_due_valli_errore_sulla_clearance_entro_15_percento():
    r = vs.esegui(DUE_VALLI)
    assert r.cl_stima <= 15
    assert r.cl_stima <= 0.5 * r.cl_popolazione


def test_4_prelievi_dello_studio_ACT1_ritrovano_clearance_e_V1():
    r = vs.esegui(ACT1)
    assert r.cl_stima <= 10
    assert r.v1_stima <= 15 and r.v1_stima < r.v1_popolazione


@pytest.mark.parametrize("disegno", list(vs.DISEGNI))
def test_4_nessun_errore_sistematico_e_mai_peggio_del_modello_senza_misure(disegno):
    r = vs.esegui(disegno)
    assert abs(r.cl_distorsione) <= 5 and abs(r.v1_distorsione) <= 5
    # Con sole valli V1 resta vicino al valore tipico (le valli dicono poco su
    # V1), ma la stima non deve peggiorarlo.
    assert r.v1_stima <= 1.05 * r.v1_popolazione
    # Classificare sopra/sotto la soglia di 3 µg/mL: mai peggio di senza misure.
    assert r.soglia_stima >= r.soglia_popolazione
