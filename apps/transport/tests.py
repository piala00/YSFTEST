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
        self.assertEqual(solde("70611"), -6000)
        self.assertEqual(b.ecriture.lignes.get(compte__numero="70611").section, self.dla.section)
        with self.assertRaisesMessage(ValidationError, "déjà vendu"):
            Billet(depart=d, voyageur="Voyageur Deux", siege=1).vendre()

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
        self.assertEqual(solde("70611"), -1000)                               # la retenue reste un produit
        self.assertEqual(Depart.objects.get(pk=b.depart_id).places_vendues, 0)
        with self.assertRaises(ValidationError):
            b.annuler()

    def test_report_sur_un_autre_depart(self):
        d1, d2 = self.depart(), self.depart()
        b = Billet(depart=d1, voyageur="Voyageur", siege=2).vendre()
        b.reporter(d2, siege=3)
        self.assertEqual((b.depart, b.siege), (d2, 3))
        self.assertEqual(solde("5711"), 6000)                                 # aucune écriture de plus

    def test_cycle_du_depart_et_des_colis(self):
        d = self.depart()
        b = Billet(depart=d, voyageur="Voyageur").vendre()
        c = Colis(gare_depart=self.dla, gare_arrivee=self.yde, expediteur="Exp", destinataire="Dest", poids=30).enregistrer()
        self.assertEqual(c.prix, 3000)                                        # 30 kg × 100, au-dessus du forfait
        self.assertEqual(len(c.code_retrait), 6)
        self.assertEqual(solde("70612"), -3000)
        c.charger(d)
        d.partir()
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
        self.assertEqual(solde("4718"), -50000)                               # dû à l'expéditeur
        c.reverser_contre_remboursement()
        self.assertEqual(solde("4718"), 0)
        self.assertEqual(solde("5711"), 2000)
        with self.assertRaises(ValidationError):
            c.reverser_contre_remboursement()

    def test_fret_et_annulation_colis(self):
        c = Colis(nature=Colis.FRET, gare_depart=self.dla, gare_arrivee=self.yde, expediteur="Usine", destinataire="Dépôt",
                  prix=150000).enregistrer()
        self.assertEqual(solde("70613"), -150000)
        c.annuler()
        self.assertEqual(solde("70613"), 0)
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
        b = Billet(depart=self.depart(), voyageur="V", prix=11925).vendre()
        self.assertEqual(b.ecriture.lignes.get(compte__numero="70611").credit, 10000)
        self.assertEqual(b.ecriture.lignes.get(compte__numero="4431").credit, 1925)

    def test_comptes_crees_au_premier_usage(self):
        ParametresTransport.get()
        for numero in ("70611", "70612", "70613", "4718"):
            self.assertTrue(Compte.objects.filter(numero=numero).exists())


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

        self.assertContains(self.client.get(reverse("core:portail")), "Transport de voyageurs")
        Societe.objects.update(activite=Societe.ACTIVITE_COMMERCE)
        self.assertNotContains(self.client.get(reverse("core:portail")), "Transport de voyageurs")

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
