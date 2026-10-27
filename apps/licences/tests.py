"""Licences : signature, serveur, édition, échéance (rappel, grâce, lecture seule), essai, horloge, postes, écran,
et l'outil d'émission du propriétaire (deploy/licences/licences.py) utilisé tel quel."""
import base64
import datetime
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from . import licence as l
from .models import EtatLicence, LicenceDeposee

OUTIL = settings.BASE_DIR / "deploy" / "licences" / "licences.py"
J = datetime.date(2030, 3, 1)


class LicencesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.dossier = tempfile.TemporaryDirectory()
        cls.env = {**os.environ, "ERP_LICENCES_MDP": "Mot-de-passe-essai-2030"}
        subprocess.run([sys.executable, str(OUTIL), "cles", "--dossier", cls.dossier.name], env=cls.env, check=True,
                       capture_output=True)
        cls.publique = Path(cls.dossier.name, "cle-publique.txt").read_text().strip()

    @classmethod
    def tearDownClass(cls):
        cls.dossier.cleanup()
        super().tearDownClass()

    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", verbosity=0)

    def setUp(self):
        donnees = tempfile.TemporaryDirectory()
        self.addCleanup(donnees.cleanup)
        self.donnees = Path(donnees.name)
        for patch in (mock.patch.object(l, "cles_publiques", lambda: [self.publique]),
                      mock.patch.dict(os.environ, {"ERP_MACHINE_ID": "machine-essai-1", "ERP_DOSSIER_DONNEES": donnees.name}),
                      mock.patch.object(l, "_registre_lire", lambda: None), mock.patch.object(l, "_registre_ecrire", lambda v: None)):
            patch.start()
            self.addCleanup(patch.stop)
        l.oublier()
        self.addCleanup(l.oublier)

    def emettre(self, *options, code=None):
        sortie = subprocess.run([sys.executable, str(OUTIL), "emettre", "--cle", str(Path(self.dossier.name, "cle-privee.pem")),
                                 "--client", "Transports Essai SA", "--edition", "transport", "--role", "siege",
                                 "--postes", "10", "--code", code or l.code_activation(), "--sortie", str(self.donnees),
                                 *options], env=self.env, capture_output=True, text=True)
        self.assertEqual(sortie.returncode, 0, sortie.stderr + sortie.stdout)
        return next(self.donnees.glob("LIC-*.erplic")).read_text(), sortie

    def tearDown(self):
        for f in self.donnees.glob("LIC-*.erplic"):
            f.unlink()

    # ------------------------------------------------------------ fichier et signature
    def test_licence_valide_puis_rappel_grace_lecture_seule(self):
        contenu, _ = self.emettre("--jusqu-au", "2030-12-31")
        l.deposer(contenu)
        e = l.etat(J)
        self.assertEqual((e.mode, e.statut, e.postes, e.lecture_seule), ("licence", "valide", 10, False))
        self.assertEqual(e.licence["client"], "Transports Essai SA")
        l.oublier()
        self.assertEqual(l.etat(datetime.date(2030, 12, 10)).statut, "rappel")
        l.oublier()
        e = l.etat(datetime.date(2031, 1, 5))
        self.assertEqual((e.statut, e.jours, e.lecture_seule), ("grace", 10, False))
        l.oublier()
        e = l.etat(datetime.date(2031, 1, 16))
        self.assertEqual((e.statut, e.lecture_seule), ("expiree", True))
        self.assertIn("lecture seule", e.message)

    def test_licence_definitive(self):
        contenu, _ = self.emettre("--definitive")
        l.deposer(contenu)
        e = l.etat(datetime.date(2045, 1, 1))
        self.assertEqual((e.statut, e.echeance, e.lecture_seule), ("valide", None, False))

    def test_refus(self):
        contenu, _ = self.emettre()
        lignes = contenu.splitlines()
        donnees = l.lire(contenu)[0]
        donnees["postes"] = 500                                                    # fichier retouché
        retouche = "\n".join([lignes[0], base64.b64encode(l.canonique(donnees)).decode(), lignes[2]])
        for fichier, motif in ((retouche, "signature"), ("n'importe quoi", "pas un fichier")):
            with self.assertRaisesRegex(l.LicenceInvalide, motif):
                l.deposer(fichier)
        with mock.patch.dict(os.environ, {"ERP_MACHINE_ID": "autre-serveur"}):
            with self.assertRaisesRegex(l.LicenceInvalide, "autre serveur"):
                l.deposer(contenu)
        from apps.core.models import Societe

        Societe.objects.update(activite="COMMERCE")
        with self.assertRaisesRegex(l.LicenceInvalide, "édition"):
            l.deposer(contenu)
        self.assertEqual(LicenceDeposee.objects.filter(valide=False).count(), 4)       # historique des refus
        with mock.patch.object(l, "cles_publiques", lambda: []):
            with self.assertRaisesRegex(l.LicenceInvalide, "clé de vérification"):
                l.controler(contenu)

    def test_outil_verifier_et_registre(self):
        contenu, sortie = self.emettre("--niu", "M0123456789")
        self.assertIn("LIC-", sortie.stdout)
        fichier = next(self.donnees.glob("LIC-*.erplic"))
        v = subprocess.run([sys.executable, str(OUTIL), "verifier", str(fichier), "--publique",
                            str(Path(self.dossier.name, "cle-publique.txt"))], capture_output=True, text=True)
        self.assertIn("Signature correcte", v.stdout)
        self.assertIn("M0123456789", Path(self.dossier.name, "registre-licences.csv").read_text())
        mauvais = subprocess.run([sys.executable, str(OUTIL), "emettre", "--cle", str(Path(self.dossier.name, "cle-privee.pem")),
                                  "--client", "X", "--edition", "transport", "--role", "siege", "--postes", "1",
                                  "--code", "pas-un-code"], env=self.env, capture_output=True, text=True)
        self.assertNotEqual(mauvais.returncode, 0)

    # ------------------------------------------------------------ essai
    def test_essai_trente_jours_puis_lecture_seule(self):
        e = l.etat(J)
        self.assertEqual((e.mode, e.statut, e.jours, e.postes), ("essai", "valide", 30, 3))
        l.oublier()
        self.assertEqual(l.etat(J + datetime.timedelta(days=31)).statut, "expiree")

    def test_essai_non_relance(self):
        l.etat(J)
        l.oublier()
        EtatLicence.objects.all().delete()                     # base neuve : la mémoire hors base garde le début
        self.assertEqual(l.etat(J + datetime.timedelta(days=40)).statut, "expiree")
        l.oublier()
        EtatLicence.objects.update(debut_essai=J + datetime.timedelta(days=60))   # date retouchée à la main
        self.assertEqual(l.etat(J + datetime.timedelta(days=41)).statut, "expiree")

    def test_horloge_reculee(self):
        l.etat(J)
        l.oublier()
        l.etat(J + datetime.timedelta(days=20))
        l.oublier()
        e = l.etat(J)                                          # on remet l'horloge 20 jours en arrière
        self.assertTrue(e.horloge_reculee)
        self.assertEqual(e.jours, 10)                          # l'essai ne s'allonge pas

    # ------------------------------------------------------------ dans le logiciel
    @override_settings(ERP_LICENCE=True)
    def test_lecture_seule_postes_et_ecran(self):
        U = get_user_model()
        admin = U.objects.create_superuser("chef", "", "Chef-2030-ok")
        self.client.force_login(admin)
        autorisations = reverse("comptabilite:autorisations")
        for nom in ("a1", "a2", "a3"):
            self.client.post(autorisations, {"action": "utilisateur", "nom_utilisateur": nom, "mot_de_passe": "Essai-2030-ok"})
        self.assertEqual(U.objects.filter(is_active=True).count(), 3)       # essai : 3 postes (a3 refusé)
        self.assertFalse(U.objects.filter(username="a3").exists())
        self.client.post(autorisations, {"action": "activer", "nom_utilisateur": "a2"})
        self.assertFalse(U.objects.get(username="a2").is_active)
        self.client.post(autorisations, {"action": "utilisateur", "nom_utilisateur": "a3", "mot_de_passe": "Essai-2030-ok"})
        self.client.post(autorisations, {"action": "activer", "nom_utilisateur": "a2"})          # plus de place
        self.assertFalse(U.objects.get(username="a2").is_active)

        # Trop de comptes actifs (licence réduite) : seuls les administrateurs entrent
        U.objects.create_user("a4", "", "Essai-2030-ok")
        c = self.client_class()
        c.force_login(U.objects.get(username="a1"))
        self.assertContains(c.get("/"), "Trop de comptes actifs", status_code=403)
        self.assertEqual(self.client.get("/").status_code, 200)

        # Essai fini : lecture seule (les pages s'ouvrent, les saisies sont refusées, la sauvegarde reste permise)
        EtatLicence.objects.update(debut_essai=datetime.date(2000, 1, 1))
        EtatLicence.objects.update(sceau=l._sceau("2000-01-01", EtatLicence.objects.get().derniere_date_vue.isoformat()))
        l.oublier()
        self.assertContains(self.client.get(reverse("comptabilite:accueil")), "lecture seule")
        reponse = self.client.post(reverse("comptabilite:tresorerie_projetee"), {"action": "ajouter", "date": "2030-02-01",
                                                                                 "montant": "1", "libelle": "x"})
        self.assertContains(reponse, "Rien n'a été enregistré", status_code=403)
        self.assertEqual(self.client.post(reverse("comptabilite:sauvegarde"), {"action": "sauvegarder"}).status_code, 200)

        # Dépôt de la licence à l'écran : tout se rétablit
        contenu, _ = self.emettre("--jusqu-au", "2099-12-31")
        page = self.client.get(reverse("licence"))
        self.assertContains(page, l.code_activation())
        page = self.client.post(reverse("licence"), {"fichier": SimpleUploadedFile("lic.erplic", contenu.encode())}, follow=True)
        self.assertContains(page, "installée pour Transports Essai SA")
        self.assertFalse(l.etat().lecture_seule)
        self.assertEqual(l.etat().postes, 10)
        page = self.client.post(reverse("licence"), {"fichier": SimpleUploadedFile("x.erplic", b"faux")}, follow=True)
        self.assertContains(page, "Licence refusée")

    @override_settings(ERP_LICENCE=False)
    def test_hors_programme_compile_aucune_limite(self):
        self.assertEqual(l.peut_activer_un_compte(), (True, ""))
