"""Barème des licences (FCFA) : calculs purs et écran Tarifs accessible en version d'essai."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.licences import tarifs as t


class BaremeTests(TestCase):
    def test_abonnement_un_poste_par_agence_inclus(self):
        # 1 agence, 1 poste : seul l'abonnement de base est facturé (poste inclus).
        d = t.devis_abonnement(agences=1, postes=1, modules=0, periode="mensuel")
        self.assertEqual(len(d["lignes"]), 1)
        self.assertEqual(d["total"], t.ABONNEMENT["base_agence"]["mensuel"])

    def test_abonnement_postes_supplementaires_et_modules(self):
        d = t.devis_abonnement(agences=2, postes=5, modules=3, periode="mensuel")
        a = t.ABONNEMENT
        attendu = (2 * a["base_agence"]["mensuel"]          # 2 agences
                   + 3 * a["poste_supplementaire"]["mensuel"]  # 5 postes - 2 inclus
                   + 3 * a["module_optionnel"]["mensuel"])
        self.assertEqual(d["total"], attendu)

    def test_abonnement_annuel_deux_mois_offerts(self):
        self.assertEqual(t.ABONNEMENT["base_agence"]["annuel"],
                         10 * t.ABONNEMENT["base_agence"]["mensuel"])

    def test_definitive_licence_et_maintenance_18_pourcent(self):
        d = t.devis_definitive(agences=1, postes=2, modules=1)
        dd = t.DEFINITIVE
        licence = dd["base_agence"] + 2 * dd["poste"] + 1 * dd["module"]
        self.assertEqual(d["licence"], licence)
        self.assertEqual(d["maintenance_annuelle"], int(licence * dd["maintenance_taux"]))
        self.assertEqual(d["total_premiere_annee"], licence + d["maintenance_annuelle"])

    def test_saisie_invalide_tolere_sans_planter(self):
        # Une saisie client vide ou absurde ne doit jamais lever.
        d = t.grille(agences="", postes="deux", modules=None)
        self.assertEqual(d["parametres"]["agences"], 1)
        self.assertGreaterEqual(d["parametres"]["postes"], 1)
        self.assertEqual(d["parametres"]["modules"], 0)

    def test_comparatif_abonnement_aligne_mensuel_et_annuel(self):
        c = t.abonnement_compare(agences=1, postes=3, modules=0)
        for ligne in c["lignes"]:
            self.assertIn("mensuel", ligne)
            self.assertIn("annuel", ligne)
        self.assertEqual(c["total_annuel"], 10 * c["total_mensuel"])


class EcranTarifsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("agent", password="x")

    def test_tarifs_visible_par_utilisateur_connecte(self):
        self.client.force_login(self.user)
        reponse = self.client.get(reverse("tarifs"), {"agences": 2, "postes": 6, "modules": 1})
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Abonnement")
        self.assertContains(reponse, "Licence définitive")
        self.assertContains(reponse, "FCFA")

    def test_tarifs_exige_connexion(self):
        reponse = self.client.get(reverse("tarifs"))
        self.assertEqual(reponse.status_code, 302)
