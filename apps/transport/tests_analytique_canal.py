import datetime
from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.comptabilite.plan_analytique import balance_axe, axes
from .models import Billet, Chauffeur, Colis, Depart, Gare, Ligne, Vehicule


@override_settings(CONTROLE_HEURE_DEPART=False)
class CanalVenteAnalytiqueTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", verbosity=0)
        cls.dla = Gare.objects.create(code="CAN-DLA", nom="Gare de Douala CAN", ville="Douala")
        cls.yde = Gare.objects.create(code="CAN-YDE", nom="Gare de Yaoundé CAN", ville="Yaoundé")
        cls.ligne = Ligne.objects.create(code="CAN-DLA-YDE", gare_depart=cls.dla, gare_arrivee=cls.yde,
                                         prix_billet=10000, colis_forfait=1000, colis_prix_kg=100)
        cls.vehicule = Vehicule.objects.create(immatriculation="CAN-001", designation="Car recette CAN", nombre_places=30)
        cls.chauffeur = Chauffeur.objects.create(nom="Chauffeur CAN")

    def depart(self):
        return Depart.objects.create(ligne=self.ligne, date=timezone.localdate(), heure=datetime.time(8, 0),
                                     vehicule=self.vehicule, chauffeur=self.chauffeur)

    def balance(self):
        jour = timezone.localdate()
        return balance_axe("canaux_vente", jour, jour)

    def test_canaux_billets_et_colis_payes_ventiles_sans_double_comptage(self):
        self.assertIn("canaux_vente", {code for code, _, _ in axes()})
        depart = self.depart()
        Billet(depart=depart, voyageur="Vente Web", prix=10000, canal_vente="WEB").vendre()
        Billet(depart=depart, voyageur="Vente application", prix=20000, canal_vente="APP").vendre()
        Billet(depart=depart, voyageur="Vente guichet", prix=5000).vendre()
        colis = Colis(gare_depart=self.dla, gare_arrivee=self.yde, expediteur="Expéditeur", destinataire="Destinataire",
                      prix=3000, canal_vente="REVENDEUR").enregistrer()
        colis.charger(depart)
        depart.partir()

        resultat = self.balance()
        montants = {ligne["cle"]: ligne["produits"] for ligne in resultat["elements"]}
        self.assertEqual(montants["WEB"], Decimal("10000"))
        self.assertEqual(montants["APP"], Decimal("20000"))
        self.assertEqual(montants["GUICHET"], Decimal("5000"))
        self.assertEqual(montants["REVENDEUR"], Decimal("3000"))
        self.assertTrue(resultat["rapproche"])
        self.assertEqual(resultat["total_elements"]["produits"] + resultat["non_affecte"]["produits"],
                         resultat["gl"]["produits"])

    def test_croisement_points_vente_canaux_reste_exact_sur_les_pieces_sources(self):
        from apps.comptabilite.plan_analytique import etat_element

        point = Gare.objects.create(
            code="CAN-PDV", nom="Point de vente Douala", ville="Douala",
            type_gare=Gare.POINT_VENTE, rattachement=self.dla,
        )
        depart = self.depart()
        Billet(depart=depart, gare=self.dla, voyageur="Vente Web agence", prix=10000, canal_vente="WEB").vendre()
        Billet(depart=depart, gare=point, voyageur="Vente application point", prix=20000, canal_vente="APP").vendre()
        depart.partir()
        jour = timezone.localdate()

        par_point = etat_element("points_vente", point.pk, "croise", jour, jour, axe2="canaux_vente")
        self.assertTrue(par_point["croise_disponible"])
        self.assertEqual(
            {ligne["cle"]: ligne["produits"] for ligne in par_point["croise"]},
            {"APP": Decimal("20000")},
        )
        self.assertEqual(par_point["total"]["produits"], Decimal("20000"))

        par_canal = etat_element("canaux_vente", "APP", "croise", jour, jour, axe2="points_vente")
        self.assertTrue(par_canal["croise_disponible"])
        self.assertEqual(
            {ligne["cle"]: ligne["produits"] for ligne in par_canal["croise"]},
            {point.pk: Decimal("20000")},
        )
        self.assertEqual(par_canal["total"]["produits"], Decimal("20000"))

    def test_port_du_a_la_livraison_conserve_le_canal_source(self):
        depart = self.depart()
        colis = Colis(gare_depart=self.dla, gare_arrivee=self.yde, expediteur="Expéditeur", destinataire="Destinataire",
                      prix=4500, port=Colis.DU, canal_vente="WEB").enregistrer()
        colis.charger(depart)
        depart.partir()
        depart.arriver()
        colis.livrer(colis.code_retrait, "Destinataire — CNI 1")

        resultat = self.balance()
        montants = {ligne["cle"]: ligne["produits"] for ligne in resultat["elements"]}
        self.assertEqual(montants["WEB"], Decimal("4500"))
        self.assertTrue(resultat["rapproche"])

    def test_retenue_annulation_billet_conserve_le_canal_source(self):
        billet = Billet(depart=self.depart(), voyageur="Voyageur annulé", prix=10000, canal_vente="APP")
        billet.vendre()
        billet.annuler(retenue=Decimal("1500"))

        resultat = self.balance()
        montants = {ligne["cle"]: ligne["produits"] for ligne in resultat["elements"]}
        self.assertEqual(montants["APP"], Decimal("1500"))
        self.assertTrue(resultat["rapproche"])

    def test_formulaires_exposent_le_canal_et_ancien_defaut_guichet(self):
        from apps.transport.forms import BilletForm, ColisForm

        self.assertEqual(Billet(depart=self.depart(), voyageur="V").canal_vente, "GUICHET")
        self.assertEqual(Colis(gare_depart=self.dla, gare_arrivee=self.yde, expediteur="E", destinataire="D").canal_vente,
                         "GUICHET")
        self.assertIn("canal_vente", BilletForm().fields)
        self.assertIn("canal_vente", ColisForm().fields)
        self.assertFalse(BilletForm().fields["canal_vente"].required)
        self.assertFalse(ColisForm().fields["canal_vente"].required)

    def test_serialisation_echanges_transporte_le_canal(self):
        from apps.echanges.contrats import serialiser

        billet = Billet(depart=self.depart(), voyageur="Voyageur Web", prix=8000, canal_vente="WEB").vendre()
        colis = Colis(gare_depart=self.dla, gare_arrivee=self.yde, expediteur="E", destinataire="D", prix=2000,
                      canal_vente="REVENDEUR").enregistrer()
        self.assertEqual(serialiser(billet)[1]["canal_vente"], "WEB")
        self.assertEqual(serialiser(colis)[1]["canal_vente"], "REVENDEUR")

    def test_colis_paye_recu_d_une_agence_est_ventile_meme_sans_flag_local(self):
        from apps.comptabilite.models import Journal
        from apps.comptabilite.services import creer_ecriture
        from apps.transport.models import ParametresTransport

        depart = self.depart()
        colis = Colis(numero="COL-REMOTE-CAN", site_origine="DLA", nature=Colis.COLIS, date=timezone.localdate(),
                      gare_depart=self.dla, gare_arrivee=self.yde, expediteur="Agence DLA", destinataire="Client",
                      prix=4500, port=Colis.PAYE, canal_vente="REVENDEUR", depart=depart,
                      statut=Colis.EN_ROUTE, recette_constatee=False)
        colis.save()
        p = ParametresTransport.get()
        creer_ecriture(Journal.objects.get(code="OD"), timezone.localdate(), "Recette colis départ distant",
                       [{"compte": p.compte_colis_a_transporter, "debit": 4500},
                        {"compte": p.compte_colis, "credit": 4500, "vehicule": self.vehicule,
                         "section": self.dla.section}],
                       reference=depart.numero, origine=depart.numero)

        resultat = self.balance()
        montants = {ligne["cle"]: ligne["produits"] for ligne in resultat["elements"]}
        self.assertEqual(montants["REVENDEUR"], Decimal("4500"))
        self.assertTrue(resultat["rapproche"])

    def test_annulation_et_livraison_distantes_utilisent_la_reference_de_piece(self):
        from apps.comptabilite.models import Journal
        from apps.comptabilite.services import creer_ecriture
        from apps.transport.models import ParametresTransport

        depart = self.depart()
        maintenant = timezone.now()
        billet = Billet(numero="BIL-REMOTE-CAN", site_origine="DLA", depart=depart, voyageur="Billet annulé distant",
                        prix=10000, retenue=1500, statut=Billet.ANNULE, annule_le=maintenant, canal_vente="APP")
        billet.save()
        colis = Colis(numero="COL-REMOTE-DU", site_origine="DLA", nature=Colis.COLIS, date=timezone.localdate(),
                      gare_depart=self.dla, gare_arrivee=self.yde, expediteur="Agence DLA", destinataire="Client",
                      prix=4500, port=Colis.DU, canal_vente="WEB", depart=depart, statut=Colis.LIVRE,
                      livre_le=maintenant)
        colis.save()
        p = ParametresTransport.get()
        journal = Journal.objects.get(code="OD")
        creer_ecriture(journal, timezone.localdate(), "Retenue billet annulé distant",
                       [{"compte": p.compte_billets_a_voyager, "debit": 1500},
                        {"compte": p.compte_billets, "credit": 1500}],
                       reference=billet.numero, origine=billet.numero)
        creer_ecriture(journal, timezone.localdate(), "Port dû livré dans une agence distante",
                       [{"compte": p.compte_colis_a_transporter, "debit": 4500},
                        {"compte": p.compte_colis, "credit": 4500}],
                       reference=colis.numero, origine=colis.numero)

        resultat = self.balance()
        montants = {ligne["cle"]: ligne["produits"] for ligne in resultat["elements"]}
        self.assertEqual(montants["APP"], Decimal("1500"))
        self.assertEqual(montants["WEB"], Decimal("4500"))
        self.assertTrue(resultat["rapproche"])
