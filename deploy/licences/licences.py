"""Outil du PROPRIÉTAIRE pour émettre les licences de l'ERP OHADA (jamais livré aux clients).

    ERP-OHADA-Licences.exe                       fenêtre (double-clic) : société, licence, « Enregistrer sous »
    ERP-OHADA-Licences.exe cles --dossier D      crée la paire de clés (une seule fois, sur VOTRE ordinateur)
    ERP-OHADA-Licences.exe emettre --cle D\\cle-privee.pem --client "…" --edition transport --role siege
                          --postes 10 --code T-ABCD-EFGH-IJKL-MNOP [--site SIEGE] [--niu …]
                          [--jusqu-au 2027-10-31 | --definitive] [--maj-jusqu-au 2027-10-31] [--sortie D | --fichier F]
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


def prochain_numero(registre):
    annee = datetime.date.today().year
    n = 0
    if registre.exists():
        with open(registre, encoding="utf-8", newline="") as f:
            for ligne in csv.DictReader(f, delimiter=";"):
                m = re.match(rf"LIC-{annee}-(\d+)$", ligne.get("numero", ""))
                n = max(n, int(m[1])) if m else n
    return f"LIC-{annee}-{n + 1:04d}"


def emettre(a, mdp=None):
    """Émet la licence. a.fichier : chemin exact choisi par le propriétaire (« Enregistrer sous ») ;
    sinon a.sortie (dossier) ou, à défaut, le dossier de la clé privée."""
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
    signature = charger_cle(cle_chemin, mdp).sign(canonique(donnees))
    texte = "\n".join([ENTETE, base64.b64encode(canonique(donnees)).decode(), base64.b64encode(signature).decode(), ""])
    if getattr(a, "fichier", None):
        sortie = Path(a.fichier)
        if sortie.suffix.lower() != ".erplic":
            sortie = sortie.with_name(sortie.name + ".erplic")
    else:
        sortie = Path(a.sortie or cle_chemin.parent) / nom_fichier(donnees["numero"], donnees["client"])
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(texte, encoding="utf-8")
    nouveau = not registre.exists()
    with open(registre, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        if nouveau:
            w.writerow(["numero", "client", "niu", "edition", "role", "site", "postes", "machine", "emise_le",
                        "valable_jusqu_au", "maj_jusqu_au", "fichier"])
        w.writerow([donnees[k] or "" for k in ("numero", "client", "niu", "edition", "role", "site", "postes", "machine",
                                               "emise_le", "valable_jusqu_au", "maj_jusqu_au")] + [str(sortie)])
    print(f"Licence {donnees['numero']} : {sortie}")
    print(f"  {donnees['client']} · {donnees['edition']} · {donnees['role']}{' ' + donnees['site'] if donnees['site'] else ''}"
          f" · {donnees['postes']} postes · {'définitive' if jusqu_au is None else 'jusqu au ' + jusqu_au}")
    return sortie


def nom_fichier(numero, client):
    return f"{numero}-{re.sub(r'[^A-Za-z0-9]+', '-', client).strip('-')[:40]}.erplic"


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


def interface(essai=False):
    """Fenêtre du propriétaire : choisir la société, régler la licence, choisir où l'enregistrer."""
    import tkinter as tk
    from tkinter import filedialog, messagebox, simpledialog, ttk

    fen = tk.Tk()
    fen.title("ERP OHADA — Licences (propriétaire)")
    fen.geometry("760x640")
    v = {nom: tk.StringVar(value=val) for nom, val in {
        "dossier": str(Path.home() / "ERP-OHADA-Licences"), "client": "", "niu": "", "edition": "transport",
        "role": "seul", "site": "", "postes": "5", "code": "", "duree": "annuelle",
        "jusqu_au": (datetime.date.today() + datetime.timedelta(days=365)).isoformat(),
        "maj": (datetime.date.today() + datetime.timedelta(days=365)).isoformat()}.items()}
    dernier_dossier = {"chemin": str(Path.home())}

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
    ligne(7, "Code d'activation du client", ttk.Entry(cadre, textvariable=v["code"]))
    duree = ttk.Frame(cadre)
    ttk.Radiobutton(duree, text="Abonnement jusqu'au", value="annuelle", variable=v["duree"]).pack(side="left")
    ttk.Entry(duree, textvariable=v["jusqu_au"], width=12).pack(side="left", padx=4)
    ttk.Radiobutton(duree, text="Licence définitive", value="definitive", variable=v["duree"]).pack(side="left", padx=12)
    ligne(8, "Durée", duree)
    ligne(9, "Mises à jour jusqu'au", ttk.Entry(cadre, textvariable=v["maj"]))

    registre = ttk.Treeview(cadre, columns=("numero", "client", "role", "postes", "fin"), show="headings", height=8)
    for col, titre, large in (("numero", "Licence", 110), ("client", "Société", 260), ("role", "Rôle", 90),
                              ("postes", "Postes", 60), ("fin", "Jusqu'au", 100)):
        registre.heading(col, text=titre)
        registre.column(col, width=large)
    registre.grid(row=11, column=0, columnspan=2, sticky="nsew", pady=(12, 0))
    cadre.rowconfigure(11, weight=1)

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

    def generer():
        dossier = Path(v["dossier"].get())
        if not (dossier / "cle-privee.pem").exists():
            messagebox.showerror("Licences", "Aucune clé privée dans ce dossier : créez d'abord la paire de clés.")
            return
        if not v["client"].get().strip():
            messagebox.showerror("Licences", "Choisissez ou saisissez la société.")
            return
        numero = prochain_numero(dossier / "registre-licences.csv")
        fichier = filedialog.asksaveasfilename(
            title="Enregistrer la licence", initialdir=dernier_dossier["chemin"], defaultextension=".erplic",
            initialfile=nom_fichier(numero, v["client"].get()), filetypes=[("Licence ERP OHADA", "*.erplic")])
        if not fichier:
            return
        mdp = simpledialog.askstring("Licences", "Mot de passe de la clé privée :", show="*", parent=fen)
        if not mdp:
            return
        a = argparse.Namespace(
            cle=str(dossier / "cle-privee.pem"), client=v["client"].get(), niu=v["niu"].get(), edition=v["edition"].get(),
            role=v["role"].get(), site=v["site"].get(), code=v["code"].get(), definitive=v["duree"].get() == "definitive",
            jusqu_au=v["jusqu_au"].get(), maj_jusqu_au=v["maj"].get(), sortie=None, fichier=fichier)
        try:
            a.postes = int(v["postes"].get())
            sortie = emettre(a, mdp.encode())
        except (SystemExit, ValueError) as exc:
            messagebox.showerror("Licences", str(exc) or "Valeur incorrecte.")
            return
        dernier_dossier["chemin"] = str(Path(sortie).parent)
        rafraichir()
        messagebox.showinfo("Licences", f"Licence enregistrée :\n{sortie}\n\nEnvoyez ce fichier au client.")

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

    boutons = ttk.Frame(cadre)
    boutons.grid(row=10, column=0, columnspan=2, sticky="e", pady=(10, 0))
    ttk.Button(boutons, text="Créer la paire de clés", command=creer).pack(side="left", padx=4)
    ttk.Button(boutons, text="Générer la licence…", command=generer).pack(side="left", padx=4)
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
    e.add_argument("--fichier", help="chemin exact du fichier .erplic à créer")
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
