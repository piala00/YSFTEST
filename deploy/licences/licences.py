"""Outil du propriétaire : deux modules indépendants, identité et licences regroupées.

    ERP-OHADA-Licences.exe                         interface à deux onglets
    ERP-OHADA-Licences.exe installation --dossier D  code 4×6 sans société ni coffre
    ERP-OHADA-Licences.exe cles --dossier D          coffre.dat chiffré + parametres.dat binaire
    ERP-OHADA-Licences.exe emettre --cle D\\coffre.dat --demande DEMANDE.erpdem --postes 5
    ERP-OHADA-Licences.exe verifier fichier.erplic --publique D\\parametres.dat

Le format historique reste lisible ; « cles --ancien-format » est réservé à sa compatibilité.
Le code court est une référence d'installation, pas une signature d'autorisation. Le droit commercial reste
porté par la licence signée et l'autorité publique intégrée dans le client. La clé publique est non secrète ;
son format binaire ne remplace pas le chiffrement du coffre privé. Aucun mot de passe n'est mémorisé sur disque.
Le dossier complet reste au propriétaire. Exporter le paquet client exclut le coffre et les registres.
"""
import argparse
import base64
import csv
import datetime
import getpass
import hashlib
import json
import os
import re
import secrets  # import explicite pour PyInstaller : format_cles est compilé en module natif
import sys
from pathlib import Path

if not getattr(sys, "frozen", False):                            # depuis le dépôt : format commun avec le logiciel
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from apps.licences import format_cles as fc  # noqa: E402

ENTETE = fc.ENTETE_LICENCE
EDITIONS = fc.EDITIONS
ROLES = fc.ROLES
CODE = re.compile(r"^[TCM]-([A-Z2-7]{4}-[A-Z2-7]{4}-[A-Z2-7]{4}-[A-Z2-7]{4})$")
canonique = fc.canonique


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


def creer_cles(dossier, noms_neutres=True, mdp=None):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    dossier = Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    privee = dossier / ("coffre.dat" if noms_neutres else "cle-privee.pem")
    publique = dossier / ("parametres.dat" if noms_neutres else "cle-publique.txt")
    if any((dossier / nom).exists() for nom in ("coffre.dat", "cle-privee.pem", "parametres.dat", "cle-publique.txt")):
        raise SystemExit("Ce dossier contient déjà une identité : ouvrez son coffre, ne recréez pas les clés.")
    if privee.exists():
        raise SystemExit(f"{privee} existe déjà : jamais remplacée (les licences déjà émises en dépendent).")
    cle = Ed25519PrivateKey.generate()
    privee.write_bytes(cle.private_bytes(serialization.Encoding.DER if noms_neutres else serialization.Encoding.PEM,
                                         serialization.PrivateFormat.PKCS8,
                                         serialization.BestAvailableEncryption(mdp or mot_de_passe(confirmer=True))))
    brut = cle.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    if noms_neutres:
        publique.write_bytes(b"ERPID\x01" + brut)
    else:
        publique.write_text(base64.b64encode(brut).decode() + "\n", encoding="utf-8")
    print(f"Coffre éditeur : {privee}  (secret ; copie de secours hors ligne)")
    print(f"Identité publique : {publique}  (à fournir au logiciel, jamais le coffre)")
    if not noms_neutres:
        print("  " + publique.read_text().strip())
    ecrire_guide(dossier, brut)


def chemin_coffre(dossier):
    dossier = Path(dossier)
    for nom in ("coffre.dat", "cle-privee.pem"):
        if (dossier / nom).is_file():
            return dossier / nom
    return dossier / "coffre.dat"


def regrouper_identite(source, dossier, mdp):
    """Copie binaire chiffrée de l'identité existante, sans recréer la paire ni effacer l'original."""
    from cryptography.hazmat.primitives import serialization

    source, dossier = Path(source), Path(dossier)
    if source.is_symlink() or not source.is_file() or source.stat().st_size > 64*1024:
        raise SystemExit("Choisissez un coffre privé existant, non lié à un autre fichier.")
    cle = charger_cle(source, mdp)
    brut = cle.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    destination = dossier / 'coffre.dat'
    for nom in ('coffre.dat','cle-privee.pem'):
        candidat = dossier / nom
        if candidat.is_symlink():
            raise SystemExit("Un fichier lié ne peut pas servir de coffre.")
        if candidat.exists() and candidat.resolve() != source.resolve():
            existante = charger_cle(candidat, mdp)
            if existante.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw) != brut:
                raise SystemExit("Le dossier contient une autre identité : aucun fichier n'a été remplacé.")
    for nom in ('parametres.dat','cle-publique.txt','cle_publique.txt'):
        f=dossier/nom
        if f.is_symlink():
            raise SystemExit("Un fichier lié ne peut pas servir d'identité publique.")
        if f.exists():
            contenu=f.read_bytes()
            try:
                lu=contenu[6:] if contenu.startswith(b'ERPID\x01') and len(contenu)==38 else base64.b64decode(contenu.strip(),validate=True)
            except ValueError:
                raise SystemExit("Le dossier contient une identité publique illisible ; aucun remplacement automatique.")
            if lu != brut:
                raise SystemExit("Le dossier contient une autre identité publique : aucun fichier remplacé.")
    dossier.mkdir(parents=True,exist_ok=True)
    ecrire_identite(cle,dossier)
    if not destination.exists():
        contenu=cle.private_bytes(serialization.Encoding.DER,serialization.PrivateFormat.PKCS8,
                                  serialization.BestAvailableEncryption(mdp))
        with destination.open('xb') as f:
            f.write(contenu)
    # Conserver les numéros déjà émis lors du regroupement, pour ne pas recommencer à LIC-…-0001.
    supprimees_source = {e['numero']: e['date'] for e in journal_suppressions(source.parent)
                         if e['etat'] == 'supprimee'}
    for nom_registre in ('registre-licences.csv','registre-installations.csv'):
        registre_source = source.parent / nom_registre
        registre_destination = dossier / nom_registre
        if registre_source.is_file() and registre_source.resolve() != registre_destination.resolve():
            if registre_source.is_symlink() or registre_source.stat().st_size > 10*1024*1024:
                raise SystemExit("Registre historique lié ou trop volumineux : original conservé.")
            with registre_source.open(encoding='utf-8',newline='') as f:
                lignes = list(csv.DictReader(f,delimiter=';'))
            connus = set()
            if registre_destination.exists():
                with registre_destination.open(encoding='utf-8',newline='') as f:
                    connus = {(l.get('numero',''),l.get('client',''),l.get('machine','')) for l in csv.DictReader(f,delimiter=';')}
            for ligne in lignes:
                if nom_registre == 'registre-licences.csv' and ligne.get('numero') in supprimees_source:
                    ligne['supprimee_le'] = supprimees_source[ligne['numero']]
                identifiant = (ligne.get('numero',''),ligne.get('client',''),ligne.get('machine',''))
                if identifiant in connus:
                    continue
                if nom_registre == 'registre-licences.csv' and ligne.get('fichier') and not ligne.get('supprimee_le'):
                    ancien = Path(ligne['fichier'])
                    if ancien.is_file() and not ancien.is_symlink() and ancien.suffix.lower()=='.erplic':
                        try:
                            verifier(ancien,dossier/'parametres.dat')
                            nouveau = dossier / ancien.name
                            if not nouveau.exists():
                                with nouveau.open('xb') as f:
                                    f.write(ancien.read_bytes())
                            if nouveau.read_bytes()==ancien.read_bytes():
                                ligne['fichier'] = str(nouveau)
                                notice = ancien.with_name(ancien.stem+'-LIRE-MOI.txt')
                                copie = dossier / notice.name
                                if notice.is_file() and not notice.is_symlink() and not copie.exists():
                                    with copie.open('xb') as f:
                                        f.write(notice.read_bytes())
                        except (OSError,ValueError,SystemExit,IndexError,KeyError):
                            pass  # Le registre garde la référence historique ; aucun fichier inconnu n'est remplacé.
                ajouter_registre(registre_destination,ligne)
                connus.add(identifiant)
    ecrire_guide(dossier, brut)
    return destination


