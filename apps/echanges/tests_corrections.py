"""Demandes de correction : la direction signale une erreur, l'agence corrige ou conteste, le suivi revient à la direction.

Trois dossiers séparés (direction, Douala, Yaoundé) qui ne communiquent que par fichiers d'échange.
"""
import tempfile

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from .scenario import Dossier, lots_de

ECRITURE_DLA = """
import datetime, json
from apps.comptabilite.models import Compte, Journal
from apps.comptabilite.services import creer_ecriture
for n, i in (("6252000", "Assurances"), ("6222000", "Locations de bâtiments"), ("5711000", "Caisse")):
    Compte.objects.get_or_create(numero=n, defaults={{"intitule": i}})
e = creer_ecriture(Journal.objects.get(code="OD"), datetime.date.today(), "{libelle}",
                   [{{"compte": Compte.objects.get(numero="{debit}"), "debit": {montant}}},
                    {{"compte": Compte.objects.get(numero="{credit}"), "credit": {montant}}}])
print(json.dumps(str(e.uid)))"""

ETAT = """
import json
from apps.echanges.models import DemandeCorrection
print(json.dumps({d.numero: [d.statut, len(d.ecritures_correction), d.reponse] for d in DemandeCorrection.objects.order_by("numero")}))"""


class DemandesDeCorrectionTests(SimpleTestCase):
    def test_signaler_corriger_contester_annuler(self):
        with tempfile.TemporaryDirectory() as travail:
            siege, dla, yde = Dossier(travail, "siege"), Dossier(travail, "douala"), Dossier(travail, "yaounde")
            for d in (siege, dla, yde):
                d.creer()
            siege.manage("echanges", "siege", "--code", "SIEGE", "--nom", "Direction")
            siege.manage("echanges", "agence", "--code", "DLA", "--nom", "Agence de Douala")
            siege.manage("echanges", "agence", "--code", "YDE", "--nom", "Agence de Yaoundé")
            for agence, dossier in (("DLA", dla), ("YDE", yde)):
                dossier.manage("echanges", "installer",
                               lots_de(siege.manage("echanges", "installation", "--agence", agence, "--dossier", travail))[0])

            def agence_vers_siege():
                siege.manage("echanges", "importer", lots_de(dla.manage("echanges", "exporter", "--dossier", travail))[0])

            def siege_vers_agences():
                lots = lots_de(siege.manage("echanges", "exporter", "--vers", "tous", "--dossier", travail))
                dla.manage("echanges", "importer", [l for l in lots if "vers-DLA" in l][0])
                yde.manage("echanges", "importer", [l for l in lots if "vers-YDE" in l][0])

            # Douala impute un loyer en assurance (erreur) et passe deux autres pièces
            fausse = dla.py(ECRITURE_DLA.format(libelle="Loyer d'octobre", debit="6252000", credit="5711000", montant=100000))
            dla.py(ECRITURE_DLA.format(libelle="Loyer du dépôt", debit="6222000", credit="5711000", montant=50000))
            dla.py(ECRITURE_DLA.format(libelle="Loyer du garage", debit="6222000", credit="5711000", montant=30000))
            agence_vers_siege()

            # La direction signale les trois pièces (la 2e sera contestée, la 3e annulée)
            demandes = siege.py("""
import json
from django.core.exceptions import ValidationError
from apps.comptabilite.models import Ecriture
from apps.echanges import corrections
recues = list(Ecriture.objects.filter(site_origine="DLA").order_by("id"))
d1 = corrections.demander(recues[0], "Loyer imputé en assurance", "Imputer au 6222000", "chef.comptable")
d2 = corrections.demander(recues[1], "Montant à vérifier", "", "chef.comptable")
d3 = corrections.demander(recues[2], "Doublon ?", "", "chef.comptable")
try:
    corrections.demander(Ecriture.objects.filter(site_origine="").first() or recues[0].__class__(), "x")
    refus = ""
except (ValidationError, AttributeError) as exc:
    refus = "refusée"
corrections.annuler(d3, "chef.comptable", "Pas un doublon")
print(json.dumps({"numeros": [d1.numero, d2.numero, d3.numero], "refus": refus}))""")
            self.assertEqual(demandes["numeros"], ["DC00001", "DC00002", "DC00003"])
            siege_vers_agences()

            # Douala a reçu ses demandes (accusé de réception), Yaoundé rien
            self.assertEqual(dla.py(ETAT), {"DC00001": ["RECUE", 0, ""], "DC00002": ["RECUE", 0, ""],
                                            "DC00003": ["ANNULEE", 0, ""]})
            self.assertEqual(yde.py(ETAT), {})
            # La direction ne peut pas répondre à la place de l'agence ; l'agence ne peut pas annuler
            self.assertEqual(siege.py("""
import json
from django.core.exceptions import ValidationError
from apps.echanges import corrections
from apps.echanges.models import DemandeCorrection
try:
    corrections.repondre(DemandeCorrection.objects.get(numero="DC00001"), "CONTESTEE", "non")
    print(json.dumps("accepté"))
except ValidationError:
    print(json.dumps("refusé"))"""), "refusé")

            # Douala corrige la 1re (extourne + bonne écriture) et conteste la 2e
            dla.py(ECRITURE_DLA.format(libelle="Extourne loyer d'octobre", debit="5711000", credit="6252000", montant=100000))
            dla.py(ECRITURE_DLA.format(libelle="Loyer d'octobre (corrigé)", debit="6222000", credit="5711000", montant=100000))
            reponse = dla.py("""
import json
from django.core.exceptions import ValidationError
from apps.comptabilite.models import Ecriture
from apps.echanges import corrections
from apps.echanges.models import DemandeCorrection
d1, d2 = DemandeCorrection.objects.get(numero="DC00001"), DemandeCorrection.objects.get(numero="DC00002")
erreurs = []
for essai in (lambda: corrections.repondre(d1, "CORRIGEE", "", "compta.dla", []),
              lambda: corrections.repondre(d2, "CONTESTEE", "", "compta.dla")):
    try:
        essai()
    except ValidationError as exc:
        erreurs.append(exc.messages[0])
correctives = list(Ecriture.objects.filter(libelle__in=["Extourne loyer d'octobre", "Loyer d'octobre (corrigé)"]))
corrections.repondre(d1, "CORRIGEE", "Extourne puis loyer au 6222000", "compta.dla", correctives)
corrections.repondre(d2, "CONTESTEE", "Montant conforme au bail", "compta.dla")
print(json.dumps(erreurs))""")
            self.assertEqual(len(reponse), 2)                         # correction sans écriture, contestation sans réponse

            # Avant la remontée, la direction voit seulement « reçue »
            self.assertEqual(siege.py(ETAT)["DC00001"][0], "DEMANDEE")
            agence_vers_siege()
            etat = siege.py(ETAT)
            self.assertEqual(etat["DC00001"], ["CORRIGEE", 2, "Extourne puis loyer au 6222000"])
            self.assertEqual(etat["DC00002"], ["CONTESTEE", 0, "Montant conforme au bail"])
            self.assertEqual(etat["DC00003"], ["ANNULEE", 0, ""])
            # Les écritures de correction sont dans la consolidation : le loyer est passé de 6252 à 6222
            self.assertEqual(siege.py("""
import json
from django.db.models import Sum
from apps.comptabilite.models import LigneEcriture
def solde(n):
    a = LigneEcriture.objects.filter(ecriture__site_origine="DLA", compte__numero=n).aggregate(d=Sum("debit"), c=Sum("credit"))
    return str((a["d"] or 0) - (a["c"] or 0))
print(json.dumps([solde("6252000"), solde("6222000")]))"""), ["0", "180000"])
            # Relire le même fichier ne change rien
            dla_lot = lots_de(dla.manage("echanges", "exporter", "--depuis", "1", "--dossier", travail))[0]
            siege.manage("echanges", "importer", dla_lot)
            self.assertEqual(siege.py(ETAT), etat)


class EcransDemandesDeCorrectionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        import datetime

        from django.contrib.auth import get_user_model

        from apps.comptabilite.models import Compte, Journal
        from apps.comptabilite.services import creer_ecriture

        from . import lots

        call_command("init_erp", "--activite", "transport", verbosity=0)
        lots.configurer_siege("SIEGE", "Direction")
        lots.ajouter_agence("DLA", "Agence de Douala")
        caisse = Compte.objects.get_or_create(numero="5711000", defaults={"intitule": "Caisse"})[0]
        loyer = Compte.objects.get_or_create(numero="6222000", defaults={"intitule": "Loyers"})[0]
        cls.recue = creer_ecriture(Journal.objects.get(code="OD"), datetime.date.today(), "Loyer (agence)",
                                   [{"compte": loyer, "debit": 1000}, {"compte": caisse, "credit": 1000}])
        cls.recue.site_origine = "DLA"
        cls.recue.save(update_fields=["site_origine"])
        cls.admin = get_user_model().objects.create_superuser("chef", "", "Chef-2026x")

    def test_signaler_depuis_l_ecriture_puis_suivre(self):
        from .models import DemandeCorrection

        self.client.force_login(self.admin)
        fiche = self.client.get(reverse("comptabilite:ecriture_detail", args=[self.recue.pk]) + "?seul=1")
        self.assertContains(fiche, "Signaler une erreur à l'agence")
        url = reverse("comptabilite:correction_demander", args=[self.recue.pk])
        self.assertEqual(self.client.get(url + "?seul=1").status_code, 200)
        self.client.post(url, {"motif": "", "echeance": ""})                       # motif obligatoire
        self.assertFalse(DemandeCorrection.objects.exists())
        reponse = self.client.post(url, {"motif": "Compte erroné", "correction_attendue": "6222 → 6252", "echeance": "2026-11-03"})
        d = DemandeCorrection.objects.get()
        self.assertRedirects(reponse, reverse("comptabilite:correction_detail", args=[d.pk]), fetch_redirect_response=False)
        self.assertEqual((d.agence, d.statut, d.demandee_par), ("DLA", "DEMANDEE", "chef"))
        self.assertContains(self.client.get(reverse("comptabilite:corrections") + "?seul=1"), d.numero)
        self.assertContains(self.client.get(reverse("comptabilite:correction_detail", args=[d.pk]) + "?seul=1"), "Annuler la demande")
        self.assertContains(self.client.get(reverse("comptabilite:ecriture_detail", args=[self.recue.pk]) + "?seul=1"), d.numero)
        self.assertContains(self.client.get(reverse("comptabilite:accueil")), "Corrections demandées")
        self.client.post(reverse("comptabilite:correction_detail", args=[d.pk]), {"action": "annuler", "motif": "erreur"})
        d.refresh_from_db()
        self.assertEqual(d.statut, "ANNULEE")

    def test_ecran_de_l_agence_pour_corriger(self):
        import datetime

        from apps.comptabilite.models import Compte, Journal
        from apps.comptabilite.services import creer_ecriture

        from .models import DemandeCorrection

        recue = DemandeCorrection.objects.create(site_origine="SIEGE", numero="DC00009", agence="DLA",
                                                 ecriture_uid=self.recue.uid, motif="Compte erroné",
                                                 statut="RECUE", demandee_le=timezone.now())
        corrective = creer_ecriture(Journal.objects.get(code="OD"), datetime.date.today(), "Extourne",
                                    [{"compte": Compte.objects.get(numero="5711000"), "debit": 1000},
                                     {"compte": Compte.objects.get(numero="6222000"), "credit": 1000}])
        self.client.force_login(self.admin)
        page = self.client.get(reverse("comptabilite:correction_detail", args=[recue.pk]) + "?seul=1")
        self.assertContains(page, "Correction faite")
        self.assertContains(page, corrective.numero)
        self.client.post(reverse("comptabilite:correction_detail", args=[recue.pk]),
                         {"action": "corriger", "ecritures": [corrective.pk], "reponse": "fait"})
        recue.refresh_from_db()
        self.assertEqual((recue.statut, recue.ecritures_correction), ("CORRIGEE", [str(corrective.uid)]))
