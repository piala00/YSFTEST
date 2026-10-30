"""Parcours fictifs : transit sans double encaissement, sièges par portion, secours et droits."""
import datetime
import shutil
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from unittest import skipUnless

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse

from apps.core import droits
from apps.core.models import DroitAcces
from apps.comptabilite.models import Ecriture, LigneEcriture
from .contacts import nouveau_jeton
from .models import ArretLigne, Billet, Chauffeur, Depart, Gare, Ligne, Vehicule
from .models_incidents import Incident


class Champs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.noms = []
        self.visibles = []
        self.details = 0

    def handle_starttag(self, tag, attrs):
        if tag == "details":
            self.details += 1
        attr = dict(attrs)
        if tag in ("input", "select", "textarea"):
            self.noms.append(attr.get("name"))
            if not self.details and attr.get("type") != "hidden":
                self.visibles.append(attr.get("name"))

    def handle_endtag(self, tag):
        if tag == "details":
            self.details -= 1


class GuichetTransitTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0)
        cls.admin = get_user_model().objects.create_superuser("guichet-transit", "", "x")
        cls.a = Gare.objects.create(code="GT-A", nom="Agence Alpha", ville="Alpha")
        cls.b = Gare.objects.create(code="GT-B", nom="Agence Beta", ville="Beta")
        cls.c = Gare.objects.create(code="GT-C", nom="Agence Gamma", ville="Gamma")
        cls.m = Gare.objects.create(code="GT-M", nom="Arrêt Milieu", ville="Milieu")
        cls.l1 = Ligne.objects.create(code="GT-AB", gare_depart=cls.a, gare_arrivee=cls.b, prix_billet=6000)
        cls.l2 = Ligne.objects.create(code="GT-BC", gare_depart=cls.b, gare_arrivee=cls.c, prix_billet=4000)
        ArretLigne.objects.create(ligne=cls.l1, gare=cls.m, ordre=1)
        cls.v1 = Vehicule.objects.create(immatriculation="FICTIF-CAR-1", nombre_places=3)
        cls.v2 = Vehicule.objects.create(immatriculation="FICTIF-CAR-2", nombre_places=3)
        cls.ch = Chauffeur.objects.create(nom="Chauffeur fictif")

    def setUp(self):
        self.client.force_login(self.admin)
        jour = datetime.date.today() - datetime.timedelta(days=1)
        self.d1 = Depart.objects.create(ligne=self.l1, vehicule=self.v1, chauffeur=self.ch, date=jour, heure=datetime.time(6))
        self.d2 = Depart.objects.create(ligne=self.l2, vehicule=self.v2, chauffeur=self.ch, date=jour, heure=datetime.time(15))
        self.vente = reverse("transport:billet_vente")
        self.transit = reverse("transport:billets_transit") + f"?depart={self.d2.pk}"
        self.secours = reverse("transport:transvasement")

    def donnees(self, **kw):
        d = {"depart": self.d1.pk, "voyageur": "Alice Fictive", "telephone": "699000001",
             "piece_identite": "DEMO-123", "siege": 1, "paiement": Billet.ESPECES,
             "cle_saisie": nouveau_jeton(self.admin, "billet"), "interface_rapide": "1", "mode": "direct"}
        d.update(kw)
        return d

    def attente(self):
        billet = Billet(depart=self.d1, gare_arrivee=self.c, voyageur="Transit déjà payé", siege=1).vendre(self.admin)
        self.d1.partir()
        return billet.troncons.get(ordre=2)

    def test_formulaires_compacts_et_champs_sans_doublons(self):
        for mode in ("direct", "transit", "correspondance"):
            page = self.client.get(self.vente, {"depart": self.d1.pk, "mode": mode})
            self.assertEqual(page.status_code, 200)
            parser = Champs()
            parser.feed(page.content.decode())
            for nom in page.context["form"].fields:
                self.assertEqual(parser.noms.count(nom), 1, (mode, nom))
            self.assertContains(page, "--erp-largeur-fenetre:380")
            if mode == "direct":
                self.assertEqual(parser.visibles, ["depart", "telephone", "voyageur", "piece_identite", "siege", "prix", "paiement"])
            elif mode == "transit":
                self.assertIn("gare_montee", parser.visibles)
            else:
                self.assertIn("depart_correspondance", parser.visibles)

    def test_vente_transit_siege_reutilise_apres_arret(self):
        Billet(depart=self.d1, gare_arrivee=self.m, voyageur="Descend au milieu", siege=1, prix=2000).vendre()
        reponse = self.client.post(self.vente, self.donnees(mode="transit", gare_montee=self.m.pk,
            gare_arrivee=self.b.pk, prix=4000, imprimer="1"))
        self.assertEqual(reponse.status_code, 302)
        billet = Billet.objects.get(voyageur="Alice Fictive")
        self.assertEqual((billet.gare_montee, billet.gare_arrivee, billet.siege), (self.m, self.b, 1))
        self.assertEqual(self.d1.places_vendues, 1)
        suivant = self.client.get(reponse.url).context["suivant_url"]
        self.assertEqual(suivant, self.vente + f"?depart={self.d1.pk}&mode=transit")
        self.assertEqual(sum(LigneEcriture.objects.filter(compte__numero__startswith="571").values_list("debit", flat=True)), 6000)

    def test_transit_refuse_origine_et_siege_occupe(self):
        r = self.client.post(self.vente, self.donnees(mode="transit", gare_montee=self.a.pk, prix=4000))
        self.assertEqual(r.status_code, 200)
        self.assertIn("gare_montee", r.context["form"].errors)
        Billet(depart=self.d1, voyageur="Déjà à bord", siege=1).vendre()
        avant = Ecriture.objects.count()
        r = self.client.post(self.vente, self.donnees(mode="transit", gare_montee=self.m.pk, prix=4000))
        self.assertContains(r, "déjà vendu")
        self.assertEqual(Ecriture.objects.count(), avant)
        self.assertFalse(Billet.objects.filter(voyageur="Alice Fictive").exists())

    def test_correspondance_deux_vehicules_un_paiement_et_ticket_complet(self):
        r = self.client.post(self.vente, self.donnees(mode="correspondance", gare_arrivee=self.c.pk,
            depart_correspondance=self.d2.pk, siege_correspondance=3, imprimer="1"))
        self.assertEqual(r.status_code, 302)
        b = Billet.objects.get(voyageur="Alice Fictive")
        self.assertEqual(b.prix, 10000)
        self.assertEqual(list(b.troncons.values_list("part", flat=True)), [6000, 4000])
        self.assertEqual(sum(LigneEcriture.objects.filter(compte__numero__startswith="571").values_list("debit", flat=True)), 10000)
        page = self.client.get(r.url)
        for texte in ("FICTIF-CAR-1", "FICTIF-CAR-2", "Agence Gamma", "siège <strong>3</strong>"):
            self.assertContains(page, texte)
        self.assertTrue(page.context["suivant_url"].endswith("&mode=correspondance"))

    def test_correspondance_sans_second_vehicule_explicitement_a_affecter(self):
        r = self.client.post(self.vente, self.donnees(mode="correspondance", gare_arrivee=self.c.pk, imprimer="1"))
        self.assertEqual(r.status_code, 302)
        self.assertContains(self.client.get(r.url), "Véhicule et siège à choisir à Agence Beta")

    def test_placement_transit_ne_revend_pas_et_resiste_a_la_reemission(self):
        t = self.attente()
        avant = (Billet.objects.count(), Ecriture.objects.count(), t.billet.historique.count())
        self.assertContains(self.client.get(self.transit), t.billet.numero)
        for _ in range(2):
            r = self.client.post(self.transit, {"troncon": t.pk, "siege": 2, "imprimer": "1"})
            self.assertEqual(r.status_code, 302)
        t.refresh_from_db()
        self.assertEqual((t.depart, t.siege), (self.d2, 2))
        self.assertEqual((Billet.objects.count(), Ecriture.objects.count()), avant[:2])
        self.assertEqual(t.billet.historique.count(), avant[2] + 1)
        self.assertEqual(self.client.get(r.url).context["suivant_url"], self.transit)
        self.assertNotContains(self.client.get(self.transit), 'name="troncon"')

    def test_placement_refuse_siege_hors_plage_occupe_et_autre_trajet(self):
        t = self.attente()
        Billet(depart=self.d2, voyageur="Autre", siege=1).vendre()
        avant = Ecriture.objects.count()
        for siege, texte in ((4, "inexistant"), (1, "déjà vendu")):
            self.assertContains(self.client.post(self.transit, {"troncon": t.pk, "siege": siege}), texte)
            t.refresh_from_db()
            self.assertIsNone(t.depart_id)
        mauvaise = reverse("transport:billets_transit") + f"?depart={self.d1.pk}"
        self.assertContains(self.client.post(mauvaise, {"troncon": t.pk, "siege": 2}), "Choisissez un départ local")
        self.assertEqual(Ecriture.objects.count(), avant)

    def test_pas_de_vente_sur_depart_parti_ni_depart_distant(self):
        self.d1.partir()
        r = self.client.post(self.vente, self.donnees(mode="transit", gare_montee=self.m.pk, prix=4000))
        self.assertEqual(r.status_code, 200)
        self.assertIn("depart", r.context["form"].errors)
        Depart.objects.filter(pk=self.d2.pk).update(site_origine="DISTANT")
        r = self.client.get(self.transit)
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.context["depart"])

    def test_get_transvasement_sans_ecriture_et_post_idempotent(self):
        Billet(depart=self.d1, voyageur="V", bagages="Sac", prix_bagages=1000).vendre()
        self.d1.partir()
        avant = Ecriture.objects.count()
        self.assertEqual(self.client.get(self.secours).status_code, 200)
        self.assertEqual(Ecriture.objects.count(), avant)
        d = {"depart": self.d1.pk, "vehicule_secours": self.v2.pk, "part_restante": "40", "lieu": "Milieu", "description": "Panne"}
        for _ in range(2):
            self.assertEqual(self.client.post(self.secours, d).status_code, 302)
        i = Incident.objects.get(depart=self.d1, type_incident=Incident.TRANSBORDEMENT)
        self.assertEqual(Ecriture.objects.count(), avant + 1)
        self.assertEqual(sum(l.debit - l.credit for l in i.ecriture.lignes.all()), 0)
        self.assertEqual(sum(i.ecriture.lignes.filter(vehicule=self.v2).values_list("credit", flat=True)), 2800)
        self.assertEqual(Billet.objects.count(), 1)
        self.assertContains(self.client.post(self.secours, {**d, "part_restante": "50"}), "déjà enregistré")
        self.assertEqual(Ecriture.objects.count(), avant + 1)

    def test_transvasement_refuse_depart_distant_et_meme_car(self):
        self.d1.partir()
        with self.assertRaises(ValidationError):
            Incident.transborder(self.d1, 50, self.v1)
        Depart.objects.filter(pk=self.d1.pk).update(site_origine="DISTANT")
        with self.assertRaisesMessage(ValidationError, "appartient"):
            Incident.transborder(self.d1, 50, self.v2)
        self.assertFalse(Incident.objects.exists())

    def test_droits_serveur_et_ancien_post_ne_contournent_pas_interdiction(self):
        t = self.attente()
        user = get_user_model().objects.create_user("lecture-guichet", "", "x")
        groupe = Group.objects.create(name="Guichet consultation")
        user.groups.add(groupe)
        for code in ("billetterie.transit", "billetterie.transvasement"):
            DroitAcces.objects.create(groupe=groupe, module="billetterie", code=code, niveau=droits.LECTURE)
        self.client.force_login(user)
        self.assertEqual(self.client.post(self.transit, {"troncon": t.pk, "siege": 2}).status_code, 403)
        self.assertEqual(self.client.post(self.secours, {}).status_code, 403)
        url = reverse("transport:depart_detail", args=[self.d1.pk])
        self.assertEqual(self.client.post(url, {"action": "transborder", "vehicule_secours": self.v2.pk, "part_restante": "40"}).status_code, 403)
        self.assertFalse(Incident.objects.exists())

    def test_post_transit_et_secours_exigent_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        for url in (self.transit, self.secours):
            self.assertEqual(client.post(url, {}).status_code, 403)


class FenetreGuichetJavaScriptTests(SimpleTestCase):
    @skipUnless(shutil.which("node"), "Node nécessaire au contrôle des dimensions")
    def test_dimensions_reelles_utilisees_par_fenetres(self):
        r = subprocess.run([shutil.which("node"), str(Path(settings.BASE_DIR) / "tests_js/test_fenetre_guichet.js")],
                           capture_output=True, text=True, timeout=25)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
