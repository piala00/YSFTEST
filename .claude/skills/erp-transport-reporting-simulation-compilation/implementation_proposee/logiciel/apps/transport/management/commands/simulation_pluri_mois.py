"""Simulation CONTINUE de 1 a 36 mois sur une base de TEST isolee.

Exemple (dans une base SQLite de test vide, contenant «simulation» dans son nom) :
  python manage.py migrate --noinput
  python manage.py simulation_pluri_mois --mois 2026-01 --nombre-mois 12 \
      --echelle 0.1 --rapport docs/retour/SIMULATION_12_MOIS.md

La société et la flotte sont créées une seule fois. Les voyages et opérations
s'ajoutent mois après mois. Une paie et un decompte propriétaire sont generés
a chaque clôture mensuelle. Aucune base réelle ne doit être ciblée.
"""
import calendar
import datetime as dt
import json
import random
from decimal import Decimal
from pathlib import Path

from django.core.management.base import CommandError
from django.db import connection
from django.db.models import Sum
from django.utils import timezone

from .simulation import Command as SimulationMensuelle, horloge


class Command(SimulationMensuelle):
    help = "Simule plusieurs mois CONSECUTIFS dans une base fictive SQLite isolée."

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("--nombre-mois", type=int, default=3, help="Nombre de mois consécutifs : 1 à 36")
        parser.add_argument("--rapport-json", default="", help="Bilan structuré JSON, uniquement de démonstration")

    def handle(self, *args, **options):
        from apps.transport.models import Depart
        nombre = options["nombre_mois"]
        if nombre < 1 or nombre > 36:
            raise CommandError("--nombre-mois doit être compris entre 1 et 36")
        if options["forcer"]:
            raise CommandError("L'option --forcer est interdite pour la simulation pluri-mois")
        if connection.vendor != "sqlite" or "simulation" not in str(connection.settings_dict["NAME"]).lower():
            raise CommandError("Utiliser une base SQLite dédiée, dont le nom contient 'simulation', jamais une base réelle")
        if Depart.objects.exists():
            raise CommandError("Base non vierge : créer une nouvelle base de simulation (sans effacer la base existante)")
        try:
            debut = dt.date.fromisoformat(options["mois"] + "-01")
        except ValueError as exc:
            raise CommandError("--mois doit être au format AAAA-MM") from exc
        if options["jours"]:
            raise CommandError("--jours est interdit ici : chaque mois doit être simulé EN ENTIER")
        if not (0 < options["echelle"] <= 1):
            raise CommandError("--echelle doit être comprise entre 0 exclu et 1 inclus")

        self.r = random.Random(options["graine"])
        self.echelle = options["echelle"]
        self.jours = self._jours_du_mois(debut)
        self.moment(self.jours[0], 6)
        with horloge(self.maintenant):
            self.preparer(options["vehicules"], options["salaries"])
        self.stdout.write(f"Société de simulation créée ; début : {debut} ; durée : {nombre} mois")

        donnees = []
        compteurs_anterieurs = dict(self.compteurs)
        for indice in range(nombre):
            annee = debut.year + (debut.month - 1 + indice) // 12
            mois = (debut.month - 1 + indice) % 12 + 1
            premiere_journee = dt.date(annee, mois, 1)
            self.jours = self._jours_du_mois(premiere_journee)
            for jour in self.jours:
                self.journee(jour)
            self.moment(self.jours[-1], 22)
            with horloge(self.maintenant):
                self.fin_de_mois()
            mouvements = self._journal_du_mois(self.jours[0], self.jours[-1])
            indicateurs = {k: self.compteurs[k] - compteurs_anterieurs.get(k, 0) for k in self.compteurs}
            compteurs_anterieurs = dict(self.compteurs)
            balance_ok = mouvements["debit"] == mouvements["credit"]
            mois_resultat = {"mois": f"{annee:04d}-{mois:02d}", **indicateurs, **mouvements,
                             "resultat_partiel": mouvements["produits"] - mouvements["charges"],
                             "equilibre_debit_credit": balance_ok}
            donnees.append(mois_resultat)
            self.stdout.write(f"{mois_resultat['mois']} : {indicateurs.get('voyages',0)} voyages ; "
                              f"{indicateurs.get('billets',0)} billets ; "
                              f"{'OK' if balance_ok else 'ECART'} (débit/crédit)")
            if not balance_ok:
                raise CommandError("Balance déséquilibrée : simulation interrompue, résultats à auditer")

        resultats = {
            "fictif": True, "parametres": {"premier_mois": options["mois"], "nombre_mois": nombre,
                                          "graine": options["graine"], "echelle": options["echelle"],
                                          "vehicules": options["vehicules"], "salaries": options["salaries"]},
            "mois": donnees,
        }
        texte = self._markdown(resultats)
        self.stdout.write(texte)
        if options["rapport"]:
            p = Path(options["rapport"])
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(texte, encoding="utf-8")
        if options["rapport_json"]:
            p = Path(options["rapport_json"])
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(resultats, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    @staticmethod
    def _jours_du_mois(premier):
        dernier = calendar.monthrange(premier.year, premier.month)[1]
        return [dt.date(premier.year, premier.month, j) for j in range(1, dernier + 1)]

    @staticmethod
    def _journal_du_mois(debut, fin):
        """Synthèse réelle des écritures validées de la période, pas une 2e comptabilité."""
        from apps.comptabilite.models import Ecriture, LigneEcriture
        donnees = (LigneEcriture.objects.filter(ecriture__statut=Ecriture.STATUT_VALIDEE,
                                               ecriture__date__range=(debut, fin))
                   .values("compte__numero").annotate(d=Sum("debit"), c=Sum("credit")))
        debit = credit = produits = charges = Decimal("0")
        for row in donnees:
            d, c = row["d"] or Decimal("0"), row["c"] or Decimal("0")
            debit += d
            credit += c
            numero = row["compte__numero"] or ""
            if numero.startswith("6"):
                charges += d - c
            if numero.startswith("7"):
                produits += c - d
        return {"debit": debit, "credit": credit, "produits": produits, "charges": charges}

    @staticmethod
    def _markdown(resultats):
        lignes = ["# Simulation ERP Transport pluri-mois — DONNÉES FICTIVES", "",
                  "Les montants sont issus d'écritures générales validées dans une BASE DE TEST, et ne valent pas",
                  "audit fiscal/comptable. Les charges incomplètes ne permettent pas de calculer un bénéfice définitif.", "",
                  "| Mois | Voyages | Billets | Colis | Produits FCFA | Charges FCFA | Résultat partiel | Débit = crédit |",
                  "|---|---:|---:|---:|---:|---:|---:|:---:|"]
        def f(v): return f"{v:,.0f}".replace(",", " ")
        for m in resultats["mois"]:
            lignes.append(f"| {m['mois']} | {m.get('voyages',0)} | {m.get('billets',0)} | {m.get('colis',0)} | "
                          f"{f(m['produits'])} | {f(m['charges'])} | {f(m['resultat_partiel'])} | "
                          f"{'OK' if m['equilibre_debit_credit'] else 'ÉCART'} |")
        lignes += ["", "**Contrôles complémentaires obligatoires avant validation métier :** ventilation des dix plans,",
                   "soldes caisses par agence, stocks, créances fournisseurs, paie et cotisations, compte des propriétaires,",
                   "quotas des sièges, colis affectés au véhicule transporteur, transferts entre agences.", "",
                   "**Alerte :** une balance équilibrée n'est pas une preuve suffisante de justesse métier."]
        return "\n".join(lignes) + "\n"
