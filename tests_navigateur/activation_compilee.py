"""Recette de l'EXE : licence fictive signée, deux démarrages, refus et aucun import public.

preparer : crée une paire fictive dans RUNNER_TEMP, intègre SEULEMENT le public dans la copie CI.
verifier EXE EDITION : utilise le vrai serveur compilé, HTTP localhost, base jetable et privé hors artefacts.
"""
import base64
import datetime
import http.cookiejar
import json
import os
from pathlib import Path
import platform
import secrets
import subprocess
import sys
import time
import urllib.parse
import urllib.request

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))
DOSSIER = Path(os.environ["RUNNER_TEMP"]) / "activation-fictive"


def preparer():
    from deploy.executable.personnaliser_identite import personnaliser
    from apps.licences.identite import empreinte

    DOSSIER.mkdir(exist_ok=True)
    privee = Ed25519PrivateKey.generate()
    (DOSSIER / "privee-fictive.der").write_bytes(privee.private_bytes(serialization.Encoding.DER,
        serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    publique = privee.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    personnaliser(RACINE, b"ERPID\x01" + publique, empreinte(publique))
    print("Identité FICTIVE intégrée pour recette ; aucun exécutable de ce travail n'est distribué.")


class Navigateur:
    def __init__(self, port):
        self.base = f"http://127.0.0.1:{port}"
        self.cookies = http.cookiejar.CookieJar()
        self.client = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPCookieProcessor(self.cookies))

    def get(self, chemin):
        with self.client.open(self.base + chemin, timeout=10) as r:
            return r.read().decode("utf-8")

    def post(self, chemin, champs=None, fichier=None):
        csrf = next(c.value for c in self.cookies if c.name.endswith("csrftoken"))
        champs = {**(champs or {}), "csrfmiddlewaretoken": csrf}
        headers = {"Referer": self.base + chemin}
        if fichier is None:
            data = urllib.parse.urlencode(champs).encode()
        else:
            frontiere = "ERP" + secrets.token_hex(16)
            elements = []
            for nom, valeur in champs.items():
                elements.append(f'--{frontiere}\r\nContent-Disposition: form-data; name="{nom}"\r\n\r\n{valeur}\r\n'.encode())
            elements.append(f'--{frontiere}\r\nContent-Disposition: form-data; name="fichier"; filename="fictive.erplic"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode() + fichier + b"\r\n")
            elements.append(f"--{frontiere}--\r\n".encode())
            data = b"".join(elements)
            headers["Content-Type"] = f"multipart/form-data; boundary={frontiere}"
        with self.client.open(urllib.request.Request(self.base + chemin, data=data, headers=headers), timeout=20) as r:
            return r.read().decode("utf-8")

    def connecter(self):
        self.get("/connexion/")
        self.post("/connexion/", {"username": "activation-fictive", "password": "Fictif-CI-2026-Activation"})
        return self.get("/licence/")


def verifier(exe, edition):
    from apps.licences import format_cles as fc

    paquet = Path(exe).resolve().parent
    for f in paquet.rglob("*"):
        if f.is_file() and (f.name.lower() in ("coffre.dat", "cle-privee.pem", "cle_publique.txt", "cle-publique.txt") or f.suffix.lower() == ".erpinst"):
            raise AssertionError("Fichier d'émission ou autorisation à exclure du paquet client : " + str(f))

    privee = serialization.load_der_private_key((DOSSIER / "privee-fictive.der").read_bytes(), password=None)
    port = 18300 if edition == "commerce" else 18310
    data = DOSSIER / edition
    data.mkdir(exist_ok=True)
    env = {**os.environ, "ERP_DONNEES": str(data), "ERP_PORT": str(port), "ERP_RESEAU": "0",
           "ERP_SANS_NAVIGATEUR": "1", "ERP_ADMIN": "activation-fictive", "ERP_ADMIN_MDP": "Fictif-CI-2026-Activation",
           "ERP_ASSISTANT": "0", "MIROIR_DB_ENGINE": "", "RELAIS_ACTIF": "0", "ECHANGES_RELAIS_URL": "",
           "ECHANGES_DOSSIER_PARTAGE": "", "HTTP_PROXY": "http://127.0.0.1:9", "HTTPS_PROXY": "http://127.0.0.1:9"}
    resultats = []

    def signer(d):
        return fc.licence_texte(d, privee.sign(fc.canonique(d))).encode()

    def verifier_texte(texte, attendu):
        if attendu not in texte:
            raise AssertionError(f"Résultat attendu absent : {attendu}")

    for tour in (1, 2):
        with (data / f"serveur-{tour}.log").open("w", encoding="utf-8") as journal:
            serveur = subprocess.Popen([str(Path(exe).resolve())], env=env, stdout=journal, stderr=subprocess.STDOUT)
            try:
                navigateur = Navigateur(port)
                for _ in range(120):
                    if serveur.poll() is not None:
                        raise AssertionError("Le serveur compilé s'est arrêté : " + (data / f"serveur-{tour}.log").read_text()[-2000:])
                    try:
                        navigateur.get("/connexion/")
                        break
                    except (OSError, urllib.error.URLError):
                        time.sleep(1)
                else:
                    raise AssertionError("Le serveur compilé ne répond pas.")
                page = navigateur.connecter()
                if tour == 2:
                    verifier_texte(page, "LIC-2026-0001")
                    verifier_texte(page, "licence définitive")
                    resultats.append("licence conservée après arrêt et nouveau processus")
                    continue
                navigateur.post("/licence/", {"action": "installation", "cle": fc.installation_courte_creer()})
                demande = fc.demande_lire(navigateur.get("/licence/?demande=1"))
                conditions = {"numero": "LIC-2026-0001", "edition": edition, "role": demande["role"], "postes": 5,
                              "emise_le": datetime.date.today().isoformat(), "valable_jusqu_au": None, "maj_jusqu_au": None}
                d = fc.licence_donnees(demande, conditions)
                for changement, attendu in [({"edition": "transport" if edition == "commerce" else "commerce"}, "ne couvre pas"),
                        ({"machine": "AUTRE-SERVEUR"}, "autre serveur"), ({"installation": "AUTRE-INSTALLATION"}, "code d&#x27;installation"),
                        ({"valable_jusqu_au": "2020-01-01"}, "licence déjà expirée")]:
                    page = navigateur.post("/licence/", {"action": "fichier"}, signer({**d, **changement}))
                    verifier_texte(page, attendu)
                    resultats.append("refus " + next(iter(changement)))
                pirate = Ed25519PrivateKey.generate()
                fichier = fc.licence_texte(d, pirate.sign(fc.canonique(d))).encode()
                verifier_texte(navigateur.post("/licence/", {"action": "fichier"}, fichier), "signature incorrecte")
                resultats.append("refus autre signataire")
                verifier_texte(navigateur.post("/licence/", {"action": "fichier"}, signer(d)), "installée pour")
                verifier_texte(navigateur.get("/licence/"), "LIC-2026-0001")
                resultats.append("activation réelle .erplic seul, aucun fichier public sélectionné")
                cle_texte = fc.activation_creer(conditions, privee.sign(fc.canonique(d)))
                verifier_texte(navigateur.post("/licence/", {"action": "activation", "cle": cle_texte}), "activée pour")
                verifier_texte(navigateur.get("/licence/"), "LIC-2026-0001")
                resultats.append("activation réelle par clé texte signée, mêmes conditions et même serveur")
            finally:
                if os.name == "nt":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(serveur.pid)], capture_output=True, check=False)
                else:
                    serveur.terminate()
                serveur.wait(timeout=30)
    rapport = {"edition": edition, "os": platform.platform(), "executable": str(exe), "resultats": resultats,
               "limite": "Identité et base fictives. HTTP local sans service distant ; ne prouve pas un essai sur le PC du propriétaire ni sous Windows 10/11."}
    (DOSSIER / f"RESULTATS-{edition}.json").write_text(json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(rapport, ensure_ascii=False))


if __name__ == "__main__":
    if sys.argv[1] == "preparer":
        preparer()
    else:
        verifier(sys.argv[2], sys.argv[3])
