"""ERP OHADA — Comptabilité analytique : fenêtre distincte, lecture des mêmes écritures générales."""
from pages import ECRANS_ANALYTIQUE
from shell import lancer

if __name__ == "__main__":
    lancer("analytique", ECRANS_ANALYTIQUE)
