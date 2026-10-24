"""Écrans natifs du client bureau et correspondance avec les éléments de navigation."""
from tkinter import messagebox

import customtkinter as ctk

from api_client import ApiError
from shell import Page, PageListe, Tableau, assombrir, montant

TVA_DEFAUT = 19.25


# ---------------------------------------------------------------------------
# Écrans
# ---------------------------------------------------------------------------
class PageDashboard(Page):
    def __init__(self, app, titre):
        super().__init__(app, titre)
        self.bouton("Actualiser", self.rafraichir)
        grille = ctk.CTkFrame(self, fg_color="transparent")
        grille.pack(fill="x")
        self.kpis = {}
        indicateurs = [
            ("ca_exercice", "CA HT exercice"), ("marge_commerciale", "Marge commerciale"),
            ("resultat", "Résultat net"), ("tresorerie", "Trésorerie nette"),
            ("creances_clients", "Créances clients"), ("dettes_fournisseurs", "Dettes fournisseurs"),
            ("valeur_stock", "Valeur du stock"), ("ca_mois", "CA du mois"),
        ]
        for i, (cle, libelle) in enumerate(indicateurs):
            carte = ctk.CTkFrame(grille, corner_radius=10, fg_color="white")
            carte.grid(row=i // 4, column=i % 4, padx=6, pady=6, sticky="nsew")
            grille.grid_columnconfigure(i % 4, weight=1)
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

    def __init__(self, app, titre, type_tiers):
        self.type_tiers = type_tiers
        super().__init__(app, titre)

    def rafraichir(self):
        self.charger(lambda: self.api.tiers(self.type_tiers, self.recherche.get()), self.tableau.remplir)


class PageArticles(PageListe):
    colonnes = [("reference", "Réf.", 90, "w"), ("designation", "Désignation", 260, "w"), ("unite", "Unité", 70, "w"),
                ("prix_achat_f", "P.A. HT", 95, "e"), ("prix_vente_f", "P.V. HT", 95, "e"), ("stock", "Stock", 85, "e"),
                ("stock_minimum", "Alerte", 75, "e"), ("cmup_f", "CMUP", 90, "e"), ("valeur_f", "Valeur", 110, "e")]

    def __init__(self, app, titre, alerte_seulement=False):
        self.alerte_seulement = alerte_seulement
        super().__init__(app, titre)

    def rafraichir(self):
        def remplir(articles):
            if self.alerte_seulement:
                articles = [a for a in articles if a["en_alerte"]]
            for a in articles:
                a["prix_achat_f"], a["prix_vente_f"] = montant(a["prix_achat"]), montant(a["prix_vente"])
                a["cmup_f"], a["valeur_f"] = montant(a["cmup"]), montant(a["valeur_stock"])
            self.tableau.remplir(articles, tags=lambda a: "alerte" if a["en_alerte"] else "")
        self.charger(lambda: self.api.articles(self.recherche.get()), remplir)


class PageDocuments(PageListe):
    colonnes = [("numero", "N°", 140, "w"), ("type_libelle", "Type", 170, "w"), ("date", "Date", 100, "w"),
                ("tiers_nom", "Tiers", 210, "w"), ("depot_nom", "Dépôt", 140, "w"), ("ht", "HT", 110, "e"), ("ttc", "TTC", 110, "e"),
                ("reste", "Reste dû", 110, "e"), ("statut", "Statut", 100, "w")]

    def __init__(self, app, titre, domaine, type_document="", statut=""):
        self.domaine, self.type_document, self.filtre_statut = domaine, type_document, statut
        super().__init__(app, titre)
        if domaine != "stocks":
            self.bouton("Nouvelle facture", self.nouvelle_facture)

    def rafraichir(self):
        def remplir(docs):
            if self.filtre_statut:
                docs = [d for d in docs if d["statut"] == self.filtre_statut]
            for d in docs:
                d["ht"], d["ttc"] = montant(d["total_ht"]), montant(d["total_ttc"])
                d["reste"] = montant(d["reste_a_payer"]) if float(d["reste_a_payer"] or 0) else ""
                if d["numero"].startswith("BROU-"):
                    d["numero"] = "(brouillon)"
            self.tableau.remplir(docs)
        self.charger(lambda: self.api.documents(self.domaine, self.type_document, self.recherche.get()), remplir)

    def ouvrir(self, ligne):
        FenetreDocument(self, ligne["id"])

    def nouvelle_facture(self):
        FenetreSaisieFacture(self, "FACTURE" if self.domaine == "ventes" else "ACHAT_FACTURE")


class PageBalance(PageListe):
    colonnes = [("numero", "Compte", 90, "w"), ("intitule", "Intitulé", 280, "w"), ("mvt_d", "Mvt débit", 120, "e"),
                ("mvt_c", "Mvt crédit", 120, "e"), ("solde_d", "Solde débiteur", 120, "e"), ("solde_c", "Solde créditeur", 120, "e")]

    def __init__(self, app, titre, compte_debut="", compte_fin=""):
        self.compte_debut, self.compte_fin = compte_debut, compte_fin
        super().__init__(app, titre)

    def rafraichir(self):
        cles = ("mvt_d", "mvt_c", "solde_d", "solde_c")

        def remplir(data):
            lignes = [{**l, **{k: montant(l[k]) if float(l[k]) else "" for k in cles}} for l in data["lignes"]]
            t = data["totaux"]
            lignes.append({"numero": "", "intitule": "TOTAUX", **{k: montant(t[k]) for k in cles}, "_total": True})
            self.tableau.remplir(lignes, tags=lambda l: "total" if l.get("_total") else "")
        self.charger(lambda: self.api.balance(compte_debut=self.compte_debut, compte_fin=self.compte_fin), remplir)


class PageBilan(PageListe):
    colonnes = [("ref", "Réf", 50, "w"), ("libelle", "Actif", 300, "w"), ("net", "Net", 130, "e"),
                ("ref_p", "Réf", 50, "w"), ("libelle_p", "Passif", 300, "w"), ("montant_p", "Net", 130, "e")]

    def rafraichir(self):
        self.charger(self.api.bilan, self.afficher)

    def afficher(self, b):
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


class PageCompteResultat(PageListe):
    colonnes = [("ref", "Réf", 50, "w"), ("libelle", "Libellé", 420, "w"), ("montant", "Montant", 150, "e")]

    def rafraichir(self):
        def remplir(cr):
            self.tableau.remplir([{**l, "montant": montant(l["montant"])} for l in cr["lignes"]],
                                 tags=lambda l: "total" if l["total"] else "")
        self.charger(self.api.compte_resultat, remplir)


class PageBalanceAgee(PageListe):
    colonnes = [("nom", "Tiers", 240, "w"), ("non_echu", "Non échu", 110, "e"), ("j30", "1-30 j", 110, "e"),
                ("j60", "31-60 j", 110, "e"), ("j90", "61-90 j", 110, "e"), ("plus", "> 90 j", 110, "e"), ("total", "Total", 120, "e")]

    def __init__(self, app, titre, type_tiers):
        self.type_tiers = type_tiers
        super().__init__(app, titre)

    def rafraichir(self):
        cles = ("non_echu", "j30", "j60", "j90", "plus", "total")

        def remplir(data):
            # Intitulés des tranches renvoyés par le serveur (délais et « d'après la date d' » de la sélection)
            titres = dict(data.get("tranches", []))
            for cle in cles[:-1]:
                self.tableau.tree.heading(cle, text=titres.get(cle, ""))
            self.tableau.colonnes = [(c, titres.get(c, t), l, a) if c in titres else (c, t, l, a) for c, t, l, a in self.tableau.colonnes]
            lignes = [{"nom": l["tiers"]["nom"], **{k: montant(l[k]) if float(l[k]) else "" for k in cles}} for l in data["lignes"]]
            lignes.append({"nom": "TOTAL", **{k: montant(data["totaux"][k]) for k in cles}, "_total": True})
            self.tableau.remplir(lignes, tags=lambda l: "total" if l.get("_total") else "")
        self.charger(lambda: self.api.balance_agee(self.type_tiers), remplir)


# ---------------------------------------------------------------------------
# Fenêtres
# ---------------------------------------------------------------------------
def _bouton(parent, app, texte, commande, **kwargs):
    kwargs.setdefault("fg_color", app.couleur)
    kwargs.setdefault("hover_color", assombrir(app.couleur))
    return ctk.CTkButton(parent, text=texte, command=commande, **kwargs)


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
        app = self.page.app
        if d["statut"] == "BROUILLON":
            _bouton(self.boutons, app, "Valider", self.valider, fg_color="#2e7d32", hover_color="#1b5e20").pack(side="left", padx=4)
        if d["statut"] == "VALIDE" and float(d["reste_a_payer"] or 0) > 0:
            _bouton(self.boutons, app, "Saisir un règlement", self.regler).pack(side="left", padx=4)
        ctk.CTkButton(self.boutons, text="Fermer", fg_color="gray", command=self.destroy).pack(side="right", padx=4)

    def valider(self):
        if not messagebox.askyesno("Validation", "Valider définitivement ce document ?", parent=self):
            return
        try:
            resultat = self.api.valider_document(self.pk)
        except ApiError as exc:
            messagebox.showerror("Erreur", str(exc), parent=self)
            return
        if resultat.get("avertissement"):
            messagebox.showwarning("Encours client", resultat["avertissement"], parent=self)
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
        _bouton(self, fenetre.page.app, "Enregistrer", self.enregistrer).pack(pady=14)

    def enregistrer(self):
        mode, journal = self.MODES[self.mode.get()]
        if journal not in self.journaux:
            messagebox.showerror("Erreur", f"Journal {journal} introuvable.", parent=self)
            return
        try:
            r = self.api.creer_reglement({"tiers": self.document.get("payeur") or self.document["tiers"], "facture": self.document["id"],
                                          "mode": mode, "journal": self.journaux[journal],
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
        app = page.app

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
        _bouton(saisie, app, "Ajouter", self.ajouter, width=80).pack(side="left", padx=6)

        self.tableau = Tableau(self, [("designation", "Désignation", 320, "w"), ("quantite", "Qté", 70, "e"),
                                      ("pu", "P.U. HT", 110, "e"), ("taux_tva", "TVA %", 70, "e"), ("ht", "Montant HT", 120, "e")])
        self.tableau.pack(fill="both", expand=True, padx=16, pady=10)
        self.total = ctk.CTkLabel(self, text="", font=ctk.CTkFont(weight="bold"))
        self.total.pack(anchor="e", padx=20)
        bas = ctk.CTkFrame(self, fg_color="transparent")
        bas.pack(fill="x", padx=16, pady=12)
        ctk.CTkButton(bas, text="Retirer la ligne", fg_color="gray", command=self.retirer).pack(side="left")
        _bouton(bas, app, "Enregistrer et valider", lambda: self.enregistrer(True), fg_color="#2e7d32", hover_color="#1b5e20").pack(side="right", padx=4)
        _bouton(bas, app, "Enregistrer en brouillon", lambda: self.enregistrer(False)).pack(side="right", padx=4)

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


# ---------------------------------------------------------------------------
# Correspondance élément de navigation → écran natif
# ---------------------------------------------------------------------------
TYPES_VENTE = ["DEVIS", "COMMANDE", "PREPARATION", "LIVRAISON", "RETOUR", "AVOIR_FINANCIER", "FACTURE", "FACTURE_RETOUR", "AVOIR"]
TYPES_ACHAT = ["ACHAT_DEMANDE", "ACHAT_PREPARATION", "ACHAT_COMMANDE", "ACHAT_RECEPTION", "ACHAT_RETOUR",
               "ACHAT_AVOIR_FINANCIER", "ACHAT_FACTURE", "ACHAT_FACTURE_RETOUR", "ACHAT_AVOIR"]
TYPES_STOCK = ["STOCK_ENTREE", "STOCK_SORTIE", "STOCK_VIREMENT"]

ECRANS_COMMERCIAL = {
    "tiers.clients": lambda app, el: PageTiers(app, el["titre"], "CLIENT"),
    "tiers.fournisseurs": lambda app, el: PageTiers(app, el["titre"], "FOURNISSEUR"),
    "comptes.clients": lambda app, el: PageTiers(app, el["titre"], "CLIENT"),
    "comptes.fournisseurs": lambda app, el: PageTiers(app, el["titre"], "FOURNISSEUR"),
    "articles.liste": lambda app, el: PageArticles(app, el["titre"]),
    "comptes.articles": lambda app, el: PageArticles(app, el["titre"]),
    "ventes.tous": lambda app, el: PageDocuments(app, el["titre"], "ventes"),
    "achats.tous": lambda app, el: PageDocuments(app, el["titre"], "achats"),
    "stocks.tous": lambda app, el: PageDocuments(app, el["titre"], "stocks"),
    "etats.echeances.clients": lambda app, el: PageBalanceAgee(app, "Relevé d'échéances clients", "CLIENT"),
    "etats.echeances.fournisseurs": lambda app, el: PageBalanceAgee(app, "Relevé d'échéances fournisseurs", "FOURNISSEUR"),
}
for _domaine, _types in (("ventes", TYPES_VENTE), ("achats", TYPES_ACHAT), ("stocks", TYPES_STOCK)):
    for _type in _types:
        ECRANS_COMMERCIAL[f"{_domaine}.{_type.lower()}"] = (
            lambda app, el, d=_domaine, t=_type: PageDocuments(app, el["titre"], d, t))

ECRANS_COMPTABILITE = {
    "etats.balance.generale": lambda app, el: PageBalance(app, el["titre"]),
    "etats.balance.tiers": lambda app, el: PageBalance(app, el["titre"], "4", "4"),
    "etats.financiers.bilan": lambda app, el: PageBilan(app, el["titre"]),
    "etats.financiers.resultat": lambda app, el: PageCompteResultat(app, el["titre"]),
}

ECRANS_REPORTING = {
    "synthese.dashboard": lambda app, el: PageDashboard(app, el["titre"]),
    "tiers.balance_agee_clients": lambda app, el: PageBalanceAgee(app, "Balance âgée clients", "CLIENT"),
    "tiers.balance_agee_fournisseurs": lambda app, el: PageBalanceAgee(app, "Balance âgée fournisseurs", "FOURNISSEUR"),
    "finances.bilan": lambda app, el: PageBilan(app, el["titre"]),
    "finances.resultat": lambda app, el: PageCompteResultat(app, el["titre"]),
}
