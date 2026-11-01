from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.urls import reverse

from . import poste, structure_base
from .models import Societe


class AdministrationOngletsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", verbosity=0)
        cls.admin = get_user_model().objects.create_superuser("admin-onglets", "", "Essai-2030-ok")

    def setUp(self):
        self.client.force_login(self.admin)

    def test_navigation_commune_sur_licence_base_et_echanges(self):
        for nom in ("core:poste", "licence", "core:base_donnees", "core:echanges_poste"):
            page = self.client.get(reverse(nom))
            self.assertEqual(page.status_code, 200, nom)
            self.assertContains(page, 'aria-label="Administration du poste"')
            for onglet in ("Licence", "Base de données", "Sauvegarde et restauration", "Import et export agences", "Simulation"):
                self.assertContains(page, onglet)

    def test_droits_sur_toutes_les_entrees(self):
        self.client.force_login(get_user_model().objects.create_user("guichetier-test", "", "x"))
        for nom in ("core:poste", "licence", "core:base_donnees", "core:echanges_poste"):
            self.assertEqual(self.client.get(reverse(nom)).status_code, 403, nom)
            self.assertEqual(self.client.post(reverse(nom), {"action": "migrer"}).status_code, 403, nom)

    def test_onglet_sauvegardes_distinct_de_la_structure(self):
        page = self.client.get(reverse("core:base_donnees") + "?onglet=sauvegardes")
        self.assertEqual(page.context["onglet_poste"], "sauvegardes")
        self.assertNotContains(page, "Analyser la structure")
        page = self.client.get(reverse("core:base_donnees"))
        self.assertContains(page, "Analyser la structure")
        self.assertNotContains(page, "Sauvegarder maintenant")

    def test_analyse_structure_reelle_lecture_seule(self):
        avant = list(Societe.objects.values())
        diagnostic = structure_base.analyser()
        self.assertTrue(diagnostic["ok"], diagnostic["details"])
        self.assertEqual(diagnostic["anomalies"], [])
        self.assertEqual(list(Societe.objects.values()), avant)

    def test_colonne_absente_signalee_sans_recreation(self):
        originale = connection.introspection.get_table_description
        def description(cur, table):
            champs = originale(cur, table)
            return [c for c in champs if not (table == Societe._meta.db_table and c.name == "raison_sociale")]
        with mock.patch.object(connection.introspection, "get_table_description", side_effect=description):
            diagnostic = structure_base.analyser()
        self.assertFalse(diagnostic["ok"])
        self.assertIn(f"Colonne absente : {Societe._meta.db_table}.raison_sociale.", diagnostic["anomalies"])

    def test_schema_applique_mais_incomplet_ne_se_repare_pas_par_invention(self):
        diagnostic = {"etrangeres": [], "migrations": [], "anomalies": ["Table absente"], "ok": False}
        sauvegarde = mock.Mock()
        with mock.patch.object(structure_base, "analyser", return_value=diagnostic), mock.patch.object(structure_base, "call_command") as commande:
            with self.assertRaisesMessage(ValueError, "déjà migrés"):
                structure_base.appliquer_migrations(sauvegarde)
        sauvegarde.assert_not_called()
        commande.assert_not_called()

    def test_migration_refusee_si_sauvegarde_echoue(self):
        diagnostic = {"etrangeres": [], "migrations": ["core.fictive"], "anomalies": [], "ok": False}
        with mock.patch.object(structure_base, "analyser", return_value=diagnostic), \
                mock.patch("apps.core.base_donnees.verifier", return_value=(True, [])), \
                mock.patch.object(structure_base, "call_command") as commande:
            with self.assertRaises(OSError):
                structure_base.appliquer_migrations(mock.Mock(side_effect=OSError("disque plein")))
        commande.assert_not_called()

    def test_tables_etrangeres_interdisent_mise_a_jour(self):
        diagnostic = {"etrangeres": ["F_COMPTET"], "migrations": ["core.fictive"], "anomalies": [], "ok": False}
        with mock.patch.object(structure_base, "analyser", return_value=diagnostic), mock.patch.object(structure_base, "call_command") as commande:
            with self.assertRaisesMessage(ValueError, "extérieures"):
                structure_base.appliquer_migrations(mock.Mock())
        commande.assert_not_called()

    def test_migration_sur_poste_distant_ou_sans_confirmation_refusee(self):
        with mock.patch.object(structure_base, "appliquer_migrations") as appliquer:
            for champs, ip in (({"action": "migrer"}, "127.0.0.1"),
                               ({"action": "migrer", "confirmation": "METTRE A JOUR"}, "192.0.2.10")):
                page = self.client.post(reverse("core:base_donnees"), champs, REMOTE_ADDR=ip, follow=True)
                self.assertContains(page, "Impossible")
        appliquer.assert_not_called()

    def test_reparation_precedee_de_sauvegarde_et_arretee_si_echec(self):
        with mock.patch.dict(poste.ACTIONS, {"sauvegarder": mock.Mock(side_effect=OSError("disque plein"))}), \
                mock.patch("apps.core.base_donnees.moteur", return_value="sqlite"), \
                mock.patch("apps.core.base_donnees.reparer") as reparer:
            self.client.post(reverse("core:base_donnees"), {"action": "reparer"})
        reparer.assert_not_called()
