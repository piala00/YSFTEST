"""Socle commun des logiciels de l'ERP OHADA (client bureau).

Chaque module (Gestion commerciale, Comptabilité, Reporting) est un logiciel
indépendant construit sur ce socle :

    ┌──────────────────────────────────────────────────────────┐
    │ En-tête : nom du module · utilisateur · déconnexion       │
    ├──────────────────────────────────────────────────────────┤
    │ Onglets : [Structure] [Ventes] [Achats] ...               │
    ├───────────────┬──────────────────────────────────────────┤
    │ Éléments      │                                          │
    │  ▸ Élément    │      Zone de travail                      │
    │     • Sous-…  │                                          │
    └───────────────┴──────────────────────────────────────────┘

La structure (onglets, éléments, sous-éléments) est fournie par le serveur
(/api/navigation/). Un élément disposant d'un écran natif s'affiche dans la
zone de travail ; les autres s'ouvrent dans le navigateur.
"""
import csv
import json
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from api_client import ApiError, ErpApi

CONFIG_FILE = Path.home() / ".erp_ohada.json"

MODULES = {
    "commercial": {"titre": "Gestion commerciale", "couleur": "#1565c0",
                   "description": "Tiers, articles, ventes, achats, stock, règlements"},
    "comptabilite": {"titre": "Comptabilité OHADA", "couleur": "#2e7d32",
                     "description": "Plan SYSCOHADA, saisie, grand livre, balance, états financiers"},
    "reporting": {"titre": "Reporting", "couleur": "#6a1b9a",
                  "description": "Tableaux de bord, analyses, balances âgées, synthèses"},
}


def montant(valeur):
    try:
        return f"{float(valeur):,.0f}".replace(",", " ")
    except (TypeError, ValueError):
        return ""


def charger_config():
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"serveur": "http://127.0.0.1:8000"}


def sauver_config(config):
    try:
        CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")
    except OSError:
        pass


DOSSIER = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve().parent
EXECUTABLES = {"commercial": "ERP_Commercial", "comptabilite": "ERP_Comptabilite", "reporting": "ERP_Reporting"}


def lancer_module(code):
    """Ouvre un autre logiciel de l'ERP dans sa propre fenêtre (processus séparé)."""
    if getattr(sys, "frozen", False):
        commande = [str(DOSSIER / f"{EXECUTABLES[code]}.exe")]
    else:
        commande = [sys.executable, str(DOSSIER / f"{code}.py")]
    subprocess.Popen(commande, cwd=DOSSIER)


