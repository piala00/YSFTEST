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
        for f in self.donnees.glob("LIC-*"):
            f.unlink()

    def outil(self, *arguments):
        sortie = subprocess.run([sys.executable, str(OUTIL), *arguments], env=self.env, capture_output=True, text=True)
        self.assertEqual(sortie.returncode, 0, sortie.stderr + sortie.stdout)
        return sortie

    def cle_installation(self, client="Transports Essai SA", edition="transport"):
        sortie = self.outil("installation", "--cle", str(Path(self.dossier.name, "cle-privee.pem")), "--client", client,
                            "--edition", edition, "--sortie", str(self.donnees))
        return sortie.stdout.strip().splitlines()[-1]

    # ------------------------------------------------------------ clé d'installation, demande, clé d'activation
    def test_cle_installation(self):
        from apps.core.models import Societe

        cle = self.cle_installation("Société Générale de Voyages")
        d = l.enregistrer_cle_installation(cle.lower().replace("-", " "))          # recopiée sans soin : acceptée
        self.assertEqual((d["societe"], d["edition"]), ("Société Générale de Voyages", "transport"))
        self.assertTrue(d["numero"].startswith("INS-"))
        self.assertEqual(Societe.get().raison_sociale, "Société Générale de Voyages")
        self.assertEqual(l.cle_installation()["numero"], d["numero"])
        self.assertIn(d["numero"], Path(self.dossier.name, "registre-installations.csv").read_text())
        with self.assertRaisesRegex(l.LicenceInvalide, "édition"):
            l.enregistrer_cle_installation(self.cle_installation(edition="commerce"))
        brut = bytearray(l.fc.depuis_texte(cle))
        brut[12] ^= 1                                                                # une lettre du nom changée
        with self.assertRaisesRegex(l.LicenceInvalide, "signature"):
            l.enregistrer_cle_installation(l.fc.en_texte(bytes(brut)))
        for faux in ("", "ABCDE-FGHIJ", "n'importe quoi"):
            with self.assertRaises(l.LicenceInvalide):
                l.enregistrer_cle_installation(faux)

    @override_settings(ERP_LICENCE=True)
    def test_demande_puis_fichier_et_cle_activation(self):
        U = get_user_model()
        self.client.force_login(U.objects.create_superuser("chef", "", "Chef-2030-ok"))
        self.client.post(reverse("licence"), {"action": "installation", "cle": self.cle_installation()})
        reponse = self.client.get(reverse("licence") + "?demande=1")
        self.assertIn("DEMANDE-LICENCE-", reponse["Content-Disposition"])
        demande = l.fc.demande_lire(reponse.content)
        self.assertEqual(demande["societe"], "Transports Essai SA")
        self.assertEqual(demande["materiel"], l.empreinte_machine())
        self.assertEqual(demande["machine_nom"], l.nom_machine())
        self.assertTrue(demande["installation"].startswith("INS-"))
        fichier_demande = self.donnees / "LIC-demande.erpdem"
        fichier_demande.write_bytes(reponse.content)
        sortie = self.outil("emettre", "--cle", str(Path(self.dossier.name, "cle-privee.pem")), "--demande",
                            str(fichier_demande), "--postes", "12", "--jusqu-au", "2099-12-31", "--sortie", str(self.donnees))
        cle = sortie.stdout.strip().splitlines()[-1]
        licence = next(self.donnees.glob("LIC-2*.erplic"))
        self.assertTrue(licence.with_name(licence.stem + "-CLE-ACTIVATION.txt").read_text().strip().endswith(cle))
        registre = Path(self.dossier.name, "registre-licences.csv").read_text()
        self.assertIn(demande["machine_nom"], registre)

        # La clé d'activation ne vaut que pour ce serveur, cette société et cette clé d'installation
        with mock.patch.dict(os.environ, {"ERP_MACHINE_ID": "autre-serveur"}):
            with self.assertRaisesRegex(l.LicenceInvalide, "autre serveur"):
                l.activer(cle)
        page = self.client.post(reverse("licence"), {"action": "activation", "cle": cle}, follow=True)
        self.assertContains(page, "activée pour Transports Essai SA")
        e = l.etat()
        self.assertEqual((e.mode, e.postes, e.licence["machine_nom"]), ("licence", 12, l.nom_machine()))
        # le fichier .erplic donne la même licence
        LicenceDeposee.objects.all().delete()
        l.oublier()
        l.deposer(licence.read_text())
        self.assertEqual(l.etat().licence["numero"], e.licence["numero"])

        # Demande dont la clé d'installation n'a pas été émise par le propriétaire : l'outil refuse
        autre = tempfile.TemporaryDirectory()
        self.addCleanup(autre.cleanup)
        subprocess.run([sys.executable, str(OUTIL), "cles", "--dossier", autre.name], env=self.env, check=True,
                       capture_output=True)
        pirate = subprocess.run([sys.executable, str(OUTIL), "installation", "--cle", str(Path(autre.name, "cle-privee.pem")),
                                 "--client", "Pirate", "--edition", "transport", "--sortie", autre.name],
                                env=self.env, capture_output=True, text=True).stdout.strip().splitlines()[-1]
        faux = {**demande, "cle_installation": pirate}
        fichier_demande.write_text(l.fc.demande_ecrire(faux), encoding="utf-8")
        refus = subprocess.run([sys.executable, str(OUTIL), "emettre", "--cle", str(Path(self.dossier.name, "cle-privee.pem")),
                                "--demande", str(fichier_demande), "--postes", "2", "--sortie", str(self.donnees)],
                               env=self.env, capture_output=True, text=True)
        self.assertNotEqual(refus.returncode, 0)
        self.assertIn("pas été émise par vous", refus.stdout + refus.stderr)

    @override_settings(ERP_LICENCE=True)
    def test_premier_demarrage_demande_la_cle(self):
        U = get_user_model()
        self.client.force_login(U.objects.create_superuser("chef", "", "Chef-2030-ok"))
        self.assertContains(self.client.get(reverse("core:installation") + "?etape=role"), "clé d'installation")
        page = self.client.post(reverse("core:installation"), {"cle": "FAUSSE-CLE22"}, follow=True)
        self.assertContains(page, "refusée : clé incomplète")
        reponse = self.client.post(reverse("core:installation"), {"cle": self.cle_installation("Voyages du Nord")})
        self.assertRedirects(reponse, reverse("core:installation") + "?etape=identite", fetch_redirect_response=False)
        self.assertContains(self.client.get(reverse("core:installation")), "Voyages du Nord")

    @override_settings(ERP_LICENCE=True)
    def test_code_court_puis_fichier_signe_sans_double_activation(self):
        from apps.core.models import Societe

        self.client.force_login(get_user_model().objects.create_superuser("chef-court", "", "Chef-2030-ok"))
        code = l.fc.installation_courte_creer()
        self.assertRegex(code, r"^[A-Z2-7]{6}(?:-[A-Z2-7]{6}){3}$")
        self.client.post(reverse("licence"), {"action": "installation", "cle": code.lower()})
        self.assertEqual(l.cle_installation()["numero"], code)
        demande = l.fc.demande_lire(self.client.get(reverse("licence") + "?demande=1").content)
        chemin = self.donnees / "demande.erpdem"
        chemin.write_text(l.fc.demande_ecrire(demande), encoding="utf-8")
        self.outil("emettre", "--cle", str(Path(self.dossier.name, "cle-privee.pem")), "--demande", str(chemin),
                   "--postes", "4", "--jusqu-au", "2099-12-31", "--sortie", str(self.donnees))
        fichier = next(self.donnees.glob("LIC-2*.erplic"))
        contenu = fichier.read_bytes()
        page = self.client.post(reverse("licence"), {"action": "fichier", "fichier":
                                SimpleUploadedFile(fichier.name, contenu)}, follow=True)
        self.assertContains(page, "installée pour")
        self.assertEqual(l.etat().postes, 4)
        self.assertFalse(l.etat().lecture_seule)
        self.assertEqual(l.controler(contenu)["version"], 3)
        ancien_nom = Societe.get().raison_sociale
        Societe.objects.update(raison_sociale="Autre société")
        with self.assertRaisesRegex(l.LicenceInvalide, "société"):
            l.controler(contenu)
        Societe.objects.update(raison_sociale=ancien_nom)
        self.client.post(reverse("licence"), {"action": "installation", "cle": l.fc.installation_courte_creer()})
        with self.assertRaisesRegex(l.LicenceInvalide, "code d'installation"):
            l.controler(contenu)

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

    def _echeance_attendue(self, mois):
        import calendar

        d = datetime.date.today()
        total = d.month - 1 + mois
        annee, m = d.year + total // 12, total % 12 + 1
        return datetime.date(annee, m, min(d.day, calendar.monthrange(annee, m)[1]))

    def test_licences_mensuelle_a_pluriannuelle(self):
        for option, mois in (("--mensuelle", 1), ("--trimestrielle", 3), ("--semestrielle", 6),
                             ("--annuelle", 12), ("--ans", 24), ("--mois", 6)):  # --ans 2 → 24 mois
            with self.subTest(option=option):
                args = (option, "2") if option == "--ans" else (option, "6") if option == "--mois" else (option,)
                contenu, _ = self.emettre(*args)
                donnees = l.controler(contenu)
                fin = datetime.date.fromisoformat(donnees["valable_jusqu_au"])
                self.assertEqual(fin, self._echeance_attendue(mois))
                for f in self.donnees.glob("LIC-*.erplic"):
                    f.unlink()

    def test_licence_permanente(self):
        contenu, _ = self.emettre("--permanente")
        l.deposer(contenu)
        self.assertEqual(l.etat(datetime.date(2099, 1, 1)).echeance, None)

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

    def test_outil_enregistrer_sous_et_societes_connues(self):
        import importlib.util

        choisi = self.donnees / "Clients" / "Transports du Centre" / "licence serveur"     # dossier et nom choisis
        sortie = subprocess.run([sys.executable, str(OUTIL), "emettre", "--cle", str(Path(self.dossier.name, "cle-privee.pem")),
                                 "--client", "Transports du Centre", "--niu", "M999", "--edition", "transport", "--role", "agence",
                                 "--site", "BTA", "--postes", "4", "--code", l.code_activation(), "--fichier", str(choisi)],
                                env=self.env, capture_output=True, text=True)
        self.assertEqual(sortie.returncode, 0, sortie.stderr)
        fichier = choisi.with_name("licence serveur.erplic")
        self.assertTrue(fichier.exists())
        spec = importlib.util.spec_from_file_location("outil_licences", OUTIL)
        outil = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(outil)
        connus = outil.clients_connus(self.dossier.name)
        self.assertEqual(connus["Transports du Centre"]["niu"], "M999")
        self.assertEqual(connus["Transports du Centre"]["fichier"], str(fichier))

    # ------------------------------------------------------------ essai
    def test_essai_quinze_jours_au_plus(self):
        e = l.etat(J)
        self.assertEqual((e.mode, e.statut, e.jours, e.postes, e.ouvertures_restantes), ("essai", "valide", 15, 3, 30))
        l.oublier()
        self.assertEqual(l.etat(J + datetime.timedelta(days=16)).statut, "expiree")

    def test_essai_trente_ouvertures(self):
        l.etat(J)
        for _ in range(30):
            l.memoire(J, ouvrir=True)
        l.oublier()
        e = l.etat(J)
        self.assertEqual((e.statut, e.ouvertures_restantes), ("valide", 0))     # la 30e ouverture reste utilisable
        l.memoire(J, ouvrir=True)
        l.oublier()
        self.assertEqual(l.etat(J).statut, "expiree")
        EtatLicence.objects.all().delete()                     # base neuve : le compteur hors base reste
        l.oublier()
        self.assertEqual(l.etat(J).statut, "expiree")
        EtatLicence.objects.update(ouvertures=0)               # compteur remis à zéro à la main : refusé
        (self.donnees / ".erp-essai").unlink()
        l.oublier()
        self.assertEqual(l.etat(J).statut, "expiree")

    @override_settings(ERP_LICENCE=True)
    def test_sauvegarde_et_base_bloquees_en_essai(self):
        U = get_user_model()
        self.client.force_login(U.objects.create_superuser("chef", "", "Chef-2030-ok"))
        # Essai (mode == essai) : sauvegarde / restauration et gestion de la base indisponibles
        self.assertTrue(l.etat().mode == "essai")
        self.assertFalse(l.fonctions_pro_disponibles()[0])
        page = self.client.get(reverse("comptabilite:sauvegarde"))
        self.assertContains(page, "réservée à la version sous licence")
        self.assertNotContains(page, 'value="sauvegarder"')
        refus = self.client.post(reverse("comptabilite:sauvegarde"), {"action": "sauvegarder"}, follow=True)
        self.assertNotIn("application/json", refus["Content-Type"])     # aucun téléchargement
        self.assertContains(self.client.get(reverse("core:base_donnees")), "ne sont pas disponibles en version")
        # Avec une licence : de nouveau disponibles
        contenu, _ = self.emettre("--jusqu-au", "2099-12-31")
        l.deposer(contenu)
        self.assertTrue(l.fonctions_pro_disponibles()[0])
        self.assertContains(self.client.get(reverse("comptabilite:sauvegarde")), 'value="sauvegarder"')

    @override_settings(ERP_LICENCE=True)
    def test_sauvegarde_reste_possible_licence_expiree(self):
        U = get_user_model()
        self.client.force_login(U.objects.create_superuser("chef", "", "Chef-2030-ok"))
        contenu, _ = self.emettre("--jusqu-au", "2020-01-01")       # déjà expirée → lecture seule, mais sous licence
        l.deposer(contenu)
        e = l.etat()
        self.assertTrue(e.lecture_seule and e.mode == "licence")
        self.assertTrue(l.fonctions_pro_disponibles()[0])           # données d'un client : jamais bloquées
        self.assertContains(self.client.get(reverse("comptabilite:sauvegarde")), 'value="sauvegarder"')

    @override_settings(ERP_LICENCE=True)
    def test_chaque_connexion_compte(self):
        U = get_user_model()
        u = U.objects.create_user("caisse", "", "Essai-2030-ok")
        avant = l.etat().ouvertures
        self.assertTrue(self.client.login(username="caisse", password="Essai-2030-ok"))
        self.client.logout()
        self.client.force_login(u)
        self.assertEqual(l.etat().ouvertures, avant + 2)

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
        l.etat(J + datetime.timedelta(days=10))
        l.oublier()
        e = l.etat(J)                                          # on remet l'horloge 10 jours en arrière
        self.assertTrue(e.horloge_reculee)
        self.assertEqual(e.jours, 5)                           # l'essai ne s'allonge pas

    # ------------------------------------------------------------ dans le logiciel
    @override_settings(ERP_LICENCE=True)
    def test_lecture_seule_postes_et_ecran(self):
        U = get_user_model()
        admin = U.objects.create_superuser("chef", "", "Chef-2030-ok")
        self.client.force_login(admin)
        self.assertTrue(l.etat().sans_cle)                     # clé d'installation exigée : lecture seule sans elle
        self.assertTrue(l.etat().lecture_seule)
        page = self.client.post(reverse("licence"), {"action": "installation", "cle": self.cle_installation()}, follow=True)
        self.assertContains(page, "enregistrée pour Transports Essai SA")
        self.assertFalse(l.etat().lecture_seule)
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

        # Essai fini : lecture seule (les pages s'ouvrent, les saisies sont refusées, la sauvegarde reste bloquée en essai)
        etat = EtatLicence.objects.get()
        EtatLicence.objects.update(debut_essai=datetime.date(2000, 1, 1), sceau=l._sceau(
            "2000-01-01", etat.derniere_date_vue.isoformat(), etat.ouvertures))
        l.oublier()
        self.assertContains(self.client.get(reverse("comptabilite:accueil")), "lecture seule")
        reponse = self.client.post(reverse("comptabilite:tresorerie_projetee"), {"action": "ajouter", "date": "2030-02-01",
                                                                                 "montant": "1", "libelle": "x"})
        self.assertContains(reponse, "Rien n'a été enregistré", status_code=403)
        self.assertEqual(self.client.post(reverse("comptabilite:sauvegarde"), {"action": "sauvegarder"}).status_code, 302)

        # Dépôt de la licence à l'écran : tout se rétablit
        contenu, _ = self.emettre("--jusqu-au", "2099-12-31")
        page = self.client.get(reverse("licence"))
        self.assertContains(page, l.empreinte_machine())
        page = self.client.post(reverse("licence"), {"fichier": SimpleUploadedFile("lic.erplic", contenu.encode())}, follow=True)
        self.assertContains(page, "installée pour Transports Essai SA")
        self.assertFalse(l.etat().lecture_seule)
        self.assertEqual(l.etat().postes, 10)
        page = self.client.post(reverse("licence"), {"fichier": SimpleUploadedFile("x.erplic", b"faux")}, follow=True)
        self.assertContains(page, "Refusé")

    @override_settings(ERP_LICENCE=False)
    def test_hors_programme_compile_aucune_limite(self):
        self.assertEqual(l.peut_activer_un_compte(), (True, ""))


