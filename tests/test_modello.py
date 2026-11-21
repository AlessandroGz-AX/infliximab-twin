"""
TEST 1 e TEST 2: il modello coincide con l'articolo.

Fonte: Fasanmade AA et al., Eur J Clin Pharmacol 2009;65:1211-28.
Per farli girare, dalla cartella del progetto:   python -m pytest
"""

import itertools

import numpy as np
import pytest

from gemello import modello as m


def paziente(peso=77.0, donna=False, albumina=4.1, anticorpi=False):
    """Scorciatoia: paziente tipico, salvo le caratteristiche indicate."""
    return m.Paziente(peso_kg=peso, donna=donna, albumina_g_dl=albumina, anticorpi=anticorpi)


# =====================================================================
# TEST 1 - Paziente tipico
# =====================================================================

def test_paziente_tipico_ha_i_parametri_della_tabella_3():
    p = m.parametri_tipici(m.PAZIENTE_TIPICO)
    assert p.CL == pytest.approx(0.407, rel=1e-12)  # L/giorno
    assert p.V1 == pytest.approx(3.29, rel=1e-12)   # L
    assert p.V2 == pytest.approx(4.13, rel=1e-12)   # L
    assert p.Q == pytest.approx(7.14, rel=1e-12)    # L/giorno


def test_emivita_terminale_del_paziente_tipico():
    """
    Dai quattro parametri tipici l'emivita terminale risulta 12,86 giorni.
    L'articolo scrive "circa 14 giorni", ma a p. 1221 chiarisce che 14 è la
    MEDIANA delle emivite calcolate sui singoli pazienti (intervallo
    interquartile 10,4-17,8 giorni). Il paziente tipico deve quindi cadere
    in quell'intervallo; il confronto con la mediana della popolazione è
    nel Test 3.
    """
    t = m.emivita_terminale_giorni(m.parametri_tipici(m.PAZIENTE_TIPICO))
    assert t == pytest.approx(12.86, abs=0.01)
    assert 10.4 <= t <= 17.8


def test_alfa_e_beta_coincidono_con_gli_autovalori_del_sistema():
    """Controllo indipendente della formula di alfa e beta con l'algebra lineare."""
    p = m.parametri_tipici(m.PAZIENTE_TIPICO)
    k10, k12, k21 = p.CL / p.V1, p.Q / p.V1, p.Q / p.V2
    matrice = np.array([[-(k10 + k12), k21],
                        [k12, -k21]])
    beta_numerico, alfa_numerico = sorted(-np.linalg.eigvals(matrice).real)
    alfa, beta = m.costanti_di_velocita(p)
    assert alfa == pytest.approx(alfa_numerico, rel=1e-10)
    assert beta == pytest.approx(beta_numerico, rel=1e-10)


def test_volume_allo_stato_stazionario_del_paziente_tipico():
    # V1 + V2 = 7,42 L. A p. 1221 l'articolo scrive 7,71 L: discrepanza
    # segnalata in docs/confronto_articolo.md.
    p = m.parametri_tipici(m.PAZIENTE_TIPICO)
    assert m.volume_stato_stazionario(p) == pytest.approx(7.42, abs=1e-9)


# =====================================================================
# TEST 2 - Effetti delle covariate = equazioni dell'articolo
# =====================================================================

PESI = [40.0, 60.0, 77.0, 100.0, 177.3]        # kg, dentro l'intervallo dello studio
ALBUMINE = [2.4, 3.0, 3.8, 4.1, 4.3, 5.2]      # g/dL, dentro l'intervallo dello studio
COMBINAZIONI = list(itertools.product(PESI, ALBUMINE, [False, True], [False, True]))


@pytest.mark.parametrize("peso,albumina,donna,anticorpi", COMBINAZIONI)
def test_equazioni_finali_stampate_a_pagina_1218(peso, albumina, donna, anticorpi):
    """Per 120 pazienti diversi, confronto con le equazioni scritte nell'articolo."""
    sex, ati = int(donna), int(anticorpi)
    cl_articolo = 0.407 * (albumina / 4.1) ** -1.54 * 1.471 ** ati * 0.764 ** sex
    v1_articolo = 3.29 * (peso / 77) ** 0.538 * 0.863 ** sex

    p = m.parametri_tipici(paziente(peso, donna, albumina, anticorpi))
    assert p.CL == pytest.approx(cl_articolo, rel=1e-12)
    assert p.V1 == pytest.approx(v1_articolo, rel=1e-12)
    assert p.V2 == 4.13
    assert p.Q == 7.14


