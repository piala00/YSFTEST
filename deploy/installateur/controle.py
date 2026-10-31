"""Contrôle embarqué de l'installateur ; jamais de clé privée, jamais de lecture d'une base métier."""
import argparse
from pathlib import Path
import sys

if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from apps.licences import licence as l
from apps.licences.installation import autoriser
from apps.licences.nettoyage import MARQUEUR, marquer, sur


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--edition", required=True, choices=("transport", "commerce"))
    p.add_argument("--verifier", type=Path)
    p.add_argument("--dossier-cible", type=Path)
    p.add_argument("--marquer-programme", type=Path)
    p.add_argument("--marquer-donnees", type=Path)
    p.add_argument("--rapport", required=True, type=Path)
    a = p.parse_args(argv)
    try:
        if (a.marquer_programme or a.marquer_donnees) and (a.verifier or a.dossier_cible):
            raise ValueError("Le marquage et la vérification d'autorisation sont des actions distinctes.")
        if a.dossier_cible:
            cible = sur(a.dossier_cible)
            marqueur = cible / MARQUEUR
            if marqueur.exists():
                sur(marqueur)
                if marqueur.read_text(encoding="utf-8") != a.edition:
                    raise ValueError("Le dossier choisi appartient à une autre édition.")
            elif cible.exists() and any(cible.iterdir()) and not (cible / f"ERP-OHADA-{a.edition.capitalize()}.exe").is_file():
                raise ValueError("Choisissez un dossier vide réservé à cette édition.")
        if a.marquer_programme or a.marquer_donnees:
            for dossier in (a.marquer_programme, a.marquer_donnees):
                if dossier:
                    marquer(dossier, a.edition)
            a.rapport.write_text("Dossiers de cette édition identifiés ; fichiers inconnus toujours préservés.", encoding="utf-8")
            return 0
        if a.verifier:
            with a.verifier.open("rb") as f:
                resultat = autoriser(f.read(65537), a.edition)
            message = f"Autorisation vérifiée : {resultat['numero']} ({a.edition})."
        else:
            message = a.edition[0].upper() + "-" + l.empreinte_machine()
        a.rapport.write_text(message, encoding="utf-8")
        return 0
    except (l.LicenceInvalide, ValueError, OSError) as exc:
        a.rapport.write_text("Installation refusée : " + str(exc), encoding="utf-8")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
