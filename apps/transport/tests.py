import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase

from apps.commercial.models import Tiers
from apps.comptabilite.models import Compte, Journal, LigneEcriture

from .models import Billet, Chauffeur, Colis, Depart, DepenseVehicule, Gare, Ligne, ParametresTransport, Vehicule


def solde(numero):
    lignes = LigneEcriture.objects.filter(compte__numero=numero)
    return sum((l.debit - l.credit for l in lignes), Decimal("0"))


class TransportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        cls.dla = Gare.objects.create(code="DLA", nom="Gare de Douala", ville="Douala")
        cls.yde = Gare.objects.create(code="YDE", nom="Gare de Yaoundé", ville="Yaoundé")
        cls.ligne = Ligne.objects.create(code="DLA-YDE", gare_depart=cls.dla, gare_arrivee=cls.yde, prix_billet=6000,
                                         colis_forfait=1500, colis_prix_kg=100)
        cls.car = Vehicule.objects.create(immatriculation="LT 123 AB", designation="Car 70 places", nombre_places=3)
        cls.chauffeur = Chauffeur.objects.create(nom="Chauffeur Un")
        cls.jour = datetime.date.today()

    def depart(self, **champs):
        return Depart.objects.create(ligne=self.ligne, date=self.jour, heure=datetime.time(7, 0), vehicule=self.car,
                                     chauffeur=self.chauffeur, **champs)

    def test_vente_billet_comptabilisee_en_caisse(self):
        d = self.depart()
        self.assertEqual(d.places, 3)                                         # places du véhicule
        b = Billet(depart=d, voyageur="Voyageur Un", siege=1).vendre()
        self.assertEqual((b.prix, b.gare, b.caisse.code), (6000, self.dla, "CA"))
        self.assertTrue(b.numero.startswith("BIL"))
        self.assertEqual(solde("5711"), 6000)
        self.assertEqual(solde("41911"), -6000)                              # encaissé, voyage à effectuer
        self.assertEqual(solde("70611"), 0)
        with self.assertRaisesMessage(ValidationError, "déjà vendu"):
            Billet(depart=d, voyageur="Voyageur Deux", siege=1).vendre()
        d.partir()                                                            # la recette va au véhicule qui roule
        self.assertEqual(solde("41911"), 0)
        recette = LigneEcriture.objects.get(compte__numero="70611")
        self.assertEqual((recette.credit, recette.vehicule, recette.section), (6000, self.car, self.dla.section))

    def test_depart_complet(self):
        d = self.depart()
        for n in range(3):
            Billet(depart=d, voyageur=f"V{n}").vendre()
        with self.assertRaisesMessage(ValidationError, "complet"):
            Billet(depart=d, voyageur="V4").vendre()

    def test_billet_en_compte_client(self):
        client = Tiers.objects.create(code="MINSANTE", nom="Ministère", type_tiers=Tiers.CLIENT)
        b = Billet(depart=self.depart(), voyageur="Agent", paiement=Billet.COMPTE, client=client).vendre()
        self.assertEqual(b.ecriture.journal.code, "VT")
        self.assertEqual(b.ecriture.lignes.get(debit=6000).tiers, client)

    def test_annulation_avec_retenue(self):
        b = Billet(depart=self.depart(), voyageur="Voyageur").vendre()
        b.annuler(retenue=1000)
        self.assertEqual(b.statut, Billet.ANNULE)
        self.assertEqual(solde("5711"), 1000)                                 # 6 000 encaissés, 5 000 rendus
        self.assertEqual(solde("41911"), 0)
        self.assertEqual(solde("70611"), -1000)                               # la retenue reste un produit
        self.assertEqual(Depart.objects.get(pk=b.depart_id).places_vendues, 0)
        with self.assertRaises(ValidationError):
            b.annuler()

    def test_report_sur_un_autre_depart(self):
        d1, d2 = self.depart(), self.depart()
        b = Billet(depart=d1, voyageur="Voyageur", siege=2).vendre()
        b.reporter(d2, siege=3)
        b.refresh_from_db()
        self.assertEqual((b.depart, b.siege), (d2, 3))
        self.assertEqual((d1.places_vendues, d2.places_vendues), (0, 1))
        self.assertEqual(solde("5711"), 6000)                                 # aucune écriture de plus

    def test_cycle_du_depart_et_des_colis(self):
        d = self.depart()
        b = Billet(depart=d, voyageur="Voyageur").vendre()
        c = Colis(gare_depart=self.dla, gare_arrivee=self.yde, expediteur="Exp", destinataire="Dest", poids=30).enregistrer()
        self.assertEqual(c.prix, 3000)                                        # 30 kg × 100, au-dessus du forfait
        self.assertEqual(len(c.code_retrait), 6)
        self.assertEqual((solde("41912"), solde("70612")), (-3000, 0))      # encaissé, transport à effectuer
        c.charger(d)
        d.partir()
        recette = LigneEcriture.objects.get(compte__numero="70612")         # recette du car qui le transporte
        self.assertEqual((recette.credit, recette.vehicule), (3000, self.car))
        self.assertEqual(solde("41912"), 0)
        self.assertEqual(Billet.objects.get(pk=b.pk).statut, Billet.EMBARQUE)
        self.assertEqual(Colis.objects.get(pk=c.pk).statut, Colis.EN_ROUTE)
        with self.assertRaisesMessage(ValidationError, "vente impossible"):
            Billet(depart=d, voyageur="Retardataire").vendre()
        d.arriver()
        c.refresh_from_db()
        with self.assertRaisesMessage(ValidationError, "Code de retrait incorrect"):
            c.livrer("000000" if c.code_retrait != "000000" else "111111", "Dest CNI 123")
        c.livrer(c.code_retrait, "Dest CNI 123")
        self.assertEqual(c.statut, Colis.LIVRE)
        self.assertIsNone(c.ecriture_livraison)                               # port payé, rien à encaisser

    def test_port_du_et_contre_remboursement(self):
        d = self.depart()
        c = Colis(gare_depart=self.dla, gare_arrivee=self.yde, expediteur="Boutique", destinataire="Client", prix=2000,
                  port=Colis.DU, contre_remboursement=50000).enregistrer()
        self.assertIsNone(c.ecriture)                                         # rien encaissé au départ
        c.charger(d); d.partir(); d.arriver(); c.refresh_from_db()
        c.livrer(c.code_retrait, "Client CNI 9")
        self.assertEqual(c.ecriture_livraison.lignes.get(debit__gt=0).debit, 52000)
        self.assertEqual(solde("70612"), -2000)
        self.assertEqual(LigneEcriture.objects.get(compte__numero="70612").vehicule, self.car)   # port dû : car du départ
        self.assertEqual(solde("4718"), -50000)                               # dû à l'expéditeur
        c.reverser_contre_remboursement()
        self.assertEqual(solde("4718"), 0)
        self.assertEqual(solde("5711"), 2000)
        with self.assertRaises(ValidationError):
            c.reverser_contre_remboursement()

    def test_fret_et_annulation_colis(self):
        c = Colis(nature=Colis.FRET, gare_depart=self.dla, gare_arrivee=self.yde, expediteur="Usine", destinataire="Dépôt",
                  prix=150000).enregistrer()
        self.assertEqual(solde("41912"), -150000)
        c.annuler()
        self.assertEqual(solde("41912"), 0)
        self.assertEqual(solde("5711"), 0)

    def test_colis_sur_mauvais_depart(self):
        autre = Gare.objects.create(code="BFS", nom="Gare de Bafoussam", ville="Bafoussam")
        c = Colis(gare_depart=self.dla, gare_arrivee=autre, expediteur="E", destinataire="D", prix=1000).enregistrer()
        with self.assertRaisesMessage(ValidationError, "ne va pas"):
            c.charger(self.depart())

    def test_depense_vehicule_et_rentabilite(self):
        d = self.depart()
        Billet(depart=d, voyageur="V").vendre()
        dv = DepenseVehicule(vehicule=self.car, depart=d, nature=DepenseVehicule.CARBURANT, montant=40000,
                             caisse=Journal.objects.get(code="CA")).enregistrer()
        ligne = dv.ecriture.lignes.get(debit=40000)
        self.assertEqual((ligne.compte.numero, ligne.section), ("6053", self.car.section))
        self.assertEqual(d.recette_billets() - d.depenses(), -34000)

    def test_taxe_reglable(self):
        from apps.comptabilite.models import Taxe

        p = ParametresTransport.get()
        p.taxe_billets = Taxe.objects.create(code="T19", intitule="TVA 19,25 %", sens=Taxe.COLLECTEE, taux=Decimal("19.25"),
                                             compte=Compte.objects.get(numero="4431"))
        p.save()
        d = self.depart()
        Billet(depart=d, voyageur="V", prix=11925).vendre()
        d.partir()
        self.assertEqual(d.ecriture_recettes.lignes.get(compte__numero="70611").credit, 10000)
        self.assertEqual(d.ecriture_recettes.lignes.get(compte__numero="4431").credit, 1925)

    def test_comptes_crees_au_premier_usage(self):
        ParametresTransport.get()
        for numero in ("70611", "70612", "70613", "4718", "41911"):
            self.assertTrue(Compte.objects.filter(numero=numero).exists())


