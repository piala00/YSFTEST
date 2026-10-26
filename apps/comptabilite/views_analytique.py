"""Écrans du plan analytique : axes → éléments → états détaillés, sur une période choisie en un clic."""
import csv
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import render

from . import plan_analytique as pa

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
    if request.GET.get("export") == "csv":
        lignes = [[e["libelle"], e["produits"], e["charges"], e["resultat"], e["lignes"]] for e in b["elements"]]
        lignes.append(["Non affecté", b["non_affecte"]["produits"], b["non_affecte"]["charges"], b["non_affecte"]["resultat"],
                       b["non_affecte"]["lignes"]])
        return _csv(f"analytique-{axe}-{p['du']}-{p['au']}", ["Élément", "Produits", "Charges", "Résultat", "Lignes"], lignes)
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
    if request.GET.get("export") == "csv":
        nom = f"analytique-{axe}-{cle}-{etat}-{p['du']}-{p['au']}"
        if etat == "comptes":
            return _csv(nom, ["Compte", "Intitulé", "Débit", "Crédit", "Lignes"],
                        [[c["compte"], c["intitule"], c["debit"], c["credit"], c["lignes"]] for c in r["comptes"]])
        if etat == "evolution":
            return _csv(nom, ["Période", "Produits", "Charges", "Résultat"],
                        [[s["periode"], s["produits"], s["charges"], s["resultat"]] for s in r["series"]])
        if etat == "croise":
            return _csv(nom, ["Élément", "Produits", "Charges", "Résultat"],
                        [[g["libelle"], g["produits"], g["charges"], g["resultat"]] for g in r["croise"]])
        if etat == "comparaison":
            return _csv(nom, ["Compte", "Intitulé", "Période", "Période précédente", "Écart"],
                        [[c["compte"], c["intitule"], c["actuel"], c["precedent"], c["ecart"]] for c in r["comparaison"]])
        if etat == "journal":
            return _csv(nom, ["Date", "Pièce", "Compte", "Libellé", "Montant"] + [t for _, t in r["journal_axes"]],
                        [[f["date"], f["piece"], f["compte"], f["libelle"], f["montant"], *f["attributions"]]
                         for f in r["journal"]])
        return _csv(nom, ["Date", "Pièce", "Journal", "Compte", "Libellé", "Produit (+) / charge (−)"],
                    [[f["date"], f["piece"], f["journal"], f["compte"], f["libelle"], f["montant"]] for f in r["lignes"]])
    lignes_gl = r["lignes"][:1000] if etat == "grand_livre" else []
    return render(request, "comptabilite/analytique_element.html", {
        **p, **r, "axe": axe, "titre_axe": titre, "cle": cle, "libelle": libelle, "etat": etat, "etats": pa.ETATS,
        "axe2": axe2, "autres_axes": autres_axes, "comparer": comparer, "titre_axe2": dict(autres_axes).get(axe2, ""),
        "lignes_gl": lignes_gl, "tronque": etat == "grand_livre" and len(r["lignes"]) > 1000})
