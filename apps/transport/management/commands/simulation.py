"""Simulation d'un mois complet dans un dossier SÉPARÉ (données fictives), par les fonctions du logiciel lui-même.

    set DB_ENGINE=sqlite & set SQLITE_FICHIER=simulation.sqlite3        (Windows : 7-SIMULATION.bat le fait)
    python manage.py migrate
    python manage.py simulation --mois 2026-09 --rapport docs/retour/BILAN_SIMULATION_RESULTATS.md

8 gares (agences), 60 cars voyageurs (24 VIP, 36 Classique) dont 15 de propriétaires partenaires, 5 camions courrier,
300 salariés, ventes de billets avec bagages, colis, carburant, magasin (achats, sorties, réparations), loyers
autorisés, transferts en banque, paie, décomptes des propriétaires. Chaque jour est joué « à sa date » : l'horloge du
logiciel est avancée au jour simulé, pour que chaque écriture porte la bonne date.
Tous les noms, prix, salaires et taux sont FICTIFS (taux de paie de démonstration : 5 % salarié, 10 % employeur).
Après l'essai : supprimer le fichier du dossier de simulation, ou créer la vraie société dans un autre dossier.
"""
import calendar
import contextlib
import datetime
import random
import time

from apps.transport.simulation_metier import SimulationMetierMixin
from decimal import Decimal
from unittest import mock

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

GARES = [("DLA", "Douala"), ("YDE", "Yaoundé"), ("BFS", "Bafoussam"), ("BTA", "Bertoua"), ("NGD", "Ngaoundéré"),
         ("GAR", "Garoua"), ("KRI", "Kribi"), ("EBW", "Ebolowa")]
# (départ, arrivée, km, prix Classique, prix VIP)
ROUTES = [("DLA", "YDE", 240, 6000, 10000), ("DLA", "BFS", 280, 5000, 9000), ("YDE", "BTA", 340, 6000, 10000),
          ("YDE", "NGD", 620, 10000, 15000), ("NGD", "GAR", 290, 6000, 9000), ("DLA", "KRI", 170, 4000, 7000),
          ("YDE", "EBW", 160, 3500, 6000), ("YDE", "BFS", 300, 5000, 8000)]
PRIX_LITRE = Decimal("840")
SAISON = {1: 0.85, 2: 0.9, 7: 1.05, 8: 1.12, 12: 1.15}                    # remplissage relatif (fictif)
ARTICLES = [("FILT", "Filtre à huile", "PIECE", 100, 5000), ("PLAQ", "Plaquettes de frein", "PIECE", 60, 8000),
            ("PNEU", "Pneu 315/80", "PNEU", 40, 110000), ("HUIL", "Huile moteur (litre)", "LUBRIFIANT", 200, 3500),
            ("CART", "Carton d'emballage", "EMBALLAGE", 2000, 150), ("RUBA", "Ruban adhésif", "EMBALLAGE", 500, 800),
            ("PAPI", "Papier (rame)", "BUREAU", 100, 3000)]


@contextlib.contextmanager
def horloge(moment):
    """Le logiciel croit être à ce moment (dates des pièces, contrôles d'heure de départ)."""
    with mock.patch("django.utils.timezone.now", return_value=moment):
        yield


