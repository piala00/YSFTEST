import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TransactionTestCase, SimpleTestCase
from django.urls import reverse

from apps.comptabilite.models import Ecriture
from apps.transport.models import Billet, Colis, Depart

from . import sauvegarde as s
from .models import Societe


class SauvegardeCompleteTests(TransactionTestCase):
    def setUp(self):
        call_command("init_erp", "--activite", "transport", "--demo", verbosity=0)
        get_user_model().objects.create_superuser("admin-sauvegarde", "", "Essai-2030-ok")

    def test_transport_comptabilite_et_licence_conserves_au_retour(self):
        from apps.licences import licence
        from apps.licences.models import EtatLicence
        from apps.personnel.models import Employe
        from apps.echanges import lots
        from apps.echanges.models import Evenement

        lots.configurer_siege("SIEGE", "Siège fictif")
        depart = Depart.objects.filter(statut=Depart.PROGRAMME).first()
        billet = Billet(depart=depart, voyageur="Passager à conserver", telephone="699000001").vendre()
        colis = Colis(gare_depart=depart.ligne.gare_depart, gare_arrivee=depart.ligne.gare_arrivee,
                      expediteur="Expéditeur Fictif", destinataire="Destinataire Fictif", prix=1500).enregistrer()
        code = licence.fc.installation_courte_creer()
        licence.enregistrer_cle_installation(code)
        comptes = (Billet.objects.count(), Colis.objects.count(), Ecriture.objects.count(), Employe.objects.count())
        evenements = Evenement.objects.count()
        contenu = s.sauvegarder()
        modeles = {o.get("model") for o in json.loads(contenu)[1:]}
        self.assertTrue({"transport.billet", "transport.colis", "personnel.employe", "licences.etatlicence"} <= modeles)
        Billet(depart=depart, voyageur="Après sauvegarde").vendre()
        s.restaurer(contenu)
        self.assertEqual((Billet.objects.count(), Colis.objects.count(), Ecriture.objects.count(), Employe.objects.count()), comptes)
        self.assertEqual(Billet.objects.get(pk=billet.pk).voyageur, "Passager à conserver")
        self.assertEqual(Colis.objects.get(pk=colis.pk).prix, colis.prix)
        self.assertEqual(licence.cle_installation()["texte"], code)
        self.assertTrue(EtatLicence.objects.exists())
        self.assertFalse(Billet.objects.filter(voyageur="Après sauvegarde").exists())
        self.assertEqual(Evenement.objects.count(), evenements)  # le rechargement ne republie pas les pièces

    def test_ancienne_archive_partielle_refusee_avant_vidage(self):
        avant = list(Societe.objects.values())
        ancienne = json.loads(s.sauvegarder())
        ancienne[0]["version"] = 1
        ancienne[0].pop("applications", None)
        with self.assertRaisesMessage(ValueError, "partielle"):
            s.restaurer(json.dumps(ancienne))
        self.assertEqual(list(Societe.objects.values()), avant)
        self.assertTrue(get_user_model().objects.filter(username="admin-sauvegarde").exists())

    def test_archive_tronquee_ou_modele_exterieur_refuse_sans_ecriture(self):
        contenu = json.loads(s.sauvegarder())
        contenu.pop()
        with self.assertRaisesMessage(ValueError, "incomplète"):
            s.restaurer(json.dumps(contenu))
        contenu = json.loads(s.sauvegarder())
        contenu.append({"model": "sessions.session", "pk": "interdit", "fields": {}})
        contenu[0]["objets"] += 1
        contenu[0]["sha256"] = s.empreinte_objets(contenu[1:])
        with self.assertRaisesMessage(ValueError, "non admis"):
            s.restaurer(json.dumps(contenu))
        self.assertTrue(Societe.objects.exists())

    def test_champ_modifie_sans_changer_nombre_objets_refuse(self):
        contenu = json.loads(s.sauvegarder())
        societe = next(o for o in contenu if o.get("model") == "core.societe")
        societe["fields"]["raison_sociale"] = "Altération fictive"
        avant = list(Societe.objects.values())
        with self.assertRaisesMessage(ValueError, "altérée"):
            s.restaurer(json.dumps(contenu))
        self.assertEqual(list(Societe.objects.values()), avant)

    def test_restauration_par_un_administrateur_absent_du_fichier(self):
        from .models import JournalEvenement

        contenu = s.sauvegarder()
        autre = get_user_model().objects.create_superuser("admin-apres-export", "", "Essai-2030-ok")
        self.client.force_login(autre)
        page = self.client.post(reverse("commercial:sauvegarde"), {"action": "restaurer", "confirmation": "RESTAURER",
                    "fichier": SimpleUploadedFile("sauvegarde.json", contenu.encode())})
        self.assertEqual(page.status_code, 302)
        self.assertFalse(get_user_model().objects.filter(username="admin-apres-export").exists())
        self.assertNotIn("_auth_user_id", self.client.session)
        evenement = JournalEvenement.objects.filter(action="RESTAURATION").latest("pk")
        self.assertEqual(evenement.details["auteur_avant_restauration"], "admin-apres-export")

    def test_sauvegarde_native_en_echec_empeche_restauration_json(self):
        from . import poste

        admin = get_user_model().objects.get(username="admin-sauvegarde")
        self.client.force_login(admin)
        contenu = s.sauvegarder()
        avant = list(Societe.objects.values())
        with mock.patch.dict(poste.ACTIONS, {"sauvegarder": mock.Mock(side_effect=OSError("disque plein"))}), \
                mock.patch.object(s, "restaurer") as restaurer:
            self.client.post(reverse("transport:sauvegarde"), {"action": "restaurer", "confirmation": "RESTAURER",
                "fichier": SimpleUploadedFile("sauvegarde.json", contenu.encode())})
        restaurer.assert_not_called()
        self.assertEqual(list(Societe.objects.values()), avant)

class CommandesClientTests(SimpleTestCase):
    def test_commandes_python_et_ancienne_simulation_refusees_avant_ouverture_de_base(self):
        import sys
        from .tests_executable import lanceur

        with mock.patch.object(sys, "frozen", True, create=True), \
                mock.patch.object(lanceur, "edition", return_value="transport"), \
                mock.patch.object(lanceur, "preparer_environnement") as preparer, mock.patch("builtins.print"):
            for commande in (["manage", "shell"], ["manage", "runserver"], ["simulation", "1"]):
                self.assertEqual(lanceur.main(commande), 2)
        preparer.assert_not_called()

