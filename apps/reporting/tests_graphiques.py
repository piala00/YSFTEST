"""Un graphique sous chaque tableau du reporting (static/js/graphiques.js lit les tableaux marqués data-graphique)."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse


class GraphiquesSousLesTableauxTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", verbosity=0)
        cls.admin = get_user_model().objects.create_superuser("chef", "", "Chef-2026x")

    def test_pages_du_reporting(self):
        self.client.force_login(self.admin)
        periode = "?seul=1&du=2026-09-01&au=2026-11-30"
        pages = [reverse("reporting:evolution"), reverse("reporting:comparaison"), reverse("reporting:matrice"),
                 reverse("reporting:classement"), reverse("analytique:plan"), reverse("analytique:axe", args=["agences"]),
                 reverse("comptabilite:analytique_vehicules"), reverse("transport:rentabilite"),
                 reverse("reporting:comparaisons_transport"),
                 reverse("comptabilite:statistiques_tiers") + "?date_debut=2026-09-01&date_fin=2026-11-30&type=CLIENT&seul=1&ok=1"]
        for url in pages:
            with self.subTest(url=url):
                reponse = self.client.get(url if "?" in url else url + periode)
                self.assertEqual(reponse.status_code, 200)
                self.assertContains(reponse, "data-graphique=")
                self.assertContains(reponse, "js/graphiques.js")

    def test_script_present(self):
        script = (settings.BASE_DIR / "static" / "js" / "graphiques.js").read_text(encoding="utf-8")
        self.assertIn("table[data-graphique]", script)
