"""ERP OHADA — client bureau (Windows / Linux / macOS).

Se connecte au serveur Django via l'API REST. Lancer :  python app.py
"""
import csv
import json
import threading
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from api_client import ApiError, ErpApi

CONFIG_FILE = Path.home() / ".erp_ohada.json"
TVA_DEFAUT = 19.25


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
    titre = ""

    def __init__(self, app):
        super().__init__(app.contenu, fg_color="transparent")
        self.app = app
        self.api = app.api
        entete = ctk.CTkFrame(self, fg_color="transparent")
        entete.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(entete, text=self.titre, font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        self.barre = ctk.CTkFrame(entete, fg_color="transparent")
        self.barre.pack(side="right")

    def bouton(self, texte, commande, **kwargs):
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
                self.after(0, lambda: (self.app.statut(""), messagebox.showerror("Erreur", str(exc))))
                return
            self.after(0, lambda: (rappel(resultat), self.app.statut("")))

        threading.Thread(target=tache, daemon=True).start()

    def rafraichir(self):
        pass


class PageListe(Page):
    colonnes = []

    def __init__(self, app):
        super().__init__(app)
        self.recherche = ctk.CTkEntry(self.barre, placeholder_text="Rechercher…", width=200)
        self.recherche.pack(side="left", padx=4)
        self.recherche.bind("<Return>", lambda e: self.rafraichir())
        self.bouton("Actualiser", self.rafraichir)
        self.bouton("Export CSV", lambda: self.tableau.exporter(), fg_color="#2e7d32")
        self.tableau = Tableau(self, self.colonnes, on_double_click=self.ouvrir)
        self.tableau.pack(fill="both", expand=True)

    def ouvrir(self, ligne):
        pass


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------
class PageDashboard(Page):
    titre = "Tableau de bord"

    def __init__(self, app):
        super().__init__(app)
        self.bouton("Actualiser", self.rafraichir)
        self.grille = ctk.CTkFrame(self, fg_color="transparent")
        self.grille.pack(fill="x")
        self.kpis = {}
        indicateurs = [
            ("ca_exercice", "CA HT exercice"), ("marge_commerciale", "Marge commerciale"),
            ("resultat", "Résultat net"), ("tresorerie", "Trésorerie nette"),
            ("creances_clients", "Créances clients"), ("dettes_fournisseurs", "Dettes fournisseurs"),
            ("valeur_stock", "Valeur du stock"), ("ca_mois", "CA du mois"),
        ]
        for i, (cle, libelle) in enumerate(indicateurs):
            carte = ctk.CTkFrame(self.grille, corner_radius=10)
            carte.grid(row=i // 4, column=i % 4, padx=6, pady=6, sticky="nsew")
            self.grille.grid_columnconfigure(i % 4, weight=1)
            ctk.CTkLabel(carte, text=libelle.upper(), text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=14, pady=(10, 0))
            valeur = ctk.CTkLabel(carte, text="—", font=ctk.CTkFont(size=20, weight="bold"))
            valeur.pack(anchor="w", padx=14, pady=(0, 10))
            self.kpis[cle] = valeur
        bas = ctk.CTkFrame(self, fg_color="transparent")
        bas.pack(fill="both", expand=True, pady=10)
        bas.grid_columnconfigure((0, 1), weight=1)
        bas.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(bas, text="CA mensuel (HT)", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(bas, text="Alertes de stock", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, sticky="w")
        self.mensuel = Tableau(bas, [("mois", "Mois", 120, "w"), ("montant", "CA HT", 140, "e")])
        self.mensuel.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        self.alertes = Tableau(bas, [("designation", "Article", 220, "w"), ("stock", "Stock", 90, "e"), ("stock_minimum", "Minimum", 90, "e")])
        self.alertes.grid(row=1, column=1, sticky="nsew", padx=(6, 0))

    def rafraichir(self):
        self.charger(self.api.dashboard, self.afficher)

    def afficher(self, d):
        for cle, label in self.kpis.items():
            valeur = float(d.get(cle) or 0)
            label.configure(text=montant(valeur), text_color="#c62828" if valeur < 0 else ("gray10", "gray90"))
        self.mensuel.remplir([{"mois": m["mois"], "montant": montant(m["montant"])} for m in d["ca_mensuel"]])
        self.alertes.remplir(d["alertes_stock"], tags=lambda l: "alerte")


class PageTiers(PageListe):
    colonnes = [("code", "Code", 90, "w"), ("nom", "Nom", 260, "w"), ("ville", "Ville", 140, "w"),
                ("telephone", "Téléphone", 140, "w"), ("niu", "NIU", 140, "w"), ("delai_paiement", "Délai (j)", 80, "e")]

    def __init__(self, app, type_tiers):
        self.type_tiers = type_tiers
        self.titre = "Clients" if type_tiers == "CLIENT" else "Fournisseurs"
        super().__init__(app)

    def rafraichir(self):
        self.charger(lambda: self.api.tiers(self.type_tiers, self.recherche.get()), self.tableau.remplir)


class PageArticles(PageListe):
    titre = "Articles"
    colonnes = [("reference", "Réf.", 90, "w"), ("designation", "Désignation", 280, "w"), ("unite", "Unité", 70, "w"),
                ("prix_achat_f", "P.A. HT", 100, "e"), ("prix_vente_f", "P.V. HT", 100, "e"), ("stock", "Stock", 90, "e"),
                ("stock_minimum", "Alerte", 80, "e")]

    def rafraichir(self):
        def remplir(articles):
            for a in articles:
                a["prix_achat_f"], a["prix_vente_f"] = montant(a["prix_achat"]), montant(a["prix_vente"])
            self.tableau.remplir(articles, tags=lambda a: "alerte" if a["en_alerte"] else "")
        self.charger(lambda: self.api.articles(self.recherche.get()), remplir)


class PageDocuments(PageListe):
    colonnes = [("numero", "N°", 140, "w"), ("type_libelle", "Type", 170, "w"), ("date", "Date", 100, "w"),
                ("tiers_nom", "Tiers", 230, "w"), ("ht", "HT", 110, "e"), ("ttc", "TTC", 110, "e"),
                ("reste", "Reste dû", 110, "e"), ("statut", "Statut", 100, "w")]

    def __init__(self, app, domaine):
        self.domaine = domaine
        self.titre = "Ventes" if domaine == "ventes" else "Achats"
        super().__init__(app)
        self.bouton("Nouvelle facture", self.nouvelle_facture, fg_color="#1565c0")

    def rafraichir(self):
        def remplir(docs):
            for d in docs:
                d["ht"], d["ttc"] = montant(d["total_ht"]), montant(d["total_ttc"])
                d["reste"] = montant(d["reste_a_payer"]) if float(d["reste_a_payer"] or 0) else ""
                if d["numero"].startswith("BROU-"):
                    d["numero"] = "(brouillon)"
            self.tableau.remplir(docs)
        self.charger(lambda: self.api.documents(self.domaine, q=self.recherche.get()), remplir)

    def ouvrir(self, ligne):
        FenetreDocument(self, ligne["id"])

    def nouvelle_facture(self):
        FenetreSaisieFacture(self, "FACTURE" if self.domaine == "ventes" else "ACHAT_FACTURE")


class PageBalance(PageListe):
    titre = "Balance générale"
    colonnes = [("numero", "Compte", 90, "w"), ("intitule", "Intitulé", 280, "w"), ("mvt_d", "Mvt débit", 120, "e"),
                ("mvt_c", "Mvt crédit", 120, "e"), ("solde_d", "Solde débiteur", 120, "e"), ("solde_c", "Solde créditeur", 120, "e")]

    def rafraichir(self):
        def remplir(data):
            lignes = [{**l, **{k: montant(l[k]) if float(l[k]) else "" for k in ("mvt_d", "mvt_c", "solde_d", "solde_c")}}
                      for l in data["lignes"]]
            t = data["totaux"]
            lignes.append({"numero": "", "intitule": "TOTAUX", **{k: montant(t[k]) for k in ("mvt_d", "mvt_c", "solde_d", "solde_c")}, "_total": True})
            self.tableau.remplir(lignes, tags=lambda l: "total" if l.get("_total") else "")
        self.charger(self.api.balance, remplir)


class PageEtat(PageListe):
    """Bilan ou compte de résultat SYSCOHADA."""

    def __init__(self, app, etat):
        self.etat = etat
        self.titre = "Bilan SYSCOHADA" if etat == "bilan" else "Compte de résultat SYSCOHADA"
        self.colonnes = ([("ref", "Réf", 50, "w"), ("libelle", "Actif", 300, "w"), ("net", "Net", 130, "e"),
                          ("ref_p", "Réf", 50, "w"), ("libelle_p", "Passif", 300, "w"), ("montant_p", "Net", 130, "e")]
                         if etat == "bilan" else
                         [("ref", "Réf", 50, "w"), ("libelle", "Libellé", 420, "w"), ("montant", "Montant", 150, "e")])
        super().__init__(app)

    def rafraichir(self):
        if self.etat == "bilan":
            self.charger(self.api.bilan, self.afficher_bilan)
        else:
            def remplir(cr):
                self.tableau.remplir([{**l, "montant": montant(l["montant"])} for l in cr["lignes"]],
                                     tags=lambda l: "total" if l["total"] else "")
            self.charger(self.api.compte_resultat, remplir)

    def afficher_bilan(self, b):
        actif, passif = b["actif"], b["passif"]
        lignes = []
        for i in range(max(len(actif), len(passif))):
            a = actif[i] if i < len(actif) else {}
            p = passif[i] if i < len(passif) else {}
            lignes.append({"ref": a.get("ref", ""), "libelle": a.get("libelle", ""),
                           "net": montant(a["net"]) if a and float(a["net"]) else "",
                           "ref_p": p.get("ref", ""), "libelle_p": p.get("libelle", ""),
                           "montant_p": montant(p["montant"]) if p and float(p["montant"]) else "",
                           "_total": a.get("total") or p.get("total")})
        lignes.append({"ref": "BZ", "libelle": "TOTAL GÉNÉRAL", "net": montant(b["total_actif"]["net"]),
                       "ref_p": "DZ", "libelle_p": "TOTAL GÉNÉRAL", "montant_p": montant(b["total_passif"]), "_total": True})
        self.tableau.remplir(lignes, tags=lambda l: "total" if l["_total"] else "")


class PageBalanceAgee(PageListe):
    titre = "Balance âgée clients"
    colonnes = [("nom", "Client", 240, "w"), ("non_echu", "Non échu", 110, "e"), ("j30", "1-30 j", 110, "e"),
                ("j60", "31-60 j", 110, "e"), ("j90", "61-90 j", 110, "e"), ("plus", "> 90 j", 110, "e"), ("total", "Total", 120, "e")]

    def rafraichir(self):
        cles = ("non_echu", "j30", "j60", "j90", "plus", "total")

        def remplir(data):
            lignes = [{"nom": l["tiers"]["nom"], **{k: montant(l[k]) if float(l[k]) else "" for k in cles}} for l in data["lignes"]]
            lignes.append({"nom": "TOTAL", **{k: montant(data["totaux"][k]) for k in cles}, "_total": True})
            self.tableau.remplir(lignes, tags=lambda l: "total" if l.get("_total") else "")
        self.charger(self.api.balance_agee, remplir)


# ---------------------------------------------------------------------------
# Fenêtres
# ---------------------------------------------------------------------------
class FenetreDocument(ctk.CTkToplevel):
    def __init__(self, page, pk):
        super().__init__(page)
        self.page, self.api, self.pk = page, page.api, pk
        self.geometry("820x520")
        self.transient(page.winfo_toplevel())
        self.entete = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=18, weight="bold"), justify="left")
        self.entete.pack(anchor="w", padx=16, pady=(14, 4))
        self.infos = ctk.CTkLabel(self, text="", justify="left")
        self.infos.pack(anchor="w", padx=16)
        self.tableau = Tableau(self, [("designation", "Désignation", 300, "w"), ("quantite", "Qté", 80, "e"),
                                      ("pu", "P.U. HT", 110, "e"), ("taux_tva", "TVA %", 70, "e"), ("ht", "Montant HT", 120, "e")])
        self.tableau.pack(fill="both", expand=True, padx=16, pady=10)
        self.boutons = ctk.CTkFrame(self, fg_color="transparent")
        self.boutons.pack(fill="x", padx=16, pady=(0, 14))
        self.recharger()

    def recharger(self):
        try:
            d = self.api.document(self.pk)
        except ApiError as exc:
            messagebox.showerror("Erreur", str(exc), parent=self)
            return
        self.document = d
        numero = "(brouillon)" if d["numero"].startswith("BROU-") else d["numero"]
        self.title(f"{d['type_libelle']} {numero}")
        self.entete.configure(text=f"{d['type_libelle']} {numero} — {d['statut']}")
        self.infos.configure(text=f"Tiers : {d['tiers_nom']}    Date : {d['date']}    Échéance : {d['date_echeance'] or '—'}\n"
                                  f"Total HT : {montant(d['total_ht'])}    TVA : {montant(d['total_tva'])}    "
                                  f"TTC : {montant(d['total_ttc'])}    Reste dû : {montant(d['reste_a_payer'])}")
        self.tableau.remplir([{**l, "pu": montant(l["prix_unitaire"]), "ht": montant(l["montant_ht"])} for l in d["lignes"]])
        for w in self.boutons.winfo_children():
            w.destroy()
        if d["statut"] == "BROUILLON":
            ctk.CTkButton(self.boutons, text="Valider", fg_color="#2e7d32", command=self.valider).pack(side="left", padx=4)
        if d["statut"] == "VALIDE" and float(d["reste_a_payer"] or 0) > 0:
            ctk.CTkButton(self.boutons, text="Saisir un règlement", command=self.regler).pack(side="left", padx=4)
        ctk.CTkButton(self.boutons, text="Fermer", fg_color="gray", command=self.destroy).pack(side="right", padx=4)

    def valider(self):
        if not messagebox.askyesno("Validation", "Valider définitivement ce document ?", parent=self):
            return
        try:
            self.api.valider_document(self.pk)
        except ApiError as exc:
            messagebox.showerror("Erreur", str(exc), parent=self)
            return
        self.recharger()
        self.page.rafraichir()

    def regler(self):
        FenetreReglement(self, self.document)


class FenetreReglement(ctk.CTkToplevel):
    MODES = {"Espèces": ("ESPECES", "CA"), "Chèque": ("CHEQUE", "BQ"), "Virement": ("VIREMENT", "BQ"), "Mobile Money": ("MOBILE_MONEY", "MM")}

    def __init__(self, fenetre, document):
        super().__init__(fenetre)
        self.fenetre, self.api, self.document = fenetre, fenetre.api, document
        self.title("Règlement")
        self.geometry("380x300")
        self.transient(fenetre)
        try:
            self.journaux = {j["code"]: j["id"] for j in self.api.journaux()}
        except ApiError as exc:
            messagebox.showerror("Erreur", str(exc), parent=self)
            self.destroy()
            return
        ctk.CTkLabel(self, text=f"Facture {document['numero']} — {document['tiers_nom']}").pack(pady=(14, 8))
        self.mode = ctk.CTkOptionMenu(self, values=list(self.MODES))
        self.mode.pack(pady=4)
        self.montant = ctk.CTkEntry(self, placeholder_text="Montant")
        self.montant.insert(0, str(int(float(document["reste_a_payer"]))))
        self.montant.pack(pady=4)
        self.reference = ctk.CTkEntry(self, placeholder_text="Référence (chèque, transaction…)")
        self.reference.pack(pady=4)
        ctk.CTkButton(self, text="Enregistrer", command=self.enregistrer).pack(pady=14)

    def enregistrer(self):
        mode, journal = self.MODES[self.mode.get()]
        if journal not in self.journaux:
            messagebox.showerror("Erreur", f"Journal {journal} introuvable.", parent=self)
            return
        try:
            r = self.api.creer_reglement({"tiers": self.document["tiers"], "mode": mode, "journal": self.journaux[journal],
                                          "montant": float(self.montant.get().replace(" ", "").replace(",", ".")),
                                          "reference": self.reference.get(), "libelle": f"Règlement {self.document['numero']}"})
        except (ApiError, ValueError) as exc:
            messagebox.showerror("Erreur", str(exc), parent=self)
            return
        messagebox.showinfo("Règlement", f"Règlement {r['numero']} enregistré.", parent=self)
        self.destroy()
        self.fenetre.recharger()
        self.fenetre.page.rafraichir()


class FenetreSaisieFacture(ctk.CTkToplevel):
    def __init__(self, page, type_document):
        super().__init__(page)
        self.page, self.api, self.type_document = page, page.api, type_document
        est_vente = type_document == "FACTURE"
        self.title("Nouvelle facture " + ("client" if est_vente else "fournisseur"))
        self.geometry("860x560")
        self.transient(page.winfo_toplevel())
        try:
            self.tiers = {f"{t['code']} - {t['nom']}": t for t in self.api.tiers("CLIENT" if est_vente else "FOURNISSEUR") if t["actif"]}
            self.articles = {f"{a['reference']} - {a['designation']}": a for a in self.api.articles() if a["actif"]}
        except ApiError as exc:
            messagebox.showerror("Erreur", str(exc), parent=self)
            self.destroy()
            return
        self.cle_prix = "prix_vente" if est_vente else "prix_achat"
        self.lignes = []

        haut = ctk.CTkFrame(self, fg_color="transparent")
        haut.pack(fill="x", padx=16, pady=12)
        ctk.CTkLabel(haut, text="Client :" if est_vente else "Fournisseur :").pack(side="left")
        self.choix_tiers = ctk.CTkComboBox(haut, values=list(self.tiers) or [""], width=340)
        self.choix_tiers.pack(side="left", padx=8)

        saisie = ctk.CTkFrame(self)
        saisie.pack(fill="x", padx=16)
        self.choix_article = ctk.CTkComboBox(saisie, values=list(self.articles) or [""], width=320, command=self.article_choisi)
        self.choix_article.pack(side="left", padx=6, pady=8)
        self.qte = ctk.CTkEntry(saisie, width=70, placeholder_text="Qté")
        self.qte.pack(side="left", padx=4)
        self.prix = ctk.CTkEntry(saisie, width=100, placeholder_text="P.U. HT")
        self.prix.pack(side="left", padx=4)
        self.tva = ctk.CTkEntry(saisie, width=60, placeholder_text="TVA %")
        self.tva.pack(side="left", padx=4)
        ctk.CTkButton(saisie, text="Ajouter", width=80, command=self.ajouter).pack(side="left", padx=6)

        self.tableau = Tableau(self, [("designation", "Désignation", 320, "w"), ("quantite", "Qté", 70, "e"),
                                      ("pu", "P.U. HT", 110, "e"), ("taux_tva", "TVA %", 70, "e"), ("ht", "Montant HT", 120, "e")])
        self.tableau.pack(fill="both", expand=True, padx=16, pady=10)
        self.total = ctk.CTkLabel(self, text="", font=ctk.CTkFont(weight="bold"))
        self.total.pack(anchor="e", padx=20)
        bas = ctk.CTkFrame(self, fg_color="transparent")
        bas.pack(fill="x", padx=16, pady=12)
        ctk.CTkButton(bas, text="Retirer la ligne", fg_color="gray", command=self.retirer).pack(side="left")
        ctk.CTkButton(bas, text="Enregistrer et valider", fg_color="#2e7d32", command=lambda: self.enregistrer(True)).pack(side="right", padx=4)
        ctk.CTkButton(bas, text="Enregistrer en brouillon", command=lambda: self.enregistrer(False)).pack(side="right", padx=4)

    def article_choisi(self, cle):
        article = self.articles.get(cle)
        if not article:
            return
        for champ, valeur in ((self.qte, "1"), (self.prix, str(article[self.cle_prix])), (self.tva, str(article["taux_tva"]))):
            champ.delete(0, "end")
            champ.insert(0, valeur)

    def ajouter(self):
        article = self.articles.get(self.choix_article.get())
        try:
            qte = float(self.qte.get().replace(",", "."))
            prix = float(self.prix.get().replace(",", ".").replace(" ", ""))
            tva = float((self.tva.get() or str(TVA_DEFAUT)).replace(",", "."))
        except ValueError:
            messagebox.showwarning("Saisie", "Quantité, prix et TVA doivent être numériques.", parent=self)
            return
        if not article:
            messagebox.showwarning("Saisie", "Choisissez un article.", parent=self)
            return
        self.lignes.append({"article": article["id"], "designation": article["designation"], "quantite": qte,
                            "prix_unitaire": prix, "taux_tva": tva, "remise": 0})
        self.actualiser()

    def retirer(self):
        ligne = self.tableau.selection()
        if ligne:
            self.lignes.remove(ligne["_source"])
            self.actualiser()

    def actualiser(self):
        affichage, ht, tva = [], 0, 0
        for l in self.lignes:
            mht = round(l["quantite"] * l["prix_unitaire"])
            ht += mht
            tva += round(mht * l["taux_tva"] / 100)
            affichage.append({**l, "pu": montant(l["prix_unitaire"]), "ht": montant(mht), "_source": l})
        self.tableau.remplir(affichage)
        self.total.configure(text=f"Total HT : {montant(ht)}    TVA : {montant(tva)}    TTC : {montant(ht + tva)}")

    def enregistrer(self, valider):
        tiers = self.tiers.get(self.choix_tiers.get())
        if not tiers or not self.lignes:
            messagebox.showwarning("Saisie", "Choisissez un tiers et ajoutez au moins une ligne.", parent=self)
            return
        try:
            doc = self.api.creer_document({"type_document": self.type_document, "tiers": tiers["id"], "lignes": self.lignes})
            if valider:
                doc = self.api.valider_document(doc["id"])
        except ApiError as exc:
            messagebox.showerror("Erreur", str(exc), parent=self)
            return
        messagebox.showinfo("Facture", f"Facture {doc['numero'] if valider else '(brouillon)'} enregistrée.", parent=self)
        self.destroy()
        self.page.rafraichir()


class FenetreConnexion(ctk.CTkToplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Connexion")
        self.geometry("360x320")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", app.destroy)
        ctk.CTkLabel(self, text="ERP OHADA", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 10))
        self.serveur = ctk.CTkEntry(self, width=280, placeholder_text="Adresse du serveur")
        self.serveur.insert(0, app.config_data.get("serveur", ""))
        self.serveur.pack(pady=5)
        self.utilisateur = ctk.CTkEntry(self, width=280, placeholder_text="Utilisateur")
        self.utilisateur.insert(0, app.config_data.get("utilisateur", ""))
        self.utilisateur.pack(pady=5)
        self.mdp = ctk.CTkEntry(self, width=280, placeholder_text="Mot de passe", show="•")
        self.mdp.pack(pady=5)
        self.mdp.bind("<Return>", lambda e: self.connecter())
        ctk.CTkButton(self, text="Se connecter", width=280, command=self.connecter).pack(pady=15)
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
# Application
# ---------------------------------------------------------------------------
class Application(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")
        self.title("ERP OHADA — Gestion commerciale · Comptabilité · Reporting")
        self.geometry("1280x760")
        self.minsize(1000, 600)
        self.config_data = charger_config()
        self.api = None
        self.pages = {}

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        self.menu = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#1e2a3a")
        self.menu.pack(side="left", fill="y")
        self.contenu = ctk.CTkFrame(self, fg_color="transparent")
        self.contenu.pack(side="left", fill="both", expand=True, padx=16, pady=16)
        self.barre_statut = ctk.CTkLabel(self, text="", anchor="w")

        token = self.config_data.get("token")
        if token:
            api = ErpApi(self.config_data["serveur"], token)
            try:
                api.get("journaux/")
                self.after(10, lambda: self.demarrer(api))
                return
            except ApiError:
                pass
        self.withdraw()
        self.after(10, lambda: FenetreConnexion(self))

    def statut(self, texte):
        self.title("ERP OHADA" + (f" — {texte}" if texte else " — Gestion commerciale · Comptabilité · Reporting"))

    def demarrer(self, api):
        self.api = api
        self.deiconify()
        ctk.CTkLabel(self.menu, text="ERP OHADA", text_color="white", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(18, 4), padx=16, anchor="w")
        ctk.CTkLabel(self.menu, text=api.base_url, text_color="#7f8fa4", font=ctk.CTkFont(size=11)).pack(padx=16, anchor="w")
        sections = [
            ("REPORTING", [("Tableau de bord", lambda: PageDashboard(self)), ("Balance âgée", lambda: PageBalanceAgee(self))]),
            ("COMMERCIAL", [("Ventes", lambda: PageDocuments(self, "ventes")), ("Achats", lambda: PageDocuments(self, "achats")),
                            ("Clients", lambda: PageTiers(self, "CLIENT")), ("Fournisseurs", lambda: PageTiers(self, "FOURNISSEUR")),
                            ("Articles", lambda: PageArticles(self))]),
            ("COMPTABILITÉ", [("Balance", lambda: PageBalance(self)), ("Bilan", lambda: PageEtat(self, "bilan")),
                              ("Compte de résultat", lambda: PageEtat(self, "resultat"))]),
        ]
        for titre, entrees in sections:
            ctk.CTkLabel(self.menu, text=titre, text_color="#7f8fa4", font=ctk.CTkFont(size=11)).pack(padx=16, pady=(16, 2), anchor="w")
            for libelle, fabrique in entrees:
                ctk.CTkButton(self.menu, text=libelle, anchor="w", fg_color="transparent", hover_color="#2c3e55",
                              text_color="#c8d1dc", command=lambda l=libelle, f=fabrique: self.afficher(l, f)).pack(fill="x", padx=8)
        ctk.CTkButton(self.menu, text="Déconnexion", fg_color="transparent", border_width=1, command=self.deconnecter).pack(side="bottom", fill="x", padx=12, pady=16)
        self.afficher("Tableau de bord", lambda: PageDashboard(self))

    def afficher(self, nom, fabrique):
        for page in self.pages.values():
            page.pack_forget()
        if nom not in self.pages:
            self.pages[nom] = fabrique()
        self.pages[nom].pack(fill="both", expand=True)
        self.pages[nom].rafraichir()

    def deconnecter(self):
        self.config_data.pop("token", None)
        sauver_config(self.config_data)
        self.destroy()


if __name__ == "__main__":
    Application().mainloop()
