"""Recette du logiciel Comptabilité (skill « sage100-comptabilite-v5-v12-expert ») et scénarios
inter-modules de la bibliothèque Sage (SCENARIOS_INTER_MODULES.md, C01 à C10), sur société fictive.
"""
import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.commercial.models import Article, Document, LigneDocument, Reglement, Tiers
from apps.core.models import Exercice
from apps.core.navigation import COMPTABILITE

from . import etats, services
from .models import Banque, Compte, Ecriture, Journal, LigneEcriture, SectionAnalytique, Taxe


class BaseCompta(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("init_erp", verbosity=0, regime_tva="automatique")
        cls.exercice = Exercice.objects.first()
        cls.date = cls.exercice.date_debut + datetime.timedelta(days=10)
        cls.client_ = Tiers.objects.create(code="CRECETTE", nom="Client recette")
        cls.client2 = Tiers.objects.create(code="CRECETTE2", nom="Client recette 2")
        cls.article = Article.objects.create(reference="ARECETTE", designation="Article recette", prix_achat=800,
                                             prix_vente=1000)

    def ecrire(self, lignes, journal="OD", date=None, valider=True):
        return services.creer_ecriture(
            Journal.objects.get(code=journal), date or self.date, "Recette",
            [{"compte": Compte.objects.get(numero=n), "debit": d, "credit": c, **extra} for n, d, c, *reste in lignes
             for extra in [reste[0] if reste else {}]],
            valider=valider,
        )

    def ligne(self, ecriture, numero):
        return ecriture.lignes.get(compte__numero=numero)


class StructureTests(BaseCompta):
    def test_parametrage_initial(self):
        self.assertEqual(Taxe.objects.get(code="C19").compte.numero, "4431")
        self.assertEqual(Taxe.objects.get(code="D19").taux, Decimal("19.25"))
        self.assertEqual(Banque.objects.get(code="BQ1").compte.numero, "5211")
        self.assertTrue(SectionAnalytique.objects.filter(plan="Agences").exists())

    def test_exercice_non_cloturable_par_la_fiche(self):
        from apps.core.forms import ExerciceForm

        self.assertNotIn("cloture", ExerciceForm().fields)


class LettrageTests(BaseCompta):
    def test_lettrage_automatique_montants_identiques_puis_solde(self):
        f1 = self.ecrire([("4111", 1000, 0, {"tiers": self.client_}), ("701", 0, 1000)], journal="VT")
        f2 = self.ecrire([("4111", 3000, 0, {"tiers": self.client_}), ("701", 0, 3000)], journal="VT")
        r1 = self.ecrire([("5711", 1000, 0), ("4111", 0, 1000, {"tiers": self.client_})], journal="CA")
        r2 = self.ecrire([("5711", 1000, 0), ("4111", 0, 1000, {"tiers": self.client_})], journal="CA")
        r3 = self.ecrire([("5711", 2000, 0), ("4111", 0, 2000, {"tiers": self.client_})], journal="CA")
        # Un autre tiers au même montant ne doit pas être lettré avec le premier
        f3 = self.ecrire([("4111", 1000, 0, {"tiers": self.client2}), ("701", 0, 1000)], journal="VT")

        codes = services.lettrage_automatique()
        self.assertEqual(codes, 2)
        a = self.ligne(f1, "4111").lettrage
        self.assertTrue(a)
        self.assertEqual(self.ligne(r1, "4111").lettrage, a)
        b = self.ligne(f2, "4111").lettrage
        self.assertEqual({self.ligne(r2, "4111").lettrage, self.ligne(r3, "4111").lettrage}, {b})
        self.assertEqual(self.ligne(f3, "4111").lettrage, "")

    def test_paiement_partiel_reste_non_lettre_puis_delettrage(self):  # C07
        f = self.ecrire([("4111", 5000, 0, {"tiers": self.client_}), ("701", 0, 5000)], journal="VT")
        self.ecrire([("5711", 2000, 0), ("4111", 0, 2000, {"tiers": self.client_})], journal="CA")
        self.assertEqual(services.lettrage_automatique(), 0)
        self.assertEqual(self.ligne(f, "4111").lettrage, "")
        r = self.ecrire([("5711", 3000, 0), ("4111", 0, 3000, {"tiers": self.client_})], journal="CA")
        self.assertEqual(services.lettrage_automatique(), 1)
        code = self.ligne(f, "4111").lettrage
        self.assertEqual(self.ligne(r, "4111").lettrage, code)
        self.assertEqual(services.delettrer(Compte.objects.get(numero="4111"), code), 3)
        self.assertEqual(services.lignes_non_lettrees(Compte.objects.get(numero="4111")).count(), 3)


class RapprochementTests(BaseCompta):
    def test_pointage_et_solde_banque_attendu(self):
        compte = Banque.objects.get(code="BQ1").compte
        e1 = self.ecrire([("5211", 100_000, 0), ("101", 0, 100_000)], journal="BQ")
        self.ecrire([("601", 30_000, 0), ("5211", 0, 30_000)], journal="BQ")          # chèque non encaissé
        situation = services.rapprochement(compte, self.date)
        self.assertEqual(situation["solde_comptable"], Decimal("70000"))
        self.assertEqual(situation["non_pointees"].count(), 2)
        services.pointer([self.ligne(e1, "5211")], self.date)
        situation = services.rapprochement(compte, self.date)
        self.assertEqual(situation["non_pointe_credit"], Decimal("30000"))
        # La banque n'a pas encore débité le chèque : son relevé affiche 100 000
        self.assertEqual(situation["solde_banque_theorique"], Decimal("100000"))


class CloturesTests(BaseCompta):
    def test_cloture_des_journaux(self):
        journal = Journal.objects.get(code="OD")
        journal.cloture_au = self.date
        journal.save()
        with self.assertRaises(ValidationError):
            self.ecrire([("5711", 1000, 0), ("101", 0, 1000)])
        self.ecrire([("5711", 1000, 0), ("101", 0, 1000)], journal="CA")   # les autres journaux restent ouverts

    def test_brouillard_bloque_la_cloture(self):
        self.ecrire([("5711", 1000, 0), ("101", 0, 1000)], valider=False)
        with self.assertRaises(ValidationError):
            services.cloturer_exercice(self.exercice)

    def test_cloture_exercice_reports_a_nouveau(self):
        self.ecrire([("5211", 1_000_000, 0), ("101", 0, 1_000_000)])
        self.ecrire([("601", 200_000, 0), ("4011", 0, 200_000)], journal="AC")
        self.ecrire([("4111", 500_000, 0, {"tiers": self.client_}), ("701", 0, 500_000)], journal="VT")
        self.ecrire([("4111", 100_000, 0, {"tiers": self.client2}), ("701", 0, 100_000)], journal="VT")
        bilan_n = etats.bilan(self.exercice.date_fin)

        r = services.cloturer_exercice(self.exercice)
        self.exercice.refresh_from_db()
        self.assertTrue(self.exercice.cloture)
        self.assertEqual(r["resultat"], Decimal("400000"))
        suivant = r["exercice_suivant"]
        self.assertEqual(suivant.date_debut, self.exercice.date_fin + datetime.timedelta(days=1))
        an = r["ecriture"]
        self.assertEqual(an.journal.type_journal, Journal.TYPE_AN)
        self.assertTrue(an.equilibree)
        self.assertEqual(self.ligne(an, "131").credit, Decimal("400000"))
        # Les soldes clients restent détaillés par tiers pour le lettrage de l'exercice suivant
        self.assertEqual(an.lignes.get(compte__numero="4111", tiers=self.client_).debit, Decimal("500000"))
        self.assertEqual(an.lignes.get(compte__numero="4111", tiers=self.client2).debit, Decimal("100000"))
        self.assertFalse(an.lignes.filter(compte__numero__startswith="7").exists())

        # Ouverture N+1 : balance d'à-nouveaux, sans double comptage de l'exercice clôturé
        lignes, totaux = services.balance(suivant.date_debut, suivant.date_fin)
        par_compte = {l["compte"].numero: l for l in lignes}
        self.assertEqual(par_compte["5211"]["an_d"], Decimal("1000000"))
        self.assertEqual(par_compte["5211"]["mvt_d"], 0)
        self.assertNotIn("701", par_compte)
        self.assertEqual(totaux["an_d"], totaux["an_c"])
        bilan_n1 = etats.bilan(suivant.date_debut)
        self.assertTrue(bilan_n1["equilibre"])
        self.assertEqual(bilan_n1["total_actif"], bilan_n["total_actif"])
        self.assertEqual(etats.compte_de_resultat(suivant.date_debut, suivant.date_fin)["valeurs"]["XI"], 0)
        # Le bilan de l'exercice clôturé reste consultable à sa date
        self.assertEqual(etats.bilan(self.exercice.date_fin)["total_actif"], bilan_n["total_actif"])

        with self.assertRaises(ValidationError):
            self.ecrire([("5711", 1000, 0), ("101", 0, 1000)])
        with self.assertRaises(ValidationError):
            services.cloturer_exercice(self.exercice)

    def test_cloture_en_perte(self):
        self.ecrire([("601", 50_000, 0), ("5711", 0, 50_000)])
        r = services.cloturer_exercice(self.exercice)
        self.assertEqual(r["resultat"], Decimal("-50000"))
        self.assertEqual(self.ligne(r["ecriture"], "139").debit, Decimal("50000"))


class InterModulesTests(BaseCompta):
    def facture(self, tiers, quantite=10, **champs):
        doc = Document.objects.create(type_document=Document.FACTURE, tiers=tiers, **champs)
        LigneDocument.objects.create(document=doc, article=self.article, quantite=quantite, prix_unitaire=1000)
        doc.recalculer()
        return doc

    def setUp(self):
        entree = Document.objects.create(type_document=Document.STOCK_ENTREE)
        LigneDocument.objects.create(document=entree, article=self.article, quantite=100, prix_unitaire=800)
        entree.recalculer()
        entree.valider()

    def test_c01_facture_transferee_sans_doublon(self):
        doc = self.facture(self.client_).valider()
        ecriture = doc.ecriture
        self.assertEqual(ecriture.journal.code, "VT")
        self.assertTrue(ecriture.equilibree)
        self.assertEqual(self.ligne(ecriture, "4111").tiers, self.client_)
        self.assertEqual(self.ligne(ecriture, "4431").credit, Decimal("1925"))
        self.assertEqual(services.comptabiliser_document(doc), ecriture)        # 2e transfert : même pièce
        self.assertEqual(Ecriture.objects.filter(origine__contains=doc.numero).count(), 1)

    def test_c07_reglement_partiel_puis_solde_lettre(self):
        doc = self.facture(self.client_).valider()                                 # 11 925 TTC
        Reglement(tiers=self.client_, journal=Journal.objects.get(code="CA"), montant=Decimal("5000"), facture=doc).enregistrer()
        services.lettrage_automatique(tiers=self.client_)
        self.assertEqual(self.ligne(doc.ecriture, "4111").lettrage, "")
        Reglement(tiers=self.client_, journal=Journal.objects.get(code="BQ"), montant=Decimal("6925"), facture=doc).enregistrer()
        services.lettrage_automatique(tiers=self.client_)
        self.assertTrue(self.ligne(doc.ecriture, "4111").lettrage)
        doc.refresh_from_db()
        self.assertEqual(doc.reste_a_payer, 0)

    def test_c08_facture_validee_conserve_sa_piece(self):
        doc = self.facture(self.client_).valider()
        with self.assertRaises(ValidationError):
            doc.annuler()
        self.assertTrue(Ecriture.objects.filter(pk=doc.ecriture_id).exists())

    def test_c10_analytique_par_agence_sans_double_compte(self):
        siege, agence = SectionAnalytique.objects.get(code="SIEGE"), SectionAnalytique.objects.get(code="AGENCE1")
        self.ecrire([("4111", 300_000, 0), ("701", 0, 200_000, {"section": siege}), ("701", 0, 100_000, {"section": agence})],
                    journal="VT")
        self.ecrire([("601", 50_000, 0, {"section": agence}), ("5711", 0, 50_000)])
        self.ecrire([("601", 10_000, 0), ("5711", 0, 10_000)])                   # non ventilée
        lignes = {l["section"].code if l["section"] else None: l
                  for l in services.balance_analytique(self.exercice.date_debut, self.exercice.date_fin)}
        self.assertEqual(lignes["SIEGE"]["resultat"], Decimal("200000"))
        self.assertEqual(lignes["AGENCE1"]["resultat"], Decimal("50000"))
        self.assertEqual(lignes[None]["charges"], Decimal("10000"))
        total = sum(l["resultat"] for l in lignes.values())
        cr = etats.compte_de_resultat(self.exercice.date_debut, self.exercice.date_fin)
        self.assertEqual(total, cr["valeurs"]["XI"])


class EcransComptaTests(BaseCompta):
    def setUp(self):
        user = get_user_model().objects.create_superuser("recette", "", "x")
        self.client.force_login(user)

    def test_ecrans_du_logiciel_comptabilite(self):
        self.ecrire([("5211", 1000, 0), ("101", 0, 1000)], journal="BQ")
        urls = [reverse("comptabilite:structure", args=[s]) for s in ("taxes", "banques", "sections")]
        urls += [reverse("comptabilite:structure_create", args=["taxes"]),
                 reverse("comptabilite:structure_update", args=["banques", Banque.objects.first().pk])]
        urls += [reverse(f"comptabilite:{n}") for n in ("lettrage_auto", "rapprochement", "cloture_exercice",
                                                        "cloture_journaux", "ventilation", "balance_analytique")]
        urls += [reverse("comptabilite:journal") + "?statut=BROUILLARD",
                 reverse("comptabilite:lettrage") + f"?compte={Compte.objects.get(numero='4111').pk}&tout=1"]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 200, url)
        self.assertEqual(self.client.get("/comptabilite/structure/inconnue/").status_code, 404)

    def test_formulaires(self):
        rep = self.client.post(reverse("comptabilite:structure_create", args=["sections"]),
                               {"plan": "Activités", "code": "NEGOCE", "intitule": "Négoce", "actif": "on"})
        self.assertEqual(rep.status_code, 302)
        self.assertTrue(SectionAnalytique.objects.filter(code="NEGOCE").exists())
        od = Journal.objects.get(code="OD")
        self.client.post(reverse("comptabilite:cloture_journaux"), {f"cloture_{od.pk}": "2000-01-31"})
        od.refresh_from_db()
        self.assertEqual(od.cloture_au, datetime.date(2000, 1, 31))
        self.client.post(reverse("comptabilite:cloture_exercice"), {"exercice": self.exercice.pk})
        self.exercice.refresh_from_db()
        self.assertTrue(self.exercice.cloture)

    def test_menus_structure_traitement_etat_relies(self):
        """Les commandes alignées sur Sage 100 Comptabilité ouvrent un écran (plus d'entrée grisée)."""
        relies = {"structure.plan_analytique", "structure.taux_taxes", "structure.banques",
                  "traitement.saisie_analytique", "traitement.lettrage_auto", "traitement.rapprochement",
                  "traitement.fin_exercice.cloture", "traitement.fin_exercice.journaux", "etats.brouillard",
                  "etats.analytique.balance"}

        def parcourir(elements):
            for el in elements:
                yield el
                yield from parcourir(el.enfants)

        trouves = {el.code: el for onglet in COMPTABILITE.onglets for el in parcourir(onglet.elements)}
        for code in relies:
            self.assertTrue(trouves[code].lien(), code)
            self.assertEqual(self.client.get(trouves[code].lien()).status_code, 200, code)


