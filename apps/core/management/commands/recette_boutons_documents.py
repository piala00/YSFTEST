"""Recette DYNAMIQUE des boutons des pièces commerciales : chaque type × chaque statut, page réellement affichée.

    SQLITE_FICHIER=recette-boutons.sqlite3 python manage.py migrate
    SQLITE_FICHIER=recette-boutons.sqlite3 python manage.py recette_boutons_documents --sortie docs/retour/CLAUDE_RECETTE_BOUTONS_DOCUMENTS

Complément du recensement statique (recenser_boutons_commercial) : ici on crée une pièce de chaque type dans chaque
statut (brouillon, validé, transformé, annulé), on ouvre sa fiche comme un administrateur et on compte les commandes
réellement affichées, actives ou grisées. Crée des données : refuse toute base dont le nom ne contient pas « recette ».
"""
import csv
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

STATUTS = ("BROUILLON", "VALIDE", "TRANSFORME", "ANNULE")


class Commandes(HTMLParser):
    """Liens, boutons et commandes inactives (span.inactif) de la zone de travail <main>."""

    def __init__(self):
        super().__init__()
        self.dans_main, self.nombre, self.libelles, self.courant = 0, Counter(), [], None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "main":
            self.dans_main += 1
        classes = a.get("class") or ""
        if self.dans_main and (tag in ("a", "button") or (tag == "span" and "inactif" in classes)):
            etat = "grise" if tag == "span" or "disabled" in a or "inactif" in classes else "actif"
            self.nombre[etat] += 1
            self.courant = [etat, ""]

    def handle_data(self, data):
        if self.courant is not None:
            self.courant[1] += data

    def handle_endtag(self, tag):
        if tag == "main" and self.dans_main:
            self.dans_main -= 1
        if tag in ("a", "button", "span") and self.courant is not None:
            texte = re.sub(r"\s+", " ", self.courant[1]).strip()
            if texte:
                self.libelles.append((self.courant[0], texte))
            self.courant = None