class CoffreSession:
    """Clé déverrouillée en mémoire ; aucun mot de passe dans les préférences."""
    def __init__(self):
        self.verrouiller()

    def verrouiller(self):
        self.cle = None
        self.identite = None

    def ouvrir(self, chemin, demander):
        import hashlib

        chemin = Path(chemin)
        identite = (str(chemin.resolve()), hashlib.sha256(chemin.read_bytes()).digest())
        if self.identite != identite:
            self.verrouiller()
            mdp = demander()
            if not mdp:
                return None
            cle = charger_cle(chemin, mdp.encode() if isinstance(mdp, str) else mdp)
            self.cle, self.identite = cle, identite
        return self.cle


def charger_cle(chemin, mdp=None):
    from cryptography.hazmat.primitives import serialization

    try:
        brut = Path(chemin).read_bytes()
        lire = serialization.load_pem_private_key if brut.startswith(b"-----BEGIN") else serialization.load_der_private_key
        cle = lire(brut, password=mdp or mot_de_passe())
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        if not isinstance(cle, Ed25519PrivateKey):
            raise ValueError("Clé Ed25519 attendue")
        return cle
    except (ValueError, TypeError):
        raise SystemExit("Mot de passe incorrect ou fichier de clé illisible.")


def creer_autorisation_installation(cle, code, reference, jusqu_au, dossier):
    """Permission de copier le programme, distincte d'une licence d'exploitation ; identité conservée."""
    from cryptography.hazmat.primitives import serialization
    code = code.strip().upper()
    if not CODE.fullmatch(code):
        raise ValueError("Code matériel attendu : T-, C- ou M- suivi des quatre groupes affichés par l'installateur.")
    fin = datetime.date.fromisoformat(jusqu_au)
    if fin < datetime.date.today():
        raise ValueError("L'autorisation ne peut pas être émise déjà expirée.")
    reference = fc.installation_courte_normaliser(reference) if reference else fc.installation_courte_creer()
    public = cle.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    d = {"version": 1, "reference": reference, "edition": {"T": "transport", "C": "commerce", "M": "toutes"}[code[0]],
         "machine": code[2:], "key_id": hashlib.sha256(public).hexdigest().upper(),
         "emise_le": datetime.date.today().isoformat(), "valable_jusqu_au": fin.isoformat()}
    contenu = fc.autorisation_texte(d, cle.sign(fc.DOMAINE_AUTORISATION + fc.canonique(d)))
    dossier = Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    fichier = dossier / ("AUTORISATION-" + hashlib.sha256(fc.canonique(d)).hexdigest()[:16].upper() + ".erpinst")
    with fichier.open("x", encoding="utf-8") as f:
        f.write(contenu)
    return fichier


def date_ou_rien(texte):
    if not texte:
        return None
    try:
        return datetime.date.fromisoformat(texte).isoformat()
    except ValueError:
        raise SystemExit(f"Date attendue au format AAAA-MM-JJ : {texte}")


def dans_mois(nombre):
    """Date d'aujourd'hui + N mois (fin de mois géré) → AAAA-MM-JJ."""
    import calendar

    d = datetime.date.today()
    mois = d.month - 1 + nombre
    annee = d.year + mois // 12
    mois = mois % 12 + 1
    jour = min(d.day, calendar.monthrange(annee, mois)[1])
    return datetime.date(annee, mois, jour).isoformat()


def prochain_numero(registre, prefixe="LIC"):
    annee = datetime.date.today().year
    n = 0
    if registre.exists():
        with open(registre, encoding="utf-8", newline="") as f:
            for ligne in csv.DictReader(f, delimiter=";"):
                m = re.match(rf"{prefixe}-{annee}-(\d+)$", ligne.get("numero", ""))
                n = max(n, int(m[1])) if m else n
    return f"{prefixe}-{annee}-{n + 1:04d}"


def ajouter_registre(registre, ligne):
    """Ajoute une ligne au registre CSV ; un registre plus ancien reçoit les colonnes nouvelles (rien n'est perdu)."""
    lignes, colonnes = [], list(ligne)
    if registre.exists():
        with open(registre, encoding="utf-8", newline="") as f:
            lecteur = csv.DictReader(f, delimiter=";")
            lignes = list(lecteur)
            colonnes = list(lecteur.fieldnames or []) + [c for c in ligne if c not in (lecteur.fieldnames or [])]
    with open(registre, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=colonnes, delimiter=";", restval="")
        w.writeheader()
        w.writerows(lignes + [{k: "" if v is None else v for k, v in ligne.items()}])


def nom_propre(texte, longueur=40):
    return re.sub(r"[^A-Za-z0-9]+", "-", texte).strip("-")[:longueur]


def generer_installation(dossier):
    """Module autonome : code 4×6 sans société, édition, coffre ni mot de passe.

    Il identifie une installation ; seule la licence signée prouve un droit commercial.
    """
    dossier = Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    registre = dossier / "registre-installations.csv"
    numero = prochain_numero(registre, "INS")
    code = fc.installation_courte_creer()
    fichier = dossier / f"INSTALLATION-{numero}.txt"
    with fichier.open("x", encoding="utf-8") as f:
        f.write(f"ERP OHADA — code d'installation {numero}\n\n{code}\n\n"
                "Ce code se génère indépendamment de la société. La licence signée reste nécessaire à l'usage commercial.\n")
    ajouter_registre(registre, {"numero": numero, "emise_le": datetime.date.today().isoformat(),
                                "cle": code, "fichier": str(fichier)})
    print(f"Code d'installation {numero} : {fichier}\n{code}")
    return numero, code, fichier


