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


class RemunerationsProprietairesTests(TestCase):
    """Skill propriétaires : exemples A (fixe garanti + variable) et B (avance sur variable), retraits, compte séparé."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        cls.car = Vehicule.objects.create(immatriculation="BUS EX 01", nombre_places=30)
        cls.proprio = Tiers.objects.create(code="OWNER1", nom="Propriétaire Exemple", type_tiers=Tiers.FOURNISSEUR)
        cls.debut, cls.fin = datetime.date(2026, 9, 1), datetime.date(2026, 9, 30)

    def activite(self):
        """Produits 1 000 000, frais d'exploitation 400 000 (carburant), sur le véhicule, en septembre."""
        from apps.comptabilite.models import Compte
        from apps.comptabilite.services import creer_ecriture
        from apps.transport.models import ParametresTransport

        p = ParametresTransport.get()
        creer_ecriture(Journal.objects.get(code="OD"), self.fin, "Recettes du mois",
                       [{"compte": p.compte_billets_a_voyager, "debit": 1000000},
                        {"compte": p.compte_billets, "credit": 1000000, "vehicule": self.car}])
        creer_ecriture(Journal.objects.get(code="CA"), self.fin, "Carburant du mois",
                       [{"compte": p.compte_carburant, "debit": 400000, "vehicule": self.car},
                        {"compte": Compte.objects.get(numero="5711"), "credit": 400000}])

    def contrat(self, modele, **champs):
        return ContratPartenaire.objects.create(vehicule=self.car, partenaire=self.proprio, modele=modele, debut=self.debut,
                                                montant_location=Decimal("150000"), taux_proprietaire=Decimal("40"),
                                                **champs).activer()

    def test_exemple_a_fixe_garanti_plus_variable_et_retraits(self):
        from django.contrib.auth import get_user_model

        from apps.transport import analytique

        from .models import DemandeRetrait

        self.activite()
        d = Decompte.calculer(self.contrat(ContratPartenaire.FIXE_PLUS_VARIABLE), self.debut, self.fin)
        self.assertEqual((d.fixe, d.variable, d.montant_du), (150000, 180000, 330000))      # 40 % de (600 000 − 150 000)
        d.approuver()
        self.assertNotEqual(d.ecriture_fixe_id, d.ecriture_id)                               # fixe et variable : deux écritures
        self.assertEqual(d.ecriture.lignes.get(credit=180000).compte.numero, "467")         # compte propriétaire, pas 401
        self.assertEqual(solde_partenaire(self.proprio), 330000)
        g = next(l for l in analytique.vehicules(self.debut, self.fin)["lignes"] if l["vehicule"] == self.car)
        self.assertEqual((g["resultat"], g["proprietaire"], g["resultat_societe"]), (600000, 330000, 270000))
        ca = Journal.objects.get(code="CA")
        ReglementPartenaire(partenaire=self.proprio, decompte=d, montant=150000, caisse=ca).enregistrer()   # fixe versé
        U = get_user_model()
        demandeur, chef = U.objects.create_user("demandeur"), U.objects.create_user("chef")
        r = DemandeRetrait(partenaire=self.proprio, montant=100000).demander(demandeur)      # disponible 180 000
        with self.assertRaisesMessage(ValidationError, "propre retrait"):
            r.decider(True, demandeur)
        r.decider(True, chef)
        r.payer(ca)
        self.assertEqual(solde_partenaire(self.proprio), 80000)
        with self.assertRaisesMessage(ValidationError, "disponible 80 000"):
            DemandeRetrait(partenaire=self.proprio, montant=90000).demander(demandeur)
        self.assertEqual(sum(l.debit - l.credit for l in LigneEcriture.objects.filter(compte__numero="622")), 330000)  # pas de double charge

    def test_exemple_b_avance_imputee_sur_le_variable(self):
        self.activite()
        c = self.contrat(ContratPartenaire.AVANCE_SUR_VARIABLE)
        ReglementPartenaire(partenaire=self.proprio, montant=150000, caisse=Journal.objects.get(code="CA"),
                            nature=ReglementPartenaire.AVANCE).enregistrer()                # avance : pas une charge
        self.assertEqual(solde_partenaire(self.proprio), -150000)
        d = Decompte.calculer(c, self.debut, self.fin).approuver()
        self.assertEqual((d.fixe, d.variable, d.montant_du), (0, 240000, 240000))           # 40 % de 600 000
        self.assertEqual(solde_partenaire(self.proprio), 90000)                              # 240 000 − 150 000
        self.assertEqual(sum(l.debit - l.credit for l in LigneEcriture.objects.filter(compte__numero="622")), 240000)

    def test_marge_negative_et_plancher_contractuel(self):
        from apps.comptabilite.models import Compte
        from apps.comptabilite.services import creer_ecriture
        from apps.transport.models import ParametresTransport

        p = ParametresTransport.get()
        creer_ecriture(Journal.objects.get(code="CA"), self.fin, "Carburant",
                       [{"compte": p.compte_carburant, "debit": 100000, "vehicule": self.car},
                        {"compte": Compte.objects.get(numero="5711"), "credit": 100000}])
        sans = Decompte.calculer(self.contrat(ContratPartenaire.VARIABLE), self.debut, datetime.date(2026, 9, 15))
        self.assertEqual(sans.montant_du, 0)                                                  # carburant du 30 hors période
        c = ContratPartenaire.objects.get()
        avec = Decompte.calculer(c, datetime.date(2026, 9, 16), self.fin)
        self.assertEqual(avec.montant_du, -40000)                                             # sans plancher : dû par le propriétaire
        c2 = c.avenant(datetime.date(2026, 10, 1), plancher_zero=True)
        self.assertTrue(c2.plancher_zero)

    def test_compte_proprietaire_distinct_du_compte_fournisseur(self):
        from apps.comptabilite.models import Compte
        from apps.comptabilite.services import creer_ecriture

        self.activite()
        Decompte.calculer(self.contrat(ContratPartenaire.FIXE_PLUS_VARIABLE), self.debut, self.fin).approuver()
        creer_ecriture(Journal.objects.get(code="OD"), self.fin, "Pièces fournies par le même tiers",
                       [{"compte": Compte.objects.get_or_create(numero="6042", defaults={"intitule": "Matières consommables"})[0],
                         "debit": 50000}, {"compte": self.proprio.get_compte_collectif(), "tiers": self.proprio, "credit": 50000}])
        self.assertEqual(solde_partenaire(self.proprio), 330000)                              # pas de compensation implicite
        fournisseur = sum(l.credit - l.debit for l in LigneEcriture.objects.filter(tiers=self.proprio, compte__numero="4011"))
        self.assertEqual(fournisseur, 50000)

    def test_ecran_releve_avance_et_retrait(self):
        from .models import DemandeRetrait

        self.client.force_login(get_user_model().objects.create_superuser("admin", "a@example.com", "x"))
        self.activite()
        Decompte.calculer(self.contrat(ContratPartenaire.FIXE_PLUS_VARIABLE), self.debut, self.fin).approuver()
        url = reverse("partenaires:releve", args=[self.proprio.pk])
        ca = Journal.objects.get(code="CA").pk
        self.client.post(url, {"action": "payer", "nature": "AVANCE", "montant": "50000", "caisse": ca})
        self.client.post(url, {"action": "retrait", "montant": "100000"})
        r = DemandeRetrait.objects.get()
        self.client.post(url, {"action": "autoriser", "retrait": r.pk})
        self.client.post(url, {"action": "payer_retrait", "retrait": r.pk, "caisse": ca})
        self.assertEqual(solde_partenaire(self.proprio), 330000 - 50000 - 100000)
        page = self.client.get(url)
        for mot in ("FIXE", "VARIABLE", "AVANCE", "RETRAIT", "Disponible pour un retrait"):
            self.assertContains(page, mot)


