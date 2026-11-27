"""Écrans du plan analytique : axes → éléments → états détaillés, sur une période choisie en un clic."""
import csv
from numbers import Number
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import render

from . import plan_analytique as pa
from .pdf_analytique import generer_pdf

PERIODES_RAPIDES = [("jour", "Aujourd'hui"), ("hier", "Hier"), ("semaine", "Cette semaine"), ("mois", "Ce mois"),
                    ("mois_precedent", "Mois précédent"), ("trimestre", "Ce trimestre"), ("annee", "Cette année"),
                    ("exercice", "Exercice")]
MOIS = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre",
        "Décembre"]
TRIS = [("libelle", "Nom"), ("resultat", "Résultat"), ("produits", "Produits"), ("charges", "Charges")]


def _contexte_periode(request):
    p = pa.lire_periode(request.GET)
    du, au = p["du"], p["au"]
    autres = {k: v for k, v in request.GET.items() if k not in ("du", "au", "periode", "mois", "export")}

    def lien(d, f):
        return "?" + urlencode({**autres, "du": d.isoformat(), "au": f.isoformat()})

    annee = du.year
    return {"du": du, "au": au, "periode_code": p["code"], "periodes": PERIODES_RAPIDES, "erreur_periode": p["erreur"],
            "params_periode": urlencode({"du": du.isoformat(), "au": au.isoformat()}), "autres_params": autres,
            "lien_precedent": lien(*pa.decaler(du, au, -1)), "lien_suivant": lien(*pa.decaler(du, au, 1)),
            "mois_choix": [(f"{annee}-{i:02d}", f"{nom} {annee}") for i, nom in enumerate(MOIS, 1)]
            + [(f"{annee - 1}-{i:02d}", f"{nom} {annee - 1}") for i, nom in enumerate(MOIS, 1)],
            "mois_courant": f"{du:%Y-%m}" if du.day == 1 and du.month == au.month and du.year == au.year else "",
            "provisoires": pa.ecritures_provisoires(du, au)}


def _csv(nom, entetes, lignes):
    reponse = HttpResponse(content_type="text/csv; charset=utf-8")
    reponse["Content-Disposition"] = f'attachment; filename="{nom}.csv"'
    reponse.write("﻿")
    w = csv.writer(reponse, delimiter=";")
    w.writerow(entetes)
    w.writerows(lignes)
    return reponse