def assombrir(couleur, facteur=0.8):
    r, g, b = (int(couleur[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(int(c * facteur) for c in (r, g, b))


# ---------------------------------------------------------------------------
# Composants
# ---------------------------------------------------------------------------
class Tableau(ctk.CTkFrame):
    """Treeview stylé avec barre de défilement et export CSV."""

    def __init__(self, master, colonnes, on_double_click=None, **kwargs):
        super().__init__(master, **kwargs)
        self.colonnes = colonnes  # [(cle, titre, largeur, alignement)]
        self.lignes = []
        self.tree = ttk.Treeview(self, columns=[c[0] for c in colonnes], show="headings", selectmode="browse")
        for cle, titre, largeur, align in colonnes:
            self.tree.heading(cle, text=titre)
            self.tree.column(cle, width=largeur, anchor=align, stretch=align == "w")
        barre = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=barre.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        barre.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.tree.tag_configure("total", font=("Segoe UI", 10, "bold"), background="#e8eef6")
        self.tree.tag_configure("alerte", foreground="#c62828")
        if on_double_click:
            self.tree.bind("<Double-1>", lambda e: self.selection() and on_double_click(self.selection()))

    def remplir(self, lignes, tags=None):
        self.tree.delete(*self.tree.get_children())
        self.lignes = lignes
        for i, ligne in enumerate(lignes):
            valeurs = [ligne.get(c[0], "") for c in self.colonnes]
            self.tree.insert("", "end", iid=str(i), values=valeurs, tags=(tags(ligne),) if tags else ())

    def selection(self):
        sel = self.tree.selection()
        return self.lignes[int(sel[0])] if sel else None

    def exporter(self):
        chemin = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not chemin:
            return
        with open(chemin, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow([c[1] for c in self.colonnes])
            for ligne in self.lignes:
                writer.writerow([ligne.get(c[0], "") for c in self.colonnes])
        messagebox.showinfo("Export", f"Fichier enregistré :\n{chemin}")


class Page(ctk.CTkFrame):
    """Écran affiché dans la zone de travail d'un module."""

    def __init__(self, app, titre):
        super().__init__(app.contenu, fg_color="transparent")
        self.app = app
        self.api = app.api
        self.titre = titre
        entete = ctk.CTkFrame(self, fg_color="transparent")
        entete.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(entete, text=titre, font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        self.barre = ctk.CTkFrame(entete, fg_color="transparent", height=30)
        self.barre.pack(side="right")

    def bouton(self, texte, commande, **kwargs):
        kwargs.setdefault("fg_color", self.app.couleur)
        kwargs.setdefault("hover_color", assombrir(self.app.couleur))
        b = ctk.CTkButton(self.barre, text=texte, command=commande, width=110, **kwargs)
        b.pack(side="left", padx=4)
        return b

    def charger(self, fonction, rappel):
        """Exécute un appel API en arrière-plan puis met à jour l'interface."""
        self.app.statut("Chargement…")

        def tache():
            try:
                resultat = fonction()
            except ApiError as exc:
                message = str(exc)
                self.after(0, lambda: (self.app.statut(""), messagebox.showerror("Erreur", message)))
                return
            self.after(0, lambda: (rappel(resultat), self.app.statut("")))

        threading.Thread(target=tache, daemon=True).start()

    def rafraichir(self):
        pass


class PageListe(Page):
    colonnes = []

    def __init__(self, app, titre):
        super().__init__(app, titre)
        self.recherche = ctk.CTkEntry(self.barre, placeholder_text="Rechercher…", width=200)
        self.recherche.pack(side="left", padx=4)
        self.recherche.bind("<Return>", lambda e: self.rafraichir())
        self.bouton("Actualiser", self.rafraichir)
        self.bouton("Export CSV", lambda: self.tableau.exporter(), fg_color="#455a64", hover_color="#37474f")
        self.tableau = Tableau(self, self.colonnes, on_double_click=self.ouvrir)
        self.tableau.pack(fill="both", expand=True)

    def ouvrir(self, ligne):
        pass


class PageWeb(Page):
    """Élément sans écran natif : ouverture dans le navigateur."""

    def __init__(self, app, titre, url):
        super().__init__(app, titre)
        self.url = app.api.base_url + url
        cadre = ctk.CTkFrame(self, corner_radius=10)
        cadre.pack(fill="x", pady=20)
        ctk.CTkLabel(cadre, text="Cet écran s'affiche dans le navigateur web.", font=ctk.CTkFont(size=14)).pack(pady=(24, 4))
        ctk.CTkLabel(cadre, text=self.url, text_color="gray").pack(pady=4)
        ctk.CTkButton(cadre, text="Ouvrir dans le navigateur", fg_color=app.couleur, hover_color=assombrir(app.couleur),
                      command=self.ouvrir).pack(pady=(8, 24))

    def ouvrir(self):
        webbrowser.open(self.url)


# ---------------------------------------------------------------------------
# Connexion
# ---------------------------------------------------------------------------
class FenetreConnexion(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title(f"Connexion — {app.titre}")
        self.geometry("380x340")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", app.destroy)
        ctk.CTkLabel(self, text=app.titre, font=ctk.CTkFont(size=22, weight="bold"), text_color=app.couleur).pack(pady=(22, 2))
        ctk.CTkLabel(self, text="ERP OHADA", text_color="gray").pack(pady=(0, 10))
        self.serveur = ctk.CTkEntry(self, width=290, placeholder_text="Adresse du serveur")
        self.serveur.insert(0, app.config_data.get("serveur", ""))
        self.serveur.pack(pady=5)
        self.utilisateur = ctk.CTkEntry(self, width=290, placeholder_text="Utilisateur")
        self.utilisateur.insert(0, app.config_data.get("utilisateur", ""))
        self.utilisateur.pack(pady=5)
        self.mdp = ctk.CTkEntry(self, width=290, placeholder_text="Mot de passe", show="•")
        self.mdp.pack(pady=5)
        self.mdp.bind("<Return>", lambda e: self.connecter())
        ctk.CTkButton(self, text="Se connecter", width=290, fg_color=app.couleur, hover_color=assombrir(app.couleur),
                      command=self.connecter).pack(pady=15)
        self.after(100, self.grab_set)

    def connecter(self):
        api = ErpApi(self.serveur.get().strip())
        try:
            token = api.connecter(self.utilisateur.get().strip(), self.mdp.get())
        except ApiError as exc:
            messagebox.showerror("Connexion", str(exc), parent=self)
            return
        self.app.config_data.update(serveur=api.base_url, utilisateur=self.utilisateur.get().strip(), token=token)
        sauver_config(self.app.config_data)
        self.grab_release()
        self.destroy()
        self.app.demarrer(api)


# ---------------------------------------------------------------------------
# Logiciel d'un module
# ---------------------------------------------------------------------------
class ModuleApp(ctk.CTk):
    """Fenêtre principale d'un module : barre de menus, en-tête, barre de navigation, zone de travail.

    `ecrans` associe le code d'un élément de navigation à une fabrique
    `fabrique(app, element) -> Page | None` (None : action sans écran, ex. ouvrir une fenêtre).
    """

    def __init__(self, code_module, ecrans):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        info = MODULES[code_module]
        self.code_module = code_module
        self.titre = info["titre"]
        self.couleur = info["couleur"]
        self.ecrans = ecrans
        self.title(f"{self.titre} — ERP OHADA")
        self.geometry("1320x800")
        self.minsize(1050, 620)
        self.config_data = charger_config()
        self.api = None
        self.navigation = None
        self.pages = {}
        self.noeuds = {}
        self.page_courante = None
        self.onglet_courant = None

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("Arbre.Treeview", rowheight=28, font=("Segoe UI", 10), background="#ffffff",
                        fieldbackground="#ffffff", borderwidth=0)
        style.map("Arbre.Treeview", background=[("selected", "#e3ebf6")], foreground=[("selected", self.couleur)])

        token = self.config_data.get("token")
        if token and self.config_data.get("serveur"):
            api = ErpApi(self.config_data["serveur"], token)
            try:
                api.get("journaux/")
                self.after(10, lambda: self.demarrer(api))
                return
            except ApiError:
                pass
        self.withdraw()
        self.after(10, lambda: FenetreConnexion(self))

    # --- Construction ----------------------------------------------------
    def demarrer(self, api):
        self.api = api
        try:
            self.navigation = api.navigation(self.code_module)
        except ApiError as exc:
            messagebox.showerror("Erreur", str(exc))
            self.destroy()
            return
        self.deiconify()
        self._barre_menus()
        self._entete()
        corps = ctk.CTkFrame(self, fg_color="#f4f6f9", corner_radius=0)
        corps.pack(fill="both", expand=True)
        self._barre_navigation(corps)
        self.contenu = ctk.CTkFrame(corps, fg_color="transparent")
        self.contenu.pack(side="left", fill="both", expand=True, padx=16, pady=14)
        onglets = self.navigation["onglets"]
        defaut = next((o for o in onglets if o["code"] in ("traitement", "etat")), onglets[0])
        self.choisir_onglet(defaut["titre"])

    def _barre_menus(self):
        """Barre de menus Windows native : Fichier · Structure · Traitement · État · Fenêtre · ?"""
        barre = tk.Menu(self, tearoff=0)

        def remplir(menu, elements):
            for el in elements:
                if el.get("separateur"):
                    menu.add_separator()
                elif el["enfants"]:
                    sous_menu = tk.Menu(menu, tearoff=0)
                    remplir(sous_menu, el["enfants"])
                    menu.add_cascade(label=el["titre"], menu=sous_menu)
                elif self.element_disponible(el):
                    menu.add_command(label=el["titre"], command=lambda e=el: self.ouvrir_depuis_menu(e))
                else:
                    menu.add_command(label=el["titre"], state="disabled")

        for onglet in self.navigation["onglets"]:
            menu = tk.Menu(barre, tearoff=0)
            remplir(menu, onglet["elements"])
            barre.add_cascade(label=onglet["titre"], menu=menu)
        self.configure(menu=barre)

    def _entete(self):
        entete = ctk.CTkFrame(self, fg_color=self.couleur, corner_radius=0, height=44)
        entete.pack(fill="x")
        ctk.CTkLabel(entete, text=self.titre, text_color="white", font=ctk.CTkFont(size=17, weight="bold")).pack(side="left", padx=16, pady=8)
        self.libelle_statut = ctk.CTkLabel(entete, text="", text_color="#e0e0e0")
        self.libelle_statut.pack(side="left", padx=10)
        ctk.CTkLabel(entete, text=f"{self.config_data.get('utilisateur', '')} · {self.api.base_url}",
                     text_color="#e0e0e0").pack(side="right", padx=16)

    def _barre_navigation(self, parent):
        cadre = ctk.CTkFrame(parent, fg_color="white", corner_radius=0, width=280)
        cadre.pack(side="left", fill="y")
        self.cadre_navigation = cadre
        cadre.pack_propagate(False)
        menus = [o["titre"] for o in self.navigation["onglets"] if o["code"] != "aide"]
        self.choix_menu = ctk.CTkOptionMenu(cadre, values=menus, command=self.choisir_onglet, fg_color=self.couleur,
                                            button_color=assombrir(self.couleur), button_hover_color=assombrir(self.couleur, 0.7))
        self.choix_menu.pack(fill="x", padx=10, pady=(10, 6))
        self.arbre = ttk.Treeview(cadre, show="tree", style="Arbre.Treeview", selectmode="browse")
        self.arbre.pack(fill="both", expand=True, padx=(6, 0), pady=(0, 8))
        self.arbre.tag_configure("groupe", font=("Segoe UI", 10, "bold"))
        self.arbre.tag_configure("desactive", foreground="#a3abb4")
        self.arbre.bind("<<TreeviewSelect>>", self._element_choisi)
        self.arbre.bind("<Double-1>", self._double_clic)

    # --- Navigation ------------------------------------------------------
    # Commandes d'interface disponibles dans le client bureau (les autres sont grisées)
    ACTIONS_BUREAU = {"imprimer", "fermer", "quitter", "actualiser", "copier", "rechercher", "ajouter", "barre_verticale"}

    def element_disponible(self, el):
        if el.get("interdit"):            # Fichier › Autorisations d'accès
            return False
        if el["action"]:
            return el["action"] in self.ACTIONS_BUREAU
        return bool(el["url"] or el["code"] in self.ecrans)

    def choisir_onglet(self, titre):
        onglet = next(o for o in self.navigation["onglets"] if o["titre"] == titre)
        self.choix_menu.set(titre)
        self.arbre.delete(*self.arbre.get_children())
        self.noeuds.clear()
        self.onglet_courant = onglet["code"]

        def inserer(parent, elements):
            for el in elements:
                if el.get("separateur"):
                    continue
                if el["enfants"]:
                    texte, tags = "  " + el["titre"], ("groupe",)
                else:
                    externe = "  ↗" if el["module"] else ""
                    texte = "  • " + el["titre"] + externe
                    tags = () if self.element_disponible(el) else ("desactive",)
                iid = self.arbre.insert(parent, "end", text=texte, open=True, tags=tags)
                self.noeuds[iid] = el
                inserer(iid, el["enfants"])

        inserer("", onglet["elements"])
        premier = next((iid for iid, el in self.noeuds.items()
                        if not el["module"] and not el["action"] and (el["url"] or el["code"] in self.ecrans)), None)
        if premier:
            self.arbre.selection_set(premier)
            self.arbre.see(premier)

    def ouvrir_depuis_menu(self, element):
        """Commande choisie dans la barre de menus : synchronise la barre de navigation."""
        if element["module"] or element["action"]:
            self.ouvrir_element(element)
            return
        onglet = next((o for o in self.navigation["onglets"] if self._contient(o["elements"], element["code"])), None)
        if onglet and onglet["code"] != "aide" and onglet["code"] != self.onglet_courant:
            self.choisir_onglet(onglet["titre"])
        iid = next((i for i, el in self.noeuds.items() if el["code"] == element["code"]), None)
        if iid:
            self.arbre.selection_set(iid)
            self.arbre.see(iid)
        else:
            self.ouvrir_element(element)

    def _contient(self, elements, code):
        return any(el["code"] == code or self._contient(el["enfants"], code) for el in elements)

    def _element_choisi(self, _event=None):
        sel = self.arbre.selection()
        if sel:
            el = self.noeuds[sel[0]]
            if not el["module"] and not el["action"]:   # les commandes externes s'ouvrent au double-clic
                self.ouvrir_element(el)

    def _double_clic(self, _event=None):
        sel = self.arbre.selection()
        if not sel:
            return
        el = self.noeuds[sel[0]]
        if el["module"] or el["action"]:
            self.ouvrir_element(el)
        elif el["code"] not in self.ecrans and el["url"]:
            webbrowser.open(self.api.base_url + el["url"])

    def ouvrir_element(self, element):
        code = element["code"]
        action = element.get("action")
        if action == "quitter":
            self.deconnecter()
            return
        if action == "fermer":
            self.destroy()
            return
        if action == "barre_verticale":
            if self.cadre_navigation.winfo_ismapped():
                self.cadre_navigation.pack_forget()
            else:
                self.cadre_navigation.pack(side="left", fill="y", before=self.contenu)
            return
        if action == "copier":
            ligne = getattr(getattr(self.page_courante, "tableau", None), "selection", lambda: None)()
            if ligne:
                tableau = self.page_courante.tableau
                self.clipboard_clear()
                self.clipboard_append("\t".join(str(ligne.get(c[0], "")) for c in tableau.colonnes))
                self.statut("Ligne copiée dans le presse-papiers")
            return
        if action == "rechercher":
            champ = getattr(self.page_courante, "recherche", None)
            if champ is not None:
                champ.focus_set()
            return
        if action == "ajouter":
            creer = getattr(self.page_courante, "nouvelle_facture", None)
            if creer and self.page_courante.domaine != "stocks":
                creer()
            return
        if action == "actualiser":
            if self.page_courante is not None:
                self.page_courante.rafraichir()
            return
        if action == "imprimer":
            page = self.page_courante
            if isinstance(page, PageWeb):
                page.ouvrir()
            elif page is not None and hasattr(page, "tableau"):
                page.tableau.exporter()
            return
        if element["module"] in MODULES:
            lancer_module(element["module"])
            return
        if element["module"]:          # page web hors logiciel (administration, portail…)
            webbrowser.open(self.api.base_url + element["url"])
            return
        if code == "aide.a_propos":
            messagebox.showinfo("À propos", f"ERP OHADA — {self.titre}\nServeur : {self.api.base_url}\n"
                                            f"Utilisateur : {self.config_data.get('utilisateur', '')}")
            return
        if code in self.pages:
            self.afficher(self.pages[code])
            return
        if code in self.ecrans and not element["enfants"]:
            page = self.ecrans[code](self, element)
            if page is None:          # action (fenêtre de saisie…)
                return
        elif element["url"]:
            page = PageWeb(self, element["titre"], element["url"])
        else:
            return                    # sous-menu ou commande non disponible
        self.pages[code] = page
        self.afficher(page)

    def afficher(self, page):
        if self.page_courante is not None:
            self.page_courante.pack_forget()
        self.page_courante = page
        page.pack(fill="both", expand=True)
        page.rafraichir()

    def statut(self, texte):
        if hasattr(self, "libelle_statut"):
            self.libelle_statut.configure(text=texte)

    def deconnecter(self):
        self.config_data.pop("token", None)
        sauver_config(self.config_data)
        self.destroy()


def lancer(code_module, ecrans):
    ModuleApp(code_module, ecrans).mainloop()