class CorrespondanceTests(TestCase):
    """Douala → Garoua-Boulaï avec changement de véhicule à Bertoua : chaque véhicule reçoit sa part de la recette."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        cls.dla = Gare.objects.create(code="DLA", nom="Gare de Douala", ville="Douala")
        cls.bta = Gare.objects.create(code="BTA", nom="Gare de Bertoua", ville="Bertoua")
        cls.gbl = Gare.objects.create(code="GBL", nom="Gare de Garoua-Boulaï", ville="Garoua-Boulaï")
        cls.l1 = Ligne.objects.create(code="DLA-BTA", gare_depart=cls.dla, gare_arrivee=cls.bta, prix_billet=8000)
        cls.l2 = Ligne.objects.create(code="BTA-GBL", gare_depart=cls.bta, gare_arrivee=cls.gbl, prix_billet=4000)
        Ligne.objects.create(code="DLA-GBL", gare_depart=cls.dla, gare_arrivee=cls.gbl, prix_billet=11000)   # tarif direct
        cls.car1 = Vehicule.objects.create(immatriculation="CAR 1", nombre_places=30)
        cls.car2 = Vehicule.objects.create(immatriculation="CAR 2", nombre_places=30)
        cls.ch = Chauffeur.objects.create(nom="Chauffeur")

    def depart(self, ligne, car, heure):
        return Depart.objects.create(ligne=ligne, date=datetime.date.today(), heure=datetime.time(heure), vehicule=car,
                                     chauffeur=self.ch)

    def recette(self, car):
        return -sum((l.debit - l.credit for l in LigneEcriture.objects.filter(compte__numero="70611", vehicule=car)), Decimal(0))

    def test_partage_entre_deux_vehicules(self):
        d1, d2 = self.depart(self.l1, self.car1, 6), self.depart(self.l2, self.car2, 15)
        b = Billet(depart=d1, gare_arrivee=self.gbl, voyageur="Voyageur", siege=4).vendre(depart_correspondance=d2,
                                                                                           siege_correspondance=9)
        self.assertEqual(b.prix, 11000)                                      # tarif Douala → Garoua-Boulaï
        t1, t2 = b.troncons.all()
        self.assertEqual((t1.part, t2.part), (7333, 3667))                   # au prorata 8 000 / 4 000
        self.assertEqual((d1.places_vendues, d2.places_vendues), (1, 1))
        self.assertIn(9, d2.sieges_occupes())
        d1.partir()
        self.assertEqual((self.recette(self.car1), self.recette(self.car2)), (7333, 0))
        self.assertEqual(solde("41911"), -3667)                              # reste à voyager
        with self.assertRaisesMessage(ValidationError, "n'a pas commencé"):
            b.annuler()
        d2.partir()
        self.assertEqual((self.recette(self.car1), self.recette(self.car2)), (7333, 3667))
        self.assertEqual(solde("41911"), 0)

    def test_correspondance_affectee_a_bertoua(self):
        d1 = self.depart(self.l1, self.car1, 6)
        b = Billet(depart=d1, gare_arrivee=self.gbl, voyageur="Voyageur").vendre()          # véhicule choisi à Bertoua
        d2 = self.depart(self.l2, self.car2, 15)
        attente = list(d2.correspondances_a_affecter())
        self.assertEqual([t.billet for t in attente], [b])
        attente[0].affecter(d2, siege=2)
        self.assertEqual(d2.places_vendues, 1)
        self.assertFalse(d2.correspondances_a_affecter().exists())
        with self.assertRaisesMessage(ValidationError, "ne fait pas le trajet"):
            b.troncons.get(ordre=1).affecter(d2)

    def test_sans_tarif_le_prix_est_demande(self):
        autre = Gare.objects.create(code="NGD", nom="Gare de Ngaoundéré", ville="Ngaoundéré")
        d1 = self.depart(self.l1, self.car1, 6)
        with self.assertRaisesMessage(ValidationError, "indiquez le prix"):
            Billet(depart=d1, gare_arrivee=autre, voyageur="V").vendre()
        b = Billet(depart=d1, gare_arrivee=autre, voyageur="V", prix=15000).vendre()
        self.assertEqual([t.part for t in b.troncons.all()], [7500, 7500])  # parts égales sans tarif


class EcransTransportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", "--demo", verbosity=0)

    def setUp(self):
        from django.contrib.auth import get_user_model

        self.client.force_login(get_user_model().objects.create_superuser("admin", "", "x"))

    def test_toutes_les_entrees_du_menu_s_ouvrent(self):
        from apps.core.navigation import TRANSPORT

        def liens(elements):
            for el in elements:
                if el.url:
                    yield el.lien()
                yield from liens(el.tous_enfants())

        vus = 0
        for onglet in TRANSPORT.onglets:
            for lien in liens(onglet.elements):
                self.assertEqual(self.client.get(lien).status_code, 200, lien)
                vus += 1
        self.assertGreater(vus, 20)

    def test_portail_selon_l_activite(self):
        from django.urls import reverse

        from apps.core.models import Societe

        portail = self.client.get(reverse("core:portail"))
        for titre in ("Direction de l&#x27;agence", "Billetterie", "Colis et expéditions", "Garage", "Personnel et paie"):
            self.assertContains(portail, titre)
        Societe.objects.update(activite=Societe.ACTIVITE_COMMERCE)
        portail = self.client.get(reverse("core:portail"))
        self.assertNotContains(portail, "Billetterie")
        self.assertContains(portail, "Personnel et paie")                   # la paie sert aussi au commerce

    def test_chacun_son_logiciel(self):
        """Un guichetier qui n'a que la Billetterie y arrive directement et ne peut pas ouvrir le Garage."""
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        from apps.core import droits as d
        from apps.core.models import AccesLogiciel
        from apps.core.navigation import MODULES

        guichetier = get_user_model().objects.create_user("guichet", "", "x")
        for m in MODULES:
            if m.code != "billetterie":
                AccesLogiciel.objects.create(utilisateur=guichetier, module=m.code, acces=d.AUCUN)
        self.client.force_login(guichetier)
        self.assertRedirects(self.client.get(reverse("core:portail")), reverse("billetterie:accueil"))
        self.assertEqual(self.client.get(reverse("transport:billet_vente")).status_code, 200)
        self.assertEqual(self.client.get(reverse("garage:pleins")).status_code, 403)
        self.assertEqual(self.client.get(reverse("transport:rapport_journalier")).status_code, 403)

    def test_vente_au_guichet_puis_colis_livre(self):
        from django.urls import reverse

        depart = Depart.objects.filter(statut=Depart.PROGRAMME).first()
        page = self.client.get(reverse("transport:depart_detail", args=[depart.pk]))
        self.assertContains(page, "Plan des sièges")
        reponse = self.client.post(reverse("transport:billet_vente"), {"depart": depart.pk, "voyageur": "Voyageur Fictif",
                                                                        "siege": 5, "paiement": "ESPECES"})
        billet = Billet.objects.get(voyageur="Voyageur Fictif")
        self.assertRedirects(reponse, reverse("transport:billet_detail", args=[billet.pk]))
        self.assertEqual(billet.prix, depart.ligne.prix_billet)
        self.assertContains(self.client.get(reverse("transport:billet_imprimer", args=[billet.pk])), "BILLET DE VOYAGE")
        self.client.post(reverse("transport:colis_create"), {
            "nature": "COLIS", "gare_depart": depart.ligne.gare_depart_id, "gare_arrivee": depart.ligne.gare_arrivee_id,
            "expediteur": "Exp", "destinataire": "Dest", "nombre": 1, "poids": 10, "valeur_declaree": 0, "port": "DU",
            "contre_remboursement": 10000})
        colis = Colis.objects.get(expediteur="Exp")
        self.client.post(reverse("transport:colis_detail", args=[colis.pk]), {"action": "charger", "depart": depart.pk})
        for action in ("partir", "arriver"):
            self.client.post(reverse("transport:depart_detail", args=[depart.pk]), {"action": action})
        self.assertContains(self.client.get(reverse("transport:manifeste", args=[depart.pk])), "Voyageur Fictif")
        colis.refresh_from_db()
        self.client.post(reverse("transport:colis_detail", args=[colis.pk]),
                         {"action": "livrer", "code": colis.code_retrait, "retire_par": "Dest CNI 1"})
        colis.refresh_from_db()
        self.assertEqual(colis.statut, Colis.LIVRE)
        recette = self.client.get(reverse("transport:recette"))
        self.assertContains(recette, "11 500")                               # port dû 1 500 + contre-remboursement 10 000
        self.assertContains(self.client.get(reverse("transport:rentabilite") + "?axe=depart"), depart.numero)


class ComptesVehiculesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", "--demo", verbosity=0)

    def test_balance_grand_livre_et_fiche(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        from . import etats

        car = Vehicule.objects.get(immatriculation="LT 101 DEMO")
        d = Depart.objects.filter(vehicule=car).first()
        Billet(depart=d, voyageur="V1").vendre()
        Billet(depart=d, voyageur="V2").vendre()
        d.partir()
        DepenseVehicule(vehicule=car, nature=DepenseVehicule.CARBURANT, montant=5000,
                        caisse=Journal.objects.get(code="CA")).enregistrer()
        jour = datetime.date.today()
        ligne = next(l for l in etats.balance_vehicules(jour, jour) if l["vehicule"] == car)
        self.assertEqual((ligne["voyageurs"], ligne["carburant"], ligne["resultat"]), (12000, 5000, 7000))
        livre = etats.grand_livre_vehicule(car, jour, jour)
        self.assertEqual(livre[-1]["cumul"], 7000)
        self.client.force_login(get_user_model().objects.create_superuser("admin", "", "x"))
        for url in (reverse("transport:vehicule_fiche", args=[car.pk]), reverse("transport:balance_vehicules"),
                    reverse("transport:grand_livre_vehicules") + f"?vehicule={car.pk}",
                    reverse("comptabilite:balance_vehicules"), reverse("comptabilite:grand_livre_vehicules")):
            self.assertContains(self.client.get(url), "LT 101 DEMO", msg_prefix=url)
        car.assurance_echeance = jour - datetime.timedelta(days=1)
        self.assertIn("Assurance expirée", car.alertes()[0])


class JourneeAgenceTests(TestCase):
    """Chaque service saisit dans son logiciel ; le rapport de la Direction et la fiche du véhicule regroupent tout."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", "--demo", verbosity=0)

    def test_rapport_journalier_et_vue_vehicule(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        from apps.garage.models import LigneReparation, OrdreReparation, PleinCarburant
        from apps.personnel.models import Employe, PeriodePaie

        from . import etats

        caisse = Journal.objects.get(code="CA")
        car = Vehicule.objects.get(immatriculation="LT 101 DEMO")
        d = Depart.objects.filter(vehicule=car).first()
        for i in range(3):                                                     # billetterie
            Billet(depart=d, voyageur=f"Voyageur {i}").vendre()
        c = Colis(gare_depart=d.ligne.gare_depart, gare_arrivee=d.ligne.gare_arrivee, expediteur="E", destinataire="D",
                  prix=2500).enregistrer()                                     # colis
        c.charger(d)
        d.partir()
        PleinCarburant(vehicule=car, depart=d, litres=100, prix_litre=840, kilometrage=1000, caisse=caisse).enregistrer()  # garage
        o = OrdreReparation.objects.create(vehicule=car, panne="Pneu")
        LigneReparation.objects.create(ordre=o, designation="Pneu", prix_unitaire=60000)
        o.cloturer(caisse=caisse)
        self.assertEqual(Employe.objects.get(vehicule=car).salaire_base, 120000)                        # chauffeur de la démo
        jour = datetime.date.today()
        paie = PeriodePaie.objects.create(annee=jour.year, mois=jour.month)
        paie.generer()
        paie.valider(date=jour)
        r = etats.rapport_journalier(jour)
        ligne = next(g for g in r["vehicules"] if g["vehicule"] == car)
        self.assertEqual((ligne["voyageurs"], ligne["colis"], ligne["litres"]), (3, 1, 100))
        self.assertEqual((ligne["recettes"], ligne["carburant"], ligne["reparations"], ligne["personnel"]), (20500, 84000, 60000, 120000))
        self.assertEqual(ligne["resultat"], 20500 - 84000 - 60000 - 120000)
        self.client.force_login(get_user_model().objects.create_superuser("admin", "", "x"))
        page = self.client.get(reverse("transport:rapport_journalier"))
        self.assertContains(page, "LT 101 DEMO")
        self.assertContains(page, "admin")                                     # guichetier
        for url in (reverse("transport:vehicule_fiche", args=[car.pk]), reverse("garage:reparation", args=[o.pk]),
                    reverse("garage:consommation"), reverse("personnel:paie", args=[paie.pk]),
                    reverse("personnel:bulletin", args=[paie.bulletins.first().pk]), reverse("billetterie:accueil"),
                    reverse("colis:accueil"), reverse("garage:accueil"), reverse("personnel:accueil"), reverse("transport:accueil")):
            self.assertEqual(self.client.get(url).status_code, 200, url)


class NumerotationAgencesTests(TestCase):
    """Deux agences ne produisent jamais le même numéro de pièce (audit du 26/10)."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", "--demo", verbosity=0)

    def test_numeros_prefixes_par_l_agence(self):
        from apps.echanges import lots

        ligne = Ligne.objects.first()
        Depart.objects.create(numero=f"DEP{datetime.date.today().year}-00004", site_origine="DLA", ligne=ligne,
                              heure=datetime.time(9))                        # copie reçue, ancien format
        lots.configurer_siege("YDE", "Agence de Yaoundé")
        d = Depart.objects.create(ligne=ligne, heure=datetime.time(10))
        self.assertTrue(d.numero.startswith("YDE-DEP"), d.numero)
        b = Billet(depart=d, voyageur="V").vendre()
        self.assertTrue(b.numero.startswith("YDE-BIL"), b.numero)

    def test_mobile_money_hors_de_la_caisse_especes(self):
        d = Depart.objects.filter(statut=Depart.PROGRAMME).first()
        b = Billet(depart=d, voyageur="V", paiement=Billet.MOBILE_MONEY).vendre()
        self.assertEqual(b.caisse.code, "MM")
        self.assertEqual(b.ecriture.lignes.get(debit__gt=0).compte, Journal.objects.get(code="MM").compte_tresorerie)


