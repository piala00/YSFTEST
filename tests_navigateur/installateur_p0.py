"""Recette Windows dans un runner jetable : preuve signée et inspection réelle après désinstallation."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from cryptography.hazmat.primitives import serialization

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))


def autorisation(outil, edition):
    from apps.licences import format_cles as fc
    dossier = Path(os.environ["RUNNER_TEMP"]) / "activation-fictive"
    rapport = dossier / "machine-controle.txt"
    subprocess.run([str(Path(outil).resolve()), "--edition", edition, "--rapport", str(rapport)], check=True)
    code = rapport.read_text(encoding="utf-8").strip()
    privee = serialization.load_der_private_key((dossier / "privee-fictive.der").read_bytes(), password=None)
    d = {"version": 1, "reference": fc.installation_courte_creer(), "edition": edition,
         "machine": code[2:], "valable_jusqu_au": None, "key_id": hashlib.sha256(privee.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)).hexdigest().upper(),
         "emise_le": datetime.date.today().isoformat()}
    fichier = dossier / f"autorisation-{edition}.erpinst"
    fichier.write_text(fc.autorisation_texte(d, privee.sign(fc.DOMAINE_AUTORISATION+fc.canonique(d))), encoding="utf-8")
    subprocess.run([str(Path(outil).resolve()), "--edition", edition, "--rapport", str(rapport), "--verifier", str(fichier)], check=True)
    d["machine"] = "AUTRE-PC"
    faux = dossier / "autre-machine.erpinst"
    faux.write_text(fc.autorisation_texte(d, privee.sign(fc.DOMAINE_AUTORISATION+fc.canonique(d))), encoding="utf-8")
    r = subprocess.run([str(Path(outil).resolve()), "--edition", edition, "--rapport", str(rapport), "--verifier", str(faux)])
    assert r.returncode == 2, "Le contrôle compilé a accepté une licence d'un autre PC."


def nettoyer(programme, donnees, edition):
    from apps.licences import nettoyage as n
    assert os.environ.get("GITHUB_ACTIONS") == "true", "Recette réservée au runner jetable."
    programme, donnees = Path(programme).resolve(), Path(donnees).resolve()
    temporaire = Path(os.environ["RUNNER_TEMP"]).resolve()
    assert temporaire in programme.parents, "Programme d'essai hors du répertoire temporaire."
    assert donnees == Path(os.environ["ProgramData"]).resolve() / "ERP-OHADA" / edition.capitalize()
    assert (donnees / n.MARQUEUR).read_text() == edition
    autre = donnees.parent / ("Commerce" if edition == "transport" else "Transport")
    assert not autre.exists(), "Dossier d'une autre édition préexistant : ne pas l'utiliser comme fixture."
    autre.mkdir()
    temoin = autre / "TEMOIN-FICTIF.txt"
    temoin.write_text("Autre édition : préserver")
    plan = n.inventorier(programme, donnees, edition)
    archive = temporaire / f"NETTOYAGE-{edition}.zip"
    n.sauvegarder(plan, archive)
    resultat = n.effacer(plan, archive, confirmation=True)
    assert not resultat["erreurs"], resultat["erreurs"]
    assert not donnees.exists(), f"Résidus données : {list(donnees.rglob('*'))}"
    assert not programme.exists(), f"Résidus programme : {list(programme.rglob('*'))}"
    assert temoin.read_text() == "Autre édition : préserver"
    n.verifier_sauvegarde(plan, archive)
    print(json.dumps({"edition": edition, "fichiers_supprimes": len(resultat["supprimes"]),
                      "verification": "Programme/données absents, sauvegarde relue, autre édition et parent préservés."}, ensure_ascii=False))


if __name__ == "__main__":
    if sys.argv[1] == "autorisation":
        autorisation(sys.argv[2], sys.argv[3])
    else:
        nettoyer(sys.argv[2], sys.argv[3], sys.argv[4])
