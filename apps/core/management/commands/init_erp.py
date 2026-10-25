import datetime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.comptabilite.models import Banque, Compte, Journal, SectionAnalytique, Taxe
from apps.comptabilite.plan_syscohada import JOURNAUX, LETTRABLES_PREFIXES, PLAN, TAXES
from apps.core.models import Exercice, Societe


class Command(BaseCommand):
    help = "Initialise l'ERP : plan comptable SYSCOHADA, journaux, exercice courant (et données de démo)."

    def add_arguments(self, parser):
        parser.add_argument("--demo", action="store_true", help="Crée des tiers, articles et documents de démonstration")
        parser.add_argument("--sahel", action="store_true",
                            help="Crée la société fictive SAHEL DISTRIBUTION des exercices du formateur Sage 100")
        parser.add_argument("--regime-tva", choices=["automatique", "manuelle", "non-assujettie", "assujettie"],
                            help="Configuration de la TVA (automatique = taux du Cameroun ; manuelle = aucune TVA ; "
                                 "« assujettie » = ancien nom d'« automatique »)")
        parser.add_argument("--systeme", choices=["normal", "smt"],
                            help="Système comptable : normal, ou minimal de trésorerie (SMT)")
        parser.add_argument("--activite", choices=["commerce", "transport", "mixte"],
                            help="Activité de la société (transport : billetterie, colis, logistique)")
        parser.add_argument("--admin", metavar="MOT_DE_PASSE", help="Crée le super-utilisateur « admin » (ou lui redonne ce mot de passe)")

    def log(self, message):
        if self.verbosity:
            self.stdout.write(message)

    @transaction.atomic
    def handle(self, *args, **options):
        self.verbosity = options["verbosity"]
        societe = Societe.get()
        if options.get("regime_tva"):
            societe.regime_tva = {"automatique": Societe.TVA_AUTOMATIQUE, "assujettie": Societe.TVA_AUTOMATIQUE,
                                  "manuelle": Societe.TVA_MANUELLE, "non-assujettie": Societe.TVA_NON_ASSUJETTIE}[options["regime_tva"]]
            societe.save(update_fields=["regime_tva"])
            self.log(f"Régime de TVA : {societe.get_regime_tva_display()}.")
        if options.get("systeme"):
            societe.systeme_comptable = {"normal": Societe.SYSTEME_NORMAL, "smt": Societe.SYSTEME_SMT}[options["systeme"]]
            societe.save(update_fields=["systeme_comptable"])
        if options.get("activite"):
            societe.activite = {"commerce": Societe.ACTIVITE_COMMERCE, "transport": Societe.ACTIVITE_TRANSPORT,
                                "mixte": Societe.ACTIVITE_MIXTE}[options["activite"]]
            societe.save(update_fields=["activite"])
            self.log(f"Activité : {societe.get_activite_display()}.")
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

        Banque.objects.get_or_create(code="BQ1", defaults={"intitule": "Banque principale", "journal": Journal.objects.get(code="BQ")})
        for code, intitule in (("SIEGE", "Siège"), ("AGENCE1", "Agence 1")):
            SectionAnalytique.objects.get_or_create(code=code, defaults={"plan": "Agences", "intitule": intitule})
        self.log(f"Banques : {Banque.objects.count()} · sections : {SectionAnalytique.objects.count()}.")

        from apps.commercial.models import Depot

        Depot.par_defaut()
        self.log(f"Dépôts : {Depot.objects.count()}.")

        annee = datetime.date.today().year
        Exercice.objects.get_or_create(
            code=str(annee),
            defaults={"date_debut": datetime.date(annee, 1, 1), "date_fin": datetime.date(annee, 12, 31)},
        )
        self.log(f"Exercice {annee} prêt.")

        if options["admin"]:
            User = get_user_model()
            admin = User.objects.filter(username="admin").first()
            if admin is None:
                User.objects.create_superuser("admin", "", options["admin"])
                self.log("Super-utilisateur « admin » créé.")
            elif not admin.check_password(options["admin"]):
                admin.set_password(options["admin"])
                admin.save(update_fields=["password"])
                self.log("Mot de passe du super-utilisateur « admin » mis à jour.")

        transport = societe.activite in (Societe.ACTIVITE_TRANSPORT, Societe.ACTIVITE_MIXTE)
        if transport:
            from apps.transport.models import ParametresTransport

            ParametresTransport.get()                      # comptes 70611, 70612, 70613, 4718
        if options["demo"]:
            if societe.activite != Societe.ACTIVITE_TRANSPORT:
                self._demo()
            if transport:
                self._demo_transport()
        if options["sahel"]:
            self._sahel()
        # TVA : rien n'est imposé ; les taux du Cameroun ne sont créés qu'en configuration automatique
        societe.refresh_from_db()
        if societe.regime_tva == Societe.TVA_AUTOMATIQUE:
            from apps.comptabilite.services import configurer_tva_automatique

            configurer_tva_automatique()
            self.log(f"TVA configurée automatiquement ({Taxe.objects.count()} taux).")
        elif societe.regime_tva == Societe.TVA_MANUELLE:
            from apps.comptabilite.services import configurer_tva_manuelle

            configurer_tva_manuelle()
            self.log("TVA en configuration manuelle : aucun taux créé.")
        self.log(self.style.SUCCESS("Initialisation terminée."))

    def _demo_transport(self):
        """Gares, lignes, cars, chauffeurs et départs du jour fictifs."""
        import datetime

        from apps.transport.models import Chauffeur, Depart, Gare, Ligne, Vehicule

        if Gare.objects.exists():
            return
        gares = {code: Gare.objects.create(code=code, nom=f"Gare de {ville}", ville=ville)
                 for code, ville in (("DLA", "Douala"), ("YDE", "Yaoundé"), ("BFS", "Bafoussam"))}
        lignes = []
        for a, b, prix, km in (("DLA", "YDE", 6000, 240), ("YDE", "DLA", 6000, 240), ("DLA", "BFS", 5000, 280), ("BFS", "DLA", 5000, 280)):
            lignes.append(Ligne.objects.create(code=f"{a}-{b}", gare_depart=gares[a], gare_arrivee=gares[b], prix_billet=prix,
                                               distance_km=km, colis_forfait=1500, colis_prix_kg=100))
        cars = [Vehicule.objects.create(immatriculation=f"LT {n} DEMO", designation=f"Car {n} (fictif)", nombre_places=30)
                for n in (101, 102, 103)]
        chauffeurs = [Chauffeur.objects.create(nom=f"Chauffeur {n} (fictif)") for n in (1, 2, 3)]
        today = datetime.date.today()
        for i, (ligne, heure) in enumerate(((lignes[0], 7), (lignes[0], 13), (lignes[2], 8))):
            Depart.objects.create(ligne=ligne, date=today, heure=datetime.time(heure, 0), vehicule=cars[i], chauffeur=chauffeurs[i])
        from apps.personnel.models import Employe

        for i, (car, ch) in enumerate(zip(cars, chauffeurs), 1):
            Employe.objects.create(matricule=f"CH{i:02d}", nom=ch.nom, poste="Chauffeur", service=Employe.CONDUITE, vehicule=car,
                                   chauffeur=ch, salaire_base=120000)
        Employe.objects.create(matricule="GU01", nom="Guichetier (fictif)", poste="Guichetier", service=Employe.BILLETTERIE,
                               salaire_base=90000)
        Employe.objects.create(matricule="ME01", nom="Mécanicien (fictif)", poste="Mécanicien", service=Employe.GARAGE,
                               salaire_base=100000)
        self.log("Démonstration transport : 3 gares, 4 lignes, 3 cars, 3 départs aujourd'hui, 5 employés.")

    def _sahel(self):
        from apps.commercial import sahel
        from apps.commercial.models import Tiers

        if Tiers.objects.exists():
            self.log("Des tiers existent déjà : la société SAHEL DISTRIBUTION n'est pas chargée (utilisez une base vierge).")
            return
        societe = Societe.get()
        societe.raison_sociale, societe.forme_juridique, societe.ville = "SAHEL DISTRIBUTION (fictive)", "SARL", "Cameroun"
        societe.regime_tva = Societe.TVA_AUTOMATIQUE
        societe.save()
        donnees = sahel.creer_societe()
        sahel.saisir_stocks_initiaux(donnees, Exercice.objects.first().date_debut)
        self.log("Société fictive SAHEL DISTRIBUTION créée (dépôts, articles, catégories GROS/DÉTAIL, tiers, stocks initiaux).")

    def _demo(self):
        from apps.commercial.models import Article, Depot, Document, FamilleArticle, LigneDocument, Reglement, Tiers

        if Tiers.objects.exists():
            self.log("Données de démo déjà présentes, ignorées.")
            return
        societe = Societe.get()
        societe.raison_sociale = "GTC SARL (démo)"
        societe.ville = "Bertoua"
        societe.save()                       # TVA : celle choisie (--regime-tva), aucune par défaut

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
        from apps.commercial.models import CategorieTarifaire

        CategorieTarifaire.objects.create(code="GROS", intitule="Gros")
        CategorieTarifaire.objects.create(code="DETAIL", intitule="Détail")
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

        principal = Depot.par_defaut()
        principal.intitule, principal.ville = "Dépôt Bertoua", "Bertoua"
        principal.save()
        abong = Depot.objects.create(code="AM", intitule="Dépôt Abong-Mbang", ville="Abong-Mbang")
        Depot.objects.create(code="GB", intitule="Dépôt Garoua-Boulaï", ville="Garoua-Boulaï")

        def doc(type_document, tiers, jours, lignes, valider=True, **champs):
            date = min(debut + datetime.timedelta(days=jours), today)
            d = Document.objects.create(type_document=type_document, tiers=tiers, date=date, **champs)
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
        # Transfert vers l'agence d'Abong-Mbang, commande client en partie livrée (reliquat)
        doc(Document.STOCK_VIREMENT, None, 20, [(a[0], 100, a[0].cmup or a[0].prix_achat), (a[2], 30, a[2].prix_achat)],
            depot=principal, depot_destination=abong)
        commande = doc(Document.COMMANDE, clients[1], jours, [(a[2], 40, a[2].prix_vente), (a[1], 20, a[1].prix_vente)])
        livraison = commande.transformer(Document.LIVRAISON)
        ligne = livraison.lignes.get(article=a[2])
        ligne.quantite = 25
        ligne.save()
        livraison.recalculer()
        livraison.valider()

        from apps.comptabilite.services import constater_variation_stock

        constater_variation_stock(today)
        caisse = Journal.objects.get(code="CA")
        banque = Journal.objects.get(code="BQ")
        for client in clients[:2]:
            # Chaque reçu de créance règle une facture précise du client
            facture = next((f for f in client.factures_a_regler().filter(type_document=Document.FACTURE).order_by("date")
                            if f.reste_a_payer > 0), None)
            if facture:
                Reglement(tiers=client, journal=caisse, mode=Reglement.ESPECES, facture=facture,
                          montant=min(Decimal("500000"), facture.reste_a_payer), date=today).enregistrer()
        Reglement(tiers=fournisseurs[0], journal=banque, mode=Reglement.VIREMENT,
                  montant=Decimal("1500000"), date=today).enregistrer()
        self.log("Données de démonstration créées.")