class CaissesEtCloturesTests(TestCase):
    """P1 : caisse de chaque guichetier, écart justifié et comptabilisé, transferts, clôture de journée."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", "--demo", verbosity=0)

    def test_journee_d_un_guichetier(self):
        from django.contrib.auth import get_user_model

        from .models_caisse import ClotureJournee, SessionCaisse, TransfertFonds, anomalies_du_jour, cloturer_journee

        User = get_user_model()
        agent, chef = User.objects.create_user("guichet", "", "x"), User.objects.create_user("chef", "", "x")
        p = ParametresTransport.get()
        p.sessions_caisse_obligatoires = True
        p.save()
        ca = Journal.objects.get(code="CA")
        d = Depart.objects.filter(statut=Depart.PROGRAMME).first()
        with self.assertRaisesMessage(ValidationError, "Ouvrez votre caisse"):
            Billet(depart=d, voyageur="V").vendre(agent)
        s = SessionCaisse.ouvrir(agent, ca, fonds_initial=10000)
        Billet(depart=d, voyageur="V1").vendre(agent)                       # 6 000 espèces
        b2 = Billet(depart=d, voyageur="V2").vendre(agent)
        Billet(depart=d, voyageur="V3", paiement=Billet.MOBILE_MONEY).vendre(agent)   # hors espèces
        b2.annuler(retenue=1000, utilisateur=agent)                          # 5 000 rendus
        Colis(gare_depart=d.ligne.gare_depart, gare_arrivee=d.ligne.gare_arrivee, expediteur="E", destinataire="D",
              prix=2000).enregistrer(agent)
        self.assertEqual(s.detail()["attendu"], 10000 + 12000 - 5000 + 2000)
        self.assertEqual(s.detail()["billets_mobile"], 6000)
        jour = datetime.date.today()
        self.assertIn("encore ouverte", anomalies_du_jour(jour, ClotureJournee.BILLETTERIE)[0][0])
        s.fermer(18500, "billet de 500 introuvable", "Chef de gare")
        self.assertEqual(s.ecart, -500)
        with self.assertRaisesMessage(ValidationError, "propre caisse"):
            s.approuver(agent)
        s.approuver(chef, imputation=SessionCaisse.AGENT)                     # manquant retenu à l'agent
        self.assertEqual(s.ecriture_ecart.lignes.get(debit=500).compte.numero, "421")
        t = TransfertFonds(origine=ca, destination=Journal.objects.get(code="BQ"), montant=15000).envoyer(chef)
        self.assertEqual(t.ecriture_envoi.lignes.get(debit=15000).compte.numero, "585")
        t.recevoir(chef)
        self.assertEqual(t.statut, TransfertFonds.RECU)
        cloturer_journee(jour, ClotureJournee.BILLETTERIE, chef)
        cloture = cloturer_journee(jour, ClotureJournee.AGENCE, chef)
        self.assertTrue(any("pas clôturé" in a for a in cloture.anomalies))   # colis et garage acceptés ouverts
        with self.assertRaises(ValidationError):
            cloturer_journee(jour, ClotureJournee.AGENCE, chef)

    def test_ecrans(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        self.client.force_login(get_user_model().objects.create_superuser("admin", "", "x"))
        page = self.client.post(reverse("transport:ma_caisse_billetterie"), {"action": "ouvrir", "caisse": Journal.objects.get(code="CA").pk,
                                                                             "fonds_initial": 5000}, follow=True)
        self.assertContains(page, "Espèces attendues")
        page = self.client.post(reverse("transport:ma_caisse_billetterie"), {"action": "fermer", "montant_compte": 5000}, follow=True)
        self.assertContains(page, "Caisse fermée")
        for url in ("transport:sessions_caisse", "transport:transferts", "transport:cloture", "transport:rapport_journalier",
                    "transport:cloture_colis", "transport:ma_caisse_colis"):
            self.assertEqual(self.client.get(reverse(url)).status_code, 200, url)
        self.assertContains(self.client.get(reverse("transport:rapport_journalier")), "Provisoire")


class ExploitationTests(TestCase):
    """P2 : contrôles du départ, avance de mission justifiée, clôture du voyage, salaire réparti selon l'accord."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", "--demo", verbosity=0)

    def test_controles_avance_et_cloture(self):
        from .models_exploitation import AvanceMission, JustificatifMission

        caisse = Journal.objects.get(code="CA")
        car = Vehicule.objects.get(immatriculation="LT 101 DEMO")
        d = Depart.objects.get(vehicule=car)
        d.km_depart = 40000
        d.save()
        doublon = Depart(ligne=d.ligne, date=d.date, heure=d.heure, vehicule=car)
        with self.assertRaisesMessage(ValidationError, "déjà programmé"):
            doublon.full_clean()
        car.assurance_echeance = d.date - datetime.timedelta(days=1)
        car.save()
        with self.assertRaisesMessage(ValidationError, "Assurance expirée"):
            Depart.objects.get(pk=d.pk).partir()
        car.assurance_echeance = None
        car.save()
        a = AvanceMission(depart=d, beneficiaire="Chauffeur 1", montant=20000, caisse=caisse).remettre()
        d.partir()
        autre = Depart.objects.create(ligne=d.ligne, date=d.date, heure=datetime.time(18), vehicule=car, chauffeur=d.chauffeur)
        with self.assertRaisesMessage(ValidationError, "encore sur la route"):
            autre.partir()
        d.arriver()
        JustificatifMission.objects.create(avance=a, nature=JustificatifMission.PEAGE, libelle="Péage Édéa", montant=5000)
        JustificatifMission.objects.create(avance=a, nature=JustificatifMission.FRAIS_ROUTE, montant=8000)
        with self.assertRaisesMessage(ValidationError, "pas encore justifiée"):
            d.cloturer(40250)
        with self.assertRaisesMessage(ValidationError, "Il manque"):
            a.justifier(restitue=0)
        a.justifier(restitue=7000)
        charges = a.ecriture_justification.lignes.filter(debit__gt=0, vehicule=car)
        self.assertEqual(sorted((l.compte.numero, l.debit) for l in charges), [("6181", 8000), ("638", 5000)])
        self.assertEqual(sum((l.debit - l.credit for l in LigneEcriture.objects.filter(compte__numero="47121")), Decimal(0)), 0)
        with self.assertRaisesMessage(ValidationError, "inférieur"):
            d.cloturer(39000)
        d.cloturer(40250, "RAS")
        self.assertEqual((d.statut, d.km_parcourus), (Depart.CLOTURE, 250))

    def test_salaire_reparti_selon_l_accord(self):
        from apps.personnel.models import Employe, PeriodePaie

        car1, car2 = Vehicule.objects.get(immatriculation="LT 101 DEMO"), Vehicule.objects.get(immatriculation="LT 102 DEMO")
        e = Employe.objects.get(vehicule=car1)
        e.ventilation = Employe.VOYAGES
        e.save()
        jour = datetime.date.today()
        for car, heure in ((car1, 20), (car2, 21), (car2, 22)):                 # 1 voyage sur car1, 2 sur car2
            Depart.objects.create(ligne=Ligne.objects.first(), date=jour, heure=datetime.time(heure), vehicule=car,
                                  chauffeur=e.chauffeur, statut=Depart.CLOTURE)
        Employe.objects.exclude(pk=e.pk).update(actif=False)
        paie = PeriodePaie.objects.create(annee=jour.year, mois=jour.month)
        paie.generer()
        paie.valider(date=jour)

        def salaire(car):
            return sum((l.debit for l in paie.ecriture.lignes.filter(compte__numero="661", vehicule=car)), Decimal(0))
        self.assertEqual((salaire(car1), salaire(car2)), (40000, 80000))
        e.ventilation = Employe.JOURS                                           # 1 jour sur chaque car
        self.assertEqual([f for _, f in e.repartition(jour.replace(day=1), jour)], [Decimal("0.5"), Decimal("0.5")])
        e.ventilation = Employe.AGENCE
        self.assertEqual(e.repartition(jour, jour), [])
