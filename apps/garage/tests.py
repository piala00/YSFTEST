import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase

from apps.commercial.models import Tiers
from apps.comptabilite.models import Journal, LigneEcriture
from apps.transport.models import Vehicule

from .models import LigneReparation, OrdreReparation, PleinCarburant


def solde_vehicule(vehicule, prefixe):
    return sum((l.debit - l.credit for l in LigneEcriture.objects.filter(vehicule=vehicule, compte__numero__startswith=prefixe)),
               Decimal(0))


class GarageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", verbosity=0)
        cls.car = Vehicule.objects.create(immatriculation="LT 1", nombre_places=30)
        cls.caisse = Journal.objects.get(code="CA")
        cls.station = Tiers.objects.create(code="STATION", nom="Station fictive", type_tiers=Tiers.FOURNISSEUR)

    def test_pleins_et_consommation(self):
        j = datetime.date(2026, 3, 1)
        PleinCarburant(vehicule=self.car, date=j, litres=200, prix_litre=840, kilometrage=10000, caisse=self.caisse).enregistrer()
        p2 = PleinCarburant(vehicule=self.car, date=j + datetime.timedelta(days=2), litres=100, prix_litre=840, kilometrage=10400,
                            paiement="COMPTE", fournisseur=self.station).enregistrer()
        self.assertEqual(p2.montant, 84000)
        self.assertEqual(p2.consommation(), Decimal("25.0"))                  # 100 L pour 400 km
        self.assertEqual(p2.ecriture.journal.code, "AC")
        self.assertEqual(p2.ecriture.lignes.get(credit=84000).tiers, self.station)
        self.assertEqual(solde_vehicule(self.car, "6053"), 252000)
        with self.assertRaisesMessage(ValidationError, "Compteur inférieur"):
            PleinCarburant(vehicule=self.car, date=j + datetime.timedelta(days=3), litres=10, prix_litre=840, kilometrage=9000,
                           caisse=self.caisse).enregistrer()

    def test_reparation_cloturee_sur_le_vehicule(self):
        o = OrdreReparation.objects.create(vehicule=self.car, panne="Embrayage", date_entree=datetime.date(2026, 3, 1))
        LigneReparation.objects.create(ordre=o, designation="Disque d'embrayage", quantite=1, prix_unitaire=85000)
        LigneReparation.objects.create(ordre=o, nature=LigneReparation.MAIN_OEUVRE_EXTERNE, designation="Soudure",
                                       prix_unitaire=15000, paiement="COMPTE", fournisseur=self.station)
        LigneReparation.objects.create(ordre=o, nature=LigneReparation.MAIN_OEUVRE_INTERNE, designation="Mécanicien", prix_unitaire=10000)
        self.assertEqual((o.cout, o.cout_comptabilise), (110000, 100000))
        o.cloturer(caisse=self.caisse, date=datetime.date(2026, 3, 3))
        self.assertEqual((o.statut, o.immobilisation_jours), (OrdreReparation.CLOTURE, 2))
        self.assertEqual(solde_vehicule(self.car, "624"), 100000)            # main d'œuvre interne : déjà dans la paie
        self.assertEqual(o.ecriture.lignes.get(credit=15000).tiers, self.station)
        with self.assertRaises(ValidationError):
            o.cloturer(caisse=self.caisse)
