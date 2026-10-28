"""Outil du PROPRIÉTAIRE pour émettre les licences de l'ERP OHADA (jamais livré aux clients).

Parcours : 1. clé d'installation remise à la société (avant l'installation) ; 2. la société envoie la DEMANDE de
licence produite par son serveur (nom de la machine, société, identifiant matériel, clé d'installation) ;
3. l'outil produit le fichier de licence .erplic ET la clé d'activation (le client utilise l'un ou l'autre).

    ERP-OHADA-Licences.exe                       fenêtre (double-clic)
    ERP-OHADA-Licences.exe cles --dossier D      crée la paire de clés (une seule fois, sur VOTRE ordinateur)
    ERP-OHADA-Licences.exe installation --cle D\\cle-privee.pem --client "…" --edition transport [--sortie D]
    ERP-OHADA-Licences.exe emettre --cle D\\cle-privee.pem --demande DEMANDE-….erpdem --postes 10 [--role siege]
                          [--jusqu-au 2027-10-31 | --definitive] [--maj-jusqu-au 2027-10-31] [--sortie D | --fichier F]
        (sans demande : --client "…" --edition transport --role siege --code T-ABCD-EFGH-IJKL-MNOP [--site …] [--niu …],
         fichier .erplic seulement)
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


def charger_cle(chemin, mdp=None):
    from cryptography.hazmat.primitives import serialization

    try:
        return serialization.load_pem_private_key(Path(chemin).read_bytes(), password=mdp or mot_de_passe())
    except (ValueError, TypeError):
        raise SystemExit("Mot de passe incorrect ou fichier de clé illisible.")


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


def emettre_installation(a, mdp=None):
    """Clé d'installation pour une société (avant l'installation du logiciel)."""
    if a.edition not in EDITIONS:
        raise SystemExit(f"Édition : {', '.join(EDITIONS)}.")
    if not a.client.strip():
        raise SystemExit("Nom de la société absent.")
    cle_chemin = Path(a.cle)
    registre = cle_chemin.with_name("registre-installations.csv")
    numero = prochain_numero(registre, "INS")
    texte = fc.installation_creer(charger_cle(cle_chemin, mdp), numero, a.client.strip(), a.edition)
    sortie = Path(a.sortie or cle_chemin.parent) / f"CLE-INSTALLATION-{numero}-{nom_propre(a.client)}.txt"
    sortie.parent.mkdir(parents=True, exist_ok=True)
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
    if cle_privee is not None and demande.get("cle_installation"):
        from cryptography.exceptions import InvalidSignature

        try:
            _, signe, signature = fc.installation_lire(demande["cle_installation"])
            cle_privee.public_key().verify(signature, signe)
        except (fc.CleInvalide, InvalidSignature):
            raise SystemExit("La clé d'installation de cette demande n'a pas été émise par vous : demande refusée.")
    return demande


def emettre(a, mdp=None):
    """Émet la licence : fichier .erplic, et la clé d'activation quand la licence part d'une demande.
    a.fichier : chemin exact du fichier ; sinon a.sortie (dossier) ou, à défaut, le dossier de la clé privée."""
    cle_chemin = Path(a.cle)
    cle_privee = charger_cle(cle_chemin, mdp)
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
    a.activation = activation
    return sortie


def nom_fichier(numero, client):
    return f"{numero}-{nom_propre(client)}.erplic"


def registre_lignes(dossier):
    registre = Path(dossier) / "registre-licences.csv"
    if not registre.exists():
        return []
    with open(registre, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def clients_connus(dossier):
    """Sociétés déjà servies (la plus récente licence de chacune) : pour les choisir dans la liste."""
    clients = {}
    for ligne in registre_lignes(dossier):
        clients[ligne["client"]] = ligne
    return dict(sorted(clients.items(), key=lambda c: c[0].lower()))


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
    """Fenêtre du propriétaire : choisir la société, régler la licence, choisir où l'enregistrer."""
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog, ttk

    fen = tk.Tk()
    fen.title("ERP OHADA — Licences (propriétaire)")
    fen.geometry("820x720")
    v = {nom: tk.StringVar(value=val) for nom, val in {
        "dossier": preferences().get("cles", str(Path.home() / "ERP-OHADA-Licences")),
        "licences": preferences().get("licences", str(bureau() / "Licences ERP")),
        "client": "", "niu": "", "edition": "transport",
        "role": "seul", "site": "", "postes": "5", "code": "", "demande": "", "duree": "abonnement",
        "jusqu_au": (datetime.date.today() + datetime.timedelta(days=365)).isoformat(),
        "maj": (datetime.date.today() + datetime.timedelta(days=365)).isoformat()}.items()}

    cadre = ttk.Frame(fen, padding=12)
    cadre.pack(fill="both", expand=True)
    cadre.columnconfigure(1, weight=1)

    def ligne(rang, libelle, widget):
        ttk.Label(cadre, text=libelle).grid(row=rang, column=0, sticky="w", pady=3, padx=(0, 8))
        widget.grid(row=rang, column=1, sticky="ew", pady=3)
        return widget

    # Dossier des clés
    zone = ttk.Frame(cadre)
    ttk.Entry(zone, textvariable=v["dossier"]).pack(side="left", fill="x", expand=True)
    ttk.Button(zone, text="Parcourir…", command=lambda: v["dossier"].set(
        filedialog.askdirectory(initialdir=v["dossier"].get()) or v["dossier"].get()) or rafraichir()).pack(side="left", padx=4)
    ligne(0, "Dossier de vos clés", zone)

    # Société : liste des clients déjà servis, ou nouvelle société
    choix_client = ligne(1, "Société (client)", ttk.Combobox(cadre, textvariable=v["client"]))
    ligne(2, "NIU", ttk.Entry(cadre, textvariable=v["niu"]))
    ligne(3, "Édition", ttk.Combobox(cadre, textvariable=v["edition"], values=EDITIONS, state="readonly"))
    ligne(4, "Rôle du serveur", ttk.Combobox(cadre, textvariable=v["role"], values=ROLES, state="readonly"))
    ligne(5, "Code du site (agence)", ttk.Entry(cadre, textvariable=v["site"]))
    ligne(6, "Postes", ttk.Spinbox(cadre, from_=1, to=500, textvariable=v["postes"]))
    zone_demande = ttk.Frame(cadre)
    ttk.Entry(zone_demande, textvariable=v["demande"]).pack(side="left", fill="x", expand=True)
    ttk.Button(zone_demande, text="Ouvrir une demande…", command=lambda: ouvrir_demande()).pack(side="left", padx=4)
    ligne(7, "Demande de licence (.erpdem)", zone_demande)
    serveur = ttk.Label(cadre, text="", foreground="#555")
    serveur.grid(row=12, column=1, sticky="w")
    ligne(11, "Sans demande : code d'activation", ttk.Entry(cadre, textvariable=v["code"]))
    def echeance(mois):
        v["duree"].set("abonnement")
        v["jusqu_au"].set(dans_mois(mois))
        v["maj"].set(dans_mois(mois))

    duree = ttk.Frame(cadre)
    ttk.Radiobutton(duree, text="Abonnement jusqu'au", value="abonnement", variable=v["duree"]).pack(side="left")
    ttk.Entry(duree, textvariable=v["jusqu_au"], width=12).pack(side="left", padx=4)
    for libelle, mois in (("1 mois", 1), ("3 mois", 3), ("6 mois", 6), ("1 an", 12), ("2 ans", 24), ("3 ans", 36)):
        ttk.Button(duree, text=libelle, width=6, command=lambda m=mois: echeance(m)).pack(side="left", padx=1)
    ttk.Radiobutton(duree, text="Permanente", value="definitive", variable=v["duree"]).pack(side="left", padx=(12, 0))
    ligne(8, "Durée", duree)
    ligne(9, "Mises à jour jusqu'au", ttk.Entry(cadre, textvariable=v["maj"]))

    registre = ttk.Treeview(cadre, columns=("numero", "client", "role", "postes", "fin"), show="headings", height=8)
    for col, titre, large in (("numero", "Licence", 110), ("client", "Société", 260), ("role", "Rôle", 90),
                              ("postes", "Postes", 60), ("fin", "Jusqu'au", 100)):
        registre.heading(col, text=titre)
        registre.column(col, width=large)
    registre.grid(row=13, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
    cadre.rowconfigure(13, weight=1)

    def rafraichir(*_):
        connus = clients_connus(v["dossier"].get())
        choix_client["values"] = list(connus)
        registre.delete(*registre.get_children())
        for l in reversed(registre_lignes(v["dossier"].get())):
            registre.insert("", "end", values=(l["numero"], l["client"], f"{l['role']} {l['site']}".strip(), l["postes"],
                                               l["valable_jusqu_au"] or "définitive"))

    def client_choisi(*_):
        connu = clients_connus(v["dossier"].get()).get(v["client"].get())
        if connu:
            v["niu"].set(connu.get("niu", ""))
            v["edition"].set(connu.get("edition") or v["edition"].get())

    choix_client.bind("<<ComboboxSelected>>", client_choisi)

    def ouvrir_demande():
        chemin = filedialog.askopenfilename(title="Demande de licence du client",
                                            filetypes=[("Demande de licence", "*.erpdem"), ("Tous les fichiers", "*.*")])
        if not chemin:
            return
        try:
            d = lire_demande(chemin)
        except SystemExit as exc:
            messagebox.showerror("Licences", str(exc))
            return
        v["demande"].set(chemin)
        v["client"].set(d["societe"])
        v["niu"].set(d.get("niu", ""))
        v["edition"].set(d.get("edition") or v["edition"].get())
        v["role"].set(d.get("role") or v["role"].get())
        v["site"].set(d.get("site", ""))
        v["code"].set(d.get("code", ""))
        serveur.configure(text=f"Serveur « {d.get('machine_nom', '?')} » · identifiant matériel {d['materiel']} · "
                               f"clé d'installation {d.get('installation') or 'aucune'}")

    def montrer_cle(titre, texte):
        fen.clipboard_clear()
        fen.clipboard_append(texte)
        boite = tk.Toplevel(fen)
        boite.title(titre)
        ttk.Label(boite, text=f"{titre} (déjà copiée : collez-la dans votre e-mail ou WhatsApp) :").pack(padx=10, pady=(10, 4))
        zone = tk.Text(boite, height=6, width=70, font=("Consolas", 10), wrap="word")
        zone.insert("1.0", texte)
        zone.pack(padx=10)
        ttk.Button(boite, text="Fermer", command=boite.destroy).pack(pady=8)

    def installation():
        dossier = Path(v["dossier"].get())
        if not (dossier / "cle-privee.pem").exists():
            messagebox.showerror("Licences", "Aucune clé privée dans ce dossier : créez d'abord la paire de clés.")
            return
        if not v["client"].get().strip():
            messagebox.showerror("Licences", "Saisissez la société (client).")
            return
        mdp = simpledialog.askstring("Licences", "Mot de passe de la clé privée :", show="*", parent=fen)
        if not mdp:
            return
        a = argparse.Namespace(cle=str(dossier / "cle-privee.pem"), client=v["client"].get(), edition=v["edition"].get(),
                               sortie=v["licences"].get())
        try:
            numero, texte, _ = emettre_installation(a, mdp.encode())
        except SystemExit as exc:
            messagebox.showerror("Licences", str(exc))
            return
        retenir(cles=str(dossier), licences=v["licences"].get())
        montrer_cle(f"Clé d'installation {numero}", texte)

    def generer():
        dossier = Path(v["dossier"].get())
        if not (dossier / "cle-privee.pem").exists():
            messagebox.showerror("Licences", "Aucune clé privée dans ce dossier : créez d'abord la paire de clés.")
            return
        if not v["client"].get().strip():
            messagebox.showerror("Licences", "Choisissez ou saisissez la société.")
            return
        numero = prochain_numero(dossier / "registre-licences.csv")
        fichier = Path(v["licences"].get()) / nom_fichier(numero, v["client"].get())
        mdp = simpledialog.askstring("Licences", "Mot de passe de la clé privée :", show="*", parent=fen)
        if not mdp:
            return
        a = argparse.Namespace(
            cle=str(dossier / "cle-privee.pem"), client=v["client"].get(), niu=v["niu"].get(), edition=v["edition"].get(),
            role=v["role"].get(), site=v["site"].get(), code=v["code"].get(), definitive=v["duree"].get() == "definitive",
            jusqu_au=v["jusqu_au"].get(), maj_jusqu_au=v["maj"].get(), sortie=None, fichier=fichier,
            demande=v["demande"].get() or None)
        try:
            a.postes = int(v["postes"].get())
            sortie = emettre(a, mdp.encode())
        except (SystemExit, ValueError) as exc:
            messagebox.showerror("Licences", str(exc) or "Valeur incorrecte.")
            return
        retenir(cles=str(dossier), licences=str(Path(sortie).parent))
        rafraichir()
        if a.activation:
            montrer_cle("Clé d'activation", a.activation)
        if messagebox.askyesno("Licences", f"Licence enregistrée :\n{sortie}\n\nEnvoyez ce fichier au client.\n\n"
                                           "Ouvrir le dossier maintenant ?"):
            ouvrir_dossier(Path(sortie).parent)

    def creer():
        dossier = Path(v["dossier"].get())
        if (dossier / "cle-privee.pem").exists():
            messagebox.showinfo("Licences", "La paire de clés existe déjà dans ce dossier.")
            return
        mdp = simpledialog.askstring("Licences", "Mot de passe de la nouvelle clé (10 caractères ou plus) :", show="*", parent=fen)
        if not mdp or len(mdp) < 10 or mdp != simpledialog.askstring("Licences", "Confirmez :", show="*", parent=fen):
            messagebox.showerror("Licences", "Mot de passe absent, trop court ou différent.")
            return
        os.environ["ERP_LICENCES_MDP"] = mdp
        try:
            creer_cles(dossier)
        finally:
            os.environ.pop("ERP_LICENCES_MDP", None)
        messagebox.showinfo("Licences", f"Clés créées dans {dossier}.\nEnvoyez le contenu de cle-publique.txt à Claude ;\n"
                                        "gardez une copie du dossier sur une clé USB au coffre.")

    zone_licences = ttk.Frame(cadre)
    ttk.Entry(zone_licences, textvariable=v["licences"]).pack(side="left", fill="x", expand=True)
    ttk.Button(zone_licences, text="Parcourir…", command=lambda: v["licences"].set(
        filedialog.askdirectory(initialdir=v["licences"].get(), title="Dossier où enregistrer les licences")
        or v["licences"].get())).pack(side="left", padx=4)
    ttk.Button(zone_licences, text="Ouvrir", command=lambda: ouvrir_dossier(v["licences"].get())).pack(side="left")
    ttk.Label(cadre, text="Dossier où enregistrer les licences").grid(row=10, column=0, sticky="w", pady=(10, 3), padx=(0, 8))
    zone_licences.grid(row=10, column=1, sticky="ew", pady=(10, 3))
    boutons = ttk.Frame(cadre)
    boutons.grid(row=14, column=0, columnspan=2, sticky="e", pady=(10, 0))
    ttk.Button(boutons, text="Créer la paire de clés", command=creer).pack(side="left", padx=4)
    ttk.Button(boutons, text="Clé d'installation", command=installation).pack(side="left", padx=4)
    ttk.Button(boutons, text="Générer la licence et la clé d'activation", command=generer).pack(side="left", padx=4)
    rafraichir()
    if essai:                                                     # contrôle automatique : la fenêtre se construit
        fen.update()
        fen.destroy()
        return
    fen.mainloop()


def question(texte, defaut=""):
    reponse = input(f"{texte}{f' [{defaut}]' if defaut else ''} : ").strip()
    return reponse or defaut


def menu():
    print("ERP OHADA — émission des licences\n  1. Créer la paire de clés (une seule fois)\n"
          "  2. Clé d'installation pour une société\n  3. Licence et clé d'activation (depuis la demande du client)\n"
          "  4. Quitter")
    choix = question("Choix", "3")
    dossier = Path(question("Dossier des clés", preferences().get("cles", str(Path.home() / "ERP-OHADA-Licences"))))
    sortie = question("Dossier où enregistrer", preferences().get("licences", str(bureau() / "Licences ERP")))
    retenir(cles=str(dossier), licences=sortie)
    if choix == "1":
        creer_cles(dossier)
    elif choix == "2":
        emettre_installation(argparse.Namespace(cle=str(dossier / "cle-privee.pem"), client=question("Société"),
                                                edition=question("Édition (transport, commerce, toutes)", "transport"),
                                                sortie=sortie))
    elif choix == "3":
        duree = question("Durée : M=mensuel, T=trimestriel, S=semestriel, A=annuel, 2/3=2 ou 3 ans, "
                         "P=permanente, ou une date AAAA-MM-JJ", "A").upper()
        defaut = {"M": dans_mois(1), "T": dans_mois(3), "S": dans_mois(6), "A": dans_mois(12),
                  "2": dans_mois(24), "3": dans_mois(36)}.get(duree)
        if duree in ("D", "P"):
            jusqu_au = None
        elif defaut:
            jusqu_au = defaut
        else:
            jusqu_au = question("Valable jusqu'au (AAAA-MM-JJ)", dans_mois(12)) if "-" not in duree else duree
        a = argparse.Namespace(
            cle=str(dossier / "cle-privee.pem"), demande=question("Fichier de la demande (.erpdem)"), client=None, niu=None,
            edition=None, role=None, site=None, code=None, postes=int(question("Postes", "5")), definitive=duree == "D",
            jusqu_au=jusqu_au, maj_jusqu_au=jusqu_au or dans_mois(12), sortie=sortie, fichier=None)
        emettre(a)
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
    i = s.add_parser("installation")
    for nom in ("--cle", "--client", "--edition"):
        i.add_argument(nom, required=True)
    i.add_argument("--sortie")
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
    v = s.add_parser("verifier")
    v.add_argument("fichier")
    v.add_argument("--publique", required=True)
    a = p.parse_args(argv)
    if a.commande == "cles":
        creer_cles(a.dossier)
    elif a.commande == "installation":
        emettre_installation(a)
    elif a.commande == "emettre":
        emettre(a)
    else:
        verifier(a.fichier, a.publique)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
