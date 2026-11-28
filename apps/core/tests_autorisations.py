"""Fichier › Autorisations d'accès : quatre niveaux par menu, héritage, contrôle web et API."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from apps.commercial.models import Article, Document, LigneDocument, Tiers
from apps.core import droits as d
from apps.core.models import DroitAcces
from apps.core.navigation import GESTION_COMMERCIALE


class AutorisationsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        User = get_user_model()
        cls.admin = User.objects.create_superuser("chef", "", "x")
        cls.vendeur = User.objects.create_user("vendeur", "", "x")
        cls.profil = Group.objects.create(name="Vendeur")
        cls.vendeur.groups.add(cls.profil)
        cls.client_ = Tiers.objects.create(code="C1", nom="Client")
        cls.article = Article.objects.create(reference="A1", designation="Article", prix_vente=1000, suivi_stock=False)

    def regler(self, code, niveau, module="commercial"):
        DroitAcces.objects.update_or_create(groupe=self.profil, module=module, code=code, defaults={"niveau": niveau})

    def facture(self):
        doc = Document.objects.create(type_document=Document.FACTURE, tiers=self.client_)
        LigneDocument.objects.create(document=doc, article=self.article, quantite=1, prix_unitaire=1000)
        doc.recalculer()
        return doc

    def test_heritage_du_menu_parent(self):
        self.regler("traitement", d.LECTURE)
        self.regler("ventes.devis", d.TOUT)
        droits = d.Droits(self.vendeur, GESTION_COMMERCIALE)
        self.assertEqual(droits.niveau("ventes.facture"), d.LECTURE)       # hérité de Traitement
        self.assertEqual(droits.niveau("ventes.devis"), d.TOUT)            # réglage propre
        self.assertEqual(droits.niveau("articles.liste"), d.TOUT)          # Structure : rien de réglé
        self.assertEqual(d.Droits(self.admin, GESTION_COMMERCIALE).niveau("ventes.facture"), d.TOUT)

    def test_tout_interdire(self):
        self.regler("structure", d.INTERDIT)
        self.client.force_login(self.vendeur)
        self.assertEqual(self.client.get(reverse("commercial:articles")).status_code, 403)
        self.assertEqual(self.client.get(reverse("commercial:article_detail", args=[self.article.pk])).status_code, 403)
        reponse = self.client.get(reverse("commercial:accueil"))
        self.assertEqual(reponse.status_code, 200)
        self.assertContains(reponse, "Interdit par vos autorisations d'accès")       # menu grisé avec cadenas
        self.assertNotIn("Articles", [l["titre"] for g in reponse.context["raccourcis"] for l in g["liens"]])

    def test_raccourcis_en_lecture_seule(self):
        self.regler("achats.documents", d.LECTURE)
        self.client.force_login(self.vendeur)
        titres = [l["titre"] for g in self.client.get(reverse("commercial:accueil")).context["raccourcis"] for l in g["liens"]]
        self.assertNotIn("Saisir un document d'achat", titres)   # formulaire de saisie : écriture interdite
        self.assertIn("Saisir un document de vente", titres)

    def test_interdire_l_ecriture(self):
        self.regler("ventes.facture", d.LECTURE)
        doc = self.facture()
        self.client.force_login(self.vendeur)
        self.assertEqual(self.client.get(reverse("commercial:document_detail", args=[doc.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("commercial:document_create", args=[Document.FACTURE])).status_code, 403)
        self.assertEqual(self.client.post(reverse("commercial:document_valider", args=[doc.pk])).status_code, 403)
        doc.refresh_from_db()
        self.assertEqual(doc.statut, Document.BROUILLON)
        # Les devis restent autorisés
        self.assertEqual(self.client.get(reverse("commercial:document_create", args=[Document.DEVIS])).status_code, 200)

    def test_interdire_la_suppression(self):
        self.regler("ventes.facture", d.SANS_SUPPRESSION)
        doc = self.facture()
        self.client.force_login(self.vendeur)
        self.assertEqual(self.client.post(reverse("commercial:document_annuler", args=[doc.pk])).status_code, 403)
        self.assertNotEqual(self.client.post(reverse("commercial:document_valider", args=[doc.pk])).status_code, 403)
        doc.refresh_from_db()
        self.assertEqual(doc.statut, Document.VALIDE)

    def test_comptabilite_independante(self):
        self.regler("traitement", d.INTERDIT, module="comptabilite")
        self.client.force_login(self.vendeur)
        self.assertEqual(self.client.get(reverse("comptabilite:ecriture_create")).status_code, 403)
        self.assertEqual(self.client.get(reverse("commercial:documents", args=["ventes"])).status_code, 200)

    def test_api_client_bureau(self):
        self.regler("ventes.facture", d.LECTURE)
        doc = self.facture()
        jeton = Token.objects.create(user=self.vendeur)
        entetes = {"HTTP_AUTHORIZATION": f"Token {jeton.key}"}
        self.assertEqual(self.client.get(f"/api/documents/{doc.pk}/", **entetes).status_code, 200)
        self.assertEqual(self.client.post(f"/api/documents/{doc.pk}/valider/", **entetes).status_code, 403)
        navigation = self.client.get("/api/navigation/?module=commercial", **entetes).json()
        traitement = next(o for o in navigation["onglets"] if o["code"] == "traitement")
        ventes = next(e for e in traitement["elements"] if e["code"] == "ventes.documents")
        facture = next(e for e in ventes["enfants"] if e["code"] == "ventes.facture")
        self.assertEqual(facture["droit"], d.LECTURE)

    def test_ecran_autorisations(self):
        self.client.force_login(self.vendeur)
        self.assertEqual(self.client.get(reverse("commercial:autorisations")).status_code, 403)   # réservé à l'administrateur
        self.client.force_login(self.admin)
        url = reverse("commercial:autorisations")
        reponse = self.client.get(url + f"?profil={self.profil.pk}")
        self.assertContains(reponse, "Documents des ventes")
        self.assertContains(reponse, "Interdire la suppression")
        self.client.post(url, {"action": "droits", "profil": self.profil.pk, "logiciel": "commercial",
                               "droit_traitement": d.LECTURE, "droit_ventes.devis": d.TOUT})
        self.assertEqual(dict(DroitAcces.objects.filter(groupe=self.profil).values_list("code", "niveau")),
                         {"traitement": d.LECTURE, "ventes.devis": d.TOUT})
        self.client.post(url, {"action": "droits", "profil": self.profil.pk, "logiciel": "commercial", "droit_traitement": ""})
        self.assertFalse(DroitAcces.objects.filter(groupe=self.profil).exists())        # « Hérité » efface le réglage
        self.client.post(url, {"action": "utilisateur", "nom_utilisateur": "magasin", "mot_de_passe": "Magasin-2026",
                               "profil_utilisateur": self.profil.pk})
        self.assertTrue(get_user_model().objects.get(username="magasin").groups.filter(pk=self.profil.pk).exists())
        self.client.post(url, {"action": "profil_creer", "nom": "Comptable"})
        self.assertTrue(Group.objects.filter(name="Comptable").exists())