def exporter_client(licence, dossier, fichier=None):
    """Paquet partageable sur liste fermée ; le coffre et les registres ne sont jamais exportés."""
    import zipfile

    dossier, licence = Path(dossier).resolve(), Path(licence)
    if licence.is_symlink() or licence.suffix.lower() != ".erplic" or licence.resolve().parent != dossier:
        raise SystemExit("Choisissez une licence du dossier de travail courant.")
    publique = dossier / "parametres.dat"
    notice = licence.with_name(licence.stem + "-LIRE-MOI.txt")
    fichiers = [licence, publique] + ([notice] if notice.exists() else [])
    if any(f.is_symlink() or not f.is_file() or f.resolve().parent != dossier for f in fichiers):
        raise SystemExit("Le paquet client contient un fichier absent ou lié à un autre emplacement.")
    donnees = verifier(licence, publique)
    supprimees={e['numero'] for e in journal_suppressions(dossier) if e['etat']=='supprimee'}
    supprimees.update(l['numero'] for l in registre_lignes(dossier,inclure_supprimees=True) if l.get('supprimee_le'))
    if donnees.get('numero') in supprimees:
        raise SystemExit("Cette licence a été supprimée du registre actif ; aucun nouvel export.")
    sortie = Path(fichier) if fichier else dossier / (licence.stem + "-CLIENT.zip")
    if sortie.suffix.lower() != ".zip":
        sortie = sortie.with_name(sortie.name + ".zip")
    with zipfile.ZipFile(sortie, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for f in fichiers:
            z.write(f, f.name)
    return sortie


def emettre_installation(a, mdp=None, cle_deverrouillee=None):
    """Anciennes clés signées conservées ; les nouveaux codes courts sont autonomes."""
    if getattr(a, "courte", False) or not getattr(a, "cle", None):
        dossier = getattr(a, "sortie", None) or getattr(a, "dossier", None)
        if not dossier and getattr(a, "cle", None):
            dossier = Path(a.cle).parent
        if not dossier:
            raise SystemExit("Choisissez le dossier d'enregistrement du code d'installation.")
        return generer_installation(dossier)
    if a.edition not in EDITIONS:
        raise SystemExit(f"Édition : {', '.join(EDITIONS)}.")
    if not (a.client or "").strip():
        raise SystemExit("Nom de la société absent.")
    cle_chemin = Path(a.cle)
    registre = cle_chemin.with_name("registre-installations.csv")
    numero = prochain_numero(registre, "INS")
    cle = cle_deverrouillee or charger_cle(cle_chemin, mdp)
    texte = (fc.installation_courte_creer() if getattr(a, "courte", False)
             else fc.installation_creer(cle, numero, a.client.strip(), a.edition))
    sortie = Path(a.sortie or cle_chemin.parent) / f"CLE-INSTALLATION-{numero}-{nom_propre(a.client)}.txt"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    ecrire_identite(cle, sortie.parent)
    sortie.write_text(f"Clé d'installation {numero} — {a.client.strip()} — édition {a.edition}\r\n\r\n{texte}\r\n",
                      encoding="utf-8")
    ajouter_registre(registre, {"numero": numero, "client": a.client.strip(), "edition": a.edition,
                                "emise_le": datetime.date.today().isoformat(), "cle": texte, "fichier": str(sortie)})
    print(f"Clé d'installation {numero} : {sortie}\n{texte}")
    return numero, texte, sortie


def lire_demande(chemin, cle_privee=None):
    """Demande de licence du client ; sa clé d'installation est vérifiée avec la clé de l'éditeur si elle est fournie."""
    try:
        demande = fc.demande_lire(Path(chemin).read_bytes())
    except (OSError, fc.CleInvalide) as exc:
        raise SystemExit(f"Demande illisible : {exc}")
    if cle_privee is not None and demande.get("cle_installation") and not fc.est_installation_courte(demande["cle_installation"]):
        from cryptography.exceptions import InvalidSignature

        try:
            _, signe, signature = fc.installation_lire(demande["cle_installation"])
            cle_privee.public_key().verify(signature, signe)
        except (fc.CleInvalide, InvalidSignature):
            raise SystemExit("La clé d'installation de cette demande n'a pas été émise par vous : demande refusée.")
    return demande


def emettre(a, mdp=None, cle_deverrouillee=None):
    """Émet la licence : fichier .erplic, et la clé d'activation quand la licence part d'une demande.
    a.fichier : chemin exact du fichier ; sinon a.sortie (dossier) ou, à défaut, le dossier de la clé privée."""
    cle_chemin = Path(a.cle)
    cle_privee = cle_deverrouillee or charger_cle(cle_chemin, mdp)
    if getattr(a, "demande", None):
        demande = lire_demande(a.demande, cle_privee)
        edition = a.edition or demande.get("edition") or "transport"
        role = a.role or demande.get("role") or "seul"
    else:
        m = CODE.match((a.code or "").strip().upper())
        if not m:
            raise SystemExit("Donnez la demande de licence du client (--demande), ou son code d'activation "
                             "(T-ABCD-EFGH-IJKL-MNOP, écran Licence).")
        demande = {"societe": (a.client or "").strip(), "niu": (a.niu or "").strip(), "materiel": m[1],
                   "site": (a.site or "").strip().upper(), "machine_nom": "", "installation": ""}
        edition, role = a.edition, a.role
        if not demande["societe"]:
            raise SystemExit("Nom du client absent.")
    if edition not in EDITIONS or role not in ROLES:
        raise SystemExit(f"Édition : {', '.join(EDITIONS)} ; rôle : {', '.join(ROLES)}.")
    if role == "agence" and not demande.get("site"):
        raise SystemExit("Une licence d'agence indique le code du site (--site DLA).")
    if a.postes < 1 or a.postes > 65000:
        raise SystemExit("Nombre de postes : de 1 à 65000.")
    mois = (1 if getattr(a, "mensuelle", False) else 3 if getattr(a, "trimestrielle", False)
            else 6 if getattr(a, "semestrielle", False) else 12 if getattr(a, "annuelle", False)
            else getattr(a, "mois", None) or (getattr(a, "ans", None) or 0) * 12 or None)
    rapide = dans_mois(mois) if mois else None
    jusqu_au = None if a.definitive else rapide or date_ou_rien(a.jusqu_au) or dans_mois(12)
    maj = date_ou_rien(a.maj_jusqu_au) or jusqu_au or dans_mois(12)
    registre = cle_chemin.with_name("registre-licences.csv")
    conditions = {"numero": prochain_numero(registre), "edition": edition, "role": role, "postes": a.postes,
                  "emise_le": datetime.date.today().isoformat(), "valable_jusqu_au": jusqu_au, "maj_jusqu_au": maj}
    donnees = fc.licence_donnees(demande, conditions)
    signature = cle_privee.sign(canonique(donnees))
    if getattr(a, "fichier", None):
        sortie = Path(a.fichier)
        if sortie.suffix.lower() != ".erplic":
            sortie = sortie.with_name(sortie.name + ".erplic")
    else:
        sortie = Path(a.sortie or cle_chemin.parent) / nom_fichier(donnees["numero"], donnees["client"])
    sortie.parent.mkdir(parents=True, exist_ok=True)
    ecrire_identite(cle_privee, sortie.parent)
    sortie.write_text(fc.licence_texte(donnees, signature), encoding="utf-8")
    activation = fc.activation_creer(conditions, signature) if getattr(a, "demande", None) else ""
    if activation:
        sortie.with_name(sortie.stem + "-CLE-ACTIVATION.txt").write_text(
            f"Clé d'activation de la licence {donnees['numero']} — {donnees['client']}\r\n"
            f"Serveur : {donnees['machine_nom']} ({donnees['machine']})\r\n\r\n{activation}\r\n", encoding="utf-8")
    ajouter_registre(registre, {**{k: donnees[k] for k in ("numero", "client", "niu", "edition", "role", "site", "postes",
                                                         "machine", "emise_le", "valable_jusqu_au", "maj_jusqu_au")},
                                "fichier": str(sortie), "machine_nom": donnees["machine_nom"],
                                "installation": donnees["installation"], "cle_activation": activation})
    print(f"Licence {donnees['numero']} : {sortie}")
    print(f"  {donnees['client']} · {edition} · {role}{' ' + donnees['site'] if donnees['site'] else ''}"
          f" · {a.postes} postes · {'définitive' if jusqu_au is None else 'jusqu au ' + jusqu_au}")
    if activation:
        print(f"Clé d'activation :\n{activation}")
    notice = sortie.with_name(sortie.stem + "-LIRE-MOI.txt")
    notice.write_text(
        f"ERP OHADA — dossier client\nSociété : {donnees['client']}\nServeur : {donnees['machine_nom']}\n"
        f"Licence : {donnees['numero']} — {edition} — {a.postes} postes\n"
        f"Code d'installation : {demande.get('cle_installation') or 'non fourni (ancien parcours)'}\n\n"
        f"ACTIVER : dans l'ERP, ouvrir Licence puis Installer le fichier et choisir {sortie.name}.\n"
        "Ce fichier suffit. Il n'est pas nécessaire de saisir aussi une clé d'activation.\n"
        "Identité publique : parametres.dat, à sélectionner dans Administration > Licence si demandé.\n"
        "Elle doit correspondre à l'éditeur autorisé dans ce logiciel. Une identité commerciale doit être\n"
        "intégrée au programme par l'éditeur ; copier un autre fichier public ne remplace pas cette identité.\n"
        "Ne jamais copier le coffre de l'éditeur dans l'installation client.\n\n"
        + (f"Activation alternative (facultative) :\n{activation}\n" if activation else ""), encoding="utf-8")
    a.activation = activation
    return sortie


def ecrire_identite(cle, dossier):
    from cryptography.hazmat.primitives import serialization

    Path(dossier).mkdir(parents=True, exist_ok=True)
    chemin = Path(dossier) / "parametres.dat"
    brut = b"ERPID\x01" + cle.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    if chemin.is_symlink():
        raise SystemExit("Le fichier public ne doit pas être un lien vers un autre fichier.")
    if chemin.exists() and chemin.read_bytes() != brut:
        raise SystemExit("Ce dossier contient l'identité d'un autre éditeur : choisissez un autre dossier.")
    chemin.write_bytes(brut)
    ecrire_guide(dossier, brut[6:])
    return chemin


def nom_fichier(numero, client):
    return f"{numero}-{nom_propre(client)}.erplic"


def registre_lignes(dossier, inclure_supprimees=False):
    registre = Path(dossier) / "registre-licences.csv"
    if not registre.exists():
        return []
    if registre.is_symlink() or registre.stat().st_size > 10*1024*1024:
        raise ValueError("Registre lié ou trop volumineux : opération refusée.")
    with open(registre, encoding="utf-8", newline="") as f:
        lignes = list(csv.DictReader(f, delimiter=";"))
    supprimees = {e['numero'] for e in journal_suppressions(dossier) if e['etat']=='supprimee'}
    return lignes if inclure_supprimees else [l for l in lignes if not l.get('supprimee_le') and l.get('numero') not in supprimees]


def clients_connus(dossier):
    """Sociétés déjà servies (la plus récente licence de chacune) : pour les choisir dans la liste."""
    clients = {}
    for ligne in registre_lignes(dossier):
        clients[ligne["client"]] = ligne
    return dict(sorted(clients.items(), key=lambda c: c[0].lower()))


def verifier(fichier, publique):
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

    try:
        if Path(fichier).stat().st_size > 64*1024:
            raise ValueError
        lignes = [l.strip() for l in Path(fichier).read_text(encoding="utf-8-sig").splitlines() if l.strip()]
        if len(lignes)!=3 or lignes[0]!=ENTETE:
            raise ValueError
        donnees = json.loads(base64.b64decode(lignes[1],validate=True))
        if not isinstance(donnees,dict):
            raise ValueError
        brut = Path(publique).read_bytes()
        brut = brut[6:] if len(brut) == 38 and brut.startswith(b"ERPID\x01") else base64.b64decode(brut.strip())
        Ed25519PublicKey.from_public_bytes(brut).verify(
            base64.b64decode(lignes[2]), canonique(donnees))
    except (InvalidSignature, ValueError, IndexError, UnicodeDecodeError):
        raise SystemExit("Signature INCORRECTE.")
    print("Signature correcte :", json.dumps(donnees, ensure_ascii=False, indent=1))
    return donnees


def journal_suppressions(dossier):
    """Journal propriétaire, jamais exporté ; une entrée finalisée masque la licence dans la liste active."""
    chemin = Path(dossier)/'journal-suppressions.json'
    if chemin.is_symlink():
        raise ValueError('Le journal des suppressions ne doit pas être un lien.')
    if not chemin.exists():
        return []
    if chemin.stat().st_size > 10*1024*1024:
        raise ValueError('Journal des suppressions trop volumineux.')
    d=json.loads(chemin.read_text(encoding='utf-8'))
    if not isinstance(d,dict) or d.get('version')!=1 or not isinstance(d.get('evenements'),list):
        raise ValueError('Journal des suppressions illisible : conservez-le pour diagnostic.')
    evenements=d['evenements']
    if any(not isinstance(e,dict) or not all(isinstance(e.get(k),str) for k in
            ('numero','date','etat','fichier','sha256','archive')) or e['etat'] not in
            ('en_cours','supprimee','annulee') for e in evenements):
        raise ValueError('Journal des suppressions incohérent : aucune suppression autorisée.')
    return evenements


def enregistrer_suppressions(dossier, evenements):
    """Remplacement atomique du seul journal, après écriture et synchronisation sur disque."""
    import tempfile

    chemin=Path(dossier)/'journal-suppressions.json'
    if chemin.is_symlink():
        raise ValueError('Journal lié : écriture refusée.')
    temporaire=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=dossier,delete=False,
                                         prefix='.suppressions-',suffix='.tmp') as f:
            temporaire=Path(f.name)
            json.dump({'version':1,'evenements':evenements},f,ensure_ascii=False,indent=2)
            f.flush();os.fsync(f.fileno())
        os.replace(temporaire,chemin)
    finally:
        if temporaire and temporaire.exists():
            temporaire.unlink()


