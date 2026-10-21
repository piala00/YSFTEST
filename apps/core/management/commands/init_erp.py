import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.comptabilite.models import Compte, Journal
from apps.comptabilite.plan_syscohada import JOURNAUX, LETTRABLES_PREFIXES, PLAN
from apps.core.models import Exercice, Societe


class Command(BaseCommand):
    help = "Initialise l'ERP : plan comptable SYSCOHADA, journaux, exercice courant (et données de démo)."

    def add_arguments(self, parser):
        parser.add_argument("--demo", action="store_true", help="Crée des tiers, articles et documents de démonstration")
        parser.add_argument("--admin", metavar="MOT_DE_PASSE", help="Crée le super-utilisateur « admin » avec ce mot de passe")

    def log(self, message):
        if self.verbosity:
            self.stdout.write(message)

    @transaction.atomic
    def handle(self, *args, **options):
        self.verbosity = options["verbosity"]
        Societe.get()
        crees = 0
        for numero, intitule in PLAN:
            _, created = Compte.objects.get_or_create(
                numero=numero,
                defaults={"intitule": intitule, "lettrable": numero.startswith(LETTRABLES_PREFIXES)},
            )
            crees += created
        self.log(f"Plan comptable : {crees} compte(s) créé(s), {Compte.objects.count()} au total.")

        for code, intitule, type_journal, compte in JOURNAUX:
            Journal.objects.get_or_create(
                code=code,
                defaults={
                    "intitule": intitule, "type_journal": type_journal,
                    "compte_tresorerie": Compte.objects.get(numero=compte) if compte else None,
                },
            )
        self.log(f"Journaux : {Journal.objects.count()}.")

        annee = datetime.date.today().year
        Exercice.objects.get_or_create(
            code=str(annee),
            defaults={"date_debut": datetime.date(annee, 1, 1), "date_fin": datetime.date(annee, 12, 31)},
        )
        self.log(f"Exercice {annee} prêt.")

        if options["admin"]:
            User = get_user_model()
            if not User.objects.filter(username="admin").exists():
                User.objects.create_superuser("admin", "", options["admin"])
                self.log("Super-utilisateur « admin » créé.")

        if options["demo"]:
            self._demo()
        self.log(self.style.SUCCESS("Initialisation terminée."))

    def _demo(self):
        from apps.commercial.models import Article, Document, FamilleArticle, LigneDocument, Reglement, Tiers

        if Tiers.objects.exists():
            self.log("Données de démo déjà présentes, ignorées.")
            return
        societe = Societe.get()
        societe.raison_sociale = "GTC SARL (démo)"
        societe.ville = "Bertoua"
        societe.save()

        clients = [
            Tiers.objects.create(code="C0001", nom="Boutique Mbarga", ville="Bertoua", telephone="+237 690 00 00 01"),
            Tiers.objects.create(code="C0002", nom="Quincaillerie de l'Est", ville="Abong-Mbang"),
            Tiers.objects.create(code="C0003", nom="Ets Garoua-Boulaï Distribution", ville="Garoua-Boulaï"),
        ]
        fournisseurs = [
            Tiers.objects.create(code="F0001", nom="CIMENCAM", type_tiers=Tiers.FOURNISSEUR, ville="Douala"),
            Tiers.objects.create(code="F0002", nom="Sodecoton Distribution", type_tiers=Tiers.FOURNISSEUR, ville="Garoua"),
        ]
        famille = FamilleArticle.objects.create(code="BTP", libelle="Matériaux de construction")
        articles = [
            Article.objects.create(reference="CIM50", designation="Ciment CPJ 42.5 - sac 50 kg", famille=famille,
                                   unite="Sac", prix_achat=Decimal("4800"), prix_vente=Decimal("5600"), stock_minimum=50),
            Article.objects.create(reference="FER10", designation="Fer à béton Ø10 - barre 12 m", famille=famille,
                                   unite="Barre", prix_achat=Decimal("3900"), prix_vente=Decimal("4700"), stock_minimum=30),
            Article.objects.create(reference="TOLE", designation="Tôle bac alu 6/10", famille=famille,
                                   unite="Feuille", prix_achat=Decimal("6500"), prix_vente=Decimal("7800"), stock_minimum=20),
            Article.objects.create(reference="LIVR", designation="Prestation de livraison", nature=Article.SERVICE,
                                   unite="Forfait", prix_vente=Decimal("15000"), suivi_stock=False),
        ]

        today = datetime.date.today()
        debut = datetime.date(today.year, 1, 1)

        def doc(type_document, tiers, jours, lignes, valider=True):
            date = min(debut + datetime.timedelta(days=jours), today)
            d = Document.objects.create(type_document=type_document, tiers=tiers, date=date)
            for article, qte, prix in lignes:
                LigneDocument.objects.create(document=d, article=article, quantite=qte, prix_unitaire=prix,
                                             taux_tva=article.taux_tva)
            d.recalculer()
            if valider:
                d.valider()
            return d

        from apps.comptabilite.models import Compte
        from apps.comptabilite.services import creer_ecriture

        creer_ecriture(Journal.objects.get(code="OD"), debut, "Apport en capital", [
            {"compte": Compte.objects.get(numero="5211"), "debit": Decimal("10000000")},
            {"compte": Compte.objects.get(numero="1013"), "credit": Decimal("10000000")},
        ])
        a = articles
        doc(Document.ACHAT_FACTURE, fournisseurs[0], 5, [(a[0], 1500, a[0].prix_achat)])
        doc(Document.ACHAT_FACTURE, fournisseurs[1], 8, [(a[1], 500, a[1].prix_achat), (a[2], 120, a[2].prix_achat)])
        jours = 15
        for mois in range(max(today.month, 1)):
            for i, client in enumerate(clients):
                jours = min(mois * 30 + 10 + i * 5, (today - debut).days)
                doc(Document.FACTURE, client, jours, [
                    (a[0], 20 + 5 * i + mois * 3, a[0].prix_vente),
                    (a[1], 10 + i * 2, a[1].prix_vente),
                    (a[3], 1, a[3].prix_vente),
                ])
        doc(Document.DEVIS, clients[0], jours, [(a[2], 40, a[2].prix_vente)])

        from apps.comptabilite.services import constater_variation_stock

        constater_variation_stock(today)
        caisse = Journal.objects.get(code="CA")
        banque = Journal.objects.get(code="BQ")
        for client in clients[:2]:
            Reglement(tiers=client, journal=caisse, mode=Reglement.ESPECES,
                      montant=Decimal("500000"), date=today).enregistrer()
        Reglement(tiers=fournisseurs[0], journal=banque, mode=Reglement.VIREMENT,
                  montant=Decimal("1500000"), date=today).enregistrer()
        self.log("Données de démonstration créées.")
