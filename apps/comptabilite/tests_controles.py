"""Contrôles de clôture : tous exécutables, et chaque anomalie provoquée est détectée."""
import datetime

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .controles import executer
from .models import Compte, Journal
from .services import creer_ecriture

DEBUT, FIN = datetime.date(2026, 1, 1), datetime.date(2026, 12, 31)


class ControlesClotureTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", verbosity=0)
        cls.c = {n: Compte.objects.get_or_create(numero=n, defaults={"intitule": n})[0]
                 for n in ("5711000", "4711000", "6222000", "1011000")}

    def statuts(self):
        return {l["titre"]: l["statut"] for g in executer(DEBUT, FIN)["groupes"] for l in g["lignes"]}

    def test_dossier_neuf_tout_est_executable(self):
        statuts = self.statuts()
        self.assertNotIn("erreur", statuts.values(), statuts)
        self.assertEqual(statuts["Écritures au brouillard"], "ok")
        self.assertEqual(statuts["Total des débits = total des crédits"], "ok")

    def test_anomalies_detectees(self):
        od = Journal.objects.get(code="OD")
        jour = datetime.date(2026, 3, 1)
        creer_ecriture(od, jour, "Loyer payé en trop", [{"compte": self.c["6222000"], "debit": 1000},
                                                        {"compte": self.c["5711000"], "credit": 1000}])     # caisse négative
        creer_ecriture(od, jour, "À reclasser", [{"compte": self.c["4711000"], "debit": 500},
                                                 {"compte": self.c["1011000"], "credit": 500}])
        creer_ecriture(od, jour, "Brouillon", [{"compte": self.c["6222000"], "debit": 10},
                                               {"compte": self.c["1011000"], "credit": 10}], valider=False)
        statuts = self.statuts()
        self.assertEqual(statuts["Caisses jamais créditrices"], "anomalie")
        self.assertEqual(statuts["Compte d'attente (471) soldé"], "anomalie")
        self.assertEqual(statuts["Écritures au brouillard"], "anomalie")
        self.assertEqual(executer(DEBUT, FIN)["anomalies"], 3)

    def test_ecran(self):
        self.client.force_login(get_user_model().objects.create_superuser("chef", "", "Chef-2026x"))
        page = self.client.get(reverse("comptabilite:controles_cloture") + "?seul=1")
        self.assertContains(page, "Contrôles de clôture")
        self.assertContains(page, "Conforme")
        self.assertNotContains(page, "Contrôle impossible")
