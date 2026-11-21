"""
Modello farmacocinetico di popolazione dell'infliximab nella colite ulcerosa.

FONTE UNICA
    Fasanmade AA, Adedokun OJ, Ford J, Hernandez D, Johanns J, Hu C,
    Davis HM, Zhou H. "Population pharmacokinetic analysis of infliximab
    in patients with ulcerative colitis". Eur J Clin Pharmacol
    2009;65:1211-1228. https://pmc.ncbi.nlm.nih.gov/articles/PMC2778780/

Accanto a ogni numero c'è la pagina o la tabella dell'articolo da cui
viene. Nessun valore è stato stimato da noi, arrotondato o preso da altre
fonti. Dove l'articolo è ambiguo lo diciamo esplicitamente.

STRUTTURA DEL MODELLO (p. 1213, 1216, 1218)
    - due compartimenti: centrale (volume V1: il sangue e i tessuti molto
      irrorati) e periferico (volume V2);
    - il farmaco entra nel compartimento centrale con un'infusione
      endovenosa a velocità costante, di circa 2 ore (p. 1212);
    - esce dal compartimento centrale con un'eliminazione del primo
      ordine (clearance CL);
    - i due compartimenti si scambiano farmaco con la clearance
      intercompartimentale Q.

UNITÀ USATE IN TUTTO IL PROGETTO
    tempo in giorni, volumi in L, clearance in L/giorno, dose in mg,
    concentrazioni in mg/L (che equivale a µg/mL).
"""

from dataclasses import dataclass
import math

# ======================================================================
# 1) VALORI TIPICI DEL MODELLO FINALE
#    Tabella 3, sezione "Final model", colonna "NONMEM Estimate" (p. 1218).
#    Valgono per il paziente di riferimento: uomo, 77 kg, albumina
#    4,1 g/dL, senza anticorpi anti-infliximab.
# ======================================================================
CL_TIPICA = 0.407  # L/giorno - clearance
V1_TIPICO = 3.29   # L        - volume del compartimento centrale
V2_TIPICO = 4.13   # L        - volume del compartimento periferico
Q_TIPICA = 7.14    # L/giorno - clearance intercompartimentale

# ======================================================================
# 2) EFFETTI DELLE COVARIATE (Tabella 3, p. 1218)
#    Covariate continue (p. 1214):  P = P_tipico * (cov / mediana) ** theta
#    Covariate sì/no   (p. 1214):  P = P_tipico * (1 + cov * theta)
#                                   con cov = 0 (riferimento) oppure 1
# ======================================================================
THETA_ALB_CL = -1.54   # esponente dell'albumina su CL (più albumina -> meno CL)
THETA_ATI_CL = 0.471   # anticorpi anti-infliximab su CL -> CL x 1,471
THETA_SEX_CL = -0.236  # sesso femminile su CL           -> CL x 0,764
THETA_WGT_V1 = 0.538   # esponente del peso su V1
THETA_SEX_V1 = -0.137  # sesso femminile su V1           -> V1 x 0,863

# Valori di riferimento = mediane della popolazione studiata
# (equazioni finali a p. 1218; Tabella 2 a p. 1217).
ALBUMINA_RIFERIMENTO = 4.1  # g/dL
PESO_RIFERIMENTO = 77.0     # kg

# Intervalli osservati nello studio (Tabella 2, p. 1217: minimo e massimo).
# Fuori da questi intervalli il modello sta estrapolando.
PESO_MIN_STUDIO, PESO_MAX_STUDIO = 40.0, 177.3        # kg
ALBUMINA_MIN_STUDIO, ALBUMINA_MAX_STUDIO = 2.4, 5.2   # g/dL

# ======================================================================
# 3) VARIABILITÀ TRA PAZIENTI (IIV) - Tabella 3, p. 1218
#    Ogni paziente ha i suoi parametri: P_i = P_tipico * exp(eta_i), dove
#    eta_i segue una normale di media 0 e varianza omega^2 (p. 1213-1214).
#    L'articolo riporta la IIV solo come percentuale.
#    Per V2 e Q la Tabella 3 riporta "–": nessuna IIV stimata.
# ======================================================================
IIV_CL_PERCENTO = 37.68
IIV_V1_PERCENTO = 22.11

# DECISIONE DI ALESSANDRO (opzione A): si usa solo la Tabella 3.
#  - omega = percentuale / 100, intesa come deviazione standard di eta
#    (lo stesso modo in cui l'articolo riporta l'errore residuo);
#  - nessuna correlazione tra eta_CL ed eta_V1: a p. 1216 l'articolo dice
#    che la covarianza era stimata, ma non ne pubblica il valore;
#  - nessuna variabilità su V2 e Q (Tabella 3: "–"), anche se il testo a
#    p. 1216 accenna a un blocco "simile" per V2 e Q.
# È un limite del prototipo, dichiarato in README, docs e app.
OMEGA_CL = IIV_CL_PERCENTO / 100  # deviazione standard di eta_CL (0,3768)
OMEGA_V1 = IIV_V1_PERCENTO / 100  # deviazione standard di eta_V1 (0,2211)

# ======================================================================
# 4) ERRORE RESIDUO: modello combinato proporzionale + additivo
#    Equazione a p. 1214:   Y = C * (1 + eps1) + eps2
#    eps1 ~ N(0, sigma1^2), eps2 ~ N(0, sigma2^2), valori in Tabella 3.
#    Le sigma sono deviazioni standard: la Tabella 1 (p. 1216) le indica
#    come sigma (non sigma^2) e i suoi valori (0,399 e 0,411) tornano con
#    il 40,2% che la Tabella 3 riporta per il modello base.
# ======================================================================
SIGMA_PROPORZIONALE = 0.403  # 40,30 %
SIGMA_ADDITIVO = 0.0413      # µg/mL

