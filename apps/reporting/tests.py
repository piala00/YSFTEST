from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.commercial.models import Article, Document, Reglement, Tiers
from apps.comptabilite.models import Ecriture


class PagesEtApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--demo", verbosity=0)
        cls.user = get_user_model().objects.create_superuser("test", "", "pwd")

    def setUp(self):
        self.client.force_login(self.user)

    def test_toutes_les_pages_repondent(self):
        doc = Document.objects.filter(type_document=Document.FACTURE).first()
        urls = [
            reverse("reporting:dashboard"), reverse("reporting:ventes"), reverse("reporting:balance_agee"),
            reverse("reporting:balance_agee") + "?type=FOURNISSEUR",
            reverse("commercial:clients"), reverse("commercial:fournisseurs"), reverse("commercial:articles"),
            reverse("commercial:stock"), reverse("commercial:familles"), reverse("commercial:reglements"),
            reverse("commercial:documents", args=["ventes"]), reverse("commercial:documents", args=["achats"]),
            reverse("commercial:document_create", args=["FACTURE"]), reverse("commercial:document_create", args=["ACHAT_COMMANDE"]),
            reverse("commercial:document_detail", args=[doc.pk]), reverse("commercial:document_print", args=[doc.pk]),
            reverse("commercial:tiers_detail", args=[doc.tiers_id]), reverse("commercial:tiers_create"),
            reverse("commercial:article_detail", args=[Article.objects.first().pk]), reverse("commercial:article_create"),
            reverse("commercial:reglement_create"), reverse("commercial:reglement_create") + f"?document={doc.pk}",
            reverse("commercial:reglement_detail", args=[Reglement.objects.first().pk]),
            reverse("comptabilite:comptes"), reverse("comptabilite:journaux"), reverse("comptabilite:ecritures"),
            reverse("comptabilite:ecriture_create"), reverse("comptabilite:ecriture_detail", args=[Ecriture.objects.first().pk]),
            reverse("comptabilite:journal"), reverse("comptabilite:grand_livre"), reverse("comptabilite:balance"),
            reverse("comptabilite:bilan"), reverse("comptabilite:compte_resultat"), reverse("comptabilite:tva"),
            reverse("comptabilite:lettrage") + "?compte=" + str(doc.ecriture.lignes.first().compte_id),
            reverse("commercial:societe"), reverse("comptabilite:exercices"), reverse("comptabilite:exercice_create"),
            reverse("core:portail"), reverse("commercial:accueil"), reverse("comptabilite:accueil"),
            reverse("commercial:mouvements"), reverse("commercial:etat_ventes") + "?vue=clients",
            reverse("commercial:etat_balance_agee") + "?type=CLIENT", reverse("reporting:bilan"), reverse("reporting:compte_resultat"),
            reverse("reporting:ventes") + "?vue=mois", reverse("commercial:documents", args=["ventes"]) + "?impayees=1",
            reverse("commercial:reglements") + "?sens=E",
            reverse("comptabilite:balance") + "?export=csv", reverse("comptabilite:grand_livre") + "?export=csv",
            reverse("reporting:ventes") + "?export=clients", reverse("reporting:ventes") + "?export=articles",
        ]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_tous_les_elements_de_navigation(self):
        """Chaque commande de chaque menu de chaque logiciel mène à une page valide."""
        from apps.core.navigation import MODULES, structure_module

        def parcourir(noeuds):
            for n in noeuds:
                if n["url"]:
                    yield n
                yield from parcourir(n["enfants"])

        total = 0
        for module in MODULES:
            onglets, _ = structure_module(module)
            for onglet in onglets:
                for noeud in parcourir(onglet["elements"]):
                    with self.subTest(module=module.code, element=noeud["code"]):
                        response = self.client.get(noeud["url"])
                        self.assertEqual(response.status_code, 200)
                        if noeud["module"] or noeud["code"].startswith("fenetre."):
                            continue  # commande qui ouvre un autre logiciel (ou l'administration)
                        # La page met en évidence le bon logiciel, le bon menu et la bonne commande
                        self.assertEqual(response.context["module"].code, module.code)
                        self.assertEqual(response.context["onglet_actif"]["code"], onglet["code"])
                        self.assertEqual(response.context["element_actif"]["code"], noeud["code"])
                    total += 1
        self.assertGreater(total, 80)

    def test_menus_comme_sage(self):
        from apps.core.navigation import MODULES_PAR_CODE as M

        attendu = ["Fichier", "Édition", "Structure", "Traitement", "Etat", "Fenêtre", "?"]
        for code in ("commercial", "comptabilite", "analytique"):
            self.assertEqual([o.titre for o in M[code].onglets], attendu)
        self.assertEqual([o.titre for o in M["reporting"].onglets], ["Fichier", "Édition", "Etat", "Fenêtre", "?"])

    def test_preuves_et_matrice_d_audit(self):
        import io

        from django.core.management import call_command

        from apps.core.navigation import PREUVES, GESTION_COMMERCIALE, structure_module

        def parcourir(noeuds):
            for n in noeuds:
                if not n["separateur"]:
                    yield n
                    yield from parcourir(n["enfants"])

        onglets, _ = structure_module(GESTION_COMMERCIALE)
        for n in (n for o in onglets for n in parcourir(o["elements"])):
            self.assertIn(n["preuve"], PREUVES, n["code"])
        edition = next(o for o in onglets if o["code"] == "edition")
        self.assertTrue(all(n["preuve"] == "ERG-CLASSIQUE" for n in parcourir(edition["elements"])))
        sortie = io.StringIO()
        call_command("audit_navigation", stdout=sortie)
        self.assertIn("| Traitement › Documents des ventes | Facture d'avoir | DOC-V12 | ✅ Réalisé |", sortie.getvalue())

    def test_etats_statistiques_coherents(self):
        import datetime

        from apps.reporting import services, statistiques

        debut, fin = datetime.date(2026, 1, 1), datetime.date(2026, 12, 31)
        ca = services.chiffre_affaires(debut, fin)
        for code in ("palmares_clients", "activite_clients", "rentabilite_clients", "ventes_familles", "palmares_ventes"):
            etat = statistiques.calculer(code, debut, fin)
            cle = {"palmares_clients": "montant", "activite_clients": "total", "rentabilite_clients": "ca",
                   "ventes_familles": "montant", "palmares_ventes": "montant"}[code]
            self.assertEqual(etat["totaux"][cle], ca, code)
        rentabilite = statistiques.calculer("rentabilite_clients", debut, fin)
        for ligne in rentabilite["lignes"]:
            self.assertEqual(ligne["marge"], ligne["ca"] - ligne["cout"])
        palmares = statistiques.calculer("palmares_clients", debut, fin)["lignes"]
        self.assertEqual([l["rang"] for l in palmares], list(range(1, len(palmares) + 1)))
        self.assertAlmostEqual(float(palmares[-1]["cumul"]), 100.0)
        # Cadencier clients : colonnes par mois + total ; sur chaque article, total = somme des mois
        cad = statistiques.calculer("cadencier_clients", debut, fin)
        mois = [c[0] for c in cad["colonnes"] if c[0].startswith("m2")]
        self.assertEqual(len(mois), 12)                           # 12 colonnes mensuelles sur l'année
        self.assertEqual(cad["colonnes"][-1][0], "total")
        for ligne in cad["lignes"]:
            self.assertEqual(ligne["total"], sum(ligne[m] for m in mois))
        # La quantité totale du cadencier = quantité des ventes par article sur la même période
        total_articles = sum((l["quantite"] for l in statistiques.calculer("ventes_articles", debut, fin)["lignes"]), 0)
        self.assertEqual(cad["totaux"]["total"], total_articles)
        for code in statistiques.ETATS:
            with self.subTest(etat=code):
                self.assertEqual(self.client.get(reverse("commercial:statistique", args=[code])).status_code, 200)
                self.assertEqual(self.client.get(reverse("commercial:statistique", args=[code]) + "?export=csv").status_code, 200)
        self.assertEqual(self.client.get(reverse("commercial:statistique", args=["inexistant"])).status_code, 404)

    def test_rotation_des_stocks_et_avoirs(self):
        import datetime

        from django.db.models import Sum

        from apps.commercial.models import MouvementStock
        from apps.reporting import statistiques

        debut, fin = datetime.date(2026, 1, 1), datetime.date(2026, 12, 31)
        rotation = statistiques.calculer("rotation_stocks", debut, fin)
        self.assertTrue(rotation["lignes"])
        for l in rotation["lignes"]:
            self.assertEqual(l["fin_stock"], l["debut"] + l["entrees"] - l["sorties"])
            reel = (MouvementStock.objects.filter(article__reference=l["reference"], date__lte=fin)
                    .exclude(document__type_document=Document.STOCK_VIREMENT).aggregate(q=Sum("quantite"))["q"])
            self.assertEqual(l["fin_stock"], reel, l["reference"])
            if l["fin_stock"] <= 0:
                self.assertEqual(l["alerte"], "Rupture")

        from apps.commercial.models import Reglement

        modes = statistiques.calculer("reglements_modes", debut, fin)
        encaisse = sum(r.montant for r in Reglement.objects.filter(date__gte=debut, date__lte=fin) if r.est_encaissement)
        self.assertEqual(modes["totaux"]["encaisse"], encaisse)
        self.assertEqual(sum(l["nb"] for l in modes["lignes"]), Reglement.objects.filter(date__gte=debut, date__lte=fin).count())

        facture = Document.objects.filter(type_document=Document.FACTURE, statut=Document.VALIDE, date__gte=debut).first()
        avoir = facture.transformer(Document.AVOIR, self.user)
        avoir.valider()
        etat = statistiques.calculer("avoirs_retours", debut, fin)
        ligne = next(l for l in etat["lignes"] if l["numero"] == avoir.numero_affiche)
        self.assertEqual((ligne["origine"], ligne["ht"]), (facture.numero, avoir.total_ht))
        self.assertGreater(ligne["part"], 0)

    def test_saisie_facture_par_formulaire(self):
        tiers = Tiers.objects.filter(type_tiers=Tiers.CLIENT).first()
        article = Article.objects.first()
        data = {
            "tiers": tiers.pk, "date": "2026-03-01", "date_echeance": "", "reference_externe": "", "notes": "",
            "lignes-TOTAL_FORMS": "1", "lignes-INITIAL_FORMS": "0", "lignes-MIN_NUM_FORMS": "1", "lignes-MAX_NUM_FORMS": "1000",
            "lignes-0-article": article.pk, "lignes-0-designation": "", "lignes-0-quantite": "2",
            "lignes-0-prix_unitaire": "1000", "lignes-0-remise": "0", "lignes-0-taux_tva": "19.25", "valider": "1",
        }
        response = self.client.post(reverse("commercial:document_create", args=["FACTURE"]), data)
        self.assertEqual(response.status_code, 302)
        doc = Document.objects.latest("id")
        self.assertEqual(doc.statut, Document.VALIDE)
        self.assertEqual(doc.total_ttc, 2385)

    def test_documents_des_stocks_et_inventaire_par_le_web(self):
        from apps.commercial.models import Depot, Inventaire, StockDepot

        article = Article.objects.get(reference="CIM50")
        principal, abong = Depot.objects.get(code="DP"), Depot.objects.get(code="AM")
        avant = StockDepot.quantite_de(article.pk, abong.pk)
        data = {
            "date": "2026-03-01", "depot": principal.pk, "depot_destination": abong.pk, "reference_externe": "", "notes": "",
            "lignes-TOTAL_FORMS": "1", "lignes-INITIAL_FORMS": "0", "lignes-MIN_NUM_FORMS": "1", "lignes-MAX_NUM_FORMS": "1000",
            "lignes-0-article": article.pk, "lignes-0-designation": "", "lignes-0-quantite": "10",
            "lignes-0-prix_unitaire": "0", "lignes-0-remise": "0", "lignes-0-taux_tva": "0", "valider": "1",
        }
        response = self.client.post(reverse("commercial:document_create", args=["STOCK_VIREMENT"]), data)
        self.assertEqual(response.status_code, 302)
        doc = Document.objects.latest("id")
        self.assertEqual((doc.type_document, doc.statut), ("STOCK_VIREMENT", "VALIDE"))
        self.assertEqual(StockDepot.quantite_de(article.pk, abong.pk), avant + 10)
        # Transfert vers le même dépôt : refusé par le formulaire
        data["depot_destination"] = principal.pk
        response = self.client.post(reverse("commercial:document_create", args=["STOCK_VIREMENT"]), data)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse("commercial:inventaire_create"), {"date": "2026-03-02", "depot": abong.pk, "notes": ""})
        inventaire = Inventaire.objects.latest("id")
        self.assertRedirects(response, reverse("commercial:inventaire_detail", args=[inventaire.pk]))
        lignes = list(inventaire.lignes.all())
        donnees = {"form-TOTAL_FORMS": len(lignes), "form-INITIAL_FORMS": len(lignes), "valider": "1"}
        for i, l in enumerate(lignes):
            donnees[f"form-{i}-id"] = l.pk
            donnees[f"form-{i}-stock_reel"] = str(l.stock_theorique - 1 if l.article_id == article.pk else l.stock_theorique)
        self.client.post(reverse("commercial:inventaire_detail", args=[inventaire.pk]), donnees)
        inventaire.refresh_from_db()
        self.assertEqual(inventaire.statut, "VALIDE")
        self.assertEqual(StockDepot.quantite_de(article.pk, abong.pk), avant + 9)

        for url in (reverse("commercial:inventaire_detail", args=[inventaire.pk]), reverse("commercial:inventaires"),
                    reverse("commercial:depots"), reverse("commercial:depot_create"),
                    reverse("commercial:stock") + f"?depot={abong.pk}", reverse("commercial:mouvements") + f"?depot={abong.pk}",
                    reverse("commercial:recherche_entetes") + "?domaine=stocks&tiers=&numero=",
                    reverse("commercial:recherche_lignes") + "?article=ciment&domaine=ventes",
                    reverse("commercial:etat_inventaire") + f"?vue=livre&date=2026-06-30&depot={principal.pk}",
                    reverse("commercial:document_detail", args=[doc.pk]), reverse("commercial:document_print", args=[doc.pk]),
                    reverse("commercial:documents", args=["stocks"]), reverse("commercial:clients") + "?vue=comptes"):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_connexion_requise(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse("reporting:dashboard")).status_code, 302)

    def test_api(self):
        api = APIClient()
        token = api.post("/api/token/", {"username": "test", "password": "pwd"}).json()["token"]
        self.assertEqual(token, Token.objects.get(user=self.user).key)
        api.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        for url in ("/api/tiers/", "/api/articles/", "/api/documents/?domaine=ventes", "/api/reglements/",
                    "/api/comptes/", "/api/journaux/", "/api/ecritures/", "/api/reporting/dashboard/",
                    "/api/reporting/balance/", "/api/reporting/bilan/", "/api/reporting/compte-resultat/",
                    "/api/reporting/balance-agee/", "/api/navigation/", "/api/navigation/?module=comptabilite"):
            with self.subTest(url=url):
                self.assertEqual(api.get(url).status_code, 200)

        tiers = Tiers.objects.filter(type_tiers=Tiers.CLIENT).first()
        article = Article.objects.first()
        r = api.post("/api/documents/", {
            "type_document": "FACTURE", "tiers": tiers.pk, "date": "2026-04-01",
            "lignes": [{"article": article.pk, "designation": "x", "quantite": 1, "prix_unitaire": 1000, "taux_tva": 19.25}],
        }, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        r = api.post(f"/api/documents/{r.json()['id']}/valider/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["statut"], "VALIDE")
        self.assertEqual(APIClient().get("/api/tiers/").status_code, 401)


class MenusDuTransportTests(TestCase):
    """Le logiciel de transport a son plan tiers (partenaires, pas de clients), son plan analytique (10 axes) et son
    reporting ; chaque commande de ses menus mène à une page valide."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", "--demo", verbosity=0)
        cls.user = get_user_model().objects.create_superuser("test", "", "pwd")

    def setUp(self):
        self.client.force_login(self.user)

    def test_menus_propres_au_transport(self):
        from apps.core.navigation import MODULES_PAR_CODE as M, structure_module

        def codes(module):
            def tous(noeuds):
                for n in noeuds:
                    yield n["code"]
                    yield from tous(n["enfants"])
            return {c for o in structure_module(M[module])[0] for c in tous(o["elements"])}
        compta, analytique, reporting = codes("comptabilite"), codes("analytique"), codes("reporting")
        self.assertIn("structure.plan_tiers.partenaires", compta)
        self.assertNotIn("structure.plan_tiers.clients", compta)
        self.assertIn("structure.plan_analytique_transport", compta)
        self.assertNotIn("structure.plan_analytique", compta)
        self.assertIn("structure.plan_transport.agences", analytique)
        self.assertIn("analytique.vehicules", analytique)
        for code in ("transport.tableau_de_bord", "transport.recettes.billetterie", "transport.recettes.colis",
                     "transport.rentabilite.vehicules", "transport.flotte.consommation", "transport.proprietaires.liste"):
            self.assertIn(code, reporting)
        for code in ("synthese.rapport_commercial", "ventes.analyses", "tiers.balance_agee_clients"):
            self.assertNotIn(code, reporting)
        # Accueil du reporting : le tableau de bord du transport
        self.assertContains(self.client.get(reverse("reporting:dashboard") + "?seul=1"), "Tableau de bord du transport")
        catalogue = self.client.get(reverse("reporting:catalogue") + "?seul=1")
        self.assertContains(catalogue, "Billetterie par point de vente")
        self.assertNotContains(catalogue, "Rapport commercial journalier")

    def test_toutes_les_commandes_du_transport(self):
        from apps.core.navigation import MODULES, structure_module, modules_proposes
        from apps.core.models import Societe

        def parcourir(noeuds):
            for n in noeuds:
                if n["url"]:
                    yield n
                yield from parcourir(n["enfants"])

        total = 0
        for module in modules_proposes(Societe.get()):
            onglets, _ = structure_module(module)
            for onglet in onglets:
                for noeud in parcourir(onglet["elements"]):
                    with self.subTest(module=module.code, element=noeud["code"]):
                        self.assertEqual(self.client.get(noeud["url"]).status_code, 200)
                    total += 1
        self.assertGreater(total, 150)

    def test_colis_non_livres(self):
        import datetime

        from apps.transport import reporting as tr
        from apps.transport.models import Colis, Gare

        g = Gare.objects.order_by("pk")[:2]
        depart, arrivee = g[0], g[1] if len(g) > 1 else g[0]
        aujourdhui = datetime.date.today()
        Colis.objects.create(numero="TST-A", nature=Colis.COLIS, date=aujourdhui - datetime.timedelta(days=10), gare_depart=depart,
                             gare_arrivee=arrivee, expediteur="X", destinataire="Y", nombre=1, statut=Colis.ARRIVE)
        Colis.objects.create(numero="TST-B", nature=Colis.COLIS, date=aujourdhui - datetime.timedelta(days=2), gare_depart=depart,
                             gare_arrivee=arrivee, expediteur="X", destinataire="Z", nombre=1, statut=Colis.EN_ROUTE)
        Colis.objects.create(numero="TST-C", nature=Colis.COLIS, date=aujourdhui - datetime.timedelta(days=20), gare_depart=depart,
                             gare_arrivee=arrivee, expediteur="X", destinataire="Livré", nombre=1, statut=Colis.LIVRE)
        r = tr.colis_non_livres(aujourdhui, seuil_jours=7)
        self.assertEqual(r["total"], 2)                              # le colis livré est exclu
        self.assertEqual(r["nb_en_retard"], 1)                       # seul celui de 10 jours dépasse le seuil
        self.assertEqual(r["lignes"][0]["jours"], 10)                # trié par ancienneté décroissante
        self.assertTrue(r["lignes"][0]["en_retard"])
        self.assertEqual(self.client.get(reverse("reporting:transport_colis_non_livres") + "?seuil=7").status_code, 200)
        self.assertEqual(self.client.get(reverse("reporting:transport_colis_non_livres") + "?export=csv").status_code, 200)

    def test_etats_du_transport_coherents(self):
        import datetime

        from apps.transport import reporting as tr

        debut, fin = datetime.date(2020, 1, 1), datetime.date(2035, 12, 31)
        b, c = tr.activite_billetterie(debut, fin), tr.activite_colis(debut, fin, "liaison")
        self.assertEqual(b["total"]["total"], b["total"]["especes"] + b["total"]["mobile"] + b["total"]["compte"])
        self.assertEqual(c["total"]["envois"], c["total"]["livres"] + c["total"]["attente"])
        tdb = tr.tableau_de_bord(debut, fin)
        self.assertEqual(len(tdb["indicateurs"]), 9)
        # La recette colis/fret vient des écritures validées (comptes dédiés), jamais de la somme des prix de colis
        from apps.comptabilite import plan_analytique as pa
        from apps.transport.models import ParametresTransport

        p = ParametresTransport.get()
        comptes = {p.compte_colis.numero, p.compte_fret.numero}
        attendu = sum((f["montant"] for f in pa.faits(debut, fin) if f["produit"] and f["compte"] in comptes), 0)
        recette = next(i["valeur"] for i in tdb["indicateurs"] if i["cle"] == "colis_recette")
        self.assertEqual(recette, attendu)
        for url in ("reporting:transport_billetterie", "reporting:transport_colis", "reporting:transport_tableau_de_bord"):
            self.assertEqual(self.client.get(reverse(url) + "?seul=1&export=csv" if url != "reporting:transport_tableau_de_bord"
                                             else reverse(url) + "?seul=1").status_code, 200)