class EtatsTiersTests(BaseCompta):
    def test_justificatif_de_solde_a_date(self):
        j1, j2, j3 = (self.date + datetime.timedelta(days=n) for n in (0, 5, 20))
        f1 = self.ecrire([("4111", 1000, 0, {"tiers": self.client_}), ("701", 0, 1000)], journal="VT", date=j1)
        r1 = self.ecrire([("5711", 1000, 0), ("4111", 0, 1000, {"tiers": self.client_})], journal="CA", date=j2)
        f2 = self.ecrire([("4111", 3000, 0, {"tiers": self.client_}), ("701", 0, 3000)], journal="VT", date=j2)
        r2 = self.ecrire([("5711", 3000, 0), ("4111", 0, 3000, {"tiers": self.client_})], journal="CA", date=j3)
        services.lettrer([self.ligne(f1, "4111"), self.ligne(r1, "4111")])
        services.lettrer([self.ligne(f2, "4111"), self.ligne(r2, "4111")])
        # Au jour j2 : la facture 1 est soldée (lettrée avant), la facture 2 ne l'est pas encore (règlement en j3)
        blocs = services.justificatif_solde(j2, Tiers.CLIENT)
        self.assertEqual(len(blocs), 1)
        self.assertEqual(blocs[0]["solde"], Decimal("3000"))
        self.assertEqual([l.ecriture_id for l in blocs[0]["lignes"]], [f2.pk])
        self.assertEqual(services.justificatif_solde(j3, Tiers.CLIENT), [])
        # Le total justifie le solde comptable du tiers à la date
        solde = sum(l.debit - l.credit for l in services.lignes_validees(date_fin=j2).filter(tiers=self.client_))
        self.assertEqual(solde, Decimal("3000"))

    def test_statistiques_tiers(self):
        self.ecrire([("4111", 4000, 0, {"tiers": self.client_}), ("701", 0, 4000)], journal="VT")
        self.ecrire([("5711", 1000, 0), ("4111", 0, 1000, {"tiers": self.client_})], journal="CA")
        lignes = services.statistiques_tiers(self.exercice.date_debut, self.exercice.date_fin, Tiers.CLIENT)
        stat = next(l for l in lignes if l["tiers"] == self.client_)
        self.assertEqual((stat["facture"], stat["regle"], stat["solde"]), (Decimal("4000"), Decimal("1000"), Decimal("3000")))
        self.assertEqual(stat["taux_recouvrement"], Decimal("25"))
        self.client.force_login(get_user_model().objects.create_superuser("stat", "", "x"))
        for url in (reverse("comptabilite:statistiques_tiers") + "?type=CLIENT",
                    reverse("comptabilite:statistiques_tiers") + "?type=CLIENT&export=csv",
                    reverse("comptabilite:justificatif_solde") + "?type=FOURNISSEUR"):
            self.assertEqual(self.client.get(url).status_code, 200, url)