def _xlsx(nom, entetes, lignes):
    """Classeur Excel natif, avec filtres, en-têtes figés et valeurs numériques."""
    from io import BytesIO

    from django.utils.text import slugify
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    classeur = Workbook()
    feuille = classeur.active
    feuille.title = "Analytique"
    feuille.sheet_view.showGridLines = False
    feuille.append(entetes)
    for ligne in lignes:
        valeurs = []
        for valeur in ligne:
            # Ne jamais transformer un libellé métier en formule Excel.
            if isinstance(valeur, str) and valeur.lstrip()[:1] in ("=", "+", "-", "@"):
                valeur = "'" + valeur
            valeurs.append(valeur)
        feuille.append(valeurs)

    for cellule in feuille[1]:
        cellule.font = Font(bold=True, color="FFFFFF")
        cellule.fill = PatternFill(fill_type="solid", fgColor="1F4E78")
        cellule.alignment = Alignment(horizontal="center", vertical="center")
    feuille.row_dimensions[1].height = 22
    feuille.freeze_panes = "A2"
    feuille.auto_filter.ref = feuille.dimensions
    feuille.print_title_rows = "1:1"
    feuille.page_setup.orientation = "landscape"
    feuille.page_setup.fitToWidth = 1
    feuille.page_setup.fitToHeight = 0
    feuille.sheet_properties.pageSetUpPr.fitToPage = True

    for index, cellules in enumerate(feuille.columns, start=1):
        largeur = max((len(str(cellule.value)) if cellule.value is not None else 0) for cellule in cellules)
        feuille.column_dimensions[get_column_letter(index)].width = min(max(largeur + 2, 12), 42)
        for cellule in cellules[1:]:
            if isinstance(cellule.value, Number) and not isinstance(cellule.value, bool):
                cellule.number_format = '#,##0.00;[Red]-#,##0.00;0.00'

    sortie = BytesIO()
    classeur.save(sortie)
    reponse = HttpResponse(
        sortie.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    nom_sain = slugify(nom) or "analytique"
    reponse["Content-Disposition"] = f'attachment; filename="{nom_sain}.xlsx"'
    return reponse


def _axe_ou_404(axe):
    titre = pa.titre_axe(axe)
    if titre is None:
        raise Http404("Axe analytique inconnu")
    return titre


@login_required
def plan(request):
    """Plan analytique : tous les axes du dossier, avec ce qui leur est affecté sur la période."""
    p = _contexte_periode(request)
    return render(request, "comptabilite/analytique_plan.html", {**p, **pa.synthese_axes(p["du"], p["au"])})


@login_required
def axe(request, axe):
    """Balance d'un axe : chaque élément (gare, véhicule…), le non affecté et le rapprochement avec la générale."""
    titre = _axe_ou_404(axe)
    p = _contexte_periode(request)
    b = pa.balance_axe(axe, p["du"], p["au"])
    tri = request.GET.get("tri", "libelle")
    if tri in ("resultat", "produits", "charges"):                 # classement des éléments
        b["elements"].sort(key=lambda e: e[tri], reverse=True)
    export = request.GET.get("export")
    if export in ("csv", "xlsx", "pdf"):
        entetes = ["Élément", "Produits", "Charges", "Résultat", "Lignes"]
        lignes = [[e["libelle"], e["produits"], e["charges"], e["resultat"], e["lignes"]] for e in b["elements"]]
        lignes.append(["Non affecté", b["non_affecte"]["produits"], b["non_affecte"]["charges"], b["non_affecte"]["resultat"],
                       b["non_affecte"]["lignes"]])
        nom = f"analytique-{axe}-{p['du']}-{p['au']}"
        if export == "pdf":
            lignes_pdf = lignes[:-1] + [
                ["Total des éléments", b["total_elements"]["produits"], b["total_elements"]["charges"],
                 b["total_elements"]["resultat"], b["total_elements"]["lignes"]],
                lignes[-1],
                ["Comptabilité générale", b["gl"]["produits"], b["gl"]["charges"], b["gl"]["resultat"], b["gl"]["lignes"]],
            ]
            rapprochement = "Rapprochement avec la comptabilité générale : " + ("OK." if b["rapproche"] else "ÉCART À ANALYSER.")
            return generer_pdf(nom, f"{_axe_ou_404(axe)} — Balance analytique", p["du"], p["au"],
                               entetes, lignes_pdf, rapprochement)
        return _xlsx(nom, entetes, lignes) if export == "xlsx" else _csv(nom, entetes, lignes)
    return render(request, "comptabilite/analytique_axe.html", {**p, **b, "axe": axe, "titre_axe": titre, "tri": tri,
                                                                "tris": TRIS, "non_affecte_cle": pa.NON_AFFECTE})


@login_required
def element(request, axe, cle):
    """Fiche d'un élément : compte d'exploitation, comptes, grand-livre, évolution, ventilation croisée, comparaison."""
    titre = _axe_ou_404(axe)
    p = _contexte_periode(request)
    etat = request.GET.get("etat", "exploitation")
    if etat not in dict(pa.ETATS):
        etat = "exploitation"
    cle_interne = pa.cle_depuis_url(axe, cle)
    autres_axes = [(c, t) for c, t, _ in pa.axes() if c != axe]
    axe2 = request.GET.get("axe2") or (autres_axes[0][0] if autres_axes else "")
    if axe2 not in dict(autres_axes):
        axe2 = autres_axes[0][0] if autres_axes else ""
    comparer = "n1" if request.GET.get("comparer") == "n1" else "precedente"
    r = pa.etat_element(axe, cle_interne, etat, p["du"], p["au"], axe2=axe2, comparer=comparer)
    libelle = "Non affecté" if cle_interne is None else pa.libelles(axe, [cle_interne]).get(cle_interne, cle)
    export = request.GET.get("export")
    if export in ("csv", "xlsx", "pdf"):
        if etat == "croise" and not r.get("croise_disponible", True):
            return HttpResponse(r["croise_message"], status=409, content_type="text/plain; charset=utf-8")
        nom = f"analytique-{axe}-{cle}-{etat}-{p['du']}-{p['au']}"
        if etat == "comptes":
            entetes = ["Compte", "Intitulé", "Débit", "Crédit", "Lignes"]
            lignes = [[c["compte"], c["intitule"], c["debit"], c["credit"], c["lignes"]] for c in r["comptes"]]
        elif etat == "evolution":
            entetes = ["Période", "Produits", "Charges", "Résultat"]
            lignes = [[s["periode"], s["produits"], s["charges"], s["resultat"]] for s in r["series"]]
        elif etat == "croise":
            entetes = ["Élément", "Produits", "Charges", "Résultat"]
            lignes = [[g["libelle"], g["produits"], g["charges"], g["resultat"]] for g in r["croise"]]
        elif etat == "comparaison":
            entetes = ["Compte", "Intitulé", "Période", "Période précédente", "Écart"]
            lignes = [[c["compte"], c["intitule"], c["actuel"], c["precedent"], c["ecart"]] for c in r["comparaison"]]
        elif etat == "journal":
            entetes = ["Date", "Pièce", "Compte", "Libellé", "Montant"] + [t for _, t in r["journal_axes"]]
            lignes = [[f["date"], f["piece"], f["compte"], f["libelle"], f["montant"], *f["attributions"]]
                      for f in r["journal"]]
        else:
            entetes = ["Date", "Pièce", "Journal", "Compte", "Libellé", "Produit (+) / charge (−)"]
            lignes = [[f["date"], f["piece"], f["journal"], f["compte"], f["libelle"], f["montant"]]
                      for f in r["lignes"]]
        if export == "pdf":
            note = "Montants issus des écritures générales validées ; aucune écriture n'est créée par cet export."
            return generer_pdf(nom, f"{titre} — {libelle} — {dict(pa.ETATS)[etat]}", p["du"], p["au"],
                               entetes, lignes, note)
        return _xlsx(nom, entetes, lignes) if export == "xlsx" else _csv(nom, entetes, lignes)
    lignes_gl = r["lignes"][:1000] if etat == "grand_livre" else []
    return render(request, "comptabilite/analytique_element.html", {
        **p, **r, "axe": axe, "titre_axe": titre, "cle": cle, "libelle": libelle, "etat": etat, "etats": pa.ETATS,
        "axe2": axe2, "autres_axes": autres_axes, "comparer": comparer, "titre_axe2": dict(autres_axes).get(axe2, ""),
        "lignes_gl": lignes_gl, "tronque": etat == "grand_livre" and len(r["lignes"]) > 1000})
