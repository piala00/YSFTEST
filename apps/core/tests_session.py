"""Un seul mot de passe par session : fenêtre glissante, pas de reconnexion en cours de travail."""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class SessionGlissanteTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("agent", password="Mot-fictif-2026")

    def test_reglages_session_glissante(self):
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)       # chaque page repousse l'échéance
        self.assertFalse(settings.SESSION_EXPIRE_AT_BROWSER_CLOSE)  # la fermeture du navigateur ne déconnecte pas
        self.assertGreaterEqual(settings.SESSION_COOKIE_AGE, 24 * 3600)

    def test_chaque_requete_prolonge_la_session(self):
        self.client.force_login(self.user)
        reponse = self.client.get(reverse("core:portail"))
        self.assertEqual(reponse.status_code, 200)
        # SESSION_SAVE_EVERY_REQUEST : la réponse renvoie le cookie de session avec l'échéance repoussée.
        cookie = reponse.cookies.get(settings.SESSION_COOKIE_NAME)
        self.assertIsNotNone(cookie)
        self.assertEqual(int(cookie["max-age"]), settings.SESSION_COOKIE_AGE)
