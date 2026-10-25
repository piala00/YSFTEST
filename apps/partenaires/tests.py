import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.commercial.models import Tiers
from apps.comptabilite.models import Journal, LigneEcriture
from apps.transport import etats
from apps.transport.models import Billet, Chauffeur, Depart, DepenseVehicule, Gare, Ligne, Vehicule

from .models import ContratPartenaire, Decompte, ReglementPartenaire, solde_partenaire


class PartenairesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        dla = Gare.objects.create(code="DLA", nom="Gare de Douala", ville="Douala")
        yde = Gare.objects.create(code="YDE", nom="Gare de Yaoundé", ville="Yaoundé")
        cls.ligne = Ligne.objects.create(code="DLA-YDE", gare_depart=dla, gare_arrivee=yde, prix_billet=10000)
        cls.car = Vehicule.objects.create(immatriculation="LT 500 PP", designation="Car partenaire", nombre_places=10)
        cls.proprio = Tiers.objects.create(code="PROPRIO1", nom="Propriétaire Un", type_tiers=Tiers.FOURNISSEUR)
        cls.chauffeur = Chauffeur.objects.create(nom="Chauffeur")
        cls.jour = datetime.date.today()
        cls.debut_mois = cls.jour.replace(day=1)

    def activite(self, billets=3, carburant=5000, assurance=2000):
        d = Depart.objects.create(ligne=self.ligne, date=self.jour, heure=datetime.time(6), vehicule=self.car, chauffeur=self.chauffeur)
        for n in range(billets):
            Billet(depart=d, voyageur=f"V{n}").vendre()
        d.partir()
        caisse = Journal.objects.get(code="CA")
        DepenseVehicule(vehicule=self.car, nature=DepenseVehicule.CARBURANT, montant=carburant, caisse=caisse).enregistrer()
        DepenseVehicule(vehicule=self.car, nature=DepenseVehicule.ASSURANCE, montant=assurance, caisse=caisse).enregistrer()

    def contrat(self, **champs):
        valeurs = {"vehicule": self.car, "partenaire": self.proprio, "modele": ContratPartenaire.COMMISSION,
                   "debut": self.debut_mois, "taux_commission": Decimal("20")}
        valeurs.update(champs)
        return ContratPartenaire.objects.create(**valeurs).activer()

    def test_commission_sur_recettes(self):
        self.activite()                                           # recettes 30 000, carburant 5 000, assurance 2 000
        c = self.contrat()
        self.assertTrue(c.numero.startswith("CTP"))
        self.assertEqual(Vehicule.objects.get(pk=self.car.pk).proprietaire, self.proprio)
        d = Decompte.calculer(c, self.debut_mois, self.jour)
        # 30 000 - 20 % (6 000) - carburant à sa charge (5 000) ; l'assurance (« autres ») reste à l'agence
        self.assertEqual((d.recettes, d.commission, d.depenses, d.montant_du), (30000, 6000, 5000, 19000))
        self.assertEqual(d.detail["version"], 1)
        self.assertIsNone(d.ecriture)
        d.approuver()
        self.assertEqual(solde_partenaire(self.proprio), 19000)
        ligne = d.ecriture.lignes.get(debit=19000)
        self.assertEqual((ligne.compte.numero, ligne.vehicule), ("622", self.car))
        # résultat du véhicule pour l'agence : 30 000 - 5 000 - 2 000 - 19 000 = 4 000
        l = next(l for l in etats.balance_vehicules(self.debut_mois, self.jour) if l["vehicule"] == self.car)
        self.assertEqual(l["recettes"] - l["depenses"], 4000)
        with self.assertRaisesMessage(ValidationError, "déjà dans le décompte"):
            Decompte.calculer(c, self.debut_mois, self.jour)      # une période ne se décompte qu'une fois

    def test_reglements_partiels_et_releve(self):
        self.activite()
        d = Decompte.calculer(self.contrat(), self.debut_mois, self.jour).approuver()
        caisse = Journal.objects.get(code="CA")
        ReglementPartenaire(partenaire=self.proprio, decompte=d, montant=10000, caisse=caisse).enregistrer()
        self.assertEqual(solde_partenaire(self.proprio), 9000)
        ReglementPartenaire(partenaire=self.proprio, decompte=d, montant=9000, caisse=caisse).enregistrer()
        self.assertEqual(solde_partenaire(self.proprio), 0)
        with self.assertRaises(ValidationError):
            ReglementPartenaire(partenaire=self.proprio, montant=0, caisse=caisse).enregistrer()
        # le paiement ne change pas le résultat du véhicule
        l = next(l for l in etats.balance_vehicules(self.debut_mois, self.jour) if l["vehicule"] == self.car)
        self.assertEqual(l["recettes"] - l["depenses"], 4000)

    def test_location_forfaitaire_au_prorata(self):
        self.activite()
        c = self.contrat(modele=ContratPartenaire.LOCATION, taux_commission=0, montant_location=Decimal("3000"),
                         periodicite=ContratPartenaire.JOUR, charge_carburant=False)
        d = Decompte.calculer(c, self.debut_mois, self.jour)
        jours = (self.jour - self.debut_mois).days + 1
        self.assertEqual((d.location, d.depenses, d.montant_du, d.commission), (3000 * jours, 0, 3000 * jours, 0))

    def test_depenses_superieures_au_du(self):
        self.activite(billets=1, carburant=9000)                  # 10 000 - 20 % - 9 000 = -1 000 : il doit à l'agence
        d = Decompte.calculer(self.contrat(), self.debut_mois, self.jour).approuver()
        self.assertEqual(d.montant_du, -1000)
        self.assertEqual(solde_partenaire(self.proprio), -1000)

    def test_avenant_versionne_sans_ecraser(self):
        c = self.contrat(debut=self.jour - datetime.timedelta(days=40))
        nouveau = c.avenant(self.jour, taux_commission=Decimal("25"))
        c.refresh_from_db()
        self.assertEqual((c.statut, c.fin, c.taux_commission), (ContratPartenaire.CLOS, self.jour - datetime.timedelta(days=1), 20))
        self.assertEqual((nouveau.numero, nouveau.version, nouveau.taux_commission, nouveau.statut),
                         (c.numero, 2, 25, ContratPartenaire.ACTIF))
        self.activite()
        d = Decompte.calculer(nouveau, self.debut_mois, self.jour)
        self.assertEqual((d.debut, d.commission, d.detail["version"]), (self.jour, 7500, 2))

    def test_contrats_qui_se_chevauchent_refuses(self):
        self.contrat()
        autre = ContratPartenaire.objects.create(vehicule=self.car, partenaire=self.proprio, debut=self.jour,
                                                 modele=ContratPartenaire.COMMISSION, taux_commission=10)
        with self.assertRaisesMessage(ValidationError, "déjà un contrat"):
            autre.activer()

    def test_ecrans(self):
        self.client.force_login(get_user_model().objects.create_superuser("admin", "a@example.com", "x"))
        self.activite()
        r = self.client.post(reverse("partenaires:contrats"), {
            "vehicule": self.car.pk, "partenaire": self.proprio.pk, "modele": "COMMISSION", "debut": self.debut_mois.isoformat(),
            "taux_commission": "20", "montant_location": "0", "periodicite": "MOIS", "charge_carburant": "on"})
        self.assertEqual(r.status_code, 302)
        c = ContratPartenaire.objects.get()
        self.client.post(reverse("partenaires:contrats"), {"action": "activer", "contrat": c.pk})
        self.client.post(reverse("partenaires:decomptes"), {"action": "calculer", "contrat": c.pk,
                                                            "debut": self.debut_mois.isoformat(), "fin": self.jour.isoformat()})
        d = Decompte.objects.get()
        self.client.post(reverse("partenaires:decomptes"), {"action": "approuver", "decompte": d.pk})
        r = self.client.post(reverse("partenaires:releve", args=[self.proprio.pk]), {
            "decompte": d.pk, "montant": "5000", "caisse": Journal.objects.get(code="CA").pk})
        self.assertEqual(solde_partenaire(self.proprio), 14000)
        for url in (reverse("partenaires:contrats"), reverse("partenaires:decomptes"), reverse("partenaires:releves"),
                    reverse("partenaires:releve", args=[self.proprio.pk])):
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertContains(self.client.get(reverse("partenaires:releve", args=[self.proprio.pk])), "14")
