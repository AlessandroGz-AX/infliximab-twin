"""
Controlli del simulatore: schema di terapia, formula esatta, soglia.

Per farli girare, dalla cartella del progetto:   python -m pytest
"""

import numpy as np
import pytest
from scipy.integrate import solve_ivp

from gemello import modello as m
from gemello import simulazione as sim

TIPICO = m.parametri_tipici(m.PAZIENTE_TIPICO)
PESO = m.PAZIENTE_TIPICO.peso_kg


def test_schema_di_default_come_negli_studi_ACT():
    schema = sim.Schema()
    assert schema.settimane_delle_dosi() == [0, 2, 6, 14, 22, 30, 38, 46]
    assert schema.settimane_dei_minimi() == [2, 6, 14, 22, 30, 38, 46, 54]
    assert schema.dosi(77.0)[0] == (0.0, 385.0)  # 5 mg/kg x 77 kg, giorno 0


def test_schema_modificabile():
    schema = sim.Schema(mg_per_kg=10.0, intervallo_mantenimento_settimane=4.0)
    assert schema.settimane_delle_dosi() == [0, 2, 6, 10, 14, 18, 22, 26, 30, 34, 38, 42, 46, 50]
    assert schema.settimane_dei_minimi()[-1] == 54
    assert schema.dosi(60.0)[0] == (0.0, 600.0)
    for sbagliato in (dict(mg_per_kg=0), dict(intervallo_mantenimento_settimane=0),
                      dict(durata_settimane=-1)):
        with pytest.raises(ValueError):
            sim.Schema(**sbagliato)


def test_schema_che_cambia_da_una_certa_settimana():
    base = sim.Schema()
    alternativo = sim.SchemaConCambio(base, settimana_cambio=14, mg_per_kg=10,
                                      intervallo_settimane=4)
    assert alternativo.settimane_delle_dosi() == [0, 2, 6, 14, 18, 22, 26, 30, 34, 38, 42, 46, 50]
    assert [mg_kg for _, mg_kg in alternativo.dosi_in_mg_per_kg()] == [5, 5, 5] + [10] * 10
    assert alternativo.settimane_dei_minimi() == [2, 6, 14, 18, 22, 26, 30, 34, 38, 42, 46, 50, 54]
    assert alternativo.dosi(77.0)[3] == (98.0, 770.0)
    # Se dose e intervallo non cambiano, è identico allo schema di partenza.
    assert sim.SchemaConCambio(base, 14, 5, 8).dosi(77.0) == base.dosi(77.0)
    for sbagliato in (dict(settimana_cambio=60), dict(mg_per_kg=0), dict(intervallo_settimane=0)):
        valori = dict(settimana_cambio=14, mg_per_kg=10, intervallo_settimane=8)
        valori.update(sbagliato)
        with pytest.raises(ValueError):
            sim.SchemaConCambio(base, **valori)


def test_farmaco_totale_in_54_settimane():
    assert sim.dose_totale_mg(sim.Schema(), 77.0) == 8 * 385.0  # 8 infusioni da 385 mg


def test_formula_esatta_uguale_a_integrazione_numerica():
    """
    Controllo indipendente: risolvo numericamente le equazioni
    differenziali del modello a due compartimenti e confronto con la
    formula esatta, ogni mezza giornata per 54 settimane.
    """
    schema = sim.Schema()
    dosi = schema.dosi(PESO)
    durata = m.DURATA_INFUSIONE_GIORNI
    k10, k12, k21 = TIPICO.CL / TIPICO.V1, TIPICO.Q / TIPICO.V1, TIPICO.Q / TIPICO.V2

    def velocita_infusione(t):
        return sum(dose / durata for giorno, dose in dosi if giorno <= t < giorno + durata)

    def derivate(t, quantita):
        centrale, periferico = quantita  # mg nei due compartimenti
        return [velocita_infusione(t) - (k10 + k12) * centrale + k21 * periferico,
                k12 * centrale - k21 * periferico]

    fine = schema.durata_settimane * 7
    tempi = np.linspace(0, fine, int(fine * 2) + 1)
    # Integro a tratti, fermandomi a ogni inizio e fine infusione.
    confini = sorted({0.0, fine} | {g for g, _ in dosi} | {g + durata for g, _ in dosi})
    numerica, stato = {}, [0.0, 0.0]
    for t0, t1 in zip(confini[:-1], confini[1:]):
        punti = sorted({t1} | set(tempi[(tempi >= t0) & (tempi <= t1)]))
        soluzione = solve_ivp(derivate, (t0, t1), stato, t_eval=punti,
                              method="LSODA", rtol=1e-10, atol=1e-10)
        numerica.update(zip(soluzione.t, soluzione.y[0] / TIPICO.V1))
        stato = soluzione.y[:, -1]

    esatta = sim.concentrazione(tempi, TIPICO, dosi)
    attesa = np.array([numerica[t] for t in tempi])
    assert np.allclose(esatta, attesa, rtol=1e-6, atol=1e-8)


