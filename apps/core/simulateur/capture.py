"""Capture de l'ERP pour les simulateurs HTML autonomes (version web et version bureau).

Version web : chaque page est rendue par Django (vraies vues, vrais gabarits, données de la base) ;
on conserve le contenu de la zone de travail et ses scripts, le cadre (menus, barre d'outils,
barre de navigation) étant reconstruit dans le navigateur à partir de navigation.py.

Version bureau : on capture les réponses de l'API REST que lit le client CustomTkinter.
"""
import ast
import html
import re
from collections import deque
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client

EXCLUS = ("/admin", "/api/", "/static/", "/deconnexion", "/imprimer/")
MAX_PAGES = 900


def _client():
    utilisateur = get_user_model().objects.filter(is_superuser=True).first()
    if utilisateur is None:
        utilisateur = get_user_model().objects.create_superuser("simulation", "", None)
    client = Client(HTTP_HOST="localhost")
    client.force_login(utilisateur)
    return client, utilisateur


def normaliser(url):
    """Chemin + paramètres triés : deux liens équivalents donnent la même clé."""
    morceaux = urlsplit(html.unescape(url))
    parametres = sorted((k, v) for k, v in parse_qsl(morceaux.query, keep_blank_values=False) if v != "")
    return morceaux.path + (("?" + urlencode(parametres)) if parametres else "")


def _interne(url):
    if not url.startswith("/") or url.startswith("//"):
        return False
    if any(url.startswith(e) or e in url for e in EXCLUS):
        return False
    return "export=" not in url


def _extraire(contenu):
    """Contenu de <main>, scripts inline de fin de page et titre."""
    debut = contenu.find("<main")
    debut = contenu.find(">", debut) + 1
    fin = contenu.rfind("</main>")
    main = contenu[debut:fin]
    scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", contenu[fin:], flags=re.S)
    titre = re.search(r"<title>(.*?)</title>", contenu, flags=re.S)
    return main, [s for s in scripts if s.strip()], html.unescape(titre.group(1).strip()) if titre else ""


def capturer_web(urls_depart, progression=None):
    client, _ = _client()
    pages, vus = {}, set()
    file = deque(normaliser(u) for u in urls_depart)
    while file and len(pages) < MAX_PAGES:
        url = file.popleft()
        if url in vus:
            continue
        vus.add(url)
        reponse = client.get(url)
        if reponse.status_code != 200 or "text/html" not in reponse.get("Content-Type", ""):
            continue
        contenu = reponse.content.decode()
        if "<main" not in contenu:
            continue
        main, scripts, titre = _extraire(contenu)
        pages[url] = {"titre": titre, "html": main, "scripts": scripts}
        for lien in re.findall(r'href="([^"#]+)"', main):
            lien = html.unescape(lien)
            if _interne(lien):
                cible = normaliser(lien)
                if cible not in vus:
                    file.append(cible)
        if progression:
            progression(len(pages))
    # Page de connexion, rendue sans session
    reponse = Client(HTTP_HOST="localhost").get("/connexion/")
    contenu = reponse.content.decode()
    corps = contenu[contenu.find("<body>") + 6:contenu.rfind("<script")]
    pages["/connexion/"] = {"titre": "Connexion", "html": corps, "scripts": []}
    return pages


def ressources_statiques():
    """Feuilles de style et scripts embarqués (aucun accès réseau dans le simulateur)."""
    import base64

    statique = Path(settings.BASE_DIR) / "static"
    police = base64.b64encode((statique / "vendor/fonts/bootstrap-icons.woff2").read_bytes()).decode()
    icones = (statique / "vendor/bootstrap-icons.min.css").read_text(encoding="utf-8")
    icones = re.sub(r'src:url\("fonts/bootstrap-icons\.woff2[^"]*"\) format\("woff2"\),url\("fonts/bootstrap-icons\.woff[^"]*"\) format\("woff"\)',
                    f'src:url("data:font/woff2;base64,{police}") format("woff2")', icones)
    def lire(chemin):
        return (statique / chemin).read_text(encoding="utf-8").replace("</script", "<\\/script")
    return {
        "bootstrap_css": (statique / "vendor/bootstrap.min.css").read_text(encoding="utf-8"),
        "icones_css": icones,
        "erp_css": (statique / "css/erp.css").read_text(encoding="utf-8"),
        "bootstrap_js": lire("vendor/bootstrap.bundle.min.js"),
        "chart_js": lire("vendor/chart.umd.min.js"),
    }


