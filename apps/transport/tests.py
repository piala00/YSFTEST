import datetime
import io
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
        self.assertEqual((ligne.compte.numero, ligne.section), ("6053000", self.car.section))
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
        from apps.comptabilite.models import Compte
        from apps.comptabilite.services import creer_ecriture

        creer_ecriture(ca, datetime.date.today(), "Fonds de caisse", [               # fonds remis au guichet, déjà en caisse
            {"compte": Compte.objects.get(numero="5711"), "debit": 10000},
            {"compte": Compte.objects.get_or_create(numero="101", defaults={"intitule": "Capital social"})[0], "credit": 10000}])
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
        self.assertEqual(s.ecriture_ecart.lignes.get(debit=500).compte.numero, "4210000")
        t = TransfertFonds(origine=ca, destination=Journal.objects.get(code="BQ"), montant=15000).envoyer(chef)
        self.assertEqual(t.ecriture_envoi.lignes.get(debit=15000).compte.numero, "5850000")
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
        self.assertEqual(sorted((l.compte.numero, l.debit) for l in charges), [("6181000", 8000), ("6380000", 5000)])
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


class BilletterieAvanceeTests(TestCase):
    """P4 : arrêts intermédiaires et sièges par tronçon, embarquement pointé sur la liste, remboursement après
    autorisation, historique du billet."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        cls.dla = Gare.objects.create(code="DLA", nom="Gare de Douala", ville="Douala")
        cls.ede = Gare.objects.create(code="EDE", nom="Arrêt d'Edéa", ville="Edéa")
        cls.yde = Gare.objects.create(code="YDE", nom="Gare de Yaoundé", ville="Yaoundé")
        cls.ligne = Ligne.objects.create(code="DLA-YDE", gare_depart=cls.dla, gare_arrivee=cls.yde, prix_billet=6000)
        Ligne.objects.create(code="DLA-EDE", gare_depart=cls.dla, gare_arrivee=cls.ede, prix_billet=2000)
        Ligne.objects.create(code="EDE-YDE", gare_depart=cls.ede, gare_arrivee=cls.yde, prix_billet=4500)
        from .models import ArretLigne

        ArretLigne.objects.create(ligne=cls.ligne, ordre=1, gare=cls.ede)
        cls.car = Vehicule.objects.create(immatriculation="LT 700 AV", nombre_places=2)
        cls.chauffeur = Chauffeur.objects.create(nom="Chauffeur")

    def depart(self, heure=7):
        return Depart.objects.create(ligne=self.ligne, date=datetime.date.today(), heure=datetime.time(heure),
                                     vehicule=self.car, chauffeur=self.chauffeur)

    def test_arrets_sieges_revendus_apres_descente(self):
        d = self.depart()
        b1 = Billet(depart=d, voyageur="Descend à Edéa", gare_arrivee=self.ede, siege=1).vendre()
        self.assertEqual((b1.prix, b1.troncons.get().gare_arrivee), (2000, self.ede))      # tarif DLA-EDE
        b2 = Billet(depart=d, voyageur="Monte à Edéa", gare_montee=self.ede, siege=1).vendre()  # même siège, après Edéa
        self.assertEqual((b2.prix, b2.montee, b2.destination), (4500, self.ede, self.yde))
        self.assertEqual(d.places_vendues, 1)                                 # au plus 1 voyageur à bord à la fois
        with self.assertRaisesMessage(ValidationError, "déjà vendu"):
            Billet(depart=d, voyageur="Tout le trajet", siege=1).vendre()
        Billet(depart=d, voyageur="Tout le trajet", siege=2).vendre()
        with self.assertRaisesMessage(ValidationError, "complet"):
            Billet(depart=d, voyageur="De trop", gare_arrivee=self.ede).vendre()
        with self.assertRaisesMessage(ValidationError, "avant"):
            Billet(depart=d, voyageur="À l'envers", gare_montee=self.ede, gare_arrivee=self.dla).vendre()
        d.partir()
        self.assertEqual(solde("70611"), -(2000 + 4500 + 6000))
        self.assertEqual(solde("41911"), 0)

    def test_embarquement_pointe_absent_puis_reporte(self):
        d = self.depart()
        present = Billet(depart=d, voyageur="Présent", siege=1).vendre()
        absent = Billet(depart=d, voyageur="Absent", siege=2).vendre()
        d.pointer_embarquement([present.troncons.get().pk])
        d.refresh_from_db()
        d.partir()
        self.assertEqual(solde("70611"), -6000)                               # seul le présent est une recette du car
        self.assertEqual(solde("41911"), -6000)                               # l'absent reste dû au voyageur
        t = absent.troncons.get()
        self.assertEqual((t.depart, t.depart_manque, t.statut), (None, d, "A_VOYAGER"))
        self.assertEqual(Billet.objects.get(pk=absent.pk).statut, Billet.VENDU)
        self.assertEqual(Billet.objects.get(pk=present.pk).statut, Billet.EMBARQUE)
        suivant = self.depart(heure=15)
        absent.refresh_from_db()
        absent.reporter(suivant, siege=1)
        self.assertEqual(absent.troncons.get().depart, suivant)
        evenements = list(absent.historique.values_list("evenement", flat=True))
        self.assertEqual(evenements, ["VENTE", "ABSENT", "REPORT"])
        self.assertIn("PARTI", present.historique.values_list("evenement", flat=True))

    def test_remboursement_autorise_puis_paye(self):
        b = Billet(depart=self.depart(), voyageur="Annule").vendre()
        b.annuler(retenue=1000, rembourser=False)
        self.assertEqual((b.remboursement, b.rembourse), (Billet.AUTORISE, 5000))
        self.assertEqual(solde("5711"), 6000)                                 # rien n'est encore sorti de la caisse
        self.assertEqual(solde("41913"), -5000)                               # dû au voyageur
        b.rembourser()
        self.assertEqual(solde("5711"), 1000)
        self.assertEqual(solde("41913"), 0)
        self.assertEqual(b.remboursement, Billet.PAYE)
        with self.assertRaisesMessage(ValidationError, "Aucun remboursement"):
            b.rembourser()
        self.assertEqual(list(b.historique.values_list("evenement", flat=True)), ["VENTE", "ANNULATION", "REMBOURSEMENT"])

    def test_remboursement_dans_la_session_du_guichetier_qui_paie(self):
        from django.contrib.auth import get_user_model

        from .models_caisse import SessionCaisse

        p = ParametresTransport.get()
        p.sessions_caisse_obligatoires = True
        p.save()
        vendeur = get_user_model().objects.create_user("vendeur", password="x")
        payeur = get_user_model().objects.create_user("payeur", password="x")
        ca = Journal.objects.get(code="CA")
        s1 = SessionCaisse.ouvrir(vendeur, ca, fonds_initial=0)
        b = Billet(depart=self.depart(), voyageur="V").vendre(vendeur)
        b.annuler(retenue=0, utilisateur=vendeur, rembourser=False)
        self.assertEqual(s1.detail()["attendu"], 6000)                        # autorisé, pas payé
        s2 = SessionCaisse.ouvrir(payeur, ca, fonds_initial=10000)
        b.rembourser(payeur)
        self.assertEqual((s1.detail()["attendu"], s2.detail()["attendu"]), (6000, 4000))

    def test_ligne_avec_arrets_par_le_formulaire(self):
        from .forms import LigneForm

        form = LigneForm({"code": "DLA-BFS", "gare_depart": self.dla.pk, "gare_arrivee": self.yde.pk, "arrets": "ede",
                          "prix_billet": 7000, "colis_forfait": 0, "colis_prix_kg": 0, "gamme": "CLASSIQUE", "actif": "on"})
        self.assertTrue(form.is_valid(), form.errors)
        ligne = form.save()
        self.assertEqual([g.code for g in ligne.gares()], ["DLA", "EDE", "YDE"])
        self.assertFalse(LigneForm({"code": "X", "gare_depart": self.dla.pk, "gare_arrivee": self.yde.pk, "arrets": "DLA",
                                    "prix_billet": 1, "colis_forfait": 0, "colis_prix_kg": 0}).is_valid())

    def test_ecrans(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        self.client.force_login(get_user_model().objects.create_superuser("admin", "a@example.com", "x"))
        d = self.depart()
        b = Billet(depart=d, voyageur="Voyageur", siege=1).vendre()
        self.client.post(reverse("transport:depart_detail", args=[d.pk]), {"action": "embarquement", "embarques": [b.troncons.get().pk]})
        self.assertTrue(b.troncons.get().embarque)
        self.assertContains(self.client.get(reverse("transport:depart_detail", args=[d.pk])), "Liste pointée")
        self.assertContains(self.client.get(reverse("transport:manifeste", args=[d.pk])), "Montée")
        self.client.post(reverse("transport:billet_detail", args=[b.pk]), {"action": "annuler", "retenue": "0", "rembourser": "plus_tard"})
        self.assertEqual(Billet.objects.get(pk=b.pk).remboursement, Billet.AUTORISE)
        self.assertContains(self.client.get(reverse("transport:billets") + "?remboursement=AUTORISE"), b.numero)
        self.client.post(reverse("transport:billet_detail", args=[b.pk]), {"action": "rembourser"})
        r = self.client.get(reverse("transport:billet_detail", args=[b.pk]))
        self.assertContains(r, "Historique du billet")
        self.assertContains(r, "remboursé 6")
        self.assertContains(self.client.get(reverse("transport:fiche_update", args=["lignes", self.ligne.pk])), 'value="EDE"')
        self.assertEqual(self.client.get(reverse("transport:billet_vente") + f"?depart={d.pk}").status_code, 200)


class RapportJournalierA4Tests(TestCase):
    """Rapport journalier simple (tableaux) imprimable en A4 portrait : départs du jour d'un côté, encaissements réels
    de l'autre, sans double compte."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        cls.dla = Gare.objects.create(code="DLA", nom="Gare de Douala", ville="Douala")
        cls.yde = Gare.objects.create(code="YDE", nom="Gare de Yaoundé", ville="Yaoundé")
        cls.ligne = Ligne.objects.create(code="DLA-YDE", gare_depart=cls.dla, gare_arrivee=cls.yde, prix_billet=6000,
                                         colis_forfait=1500)
        cls.car = Vehicule.objects.create(immatriculation="LT 800 RJ", designation="Car 08", nombre_places=30)
        cls.chauffeur = Chauffeur.objects.create(nom="Chauffeur")
        cls.jour = datetime.date.today()

    def test_tableaux_et_caisse(self):
        from . import etats
        from .models_caisse import TransfertFonds

        ca, mm, bq = (Journal.objects.get(code=c) for c in ("CA", "MM", "BQ"))
        hier = self.jour - datetime.timedelta(days=1)
        d = Depart.objects.create(ligne=self.ligne, date=self.jour, heure=datetime.time(8), vehicule=self.car, chauffeur=self.chauffeur)
        Billet(depart=d, voyageur="Payé hier", date_vente=hier).vendre()            # caisse d'hier, départ d'aujourd'hui
        Billet(depart=d, voyageur="Espèces").vendre()
        Billet(depart=d, voyageur="Mobile", paiement=Billet.MOBILE_MONEY).vendre()
        Billet(depart=d, voyageur="Prix spécial", prix=5000).vendre()
        Billet(depart=d, voyageur="Annulé").vendre().annuler(retenue=1000)          # remboursé 5 000 en espèces
        Colis(gare_depart=self.dla, gare_arrivee=self.yde, expediteur="E", destinataire="D", prix=2000).enregistrer()
        d.partir()
        DepenseVehicule(vehicule=self.car, nature=DepenseVehicule.CARBURANT, montant=10000, caisse=ca).enregistrer()
        TransfertFonds(origine=ca, destination=bq, montant=4000).envoyer()          # versement : ni recette ni dépense

        r = etats.rapport_agence_a4(self.jour)
        lignes = [(l["trajet"], l["places"], l["prix"], l["montant"]) for l in r["billetterie"]]
        self.assertEqual(lignes, [("Douala → Yaoundé", 3, 6000, 18000), ("Douala → Yaoundé", 1, 5000, 5000)])
        self.assertEqual(r["total_billetterie"], {"places": 4, "montant": 23000})
        c = r["caisse"]
        self.assertEqual((c["billets"], c["especes"], c["electronique"]), (6000 + 6000 + 5000 + 6000, 6000 + 5000 + 6000 + 2000, 6000))
        self.assertEqual((c["colis"], c["remboursements"], c["sorties"]), (2000, 5000, 10000))
        self.assertEqual(c["nette"], 25000 - 5000 - 10000)
        self.assertEqual([s["affectation"] for s in r["sorties"]], ["LT 800 RJ"])
        self.assertEqual(r["colis"][0]["destination"], "Yaoundé")
        # espèces : 6 000 d'hier + 19 000 − 5 000 − 10 000 − 4 000 versés
        self.assertEqual((c["ouverture_especes"], c["transferts_especes"], c["solde_especes"]), (6000, -4000, 6000))
        self.assertEqual(r["total_caisses"]["entrees"], 25000)                       # le versement n'est pas une recette

    def test_page_a4_portrait(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        self.client.force_login(get_user_model().objects.create_superuser("admin", "a@example.com", "x"))
        r = self.client.get(reverse("transport:rapport_journalier_imprimer"))
        self.assertContains(r, "size: A4 portrait")
        self.assertContains(r, "RAPPORT JOURNALIER D'AGENCE")
        self.assertContains(r, "PROVISOIRE")
        self.assertContains(r, "Aucune opération")
        self.assertContains(self.client.get(reverse("transport:rapport_journalier")), "Imprimer (A4 portrait)")


class ComptabiliteAnalytiqueTests(TestCase):
    """Comptabilité analytique Véhicules / Propriétaires : montants tirés des seules écritures générales validées,
    flottes Classique / VIP distinctes, propriétaire selon le contrat daté, rapprochement avec la générale."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        cls.dla = Gare.objects.create(code="DLA", nom="Gare de Douala", ville="Douala")
        cls.yde = Gare.objects.create(code="YDE", nom="Gare de Yaoundé", ville="Yaoundé")
        cls.ligne = Ligne.objects.create(code="DLA-YDE", gare_depart=cls.dla, gare_arrivee=cls.yde, prix_billet=6000)
        cls.ligne_vip = Ligne.objects.create(code="DLA-YDE-VIP", gare_depart=cls.dla, gare_arrivee=cls.yde, prix_billet=10000,
                                             gamme="VIP")
        cls.car = Vehicule.objects.create(immatriculation="LT 900 CL", nombre_places=30)
        cls.vip = Vehicule.objects.create(immatriculation="LT 901 VP", nombre_places=20, gamme="VIP")
        cls.chauffeur = Chauffeur.objects.create(nom="Chauffeur")
        cls.jour = datetime.date.today()
        cls.debut = cls.jour - datetime.timedelta(days=10)

    def voyage(self, vehicule, ligne, billets, jour=None):
        d = Depart.objects.create(ligne=ligne, date=jour or self.jour, heure=datetime.time(7), vehicule=vehicule,
                                  chauffeur=self.chauffeur)
        for n in range(billets):
            Billet(depart=d, voyageur=f"V{n}").vendre()
        d.partir()
        return d

    def test_flottes_classique_et_vip_distinctes(self):
        d = Depart(ligne=self.ligne_vip, date=self.jour, heure=datetime.time(9), vehicule=self.car, chauffeur=self.chauffeur)
        with self.assertRaisesMessage(ValidationError, "flotte Classique"):
            d.full_clean()
        d.vehicule = self.vip
        d.full_clean()
        self.vip.gamme = "CLASSIQUE"                                   # changement de flotte : daté, pas rétroactif
        self.vip.save()
        hier = self.jour - datetime.timedelta(days=1)
        self.assertEqual((self.vip.gamme_le(hier), self.vip.gamme_le(self.jour)), ("VIP", "CLASSIQUE"))

    def test_vehicules_source_unique_et_rapprochement(self):
        from apps.comptabilite.models import Compte
        from apps.comptabilite.services import creer_ecriture

        from . import analytique

        self.voyage(self.car, self.ligne, 2)                           # 12 000
        self.voyage(self.vip, self.ligne_vip, 1)                       # 10 000
        DepenseVehicule(vehicule=self.car, nature=DepenseVehicule.CARBURANT, montant=3000,
                        caisse=Journal.objects.get(code="CA")).enregistrer()
        loyer = Compte.objects.get_or_create(numero="6222", defaults={"intitule": "Locations de bâtiments"})[0]
        creer_ecriture(Journal.objects.get(code="CA"), self.jour, "Loyer du siège",            # sans véhicule
                       [{"compte": loyer, "debit": 50000}, {"compte": Compte.objects.get(numero="5711"), "credit": 50000}])
        brouillard = creer_ecriture(Journal.objects.get(code="OD"), self.jour, "Brouillard",   # non validée : exclue
                                    [{"compte": Compte.objects.get(numero="6053"), "debit": 999, "vehicule": self.car},
                                     {"compte": Compte.objects.get(numero="5711"), "credit": 999}], valider=False)
        self.assertEqual(brouillard.statut, "BROUILLARD")
        r = analytique.vehicules(self.debut, self.jour)
        g = {l["vehicule"].immatriculation: l for l in r["lignes"]}
        self.assertEqual((g["LT 900 CL"]["billetterie"], g["LT 900 CL"]["carburant"], g["LT 900 CL"]["resultat"]), (12000, 3000, 9000))
        self.assertEqual((g["LT 901 VP"]["gamme"], g["LT 901 VP"]["produits"]), ("VIP", 10000))
        c = r["controle"]
        self.assertEqual((c["produits_gl"], c["produits_affectes"], c["produits_non_affectes"]), (22000, 22000, 0))
        self.assertEqual((c["charges_gl"], c["charges_affectees"], c["charges_non_affectees"]), (53000, 3000, 50000))
        vip = analytique.vehicules(self.debut, self.jour, gamme="VIP")
        self.assertEqual([l["vehicule"].immatriculation for l in vip["lignes"]], ["LT 901 VP"])
        compte = analytique.compte_vehicule(self.car, self.debut, self.jour)
        self.assertEqual(len(compte["details"]["billetterie"]), 1)       # drill-down vers l'écriture du départ

    def test_proprietaires_selon_le_contrat_date(self):
        from apps.commercial.models import Tiers
        from apps.partenaires.models import ContratPartenaire, Decompte

        from . import analytique

        from apps.comptabilite.services import creer_ecriture

        avant = self.jour - datetime.timedelta(days=5)                 # avant le contrat : à la société
        creer_ecriture(Journal.objects.get(code="OD"), avant, "Recette antérieure",
                       [{"compte": ParametresTransport.get().compte_billets_a_voyager, "debit": 6000},
                        {"compte": ParametresTransport.get().compte_billets, "credit": 6000, "vehicule": self.car}])
        proprio = Tiers.objects.create(code="PROP9", nom="Propriétaire Neuf", type_tiers=Tiers.FOURNISSEUR)
        contrat = ContratPartenaire.objects.create(vehicule=self.car, partenaire=proprio, debut=self.jour,
                                                   taux_commission=Decimal("20")).activer()
        self.voyage(self.car, self.ligne, 2)                            # sous contrat : au propriétaire
        Decompte.calculer(contrat, self.jour, self.jour).approuver()     # 12 000 − 20 % = 9 600 dû
        r = {(p["partenaire"].nom if p["partenaire"] else None): p for p in analytique.proprietaires(self.debut, self.jour)}
        self.assertEqual(r[None]["total"]["produits"], 6000)
        pf = r["Propriétaire Neuf"]
        self.assertEqual((pf["total"]["produits"], pf["total"]["proprietaire"], pf["total"]["resultat_societe"]), (12000, 9600, 2400))
        self.assertEqual((pf["finance"]["comptabilise"], pf["finance"]["solde"], pf["finance"]["droits_provisoires"]), (9600, 9600, 0))

    def test_rentabilite_tiree_de_la_comptabilite(self):
        from . import etats

        d = self.voyage(self.car, self.ligne, 2)
        DepenseVehicule(vehicule=self.car, depart=d, nature=DepenseVehicule.CARBURANT, montant=4000,
                        caisse=Journal.objects.get(code="CA")).enregistrer()
        Billet(depart=self.voyage(self.vip, self.ligne_vip, 1), voyageur="x")       # non vendu : rien
        lignes = {l["libelle"]: l for l in etats.rentabilite(self.debut, self.jour, "depart")}
        l = lignes[str(d)]
        self.assertEqual((l["billets"], l["depenses"], l["marge"], l["voyageurs"]), (12000, 4000, 8000, 2))

    def test_ecrans(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        self.client.force_login(get_user_model().objects.create_superuser("admin", "a@example.com", "x"))
        self.voyage(self.car, self.ligne, 1)
        for url in (reverse("comptabilite:analytique_vehicules"), reverse("comptabilite:analytique_vehicule", args=[self.car.pk]),
                    reverse("comptabilite:analytique_proprietaires"), reverse("comptabilite:analytique_releves"),
                    reverse("comptabilite:analytique_vehicules") + "?gamme=VIP"):
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertContains(self.client.get(reverse("comptabilite:analytique_vehicules")), "Rapprochement avec la comptabilité générale")
        self.assertContains(self.client.get(reverse("comptabilite:analytique_vehicule", args=[self.car.pk])), "RÉSULTAT D'EXPLOITATION")


class BagagesTests(TestCase):
    """Bagages payants déclarés à l'achat du billet : encaissés avec le billet, recette du véhicule au départ."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        cls.dla = Gare.objects.create(code="DLA", nom="Gare de Douala", ville="Douala")
        cls.bta = Gare.objects.create(code="BTA", nom="Gare de Bertoua", ville="Bertoua")
        cls.gbl = Gare.objects.create(code="GBL", nom="Gare de Garoua-Boulaï", ville="Garoua-Boulaï")
        cls.l1 = Ligne.objects.create(code="DLA-BTA", gare_depart=cls.dla, gare_arrivee=cls.bta, prix_billet=8000)
        cls.l2 = Ligne.objects.create(code="BTA-GBL", gare_depart=cls.bta, gare_arrivee=cls.gbl, prix_billet=4000)
        cls.car1 = Vehicule.objects.create(immatriculation="LT 111 BG", nombre_places=30)
        cls.car2 = Vehicule.objects.create(immatriculation="LT 222 BG", nombre_places=30)
        cls.chauffeur = Chauffeur.objects.create(nom="Chauffeur")

    def depart(self, ligne, car, heure=7):
        return Depart.objects.create(ligne=ligne, date=datetime.date.today(), heure=datetime.time(heure), vehicule=car,
                                     chauffeur=self.chauffeur)

    def test_bagages_encaisses_puis_recette_du_vehicule(self):
        from . import analytique, etats

        d = self.depart(self.l1, self.car1)
        b = Billet(depart=d, voyageur="Avec bagages", bagages="2 cartons, 1 sac", bagages_nombre=3, bagages_poids=45,
                   prix_bagages=3000).vendre()
        self.assertEqual((b.total, solde("5711"), solde("41911")), (11000, 11000, -11000))
        with self.assertRaisesMessage(ValidationError, "Décrivez les bagages"):
            Billet(depart=d, voyageur="Sans description", prix_bagages=500).vendre()
        d.partir()
        self.assertEqual((solde("41911"), solde("70611"), solde("70614")), (0, -8000, -3000))
        bag = LigneEcriture.objects.get(compte__numero="70614")
        self.assertEqual(bag.vehicule, self.car1)
        r = etats.rapport_agence_a4(datetime.date.today())
        self.assertEqual((r["total_bagages"], r["caisse"]["bagages"], r["caisse"]["billets"]),
                         ({"quantite": 3, "montant": 3000}, 3000, 8000))
        ligne = next(l for l in analytique.vehicules(datetime.date.today(), datetime.date.today())["lignes"]
                     if l["vehicule"] == self.car1)
        self.assertEqual((ligne["billetterie"], ligne["bagages"]), (8000, 3000))

    def test_correspondance_bagages_partages_et_annulation(self):
        d1, d2 = self.depart(self.l1, self.car1), self.depart(self.l2, self.car2, heure=15)
        b = Billet(depart=d1, voyageur="Long trajet", gare_arrivee=self.gbl, prix=12000, bagages="1 malle",
                   prix_bagages=1200).vendre(depart_correspondance=d2)
        self.assertEqual([t.part_bagages for t in b.troncons.all()], [800, 400])     # même partage que le billet (8 000 / 4 000)
        b2 = Billet(depart=d1, voyageur="Annule", bagages="1 sac", prix_bagages=1000).vendre()
        b2.annuler(retenue=2000)
        self.assertEqual(b2.rembourse, 8000 + 1000 - 2000)                            # bagages rendus en entier

    def test_vente_au_guichet_avec_bagages(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        self.client.force_login(get_user_model().objects.create_superuser("admin", "a@example.com", "x"))
        d = self.depart(self.l1, self.car1)
        self.client.post(reverse("transport:billet_vente"), {
            "depart": d.pk, "voyageur": "Guichet", "paiement": "ESPECES", "bagages": "1 carton", "bagages_nombre": 1,
            "bagages_poids": "20", "prix_bagages": "1500"})
        b = Billet.objects.get(voyageur="Guichet")
        self.assertEqual((b.prix, b.prix_bagages, b.total), (8000, 1500, 9500))
        self.assertContains(self.client.get(reverse("transport:billet_detail", args=[b.pk])), "1 carton")
        self.assertContains(self.client.get(reverse("transport:manifeste", args=[d.pk])), "1 carton")


class SystemeMinimalTresorerieTests(TestCase):
    """Système comptable choisi pour la société : le SMT présente les mêmes écritures en recettes et dépenses."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--systeme", "smt", verbosity=0)
        dla = Gare.objects.create(code="DLA", nom="Gare de Douala", ville="Douala")
        yde = Gare.objects.create(code="YDE", nom="Gare de Yaoundé", ville="Yaoundé")
        cls.ligne = Ligne.objects.create(code="DLA-YDE", gare_depart=dla, gare_arrivee=yde, prix_billet=6000)
        cls.car = Vehicule.objects.create(immatriculation="LT 321 SM", nombre_places=30)
        cls.chauffeur = Chauffeur.objects.create(nom="Chauffeur")

    def test_etats_smt(self):
        from apps.comptabilite import smt
        from apps.comptabilite.models import Compte
        from apps.comptabilite.services import creer_ecriture
        from apps.core.models import Exercice, Societe

        self.assertEqual(Societe.get().systeme_comptable, Societe.SYSTEME_SMT)
        jour = datetime.date.today()
        d = Depart.objects.create(ligne=self.ligne, date=jour, heure=datetime.time(7), vehicule=self.car, chauffeur=self.chauffeur)
        Billet(depart=d, voyageur="Parti").vendre()
        d.partir()
        Billet(depart=Depart.objects.create(ligne=self.ligne, date=jour, heure=datetime.time(15), vehicule=self.car,
                                            chauffeur=self.chauffeur), voyageur="Demain").vendre()   # encaissé, pas voyagé
        ca = Journal.objects.get(code="CA")
        DepenseVehicule(vehicule=self.car, nature=DepenseVehicule.CARBURANT, montant=3000, caisse=ca).enregistrer()
        loyer = Compte.objects.get_or_create(numero="6222", defaults={"intitule": "Locations de bâtiments"})[0]
        creer_ecriture(ca, jour, "Loyer", [{"compte": loyer, "debit": 5000}, {"compte": Compte.objects.get(numero="5711"), "credit": 5000}])
        ex = Exercice.courant()
        cr = smt.compte_de_resultat(ex.date_debut, ex.date_fin)
        m = cr["montants"]
        self.assertEqual((m["ventes"], m["achats"], m["loyers"], cr["solde"]), (12000, 3000, 5000, 4000))
        self.assertEqual(cr["var_dettes"], 6000)                           # billet encaissé, voyage à faire
        self.assertEqual((cr["resultat"], cr["resultat_comptable"], cr["ecart"]), (-2000, -2000, 0))
        b = smt.bilan(ex.date_fin)
        self.assertTrue(b["equilibre"])
        self.assertEqual(b["passif"]["resultat"], -2000)

    def test_ecrans_smt_et_normal(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        self.client.force_login(get_user_model().objects.create_superuser("admin", "a@example.com", "x"))
        self.assertContains(self.client.get(reverse("comptabilite:bilan") + "?ok=1"), "système minimal de trésorerie")
        self.assertContains(self.client.get(reverse("comptabilite:compte_resultat") + "?ok=1"), "TOTAL DES RECETTES SUR PRODUITS")
        self.assertContains(self.client.get(reverse("comptabilite:bilan") + "?ok=1&systeme=NORMAL"), "Bilan SYSCOHADA")


class DepensesFonctionnementTests(TestCase):
    """Dépenses de fonctionnement : demandées, autorisées (par le siège ou un autre utilisateur), puis payées."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)

    def test_circuit_dans_un_dossier_sans_echanges(self):
        from django.contrib.auth import get_user_model

        from .models_depenses import DemandeDepense

        U = get_user_model()
        agent, chef = U.objects.create_user("agent", password="x"), U.objects.create_user("chef", password="x")
        d = DemandeDepense(nature=DemandeDepense.LOYER, libelle="Loyer d'octobre", montant=Decimal(75000)).demander(agent)
        self.assertEqual(d.statut, DemandeDepense.DEMANDEE)
        with self.assertRaisesMessage(ValidationError, "autorisée avant"):
            d.payer(Journal.objects.get(code="CA"))
        with self.assertRaisesMessage(ValidationError, "propre dépense"):
            d.decider(True, agent)
        with self.assertRaisesMessage(ValidationError, "motif"):
            d.decider(False, chef)
        d.decider(True, chef)
        d.payer(Journal.objects.get(code="CA"), agent)
        self.assertEqual((d.statut, solde("6222"), solde("5711")), (DemandeDepense.PAYEE, 75000, -75000))

    def test_plafond_autorisation_d_office(self):
        from .models_depenses import DemandeDepense

        p = ParametresTransport.get()
        p.plafond_depense_sans_autorisation = 10000
        p.save()
        petite = DemandeDepense(nature=DemandeDepense.TELECOM, libelle="Recharge Internet", montant=Decimal(5000)).demander()
        grosse = DemandeDepense(nature=DemandeDepense.LOYER, libelle="Loyer", montant=Decimal(50000)).demander()
        self.assertEqual((petite.statut, grosse.statut), (DemandeDepense.AUTORISEE, DemandeDepense.DEMANDEE))

    def test_ecran(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        from .models_depenses import DemandeDepense

        self.client.force_login(get_user_model().objects.create_superuser("admin", "a@example.com", "x"))
        url = reverse("transport:depenses_fonctionnement")
        self.client.post(url, {"action": "demander", "nature": "EAU_ELECTRICITE", "libelle": "Facture d'électricité", "montant": "30000"})
        d = DemandeDepense.objects.get()
        self.client.post(url, {"action": "autoriser", "demande": d.pk})
        self.client.post(url, {"action": "payer", "demande": d.pk, "caisse": Journal.objects.get(code="CA").pk})
        d.refresh_from_db()
        self.assertEqual(d.statut, DemandeDepense.PAYEE)
        self.assertContains(self.client.get(url), "Facture d&#x27;électricité")


class ImprevusTests(TestCase):
    """Imprévus de voyage (docs/IMPREVUS_VOYAGE.md) : seules les écritures de ce qui change, jamais de double recette."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        dla = Gare.objects.create(code="DLA", nom="Gare de Douala", ville="Douala")
        yde = Gare.objects.create(code="YDE", nom="Gare de Yaoundé", ville="Yaoundé")
        cls.ligne = Ligne.objects.create(code="DLA-YDE", gare_depart=dla, gare_arrivee=yde, prix_billet=6000)
        cls.ligne_vip = Ligne.objects.create(code="DLA-YDE-VIP", gare_depart=dla, gare_arrivee=yde, prix_billet=10000, gamme="VIP")
        cls.car = Vehicule.objects.create(immatriculation="LT 501 IM", nombre_places=30)
        cls.secours = Vehicule.objects.create(immatriculation="LT 502 IM", nombre_places=30)
        cls.chauffeur = Chauffeur.objects.create(nom="Chauffeur")
        cls.ca = Journal.objects.get(code="CA")

    def depart(self, ligne=None, heure=7):
        return Depart.objects.create(ligne=ligne or self.ligne, date=datetime.date.today(), heure=datetime.time(heure),
                                     vehicule=self.car, chauffeur=self.chauffeur)

    def recette(self, compte, vehicule):
        return -sum((l.debit - l.credit for l in LigneEcriture.objects.filter(compte__numero=compte, vehicule=vehicule)), Decimal(0))

    def test_transbordement_vers_un_car_de_la_societe(self):
        from .models_incidents import Incident

        d = self.depart()
        for n in range(2):
            Billet(depart=d, voyageur=f"V{n}", bagages="1 sac", prix_bagages=1000).vendre()
        d.partir()
        i = Incident.transborder(d, 40, self.secours, lieu="Edéa")
        self.assertEqual((self.recette("70611", self.car), self.recette("70611", self.secours)), (7200, 4800))
        self.assertEqual((self.recette("70614", self.car), self.recette("70614", self.secours)), (1200, 800))
        self.assertEqual(solde("70611"), -12000)                                 # recette totale inchangée
        self.assertEqual(i.ecriture.journal.code, "OD")

    def test_car_loue_frais_et_dedommagements(self):
        from apps.commercial.models import Tiers

        from .models_incidents import FraisIncident, Incident

        d = self.depart()
        Billet(depart=d, voyageur="V").vendre()
        d.partir()
        loue = Incident.transborder(d, 50)                                       # car loué : pas de partage de recette
        self.assertIsNone(loue.ecriture)
        loueur = Tiers.objects.create(code="LOUEUR", nom="Transporteur de secours", type_tiers=Tiers.FOURNISSEUR)
        FraisIncident(incident=loue, nature=FraisIncident.LOCATION, libelle="Car de secours", montant=Decimal(30000),
                      paiement=FraisIncident.FOURNISSEUR, fournisseur=loueur).enregistrer()
        dec = Incident.objects.create(depart=d, type_incident=Incident.DECLASSEMENT)
        FraisIncident(incident=dec, nature=FraisIncident.DEDOMMAGEMENT, libelle="Différence VIP", montant=Decimal(2000),
                      caisse=self.ca).enregistrer()
        amende = Incident.objects.create(depart=d, type_incident=Incident.AMENDE)
        FraisIncident(incident=amende, nature=FraisIncident.AMENDE, libelle="Excès de vitesse", montant=Decimal(5000),
                      paiement=FraisIncident.CHAUFFEUR, caisse=self.ca).enregistrer()
        location = LigneEcriture.objects.get(compte__numero="6228")
        self.assertEqual((location.debit, location.vehicule), (30000, self.car))
        self.assertEqual((solde("709"), solde("421"), solde("658")), (2000, 5000, 0))   # amende retenue au chauffeur
        bord = Incident.recette_a_bord(d, 3000, 1, self.ca)
        self.assertEqual(self.recette("70611", self.car), 6000 + 3000)
        self.assertEqual(bord.ecriture.lignes.get(debit=3000).compte.numero, "5711000")

    def test_annulation_par_la_compagnie(self):
        d, autre = self.depart(), self.depart(heure=15)
        b1 = Billet(depart=d, voyageur="Reporté").vendre()
        reportes, rembourses = d.annuler_par_la_compagnie("Panne avant le départ", nouveau_depart=autre)
        self.assertEqual((reportes, rembourses, Depart.objects.get(pk=d.pk).statut), (1, 0, Depart.ANNULE))
        self.assertEqual(b1.troncons.get().depart, autre)
        d2 = self.depart(heure=9)
        b2 = Billet(depart=d2, voyageur="Remboursé").vendre()
        d2.annuler_par_la_compagnie("Route coupée")
        b2.refresh_from_db()
        self.assertEqual((b2.statut, b2.retenue, b2.remboursement), (Billet.ANNULE, 0, Billet.AUTORISE))
        self.assertEqual(solde("41913"), -6000)                                  # à rendre au voyageur, sans retenue

    def test_vehicule_de_remplacement_d_une_autre_flotte(self):
        d = Depart(ligne=self.ligne_vip, date=datetime.date.today(), heure=datetime.time(10), vehicule=self.car,
                   chauffeur=self.chauffeur)
        with self.assertRaises(ValidationError):
            d.full_clean()
        d.vehicule_remplacement = True
        with self.assertRaisesMessage(ValidationError, "motif"):
            d.full_clean()
        d.motif_remplacement = "Car VIP en panne"
        d.full_clean()

    def test_ecran(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        self.client.force_login(get_user_model().objects.create_superuser("admin", "a@example.com", "x"))
        d = self.depart()
        Billet(depart=d, voyageur="V").vendre()
        d.partir()
        url = reverse("transport:depart_detail", args=[d.pk])
        self.client.post(url, {"action": "transborder", "vehicule_secours": self.secours.pk, "part_restante": "50"})
        self.client.post(url, {"action": "frais", "type_incident": "PANNE", "nature": "DEPANNAGE", "libelle": "Remorquage",
                               "montant": "15000", "paiement": "CAISSE", "caisse": self.ca.pk})
        r = self.client.get(url)
        self.assertContains(r, "Transbordement vers un autre car")
        self.assertContains(r, "Remorquage")
        self.assertEqual(solde("624"), 15000)


class ComparaisonsTransportTests(TestCase):
    """Reporting comparatif : deux périodes, mêmes écritures que la comptabilité, sans double compte."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        dla = Gare.objects.create(code="DLA", nom="Gare de Douala", ville="Douala")
        yde = Gare.objects.create(code="YDE", nom="Gare de Yaoundé", ville="Yaoundé")
        cls.ligne = Ligne.objects.create(code="DLA-YDE", gare_depart=dla, gare_arrivee=yde, prix_billet=6000)
        cls.ligne_vip = Ligne.objects.create(code="DLA-YDE-VIP", gare_depart=dla, gare_arrivee=yde, prix_billet=10000, gamme="VIP")
        cls.car = Vehicule.objects.create(immatriculation="LT 601 CP", nombre_places=10)
        cls.vip = Vehicule.objects.create(immatriculation="LT 602 CP", nombre_places=10, gamme="VIP")
        cls.chauffeur = Chauffeur.objects.create(nom="Chauffeur")

    def test_comparaison_de_deux_periodes(self):
        from apps.comptabilite.models import Compte
        from apps.comptabilite.services import creer_ecriture

        from . import reporting

        jour = datetime.date.today()
        for car, ligne, n in ((self.car, self.ligne, 2), (self.vip, self.ligne_vip, 1)):
            d = Depart.objects.create(ligne=ligne, date=jour, heure=datetime.time(7), vehicule=car, chauffeur=self.chauffeur)
            for k in range(n):
                Billet(depart=d, voyageur=f"V{k}").vendre()
            d.partir()
        avant = jour - datetime.timedelta(days=40)
        p = ParametresTransport.get()
        creer_ecriture(Journal.objects.get(code="OD"), avant, "Recette période B",
                       [{"compte": p.compte_billets_a_voyager, "debit": 5000},
                        {"compte": p.compte_billets, "credit": 5000, "vehicule": self.car}])
        loyer = Compte.objects.get_or_create(numero="6222", defaults={"intitule": "Loyers"})[0]
        creer_ecriture(Journal.objects.get(code="CA"), jour, "Loyer", [{"compte": loyer, "debit": 4000},
                                                                        {"compte": Compte.objects.get(numero="5711"), "credit": 4000}])
        a, b = (jour - datetime.timedelta(days=5), jour), (avant - datetime.timedelta(days=5), avant)
        r = reporting.comparer("vehicule", a, b)
        lignes = {l["libelle"]: l for l in r["lignes"]}
        self.assertEqual((lignes["LT 601 CP"]["a"]["produits"], lignes["LT 601 CP"]["b"]["produits"],
                          lignes["LT 601 CP"]["ecart"], lignes["LT 601 CP"]["variation_produits"]), (12000, 5000, 7000, 140))
        self.assertEqual(lignes["LT 601 CP"]["a"]["voyageurs"], 2)
        gammes = {l["libelle"]: l["a"]["produits"] for l in reporting.comparer("gamme", a, b)["lignes"]}
        self.assertEqual(gammes, {"Classique": 12000, "VIP": 10000})
        agence = reporting.comparer("agence", a, b)["total"]["a"]
        self.assertEqual((agence["produits"], agence["charges"], agence["resultat"]), (22000, 4000, 18000))   # loyer compris
        ligne = {l["libelle"]: l["a"]["produits"] for l in reporting.comparer("ligne", a, b)["lignes"]}
        self.assertEqual(ligne, {"DLA-YDE": 12000, "DLA-YDE-VIP": 10000, "Hors voyage": 0})   # B : écriture sans départ

    def test_ecrans(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        self.client.force_login(get_user_model().objects.create_superuser("admin", "a@example.com", "x"))
        for axe in ("agence", "gamme", "ligne", "vehicule", "proprietaire"):
            r = self.client.get(reverse("reporting:comparaisons_transport") + f"?axe={axe}")
            self.assertEqual(r.status_code, 200, axe)
            self.assertContains(r, "Écart A − B")


class AnomaliesRapportJournalierTests(TestCase):
    """Anomalies relevées sur le rapport RJ : caisse négative, départs futurs, rapprochement, car des colis."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        dla = Gare.objects.create(code="DLA", nom="Gare de Douala", ville="Douala")
        yde = Gare.objects.create(code="YDE", nom="Gare de Yaoundé", ville="Yaoundé")
        cls.ligne = Ligne.objects.create(code="DLA-YDE", gare_depart=dla, gare_arrivee=yde, prix_billet=6000, colis_forfait=2500)
        cls.car = Vehicule.objects.create(immatriculation="LT 701 AN", nombre_places=30)
        cls.chauffeur = Chauffeur.objects.create(nom="Chauffeur")
        cls.ca = Journal.objects.get(code="CA")

    def depart(self, jour=None, heure=7):
        return Depart.objects.create(ligne=self.ligne, date=jour or datetime.date.today(), heure=datetime.time(heure),
                                     vehicule=self.car, chauffeur=self.chauffeur)

    def test_depart_futur_refuse(self):
        from django.test import override_settings

        demain = self.depart(jour=datetime.date.today() + datetime.timedelta(days=1))
        with self.assertRaisesMessage(ValidationError, "avant ce jour"):
            demain.partir()
        p = ParametresTransport.get()
        p.avance_depart_toleree = 1
        p.save()
        tard = self.depart(heure=23)
        tard.heure = datetime.time(23, 59)
        tard.save()
        if timezone_maintenant().time() < datetime.time(23, 50):
            with override_settings(CONTROLE_HEURE_DEPART=True), self.assertRaisesMessage(ValidationError, "trop tôt"):
                tard.partir()

    def test_caisse_negative_bloquante_et_transfert_limite(self):
        from apps.comptabilite.models import Compte
        from apps.comptabilite.services import creer_ecriture

        from .models_caisse import ClotureJournee, TransfertFonds, anomalies_du_jour

        Billet(depart=self.depart(), voyageur="V").vendre()                    # 6 000 en caisse
        with self.assertRaisesMessage(ValidationError, "n'a que 6 000"):
            TransfertFonds(origine=self.ca, destination=Journal.objects.get(code="BQ"), montant=10000).envoyer()
        creer_ecriture(self.ca, datetime.date.today(), "Sortie sans fonds",
                       [{"compte": Compte.objects.get_or_create(numero="658", defaults={"intitule": "Charges diverses"})[0],
                         "debit": 9000}, {"compte": Compte.objects.get(numero="5711"), "credit": 9000}])
        bloquants, _ = anomalies_du_jour(datetime.date.today(), ClotureJournee.AGENCE)
        self.assertTrue(any("négative" in b for b in bloquants))
        from . import etats

        self.assertEqual([c["solde"] for c in etats.rapport_agence_a4(datetime.date.today())["caisses_negatives"]], [-3000])

    def test_rapprochement_des_billets_et_car_des_colis(self):
        from . import etats

        jour = datetime.date.today()
        d = self.depart()
        Billet(depart=d, voyageur="Payé hier", date_vente=jour - datetime.timedelta(days=1)).vendre()
        Billet(depart=d, voyageur="Payé ce jour").vendre()
        c = Colis(gare_depart=self.ligne.gare_depart, gare_arrivee=self.ligne.gare_arrivee, expediteur="E", destinataire="D",
                  prix=2500).enregistrer()
        c.charger(d)
        Colis(gare_depart=self.ligne.gare_depart, gare_arrivee=self.ligne.gare_arrivee, expediteur="E", destinataire="D2",
              prix=2500).enregistrer()
        d.partir()
        r = etats.rapport_agence_a4(jour)
        self.assertEqual((r["rapprochement"]["ce_jour"], r["rapprochement"]["avant"]), (6000, 6000))
        self.assertEqual(sorted(x["car"] for x in r["colis"]), ["LT 701 AN", "pas encore chargé"])


def timezone_maintenant():
    from django.utils import timezone

    return timezone.localtime()


class SimulationTests(TestCase):
    """Commande « simulation » : un mois fictif joué par le logiciel, dans un dossier séparé."""

    def test_refusee_hors_dossier_de_simulation(self):
        from django.core.management.base import CommandError

        with self.assertRaisesMessage(CommandError, "simulation"):
            call_command("simulation", jours=1, vehicules=4, salaries=10, echelle=0.1, stdout=io.StringIO())

    def test_deux_jours_a_petite_echelle(self):
        from apps.comptabilite.models import Ecriture
        from apps.garage.models_magasin import ArticleMagasin, MouvementMagasin
        from apps.partenaires.models import Decompte
        from apps.personnel.models import Bulletin

        from .management.commands.simulation import Command

        commande, sortie = Command(), io.StringIO()
        call_command(commande, mois="2026-09", jours=2, vehicules=8, salaries=25, echelle=0.1, forcer=True, stdout=sortie)
        self.assertTrue(all(ok for _, ok in commande.controles), commande.controles)
        self.assertGreater(Billet.objects.count(), 0)
        self.assertEqual(Depart.objects.exclude(statut=Depart.ARRIVE).count(), 0)
        self.assertEqual(Bulletin.objects.count(), 25)
        self.assertEqual(Decompte.objects.count(), 2)
        self.assertTrue(MouvementMagasin.objects.filter(sens=MouvementMagasin.SORTIE).exists())
        self.assertEqual(set(Ecriture.objects.values_list("date", flat=True)),
                         {datetime.date(2026, 9, 1), datetime.date(2026, 9, 2)})
        self.assertTrue(ArticleMagasin.objects.filter(quantite__gt=0).exists())
        self.assertIn("Bilan de la simulation", sortie.getvalue())


class DeuxModulesComptablesTests(TestCase):
    """Accueil : « Comptabilité générale » et « Comptabilité analytique », deux logiciels sur une seule comptabilité."""

    def setUp(self):
        from django.contrib.auth import get_user_model

        call_command("init_erp", "--activite", "transport", verbosity=0)
        self.client.force_login(get_user_model().objects.create_superuser("admin", "", "x"))

    def test_deux_modules_au_portail_et_accueil_analytique(self):
        from django.urls import reverse

        from apps.core.navigation import module_pour_chemin

        portail = self.client.get(reverse("core:portail"))
        self.assertContains(portail, "Comptabilité générale")
        self.assertContains(portail, "Comptabilité analytique")
        self.assertContains(portail, 'href="/comptabilite/analytique/"')
        accueil = self.client.get(reverse("analytique:accueil"))
        self.assertEqual(accueil.status_code, 200)
        self.assertContains(accueil, "Comptes d&#x27;exploitation")
        self.assertContains(accueil, "Résultat des véhicules")
        self.assertEqual(self.client.get(reverse("analytique:sections")).status_code, 200)
        # Les états analytiques s'ouvrent dans le module analytique ; la saisie reste en comptabilité générale
        self.assertEqual(module_pour_chemin(reverse("comptabilite:analytique_vehicules")).code, "analytique")
        self.assertEqual(module_pour_chemin(reverse("comptabilite:ecriture_create")).code, "comptabilite")


class PlanAnalytiqueCompletTests(TestCase):
    """Comptabilité analytique : tout le plan analytique (gares, véhicules, propriétaires, gammes, lignes, voyages,
    activités, contrats, plans de sections), chaque élément avec ses états détaillés, sur une période choisie."""

    @classmethod
    def setUpTestData(cls):
        from .management.commands.simulation import Command

        call_command(Command(), mois="2026-09", jours=2, vehicules=8, salaries=30, echelle=0.1, forcer=True,
                     stdout=io.StringIO())
        cls.du, cls.au = datetime.date(2026, 9, 1), datetime.date(2026, 9, 2)

    def setUp(self):
        from django.contrib.auth import get_user_model

        self.client.force_login(get_user_model().objects.create_superuser("chef", "", "x"))

    def test_chaque_axe_se_rapproche_de_la_comptabilite_generale(self):
        from apps.comptabilite import plan_analytique as pa

        codes = [c for c, _, _ in pa.axes()]
        for attendu in ("agences", "points_vente", "villes", "vehicules", "proprietaires", "services", "gammes", "lignes", "voyages", "activites", "contrats"):
            self.assertIn(attendu, codes)
        s = pa.synthese_axes(self.du, self.au)
        self.assertGreater(s["gl"]["produits"], 0)
        for code in codes:
            with self.subTest(axe=code):
                b = pa.balance_axe(code, self.du, self.au)
                self.assertTrue(b["rapproche"], code)
                self.assertEqual(b["gl"]["produits"], s["gl"]["produits"])
        # Tous les produits du transport sont attribués à une gare, un véhicule et une activité
        for code in ("agences", "points_vente", "villes", "vehicules", "activites"):
            self.assertEqual(pa.balance_axe(code, self.du, self.au)["non_affecte"]["produits"], 0, code)

    def test_etats_detailles_d_un_element(self):
        from django.urls import reverse

        from apps.comptabilite import plan_analytique as pa

        gare = pa.balance_axe("agences", self.du, self.au)["elements"][0]
        periode = "du=2026-09-01&au=2026-09-02"
        url = reverse("analytique:element", args=["agences", gare["cle"]])
        for etat, _ in pa.ETATS:
            with self.subTest(etat=etat):
                r = self.client.get(f"{url}?{periode}&etat={etat}&axe2=vehicules")
                self.assertEqual(r.status_code, 200)
                self.assertContains(r, gare["libelle"])
        croise = pa.etat_element("agences", gare["cle"], "croise", self.du, self.au, axe2="vehicules")
        self.assertEqual(sum(g["resultat"] for g in croise["croise"]), gare["resultat"])     # rien ne se perd
        export = self.client.get(f"{url}?{periode}&etat=grand_livre&export=csv")
        self.assertEqual(export["Content-Type"], "text/csv; charset=utf-8")
        self.assertEqual(len(export.content.decode("utf-8-sig").strip().splitlines()) - 1, gare["lignes"])
        for page in (reverse("analytique:plan"), reverse("analytique:axe", args=["vehicules"]),
                     reverse("analytique:element", args=["agences", "aucun"]), reverse("analytique:accueil")):
            self.assertEqual(self.client.get(f"{page}?{periode}").status_code, 200, page)
        # Période en un clic
        self.assertEqual(self.client.get(reverse("analytique:plan") + "?periode=mois_precedent").status_code, 200)
        self.assertEqual(self.client.get(reverse("analytique:axe", args=["inconnu"])).status_code, 404)

    def test_periodes_rapides(self):
        from apps.comptabilite.plan_analytique import periode, periode_precedente

        j = datetime.date(2026, 10, 26)
        self.assertEqual(periode({"periode": "semaine"}, j)[:2], (datetime.date(2026, 10, 26), datetime.date(2026, 11, 1)))
        self.assertEqual(periode({"periode": "mois_precedent"}, j)[:2], (datetime.date(2026, 9, 1), datetime.date(2026, 9, 30)))
        self.assertEqual(periode({"periode": "trimestre"}, j)[:2], (datetime.date(2026, 10, 1), datetime.date(2026, 12, 31)))
        self.assertEqual(periode({"du": "2026-09-01", "au": "2026-09-15"}, j)[:2], (datetime.date(2026, 9, 1), datetime.date(2026, 9, 15)))
        self.assertEqual(periode_precedente(datetime.date(2026, 9, 1), datetime.date(2026, 9, 30)),
                         (datetime.date(2026, 8, 1), datetime.date(2026, 8, 31)))

    def test_societe_de_commerce_sections_seulement(self):
        from apps.comptabilite import plan_analytique as pa
        from apps.comptabilite.models import SectionAnalytique
        from apps.core.models import Societe
        from apps.core.navigation import MODULES_PAR_CODE, structure_module

        Societe.objects.update(activite=Societe.ACTIVITE_COMMERCE)
        SectionAnalytique.objects.create(plan="Services", code="SV-VTE", intitule="Service des ventes")
        codes = [c for c, _, _ in pa.axes()]
        self.assertNotIn("vehicules", codes)
        self.assertIn("plan-services", codes)
        onglets, _ = structure_module(MODULES_PAR_CODE["analytique"])
        tout = str(onglets)
        self.assertNotIn("analytique.vehicules", tout)
        self.assertIn("analytique.axes.plan-services", tout)

    def test_services_periodes_journal_et_reporting_identique(self):
        from django.urls import reverse

        from apps.comptabilite import plan_analytique as pa
        from apps.comptabilite.models import LigneEcriture

        from . import reporting

        # Services : la paie hors véhicule porte la section de son service ; l'axe se rapproche de la générale
        self.assertTrue(LigneEcriture.objects.filter(section__code__startswith="SV-", compte__numero__startswith="66").exists())
        services = pa.balance_axe("services", self.du, self.au)
        self.assertTrue(services["rapproche"])
        self.assertTrue({"BILLETTERIE", "CONDUITE"} <= {e["cle"] for e in services["elements"]})
        # Reporting = état analytique, au franc près, même période
        vehicules = {e["libelle"].split(" — ")[0]: e for e in pa.balance_axe("vehicules", self.du, self.au)["elements"]}
        for l in reporting.comparer("vehicule", (self.du, self.au), (self.du, self.au))["lignes"]:
            if l["libelle"] in vehicules:
                self.assertEqual((l["a"]["produits"], l["a"]["charges"]),
                                 (vehicules[l["libelle"]]["produits"], vehicules[l["libelle"]]["charges"]), l["libelle"])
        # Périodes : Du > Au refusé, ← →, N-1, mois choisi
        p = pa.lire_periode({"du": "2026-09-30", "au": "2026-09-01"})
        self.assertTrue(p["erreur"])
        self.assertEqual(pa.decaler(datetime.date(2026, 9, 1), datetime.date(2026, 9, 30), -1),
                         (datetime.date(2026, 8, 1), datetime.date(2026, 8, 31)))
        self.assertEqual(pa.decaler(datetime.date(2026, 9, 1), datetime.date(2026, 9, 7), 1),
                         (datetime.date(2026, 9, 8), datetime.date(2026, 9, 14)))
        self.assertEqual(pa.annee_precedente(datetime.date(2028, 2, 29), datetime.date(2028, 2, 29)),
                         (datetime.date(2027, 2, 28), datetime.date(2027, 2, 28)))
        self.assertEqual(pa.periode({"mois": "2026-02"})[:2], (datetime.date(2026, 2, 1), datetime.date(2026, 2, 28)))
        r = self.client.get(reverse("analytique:plan") + "?du=2026-09-30&au=2026-09-01")
        self.assertContains(r, "La date de début est après la date de fin")
        # Journal des imputations : chaque ligne avec ses autres axes ; comparaison N-1 ; classement
        gare = pa.balance_axe("agences", self.du, self.au)["elements"][0]
        url = reverse("analytique:element", args=["agences", gare["cle"]])
        j = self.client.get(f"{url}?du=2026-09-01&au=2026-09-02&etat=journal")
        self.assertContains(j, "Véhicules")
        self.assertEqual(len(j.context["journal"]), gare["lignes"])
        self.assertEqual(self.client.get(f"{url}?du=2026-09-01&au=2026-09-02&etat=comparaison&comparer=n1").context[
            "periode_precedente"], (datetime.date(2025, 9, 1), datetime.date(2025, 9, 2)))
        classe = self.client.get(reverse("analytique:axe", args=["vehicules"]) + "?du=2026-09-01&au=2026-09-02&tri=resultat")
        resultats = [e["resultat"] for e in classe.context["elements"]]
        self.assertEqual(resultats, sorted(resultats, reverse=True))


class AgencesPointsDeVenteTests(TestCase):
    """Agences de voyage (plusieurs par grande ville) et points de vente rattachés : la recette d'un départ revient à
    l'agence qui l'exploite, et se répartit entre les points qui ont vendu les billets."""

    def test_recette_repartie_selon_le_point_de_vente(self):
        from django.core.exceptions import ValidationError

        from apps.comptabilite import plan_analytique as pa

        call_command("init_erp", "--activite", "transport", verbosity=0)
        dla = Gare.objects.create(code="DLA", nom="Agence de Douala Akwa", ville="Douala")
        bonaberi = Gare.objects.create(code="DLA2", nom="Agence de Douala Bonabéri", ville="Douala")
        pv = Gare(code="PK14", nom="Point de vente PK14", ville="Douala", type_gare=Gare.POINT_VENTE)
        with self.assertRaises(ValidationError):
            pv.full_clean()                                               # rattachement obligatoire
        pv.rattachement = dla
        pv.full_clean()
        pv.save()
        yde = Gare.objects.create(code="YDE", nom="Agence de Yaoundé", ville="Yaoundé")
        ligne = Ligne.objects.create(code="DLA-YDE", gare_depart=dla, gare_arrivee=yde, prix_billet=6000)
        car = Vehicule.objects.create(immatriculation="LT 900 PV", nombre_places=30)
        jour = datetime.date.today()
        d = Depart.objects.create(ligne=ligne, date=jour, heure=datetime.time(6), vehicule=car,
                                  chauffeur=Chauffeur.objects.create(nom="Chauffeur"))
        for k, gare in enumerate((dla, dla, pv)):
            Billet(depart=d, voyageur=f"V{k}", gare=gare).vendre()
        d.partir()
        points = {e["cle"]: e["produits"] for e in pa.balance_axe("points_vente", jour, jour)["elements"]}
        self.assertEqual(points, {dla.pk: 12000, pv.pk: 6000})
        agences = pa.balance_axe("agences", jour, jour)
        self.assertEqual({e["cle"]: e["produits"] for e in agences["elements"]}, {dla.pk: 18000})
        self.assertTrue(agences["rapproche"])
        villes = pa.balance_axe("villes", jour, jour)
        self.assertEqual({e["cle"]: e["produits"] for e in villes["elements"]}, {"Douala": 18000})
        self.assertEqual(pa.libelles("points_vente", [pv.pk])[pv.pk], "PK14 — Point de vente PK14 (rattaché à DLA)")
        # Fiche du point de vente : sa part seulement, détaillée par véhicule
        e = pa.etat_element("points_vente", pv.pk, "croise", jour, jour, axe2="vehicules")
        self.assertEqual((e["total"]["produits"], [g["produits"] for g in e["croise"]]), (6000, [6000]))
        self.assertTrue(bonaberi.pk not in points)
