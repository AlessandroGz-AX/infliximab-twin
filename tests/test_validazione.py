"""
TEST 3: il modello riproduce i valori osservati negli studi ACT 1 e 2.

Valori confrontati (dettagli in gemello/validazione.py):
 A) Fasanmade 2009, p. 1221: emivita mediana sui singoli pazienti circa
    14 giorni, intervallo interquartile 10,4-17,8 giorni.
 B) Adedokun 2014 (doi 10.1053/j.gastro.2014.08.035), 5 mg/kg, mediane di
    chi rispondeva contro chi non rispondeva: settimana 8 35,0 contro 25,8;
    valle settimana 30 3,9 contro 1,2; valle settimana 54 5,0 contro
    0,7 µg/mL. Numeri forniti da Alessandro, ancora da verificare
    sull'articolo originale.

Margini fissati PRIMA di vedere i risultati:
 - emivita mediana: 14 ± 1 giorno ("circa 14" nell'articolo);
 - quartili: ± 1,5 giorni. La nostra popolazione ha la variabilità piena,
   mentre l'articolo usa le stime individuali, che sono un po' più
   strette (shrinkage, p. 1216);
 - livelli: il valore deve cadere tra le mediane dei due gruppi.
"""

import numpy as np
import pytest

from gemello import modello as m
from gemello import popolazione
from gemello import validazione as v


def test_la_popolazione_virtuale_somiglia_alla_tabella_2():
    """Controllo di buon senso sulla popolazione simulata (Tabella 2, p. 1217)."""
    pazienti = [p for p, _, _ in popolazione.genera(v.N_VIRTUALI, v.SEME)]
    pesi = np.array([p.peso_kg for p in pazienti])
    albumine = np.array([p.albumina_g_dl for p in pazienti])
    assert np.mean([p.donna for p in pazienti]) == pytest.approx(189 / 482, abs=0.02)
    assert np.mean([p.anticorpi for p in pazienti]) == pytest.approx(33 / 482, abs=0.01)
    assert np.median(pesi) == pytest.approx(77, abs=1.5)
    assert np.std(pesi) == pytest.approx(18.4, abs=1.5)
    assert np.mean(albumine) == pytest.approx(4.1, abs=0.03)
    assert pesi.min() >= 40 and pesi.max() <= 177.3
    assert albumine.min() >= 2.4 and albumine.max() <= 5.2


def test_A_emivita_mediana_della_popolazione_come_nell_articolo():
    q1, mediana, q3 = np.percentile(v.emivite_popolazione(), [25, 50, 75])
    assert mediana == pytest.approx(v.EMIVITA_MEDIANA_ARTICOLO, abs=1.0)
    assert q1 == pytest.approx(v.EMIVITA_IQR_ARTICOLO[0], abs=1.5)
    assert q3 == pytest.approx(v.EMIVITA_IQR_ARTICOLO[1], abs=1.5)


@pytest.mark.parametrize("settimana", list(v.ADEDOKUN_2014))
def test_B_paziente_tipico_tra_chi_rispondeva_e_chi_no(settimana):
    non_risponde, risponde = v.ADEDOKUN_2014[settimana]
    livello = v.livelli_alle_settimane(m.parametri_tipici(m.PAZIENTE_TIPICO),
                                       m.PAZIENTE_TIPICO.peso_kg)[settimana]
    assert non_risponde <= livello <= risponde


@pytest.mark.parametrize("settimana", list(v.ADEDOKUN_2014))
def test_B_mediana_della_popolazione_tra_chi_rispondeva_e_chi_no(settimana):
    non_risponde, risponde = v.ADEDOKUN_2014[settimana]
    mediana = float(np.median(v.livelli_popolazione()[settimana]))
    assert non_risponde <= mediana <= risponde
