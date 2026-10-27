"""Contrats de sécurité supplémentaires du client relais.

HTTPS imposé par le client (sauf sur le poste même, pour les essais). Aucun appel réseau réel n'est effectué.
"""
from unittest import mock

from django.test import SimpleTestCase

from apps.echanges.synchro import RelaisHTTP


class PolitiqueTransportRelaisTests(SimpleTestCase):
    def test_refuser_http_avec_jeton(self):
        """Un jeton de site ne doit jamais partir vers un relais HTTP non chiffré."""
        relais = RelaisHTTP("http://exemple.invalid", "jeton-de-test")
        with mock.patch("urllib.request.urlopen") as ouvrir:
            with self.assertRaises((ValueError, ConnectionError)):
                relais.lister("DLA")
            ouvrir.assert_not_called()

    def test_url_https_conservee(self):
        relais = RelaisHTTP("https://relais.example.invalid/", "jeton-de-test")
        self.assertEqual(relais.url, "https://relais.example.invalid")

    def test_http_local_permis_pour_les_essais(self):
        relais = RelaisHTTP("http://127.0.0.1:1", "jeton-de-test", delai=1)
        with self.assertRaises(ConnectionError) as e:
            relais.lister("DLA")
        self.assertIn("injoignable", str(e.exception))