def test_anticorpi_aumentano_la_clearance_del_47_1_percento():
    senza = m.parametri_tipici(paziente())
    con = m.parametri_tipici(paziente(anticorpi=True))
    assert con.CL / senza.CL == pytest.approx(1.471, rel=1e-12)  # p. 1220: "47.1% higher"
    assert con.V1 == senza.V1  # gli anticorpi non agiscono su V1


def test_nelle_donne_clearance_e_V1_sono_piu_basse_come_da_equazione():
    """
    Equazione finale (p. 1218): CL x 0,764 (-23,6%) e V1 x 0,863 (-13,7%).
    Il testo a p. 1220 parla di "circa 33%" e "16%": non torna con
    l'equazione. Vale l'equazione (vedi docs/confronto_articolo.md).
    """
    uomo = m.parametri_tipici(paziente())
    donna = m.parametri_tipici(paziente(donna=True))
    assert donna.CL / uomo.CL == pytest.approx(0.764, rel=1e-12)
    assert donna.V1 / uomo.V1 == pytest.approx(0.863, rel=1e-12)


def test_piu_albumina_vuol_dire_meno_clearance():
    albumine = np.linspace(2.4, 5.2, 29)
    clearance = [m.parametri_tipici(paziente(albumina=a)).CL for a in albumine]
    assert np.all(np.diff(clearance) < 0)

    # Intervallo interquartile dell'albumina nello studio: 3,8-4,3 g/dL (p. 1224)
    cl_38 = m.parametri_tipici(paziente(albumina=3.8)).CL
    cl_43 = m.parametri_tipici(paziente(albumina=4.3)).CL
    assert cl_38 / cl_43 == pytest.approx((4.3 / 3.8) ** 1.54, rel=1e-12)  # +21,0%

    # L'albumina non agisce sui volumi
    assert m.parametri_tipici(paziente(albumina=3.0)).V1 == pytest.approx(3.29)


def test_il_peso_agisce_solo_su_V1():
    for peso in PESI:
        p = m.parametri_tipici(paziente(peso=peso))
        assert p.V1 == pytest.approx(3.29 * (peso / 77) ** 0.538, rel=1e-12)
        assert p.CL == pytest.approx(0.407, rel=1e-12)
        assert (p.V2, p.Q) == (4.13, 7.14)


def test_variabilita_tra_pazienti_decisione_A():
    """
    Solo Tabella 3: omega = 0,3768 su CL e 0,2211 su V1 (deviazioni
    standard), nessuna variabilità su V2 e Q. P_i = P_tipico * exp(eta).
    """
    assert m.OMEGA_CL == pytest.approx(0.3768, rel=1e-12)
    assert m.OMEGA_V1 == pytest.approx(0.2211, rel=1e-12)
    assert m.parametri_individuali(m.PAZIENTE_TIPICO) == m.parametri_tipici(m.PAZIENTE_TIPICO)
    p = m.parametri_individuali(m.PAZIENTE_TIPICO, eta_cl=0.5, eta_v1=-0.2)
    assert p.CL == pytest.approx(0.407 * np.exp(0.5), rel=1e-12)
    assert p.V1 == pytest.approx(3.29 * np.exp(-0.2), rel=1e-12)
    assert (p.V2, p.Q) == (4.13, 7.14)


def test_documentazione_allineata_al_codice():
    """
    docs/confronto_articolo.md deve contenere la tabella prodotta dal codice
    attuale, e sia la pagina sia il README devono riportare i limiti del
    modello (gemello.LIMITI, gli stessi mostrati nell'app).
    """
    from gemello import documentazione as doc
    from gemello.confronto_articolo import tabella_markdown

    messaggio = "Rigenera con: python -m gemello.documentazione"
    pagina = doc.PAGINA_CONFRONTO.read_text(encoding="utf-8")
    readme = doc.README.read_text(encoding="utf-8")
    assert tabella_markdown() in pagina, messaggio
    assert doc.elenco_limiti() in pagina, messaggio
    assert doc.elenco_limiti() in readme, messaggio


def test_avvisi_fuori_dagli_intervalli_dello_studio():
    assert m.avvisi_estrapolazione(m.PAZIENTE_TIPICO) == []
    assert len(m.avvisi_estrapolazione(paziente(peso=30))) == 1
    assert len(m.avvisi_estrapolazione(paziente(albumina=2.0))) == 1
    with pytest.raises(ValueError):
        m.parametri_tipici(paziente(peso=0))
