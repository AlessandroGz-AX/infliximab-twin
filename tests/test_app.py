"""
Controlli dell'app Streamlit: parte senza errori, mostra avvertenza e limiti,
reagisce ai dati inseriti.

Per farli girare, dalla cartella del progetto:   python -m pytest
"""

from streamlit.testing.v1 import AppTest

from gemello import AVVERTENZA, LIMITI


def avvia_app() -> AppTest:
    app = AppTest.from_file("../app.py", default_timeout=60)
    app.run()
    assert not app.exception, app.exception
    return app


def unisci_testo(elementi) -> str:
    return " ".join(str(e.value) for e in elementi)


def test_l_app_parte_e_mostra_avvertenza_e_limiti():
    app = avvia_app()
    assert AVVERTENZA in unisci_testo(app.error)
    tutto_il_testo = unisci_testo(app.markdown)
    for limite in LIMITI:
        assert limite in tutto_il_testo


def test_paziente_tipico_prima_valle_sotto_3_alla_settimana_22():
    app = avvia_app()
    riquadri = {r.label: r.value for r in app.metric}
    assert riquadri["Prima valle sotto soglia"] == "Sett. 22"
    assert "settimana 22" in unisci_testo(app.warning)


def test_donna_tipica_resta_sopra_soglia():
    app = avvia_app()
    app.sidebar.radio[0].set_value("Donna").run()
    riquadri = {r.label: r.value for r in app.metric}
    assert riquadri["Prima valle sotto soglia"] == "Nessuna"
    assert len(app.success) == 1


def test_settimane_scritte_male_danno_un_messaggio_chiaro():
    app = avvia_app()
    app.sidebar.text_input[0].set_value("zero, due").run()
    assert not app.exception
    assert "numeri separati da virgole" in unisci_testo(app.error)
    app.sidebar.text_input[0].set_value("2, 6").run()
    assert "settimana 0" in unisci_testo(app.error)


def test_avviso_se_il_peso_e_fuori_dallo_studio():
    app = avvia_app()
    app.sidebar.number_input[0].set_value(30.0).run()
    assert "estrapolando" in unisci_testo(app.warning)
