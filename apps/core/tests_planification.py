"""Sauvegardes et vérifications automatiques : quand elles sont dues, échecs signalés, réglages validés."""
import datetime
import tempfile
from unittest import mock

from django.test import SimpleTestCase

from . import planification as p

T = datetime.datetime(2030, 3, 4, 10, 0)


class PlanificationTests(SimpleTestCase):
    def test_toutes_les_n_heures_et_au_demarrage(self):
        config = p.reglages({"ERP_SAUVEGARDE_MODE": "heures", "ERP_SAUVEGARDE_HEURES": "6"})
        self.assertTrue(p.sauvegarde_due({}, config, T))                                     # au démarrage
        etat = {"derniere_sauvegarde": T.isoformat()}
        self.assertFalse(p.sauvegarde_due(etat, config, T + datetime.timedelta(hours=5)))
        self.assertTrue(p.sauvegarde_due(etat, config, T + datetime.timedelta(hours=6)))

    def test_chaque_jour_a_heure_fixe(self):
        config = p.reglages({"ERP_SAUVEGARDE_MODE": "quotidien", "ERP_SAUVEGARDE_HEURE": "22:30"})
        hier = {"derniere_sauvegarde": datetime.datetime(2030, 3, 3, 22, 30).isoformat()}
        self.assertFalse(p.sauvegarde_due(hier, config, T))                                   # 10 h : pas encore
        self.assertTrue(p.sauvegarde_due(hier, config, T.replace(hour=22, minute=31)))
        fait = {"derniere_sauvegarde": T.replace(hour=22, minute=31).isoformat()}
        self.assertFalse(p.sauvegarde_due(fait, config, T.replace(hour=23)))                  # une fois par jour
        self.assertEqual(p.prochaine_sauvegarde(fait, config, T.replace(hour=23)), datetime.datetime(2030, 3, 5, 22, 30))
        # Serveur éteint à 22 h 30 : rattrapée au démarrage suivant
        self.assertTrue(p.sauvegarde_due(hier, config, datetime.datetime(2030, 3, 5, 8, 0)))

    def test_desactivees(self):
        config = p.reglages({"ERP_SAUVEGARDE_MODE": "desactive"})
        self.assertIsNone(p.prochaine_sauvegarde({}, config, T))
        self.assertFalse(p.sauvegarde_due({}, config, T))

    def test_verification_hebdomadaire(self):
        config = p.reglages({})
        self.assertTrue(p.verification_due({}, config, T))
        etat = {"derniere_verification": T.isoformat()}
        self.assertFalse(p.verification_due(etat, config, T + datetime.timedelta(days=6)))
        self.assertTrue(p.verification_due(etat, config, T + datetime.timedelta(days=7)))
        self.assertFalse(p.verification_due({}, p.reglages({"ERP_VERIFICATION_AUTO": "desactive"}), T))

    def test_passages_echec_signale_puis_reprise(self):
        with tempfile.TemporaryDirectory() as dossier:
            appels = []

            def sauvegarder():
                appels.append(1)
                if len(appels) == 1:
                    raise OSError("disque plein")
                return "erp-x.sqlite3"
            planif = p.Planificateur(dossier, sauvegarder, lambda: (False, ["page abîmée"]), journal=lambda m: None)
            with mock.patch.dict("os.environ", {"ERP_SAUVEGARDE_MODE": "heures", "ERP_SAUVEGARDE_HEURES": "1"}):
                planif.passage(T)
                r = planif.resume(T)
                self.assertFalse(r["sauvegarde_ok"])
                self.assertIn("disque plein", r["sauvegarde_resultat"])
                self.assertFalse(r["verification_ok"])
                self.assertEqual(r["verification_details"], ["page abîmée"])
                planif.passage(T + datetime.timedelta(minutes=30))
                self.assertEqual(len(appels), 1)                                               # réessai à l'heure suivante
                planif.passage(T + datetime.timedelta(hours=1))
                self.assertTrue(planif.resume()["sauvegarde_ok"])

    def test_formulaire(self):
        valeurs = p.valider({"mode": "quotidien", "heures": "4", "heure": "21:15", "garder": "30", "copie": " E:\\Sauv ",
                             "verification": "hebdomadaire"})
        self.assertEqual((valeurs["ERP_SAUVEGARDE_MODE"], valeurs["ERP_SAUVEGARDE_HEURE"], valeurs["ERP_SAUVEGARDE_COPIE"]),
                         ("quotidien", "21:15", "E:\\Sauv"))
        for mauvais in ({"mode": "x"}, {"heure": "25:00"}, {"heures": "0"}, {"garder": "abc"}):
            with self.assertRaises(ValueError):
                p.valider({"mode": "heures", **mauvais})
