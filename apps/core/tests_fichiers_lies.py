"""Fichiers liés : la Gestion commerciale et la Comptabilité partagent tiers, utilisateurs, profils et droits."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.commercial.models import Tiers
from apps.core import droits as d
from apps.core.models import AccesLogiciel, DroitAcces
from apps.core.navigation import COMPTABILITE, GESTION_COMMERCIALE


class FichiersLiesTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        User = get_user_model()
        cls.admin = User.objects.create_superuser("chef", "", "x")
        cls.comptable = User.objects.create_user("comptable", "", "x")
        cls.profil = Group.objects.create(name="Comptable")
        cls.comptable.groups.add(cls.profil)

    def test_tiers_cree_en_gestion_commerciale_present_en_comptabilite(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("commercial:tiers_create") + "?type=CLIENT",
                         {"type_tiers": "CLIENT", "code": "CLIE", "nom": "Client lié", "delai_paiement": 30,
                          "plafond_credit": 0, "code_risque": "AVERTIR", "actif": "on"})
        self.assertTrue(Tiers.objects.filter(code="CLIE").exists())
        # Comptabilité › Structure › Plan tiers › Clients ouvre le même fichier des tiers
        lien = next(el for _, lignes in d.arbre(COMPTABILITE)[0] for el, _ in lignes if el.code == "structure.plan_tiers.clients").lien()
        self.assertContains(self.client.get(lien), "Client lié")

    def test_droit_d_un_ecran_commun_herite_dans_le_fichier_lie(self):
        """Profil comptable réglé en Comptabilité : il retrouve ses droits en Gestion commerciale."""
        self.client.force_login(self.admin)
        url = reverse("comptabilite:autorisations")
        self.client.post(url, {"action": "droits", "profil": self.profil.pk, "logiciel": "comptabilite",
                               "droit_structure.plan_tiers.clients": d.LECTURE, "droit_structure.banques": d.INTERDIT})
        reglages = set(DroitAcces.objects.filter(groupe=self.profil).values_list("module", "code", "niveau"))
        self.assertIn(("commercial", "tiers.clients", d.LECTURE), reglages)
        self.assertIn(("commercial", "structure.banques", d.INTERDIT), reglages)
        droits = d.Droits(self.comptable, GESTION_COMMERCIALE)
        self.assertEqual(droits.niveau("tiers.clients"), d.LECTURE)
        self.assertEqual(droits.niveau("ventes.facture"), d.TOUT)             # écran propre à la Gestion commerciale
        self.client.force_login(self.comptable)
        self.assertEqual(self.client.get(reverse("commercial:tiers_create") + "?type=CLIENT").status_code, 403)
        # Remis sur « Hérité » dans un logiciel : effacé aussi dans l'autre
        self.client.force_login(self.admin)
        self.client.post(reverse("commercial:autorisations"), {"action": "droits", "profil": self.profil.pk, "logiciel": "commercial",
                                                               "droit_structure.banques": d.INTERDIT})
        self.assertFalse(DroitAcces.objects.filter(groupe=self.profil, code__in=["tiers.clients", "structure.plan_tiers.clients"]).exists())
        self.assertEqual(DroitAcces.objects.filter(groupe=self.profil, niveau=d.INTERDIT).count(), 2)

    def test_acces_invite_et_aucun_acces(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("commercial:autorisations"), {
            "action": "utilisateur", "nom_utilisateur": "comptable", "profil_utilisateur": self.profil.pk,
            "acces_commercial": d.INVITE, "acces_comptabilite": d.UTILISATEUR, "acces_reporting": d.AUCUN})
        self.assertEqual(dict(AccesLogiciel.objects.filter(utilisateur=self.comptable).values_list("module", "acces")),
                         {"commercial": d.INVITE, "reporting": d.AUCUN})
        self.client.force_login(self.comptable)
        # Invité en Gestion commerciale : consultation seule
        self.assertEqual(self.client.get(reverse("commercial:clients")).status_code, 200)
        self.assertEqual(self.client.get(reverse("commercial:tiers_create") + "?type=CLIENT").status_code, 403)
        # Utilisateur en Comptabilité : saisie permise
        self.assertEqual(self.client.get(reverse("comptabilite:ecriture_create")).status_code, 200)
        # Aucun accès au Reporting : logiciel refusé, et absent du portail (chacun ne voit que ses logiciels)
        self.assertEqual(self.client.get(reverse("reporting:dashboard")).status_code, 403)
        portail = self.client.get(reverse("core:portail"))
        self.assertContains(portail, "Comptabilité générale")
        self.assertNotContains(portail, 'href="/reporting/"')
        # L'administrateur garde l'accès à tout
        AccesLogiciel.objects.create(utilisateur=self.admin, module="reporting", acces=d.AUCUN)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("reporting:dashboard")).status_code, 200)

    def test_fichier_lie_dans_a_propos_de_votre_societe(self):
        self.client.force_login(self.admin)
        reponse = self.client.get(reverse("commercial:societe"))
        self.assertContains(reponse, "Fichiers liés")
        self.assertContains(reponse, COMPTABILITE.titre)
        self.assertContains(self.client.get(reverse("comptabilite:societe")), GESTION_COMMERCIALE.titre)
