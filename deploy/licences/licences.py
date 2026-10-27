"""Outil du PROPRIÉTAIRE pour émettre les licences de l'ERP OHADA (jamais livré aux clients).

    ERP-OHADA-Licences.exe                       menu (double-clic)
    ERP-OHADA-Licences.exe cles --dossier D      crée la paire de clés (une seule fois, sur VOTRE ordinateur)
    ERP-OHADA-Licences.exe emettre --cle D\\cle-privee.pem --client "…" --edition transport --role siege
                          --postes 10 --code T-ABCD-EFGH-IJKL-MNOP [--site SIEGE] [--niu …]
                          [--jusqu-au 2027-10-31 | --definitive] [--maj-jusqu-au 2027-10-31] [--sortie D]
    ERP-OHADA-Licences.exe verifier fichier.erplic --publique D\\cle-publique.txt

La clé privée est chiffrée par un mot de passe ; gardez-en une copie hors ligne (clé USB au coffre). Elle ne doit
JAMAIS être envoyée, ni déposée sur GitHub. Seule cle-publique.txt est copiée dans le logiciel (sans danger).
Chaque licence émise est inscrite dans registre-licences.csv, à côté de la clé privée.
"""
import argparse
import base64
import csv
import datetime
import getpass
import json
import os
import re
import sys
from pathlib import Path

ENTETE = "ERP-OHADA-LICENCE-V1"
EDITIONS = ("transport", "commerce", "toutes")
ROLES = ("seul", "siege", "agence")
CODE = re.compile(r"^[TCM]-([A-Z2-7]{4}-[A-Z2-7]{4}-[A-Z2-7]{4}-[A-Z2-7]{4})$")


def canonique(donnees):
    return json.dumps(donnees, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def mot_de_passe(confirmer=False):
    if os.environ.get("ERP_LICENCES_MDP"):                        # essais automatiques
        return os.environ["ERP_LICENCES_MDP"].encode()
    while True:
        mdp = getpass.getpass("Mot de passe de la clé privée : ")
        if not confirmer:
            return mdp.encode()
        if len(mdp) < 10:
            print("10 caractères au moins.")
        elif mdp == getpass.getpass("Confirmez : "):
            return mdp.encode()
        else:
            print("Différents, recommencez.")


def creer_cles(dossier):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    dossier = Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    privee, publique = dossier / "cle-privee.pem", dossier / "cle-publique.txt"
    if privee.exists():
        raise SystemExit(f"{privee} existe déjà : jamais remplacée (les licences déjà émises en dépendent).")
    cle = Ed25519PrivateKey.generate()
    privee.write_bytes(cle.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                         serialization.BestAvailableEncryption(mot_de_passe(confirmer=True))))
    brut = cle.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    publique.write_text(base64.b64encode(brut).decode() + "\n", encoding="utf-8")
    print(f"Clé privée : {privee}  (secrète ; copie de secours hors ligne)")
    print(f"Clé publique : {publique}  -> à copier dans apps/licences/cle_publique.txt du logiciel :")
    print("  " + publique.read_text().strip())


def charger_cle(chemin):
    from cryptography.hazmat.primitives import serialization

    try:
        return serialization.load_pem_private_key(Path(chemin).read_bytes(), password=mot_de_passe())
    except (ValueError, TypeError):
        raise SystemExit("Mot de passe incorrect ou fichier de clé illisible.")


def date_ou_rien(texte):
    if not texte:
        return None
    try:
        return datetime.date.fromisoformat(texte).isoformat()
    except ValueError:
        raise SystemExit(f"Date attendue au format AAAA-MM-JJ : {texte}")


def prochain_numero(registre):
    annee = datetime.date.today().year
    n = 0
    if registre.exists():
        with open(registre, encoding="utf-8", newline="") as f:
            for ligne in csv.DictReader(f, delimiter=";"):
                m = re.match(rf"LIC-{annee}-(\d+)$", ligne.get("numero", ""))
                n = max(n, int(m[1])) if m else n
    return f"LIC-{annee}-{n + 1:04d}"


