"""
Rigenera le parti automatiche della documentazione a partire dal codice:
tabella di confronto con l'articolo, limiti del modello e risultati dei
test 3 e 4. Così i documenti non restano indietro rispetto al codice.

Uso, dalla cartella del progetto:
    python -m gemello.documentazione
"""

from pathlib import Path

from gemello import LIMITI
from gemello.confronto_articolo import tabella_markdown
from gemello.validazione import rapporto
from gemello.verifica_stima import rapporto as rapporto_stima

CARTELLA = Path(__file__).parent.parent
PAGINA_CONFRONTO = CARTELLA / "docs" / "confronto_articolo.md"
README = CARTELLA / "README.md"


def elenco_limiti() -> str:
    return "\n".join(f"- {limite}" for limite in LIMITI)


def _sostituisci(testo: str, nome: str, contenuto: str) -> str:
    """Rimpiazza il testo tra <!-- inizio nome --> e <!-- fine nome -->."""
    inizio, fine = f"<!-- inizio {nome} -->", f"<!-- fine {nome} -->"
    prima, resto = testo.split(inizio)
    _, dopo = resto.split(fine)
    return f"{prima}{inizio}\n{contenuto}\n{fine}{dopo}"


def aggiorna() -> None:
    testo = PAGINA_CONFRONTO.read_text(encoding="utf-8")
    testo = _sostituisci(testo, "tabella", tabella_markdown())
    testo = _sostituisci(testo, "limiti", elenco_limiti())
    testo = _sostituisci(testo, "test 3", rapporto())
    testo = _sostituisci(testo, "test 4", rapporto_stima())
    PAGINA_CONFRONTO.write_text(testo, encoding="utf-8")

    testo = README.read_text(encoding="utf-8")
    README.write_text(_sostituisci(testo, "limiti", elenco_limiti()), encoding="utf-8")


if __name__ == "__main__":
    aggiorna()
    print("Documentazione aggiornata.")