def preparer_suppression(dossier, numero):
    """Photographie vérifiée de la seule licence sélectionnée, avant la confirmation de l'utilisateur."""
    dossier=Path(dossier).resolve()
    lignes=[l for l in registre_lignes(dossier) if l.get('numero')==numero]
    if len(lignes)!=1:
        raise ValueError('Sélectionnez une seule licence active, sans doublon de numéro.')
    ligne=lignes[0]
    fichier=Path(ligne.get('fichier',''))
    if fichier.is_symlink() or fichier.suffix.lower()!='.erplic' or fichier.resolve().parent!=dossier or not fichier.is_file():
        raise ValueError('La licence sélectionnée doit être un fichier du dossier propriétaire courant.')
    if fichier.stat().st_nlink!=1:
        raise ValueError('La licence ne doit pas être liée à un autre fichier.')
    publique=dossier/'parametres.dat'
    if publique.is_symlink():
        raise ValueError('Fichier public lié : suppression refusée.')
    donnees=verifier(fichier,publique)
    if any(str(donnees.get(k,''))!=str(ligne.get(k,'')) for k in ('numero','client','machine')):
        raise ValueError('Le fichier ne correspond pas à la licence sélectionnée dans le registre.')
    return {'numero':numero,'client':donnees['client'],'edition':donnees.get('edition',''),
            'postes':donnees.get('postes',''),'machine':donnees.get('machine',''),
            'fichier':str(fichier.resolve()),'sha256':hashlib.sha256(fichier.read_bytes()).hexdigest(),
            'registre_sha256':hashlib.sha256((dossier/'registre-licences.csv').read_bytes()).hexdigest(),
            'publique_sha256':hashlib.sha256(publique.read_bytes()).hexdigest()}


def supprimer_licence(dossier, selection, confirme=False):
    """Retrait ciblé et réversible, avec intention durable et journal final. Ne révoque pas les clients.

    Le CSV garde le numéro pour qu'il ne soit jamais réattribué ; le fichier seul est déplacé en corbeille.
    Les clés, notices, demandes, ZIP déjà exportés et autres licences ne sont ni déplacés ni supprimés.
    """
    if confirme is not True:
        raise ValueError('Confirmation explicite nécessaire ; aucune licence supprimée.')
    dossier=Path(dossier).resolve()
    verrou=dossier/'.suppression-licences.lock'
    with verrou.open('x',encoding='utf-8') as f:
        f.write(str(os.getpid()))
    try:
        actuelle=preparer_suppression(dossier,selection.get('numero'))
        if actuelle!=selection:
            raise ValueError('La sélection a changé : relisez les informations et confirmez de nouveau.')
        evenements=journal_suppressions(dossier)
        if any(e['etat']=='en_cours' for e in evenements):
            raise ValueError('Une suppression est incomplète : contrôler le journal et la corbeille avant de poursuivre.')
        corbeille=dossier/'corbeille-licences'
        if corbeille.is_symlink():
            raise ValueError('Corbeille liée : suppression refusée.')
        corbeille.mkdir(exist_ok=True)
        destination=corbeille/secrets.token_hex(16)
        archive=destination/Path(actuelle['fichier']).name
        evenement={k:actuelle[k] for k in ('numero','client','fichier','sha256')}
        evenement.update(date=datetime.datetime.now(datetime.timezone.utc).isoformat(),etat='en_cours',
                         archive=str(archive.relative_to(dossier)),acteur=getpass.getuser())
        evenements.append(evenement)
        enregistrer_suppressions(dossier,evenements)  # Aucun déplacement si le journal ne peut pas être écrit.
        deplace=False
        try:
            destination.mkdir(mode=0o700)
            Path(actuelle['fichier']).rename(archive)
            deplace=True
            evenement['etat']='supprimee'
            enregistrer_suppressions(dossier,evenements)
        except (OSError,ValueError):
            if deplace:
                if Path(actuelle['fichier']).exists():
                    raise OSError('Suppression interrompue : fichier conservé en corbeille, contrôler le journal.')
                archive.rename(actuelle['fichier'])
            evenement['etat']='annulee'
            enregistrer_suppressions(dossier,evenements)
            raise
        return archive
    finally:
        verrou.unlink()