# ======================================================================
# 5) ALTRI DATI DELLO STUDIO
# ======================================================================
DURATA_INFUSIONE_GIORNI = 2.0 / 24.0  # "approximately 2 h" (p. 1212)
LLOQ = 0.1  # µg/mL: sotto questo valore il dosaggio non misura (p. 1213)


@dataclass(frozen=True)
class Paziente:
    """Le quattro caratteristiche del paziente usate dal modello finale."""

    peso_kg: float
    donna: bool
    albumina_g_dl: float  # albumina sierica al basale in g/dL (41 g/L = 4,1 g/dL)
    anticorpi: bool       # anticorpi anti-infliximab (ATI) positivi


@dataclass(frozen=True)
class ParametriPK:
    """I quattro parametri farmacocinetici di un paziente."""

    CL: float  # L/giorno
    V1: float  # L
    V2: float  # L
    Q: float   # L/giorno


# Il paziente di riferimento dell'articolo (valori mediani, uomo, ATI negativo).
PAZIENTE_TIPICO = Paziente(peso_kg=77.0, donna=False, albumina_g_dl=4.1, anticorpi=False)


def parametri_tipici(paziente: Paziente) -> ParametriPK:
    """
    Parametri attesi per un paziente con queste caratteristiche PRIMA di
    conoscere i suoi livelli di farmaco (cioè senza variabilità individuale).

    Equazioni del modello finale (p. 1218):
        CL = 0,407 * (ALB/4,1)^-1,54 * 1,471^ATI * 0,764^SEX
        V1 = 3,29  * (PESO/77)^0,538 * 0,863^SEX
        Q  = 7,14
        V2 = 4,13
    con ATI = 1 se anticorpi positivi e SEX = 1 se donna (0 altrimenti).
    """
    if paziente.peso_kg <= 0 or paziente.albumina_g_dl <= 0:
        raise ValueError("Peso e albumina devono essere maggiori di zero.")
    sex = 1 if paziente.donna else 0
    ati = 1 if paziente.anticorpi else 0

    CL = (CL_TIPICA
          * (paziente.albumina_g_dl / ALBUMINA_RIFERIMENTO) ** THETA_ALB_CL
          * (1 + THETA_ATI_CL * ati)
          * (1 + THETA_SEX_CL * sex))
    V1 = (V1_TIPICO
          * (paziente.peso_kg / PESO_RIFERIMENTO) ** THETA_WGT_V1
          * (1 + THETA_SEX_V1 * sex))
    return ParametriPK(CL=CL, V1=V1, V2=V2_TIPICO, Q=Q_TIPICA)


def parametri_individuali(paziente: Paziente, eta_cl: float = 0.0,
                          eta_v1: float = 0.0) -> ParametriPK:
    """
    Parametri di UN paziente specifico: quelli tipici per le sue
    caratteristiche, spostati dalla sua variabilità individuale (eta).
    Formula dell'articolo (p. 1213): P_i = P_tipico * exp(eta_i).
    eta = 0 vuol dire "esattamente come il paziente tipico con quelle
    caratteristiche". V2 e Q non hanno variabilità (decisione A).
    """
    tipici = parametri_tipici(paziente)
    return ParametriPK(CL=tipici.CL * math.exp(eta_cl),
                       V1=tipici.V1 * math.exp(eta_v1),
                       V2=tipici.V2, Q=tipici.Q)


def avvisi_estrapolazione(paziente: Paziente) -> list[str]:
    """Messaggi di avviso se il paziente è fuori dagli intervalli dello studio."""
    avvisi = []
    if not PESO_MIN_STUDIO <= paziente.peso_kg <= PESO_MAX_STUDIO:
        avvisi.append(
            f"Peso fuori dall'intervallo dello studio ({PESO_MIN_STUDIO:g}-"
            f"{PESO_MAX_STUDIO:g} kg): il modello sta estrapolando."
        )
    if not ALBUMINA_MIN_STUDIO <= paziente.albumina_g_dl <= ALBUMINA_MAX_STUDIO:
        avvisi.append(
            f"Albumina fuori dall'intervallo dello studio ({ALBUMINA_MIN_STUDIO:g}-"
            f"{ALBUMINA_MAX_STUDIO:g} g/dL): il modello sta estrapolando."
        )
    return avvisi


def costanti_di_velocita(p: ParametriPK) -> tuple[float, float]:
    """
    Velocità (1/giorno) delle due fasi in cui la concentrazione scende:
    alfa = fase rapida di distribuzione, beta = fase terminale lenta.
    Sono le soluzioni dell'equazione caratteristica del modello a due
    compartimenti (formula standard di farmacocinetica).
    """
    k10 = p.CL / p.V1  # eliminazione dal compartimento centrale
    k12 = p.Q / p.V1   # passaggio centrale -> periferico
    k21 = p.Q / p.V2   # passaggio periferico -> centrale
    somma = k10 + k12 + k21
    alfa = (somma + math.sqrt(somma ** 2 - 4 * k10 * k21)) / 2
    beta = k10 * k21 / alfa  # perché alfa * beta = k10 * k21 (forma più stabile)
    return alfa, beta


def emivita_terminale_giorni(p: ParametriPK) -> float:
    """Giorni in cui la concentrazione si dimezza nella fase terminale."""
    _, beta = costanti_di_velocita(p)
    return math.log(2) / beta


def volume_stato_stazionario(p: ParametriPK) -> float:
    """Volume di distribuzione allo stato stazionario (L) = V1 + V2."""
    return p.V1 + p.V2
