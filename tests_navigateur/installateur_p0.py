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


def autorisation(controle, emetteur, edition):
    """Émet le .erpinst avec le vrai outil propriétaire et le coffre lié à l'EXE testé."""
    from apps.licences import format_cles as fc
    from apps.licences.identite import lire_publique
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    dossier = Path(os.environ["RUNNER_TEMP"]) / "activation-fictive"
    coffre = dossier / "coffre-fictif.dat"
    publique = dossier / "parametres-fictif.dat"
    if not coffre.is_file() or not publique.is_file():
        raise FileNotFoundError("Coffre fictif chiffré ou identité publique absente du runner.")
    rapport = dossier / "machine-controle.txt"
    commande_controle = [str(Path(controle).resolve()), "--edition", edition,
                         "--rapport", str(rapport)]
    subprocess.run(commande_controle, check=True, capture_output=True, text=True)
    code = rapport.read_text(encoding="utf-8").strip()
    prefixe = {"transport": "T-", "commerce": "C-"}.get(edition)
    if not prefixe or not code.startswith(prefixe):
        raise AssertionError(f"Code matériel incompatible avec l'édition {edition}: {code!r}")

    environnement = os.environ.copy()
    environnement["ERP_LICENCES_MDP"] = "Fictif-CI-2026-Coffre"
    emission = subprocess.run([
        str(Path(emetteur).resolve()), "autoriser-installation",
        "--cle", str(coffre), "--code", code,
        "--jusqu-au", (datetime.date.today() + datetime.timedelta(days=2)).isoformat(),
        "--sortie", str(dossier),
    ], check=True, capture_output=True, text=True, env=environnement)
    chemins = [Path(ligne.strip()) for ligne in emission.stdout.splitlines()
               if ligne.strip().lower().endswith(".erpinst")]
    if not chemins:
        raise AssertionError("L'outil propriétaire n'a retourné aucun fichier .erpinst.")
    fichier = chemins[-1].resolve()
    if fichier.parent != dossier.resolve() or not fichier.is_file():
        raise AssertionError("Le fichier .erpinst émis est absent ou hors du dossier fictif.")

    donnees, signature = fc.autorisation_lire(fichier.read_bytes())
    cle_publique = lire_publique(publique.read_bytes())
    empreinte = hashlib.sha256(cle_publique).hexdigest().upper()
    if donnees.get("key_id") != empreinte:
        raise AssertionError("Le .erpinst signé n'utilise pas l'identité publique gravée dans l'installateur.")
    if donnees.get("edition") != edition or donnees.get("machine") != code[2:]:
        raise AssertionError("L'édition ou le serveur du .erpinst ne correspond pas à la demande.")
    subprocess.run(commande_controle + ["--verifier", str(fichier)],
                   check=True, capture_output=True, text=True)
    # Le script Inno Setup consomme un nom stable, quel que soit le nom haché généré par l'outil.
    fichier_attendu = dossier / f"autorisation-{edition}.erpinst"
    fichier_attendu.write_bytes(fichier.read_bytes())
    fichier = fichier_attendu

    cle_privee = serialization.load_der_private_key(
        coffre.read_bytes(), password=b"Fictif-CI-2026-Coffre"
    )

    def verifier_refus(libelle, contenu, signature_test):
        candidat = dossier / f"refus-{edition}-{libelle}.erpinst"
        candidat.write_text(fc.autorisation_texte(contenu, signature_test), encoding="utf-8")
        try:
            resultat = subprocess.run(
                commande_controle + ["--verifier", str(candidat)],
                capture_output=True, text=True, check=False,
            )
            if resultat.returncode != 2:
                raise AssertionError(
                    f"L'EXE de contrôle n'a pas refusé le cas {libelle} "
                    f"(code {resultat.returncode}): {resultat.stdout}\n{resultat.stderr}"
                )
        finally:
            candidat.unlink(missing_ok=True)

    autre_machine = dict(donnees)
    autre_machine["machine"] = "AUTRE-SERVEUR"
    verifier_refus("autre-serveur", autre_machine,
                   cle_privee.sign(fc.DOMAINE_AUTORISATION + fc.canonique(autre_machine)))

    autre_edition = dict(donnees)
    autre_edition["edition"] = "commerce" if edition == "transport" else "transport"
    verifier_refus("autre-edition", autre_edition,
                   cle_privee.sign(fc.DOMAINE_AUTORISATION + fc.canonique(autre_edition)))

    mauvaise_cle = Ed25519PrivateKey.generate()
    verifier_refus("autre-cle", dict(donnees),
                   mauvaise_cle.sign(fc.DOMAINE_AUTORISATION + fc.canonique(donnees)))

    signature_alteree = bytes([signature[0] ^ 1]) + signature[1:]
    verifier_refus("fichier-altere", dict(donnees), signature_alteree)

    preuve = {
        "edition": edition,
        "empreinte_publique": empreinte,
        "key_id": donnees["key_id"],
        "machine": code,
        "emetteur": str(Path(emetteur).resolve()),
        "installateur_controle": str(Path(controle).resolve()),
        "resultat": "OK",
        "cas_negatifs_refuses": ["autre-serveur", "autre-edition", "autre-cle", "fichier-altere"],
    }
    (dossier / f"autorisation-{edition}-preuve.json").write_text(
        json.dumps(preuve, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(preuve, ensure_ascii=False))


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
        autorisation(sys.argv[2], sys.argv[3], sys.argv[4])
    elif sys.argv[1] == "verifier-emission":
        verifier_emission(sys.argv[2], sys.argv[3])
    else:
        nettoyer(sys.argv[2], sys.argv[3], sys.argv[4])