class CompteDuCamionTests(TestCase):
    """Le propriétaire confie son camion : toutes les recettes vont au compte du camion, moins ses charges ;
    positif, il retire quand il veut ; négatif, les recettes suivantes compensent."""

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        cls.car = Vehicule.objects.create(immatriculation="CAMION 01", nombre_places=30)
        cls.proprio = Tiers.objects.create(code="OWN2", nom="Propriétaire du camion", type_tiers=Tiers.FOURNISSEUR)
        cls.j = datetime.date.today()

    def mouvement(self, jour, recette=0, charge=0):
        from apps.comptabilite.models import Compte
        from apps.comptabilite.services import creer_ecriture
        from apps.transport.models import ParametresTransport

        p = ParametresTransport.get()
        if recette:
            creer_ecriture(Journal.objects.get(code="OD"), jour, "Recettes", [
                {"compte": p.compte_billets_a_voyager, "debit": recette},
                {"compte": p.compte_billets, "credit": recette, "vehicule": self.car}])
        if charge:
            creer_ecriture(Journal.objects.get(code="CA"), jour, "Carburant", [
                {"compte": p.compte_carburant, "debit": charge, "vehicule": self.car},
                {"compte": Compte.objects.get(numero="5711"), "credit": charge}])

    def test_compte_consultable_retraits_et_compensation(self):
        from .models import DemandeRetrait

        j = self.j
        contrat = ContratPartenaire.objects.create(vehicule=self.car, partenaire=self.proprio, modele=ContratPartenaire.COMMISSION,
                                                   debut=j - datetime.timedelta(days=30), taux_commission=0, charge_autres=True,
                                                   charge_equipage=True).activer()
        self.mouvement(j - datetime.timedelta(days=25), recette=1000000, charge=400000)
        en_cours = Decompte.compte_en_cours(contrat, jusqua=j - datetime.timedelta(days=20))
        self.assertEqual((en_cours["recettes"], en_cours["depenses"], en_cours["montant_du"]), (1000000, 400000, 600000))
        self.assertEqual(solde_partenaire(self.proprio), 0)                       # consultable, pas encore disponible
        Decompte.calculer(contrat, en_cours["debut"], en_cours["fin"]).approuver()
        ca = Journal.objects.get(code="CA")
        r = DemandeRetrait(partenaire=self.proprio, montant=600000).demander()
        r.decider(True)
        r.payer(ca)
        self.mouvement(j - datetime.timedelta(days=15), charge=100000)            # réparation, pas de recette
        e = Decompte.compte_en_cours(contrat, jusqua=j - datetime.timedelta(days=10))
        self.assertEqual(e["debut"], j - datetime.timedelta(days=19))             # reprend après le dernier arrêt
        Decompte.calculer(contrat, e["debut"], e["fin"]).approuver()
        self.assertEqual(solde_partenaire(self.proprio), -100000)                 # négatif : il doit attendre
        with self.assertRaises(ValidationError):
            DemandeRetrait(partenaire=self.proprio, montant=1).demander()
        self.mouvement(j - datetime.timedelta(days=5), recette=300000)
        e = Decompte.compte_en_cours(contrat, jusqua=j - datetime.timedelta(days=1))
        Decompte.calculer(contrat, e["debut"], e["fin"]).approuver()
        self.assertEqual(solde_partenaire(self.proprio), 200000)                  # compensé par les recettes suivantes

    def test_salaire_mensuel_fixe(self):
        contrat = ContratPartenaire.objects.create(vehicule=self.car, partenaire=self.proprio, modele=ContratPartenaire.LOCATION,
                                                   debut=datetime.date(2026, 9, 1), montant_location=Decimal("100000"),
                                                   charge_carburant=False, charge_reparations=False, charge_route=False).activer()
        d = Decompte.calculer(contrat, datetime.date(2026, 9, 1), datetime.date(2026, 9, 30)).approuver()
        self.assertEqual(d.montant_du, 100000)

    def test_ecran_arreter_le_compte(self):
        self.client.force_login(get_user_model().objects.create_superuser("admin", "a@example.com", "x"))
        contrat = ContratPartenaire.objects.create(vehicule=self.car, partenaire=self.proprio, modele=ContratPartenaire.COMMISSION,
                                                   debut=self.j - datetime.timedelta(days=5), taux_commission=0).activer()
        self.mouvement(self.j, recette=50000)
        url = reverse("partenaires:releve", args=[self.proprio.pk])
        self.assertContains(self.client.get(url), "Compte du camion CAMION 01 en cours")
        self.client.post(url, {"action": "arreter", "contrat": contrat.pk})
        self.assertEqual(solde_partenaire(self.proprio), 50000)
