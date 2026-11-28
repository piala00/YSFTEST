"""Tests de sécurité du choix SQL Server, sans serveur SQL réel."""
from unittest.mock import patch
from django.test import SimpleTestCase
from apps.core.ouverture_sqlserver import verifier_base_sqlserver


class OuvertureSQLServerTests(SimpleTestCase):
    def setUp(self):
        self.entree = {"id": "transport_2026", "base": "ERP_TRANSPORT_2026"}

    def test_refus_configuration_absente(self):
        with self.assertRaisesRegex(ValueError, "non configuré"):
            verifier_base_sqlserver(self.entree, {})

    def test_refus_identifiant_invalide(self):
        with self.assertRaisesRegex(ValueError, "Identifiant"):
            verifier_base_sqlserver({**self.entree, "id": "../secrets"}, {})

    def test_refus_nom_base_invalide(self):
        with self.assertRaisesRegex(ValueError, "Nom de base"):
            verifier_base_sqlserver({**self.entree, "base": "ERP; DROP DATABASE"}, {})

    def test_refus_mot_de_passe_absent(self):
        with self.assertRaisesRegex(ValueError, "Mot de passe"):
            verifier_base_sqlserver(self.entree, {
                "ERP_SOCIETE_SQL_TRANSPORT_2026_HOST": "localhost",
                "ERP_SOCIETE_SQL_TRANSPORT_2026_USER": "erp",
            })

    @patch("apps.core.management.commands.miroir.connexion_temporaire")
    def test_ne_configure_jamais_base_non_initialisee(self, connexion):
        from unittest.mock import MagicMock
        base = MagicMock()
        base.introspection.table_names.return_value = ["django_migrations", "auth_user"]
        connexion.return_value.__enter__.return_value = base
        with patch("apps.core.management.commands.miroir.controler_tables"):
            with self.assertRaisesRegex(ValueError, "non initialisée"):
                verifier_base_sqlserver(self.entree, {
                    "ERP_SOCIETE_SQL_TRANSPORT_2026_HOST": "localhost",
                })