class Command(SimulationMetierMixin, BaseCommand):
    help = "Simule un mois d'activité (données fictives) dans le dossier courant, qui doit être un dossier de simulation"

    def add_arguments(self, p):
        p.add_argument("--mois", default="2026-09", help="Premier mois simulé (AAAA-MM)")
        p.add_argument("--nombre-mois", type=int, default=1, help="Nombre de mois simulés à la suite (1 à 24)")
        p.add_argument("--jusqu-au", default="", help="Dernier jour simulé (AAAA-MM-JJ, ou « aujourdhui ») : "
                                                       "remplace --nombre-mois, le dernier mois s'arrête à ce jour")
        p.add_argument("--jours", type=int, default=0, help="Jours simulés par mois (0 : le mois entier ; essais rapides)")
        p.add_argument("--vehicules", type=int, default=60, help="Cars voyageurs (40 % VIP, un quart de partenaires)")
        p.add_argument("--salaries", type=int, default=300)
        p.add_argument("--echelle", type=float, default=1.0, help="Fraction des voyageurs et colis (essai rapide : 0.1)")
        p.add_argument("--graine", type=int, default=2026)
        p.add_argument("--rapport", default="", help="Fichier Markdown du bilan")
        p.add_argument("--scenarios-complets", action="store_true", help="Transit, transvasement, incidents colis, garage et retraits propriétaires (fictifs)")
        p.add_argument("--departs-jour", type=int, default=0, help="Nombre exact de départs quotidiens pour toutes les agences réunies (0 : aléatoire)")
        p.add_argument("--journal-scenarios", default="", help="Rapport JSON traçable des scénarios et temps réellement mesurés")
        p.add_argument("--forcer", action="store_true", help="Lever les contrôles de dossier (tests automatiques seulement)")

    def handle(self, *a, **o):
        from apps.transport.models import Depart

        base = connection.settings_dict
        if not o["forcer"] and (connection.vendor != "sqlite" or "simulation" not in str(base["NAME"]).lower()):
            raise CommandError(f"Base {base['NAME']} : la simulation ne s'exécute que dans un fichier SQLite dont le nom contient "
                               "« simulation » (SQLITE_FICHIER=simulation.sqlite3, ou SIMULATION.bat).")
        if Depart.objects.exists() and not o["forcer"]:
            raise CommandError("Ce dossier contient déjà des départs : la simulation se fait dans un dossier SÉPARÉ "
                               "(SQLITE_FICHIER=simulation.sqlite3), jamais dans la vraie société.")
        try:
            annee, mois = (int(x) for x in o["mois"].split("-"))
            premier = datetime.date(annee, mois, 1)
        except ValueError:
            raise CommandError("--mois doit être au format AAAA-MM (ex. 2026-01).")
        fin = None
        if o["jusqu_au"]:
            try:
                fin = (timezone.localdate() if o["jusqu_au"].replace("'", "").lower() == "aujourdhui"
                       else datetime.date.fromisoformat(o["jusqu_au"]))
            except ValueError:
                raise CommandError("--jusqu-au doit être une date AAAA-MM-JJ ou « aujourdhui ».")
            if fin < premier:
                raise CommandError(f"Le dernier jour ({fin:%d/%m/%Y}) est avant le premier mois ({premier:%m/%Y}).")
            o["nombre_mois"] = (fin.year - annee) * 12 + fin.month - mois + 1
        if not 1 <= o["nombre_mois"] <= 24:
            raise CommandError("De 1 à 24 mois.")
        self.configurer_metier(o)
        self.r = random.Random(o["graine"])
        self.echelle = o["echelle"]
        self.mois = []                                           # [(premier jour, jours simulés)]
        for k in range(o["nombre_mois"]):
            a, m = annee + (mois - 1 + k) // 12, (mois - 1 + k) % 12 + 1
            nb_jours = min(o["jours"] or 31, calendar.monthrange(a, m)[1])
            self.mois.append([d for d in (datetime.date(a, m, j) for j in range(1, nb_jours + 1)) if fin is None or d <= fin])
        self.jours = [j for jours in self.mois for j in jours]
        self.exercices()
        self.moment(self.jours[0], 6)
        with horloge(self.maintenant):
            self.preparer(o["vehicules"], o["salaries"])
            self.initialiser_metier()
        self.par_mois = []
        for jours in self.mois:
            self.mois_jours, avant = jours, dict(self.compteurs)
            for jour in jours:
                avant_jour = dict(self.compteurs)
                chrono = time.perf_counter()
                self.journee(jour)
                self.mesures.append({"jour": str(jour), "secondes": round(time.perf_counter()-chrono, 3),
                    "departs": self.compteurs['voyages']-avant_jour['voyages'],
                    "billets": self.compteurs['billets']-avant_jour['billets'], "echelle": self.echelle})
                self.stdout.write(f"Durée réelle {jour} : {self.mesures[-1]['secondes']:.3f} s · {self.mesures[-1]['departs']} départs · {self.mesures[-1]['billets']} billets")
                self.stdout.write(f"{jour:%d/%m/%Y} : {self.compteurs['voyages']} voyages, {self.compteurs['billets']} billets")
            self.moment(jours[-1], 22)
            with horloge(self.maintenant):
                self.fin_de_mois(jours[0], jours[-1])
            self.par_mois.append((jours[0], jours[-1], {k: self.compteurs[k] - avant[k] for k in self.compteurs}))
        if o["journal_scenarios"]:
            self.ecrire_rapports_metier(o["journal_scenarios"])
        bilan = self.bilan()
        texte = self.texte_bilan(bilan, o)
        self.stdout.write(texte)
        if o["rapport"]:
            with open(o["rapport"], "w", encoding="utf-8") as f:
                f.write(texte)
        return None

    def exercices(self):
        """Un exercice comptable par année civile couverte (la simulation peut passer sur l'année suivante)."""
        from apps.core.models import Exercice

        for a in sorted({j.year for j in self.jours}):
            Exercice.objects.get_or_create(code=str(a), defaults={"date_debut": datetime.date(a, 1, 1),
                                                                   "date_fin": datetime.date(a, 12, 31)})

    def caisse_pour(self, montant, jour):
        """Le guichet paie en espèces s'il en a assez, sinon la dépense est réglée par la banque."""
        from apps.transport.models_caisse import solde_tresorerie

        if self.profil_complet:
            return self.assurer_especes(montant, jour)
        return self.ca if solde_tresorerie(self.ca.compte_tresorerie, jour) >= montant else self.bq

    def moment(self, jour, heure, minute=0):
        self.maintenant = timezone.make_aware(datetime.datetime.combine(jour, datetime.time(heure, minute)))
        return self.maintenant

    # ------------------------------------------------------------------ mise en place
    @transaction.atomic
    def preparer(self, nb_vehicules, nb_salaries):
        from django.contrib.auth import get_user_model

        from apps.commercial.models import Tiers
        from apps.comptabilite.models import Compte, Journal
        from apps.comptabilite.services import creer_ecriture
        from apps.core.models import Societe
        from apps.garage.models_magasin import ArticleMagasin
        from apps.partenaires.models import ContratPartenaire
        from apps.personnel.models import Employe, RubriquePaie
        from apps.transport.models import Chauffeur, Gare, Ligne, Vehicule

        call_command("init_erp", "--activite", "transport", verbosity=0)
        s = Societe.get()
        s.raison_sociale, s.ville = "SIMULATION — données fictives", "Douala"
        s.save()
        U = get_user_model()
        self.agent = U.objects.get_or_create(username="sim_agent")[0]
        self.chef = U.objects.get_or_create(username="sim_chef")[0]
        self.ca, self.bq = Journal.objects.get(code="CA"), Journal.objects.get(code="BQ")
        capital = Compte.objects.get_or_create(numero="101", defaults={"intitule": "Capital social"})[0]
        creer_ecriture(self.bq, self.jours[0], "Apport initial (simulation)", [{"compte": self.bq.compte_tresorerie, "debit": 48_000_000},
                                                                              {"compte": self.ca.compte_tresorerie, "debit": 2_000_000},
                                                                              {"compte": capital, "credit": 50_000_000}])
        self.gares = {c: Gare.objects.create(code=c, nom=f"Gare de {v}", ville=v) for c, v in GARES}
        self.lignes = []
        for a, b, km, prix, vip in ROUTES:
            for x, y in ((a, b), (b, a)):
                for gamme, p in (("CLASSIQUE", prix), ("VIP", vip)):
                    self.lignes.append(Ligne.objects.create(
                        code=f"{x}-{y}{'-VIP' if gamme == 'VIP' else ''}", gare_depart=self.gares[x], gare_arrivee=self.gares[y],
                        distance_km=km, prix_billet=p, gamme=gamme, colis_forfait=2500, colis_prix_kg=50))
        par_trajet = {(l.gare_depart.code, l.gare_arrivee.code, l.gamme): l for l in self.lignes}
        nb_vip = round(nb_vehicules * 0.4)
        self.cars = []
        for i in range(nb_vehicules):
            gamme = "VIP" if i < nb_vip else "CLASSIQUE"
            a, b, km, *_ = ROUTES[i % len(ROUTES)]
            v = Vehicule.objects.create(immatriculation=f"SIM {i + 1:03d} {'VP' if gamme == 'VIP' else 'CL'}",
                                        designation=f"Car {i + 1:02d} (fictif)", gamme=gamme,
                                        nombre_places=self.r.choice([30, 35]) if gamme == "VIP" else self.r.choice([50, 60, 70]))
            self.cars.append({"vehicule": v, "aller": par_trajet[(a, b, gamme)], "retour": par_trajet[(b, a, gamme)], "km": km})
        self.camions = [Vehicule.objects.create(immatriculation=f"SIM C{i + 1:02d}", designation=f"Camion courrier {i + 1} (fictif)",
                                                type_vehicule=Vehicule.CAMION, nombre_places=0) for i in range(5)]
        for i, c in enumerate(self.camions):
            a, b, km, *_ = ROUTES[i]
            self.cars.append({"vehicule": c, "aller": par_trajet[(a, b, "CLASSIQUE")], "retour": par_trajet[(b, a, "CLASSIQUE")],
                              "km": km, "courrier": True})
        # Personnel : un chauffeur et un convoyeur par car, le reste dans les gares
        rubrique_compte = lambda n, i: Compte.objects.get_or_create(numero=n, defaults={"intitule": i})[0]  # noqa: E731
        RubriquePaie.objects.get_or_create(code="RETSIM", defaults={
            "libelle": "Retenue salariale de démonstration (FICTIVE)", "nature": RubriquePaie.RETENUE, "calcul": RubriquePaie.TAUX,
            "valeur": 5, "compte": rubrique_compte("431", "Sécurité sociale"), "automatique": True})
        RubriquePaie.objects.get_or_create(code="PATSIM", defaults={
            "libelle": "Charge patronale de démonstration (FICTIVE)", "nature": RubriquePaie.PATRONALE, "calcul": RubriquePaie.TAUX,
            "valeur": 10, "compte": rubrique_compte("664", "Charges sociales"),
            "compte_contrepartie": rubrique_compte("431", "Sécurité sociale"), "automatique": True})
        n = 0
        for c in self.cars:
            ch = Chauffeur.objects.create(nom=f"Chauffeur {n + 1} (fictif)")
            c["chauffeur"] = ch
            Employe.objects.create(matricule=f"S{n + 1:04d}", nom=ch.nom, poste="Chauffeur", service=Employe.CONDUITE,
                                   vehicule=c["vehicule"], chauffeur=ch,
                                   salaire_base=150000, ventilation=Employe.HABITUEL)
            n += 1
            if n < nb_salaries and not c.get("courrier"):
                Employe.objects.create(matricule=f"S{n + 1:04d}", nom=f"Convoyeur {n + 1} (fictif)", poste="Convoyeur",
                                       service=Employe.CONDUITE, vehicule=c["vehicule"], salaire_base=90000, ventilation=Employe.HABITUEL)
                n += 1
        postes = [("Guichetier", Employe.BILLETTERIE, 100000), ("Agent colis", Employe.COLIS, 95000),
                  ("Mécanicien", Employe.GARAGE, 120000), ("Comptable", Employe.ADMINISTRATION, 180000), ("Gardien", Employe.AUTRE, 70000)]
        while n < nb_salaries:
            poste, service, salaire = postes[n % len(postes)]
            Employe.objects.create(matricule=f"S{n + 1:04d}", nom=f"{poste} {n + 1} (fictif)", poste=poste, service=service,
                                   salaire_base=salaire)
            n += 1
        # Propriétaires partenaires : un car sur quatre, quatre types de contrat
        modeles = [dict(modele=ContratPartenaire.COMMISSION, taux_commission=10, montant_location=50000),  # contrat type
                   dict(modele=ContratPartenaire.LOCATION, montant_location=400000, charge_carburant=False,
                        charge_reparations=False, charge_route=False),
                   dict(modele=ContratPartenaire.FIXE_PLUS_VARIABLE, montant_location=150000, taux_proprietaire=40),
                   dict(modele=ContratPartenaire.AVANCE_SUR_VARIABLE, montant_location=150000, taux_proprietaire=40)]
        nb_partenaires = max(1, round(nb_vehicules / 4))
        proprietaires = [Tiers.objects.create(code=f"PROP{i + 1:02d}", nom=f"Propriétaire {i + 1} (fictif)",
                                              type_tiers=Tiers.FOURNISSEUR) for i in range(max(1, round(nb_partenaires * 2 / 3)))]
        self.contrats = []
        for i, c in enumerate(self.cars[-nb_partenaires - 5:-5] if nb_partenaires < len(self.cars) - 5 else self.cars[:1]):
            self.contrats.append(ContratPartenaire.objects.create(
                vehicule=c["vehicule"], partenaire=proprietaires[i % len(proprietaires)], debut=self.jours[0],
                **{k: Decimal(str(v)) if isinstance(v, (int, float)) and not isinstance(v, bool) else v
                   for k, v in modeles[i % len(modeles)].items()}).activer())
        self.fournisseur = Tiers.objects.create(code="FOURPIE", nom="Pièces et fournitures (fictif)", type_tiers=Tiers.FOURNISSEUR)
        self.articles = {code: ArticleMagasin.objects.create(code=code, designation=nom, categorie=cat)
                         for code, nom, cat, _, _ in ARTICLES}
        self.compteurs = {"voyages": 0, "billets": 0, "colis": 0, "bagages": 0, "pleins": 0, "reparations": 0}

    # ------------------------------------------------------------------ une journée
    def journee(self, jour):
        from apps.garage.models import LigneReparation, OrdreReparation, PleinCarburant
        from apps.garage.models_magasin import AchatMagasin, LigneAchatMagasin, sortir
        from apps.partenaires.models import ContratPartenaire, ReglementPartenaire
        from apps.transport.models import Billet, Colis, Depart, DepenseVehicule
        from apps.transport.models_caisse import TransfertFonds, solde_tresorerie
        from apps.transport.models_depenses import DemandeDepense

        r = self.r
        with horloge(self.moment(jour, 5)), transaction.atomic():
            if jour == self.mois_jours[0]:                      # achats du magasin pour le mois
                achat = AchatMagasin.objects.create(date=jour, fournisseur=self.fournisseur, facture="FICTIVE-01")
                for code, _, _, qte, prix in ARTICLES:
                    LigneAchatMagasin.objects.create(achat=achat, article=self.articles[code], quantite=qte, prix_unitaire=prix)
                LigneAchatMagasin.objects.create(achat=achat, destination=LigneAchatMagasin.IMMOBILISATION,
                                                 designation="Imprimante de guichet", prix_unitaire=250000)
                achat.valider(self.agent)
                for c in self.cars:                              # assurance et papiers du mois, imputés au véhicule
                    DepenseVehicule(vehicule=c["vehicule"], nature=DepenseVehicule.ASSURANCE, montant=Decimal(35000),
                                    libelle="Assurance et papiers du mois (fictif)", caisse=self.bq, date=jour).enregistrer()
            if jour.day == 15 and self.cars:                     # achat direct pour un car précis
                achat = AchatMagasin.objects.create(date=jour, fournisseur=self.fournisseur, facture="FICTIVE-02")
                LigneAchatMagasin.objects.create(achat=achat, destination=LigneAchatMagasin.VEHICULE, designation="Pare-brise",
                                                 prix_unitaire=85000, vehicule=self.cars[0]["vehicule"])
                achat.valider(self.agent)
        departs = []
        for c, ligne, heure in self.plan_journee(jour):
            with horloge(self.moment(jour, max(heure - 3, 0))), transaction.atomic():
                d = Depart.objects.create(ligne=ligne, date=jour, heure=datetime.time(heure), vehicule=c["vehicule"],
                                          chauffeur=c["chauffeur"])
                if not c.get("courrier"):
                    saison = SAISON.get(jour.month, 1)                 # fêtes de fin d'année, grandes vacances
                    voyageurs = max(1, int(d.places * min(r.uniform(0.55, 0.95) * saison, 1) * self.echelle))
                    reserve = self.reserve_scenarios(c, heure, jour)
                    for k in range(min(voyageurs, d.places - reserve)):
                        bagages = r.random() < 0.15
                        Billet(depart=d, voyageur=f"Voyageur {k + 1} (fictif)",
                               paiement=Billet.MOBILE_MONEY if r.random() < (0.05 if self.profil_complet else 0.2) else Billet.ESPECES,
                               bagages="1 colis encombrant" if bagages else "", bagages_nombre=1 if bagages else 0,
                               prix_bagages=Decimal(r.choice([1000, 2000, 3000])) if bagages else Decimal(0)).vendre(self.agent)
                        self.compteurs["billets"] += 1
                        self.compteurs["bagages"] += bagages
                nb_colis = max(0, int(r.randint(0, 3 if not c.get("courrier") else 12) * max(self.echelle, 0.25)))
                for k in range(nb_colis):
                    colis = Colis(gare_depart=ligne.gare_depart, gare_arrivee=ligne.gare_arrivee, expediteur="Expéditeur (fictif)",
                                  destinataire="Destinataire (fictif)", poids=Decimal(r.randint(2, 40)), description="Carton").enregistrer()
                    colis.charger(d)
                    self.compteurs["colis"] += 1
            departs.append((d, c, heure))
        with horloge(self.moment(jour, 0)), transaction.atomic():
            self.scenarios_avant_depart(jour, departs)
        for d, c, heure in departs:
            with horloge(self.moment(jour, heure, 5)), transaction.atomic():
                if self.profil_complet and d.pk in (getattr(self, '_depart_scenario', None), getattr(self, '_depart_suite_scenario', None)):
                    self.tracer_scenario('Transport', 'Départ : reconnaissance des produits de cette portion, sans nouvel encaissement', d.partir)
                else:
                    d.partir()
                self.scenarios_en_route(jour, d)
                litres = Decimal(c["km"] * 35 // 100)
                PleinCarburant(vehicule=c["vehicule"], depart=d, litres=litres, prix_litre=PRIX_LITRE,
                               caisse=self.caisse_pour(litres * PRIX_LITRE, jour), date=jour).enregistrer()
                self.compteurs["voyages"] += 1
                self.compteurs["pleins"] += 1
            arrivee_jour = jour + datetime.timedelta(days=(heure+6)//24) if self.departs_jour else jour
            arrivee_heure = (heure+6)%24 if self.departs_jour else min(heure+6,23)
            with horloge(self.moment(arrivee_jour, arrivee_heure)), transaction.atomic():
                d.arriver()
                self.scenarios_apres_arrivee(jour, d)
        with horloge(self.moment(jour, 20)), transaction.atomic():
            if self.compteurs["colis"]:                          # emballages consommés pour les colis du jour
                carton = self.articles["CART"]
                carton.refresh_from_db()
                besoin = Decimal(min(len(departs), int(carton.quantite)))
                if besoin:
                    sortir(carton, besoin, motif="Emballage des colis du jour", date=jour)
            if jour.weekday() == 2 and self.cars:                # réparations du mercredi avec pièces du magasin
                for c in r.sample(self.cars, min(3, len(self.cars))):
                    o = OrdreReparation.objects.create(vehicule=c["vehicule"], date_entree=jour, panne="Entretien périodique")
                    for code, qte in (("FILT", 1), ("HUIL", 8)):
                        a = self.articles[code]
                        a.refresh_from_db()
                        if a.quantite >= qte:
                            LigneReparation.objects.create(ordre=o, nature=LigneReparation.MAGASIN, article=a, designation=a.designation,
                                                           quantite=qte, prix_unitaire=a.cout_moyen)
                    LigneReparation.objects.create(ordre=o, nature=LigneReparation.MAIN_OEUVRE_EXTERNE, designation="Main d'œuvre",
                                                   prix_unitaire=10000)
                    o.cloturer(caisse=self.caisse_pour(o.cout, jour), date=jour)
                    self.compteurs["reparations"] += 1
            if jour == self.mois_jours[0]:                       # loyers des gares, autorisés puis payés
                for g in self.gares.values():
                    dd = DemandeDepense(nature=DemandeDepense.LOYER, libelle=f"Loyer {g.nom} (fictif)", montant=Decimal(150000),
                                        date=jour).demander(self.agent)
                    dd.decider(True, self.chef)
                    dd.payer(self.bq, self.agent, date=jour)
            if jour.day == 15:                                   # avances des contrats « avance sur variable »
                for ct in self.contrats:
                    if ct.modele == ContratPartenaire.AVANCE_SUR_VARIABLE:
                        ReglementPartenaire(partenaire=ct.partenaire, montant=ct.montant_location, caisse=self.bq,
                                            nature=ReglementPartenaire.AVANCE, date=jour).enregistrer()
            especes = solde_tresorerie(self.ca.compte_tresorerie, jour)
            versement = Decimal(0) if self.profil_complet else (especes * Decimal("0.8")).quantize(Decimal("1"))
            if versement > 0:                                    # versement en banque du soir
                t = TransfertFonds(origine=self.ca, destination=self.bq, montant=versement, date_envoi=jour, porteur="Convoyeur de fonds")
                t.envoyer(self.chef)
                t.recevoir(self.chef, date=jour)

    # ------------------------------------------------------------------ fin de mois
    @transaction.atomic
    def fin_de_mois(self, debut, fin):
        from apps.comptabilite.models import LigneEcriture
        from apps.comptabilite.services import creer_ecriture
        from apps.partenaires.models import Decompte, ReglementPartenaire
        from apps.personnel.models import PeriodePaie

        periode = PeriodePaie.objects.create(annee=fin.year, mois=fin.month)
        periode.generer()
        periode.valider(date=fin)
        periode.payer(self.caisse_pour(sum((b.net for b in periode.bulletins.all()), Decimal(0)), fin) if self.profil_complet else self.bq, date=fin)
        if self.profil_complet:
            self.decomptes_metier(debut, fin)
        else:
            for ct in self.contrats:
                d = Decompte.calculer(ct, debut, fin).approuver(date=fin)
                if d.montant_du > 0:                             # profil historique conservé
                    ReglementPartenaire(partenaire=ct.partenaire, decompte=d, montant=(d.montant_du * Decimal("0.6")).quantize(Decimal("1")),
                                        caisse=self.bq, date=fin).enregistrer()
        dette = sum((l.credit - l.debit for l in LigneEcriture.objects.filter(tiers=self.fournisseur,
                                                                              compte=self.fournisseur.get_compte_collectif())),
                    Decimal(0))
        if dette > 0:                                            # règlement du fournisseur par la banque
            journal = self.caisse_pour(dette,fin) if self.profil_complet else self.bq
            creer_ecriture(journal, fin, "Règlement fournisseur pièces (fictif)",
                           [{"compte": self.fournisseur.get_compte_collectif(), "tiers": self.fournisseur, "debit": dette},
                            {"compte": journal.compte_tresorerie, "credit": dette}])

    # ------------------------------------------------------------------ bilan et contrôles
    def bilan(self):
        from django.db.models import Sum

        from apps.comptabilite.models import Ecriture, LigneEcriture
        from apps.garage.models_magasin import ArticleMagasin
        from apps.partenaires.models import solde_partenaire
        from apps.personnel.models import Bulletin
        from apps.transport import analytique

        debut, fin = self.jours[0], self.jours[-1]
        tot = LigneEcriture.objects.filter(ecriture__statut=Ecriture.STATUT_VALIDEE).aggregate(d=Sum("debit"), c=Sum("credit"))

        def solde(prefixe):
            a = LigneEcriture.objects.filter(compte__numero__startswith=prefixe).aggregate(d=Sum("debit"), c=Sum("credit"))
            return (a["d"] or 0) - (a["c"] or 0)

        ana = analytique.vehicules(debut, fin)

        def mois_gl(d, f, prefixe):
            a = (LigneEcriture.objects.filter(ecriture__date__range=(d, f), ecriture__statut=Ecriture.STATUT_VALIDEE,
                                              compte__numero__startswith=prefixe).aggregate(d=Sum("debit"), c=Sum("credit")))
            return (a["d"] or 0) - (a["c"] or 0)

        mensuel = [{"debut": d, "fin": f, **n, "produits": -mois_gl(d, f, "7"), "charges": mois_gl(d, f, "6")}
                   for d, f, n in self.par_mois]
        return {"mensuel": mensuel,
            **self.compteurs, "ecritures": Ecriture.objects.count(), "debit": tot["d"] or 0, "credit": tot["c"] or 0,
            "produits": -solde("7"), "charges": solde("6"), "billets_70611": -solde("70611"), "bagages_70614": -solde("70614"),
            "colis_70612": -solde("70612"), "carburant": solde("6053"), "pieces_624": solde("624"), "paie_661": solde("661"),
            "paie_664": solde("664"), "net_a_payer_422": -solde("422"), "organismes_431": -solde("431"),
            "fournisseurs_401": -solde("401"), "proprietaires_467": -solde("467"), "caisse_57": solde("57"), "banque_52": solde("52"),
            "mobile_money_55": solde("55"), "transit_585": solde("585"), "stock_33": solde("33"), "immobilisations_2": solde("2"),
            "valeur_magasin": sum((a.valeur for a in ArticleMagasin.objects.all()), Decimal(0)),
            "bulletins": Bulletin.objects.count(), "net_bulletins": Bulletin.objects.aggregate(s=Sum("net"))["s"] or 0,
            "analytique": ana["controle"], "resultat_vehicules": ana["total"]["resultat_societe"],
            "proprietaires": [(c.partenaire.nom, c.vehicule.immatriculation, c.get_modele_display(), solde_partenaire(c.partenaire))
                              for c in self.contrats],
        }

    def texte_bilan(self, b, o):
        def m(v):
            return f"{Decimal(v):,.0f}".replace(",", " ")

        controles = [
            ("Débit = crédit de toutes les écritures", b["debit"] == b["credit"]),
            ("Caisse espèces positive en fin de période", b["caisse_57"] >= 0),
            ("Fonds en transit soldés (versements reçus)", b["transit_585"] == 0),
            ("Salaires nets payés (422 soldé)", b["net_a_payer_422"] == 0),
            ("Stock comptable (33) = valeur du magasin", abs(b["stock_33"] - b["valeur_magasin"]) <= len(ARTICLES)),
            ("Produits analytiques affectés + non affectés = comptabilité", b["analytique"]["produits_gl"]
             == b["analytique"]["produits_affectes"] + b["analytique"]["produits_non_affectes"]),
        ]
        lignes = [
            "# Bilan de la simulation (données FICTIVES)", "",
            f"Période simulée : {self.jours[0]:%d/%m/%Y} au {self.jours[-1]:%d/%m/%Y} ({len(self.mois)} mois) · échelle "
            f"{o['echelle']} · graine {o['graine']}", "",
            "| Mois | Voyages | Billets | Colis | Produits | Charges | Résultat |", "|---|---:|---:|---:|---:|---:|---:|",
            *[f"| {x['debut']:%m/%Y} | {x['voyages']} | {x['billets']} | {x['colis']} | {m(x['produits'])} | {m(x['charges'])} | "
              f"{m(x['produits'] - x['charges'])} |" for x in b["mensuel"]], "",
            "| Activité | Nombre |", "|---|---:|",
            *[f"| {k} | {b[k]} |" for k in ("voyages", "billets", "bagages", "colis", "pleins", "reparations", "bulletins", "ecritures")],
            "", "| Comptabilité générale | FCFA |", "|---|---:|",
            *[f"| {k} | {m(b[k])} |" for k in ("produits", "charges", "billets_70611", "bagages_70614", "colis_70612", "carburant",
                                               "pieces_624", "paie_661", "paie_664", "net_bulletins", "net_a_payer_422",
                                               "organismes_431", "fournisseurs_401", "proprietaires_467", "caisse_57", "banque_52",
                                               "mobile_money_55", "transit_585", "stock_33", "valeur_magasin", "immobilisations_2")],
            f"| Résultat (produits − charges) | {m(b['produits'] - b['charges'])} |",
            f"| Total débit = total crédit | {m(b['debit'])} = {m(b['credit'])} |", "",
            "| Analytique véhicules | FCFA |", "|---|---:|",
            *[f"| {k} | {m(v)} |" for k, v in b["analytique"].items()],
            f"| Résultat des véhicules pour la société | {m(b['resultat_vehicules'])} |", "",
            "| Propriétaire | Véhicule | Contrat | Solde du propriétaire, tous ses véhicules (467) |", "|---|---|---|---:|",
            *[f"| {p} | {v} | {c} | {m(s)} |" for p, v, c, s in b["proprietaires"]], "",
            "| Contrôle | Résultat |", "|---|---|",
            *[f"| {t} | {'OK' if ok else 'ÉCART'} |" for t, ok in controles], "",
            "Taux de paie de démonstration (5 % / 10 %), prix, salaires et contrats : fictifs, sans valeur réglementaire.\nNon simulés systématiquement : amortissements, péages, impôts et taxes. Les imprévus et incidents ne sont joués que dans le profil complet ; leurs montants sont fictifs, sans fréquence statistique garantie. Saisonnalité de démonstration : janvier-février plus calmes, août et décembre plus chargés.",
        ]
        if self.profil_complet:
            lignes += ["", "## Scénarios et conséquences comptables (fictifs)", "",
                "15 % : base du contrat réel À CONFIRMER. Les deux hypothèses sont comparées sans double comptabilisation.",
                "Le retrait dit salaire propriétaire débite son compte tiers ; il n’est ni une paie ni une charge supplémentaire.",
                "| Date | Module | Cas | Débit | Crédit | Lignes GL |", "|---|---|---|---:|---:|---|",
                *[f"| {e['date']} | {e['module']} | {e['cas']} | {e['debit']} | {e['credit']} | {', '.join(str(l['source_gl_line_id']) for l in e['ecritures']) or 'Aucune écriture'} |" for e in self.scenarios],
                "", "## Temps réellement mesurés", "", "| Journée | Départs (toutes agences) | Billets | Secondes |", "|---|---:|---:|---:|",
                *[f"| {e['jour']} | {e['departs']} | {e['billets']} | {e['secondes']} |" for e in self.mesures],
                "", "Initialisation, paie et arrêtés mensuels s’ajoutent aux temps des journées."]
            controles += [("Scénarios équilibrés individuellement", all(Decimal(e['debit']) == Decimal(e['credit']) for e in self.scenarios))]
            if self.departs_jour:
                controles += [("Nombre exact de départs quotidiens toutes agences réunies", all(e['departs']==self.departs_jour for e in self.mesures))]
            lignes += [f"{t} : {'OK' if ok else 'ÉCART'}" for t,ok in controles[-2:]]
        self.controles = controles
        return "\n".join(lignes) + "\n"

