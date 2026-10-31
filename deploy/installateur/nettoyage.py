"""Écran de nettoyage proposé APRÈS désinstallation ; jamais d'effacement silencieux."""
import argparse
from contextlib import closing
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import zipfile

if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from apps.licences import nettoyage as n


def main(argv=None, _essai=False):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--programme", type=Path)
    p.add_argument("--donnees", type=Path)
    p.add_argument("--edition", choices=("transport", "commerce"))
    p.add_argument("--recette-fictive", action="store_true", help="Crée ses propres fichiers temporaires ; aucun chemin fourni n'est utilisé.")
    a = p.parse_args(argv)
    if a.recette_fictive:
        return recette_fictive()
    if not all((a.programme, a.donnees, a.edition)):
        p.error("programme, donnees et edition sont requis")
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext

    fenetre = tk.Tk()
    fenetre.title("ERP OHADA — Données après désinstallation")
    fenetre.geometry("820x640")
    fenetre.minsize(620, 420)
    tk.Label(fenetre, text=f"Nettoyage contrôlé — {a.edition.capitalize()}", font=("Segoe UI", 14)).pack(pady=8)
    texte = scrolledtext.ScrolledText(fenetre, wrap="word", height=10, font=("Segoe UI", 10))
    texte.pack(fill="both", expand=True, padx=12)
    approuve = tk.BooleanVar(value=False)
    plan = None

    def afficher():
        nonlocal plan
        plan = n.inventorier(a.programme, a.donnees, a.edition)
        texte.delete("1.0", "end")
        texte.insert("end", "Les données et sauvegardes ci-dessous seront effacées UNIQUEMENT après une nouvelle sauvegarde vérifiée et votre confirmation.\n\n")
        for f in plan["fichiers"]:
            texte.insert("end", f"À sauvegarder puis supprimer : {Path(plan['racines'][f['genre']]) / f['relatif']} ({f['taille']} octets)\n")
        for d in plan["repertoires"]:
            texte.insert("end", f"Dossier à retirer s'il est vide : {Path(plan['racines'][d['genre']]) / d['relatif']}\n")
        for f in plan["conserves"]:
            texte.insert("end", f"CONSERVÉ : {f['chemin']} — {f['raison']}\n")
        texte.insert("end", "\n" + "\n".join(plan["avertissements"]))

    def executer():
        if not approuve.get():
            messagebox.showinfo("Vérification requise", "Examinez l'inventaire et cochez la confirmation.")
            return
        try:
            if os.name == "nt":
                nom = f"ERP-OHADA-{a.edition.capitalize()}.exe"
                r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq " + nom, "/FO", "CSV", "/NH"],
                                   capture_output=True, text=True, check=True)
                if nom.lower() in r.stdout.lower():
                    raise ValueError("Le programme tourne encore : arrêtez-le avant de nettoyer ses données.")
            destination = filedialog.askdirectory(title="Sauvegarde : choisir un dossier HORS de ceux à nettoyer")
            if not destination:
                return
            archive = Path(destination) / f"ERP-{a.edition}-avant-nettoyage-{datetime.datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:8]}.zip"
            n.sauvegarder(plan, archive)
            if not messagebox.askyesno("Sauvegarde vérifiée — confirmer l'effacement",
                    f"La sauvegarde a été relue et ses empreintes vérifiées :\n{archive}\n\nSupprimer définitivement les {len(plan['fichiers'])} fichiers inventoriés ?\nLes fichiers indiqués CONSERVÉ resteront présents.", default="no"):
                messagebox.showinfo("Données conservées", f"Aucune suppression. Sauvegarde disponible :\n{archive}")
                return
            resultat = n.effacer(plan, archive, confirmation=True)
            texte.insert("end", "\n\nRÉSULTAT\n" + json.dumps(resultat, ensure_ascii=False, indent=2))
            texte.see("end")
            messagebox.showinfo("Résultat du nettoyage", f"{len(resultat['supprimes'])} fichiers supprimés ; {len(resultat['erreurs'])} erreurs ; {len(resultat['conserves'])} éléments préservés.\nRapport à côté de la sauvegarde. Consultez les chemins et raisons ci-dessous.")
            bouton.configure(state="disabled")
        except (ValueError, OSError, zipfile.BadZipFile, subprocess.SubprocessError) as exc:
            messagebox.showerror("Nettoyage arrêté", str(exc) + "\nLes éléments non traités sont conservés ; vérifiez le rapport éventuel à côté de la sauvegarde.")

    tk.Checkbutton(fenetre, text="J'ai examiné les fichiers à supprimer et les éléments conservés.", variable=approuve).pack(pady=6)
    def rafraichir():
        try:
            approuve.set(False)
            afficher()
        except (ValueError, OSError) as exc:
            messagebox.showerror("Inventaire impossible", str(exc))
    tk.Button(fenetre, text="Rafraîchir l'inventaire", command=rafraichir).pack(pady=2)
    boutons = tk.Frame(fenetre)
    boutons.pack(fill="x", padx=12, pady=10)
    tk.Button(boutons, text="Fermer et conserver les données", command=fenetre.destroy).pack(side="left")
    bouton = tk.Button(boutons, text="Sauvegarder, vérifier et confirmer…", command=executer)
    bouton.pack(side="right")
    try:
        afficher()
    except (ValueError, OSError) as exc:
        texte.insert("end", "Inventaire impossible : " + str(exc) + "\nAucune suppression n'est proposée.")
        bouton.configure(state="disabled")
    if _essai:
        def parcours():
            approuve.set(True)
            bouton.invoke()
            fenetre.destroy()
        fenetre.after(200, parcours)
    fenetre.mainloop()
    return 0


