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


def verifier_emission(publique, fichier):
    """Vérifie indépendamment la preuve émise par le vrai outil propriétaire compilé."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from apps.licences import format_cles as fc
    from apps.licences.identite import lire_publique

    brut = lire_publique(Path(publique).read_bytes())
    donnees, signature = fc.autorisation_lire(Path(fichier).read_bytes())
    Ed25519PublicKey.from_public_bytes(brut).verify(signature, fc.DOMAINE_AUTORISATION + fc.canonique(donnees))
    assert donnees["key_id"] == hashlib.sha256(brut).hexdigest().upper()
    assert donnees["version"] == 1 and donnees["edition"] == "transport"
    assert donnees["machine"] == "AAAA-BBBB-CCCC-DDDD"
    assert fc.est_installation_courte(donnees["reference"])
    assert datetime.date.fromisoformat(donnees["valable_jusqu_au"]) >= datetime.date.today()
    print("Outil propriétaire compilé : autorisation .erpinst émise, signature et conditions vérifiées avec son public.")


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
    try:
        n.sauvegarder(plan, archive)
    except (ValueError, OSError):
        courant = n.inventorier(programme, donnees, edition)
        rapport = {"avant": plan, "apres": courant}
        (temporaire / f"NETTOYAGE-DIAGNOSTIC-{edition}.json").write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Inventaire du runner modifié ; diagnostic sauvegardé, aucune suppression exécutée.")
        raise
    resultat = n.effacer(plan, archive, confirmation=True)
    (temporaire / f"NETTOYAGE-DIAGNOSTIC-suppression-{edition}.json").write_text(
        json.dumps(resultat, ensure_ascii=False, indent=2), encoding="utf-8")
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
    elif sys.argv[1] == "verifier-emission":
        verifier_emission(sys.argv[2], sys.argv[3])
    else:
        nettoyer(sys.argv[2], sys.argv[3], sys.argv[4])