def test_area_sotto_la_curva_di_una_dose_uguale_dose_diviso_clearance():
    """Bilancio di massa: tutto il farmaco infuso viene eliminato (AUC = Dose/CL)."""
    dose = 385.0
    tempi = np.concatenate([np.linspace(0, 2, 20001), np.linspace(2, 1500, 150001)[1:]])
    c = sim.concentrazione(tempi, TIPICO, [(0.0, dose)])
    assert np.trapezoid(c, tempi) == pytest.approx(dose / TIPICO.CL, rel=1e-4)


def test_dose_doppia_concentrazione_doppia():
    """Il modello è lineare: 10 mg/kg danno esattamente il doppio di 5 mg/kg."""
    tempi = np.linspace(0, 378, 500)
    c5 = sim.concentrazione(tempi, TIPICO, sim.Schema(mg_per_kg=5).dosi(PESO))
    c10 = sim.concentrazione(tempi, TIPICO, sim.Schema(mg_per_kg=10).dosi(PESO))
    assert np.allclose(c10, 2 * c5, rtol=1e-12)


def test_prima_della_prima_infusione_concentrazione_zero():
    c = sim.concentrazione([-1.0, 0.0], TIPICO, sim.Schema().dosi(PESO))
    assert np.all(c == 0)


def test_la_curva_contiene_picchi_e_valli_esatti():
    settimane, c = sim.curva(TIPICO, sim.Schema(), PESO)
    fine_infusione_2 = (14 + m.DURATA_INFUSIONE_GIORNI) / 7
    assert np.any(np.isclose(settimane, fine_infusione_2))  # il picco è nella curva
    assert settimane[np.argmax(c)] == pytest.approx(fine_infusione_2)
    assert settimane[0] == 0 and settimane[-1] == 54


def test_valli_e_prima_valle_sotto_soglia_paziente_tipico():
    valli = sim.concentrazioni_minime(TIPICO, sim.Schema(), PESO)
    assert [s for s, _ in valli] == [2, 6, 14, 22, 30, 38, 46, 54]
    # Con soglia 3 µg/mL la prima valle sotto soglia è alla settimana 22.
    settimana, valore = sim.primo_minimo_sotto_soglia(valli, 3.0)
    assert settimana == 22 and valore < 3.0
    assert sim.primo_minimo_sotto_soglia(valli, 0.5) is None


def test_periodi_sotto_soglia():
    schema = sim.Schema()
    dosi = schema.dosi(PESO)
    periodi = sim.periodi_sotto_soglia(TIPICO, schema, PESO, 3.0)
    assert len(periodi) == 5  # prima delle dosi delle settimane 22, 30, 38, 46 e a fine 54
    for inizio, fine in periodi:
        assert inizio < fine
        # nel punto di discesa la concentrazione vale esattamente la soglia
        assert sim.concentrazione(inizio * 7, TIPICO, dosi)[0] == pytest.approx(3.0, abs=1e-6)
        # a metà del periodo è sotto soglia
        assert sim.concentrazione((inizio + fine) / 2 * 7, TIPICO, dosi)[0] < 3.0
    # Soglia molto bassa: mai sotto. Soglia altissima: sotto da subito dopo ogni infusione.
    assert sim.periodi_sotto_soglia(TIPICO, schema, PESO, 0.5) == []
    assert len(sim.periodi_sotto_soglia(TIPICO, schema, PESO, 1000.0)) == 8
