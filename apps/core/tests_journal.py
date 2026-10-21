"""Journal des événements : création, modification, validation, suppression et connexions sont tracées."""
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token

from apps.commercial.models import Article, Document, LigneDocument, Tiers
from apps.core.models import JournalEvenement


class JournalEvenementsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        cls.admin = get_user_model().objects.create_superuser("chef", "", "Chef-2026")
        cls.vendeur = get_user_model().objects.create_user("vendeur", "", "Vendeur-2026")

    def dernier(self, **filtres):
        return JournalEvenement.objects.filter(**filtres).first()

    def test_creation_et_modification_depuis_le_web(self):
        self.client.force_login(self.vendeur)
        self.client.post(reverse("commercial:tiers_create") + "?type=CLIENT",
                         {"type_tiers": "CLIENT", "code": "CJOUR", "nom": "Client journal", "delai_paiement": 30,
                          "plafond_credit": 0, "code_risque": "AVERTIR", "assujetti_tva": "on", "actif": "on"})
        tiers = Tiers.objects.get(code="CJOUR")
        creation = self.dernier(action="CREATION", objet_type="Tiers")
        self.assertEqual((creation.utilisateur, creation.objet_libelle), (self.vendeur, str(tiers)))
        self.assertEqual(creation.logiciel, "Gestion commerciale")
        tiers.ville = "Bertoua"
        tiers.save()
        modification = self.dernier(action="MODIFICATION", objet_type="Tiers")
        self.assertEqual(modification.details["champs"]["ville"], ["", "Bertoua"])

    def test_validation_et_suppression(self):
        client = Tiers.objects.create(code="C1", nom="Client")
        article = Article.objects.create(reference="A1", designation="Article", suivi_stock=False)
        doc = Document.objects.create(type_document=Document.FACTURE, tiers=client)
        LigneDocument.objects.create(document=doc, article=article, quantite=1, prix_unitaire=1000)
        doc.recalculer()
        doc.valider()
        validation = self.dernier(action="VALIDATION", objet_type=Document._meta.verbose_name.capitalize())
        self.assertIsNotNone(validation)
        self.assertEqual(validation.details["champs"]["statut"], ["BROUILLON", "VALIDE"])
        self.assertEqual(validation.logiciel, "serveur")                        # hors requête : commande, test…
        self.assertTrue(JournalEvenement.objects.filter(action="VALIDATION", objet_type="Écriture").exists())
        Article.objects.create(reference="A2", designation="Inutilisé").delete()
        suppression = self.dernier(action="SUPPRESSION")
        self.assertEqual(suppression.details["fiche"]["reference"], "A2")

    def test_connexions(self):
        self.client.post(reverse("login"), {"username": "vendeur", "password": "mauvais"})
        self.assertEqual(self.dernier(action="ECHEC_CONNEXION").objet_libelle, "vendeur")
        self.client.post(reverse("login"), {"username": "vendeur", "password": "Vendeur-2026"})
        self.assertEqual(self.dernier(action="CONNEXION").utilisateur, self.vendeur)

    def test_client_bureau(self):
        jeton = Token.objects.create(user=self.vendeur)
        self.client.post("/api/articles/", {"reference": "ABUREAU", "designation": "Saisi au bureau"},
                         HTTP_AUTHORIZATION=f"Token {jeton.key}")
        evenement = self.dernier(action="CREATION", objet_libelle__contains="ABUREAU")
        self.assertEqual((evenement.utilisateur, evenement.logiciel), (self.vendeur, "bureau (API)"))

    def test_ecran_reserve_a_l_administrateur(self):
        Tiers.objects.create(code="C2", nom="Client deux")
        url = reverse("commercial:journal_evenements")
        self.client.force_login(self.vendeur)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.admin)
        reponse = self.client.get(url + "?action=CREATION&q=Client deux")
        self.assertContains(reponse, "Client deux")
        self.assertEqual(len(reponse.context["page"]), 1)
