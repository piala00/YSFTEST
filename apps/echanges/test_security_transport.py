"""Contrats de sécurité supplémentaires du client relais.

Ces tests sont volontairement des échecs attendus tant que la politique HTTPS
n'est pas imposée par le client. Aucun appel réseau réel n'est effectué.
"""
from unittest import expectedFailure, mock

from django.test import SimpleTestCase

from apps.echanges.synchro import RelaisHTTP


class PolitiqueTransportRelaisTests(SimpleTestCase):
    @expectedFailure
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