def ecrire_guide(dossier, publique=None):
    """Guide placé à côté du coffre, sans secret et sans prétendre importer une nouvelle autorité."""
    dossier=Path(dossier)
    dossier.mkdir(parents=True,exist_ok=True)
    guide=dossier/'INSTALLATION_CLE_PUBLIQUE.md'
    if guide.is_symlink():
        raise ValueError('Le guide ne doit pas être un lien vers un autre fichier.')
    if guide.exists() and (not guide.is_file() or guide.stat().st_nlink!=1):
        raise ValueError('Le guide doit être un fichier ordinaire non partagé ; aucun remplacement.')
    if publique is None and (dossier/'parametres.dat').is_file():
        contenu=(dossier/'parametres.dat').read_bytes()
        if len(contenu)==38 and contenu.startswith(b'ERPID\x01'):
            publique=contenu[6:]
    empreinte=hashlib.sha256(publique).hexdigest().upper() if publique else 'à relever après création ou regroupement de votre identité'
    texte=f'''# Installer la licence et reconnaître la clé publique — ERP OHADA

## Fichiers et emplacement exact

Le dossier propriétaire choisi dans le générateur contient coffre.dat (privé, chiffré), parametres.dat
(public, binaire) et les licences .erplic. Il reste sur le poste du propriétaire. Aucun coffre privé
ne doit être envoyé, copié ou installé chez un client. Utiliser « Exporter le paquet client ».

Empreinte SHA-256 de la clé publique brute de ce dossier : {empreinte}

Sur le client compilé, aucun chemin de copie manuelle de parametres.dat n'est nécessaire ni accepté
comme nouvelle autorité. L'autorité de l'éditeur est intégrée au programme compilé livré.
Un fichier public différent ne peut pas la remplacer. Si elle manque, demander à l'éditeur une version
personnalisée avec cette identité PUBLIQUE uniquement. Ne jamais lui transmettre le coffre privé.

Emplacements par défaut de l'installateur (ils peuvent être changés à l'installation) :
- Programme Transport : C:\\Program Files\\ERP-OHADA\\Transport ; Commerce : C:\\Program Files\\ERP-OHADA\\Commerce.
- Données serveur Transport : C:\\ProgramData\\ERP-OHADA\\Transport ; Commerce : C:\\ProgramData\\ERP-OHADA\\Commerce.
Ces dossiers ne sont pas des destinations où coller les clés. Les fichiers licence et public peuvent
être choisis dans tout dossier lisible par le navigateur de l'administrateur (par exemple Téléchargements).
La licence validée est déposée dans l'historique de la base active ; la clé privée n'est jamais requise.

## Installation automatique depuis les deux fichiers

1. Ouvrir l'ERP concerné et se connecter comme administrateur.
2. Aller dans Fichier > Administration du poste > Licence.
3. Choisir le fichier .erplic destiné à cette société, édition et machine.
4. Aucun fichier public à choisir : l’identité de l’éditeur doit déjà être intégrée au programme.
5. Cliquer « Installer la licence ». Le serveur vérifie l’autorité intégrée, la signature et la destination
   de la licence, puis enregistre la licence. Aucune copie dans les dossiers Windows ni deuxième code n'est nécessaire.
6. Vérifier le message de réussite, le numéro, la société, l'édition, les postes et l'échéance dans l'état affiché.
   Comparer l'empreinte de l'éditeur affichée par l'ERP à celle de ce guide, obtenue auprès du propriétaire.
7. Recharger la page : la licence doit rester dans l'historique et l'état doit être cohérent avec ses dates.

## Windows 10, Windows 11 et Windows Server

Même procédure d'import dans le navigateur. L'installateur peut demander l'élévation administrateur pour
Program Files, le service et le pare-feu. Aucun droit d'écriture dans Program Files n'est nécessaire pour
importer une licence. Sous Windows Server, utiliser une session graphique/navigateur ; le générateur Tk
n'est pas prévu pour Server Core sans interface. Depuis un poste distant, les fichiers sont sélectionnés
sur ce poste et envoyés au serveur ERP. L'identité machine de la licence est celle du serveur, pas du navigateur.
Nommer les OS réellement essayés dans la livraison ; un essai windows-latest ne prouve pas les trois versions.

## Refus et solutions

- « Identité de votre éditeur doit être intégrée » / version d'essai : obtenir la version personnalisée
  auprès de l'éditeur ; coller un fichier ou recréer une paire ne résout pas l'absence d'autorité approuvée.
- « Ce fichier public n'appartient pas à l'éditeur » : choisir le public correspondant à l'autorité du programme.
- « Choisissez uniquement le fichier public » : coffre.dat ou fichier illisible sélectionné ; choisir parametres.dat.
- « Signature incorrecte » : fichier modifié ou autre éditeur ; reprendre la licence originale auprès de l'éditeur.
- Refus de machine, édition ou société : produire une demande .erpdem depuis le serveur et la société concernés,
  puis demander la licence correspondante. Ne pas modifier les champs du fichier signé.
- Fichier absent/trop volumineux : choisir le .erplic (64 Ko maximum), pas le ZIP complet ; public : 8 Ko maximum.
- Droits insuffisants : se connecter comme administrateur. Vérifier aussi l'horloge et l'échéance affichées.

## Conservation et suppression dans l'outil propriétaire

Sauvegarder le dossier propriétaire dans un emplacement protégé, avec son coffre chiffré et son mot de passe.
« Supprimer la licence » affiche les informations et exige une confirmation. Seul le .erplic sélectionné
est déplacé vers corbeille-licences ; le numéro reste réservé et le journal est journal-suppressions.json.
Les clés, autres licences, notices et ZIP déjà exportés sont conservés. Ce retrait local ne révoque pas
une licence déjà remise/installée. Après interruption, vérifier le journal et la corbeille avant de retirer
un ancien verrou .suppression-licences.lock ; conserver les fichiers pour diagnostic.
'''
    guide.write_text(texte,encoding='utf-8')
    return guide


def bureau():
    """Bureau de Windows (OneDrive compris), sinon le dossier personnel."""
    profil = Path(os.environ.get("USERPROFILE") or Path.home())
    for d in (profil / "OneDrive" / "Desktop", profil / "OneDrive" / "Bureau", profil / "Desktop", profil / "Bureau"):
        if d.is_dir():
            return d
    return profil


PREFERENCES = Path.home() / ".erp-ohada-licences.json"