class CleEditeurTests(TestCase):
    """La clé de l'éditeur gravée dans le module compilé fait autorité ; le fichier texte (remplaçable) est ignoré."""

    def test_cle_gravee_prioritaire_sur_le_fichier(self):
        with mock.patch("apps.licences.cle_editeur.CLES", ["CleGraveeBase64="]):
            self.assertEqual(l.cles_publiques(), ["CleGraveeBase64="])      # fichier texte ignoré
        with mock.patch("apps.licences.cle_editeur.CLES", []):
            self.assertNotIn("CleGraveeBase64=", l.cles_publiques())        # repli fichier (vide ici)

    def test_fichier_repli_accepte_tiret_et_tiret_bas(self):
        from pathlib import Path

        dossier = Path(l.__file__).parent
        for nom in ("cle-publique.txt", "cle_publique.txt"):               # l'outil crée « cle-publique.txt » (tiret)
            fichier = dossier / nom
            if fichier.exists():                                           # le vrai fichier du dépôt : ne pas l'écraser
                continue
            self.addCleanup(lambda f=fichier: f.unlink(missing_ok=True))
            fichier.write_text("CleDeSecoursBase64=\n", encoding="utf-8")
            with mock.patch("apps.licences.cle_editeur.CLES", []):
                self.assertIn("CleDeSecoursBase64=", l.cles_publiques())
            fichier.unlink()

    def test_cle_gravee_verifie_une_vraie_licence(self):
        import subprocess
        import sys
        import tempfile
        from pathlib import Path

        dossier = tempfile.TemporaryDirectory()
        self.addCleanup(dossier.cleanup)
        env = {**os.environ, "ERP_LICENCES_MDP": "Mot-de-passe-essai-2030"}
        subprocess.run([sys.executable, str(OUTIL), "cles", "--dossier", dossier.name], env=env, check=True,
                       capture_output=True)
        publique = Path(dossier.name, "cle-publique.txt").read_text().strip()
        with mock.patch("apps.licences.cle_editeur.CLES", [publique]):
            self.assertEqual(l.cles_publiques(), [publique])
            self.assertTrue(l.cles_publiques())                            # clé disponible → plus en essai « sans clé »



class IdentiteBinaireTests(TestCase):
    def test_identite_publique_a_cote_executable_et_priorite_cle_integree(self):
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from cryptography.hazmat.primitives import serialization
        from . import cle_editeur

        with tempfile.TemporaryDirectory() as dossier:
            publique = Ed25519PrivateKey.generate().public_key().public_bytes(serialization.Encoding.Raw,
                                                                            serialization.PublicFormat.Raw)
            Path(dossier, "parametres.dat").write_bytes(b"ERPID\x01" + publique)
            with mock.patch.object(sys, "frozen", True, create=True), mock.patch.object(sys, "executable", str(Path(dossier, "ERP.exe"))):
                with mock.patch.object(cle_editeur, "CLES", []):
                    self.assertEqual(l.cles_publiques(), [])  # le fichier remplaçable ne crée aucune autorité
                with mock.patch.object(cle_editeur, "CLES", ["identite-integree"]):
                    self.assertEqual(l.cles_publiques(), ["identite-integree"])
