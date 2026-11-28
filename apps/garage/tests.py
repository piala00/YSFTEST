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


def _solde(numero):
    return sum((l.debit - l.credit for l in LigneEcriture.objects.filter(compte__numero=numero)), Decimal(0))


class MagasinTests(TestCase):
    """Achat pour le stock (actif) puis sortie (charge du véhicule), achat direct pour un véhicule, immobilisation."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", verbosity=0)
        cls.bus = Vehicule.objects.create(immatriculation="BUS 005", nombre_places=30)
        cls.autre = Vehicule.objects.create(immatriculation="BUS 006", nombre_places=30)
        cls.fournisseur = Tiers.objects.create(code="PIECES", nom="Pièces Auto", type_tiers=Tiers.FOURNISSEUR)

    def achat(self, *lignes, paiement="COMPTE"):
        from .models_magasin import AchatMagasin, LigneAchatMagasin

        a = AchatMagasin.objects.create(fournisseur=self.fournisseur, facture="F-001", paiement=paiement)
        for l in lignes:
            LigneAchatMagasin.objects.create(achat=a, **l)
        return a.valider()

    def test_filtres_en_stock_puis_un_consomme_par_le_bus(self):
        from .models_magasin import ArticleMagasin, sortir

        filtre = ArticleMagasin.objects.create(code="FILT", designation="Filtre à huile", categorie=ArticleMagasin.PIECE)
        self.achat({"destination": "STOCK", "article": filtre, "quantite": 6, "prix_unitaire": 5000})
        filtre.refresh_from_db()
        self.assertEqual((filtre.quantite, filtre.cout_moyen, filtre.valeur), (6, 5000, 30000))
        self.assertEqual((_solde("338"), _solde("401") + _solde("4011"), _solde("624")), (30000, -30000, 0))  # pas de charge à l'achat
        sortir(filtre, 1, self.bus, "Vidange")
        filtre.refresh_from_db()
        self.assertEqual((filtre.quantite, _solde("338"), _solde("624")), (5, 25000, 5000))
        charge = LigneEcriture.objects.get(compte__numero="624")
        self.assertEqual(charge.vehicule, self.bus)
        with self.assertRaisesMessage(ValidationError, "en stock"):
            sortir(filtre, 10, self.bus)

    def test_cout_moyen_pondere(self):
        from .models_magasin import ArticleMagasin

        pneu = ArticleMagasin.objects.create(code="PNEU", designation="Pneu 315/80", categorie=ArticleMagasin.PNEU)
        self.achat({"destination": "STOCK", "article": pneu, "quantite": 2, "prix_unitaire": 100000})
        self.achat({"destination": "STOCK", "article": pneu, "quantite": 2, "prix_unitaire": 120000})
        pneu.refresh_from_db()
        self.assertEqual((pneu.quantite, pneu.cout_moyen), (4, 110000))

    def test_achat_direct_pour_un_vehicule_et_immobilisation(self):
        from apps.comptabilite.models import Compte

        self.achat({"destination": "VEHICULE", "designation": "Rétroviseur", "quantite": 1, "prix_unitaire": 15000, "vehicule": self.autre},
                   {"destination": "IMMOBILISATION", "designation": "Imprimante", "quantite": 1, "prix_unitaire": 250000})
        self.assertEqual(LigneEcriture.objects.get(compte__numero="624").vehicule, self.autre)
        self.assertEqual(_solde("244"), 250000)                                  # actif, pas une charge
        with self.assertRaisesMessage(ValidationError, "classe 2"):
            self.achat({"destination": "IMMOBILISATION", "designation": "X", "quantite": 1, "prix_unitaire": 1,
                        "compte": Compte.objects.get_or_create(numero="605", defaults={"intitule": "x"})[0]})

    def test_emballages_pour_le_courrier_sans_vehicule(self):
        from .models_magasin import ArticleMagasin, sortir

        ruban = ArticleMagasin.objects.create(code="RUBAN", designation="Ruban adhésif", categorie=ArticleMagasin.EMBALLAGE)
        self.achat({"destination": "STOCK", "article": ruban, "quantite": 10, "prix_unitaire": 1000})
        sortir(ruban, 3, motif="Emballage des colis")
        self.assertEqual((_solde("335"), _solde("608")), (7000, 3000))

    def test_piece_du_magasin_sur_une_reparation(self):
        from .models_magasin import ArticleMagasin

        plaquette = ArticleMagasin.objects.create(code="PLAQ", designation="Plaquettes de frein")
        self.achat({"destination": "STOCK", "article": plaquette, "quantite": 4, "prix_unitaire": 8000})
        ordre = OrdreReparation.objects.create(vehicule=self.bus, panne="Freins")
        LigneReparation.objects.create(ordre=ordre, nature=LigneReparation.MAGASIN, article=plaquette, designation="Plaquettes",
                                       quantite=2, prix_unitaire=8000)
        LigneReparation.objects.create(ordre=ordre, nature=LigneReparation.MAIN_OEUVRE_EXTERNE, designation="Pose",
                                       quantite=1, prix_unitaire=5000)
        ordre.cloturer(caisse=Journal.objects.get(code="CA"))
        plaquette.refresh_from_db()
        self.assertEqual((plaquette.quantite, _solde("338")), (2, 16000))
        lignes_bus = LigneEcriture.objects.filter(vehicule=self.bus, compte__numero="624")
        self.assertEqual(sum(l.debit for l in lignes_bus), 16000 + 5000)          # pièces au coût moyen + pose

    def test_ecrans(self):
        from django.contrib.auth import get_user_model
        from django.urls import reverse

        from .models_magasin import ArticleMagasin

        self.client.force_login(get_user_model().objects.create_superuser("admin", "a@example.com", "x"))
        self.client.post(reverse("garage:magasin_stock"), {"code": "CART", "designation": "Carton", "categorie": "EMBALLAGE"})
        carton = ArticleMagasin.objects.get(code="CART")
        self.client.post(reverse("garage:magasin_achat"), {"fournisseur": self.fournisseur.pk, "paiement": "COMPTE",
                                                           "destination_0": "STOCK", "article_0": carton.pk, "quantite_0": "50",
                                                           "prix_0": "200"})
        carton.refresh_from_db()
        self.assertEqual(carton.quantite, 50)
        self.client.post(reverse("garage:magasin_sorties"), {"article": carton.pk, "quantite": "5"})
        carton.refresh_from_db()
        self.assertEqual(carton.quantite, 45)
        for nom in ("magasin_stock", "magasin_achats", "magasin_achat", "magasin_sorties"):
            self.assertEqual(self.client.get(reverse(f"garage:{nom}")).status_code, 200, nom)