def preferences():
    try:
        return json.loads(PREFERENCES.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def retenir(**valeurs):
    try:
        PREFERENCES.write_text(json.dumps({**preferences(), **valeurs}, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def ouvrir_dossier(dossier):
    Path(dossier).mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        os.startfile(dossier)                                     # l'Explorateur sur le dossier choisi


def interface(essai=False):
    """Deux modules : installation autonome ; licence et identité réunies dans le dossier propriétaire."""
    import tempfile
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog, ttk

    temporaire = tempfile.TemporaryDirectory(prefix="erp-licences-interface-") if essai else None
    prefs = {} if essai else preferences()
    fen = tk.Tk()
    fen.title("ERP OHADA — Installation et licences 3.1 (propriétaire)")
    fen.geometry("760x640")
    fen.minsize(600, 440)
    session = CoffreSession()
    v = {nom: tk.StringVar(value=val) for nom, val in {
        "dossier": temporaire.name if essai else prefs.get("dossier_unique", prefs.get("cles", str(Path.home()/"ERP-OHADA-Licences"))),
        "client": "", "niu": "", "edition": "transport", "role": "seul", "site": "", "postes": "5",
        "code": "", "demande": "", "duree": "abonnement", "jusqu_au": dans_mois(12), "maj": dans_mois(12)}.items()}
    resultat_installation = tk.StringVar()
    etat = tk.StringVar()
    derniere_licence = [None]
    dernier_code = [None]

    def erreur(exc):
        if essai:
            raise RuntimeError(str(exc)) from exc
        messagebox.showerror("Installation et licences", str(exc), parent=fen)

    def memoriser():
        if not essai:
            retenir(dossier_unique=v['dossier'].get(), cles=v['dossier'].get(), licences=v['dossier'].get())

    def fermer():
        session.verrouiller()
        fen.destroy()

    fen.protocol("WM_DELETE_WINDOW", fermer)
    cadre = ttk.Frame(fen, padding=8)
    cadre.pack(fill='both', expand=True)
    ttk.Label(cadre, text="Dossier propriétaire — clés et licences réunies").pack(anchor='w')
    ligne_dossier = ttk.Frame(cadre)
    ligne_dossier.pack(fill='x', pady=(3,8))
    ttk.Entry(ligne_dossier, textvariable=v['dossier']).pack(side='left', fill='x', expand=True)

    def choisir_dossier():
        d = filedialog.askdirectory(initialdir=v['dossier'].get(), title="Dossier du propriétaire")
        if d:
            v['dossier'].set(d)
            memoriser()

    ttk.Button(ligne_dossier, text='Parcourir…', command=choisir_dossier).pack(side='left', padx=4)
    ttk.Button(ligne_dossier, text='Ouvrir le dossier', command=lambda: ouvrir_dossier(v['dossier'].get())).pack(side='left')
    onglets = ttk.Notebook(cadre)
    onglets.pack(fill='both', expand=True)
    installation_tab, licence_onglet = ttk.Frame(onglets, padding=8), ttk.Frame(onglets)
    onglets.add(installation_tab, text='1 · Installation')
    onglets.add(licence_onglet, text='2 · Licence')
    licence_onglet.columnconfigure(0,weight=1)
    licence_onglet.rowconfigure(0,weight=1)
    defilement=tk.Canvas(licence_onglet,highlightthickness=0)
    defilement.grid(row=0,column=0,sticky='nsew')
    barre=ttk.Scrollbar(licence_onglet,orient='vertical',command=defilement.yview)
    barre.grid(row=0,column=1,sticky='ns')
    defilement.configure(yscrollcommand=barre.set)
    licence_tab=ttk.Frame(defilement,padding=8)
    contenu=defilement.create_window((0,0),window=licence_tab,anchor='nw')
    licence_tab.bind('<Configure>',lambda _e:defilement.configure(scrollregion=defilement.bbox('all')))
    defilement.bind('<Configure>',lambda e:defilement.itemconfigure(contenu,width=e.width))

    ttk.Label(installation_tab, text="Générer un code d’installation", font=('Segoe UI',14,'bold')).pack(anchor='w')
    ttk.Label(installation_tab, text="Aucune société à saisir. Aucun coffre à ouvrir, aucun mot de passe demandé.",
              wraplength=520).pack(anchor='w', pady=8)
    ttk.Label(installation_tab, text="Le code est enregistré dans le dossier choisi. La licence signée reste l’autorisation commerciale du logiciel.",
              wraplength=520).pack(anchor='w', pady=4)
    ttk.Entry(installation_tab, textvariable=resultat_installation, state='readonly', font=('Consolas',14)).pack(fill='x', pady=12)

    def installation():
        try:
            numero, code, fichier = generer_installation(v['dossier'].get())
            dernier_code[0] = code
            resultat_installation.set(code)
            statut_installation.configure(text=f"{numero} · enregistré : {fichier.name}")
            memoriser()
        except (OSError, ValueError, SystemExit) as exc:
            erreur(exc)

    def copier_code():
        if resultat_installation.get():
            fen.clipboard_clear()
            fen.clipboard_append(resultat_installation.get())

    boutons_installation = ttk.Frame(installation_tab)
    boutons_installation.pack(anchor='w')
    generer_code_btn = ttk.Button(boutons_installation, text='Générer une clé d’installation', command=installation)
    generer_code_btn.pack(side='left', padx=(0,5))
    ttk.Button(boutons_installation, text='Copier le code', command=copier_code).pack(side='left')
    statut_installation = ttk.Label(installation_tab, text='', wraplength=520)
    statut_installation.pack(anchor='w', pady=12)

    licence_tab.columnconfigure(1, weight=1)
    def ligne(rang, texte, widget):
        ttk.Label(licence_tab, text=texte).grid(row=rang, column=0, sticky='w', padx=(0,8), pady=3)
        widget.grid(row=rang, column=1, sticky='ew', pady=3)
        return widget

    def verrouiller():
        session.verrouiller()
        etat.set('Coffre verrouillé. Le code d’installation reste disponible sans mot de passe.')

    def demander_mdp(texte):
        return (os.environ.get('ERP_LICENCES_MDP') or 'Essai-Interface-Fictif-2026') if essai else simpledialog.askstring(
            'Coffre du propriétaire', texte, show='*', parent=fen)

    def ouvrir_coffre():
        try:
            cle = session.ouvrir(chemin_coffre(v['dossier'].get()), lambda: demander_mdp('Mot de passe — une fois pour cette session :'))
            if cle:
                ecrire_identite(cle, v['dossier'].get())
                etat.set('Coffre ouvert pour cette session. Clé publique binaire : parametres.dat.')
            return cle
        except (OSError, ValueError, SystemExit) as exc:
            erreur(exc)

    def autoriser_installation():
        code = simpledialog.askstring('Autorisation d’installation', 'Code matériel affiché par l’installateur (T-… ou C-…) :', parent=fen)
        if not code:
            return
        fin = simpledialog.askstring('Durée de l’autorisation', 'Autorisation d’installation valable jusqu’au (AAAA-MM-JJ) :',
                                     initialvalue=(datetime.date.today()+datetime.timedelta(days=30)).isoformat(), parent=fen)
        if not fin:
            return
        try:
            cle = ouvrir_coffre()
            if cle is None:
                return
            fichier = creer_autorisation_installation(cle, code, resultat_installation.get(), fin, v['dossier'].get())
            statut_installation.configure(text=f'Autorisation signée créée : {fichier.name}. Ce fichier ne remplace pas la licence d’exploitation.')
        except (OSError, ValueError, SystemExit) as exc:
            erreur(exc)

    ttk.Button(installation_tab, text='Autoriser une installation (.erpinst)…', command=autoriser_installation).pack(anchor='w', pady=8)
    ttk.Label(installation_tab, text='Le code court reste autonome. Signer une autorisation exige le coffre existant et le code matériel du serveur ; aucune société à saisir.',
              wraplength=520).pack(anchor='w')

    def creer():
        dossier = Path(v['dossier'].get())
        if chemin_coffre(dossier).exists():
            ouvrir_coffre()
            return
        mdp = demander_mdp('Choisissez le mot de passe du coffre (10 caractères minimum) :')
        if not mdp:
            return
        if len(mdp)<10 or (not essai and mdp != demander_mdp('Confirmez le mot de passe :')):
            erreur(ValueError('Mot de passe trop court ou confirmation différente.'))
            return
        try:
            creer_cles(dossier, mdp=mdp.encode())
            session.ouvrir(chemin_coffre(dossier), lambda: mdp)
            etat.set('Identité créée : coffre.dat chiffré et parametres.dat binaire, dans ce dossier.')
            memoriser()
        except (OSError, ValueError, SystemExit) as exc:
            erreur(exc)

    def rassembler():
        source = filedialog.askopenfilename(title='Votre clé privée existante — elle restera sur votre poste',
            filetypes=[('Coffre existant','*.dat *.pem'),('Tous fichiers','*.*')])
        if not source:
            return
        mdp = demander_mdp('Mot de passe du coffre existant :')
        if not mdp:
            return
        try:
            chemin = regrouper_identite(source, v['dossier'].get(), mdp.encode())
            session.ouvrir(chemin, lambda: mdp)
            etat.set('Identité rassemblée au format binaire. L’original est conservé à son emplacement.')
            memoriser()
        except (OSError, ValueError, SystemExit) as exc:
            erreur(exc)

    identite = ttk.Frame(licence_tab)
    creer_btn = ttk.Button(identite, text='Créer l’identité', command=creer)
    creer_btn.pack(side='left')
    ttk.Button(identite, text='Regrouper…', command=rassembler).pack(side='left', padx=4)
    ttk.Button(identite, text='Verrouiller', command=verrouiller).pack(side='left')
    def guide():
        try:
            fichier=ecrire_guide(v['dossier'].get())
            etat.set(f'Guide disponible : {fichier.name}')
            if os.name=='nt' and not essai:
                os.startfile(fichier)
        except (OSError,ValueError) as exc:
            erreur(exc)
    ttk.Button(identite,text='Guide',command=guide).pack(side='left',padx=4)
    ligne(0, 'Identité de l’éditeur', identite)
    ttk.Label(licence_tab,textvariable=etat,wraplength=520).grid(row=1,column=0,columnspan=2,sticky='w',pady=4)
    choix_client=ligne(2,'Société à licencier',ttk.Combobox(licence_tab,textvariable=v['client']))
    ligne(3,'Édition',ttk.Combobox(licence_tab,textvariable=v['edition'],values=EDITIONS,state='readonly'))
    ligne(4,'Nombre de postes',ttk.Spinbox(licence_tab,from_=1,to=65000,textvariable=v['postes']))

    def charger_demande(chemin):
        d=lire_demande(chemin)
        v['demande'].set(str(chemin))
        for champ, cle in [('client','societe'),('niu','niu'),('edition','edition'),('role','role'),('site','site')]:
            if d.get(cle) is not None:
                v[champ].set(d[cle])
        serveur.configure(text=f"Serveur : {d.get('machine_nom','')} · {d['materiel']}")

    def choisir_demande():
        chemin=filedialog.askopenfilename(title='Demande de licence du client',filetypes=[('Demande de licence','*.erpdem')])
        if chemin:
            try:
                charger_demande(chemin)
            except (OSError, ValueError, SystemExit) as exc:
                erreur(exc)

    demande=ttk.Frame(licence_tab)
    ttk.Entry(demande,textvariable=v['demande']).pack(side='left',fill='x',expand=True)
    ttk.Button(demande,text='Parcourir…',command=choisir_demande).pack(side='left',padx=4)
    ligne(5,'Demande du logiciel client',demande)
    serveur=ttk.Label(licence_tab,text='',wraplength=520)
    serveur.grid(row=6,column=0,columnspan=2,sticky='w')
    duree=ttk.Frame(licence_tab)
    ttk.Radiobutton(duree,text='Jusqu’au',variable=v['duree'],value='abonnement').pack(side='left')
    ttk.Entry(duree,textvariable=v['jusqu_au'],width=12).pack(side='left',padx=4)
    def echeance(n):
        v['duree'].set('abonnement');v['jusqu_au'].set(dans_mois(n));v['maj'].set(dans_mois(n))
    choix_duree=tk.StringVar(value='1 an')
    durees={'1 mois':1,'3 mois':3,'1 an':12,'3 ans':36}
    raccourci=ttk.Combobox(duree,textvariable=choix_duree,values=list(durees),state='readonly',width=8)
    raccourci.pack(side='left',padx=4)
    raccourci.bind('<<ComboboxSelected>>',lambda _e:echeance(durees[choix_duree.get()]))
    ttk.Radiobutton(duree,text='Permanente',variable=v['duree'],value='definitive').pack(side='left')
    ligne(7,'Durée de licence',duree)
    avancees=ttk.Frame(licence_tab)
    avancees.columnconfigure(1,weight=1)
    for i,(champ,texte) in enumerate([('niu','NIU'),('role','Rôle (seul / siège / agence)'),('site','Site agence'),
        ('maj','Mises à jour jusqu’au'),('code','Ancien identifiant serveur')]):
        ttk.Label(avancees,text=texte).grid(row=i,column=0,sticky='w',padx=(0,8),pady=2)
        widget = ttk.Combobox(avancees,textvariable=v[champ],values=ROLES,state='readonly') if champ=='role' else ttk.Entry(avancees,textvariable=v[champ])
        widget.grid(row=i,column=1,sticky='ew')
    affiche_avancees=tk.BooleanVar(value=False)
    def options_avancees():
        avancees.grid(row=9,column=0,columnspan=2,sticky='ew') if affiche_avancees.get() else avancees.grid_remove()
    ttk.Checkbutton(licence_tab,text='Options avancées',variable=affiche_avancees,command=options_avancees).grid(row=8,column=0,columnspan=2,sticky='w')
    historique=ttk.Frame(licence_tab)
    historique.columnconfigure(0,weight=1);historique.rowconfigure(0,weight=1)
    registre=ttk.Treeview(historique,columns=('numero','client','postes','fin'),show='headings',height=4,selectmode='browse')
    for col,titre,large in [('numero','Licence',110),('client','Société',180),('postes','Postes',50),('fin','Échéance',90)]:
        registre.heading(col,text=titre);registre.column(col,width=large,minwidth=40)
    registre.grid(row=0,column=0,sticky='nsew')
    ascenseur=ttk.Scrollbar(historique,orient='vertical',command=registre.yview)
    ascenseur.grid(row=0,column=1,sticky='ns');registre.configure(yscrollcommand=ascenseur.set)
    historique.grid(row=10,column=0,columnspan=2,sticky='nsew',pady=8)
    licence_tab.rowconfigure(10,weight=1)

    def rafraichir(*_):
        registre.delete(*registre.get_children())
        try:
            choix_client['values']=list(clients_connus(v['dossier'].get()))
            for l in reversed(registre_lignes(v['dossier'].get())):
                registre.insert('', 'end', values=(l['numero'],l['client'],l['postes'],l['valable_jusqu_au'] or 'Permanente'))
        except (OSError,ValueError,KeyError) as exc:
            etat.set(f'Registre non disponible : {exc}')

    def generer():
        try:
            dossier=Path(v['dossier'].get())
            if not chemin_coffre(dossier).exists():
                raise ValueError('Créez votre identité, ou rassemblez le coffre existant dans ce dossier.')
            if not v['client'].get().strip():
                raise ValueError('Indiquez la société à licencier ou ouvrez sa demande.')
            cle=ouvrir_coffre()
            if cle is None:
                return
            a=argparse.Namespace(cle=str(chemin_coffre(dossier)), client=v['client'].get(), niu=v['niu'].get(),
                edition=v['edition'].get(), role=v['role'].get(), site=v['site'].get(), code=v['code'].get(),
                demande=v['demande'].get() or None, postes=int(v['postes'].get()), definitive=v['duree'].get()=='definitive',
                jusqu_au=v['jusqu_au'].get(),maj_jusqu_au=v['maj'].get(),sortie=str(dossier),fichier=None)
            fichier=emettre(a,cle_deverrouillee=cle)
            derniere_licence[0]=fichier
            memoriser();rafraichir()
            etat.set(f'Licence {fichier.name} créée à côté de coffre.dat et parametres.dat. Exportez le paquet client pour la remettre.')
        except (OSError,ValueError,SystemExit) as exc:
            erreur(exc)

    def exporter():
        try:
            chemin=derniere_licence[0]
            selection=registre.selection()
            if selection:
                numero=registre.item(selection[0],'values')[0]
                chemin=next((Path(l['fichier']) for l in registre_lignes(v['dossier'].get()) if l['numero']==numero),chemin)
            if not chemin:
                raise ValueError('Générez ou sélectionnez une licence dans la liste.')
            fichier=exporter_client(chemin,v['dossier'].get())
            etat.set(f'Paquet client : {fichier.name}. Il contient la licence, l’identité publique et la notice, jamais votre coffre.')
            return fichier
        except (OSError,ValueError,SystemExit) as exc:
            erreur(exc)

    confirmations_essai=iter((False,True)) if essai else None
    def supprimer():
        try:
            selection=registre.selection()
            if len(selection)!=1:
                raise ValueError('Sélectionnez la licence à supprimer dans la liste.')
            numero=registre.item(selection[0],'values')[0]
            detail=preparer_suppression(v['dossier'].get(),numero)
            texte=(f"Licence : {detail['numero']}\nSociété : {detail['client']}\n"
                   f"Édition : {detail['edition']} — {detail['postes']} postes\nServeur : {detail['machine']}\n"
                   f"Fichier : {Path(detail['fichier']).name}\n\n"
                   "Déplacer ce seul fichier dans la corbeille du dossier propriétaire ?\n"
                   "Les clés et les autres licences seront conservées.\n"
                   "Cette suppression locale ne révoque pas les licences déjà installées.")
            confirme=next(confirmations_essai) if essai else messagebox.askyesno('Supprimer la licence',texte,parent=fen)
            if not confirme:
                etat.set('Suppression annulée ; aucun fichier déplacé.')
                return
            supprimer_licence(v['dossier'].get(),detail,confirme=True)
            if derniere_licence[0] and str(derniere_licence[0].resolve())==detail['fichier']:
                derniere_licence[0]=None
            rafraichir()
            etat.set(f'Licence {numero} retirée et conservée en corbeille. Journal de suppression enregistré.')
        except (OSError,ValueError,SystemExit) as exc:
            erreur(exc)

    boutons=ttk.Frame(licence_onglet,padding=6)
    boutons.grid(row=1,column=0,columnspan=2,sticky='ew')
    generer_licence_btn=ttk.Button(boutons,text='Générer la licence',command=generer)
    generer_licence_btn.pack(side='left',padx=4)
    exporter_btn=ttk.Button(boutons,text='Exporter au client',command=exporter)
    exporter_btn.pack(side='left')
    supprimer_btn=ttk.Button(boutons,text='Supprimer la licence',command=supprimer)
    supprimer_btn.pack(side='left',padx=4)
    ttk.Label(licence_onglet,text='Le dossier complet et le coffre privé restent chez le propriétaire.',
              wraplength=520,padding=6).grid(row=2,column=0,columnspan=2,sticky='w')
    def molette(e):
        if onglets.select()==str(licence_onglet) and e.widget!=registre:
            defilement.yview_scroll(-1 if e.delta>0 else 1,'units')
    fen.bind('<MouseWheel>',molette)
    def dossier_change(*_):
        session.verrouiller();derniere_licence[0]=None;resultat_installation.set('')
        etat.set('Dossier sélectionné. Les nouvelles licences seront enregistrées ici avec les clés.')
        rafraichir()
    v['dossier'].trace_add('write',dossier_change)
    rafraichir()
    etat.set('Choisissez votre dossier. La création du code d’installation ne nécessite aucune clé.')
    if essai:
        try:
            dossier=Path(temporaire.name)
            assert len(onglets.tabs())==2
            generer_code_btn.invoke()
            assert fc.est_installation_courte(dernier_code[0])
            assert not chemin_coffre(dossier).exists() and not v['client'].get()
            onglets.select(licence_onglet)
            creer_btn.invoke()
            demande=dossier/'DEMANDE-ESSAI.erpdem'
            demande.write_text(fc.demande_ecrire({'societe':'Société fictive GUI','materiel':'POSTE-INTERFACE-FICTIF',
                'machine_nom':'GUI-FICTIVE','edition':'transport','role':'seul','site':'',
                'installation':dernier_code[0],'cle_installation':dernier_code[0]}),encoding='utf-8')
            charger_demande(demande)
            generer_licence_btn.invoke()
            assert derniere_licence[0] and derniere_licence[0].parent==dossier
            assert (dossier/'coffre.dat').exists() and (dossier/'parametres.dat').read_bytes().startswith(b'ERPID\x01')
            assert not (dossier/'cle-publique.txt').exists()
            fichier=exporter()
            import zipfile
            with zipfile.ZipFile(fichier) as z:
                assert 'coffre.dat' not in z.namelist() and 'parametres.dat' in z.namelist()
                assert len(z.namelist())==3
            assert (dossier/'INSTALLATION_CLE_PUBLIQUE.md').is_file()
            # Une deuxième licence reste intacte après annulation puis suppression de la première.
            premiere=derniere_licence[0]
            generer_licence_btn.invoke()
            seconde=derniere_licence[0]
            cible=next(i for i in registre.get_children() if registre.item(i,'values')[0]==registre_lignes(dossier)[0]['numero'])
            registre.selection_set(cible)
            supprimer_btn.invoke()
            assert premiere.exists() and len(registre_lignes(dossier))==2
            supprimer_btn.invoke()
            assert not premiere.exists() and seconde.exists() and len(registre_lignes(dossier))==1
            assert journal_suppressions(dossier)[-1]['etat']=='supprimee'
            for largeur,hauteur in ((760,640),(600,440)):
                fen.geometry(f'{largeur}x{hauteur}');fen.update()
                for bouton in (generer_licence_btn,exporter_btn,supprimer_btn):
                    assert bouton.winfo_ismapped()
                    assert bouton.winfo_rootx()+bouton.winfo_width()<=fen.winfo_rootx()+fen.winfo_width()
                    assert bouton.winfo_rooty()+bouton.winfo_height()<=fen.winfo_rooty()+fen.winfo_height()
                affiche_avancees.set(True);options_avancees();fen.update()
                defilement.yview_moveto(1.0);fen.update()
            # Le module 1 fonctionne encore après verrouillage du module Licence.
            verrouiller();onglets.select(installation_tab);generer_code_btn.invoke()
            assert session.cle is None
            fen.update()
            print('Interface 3.1 : deux modules, 760x640 et 600x440, actions accessibles, guide, suppression confirmée/journalisée, clés conservées : OK')
        finally:
            fermer();temporaire.cleanup()
        return
    fen.mainloop()


def question(texte, defaut=""):
    reponse = input(f"{texte}{f' [{defaut}]' if defaut else ''} : ").strip()
    return reponse or defaut


def menu():
    print("ERP OHADA — deux modules\n  1. Code d'installation autonome\n  2. Créer une licence\n  3. Quitter")
    choix = question("Choix", "1")
    if choix == "3":
        return
    dossier = Path(question("Dossier de travail", preferences().get("dossier_unique", preferences().get("cles", str(Path.home()/"ERP-OHADA-Licences")))))
    retenir(dossier_unique=str(dossier), cles=str(dossier), licences=str(dossier))
    if choix == "1":
        generer_installation(dossier)
    elif choix == "2":
        if not chemin_coffre(dossier).exists():
            creer_cles(dossier)
        duree = question("Durée en mois (ou P = permanente)", "12").upper()
        permanente = duree == "P"
        jusqu_au = None if permanente else dans_mois(int(duree))
        emettre(argparse.Namespace(cle=str(chemin_coffre(dossier)), demande=question("Demande du client (.erpdem)"),
            client=None, niu=None, edition=None, role=None, site=None, code=None, postes=int(question("Postes", "5")),
            definitive=permanente, jusqu_au=jusqu_au, maj_jusqu_au=jusqu_au or dans_mois(12), sortie=str(dossier), fichier=None))
    input("\nEntrée pour fermer…")


def main(argv):
    if not argv or argv == ["interface-essai"]:
        try:
            interface(essai=bool(argv))
        except ImportError:                                       # pas d'interface graphique : questions en console
            menu()
        return 0
    p = argparse.ArgumentParser(prog="ERP-OHADA-Licences")
    s = p.add_subparsers(dest="commande", required=True)
    c = s.add_parser("cles")
    c.add_argument("--dossier", required=True)
    c.set_defaults(noms_neutres=True)
    c.add_argument("--noms-neutres", action="store_true", help="format binaire par défaut : coffre.dat et parametres.dat")
    c.add_argument("--ancien-format", dest="noms_neutres", action="store_false", help="compatibilité explicite PEM / texte")
    i = s.add_parser("installation")
    for nom in ("--cle", "--client", "--edition"):
        i.add_argument(nom, help="ancienne clé signée seulement ; inutile pour le module autonome")
    i.add_argument("--dossier", help="dossier du code autonome, sans société ni clé")
    i.add_argument("--sortie")
    i.add_argument("--courte", action="store_true", help="référence de quatre groupes de six caractères")
    e = s.add_parser("emettre")
    e.add_argument("--cle", required=True)
    e.add_argument("--demande", help="demande de licence (.erpdem) envoyée par le client")
    for nom in ("--client", "--edition", "--role", "--code"):
        e.add_argument(nom)
    e.add_argument("--postes", type=int, required=True)
    e.add_argument("--site")
    e.add_argument("--niu")
    e.add_argument("--jusqu-au", dest="jusqu_au")
    e.add_argument("--mensuelle", action="store_true", help="valable 1 mois")
    e.add_argument("--trimestrielle", action="store_true", help="valable 3 mois")
    e.add_argument("--semestrielle", action="store_true", help="valable 6 mois")
    e.add_argument("--annuelle", action="store_true", help="valable 1 an")
    e.add_argument("--mois", type=int, help="valable ce nombre de mois")
    e.add_argument("--ans", type=int, help="valable ce nombre d'années")
    e.add_argument("--definitive", "--permanente", dest="definitive", action="store_true")
    e.add_argument("--maj-jusqu-au", dest="maj_jusqu_au")
    e.add_argument("--sortie")
    e.add_argument("--fichier", help="chemin exact du fichier .erplic à créer")
    ai = s.add_parser("autoriser-installation")
    for nom in ("--cle", "--code", "--jusqu-au", "--sortie"):
        ai.add_argument(nom, required=True)
    ai.add_argument("--reference", help="référence autonome 4×6 déjà générée, facultative")
    v = s.add_parser("verifier")
    v.add_argument("fichier")
    v.add_argument("--publique", required=True)
    a = p.parse_args(argv)
    if a.commande == "cles":
        creer_cles(a.dossier, noms_neutres=a.noms_neutres)
    elif a.commande == "installation":
        emettre_installation(a)
    elif a.commande == "emettre":
        emettre(a)
    elif a.commande == "autoriser-installation":
        print(creer_autorisation_installation(charger_cle(a.cle), a.code, a.reference, a.jusqu_au, a.sortie))
    else:
        verifier(a.fichier, a.publique)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