class Command(BaseCommand):
    help = "Recette des boutons affichés sur chaque type de pièce commerciale dans chaque statut (base de recette)"

    def add_arguments(self, parser):
        parser.add_argument("--sortie", default="recette-boutons-documents", help="Chemin sans extension (.csv et .md)")

    def handle(self, *args, **o):
        nom = str(connection.settings_dict["NAME"]).lower()
        if connection.vendor != "sqlite" or "recette" not in nom:
            raise CommandError("Base de recette seulement : SQLITE_FICHIER=recette-boutons.sqlite3 (la commande crée des pièces).")
        from django.contrib.auth import get_user_model
        from django.test import Client
        from django.urls import reverse

        from apps.commercial.models import Article, Depot, Document, LigneDocument, Tiers

        call_command("init_erp", verbosity=0)
        client_ = Tiers.objects.get_or_create(code="RCLI", defaults={"nom": "Client de recette"})[0]
        fournisseur = Tiers.objects.get_or_create(code="RFOU", defaults={"nom": "Fournisseur de recette",
                                                                         "type_tiers": Tiers.FOURNISSEUR})[0]
        article = Article.objects.get_or_create(reference="RART", defaults={"designation": "Article de recette",
                                                                             "prix_achat": 800, "prix_vente": 1000})[0]
        Depot.par_defaut()
        agence = Depot.objects.get_or_create(code="RAG", defaults={"intitule": "Dépôt de recette"})[0]

        def piece(type_document, quantite=1):
            tiers = None if type_document in Document.TYPES_STOCK else (
                fournisseur if type_document in Document.TYPES_ACHAT else client_)
            d = Document.objects.create(type_document=type_document, tiers=tiers,
                                        depot_destination=agence if type_document == Document.STOCK_VIREMENT else None)
            LigneDocument.objects.create(document=d, article=article, quantite=quantite, prix_unitaire=1000)
            d.recalculer()
            return d

        piece(Document.STOCK_ENTREE, 1000).valider()                      # stock pour les livraisons et sorties
        admin = get_user_model().objects.filter(username="recette").first() or \
            get_user_model().objects.create_superuser("recette", "", "Recette-Boutons-2026")
        navigateur = Client(HTTP_HOST="localhost")
        navigateur.force_login(admin)
        resultats = []
        for type_document, libelle_type in Document.TYPES:
            for statut in STATUTS:
                r = {"type": type_document, "libelle_type": libelle_type, "statut": statut}
                try:
                    d = piece(type_document)
                    if statut in ("VALIDE", "TRANSFORME"):
                        d.valider()
                    if statut == "TRANSFORME":
                        cibles = Document.TRANSFORMATIONS.get(type_document)
                        if not cibles:
                            raise ValueError("sans objet : ce type ne se transforme pas")
                        nouveau = d.transformer(cibles[0])
                        (nouveau if isinstance(nouveau, Document) else d.documents_generes.order_by("-pk").first()).valider()
                    if statut == "ANNULE":
                        d.annuler()
                    d.refresh_from_db()
                    if d.statut != statut:
                        raise ValueError(f"statut obtenu : {d.statut}")
                    page = navigateur.get(reverse("commercial:document_detail", args=[d.pk]) + "?seul=1")
                    lecteur = Commandes()
                    lecteur.feed(page.content.decode())
                    actives = sorted({t for e, t in lecteur.libelles if e == "actif" and not re.match(r"^[A-Z]{2}\d{4}-", t)})
                    grisees = sorted({t for e, t in lecteur.libelles if e == "grise"})
                    r.update(http=page.status_code, actifs=lecteur.nombre["actif"], grises=lecteur.nombre["grise"],
                             commandes_actives=actives, commandes_grisees=grisees)
                except Exception as exc:
                    r["sans_objet"] = f"{exc}"[:160]
                resultats.append(r)
        self._ecrire(Path(o["sortie"]), resultats)

    def _ecrire(self, base, resultats):
        base.parent.mkdir(parents=True, exist_ok=True)
        with open(base.with_suffix(".csv"), "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["type", "libellé", "statut", "http", "commandes actives", "commandes grisées",
                        "libellés actifs", "libellés grisés", "sans objet"])
            for r in resultats:
                w.writerow([r["type"], r["libelle_type"], r["statut"], r.get("http", ""), r.get("actifs", ""),
                            r.get("grises", ""), " | ".join(r.get("commandes_actives", [])),
                            " | ".join(r.get("commandes_grisees", [])), r.get("sans_objet", "")])
        affichees = [r for r in resultats if "http" in r]
        lignes = ["# Recette des boutons affichés sur les pièces commerciales",
                  "", "Produit par `python manage.py recette_boutons_documents` (base de recette, administrateur).",
                  "Chaque fiche est réellement affichée ; on compte dans la zone de travail les liens et boutons actifs,",
                  "et les commandes grisées (inactives ou désactivées). Les numéros de pièces liées ne sont pas des commandes.",
                  "", f"- Combinaisons type × statut : **{len(resultats)}** ; fiches affichées : **{len(affichees)}** ;"
                  f" sans objet : **{len(resultats) - len(affichees)}** (types qui ne se transforment pas).",
                  f"- Erreurs d'affichage (code HTTP différent de 200) : **{sum(1 for r in affichees if r['http'] != 200)}**.",
                  "", "| Type | Brouillon | Validé | Transformé | Annulé |", "|---|---|---|---|---|"]
        for type_document, libelle in dict.fromkeys((r["type"], r["libelle_type"]) for r in resultats):
            cases = []
            for statut in STATUTS:
                r = next(x for x in resultats if x["type"] == type_document and x["statut"] == statut)
                cases.append(f"{r['actifs']} / {r['grises']}" if "http" in r else "—")
            lignes.append(f"| {libelle} | " + " | ".join(cases) + " |")
        lignes += ["", "Cases : commandes actives / grisées. « — » : sans objet.", "", "## Commandes actives selon le statut", ""]
        for statut in STATUTS:
            union = sorted({c for r in affichees if r["statut"] == statut for c in r["commandes_actives"]})
            lignes.append(f"- **{statut}** : " + ", ".join(union))
        base.with_suffix(".md").write_text("\n".join(lignes) + "\n", encoding="utf-8")
        self.stdout.write(json.dumps({"combinaisons": len(resultats), "affichees": len(affichees)}))
        self.stdout.write(str(base.with_suffix(".md")))
