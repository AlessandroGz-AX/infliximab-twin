"""
Gemello digitale dell'infliximab - prototipo dimostrativo.

Modello (unica fonte): Fasanmade AA et al. "Population pharmacokinetic
analysis of infliximab in patients with ulcerative colitis".
Eur J Clin Pharmacol 2009;65:1211-1228.
"""

# Testo dell'avvertenza, riusato ovunque serva (app, documenti, output).
AVVERTENZA = (
    "PROTOTIPO DIMOSTRATIVO. Non è un dispositivo medico e non deve mai "
    "essere usato per decidere la terapia di pazienti reali."
)

# Limiti del modello, mostrati nel README, in docs/confronto_articolo.md
# e nell'app. Ogni frase è verificabile sull'articolo.
LIMITI = [
    "Variabilità tra pazienti presa solo dalla Tabella 3 dell'articolo: "
    "37,68% sulla clearance (CL) e 22,11% sul volume centrale (V1), senza "
    "correlazione tra le due e senza variabilità su V2 e Q. L'articolo dice "
    "che una correlazione CL-V1 era stimata, ma non ne pubblica il valore.",
    "Il modello viene da adulti (18-81 anni) con colite ulcerosa da moderata "
    "a grave, trattati negli studi ACT 1 e ACT 2 con 5 o 10 mg/kg: non vale "
    "automaticamente per altre malattie, per i bambini o per altri dosaggi.",
    "Gli anticorpi anti-infliximab sono un sì/no valido per tutta la terapia, "
    "come nell'articolo, non dal momento in cui compaiono.",
    "Peso e albumina sono i valori di partenza e restano costanti per tutta "
    "la simulazione, come nell'articolo.",
    "I livelli sotto 0,1 µg/mL (il limite di quantificazione dello studio) non "
    "vengono usati dalla stima bayesiana, perché l'articolo non dice come li ha "
    "trattati. Un livello non dosabile, che spesso indica una clearance alta o "
    "la presenza di anticorpi, oggi quindi non sposta la curva.",
]