def recette_fictive():
    """Pilote la vraie fenêtre et son bouton sur des dossiers créés ici, jamais des chemins externes."""
    import sqlite3
    import tempfile
    from unittest import mock
    from tkinter import filedialog, messagebox

    with tempfile.TemporaryDirectory(prefix="ERP-nettoyage-fictif-") as temporaire:
        racine = Path(temporaire).resolve()
        programme, donnees = racine / "programme", racine / "donnees"
        n.marquer(programme, "transport")
        n.marquer(donnees, "transport")
        with closing(sqlite3.connect(donnees / "erp.sqlite3")) as c, c:
            c.execute("CREATE TABLE fictif (texte TEXT)")
        temoin = racine / "autre-edition.txt"
        temoin.write_text("préserver")
        erreurs = []
        with mock.patch.object(filedialog, "askdirectory", return_value=str(racine)), \
             mock.patch.object(messagebox, "askyesno", return_value=True), \
             mock.patch.object(messagebox, "showinfo"), \
             mock.patch.object(messagebox, "showerror", side_effect=lambda *a: erreurs.append(a)):
            main(["--programme", str(programme), "--donnees", str(donnees), "--edition", "transport"], _essai=True)
        assert not erreurs, erreurs
        assert not donnees.exists() and not programme.exists(), "Dossiers fictifs non nettoyés."
        assert temoin.read_text() == "préserver"
        archive = next(racine.glob("ERP-*.zip"))
        assert archive.with_suffix(".rapport.json").is_file()
        rapport = Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir())) / "NETTOYAGE-INTERFACE-FICTIVE.json"
        rapport.write_text(json.dumps({"resultat": "OK", "fenetre": "Tk réelle et bouton invoqué", "confirmation": "Dialogues simulés sur données fictives",
                                      "sauvegarde": "ZIP effectivement créé, relu et vérifié avant suppression", "production": "Aucun chemin de production utilisé."}, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        if "--recette-fictive" in sys.argv:
            import tempfile
            (Path(os.environ.get("RUNNER_TEMP", tempfile.gettempdir())) / "NETTOYAGE-INTERFACE-ERREUR.txt").write_text(str(exc), encoding="utf-8")
            raise SystemExit(1)
        raise
