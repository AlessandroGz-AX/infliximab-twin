"""
Simulatore: concentrazione di infliximab nel sangue nel tempo.

Il modello dell'articolo è lineare (eliminazione del primo ordine, p. 1213):
l'effetto di ogni infusione si somma a quello delle altre (principio di
sovrapposizione). Per un modello a due compartimenti con infusione a
velocità costante esiste una formula esatta, che usiamo qui al posto di
approssimazioni numeriche. Un test la confronta con un'integrazione
numerica indipendente delle equazioni differenziali del modello.

Unità: tempo in giorni (le settimane solo per input e output),
dosi in mg, concentrazioni in µg/mL.
"""

from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq

from gemello import modello as m

GIORNI_PER_SETTIMANA = 7.0


@dataclass(frozen=True)
class Schema:
    """
    Schema di terapia. Di default è quello degli studi ACT (p. 1212):
    5 mg/kg alle settimane 0, 2 e 6, poi ogni 8 settimane; simuliamo 54
    settimane.
    """

    mg_per_kg: float = 5.0
    settimane_induzione: tuple[float, ...] = (0.0, 2.0, 6.0)
    intervallo_mantenimento_settimane: float = 8.0
    durata_settimane: float = 54.0

    def __post_init__(self):
        if self.mg_per_kg <= 0:
            raise ValueError("La dose deve essere maggiore di zero.")
        if self.intervallo_mantenimento_settimane <= 0:
            raise ValueError("L'intervallo di mantenimento deve essere maggiore di zero.")
        if self.durata_settimane <= 0:
            raise ValueError("La durata deve essere maggiore di zero.")

    def settimane_delle_dosi(self) -> list[float]:
        """Settimane in cui si fa un'infusione, dentro la durata simulata."""
        settimane = sorted(s for s in self.settimane_induzione
                           if 0 <= s < self.durata_settimane)
        if not settimane:
            return []
        prossima = settimane[-1] + self.intervallo_mantenimento_settimane
        while prossima < self.durata_settimane - 1e-9:
            settimane.append(prossima)
            prossima += self.intervallo_mantenimento_settimane
        return settimane

    def settimane_dei_minimi(self) -> list[float]:
        """
        Momenti della concentrazione minima ("valle"): subito prima di ogni
        infusione dalla seconda in poi, più la data dell'infusione che
        seguirebbe l'ultima, se rientra nella durata simulata.
        Con lo schema di default: settimane 2, 6, 14, 22, 30, 38, 46 e 54.
        """
        dosi = self.settimane_delle_dosi()
        if not dosi:
            return []
        minimi = dosi[1:]
        prossima = dosi[-1] + self.intervallo_mantenimento_settimane
        if prossima <= self.durata_settimane + 1e-9:
            minimi.append(prossima)
        return minimi

    def dosi(self, peso_kg: float) -> list[tuple[float, float]]:
        """Elenco delle infusioni come coppie (giorno, dose in mg)."""
        return [(s * GIORNI_PER_SETTIMANA, self.mg_per_kg * peso_kg)
                for s in self.settimane_delle_dosi()]


def concentrazione(tempi_giorni, parametri: m.ParametriPK,
                   dosi: list[tuple[float, float]],
                   durata_infusione: float = m.DURATA_INFUSIONE_GIORNI) -> np.ndarray:
    """
    Concentrazione nel sangue (µg/mL) ai tempi richiesti (in giorni).

    Formula esatta per una dose D infusa in un tempo T (velocità R = D/T),
    a un tempo d dall'inizio dell'infusione:
        C(d) = R * [ a/alfa * (exp(-alfa*(d-s)) - exp(-alfa*d))
                   + b/beta * (exp(-beta*(d-s)) - exp(-beta*d)) ]
    dove s = min(d, T) è la parte di infusione già fatta, e
        a = (alfa - k21) / (V1 * (alfa - beta))
        b = (k21 - beta) / (V1 * (alfa - beta))
    sono i pesi delle due fasi. I contributi delle dosi si sommano.
    Al momento esatto di inizio di un'infusione la formula dà il valore
    PRIMA dell'infusione (la concentrazione minima, o "valle").
    """
    t = np.atleast_1d(np.asarray(tempi_giorni, dtype=float))
    alfa, beta = m.costanti_di_velocita(parametri)
    k21 = parametri.Q / parametri.V2
    a = (alfa - k21) / (parametri.V1 * (alfa - beta))
    b = (k21 - beta) / (parametri.V1 * (alfa - beta))

    c = np.zeros_like(t)
    for giorno_dose, dose_mg in dosi:
        d = t - giorno_dose        # tempo trascorso dall'inizio di questa infusione
        attivo = d > 0             # prima dell'infusione il suo contributo è zero
        d = d[attivo]
        s = np.minimum(d, durata_infusione)
        velocita = dose_mg / durata_infusione  # mg/giorno
        c[attivo] += velocita * (
            a / alfa * (np.exp(-alfa * (d - s)) - np.exp(-alfa * d))
            + b / beta * (np.exp(-beta * (d - s)) - np.exp(-beta * d)))
    return c


