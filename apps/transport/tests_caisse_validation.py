"""Concurrence et anciennes instances sur les clôtures de caisse des guichets."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import close_old_connections, connections
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django.utils.functional import SimpleLazyObject

from apps.comptabilite.models import Ecriture, Journal

from .models_caisse import SessionCaisse


class DonneesSessionCaisse:
    @classmethod
    def preparer(cls):
        call_command("init_erp", "--activite", "transport", "--demo", verbosity=0)
        User = get_user_model()
        cls.agent = User.objects.create_user("caissier-session-p0", password="Mot-fictif-2026")
        cls.chef = User.objects.create_user("chef-session-p0", password="Mot-fictif-2026")
        cls.caisse = Journal.objects.get(code="CA")

    def session_avec_surplus(self):
        session = SessionCaisse.ouvrir(self.agent, self.caisse, fonds_initial=0)
        session.fermer(1000, justification="Surplus fictif de recette")
        return session


class SessionsCaisseInstancesPerimeesTests(DonneesSessionCaisse, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.preparer()

    def test_ancienne_instance_ne_peut_pas_fermer_deux_fois(self):
        session = SessionCaisse.ouvrir(self.agent, self.caisse, fonds_initial=0)
        ancienne = SessionCaisse.objects.get(pk=session.pk)
        session.fermer(1000, justification="Premier comptage fictif")
        with self.assertRaisesMessage(ValidationError, "déjà fermée"):
            ancienne.fermer(2000, justification="Second comptage fictif")
        persistante = SessionCaisse.objects.get(pk=session.pk)
        self.assertEqual(persistante.montant_compte, 1000)
        self.assertEqual(persistante.statut, SessionCaisse.FERMEE)

    def test_ouverture_accepte_utilisateur_lazy_du_middleware(self):
        agent = SimpleLazyObject(lambda: self.agent)
        session = SessionCaisse.ouvrir(agent, self.caisse, fonds_initial=0)
        self.assertEqual(session.agent_id, self.agent.pk)

    def test_ancienne_instance_ne_peut_pas_comptabiliser_deux_ecarts(self):
        session = self.session_avec_surplus()
        ancienne = SessionCaisse.objects.get(pk=session.pk)
        session.approuver(self.chef)
        with self.assertRaisesMessage(ValidationError, "Seule une caisse fermée"):
            ancienne.approuver(self.chef)
        persistante = SessionCaisse.objects.get(pk=session.pk)
        self.assertEqual(persistante.statut, SessionCaisse.APPROUVEE)
        self.assertEqual(Ecriture.objects.filter(reference=session.numero).count(), 1)
        self.assertEqual(persistante.ecriture_ecart_id, Ecriture.objects.get(reference=session.numero).pk)

    def test_ancienne_instance_ne_peut_pas_reverser_deux_fois(self):
        session = self.session_avec_surplus()
        ancienne = SessionCaisse.objects.get(pk=session.pk)
        destination = Journal.objects.get(code="BQ")
        session.approuver(self.chef, reverser_vers=destination)
        with self.assertRaisesMessage(ValidationError, "Seule une caisse fermée"):
            ancienne.approuver(self.chef, reverser_vers=destination)
        persistante = SessionCaisse.objects.get(pk=session.pk)
        self.assertIsNotNone(persistante.transfert_reversement_id)
        self.assertEqual(persistante.transfert_reversement.__class__.objects.filter(
            porteur__contains=session.numero
        ).count(), 1)


@skipUnlessDBFeature("has_select_for_update")
class SessionsCaisseConcurrentesTests(DonneesSessionCaisse, TransactionTestCase):
    def setUp(self):
        self.preparer()

    def _concurrents(self, session, action):
        barriere = Barrier(2, timeout=20)

        def travail():
            close_old_connections()
            try:
                connexion = connections["default"]
                with connexion.cursor() as curseur:
                    if connexion.vendor in ("microsoft", "mssql"):
                        curseur.execute("SET LOCK_TIMEOUT 15000")
                courant = SessionCaisse.objects.get(pk=session.pk)
                chef = get_user_model().objects.get(pk=self.chef.pk)
                barriere.wait()
                try:
                    action(courant, chef)
                    return "ok"
                except ValidationError:
                    return "refus"
            finally:
                connections["default"].close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futurs = [pool.submit(travail) for _ in range(2)]
            resultats = [f.result(timeout=45) for f in futurs]
        self.assertEqual(sorted(resultats), ["ok", "refus"])

    def test_fermeture_concurrente_ne_garde_qu_un_comptage(self):
        session = SessionCaisse.ouvrir(self.agent, self.caisse, fonds_initial=0)
        self._concurrents(session, lambda courant, chef: courant.fermer(1000, "Comptage fictif"))
        persistante = SessionCaisse.objects.get(pk=session.pk)
        self.assertEqual(persistante.statut, SessionCaisse.FERMEE)
        self.assertEqual(persistante.montant_compte, 1000)

    def test_ouverture_concurrente_ne_cree_qu_une_caisse(self):
        barriere = Barrier(2, timeout=20)

        def travail():
            close_old_connections()
            try:
                connexion = connections["default"]
                with connexion.cursor() as curseur:
                    if connexion.vendor in ("microsoft", "mssql"):
                        curseur.execute("SET LOCK_TIMEOUT 15000")
                agent = get_user_model().objects.get(pk=self.agent.pk)
                caisse = Journal.objects.get(pk=self.caisse.pk)
                barriere.wait()
                try:
                    SessionCaisse.ouvrir(agent, caisse, fonds_initial=0)
                    return "ok"
                except ValidationError:
                    return "refus"
            finally:
                connections["default"].close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futurs = [pool.submit(travail) for _ in range(2)]
            resultats = [f.result(timeout=45) for f in futurs]
        self.assertEqual(sorted(resultats), ["ok", "refus"])
        self.assertEqual(
            SessionCaisse.objects.filter(agent=self.agent, statut=SessionCaisse.OUVERTE).count(),
            1,
        )

    def test_approbation_concurrente_ne_publie_qu_un_ecart(self):
        session = self.session_avec_surplus()
        self._concurrents(session, lambda courant, chef: courant.approuver(chef))
        persistante = SessionCaisse.objects.get(pk=session.pk)
        self.assertEqual(persistante.statut, SessionCaisse.APPROUVEE)
        self.assertEqual(Ecriture.objects.filter(reference=session.numero).count(), 1)
