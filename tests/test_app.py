"""
Controlli dell'app Streamlit: parte senza errori, mostra avvertenza e limiti,
reagisce ai dati inseriti.

Per farli girare, dalla cartella del progetto:   python -m pytest
"""

from datetime import date, timedelta

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


# ---------------------------------------------------------------------
# Passo 5: livelli misurati e schema alternativo
# (date di default: prima infusione 24 settimane fa, prelievo 10 settimane
# fa, cioè alla settimana 14, dove il paziente tipico avrebbe circa 3,25 µg/mL)
# ---------------------------------------------------------------------

def tabella_confronto(app):
    tabella = next(t.value for t in app.dataframe if "Alternativa B" in t.value.columns)
    return tabella.set_index("")


def test_caso_dimostrativo():
    """
    Valle di 1,2 µg/mL alla settimana 14 e confronto dalla settimana 14 tra
    10 mg/kg ogni 8 settimane (A) e 5 mg/kg ogni 4 settimane (B).
    """
    app = avvia_app()
    app.button(key="caso_dimostrativo").click().run()
    assert not app.exception
    messaggio = unisci_testo(app.info)
    assert "Curva aggiornata con 1 livello misurato" in messaggio
    assert "la clearance stimata è più alta" in messaggio
    assert "verificata solo su pazienti virtuali" in unisci_testo(app.caption)
    assert any("Dopo i livelli misurati" in tabella.value.columns for tabella in app.dataframe)

    righe = tabella_confronto(app)
    assert righe.loc["Schema dalla settimana 14", "Alternativa A"] == "10 mg/kg ogni 8 sett."
    assert righe.loc["Schema dalla settimana 14", "Alternativa B"] == "5 mg/kg ogni 4 sett."
    # Stessa quantità di farmaco, risultato opposto dopo il cambio.
    farmaco = "Farmaco totale in 54 settimane"
    assert righe.loc[farmaco, "Alternativa A"] == righe.loc[farmaco, "Alternativa B"] == "5.005 mg"
    dopo = "Prima valle sotto soglia dopo il cambio"
    assert righe.loc[dopo, "Schema attuale"] == "Settimana 22"
    assert righe.loc[dopo, "Alternativa A"] == "Settimana 22"
    assert righe.loc[dopo, "Alternativa B"] == "Nessuna"
    assert righe.loc["Giorni sotto soglia dopo il cambio", "Alternativa B"] == "0"

    frase = unisci_testo(app.info)
    assert "Caso dimostrativo" in frase
    assert "paziente virtuale, non un consiglio di terapia" in frase


def test_la_frase_del_caso_dimostrativo_sparisce_se_cambi_un_dato():
    app = avvia_app()
    app.button(key="caso_dimostrativo").click().run()
    app.number_input(key="dose_b").set_value(6.0).run()
    assert "Caso dimostrativo" not in unisci_testo(app.info)


def test_livello_inserito_a_mano_e_poi_tolto():
    app = avvia_app()
    app.number_input(key="valore_livello").set_value(8.0).run()
    app.button(key="aggiungi").click().run()
    assert "la clearance stimata è più bassa" in unisci_testo(app.info)  # 8 > 3,25 atteso
    app.button(key="rimuovi_0").click().run()
    assert len(app.info) == 0


def test_livello_non_dosabile_usato_con_il_metodo_M3():
    app = avvia_app()
    app.checkbox(key="non_dosabile").check().run()
    app.button(key="aggiungi").click().run()
    assert "metodo M3" in unisci_testo(app.caption)
    assert "la clearance stimata è più alta" in unisci_testo(app.info)


def test_prelievo_prima_della_prima_infusione_rifiutato():
    app = avvia_app()
    app.date_input(key="data_prelievo").set_value(date.today() - timedelta(weeks=30)).run()
    app.button(key="aggiungi").click().run()
    assert "successivo alla prima infusione" in unisci_testo(app.error)
    assert len(app.info) == 0


def test_confronto_con_schemi_alternativi_senza_livelli_misurati():
    """Di default, dalla settimana 14: A = 10 mg/kg ogni 8, B = 5 mg/kg ogni 4."""
    app = avvia_app()
    app.toggle(key="confronta").set_value(True).run()
    assert not app.exception
    righe = tabella_confronto(app)
    dopo = "Prima valle sotto soglia dopo il cambio"
    assert righe.loc[dopo, "Schema attuale"] == "Settimana 22"
    assert righe.loc[dopo, "Alternativa A"] == "Nessuna"
    assert righe.loc[dopo, "Alternativa B"] == "Nessuna"
    assert righe.loc["Farmaco totale in 54 settimane", "Schema attuale"] == "3.080 mg"
    # Senza il livello misurato non è il caso dimostrativo: niente frase.
    assert "Caso dimostrativo" not in unisci_testo(app.info)
