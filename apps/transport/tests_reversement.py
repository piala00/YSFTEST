"""T-24 : la recette comptée d'un point de vente qui ferme est reversée vers une
caisse encore ouverte (transfert en transit, compte 585), au moment de l'approbation."""
import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase

from apps.comptabilite.models import Compte, Journal
from apps.comptabilite.services import creer_ecriture

from .models import Billet, Depart
from .models_caisse import SessionCaisse, TransfertFonds, solde_tresorerie


class ReversementRecetteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", "--demo", verbosity=0)
        User = get_user_model()
        cls.agent = User.objects.create_user("vendeur", "", "x")
        cls.agent2 = User.objects.create_user("vendeur2", "", "x")
        cls.chef = User.objects.create_user("chefgare", "", "x")
        cls.ca = Journal.objects.get(code="CA")
        cls.bq = Journal.objects.get(code="BQ")

    def session_avec_recette(self):
        # Fonds de caisse déjà en caisse, puis une vente en espèces : la caisse CA a de quoi reverser.
        creer_ecriture(self.ca, datetime.date.today(), "Fonds de caisse",
                       [{"compte": Compte.objects.get(numero="5711"), "debit": 10000},
                        {"compte": Compte.objects.get_or_create(numero="101", defaults={"intitule": "Capital"})[0], "credit": 10000}])
        s = SessionCaisse.ouvrir(self.agent, self.ca, fonds_initial=10000)
        d = Depart.objects.filter(statut=Depart.PROGRAMME).first()
        Billet(depart=d, voyageur="V1").vendre(self.agent)  # 6 000 espèces
        return s

    def test_caisses_ouvertes_exclut_la_sienne(self):
        self.session_avec_recette()
        SessionCaisse.ouvrir(self.agent2, self.bq)
        ouvertes = SessionCaisse.caisses_ouvertes(sauf_pk=self.ca.pk)
        self.assertIn(self.bq, list(ouvertes))
        self.assertNotIn(self.ca, list(ouvertes))

    def test_reversement_vers_caisse_ouverte(self):
        s = self.session_avec_recette()
        SessionCaisse.ouvrir(self.agent2, self.bq)   # une autre caisse reste ouverte
        attendu = s.detail()["attendu"]
        s.fermer(attendu)                            # compté = attendu, pas d'écart
        s.approuver(self.chef, reverser_vers=self.bq)
        self.assertIsNotNone(s.transfert_reversement)
        t = s.transfert_reversement
        self.assertEqual((t.origine, t.destination, t.montant, t.statut), (self.ca, self.bq, attendu, TransfertFonds.EN_TRANSIT))
        self.assertEqual(t.ecriture_envoi.lignes.get(debit=attendu).compte.numero, "5850000")
        self.assertEqual(solde_tresorerie(self.ca.compte_tresorerie, datetime.date.today()), 0)

    def test_reversement_meme_caisse_refuse(self):
        s = self.session_avec_recette()
        s.fermer(s.detail()["attendu"])
        with self.assertRaisesMessage(ValidationError, "différente"):
            s.approuver(self.chef, reverser_vers=self.ca)

    def test_approbation_sans_reversement_reste_sur_place(self):
        s = self.session_avec_recette()
        s.fermer(s.detail()["attendu"])
        s.approuver(self.chef)
        self.assertIsNone(s.transfert_reversement)