def emettre(a):
    m = CODE.match(a.code.strip().upper())
    if not m:
        raise SystemExit("Code d'activation attendu comme T-ABCD-EFGH-IJKL-MNOP (affiché dans l'écran Licence du client).")
    if a.edition not in EDITIONS or a.role not in ROLES:
        raise SystemExit(f"Édition : {', '.join(EDITIONS)} ; rôle : {', '.join(ROLES)}.")
    if a.role == "agence" and not a.site:
        raise SystemExit("Une licence d'agence indique le code du site (--site DLA).")
    if a.postes < 1:
        raise SystemExit("Au moins 1 poste.")
    jusqu_au = None if a.definitive else date_ou_rien(a.jusqu_au) or (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
    maj = date_ou_rien(a.maj_jusqu_au) or jusqu_au or (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
    cle_chemin = Path(a.cle)
    registre = cle_chemin.with_name("registre-licences.csv")
    donnees = {"version": 1, "numero": prochain_numero(registre), "client": a.client.strip(), "niu": (a.niu or "").strip(),
               "edition": a.edition, "role": a.role, "site": (a.site or "").strip().upper(), "postes": a.postes,
               "machine": m[1], "emise_le": datetime.date.today().isoformat(), "valable_jusqu_au": jusqu_au,
               "maj_jusqu_au": maj}
    signature = charger_cle(cle_chemin).sign(canonique(donnees))
    texte = "\n".join([ENTETE, base64.b64encode(canonique(donnees)).decode(), base64.b64encode(signature).decode(), ""])
    sortie = Path(a.sortie or cle_chemin.parent) / f"{donnees['numero']}-{re.sub(r'[^A-Za-z0-9]+', '-', donnees['client'])[:40]}.erplic"
    sortie.write_text(texte, encoding="utf-8")
    nouveau = not registre.exists()
    with open(registre, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        if nouveau:
            w.writerow(["numero", "client", "niu", "edition", "role", "site", "postes", "machine", "emise_le",
                        "valable_jusqu_au", "maj_jusqu_au", "fichier"])
        w.writerow([donnees[k] or "" for k in ("numero", "client", "niu", "edition", "role", "site", "postes", "machine",
                                               "emise_le", "valable_jusqu_au", "maj_jusqu_au")] + [sortie.name])
    print(f"Licence {donnees['numero']} : {sortie}")
    print(f"  {donnees['client']} · {donnees['edition']} · {donnees['role']}{' ' + donnees['site'] if donnees['site'] else ''}"
          f" · {donnees['postes']} postes · {'définitive' if jusqu_au is None else 'jusqu au ' + jusqu_au}")
    return sortie


def verifier(fichier, publique):
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    lignes = [l.strip() for l in Path(fichier).read_text(encoding="utf-8").splitlines() if l.strip()]
    donnees = json.loads(base64.b64decode(lignes[1]))
    try:
        Ed25519PublicKey.from_public_bytes(base64.b64decode(Path(publique).read_text().strip())).verify(
            base64.b64decode(lignes[2]), canonique(donnees))
    except (InvalidSignature, ValueError):
        raise SystemExit("Signature INCORRECTE.")
    print("Signature correcte :", json.dumps(donnees, ensure_ascii=False, indent=1))


def question(texte, defaut=""):
    reponse = input(f"{texte}{f' [{defaut}]' if defaut else ''} : ").strip()
    return reponse or defaut


def menu():
    print("ERP OHADA — émission des licences\n  1. Créer la paire de clés (une seule fois)\n  2. Émettre une licence\n  3. Quitter")
    choix = question("Choix", "2")
    if choix == "1":
        creer_cles(question("Dossier des clés", str(Path.home() / "ERP-OHADA-Licences")))
    elif choix == "2":
        dossier = Path(question("Dossier des clés", str(Path.home() / "ERP-OHADA-Licences")))
        duree = question("Durée : A = abonnement annuel, D = définitive", "A").upper()
        a = argparse.Namespace(
            cle=str(dossier / "cle-privee.pem"), client=question("Client (raison sociale)"), niu=question("NIU", ""),
            edition=question("Édition (transport, commerce, toutes)", "transport"),
            role=question("Rôle (seul, siege, agence)", "seul"), site=question("Code du site (agence : DLA…)", ""),
            postes=int(question("Postes", "5")), code=question("Code d'activation du client"),
            definitive=duree == "D", jusqu_au=None if duree == "D" else question("Valable jusqu'au (AAAA-MM-JJ)", (
                datetime.date.today() + datetime.timedelta(days=365)).isoformat()),
            maj_jusqu_au=question("Mises à jour jusqu'au (AAAA-MM-JJ)", (datetime.date.today() + datetime.timedelta(days=365)).isoformat()),
            sortie=None)
        emettre(a)
    input("\nEntrée pour fermer…")


def main(argv):
    if not argv:
        menu()
        return 0
    p = argparse.ArgumentParser(prog="ERP-OHADA-Licences")
    s = p.add_subparsers(dest="commande", required=True)
    c = s.add_parser("cles")
    c.add_argument("--dossier", required=True)
    e = s.add_parser("emettre")
    for nom in ("--cle", "--client", "--edition", "--role", "--code"):
        e.add_argument(nom, required=True)
    e.add_argument("--postes", type=int, required=True)
    e.add_argument("--site")
    e.add_argument("--niu")
    e.add_argument("--jusqu-au", dest="jusqu_au")
    e.add_argument("--definitive", action="store_true")
    e.add_argument("--maj-jusqu-au", dest="maj_jusqu_au")
    e.add_argument("--sortie")
    v = s.add_parser("verifier")
    v.add_argument("fichier")
    v.add_argument("--publique", required=True)
    a = p.parse_args(argv)
    if a.commande == "cles":
        creer_cles(a.dossier)
    elif a.commande == "emettre":
        emettre(a)
    else:
        verifier(a.fichier, a.publique)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