# ---------------------------------------------------------------------------
# Version bureau
# ---------------------------------------------------------------------------
def _liste(client, url):
    donnees = client.get(url).json()
    if isinstance(donnees, list):
        return donnees
    resultats = list(donnees["results"])
    while donnees.get("next"):
        donnees = client.get(donnees["next"].replace("http://localhost", "")).json()
        resultats.extend(donnees["results"])
    return resultats


def capturer_api():
    client, utilisateur = _client()
    from apps.core.navigation import MODULES

    api = {
        "utilisateur": utilisateur.username,
        "navigation": {m.code: client.get(f"/api/navigation/?module={m.code}").json() for m in MODULES},
        "dashboard": client.get("/api/reporting/dashboard/").json(),
        "tiers": {t: _liste(client, f"/api/tiers/?type={t}") for t in ("CLIENT", "FOURNISSEUR")},
        "articles": _liste(client, "/api/articles/"),
        "documents": _liste(client, "/api/documents/"),
        "balance": client.get("/api/reporting/balance/").json(),
        "balance_tiers": client.get("/api/reporting/balance/?compte_debut=4&compte_fin=4").json(),
        "bilan": client.get("/api/reporting/bilan/").json(),
        "compte_resultat": client.get("/api/reporting/compte-resultat/").json(),
        "balance_agee": {t: client.get(f"/api/reporting/balance-agee/?type={t}").json() for t in ("CLIENT", "FOURNISSEUR")},
        "journaux": client.get("/api/journaux/").json(),
    }
    return api


def ecrans_bureau():
    """Correspondance élément de menu → écran natif, lue dans desktop/pages.py (sans importer Tkinter)."""
    source = (Path(settings.BASE_DIR) / "desktop" / "pages.py").read_text(encoding="utf-8")
    arbre = ast.parse(source)
    listes, ecrans = {}, {}

    def valeur(noeud):
        if isinstance(noeud, ast.Constant):
            return noeud.value
        if isinstance(noeud, ast.Subscript):          # el["titre"]
            return {"titre_element": True}
        return None

    for instruction in arbre.body:
        if isinstance(instruction, ast.Assign) and isinstance(instruction.targets[0], ast.Name):
            nom = instruction.targets[0].id
            if isinstance(instruction.value, ast.List):
                listes[nom] = [e.value for e in instruction.value.elts if isinstance(e, ast.Constant)]
            elif nom.startswith("ECRANS_") and isinstance(instruction.value, ast.Dict):
                module = nom.removeprefix("ECRANS_").lower()          # ECRANS_ANALYTIQUE → analytique, etc.
                ecrans[module] = {}
                for cle, fonction in zip(instruction.value.keys, instruction.value.values):
                    appel = fonction.body
                    ecrans[module][cle.value] = {
                        "page": appel.func.id,
                        "args": [valeur(a) for a in appel.args[1:]],
                        "kwargs": {k.arg: valeur(k.value) for k in appel.keywords},
                    }
        # Boucle des types de documents : ECRANS_COMMERCIAL[f"{domaine}.{type}"] = PageDocuments(app, titre, domaine, type)
        if isinstance(instruction, ast.For) and "ECRANS_COMMERCIAL" in ast.unparse(instruction):
            for domaine, liste in (("ventes", "TYPES_VENTE"), ("achats", "TYPES_ACHAT"), ("stocks", "TYPES_STOCK")):
                for type_document in listes.get(liste, []):
                    ecrans["commercial"][f"{domaine}.{type_document.lower()}"] = {
                        "page": "PageDocuments", "args": [{"titre_element": True}, domaine, type_document], "kwargs": {}}
    return ecrans
