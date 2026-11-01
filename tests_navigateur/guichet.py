"""Contrôle Chromium du vrai bureau Django sur un dossier jetable, jamais sur une société existante."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.request

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE))


def main():
    with tempfile.TemporaryDirectory(prefix="erp-guichet-navigateur-") as temporaire:
        os.environ.update(DJANGO_SETTINGS_MODULE="erp.settings", DB_ENGINE="sqlite", DATABASE_URL="",
                          SQLITE_FICHIER=str(Path(temporaire) / "fictif.sqlite3"), MIROIR_DB_ENGINE="",
                          ERP_EDITION="transport", DEBUG="1", ALLOWED_HOSTS="localhost,127.0.0.1")
        import django
        django.setup()
        from django.core.management import call_command
        from django.contrib.auth import get_user_model
        from django.urls import reverse
        from apps.transport.models import Depart
        from playwright.sync_api import sync_playwright

        dossier = Path(os.environ.get("RUNNER_TEMP", temporaire)) / "guichet-navigateur"
        dossier.mkdir(exist_ok=True)
        call_command("migrate", verbosity=0, interactive=False)
        call_command("init_erp", "--activite", "transport", "--demo", verbosity=0)
        get_user_model().objects.create_superuser("controle-guichet", "", "Essai-Guichet-2026")
        depart = Depart.objects.filter(statut=Depart.PROGRAMME, site_origine="").first()
        assert depart is not None
        origine = "http://127.0.0.1:18100"
        with (dossier / "serveur.txt").open("w") as journal:
            serveur = subprocess.Popen([sys.executable, "manage.py", "runserver", "127.0.0.1:18100", "--noreload"],
                                       cwd=RACINE, env=os.environ.copy(), stdout=journal, stderr=journal)
            try:
                for _ in range(120):
                    try:
                        urllib.request.urlopen(origine + "/connexion/", timeout=1).close()
                        break
                    except Exception:
                        if serveur.poll() is not None:
                            raise RuntimeError("Serveur arrêté")
                        time.sleep(.25)
                else:
                    raise RuntimeError("Serveur indisponible")
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page(viewport={"width": 1600, "height": 1000})
                    page.goto(origine + "/connexion/")
                    page.locator('[name="username"]').fill("controle-guichet")
                    page.locator('[name="password"]').fill("Essai-Guichet-2026")
                    page.get_by_role("button", name="Se connecter").click()
                    page.goto(origine + reverse("billetterie:accueil"))
                    page.wait_for_function("Boolean(window.erpFenetres)")
                    url = reverse("transport:billet_vente") + f"?depart={depart.pk}"
                    page.evaluate("url => { window.erpFenetres.ouvrir(url); }", url)
                    page.wait_for_function("document.querySelector('.fenetre-mdi')?.getBoundingClientRect().width === 380")
                    cadre = page.locator(".fenetre-mdi iframe").last.element_handle().content_frame()
                    cadre.wait_for_selector('[name="telephone"]')
                    assert cadre.locator('[name="gare_montee"]').is_hidden()
                    assert cadre.locator('[name="depart_correspondance"]').is_hidden()
                    assert cadre.evaluate("document.documentElement.scrollWidth <= innerWidth"), "Débordement horizontal"
                    # Le choix du véhicule reste saisissable au clavier, sans liste native à parcourir.
                    recherche = cadre.locator('#id_depart-recherche')
                    recherche.fill(depart.numero)
                    recherche.press("Enter")
                    assert cadre.locator('[name="depart"]').input_value() == str(depart.pk)
                    assert cadre.locator('[name="depart"]').is_hidden()
                    filtre = cadre.locator('.depart-recherche').first
                    assert filtre.get_by_label("VIP", exact=True).is_checked()
                    assert filtre.get_by_label("Classique", exact=True).is_checked()
                    filtre.get_by_label("VIP", exact=True).uncheck()
                    filtre.get_by_label("Classique", exact=True).uncheck()
                    assert cadre.locator('[name="depart"]').input_value() == ""
                    assert filtre.locator('[role="status"]').inner_text().startswith("Aucun départ")
                    filtre.get_by_label("VIP", exact=True).check()
                    filtre.get_by_label("Classique", exact=True).check()
                    recherche.fill(depart.numero)
                    recherche.press("Enter")
                    cadre.locator('[name="voyageur"]').fill("Alice Fictive")
                    cadre.locator('[name="voyageur"]').press("Enter")
                    assert cadre.locator('[name="piece_identite"]').evaluate("e => e === document.activeElement")
                    page.screenshot(path=str(dossier / "01-vente-portrait.png"))
                    # Une seconde voiture s'ouvre sans fermer ni écraser la saisie de la première.
                    page.evaluate("url => { window.erpFenetres.ouvrir(url); }", url + "&mode=correspondance")
                    page.wait_for_function("document.querySelectorAll('.fenetre-mdi').length === 2 && [...document.querySelectorAll('.fenetre-mdi')].every(e=>e.getBoundingClientRect().width === 380)")
                    second = page.locator(".fenetre-mdi iframe").last.element_handle().content_frame()
                    second.wait_for_selector('#id_depart_correspondance-recherche', state="visible")
                    assert cadre.locator('[name="voyageur"]').input_value() == "Alice Fictive"
                    # Redimensionnement choisi par le guichetier préservé après rechargement.
                    page.evaluate("() => { const f=window.erpFenetres.active(); f.ajustee=true; f.l=510; f.iframe.contentWindow.location.reload(); }")
                    page.wait_for_function("window.erpFenetres.active().el.getBoundingClientRect().width === 510")
                    page.screenshot(path=str(dossier / "02-correspondance-fenetres.png"))
                    page.evaluate("url => { window.erpFenetres.ouvrir(url); }", reverse("transport:billets_transit") + f"?depart={depart.pk}")
                    transit = page.locator(".fenetre-mdi iframe").last.element_handle().content_frame()
                    transit.wait_for_selector('text=Billet déjà payé : placer le passager')
                    page.screenshot(path=str(dossier / "03-transit.png"))
                    page.evaluate("url => { window.erpFenetres.ouvrir(url); }", reverse("transport:transvasement"))
                    secours = page.locator(".fenetre-mdi iframe").last.element_handle().content_frame()
                    secours.wait_for_selector('[name="part_restante"]')
                    page.screenshot(path=str(dossier / "04-transvasement.png"))
                    # Téléphone : rendu étroit réel, sans débordement du formulaire.
                    mobile = browser.new_page(viewport={"width": 320, "height": 740})
                    mobile.context.add_cookies(page.context.cookies())
                    mobile.goto(origine + url)
                    mobile.wait_for_selector('[name="telephone"]')
                    assert mobile.evaluate("document.documentElement.scrollWidth <= innerWidth"), "Débordement sur petit écran"
                    mobile.screenshot(path=str(dossier / "05-petit-ecran.png"))
                    (dossier / "resultat.json").write_text(json.dumps({"resultat": "OK", "navigateur": browser.version,
                        "largeur_initiale": 380, "controles": ["vrai bureau MDI", "champs courants", "clavier Entrée",
                        "correspondance visible", "deux fenêtres et saisie conservée", "redimensionnement conservé",
                        "transit", "transvasement", "petit écran 320px sans débordement"]}, ensure_ascii=False, indent=2))
                    print("Chromium : guichet portrait, clavier, fenêtres, transit, transvasement, mobile OK")
                    browser.close()
            finally:
                serveur.terminate()
                serveur.wait(timeout=20)


if __name__ == "__main__":
    main()

