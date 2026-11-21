"""
Test 3: confronto del modello con valori osservati negli studi ACT 1 e 2.

Uso, dalla cartella del progetto:
    python -m gemello.validazione

Valori di riferimento:
 A) Fasanmade 2009, p. 1221: emivita mediana calcolata sui singoli
    pazienti circa 14 giorni, intervallo interquartile 10,4-17,8 giorni.
 B) Adedokun OJ et al., Gastroenterology 2014 (doi 10.1053/j.gastro.2014.08.035):
    livelli di infliximab misurati negli stessi studi ACT 1 e 2 con
    5 mg/kg. Mediane nei pazienti che rispondevano e in quelli che non
    rispondevano. Numeri forniti da Alessandro e NON ancora verificati
    sull'articolo originale: il sito dell'editore blocca l'accesso
    automatico.
"""

import numpy as np

from gemello import modello as m
from gemello import popolazione
from gemello import simulazione as sim

# Fasanmade 2009, p. 1221
EMIVITA_MEDIANA_ARTICOLO = 14.0
EMIVITA_IQR_ARTICOLO = (10.4, 17.8)

# Adedokun 2014, 5 mg/kg: settimana -> (non rispondevano, rispondevano), µg/mL.
# La settimana 8 non è un giorno di infusione (2 settimane dopo la dose della
# settimana 6); le settimane 30 e 54 sono concentrazioni minime (valle).
ADEDOKUN_2014 = {
    8: (25.8, 35.0),
    30: (1.2, 3.9),
    54: (0.7, 5.0),
}

SCHEMA_ACT = sim.Schema()  # 5 mg/kg alle settimane 0, 2, 6, poi ogni 8
N_VIRTUALI = 5000          # pazienti della popolazione virtuale
SEME = 2009                # seme fisso: risultati ripetibili


def livelli_alle_settimane(parametri: m.ParametriPK, peso_kg: float,
                           settimane=tuple(ADEDOKUN_2014)) -> dict[int, float]:
    """Concentrazione del modello (µg/mL) alle settimane richieste."""
    giorni = np.array(settimane, dtype=float) * sim.GIORNI_PER_SETTIMANA
    valori = sim.concentrazione(giorni, parametri, SCHEMA_ACT.dosi(peso_kg))
    return dict(zip(settimane, valori.tolist()))


def posizione(valore: float, non_risponde: float, risponde: float) -> float:
    """
    Dove cade il valore tra i due gruppi: 0% = mediana di chi non rispondeva,
    100% = mediana di chi rispondeva (fuori da 0-100% = fuori dai due valori).
    """
    return (valore - non_risponde) / (risponde - non_risponde) * 100


def emivite_popolazione(n: int = N_VIRTUALI, seme: int = SEME) -> np.ndarray:
    """Emivita terminale (giorni) di ogni paziente della popolazione virtuale."""
    return np.array([m.emivita_terminale_giorni(m.parametri_individuali(p, e_cl, e_v1))
                     for p, e_cl, e_v1 in popolazione.genera(n, seme)])


def livelli_popolazione(n: int = N_VIRTUALI, seme: int = SEME) -> dict[int, np.ndarray]:
    """Livelli alle settimane di Adedokun per ogni paziente virtuale."""
    risultati = {s: [] for s in ADEDOKUN_2014}
    for p, e_cl, e_v1 in popolazione.genera(n, seme):
        livelli = livelli_alle_settimane(m.parametri_individuali(p, e_cl, e_v1), p.peso_kg)
        for s, v in livelli.items():
            risultati[s].append(v)
    return {s: np.array(v) for s, v in risultati.items()}


def _num(x: float, decimali: int = 1) -> str:
    return f"{x:.{decimali}f}".replace(".", ",")


def rapporto() -> str:
    """Testo del confronto, in formato Markdown."""
    righe = []
    emivite = emivite_popolazione()
    q1, mediana, q3 = np.percentile(emivite, [25, 50, 75])
    righe += [
        f"### A) Emivita sulla popolazione virtuale ({N_VIRTUALI} pazienti)",
        "",
        "| | Articolo (p. 1221) | Modello |",
        "|---|---|---|",
        f"| Mediana | circa {_num(EMIVITA_MEDIANA_ARTICOLO)} giorni | {_num(mediana)} giorni |",
        f"| Intervallo interquartile | {_num(EMIVITA_IQR_ARTICOLO[0])}-{_num(EMIVITA_IQR_ARTICOLO[1])} "
        f"giorni | {_num(q1)}-{_num(q3)} giorni |",
        "",
    ]

    uomo = m.PAZIENTE_TIPICO
    donna = m.Paziente(peso_kg=77.0, donna=True, albumina_g_dl=4.1, anticorpi=False)
    liv_uomo = livelli_alle_settimane(m.parametri_tipici(uomo), uomo.peso_kg)
    liv_donna = livelli_alle_settimane(m.parametri_tipici(donna), donna.peso_kg)
    liv_pop = livelli_popolazione()
    righe += [
        "### B) Livelli misurati negli studi ACT, 5 mg/kg (Adedokun 2014, da verificare)",
        "",
        "| Momento | Non rispondevano | Rispondevano | Uomo tipico | Donna tipica "
        "| Mediana popolazione virtuale |",
        "|---|---|---|---|---|---|",
    ]
    for settimana, (no, si) in ADEDOKUN_2014.items():
        etichetta = "Settimana 8" if settimana == 8 else f"Valle settimana {settimana}"
        pop = float(np.median(liv_pop[settimana]))
        righe.append(
            f"| {etichetta} | {_num(no)} | {_num(si)} "
            f"| {_num(liv_uomo[settimana])} ({posizione(liv_uomo[settimana], no, si):.0f}%) "
            f"| {_num(liv_donna[settimana])} ({posizione(liv_donna[settimana], no, si):.0f}%) "
            f"| {_num(pop)} ({posizione(pop, no, si):.0f}%) |")
    righe += [
        "",
        "Valori in µg/mL. Tra parentesi la posizione tra i due gruppi: 0% = mediana di chi "
        "non rispondeva, 100% = mediana di chi rispondeva.",
    ]
    return "\n".join(righe)


if __name__ == "__main__":
    print(rapporto())
