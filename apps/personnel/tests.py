import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase

from apps.comptabilite.models import Compte, Journal, LigneEcriture
from apps.transport.models import Vehicule

from .models import Avance, Employe, PeriodePaie, RubriquePaie


def solde(numero, **filtre):
    return sum((l.debit - l.credit for l in LigneEcriture.objects.filter(compte__numero=numero, **filtre)), Decimal(0))


class PaieTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", verbosity=0)
        cls.car = Vehicule.objects.create(immatriculation="LT 1", nombre_places=30)
        cls.caisse = Journal.objects.get(code="CA")

    def test_paie_du_mois(self):
        chauffeur = Employe.objects.create(matricule="E1", nom="Chauffeur Fictif", service=Employe.CONDUITE, vehicule=self.car,
                                           salaire_base=150000)
        guichetiere = Employe.objects.create(matricule="E2", nom="Guichetière Fictive", service=Employe.BILLETTERIE, salaire_base=100000)
        # Rubriques fictives pour l'essai : les taux réels sont à fixer avec l'expert-comptable
        RubriquePaie.objects.create(code="PRIME", libelle="Prime de route", nature=RubriquePaie.GAIN, valeur=20000,
                                    compte=Compte.objects.get(numero="661"))
        RubriquePaie.objects.create(code="RET", libelle="Retenue fictive", nature=RubriquePaie.RETENUE, calcul=RubriquePaie.TAUX,
                                    valeur=10, automatique=True, compte=Compte.objects.get(numero="431"))
        RubriquePaie.objects.create(code="PAT", libelle="Charge patronale fictive", nature=RubriquePaie.PATRONALE,
                                    calcul=RubriquePaie.TAUX, valeur=5, automatique=True, compte=Compte.objects.get(numero="664"),
                                    compte_contrepartie=Compte.objects.get(numero="431"))
        Avance(employe=chauffeur, date=datetime.date(2026, 3, 10), montant=30000, caisse=self.caisse).enregistrer()
        paie = PeriodePaie.objects.create(annee=2026, mois=3)
        self.assertEqual(paie.generer(), 2)
        b = paie.bulletins.get(employe=chauffeur)
        b.lignes.create(rubrique=RubriquePaie.objects.get(code="PRIME"))
        b.calculer()
        self.assertEqual((b.brut, b.retenues, b.avances, b.net, b.patronales), (170000, 17000, 30000, 123000, 8500))
        paie.valider()
        self.assertEqual(solde("421"), 0)                                     # avance reprise
        self.assertEqual(solde("422"), -(123000 + 90000))
        self.assertEqual(solde("661", vehicule=self.car), 170000)            # salaire du chauffeur sur son car
        self.assertEqual(solde("664", vehicule=self.car), 8500)
        self.assertEqual(solde("661", vehicule=None), 100000)
        self.assertEqual(solde("661", employe=chauffeur), 170000)
        self.assertEqual(solde("664", employe=chauffeur), 8500)
        self.assertEqual(solde("661", employe=guichetiere), 100000)
        self.assertEqual(solde("421", employe=chauffeur), 0)
        self.assertEqual(solde("422", employe=chauffeur), -123000)

        from apps.comptabilite.plan_analytique import faits
        mouvements = list(faits(datetime.date(2026, 3, 1), datetime.date(2026, 3, 31)))
        charges_chauffeur = sum((-ligne["montant"] for ligne in mouvements
                                 if ligne["employes"] == chauffeur.pk and not ligne["produit"]), Decimal("0"))
        self.assertEqual(charges_chauffeur, Decimal("178500"))

        from apps.echanges.contrats import ecriture as serialiser_ecriture
        payload = serialiser_ecriture(paie.ecriture)
        employes_serialises = {ligne["employe"]["uid"] for ligne in payload["lignes"] if ligne["employe"]}
        self.assertEqual(employes_serialises, {str(chauffeur.uid), str(guichetiere.uid)})

        with self.assertRaises(ValidationError):
            paie.generer()
        paie.payer(self.caisse)
        self.assertEqual(solde("422"), 0)
        self.assertEqual(solde("422", employe=chauffeur), 0)
        self.assertEqual(solde("422", employe=guichetiere), 0)

    def test_salaire_ventile_sur_vehicule_conserve_le_service_historique(self):
        employe = Employe.objects.create(
            matricule="MEC-01", nom="Mécanicien Fictif", service=Employe.GARAGE,
            vehicule=self.car, salaire_base=50000,
        )
        paie = PeriodePaie.objects.create(annee=2026, mois=4)
        self.assertEqual(paie.generer(), 1)
        paie.valider()

        ligne = paie.ecriture.lignes.get(compte__numero="661")
        self.assertEqual(ligne.vehicule_id, self.car.pk)
        self.assertEqual(ligne.section.plan, "Services")
        self.assertEqual(ligne.section.code, "SV-GARAGE")

        # Une modification ultérieure de la fiche ne doit pas reclasser une paie déjà validée.
        employe.service = Employe.CONDUITE
        employe.save(update_fields=["service"])

        from apps.comptabilite.plan_analytique import balance_axe, faits

        debut, fin = datetime.date(2026, 4, 1), datetime.date(2026, 4, 30)
        mouvements = list(faits(debut, fin))
        charges = [f for f in mouvements if f["employes"] == employe.pk and not f["produit"]]
        self.assertEqual(sum((-f["montant"] for f in charges), Decimal("0")), Decimal("50000"))
        self.assertEqual({f["services"] for f in charges}, {Employe.GARAGE})
        self.assertEqual({f["vehicules"] for f in charges}, {self.car.pk})

        services = balance_axe("services", debut, fin)
        garage = next(e for e in services["elements"] if e["cle"] == Employe.GARAGE)
        self.assertEqual(garage["charges"], Decimal("50000"))
        self.assertTrue(services["rapproche"])

        vehicules = balance_axe("vehicules", debut, fin)
        car = next(e for e in vehicules["elements"] if e["cle"] == self.car.pk)
        self.assertEqual(car["charges"], Decimal("50000"))
        self.assertTrue(vehicules["rapproche"])