def curva(parametri: m.ParametriPK, schema: Schema, peso_kg: float,
          punti_per_giorno: int = 4) -> tuple[np.ndarray, np.ndarray]:
    """Tempi (in settimane) e concentrazioni per disegnare la curva intera."""
    fine = schema.durata_settimane * GIORNI_PER_SETTIMANA
    dosi = schema.dosi(peso_kg)
    tempi = np.linspace(0.0, fine, int(fine * punti_per_giorno) + 1)
    # Aggiungo gli istanti esatti di inizio (valli) e fine infusione (picchi).
    speciali = [g for g, _ in dosi] + [g + m.DURATA_INFUSIONE_GIORNI for g, _ in dosi]
    tempi = np.unique(np.concatenate([tempi, [x for x in speciali if x <= fine]]))
    return tempi / GIORNI_PER_SETTIMANA, concentrazione(tempi, parametri, dosi)


def concentrazioni_minime(parametri: m.ParametriPK, schema: Schema,
                          peso_kg: float) -> list[tuple[float, float]]:
    """Coppie (settimana, concentrazione in µg/mL) nei momenti di valle."""
    settimane = schema.settimane_dei_minimi()
    valori = concentrazione(np.array(settimane) * GIORNI_PER_SETTIMANA,
                            parametri, schema.dosi(peso_kg))
    return list(zip(settimane, valori.tolist()))


def primo_minimo_sotto_soglia(minimi: list[tuple[float, float]],
                              soglia: float) -> tuple[float, float] | None:
    """Prima valle sotto la soglia, come (settimana, valore); None se non succede."""
    for settimana, valore in minimi:
        if valore < soglia:
            return settimana, valore
    return None


def periodi_sotto_soglia(parametri: m.ParametriPK, schema: Schema, peso_kg: float,
                         soglia: float) -> list[tuple[float, float]]:
    """
    Periodi (inizio, fine, in settimane) in cui la concentrazione è sotto
    la soglia, dopo la prima infusione. Finita un'infusione, la
    concentrazione scende sempre fino alla dose successiva: in ogni
    intervallo c'è al massimo un punto di discesa sotto soglia, che
    troviamo con precisione con il metodo di Brent.
    """
    dosi = schema.dosi(peso_kg)
    if not dosi:
        return []
    fine = schema.durata_settimane * GIORNI_PER_SETTIMANA
    confini = [g for g, _ in dosi] + [fine]

    def c(x: float) -> float:
        return float(concentrazione(x, parametri, dosi)[0])

    periodi = []
    for inizio, prossimo in zip(confini[:-1], confini[1:]):
        picco = min(inizio + m.DURATA_INFUSIONE_GIORNI, prossimo)
        if c(prossimo) >= soglia:
            continue  # resta sopra soglia fino alla dose successiva
        if c(picco) <= soglia:
            discesa = picco  # già sotto soglia alla fine dell'infusione
        else:
            discesa = brentq(lambda x: c(x) - soglia, picco, prossimo, xtol=1e-10)
        periodi.append((discesa / GIORNI_PER_SETTIMANA, prossimo / GIORNI_PER_SETTIMANA))
    return periodi
