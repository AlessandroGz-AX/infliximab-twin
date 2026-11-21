"""
Stima bayesiana dei parametri di UN paziente a partire dai suoi livelli misurati.

Metodo: massima a posteriori (MAP). Cerchiamo i valori di eta_CL ed eta_V1
che rendono più plausibili, insieme:
  - i livelli misurati, tenendo conto dell'errore di misura del modello
    (errore residuo combinato: p. 1214 e Tabella 3);
  - quello che sappiamo in partenza sulla popolazione, cioè quanto i
    pazienti differiscono tra loro (variabilità: Tabella 3, decisione A).
Con poche misure la stima resta vicina al paziente tipico; con molte
misure segue soprattutto i dati.

In pratica minimizziamo (meno due volte il logaritmo della probabilità a
posteriori, a meno di una costante):
    somma sulle misure di [ (misura - previsione)^2 / varianza + ln(varianza) ]
    + (eta_CL / omega_CL)^2 + (eta_V1 / omega_V1)^2
con varianza = (sigma_prop * previsione)^2 + sigma_add^2.

I livelli sotto il limite di quantificazione dello studio (0,1 µg/mL,
p. 1213) NON vengono usati: l'articolo non spiega come li ha trattati
nella stima, e non inventiamo un metodo.
"""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize

from gemello import modello as m
from gemello import simulazione as sim


@dataclass(frozen=True)
class Misura:
    """Un livello di infliximab misurato nel sangue."""

    giorno: float  # giorni dall'inizio della prima infusione
    valore: float  # µg/mL


@dataclass(frozen=True)
class Stima:
    """Risultato della stima bayesiana per un paziente."""

    eta_cl: float
    eta_v1: float
    parametri: m.ParametriPK
    misure_usate: tuple[Misura, ...]
    misure_escluse: tuple[Misura, ...]  # sotto il limite di quantificazione


def funzione_obiettivo(eta, paziente: m.Paziente, dosi, misure) -> float:
    """Quanto è "implausibile" la coppia eta = (eta_CL, eta_V1): più basso è, meglio è."""
    parametri = m.parametri_individuali(paziente, eta[0], eta[1])
    giorni = np.array([x.giorno for x in misure])
    osservati = np.array([x.valore for x in misure])
    previsti = sim.concentrazione(giorni, parametri, dosi)
    varianza = (m.SIGMA_PROPORZIONALE * previsti) ** 2 + m.SIGMA_ADDITIVO ** 2
    parte_dati = np.sum((osservati - previsti) ** 2 / varianza + np.log(varianza))
    parte_popolazione = (eta[0] / m.OMEGA_CL) ** 2 + (eta[1] / m.OMEGA_V1) ** 2
    return float(parte_dati + parte_popolazione)


def stima_map(paziente: m.Paziente, dosi: list[tuple[float, float]],
              misure: list[Misura]) -> Stima:
    """
    Stima bayesiana (massima a posteriori) dei parametri del paziente.
    `dosi` sono le infusioni fatte davvero, come coppie (giorno, mg).
    """
    if not dosi:
        raise ValueError("Serve almeno un'infusione.")
    prima_infusione = min(giorno for giorno, _ in dosi)
    for x in misure:
        if x.giorno <= prima_infusione or not np.isfinite(x.valore):
            raise ValueError("Ogni misura deve avere un valore e venire dopo "
                             "l'inizio della prima infusione.")

    usate = tuple(x for x in misure if x.valore >= m.LLOQ)
    escluse = tuple(x for x in misure if x.valore < m.LLOQ)
    if not usate:  # nessuna informazione utile: resta il paziente tipico
        return Stima(0.0, 0.0, m.parametri_tipici(paziente), usate, escluse)

    # Ricerca del minimo (metodo di Nelder-Mead) da tre punti di partenza,
    # per non fermarsi in un minimo locale.
    migliore = None
    for partenza in [(0.0, 0.0), (1.5 * m.OMEGA_CL, 0.0), (-1.5 * m.OMEGA_CL, 0.0)]:
        a, b = partenza
        risultato = minimize(
            funzione_obiettivo, partenza, args=(paziente, dosi, usate),
            method="Nelder-Mead",
            options=dict(initial_simplex=[[a, b], [a + 0.2, b], [a, b + 0.2]],
                         xatol=1e-7, fatol=1e-10, maxiter=5000))
        if migliore is None or risultato.fun < migliore.fun:
            migliore = risultato

    eta_cl, eta_v1 = (float(x) for x in migliore.x)
    return Stima(eta_cl, eta_v1, m.parametri_individuali(paziente, eta_cl, eta_v1),
                 usate, escluse)
