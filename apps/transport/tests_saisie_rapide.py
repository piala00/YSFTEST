"""Parcours fictifs du guichet : identités, autorisations, impression et non-duplication."""
import importlib
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
from unittest import skipUnless

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from apps.core import droits as d
from apps.core.models import AccesLogiciel, DroitAcces

from .contacts import memoriser, nouveau_jeton
from .models import Billet, Colis, Depart
from .models_contacts import PersonneGuichet, SaisieGuichet


class ChampsHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.noms = []

    def handle_starttag(self, tag, attributs):
        if tag in ("input", "select", "textarea"):
            self.noms.append(dict(attributs).get("name"))


class SaisieRapideTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", "--activite", "transport", "--demo", verbosity=0)
        cls.admin = get_user_model().objects.create_superuser("guichet-test", "", "x")

    def setUp(self):
        self.client.force_login(self.admin)
        self.depart = Depart.objects.filter(statut=Depart.PROGRAMME, site_origine="").first()
        self.vente = reverse("transport:billet_vente")
        self.envoi = reverse("transport:colis_create")

    def billet(self, **champs):
        donnees = {"depart": self.depart.pk, "voyageur": "Alice Fictive", "telephone": "699000001",
                   "piece_identite": "DEMO-CNI-1", "siege": 5, "paiement": "ESPECES", "interface_rapide": "1",
                   "cle_saisie": nouveau_jeton(self.admin, "billet")}
        donnees.update(champs)
        return donnees

    def colis(self, **champs):
        donnees = {"nature": "COLIS", "gare_depart": self.depart.ligne.gare_depart_id,
                   "gare_arrivee": self.depart.ligne.gare_arrivee_id, "expediteur": "Alice Fictive",
                   "tel_expediteur": "699000001", "destinataire": "Bob Fictif", "tel_destinataire": "699000002",
                   "description": "Carton fictif", "nombre": 1, "poids": 0, "valeur_declaree": 0,
                   "contre_remboursement": 0, "prix": 1500, "port": "DU", "interface_rapide": "1",
                   "cle_saisie": nouveau_jeton(self.admin, "colis")}
        donnees.update(champs)
        return donnees

    def rechercher(self, telephone="699000001", service="billetterie", **champs):
        return self.client.post(reverse("transport:contacts_" + service), {"telephone": telephone, **champs})

    def test_champs_tous_presents_une_fois_et_ordre_vertical(self):
        for url, debut in ((self.vente, ["depart", "telephone", "voyageur", "piece_identite"]),
                           (self.envoi, ["tel_expediteur", "expediteur", "tel_destinataire", "destinataire"])):
            page = self.client.get(url)
            self.assertEqual(page.status_code, 200)
            parser = ChampsHTML()
            parser.feed(page.content.decode())
            form = page.context["form"]
            for nom in form.fields:
                self.assertEqual(parser.noms.count(nom), 1, nom)
            positions = [parser.noms.index(nom) for nom in debut]
            self.assertEqual(positions, sorted(positions))
            self.assertTrue(form.initial["cle_saisie"])
            self.assertContains(page, "js/saisie_rapide.js")

    def test_vendre_imprimer_et_suivant_conserve_depart_uniquement(self):
        reponse = self.client.post(self.vente, self.billet(imprimer="1"))
        billet = Billet.objects.get(voyageur="Alice Fictive")
        self.assertEqual(reponse.url, reverse("transport:billet_imprimer", args=[billet.pk]) + "?suivant=1")
        page = self.client.get(reponse.url)
        suivant = self.vente + f"?depart={self.depart.pk}"
        self.assertEqual(page.context["suivant_url"], suivant)
        self.assertContains(page, "afterprint")
        form = self.client.get(suivant).context["form"]
        self.assertEqual(form.initial["depart"].pk, self.depart.pk)
        for champ in ("voyageur", "telephone", "piece_identite", "siege", "personne"):
            self.assertIn(form[champ].value(), (None, ""), champ)
        self.assertEqual(PersonneGuichet.objects.get().piece_identite, "DEMO-CNI-1")

    def test_numero_normalise_identite_seule_et_recherche_sans_ecriture(self):
        self.client.post(self.vente, self.billet())
        avant = PersonneGuichet.objects.count()
        reponse = self.rechercher("00237 699 000 001")
        self.assertEqual(reponse.status_code, 200)
        p = reponse.json()["personnes"][0]
        self.assertEqual(set(p), {"id", "nom", "telephone", "piece_identite"})
        self.assertEqual(p["nom"], "Alice Fictive")
        self.assertEqual(PersonneGuichet.objects.count(), avant)
        self.assertIn("no-store", reponse["Cache-Control"])
        self.assertEqual(self.client.get(reverse("transport:contacts_billetterie")).status_code, 405)

    def test_telephone_partage_et_cni_differentes_ne_fusionnent_pas(self):
        a = memoriser("Alice Fictive", "699000001", "DEMO-1", self.admin)
        b = memoriser("Bob Fictif", "+237699000001", "DEMO-2", self.admin)
        homonyme = memoriser("Alice Fictive", "699000001", "DEMO-3", self.admin)
        self.assertEqual(len(self.rechercher().json()["personnes"]), 3)
        self.assertNotEqual(a.pk, homonyme.pk)
        self.assertNotEqual(a.pk, b.pk)
        self.assertEqual(memoriser("Alice Fictive", "699000001", "DEMO-1", self.admin).pk, a.pk)

    def test_correction_cni_contact_selectionne_sans_changer_ancien_billet(self):
        self.client.post(self.vente, self.billet())
        ancien = Billet.objects.get(voyageur="Alice Fictive")
        p = PersonneGuichet.objects.get()
        reponse = self.client.post(self.vente, self.billet(siege=6, personne=str(p.pk), piece_identite="DEMO-CNI-2"))
        self.assertEqual(reponse.status_code, 302)
        p.refresh_from_db()
        ancien.refresh_from_db()
        self.assertEqual(p.piece_identite, "DEMO-CNI-2")
        self.assertEqual(ancien.piece_identite, "DEMO-CNI-1")
        self.assertEqual(PersonneGuichet.objects.count(), 1)
        self.assertEqual(Billet.objects.filter(voyageur="Alice Fictive").count(), 2)

    def test_selection_falsifiee_refusee(self):
        p = memoriser("Bob Fictif", "699000002", utilisateur=self.admin)
        avant = Billet.objects.count()
        reponse = self.client.post(self.vente, self.billet(personne=str(p.pk)))
        self.assertEqual(reponse.status_code, 200)
        self.assertTrue(reponse.context["form"].errors)
        self.assertEqual(Billet.objects.count(), avant)
        p.refresh_from_db()
        self.assertEqual(p.nom, "Bob Fictif")

    def test_double_envoi_un_billet_et_une_ecriture(self):
        donnees = self.billet(imprimer="1")
        avant = Billet.objects.count()
        premiere = self.client.post(self.vente, donnees)
        billet = Billet.objects.get(voyageur="Alice Fictive")
        ecriture = billet.ecriture_id
        seconde = self.client.post(self.vente, donnees)
        self.assertEqual(premiere.status_code, 302)
        self.assertEqual(seconde.url, premiere.url)
        self.assertEqual(Billet.objects.count(), avant + 1)
        self.assertEqual(SaisieGuichet.objects.count(), 1)
        billet.refresh_from_db()
        self.assertEqual(billet.ecriture_id, ecriture)
        autre = self.client.post(self.vente, {**donnees, "voyageur": "Autre Fictif", "siege": 6})
        self.assertEqual(autre.status_code, 200)
        self.assertEqual(Billet.objects.count(), avant + 1)

    def test_jeton_manquant_falsifie_ou_autre_utilisateur_refuse(self):
        autre = get_user_model().objects.create_user("autre", "", "x")
        avant = Billet.objects.count()
        for jeton in ("", "invalide", nouveau_jeton(autre, "billet"), nouveau_jeton(self.admin, "colis")):
            self.assertEqual(self.client.post(self.vente, self.billet(cle_saisie=jeton)).status_code, 200)
        self.assertEqual(Billet.objects.count(), avant)
        self.assertFalse(SaisieGuichet.objects.exists())
        self.assertFalse(PersonneGuichet.objects.exists())

    def test_vente_refusee_aucun_contact_ni_operation_partiels(self):
        self.client.post(self.vente, self.billet())
        avant = Billet.objects.count()
        reponse = self.client.post(self.vente, self.billet(voyageur="Autre Fictif", telephone="699000009"))
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(Billet.objects.count(), avant)
        self.assertEqual(SaisieGuichet.objects.count(), 1)
        self.assertEqual(PersonneGuichet.objects.count(), 1)

    def test_colis_deux_contacts_impression_et_double_envoi(self):
        donnees = self.colis(imprimer="1")
        avant = Colis.objects.count()
        reponse = self.client.post(self.envoi, donnees)
        colis = Colis.objects.get(expediteur="Alice Fictive")
        self.assertEqual(reponse.url, reverse("transport:colis_imprimer", args=[colis.pk]) + "?suivant=1")
        self.assertEqual(self.client.post(self.envoi, donnees).url, reponse.url)
        self.assertEqual(Colis.objects.count(), avant + 1)
        self.assertEqual(PersonneGuichet.objects.count(), 2)
        self.assertEqual(self.client.get(reponse.url).context["suivant_url"], self.envoi + "?nature=COLIS")
        for tel, nom in (("699000001", "Alice Fictive"), ("699000002", "Bob Fictif")):
            p = self.rechercher(tel, service="colis").json()["personnes"][0]
            self.assertEqual(p["nom"], nom)
            self.assertNotIn("piece_identite", p)

    def test_coordonnees_absentes_ou_invalides_ne_bloquent_pas_vente(self):
        reponse = self.client.post(self.vente, self.billet(telephone="non renseigné"))
        self.assertEqual(reponse.status_code, 302)
        self.assertFalse(PersonneGuichet.objects.exists())
        self.assertEqual(self.rechercher("699").json()["personnes"], [])

    def test_recherche_nom_limitee_et_sans_creation(self):
        for i in range(12):
            memoriser(f"Élodie Démo {i}", "699000001", utilisateur=self.admin)
        resultat = self.rechercher("", nom="elodie").json()
        self.assertTrue(resultat["limite"])
        self.assertEqual(len(resultat["personnes"]), 10)
        self.assertEqual(self.rechercher("", nom="el").json()["personnes"], [])

    def test_recherche_respecte_acces_et_droits_du_service(self):
        user = get_user_model().objects.create_user("lecture", "", "x")
        groupe = Group.objects.create(name="Lecture guichet")
        user.groups.add(groupe)
        DroitAcces.objects.create(groupe=groupe, module="billetterie", code="billetterie.vendre", niveau=d.LECTURE)
        self.client.force_login(user)
        self.assertEqual(self.rechercher().status_code, 403)
        self.assertEqual(self.rechercher(service="colis", nature="INCONNU").status_code, 403)
        AccesLogiciel.objects.create(utilisateur=user, module="colis", acces=d.AUCUN)
        self.assertEqual(self.rechercher(service="colis").status_code, 403)
        self.client.logout()
        self.assertEqual(self.rechercher().status_code, 302)

    def test_recherche_post_exige_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(reverse("transport:contacts_billetterie"), {"telephone": "699000001"}).status_code, 403)

    def test_reprise_historique_locale_sans_changer_les_pieces(self):
        self.client.post(self.vente, self.billet())
        self.client.post(self.envoi, self.colis())
        avant = list(Billet.objects.values_list("pk", "voyageur", "telephone", "piece_identite", "ecriture_id"))
        distant = Billet.objects.get(voyageur="Alice Fictive")
        Billet.objects.filter(pk=distant.pk).update(site_origine="AUTRE")
        PersonneGuichet.objects.all().delete()
        migration = importlib.import_module("apps.transport.migrations.0017_coordonnees_guichet")
        editeur = SimpleNamespace(connection=SimpleNamespace(alias="default"))
        migration.reprendre(apps, editeur)
        self.assertEqual(PersonneGuichet.objects.count(), 2)
        self.assertFalse(PersonneGuichet.objects.exclude(piece_identite="").exists())  # billet distant exclu
        Billet.objects.filter(pk=distant.pk).update(site_origine="")
        migration.reprendre(apps, editeur)
        self.assertEqual(PersonneGuichet.objects.filter(piece_identite="DEMO-CNI-1").count(), 1)
        migration.reprendre(apps, editeur)
        self.assertEqual(PersonneGuichet.objects.filter(piece_identite="DEMO-CNI-1").count(), 1)
        self.assertEqual(list(Billet.objects.values_list("pk", "voyageur", "telephone", "piece_identite", "ecriture_id")), avant)


class ClavierJavaScriptTests(SimpleTestCase):
    @skipUnless(shutil.which("node"), "Node nécessaire aux scénarios JavaScript")
    def test_scenarios_clavier_et_recherche_du_script_livre(self):
        resultat = subprocess.run([shutil.which("node"), str(Path(settings.BASE_DIR) / "tests_js/test_saisie_rapide.js")],
                                  capture_output=True, text=True, timeout=25)
        self.assertEqual(resultat.returncode, 0, resultat.stdout + resultat.stderr)
        self.assertIn("13 scénarios JavaScript réussis", resultat.stdout)
