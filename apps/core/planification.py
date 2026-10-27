"""Sauvegardes et vérifications automatiques de la base, réglées à l'écran Base de données.

Réglages (configuration.env, appliqués sans redémarrage) :
  ERP_SAUVEGARDE_MODE      heures (toutes les N heures, et au démarrage) | quotidien (chaque jour à HH:MM) | desactive
  ERP_SAUVEGARDE_HEURES    N (défaut 4)              ERP_SAUVEGARDE_HEURE   HH:MM (défaut 22:00)
  ERP_SAUVEGARDE_GARDER    nombre gardé (SQLite)     ERP_SAUVEGARDE_COPIE   second dossier (clé USB, NAS…)
  ERP_SAUVEGARDE_SQL_DOSSIER  dossier des .bak sur le serveur SQL (vide : celui de l'instance)
  ERP_VERIFICATION_AUTO    hebdomadaire (défaut) | desactive
L'état (dernière sauvegarde, dernière vérification et leur résultat) est gardé dans planification.json.
"""
import datetime
import json
import os
import re
from pathlib import Path

MODES = {"heures": "Toutes les N heures (et au démarrage)", "quotidien": "Chaque jour à heure fixe", "desactive": "Désactivées"}
CLES = ("ERP_SAUVEGARDE_MODE", "ERP_SAUVEGARDE_HEURES", "ERP_SAUVEGARDE_HEURE", "ERP_SAUVEGARDE_GARDER",
        "ERP_SAUVEGARDE_COPIE", "ERP_SAUVEGARDE_SQL_DOSSIER", "ERP_VERIFICATION_AUTO")


def reglages(env=None):
    env = os.environ if env is None else env
    try:
        heures = max(1.0, float(env.get("ERP_SAUVEGARDE_HEURES") or 4))
    except ValueError:
        heures = 4.0
    heure = env.get("ERP_SAUVEGARDE_HEURE") or "22:00"
    if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", heure):
        heure = "22:00"
    mode = env.get("ERP_SAUVEGARDE_MODE") or "heures"
    return {"mode": mode if mode in MODES else "heures", "heures": heures, "heure": heure,
            "garder": int(env.get("ERP_SAUVEGARDE_GARDER") or 60), "copie": env.get("ERP_SAUVEGARDE_COPIE", ""),
            "dossier_sql": env.get("ERP_SAUVEGARDE_SQL_DOSSIER", ""),
            "verification": "desactive" if env.get("ERP_VERIFICATION_AUTO") == "desactive" else "hebdomadaire"}


def valider(post):
    """Formulaire de l'écran → valeurs de configuration.env (ValueError si incorrect)."""
    mode = post.get("mode", "heures")
    if mode not in MODES:
        raise ValueError("mode de sauvegarde inconnu")
    try:
        heures = float(str(post.get("heures") or "4").replace(",", "."))
        garder = int(post.get("garder") or 60)
    except ValueError:
        raise ValueError("nombre d'heures et nombre de sauvegardes gardées : des nombres")
    if not 1 <= heures <= 168 or not 1 <= garder <= 1000:
        raise ValueError("de 1 à 168 heures, et de 1 à 1000 sauvegardes gardées")
    heure = post.get("heure") or "22:00"
    if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", heure):
        raise ValueError("heure attendue au format HH:MM")
    return {"ERP_SAUVEGARDE_MODE": mode, "ERP_SAUVEGARDE_HEURES": f"{heures:g}", "ERP_SAUVEGARDE_HEURE": heure,
            "ERP_SAUVEGARDE_GARDER": str(garder), "ERP_SAUVEGARDE_COPIE": (post.get("copie") or "").strip() or None,
            "ERP_SAUVEGARDE_SQL_DOSSIER": (post.get("dossier_sql") or "").strip() or None,
            "ERP_VERIFICATION_AUTO": "desactive" if post.get("verification") == "desactive" else "hebdomadaire"}


def _date(texte):
    try:
        return datetime.datetime.fromisoformat(texte) if texte else None
    except (TypeError, ValueError):
        return None


def prochaine_sauvegarde(etat, config, maintenant):
    """Date de la prochaine sauvegarde automatique (None si désactivées)."""
    derniere = _date(etat.get("derniere_sauvegarde"))
    if config["mode"] == "desactive":
        return None
    if config["mode"] == "heures":
        return maintenant if derniere is None else derniere + datetime.timedelta(hours=config["heures"])
    h, m = map(int, config["heure"].split(":"))
    du_jour = maintenant.replace(hour=h, minute=m, second=0, microsecond=0)
    passee = du_jour if maintenant >= du_jour else du_jour - datetime.timedelta(days=1)   # dernière heure prévue
    if derniere is None or derniere < passee:
        return passee if derniere is not None else du_jour                 # manquée (serveur éteint) : rattrapée
    return passee + datetime.timedelta(days=1)


def sauvegarde_due(etat, config, maintenant):
    prochaine = prochaine_sauvegarde(etat, config, maintenant)
    return prochaine is not None and maintenant >= prochaine


def verification_due(etat, config, maintenant):
    if config["verification"] == "desactive":
        return False
    derniere = _date(etat.get("derniere_verification"))
    return derniere is None or maintenant - derniere >= datetime.timedelta(days=7)


class Planificateur:
    """Un passage par minute (fil du programme compilé) : sauvegarde et vérification quand elles sont dues."""

    def __init__(self, dossier, sauvegarder, verifier, journal=print):
        self.fichier = Path(dossier) / "planification.json"
        self.sauvegarder, self.verifier, self.journal = sauvegarder, verifier, journal

    def etat(self):
        try:
            return json.loads(self.fichier.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    def _ecrire(self, **valeurs):
        etat = {**self.etat(), **valeurs}
        self.fichier.write_text(json.dumps(etat, ensure_ascii=False, indent=1), encoding="utf-8")
        return etat

    def passage(self, maintenant=None):
        maintenant = maintenant or datetime.datetime.now()
        config, etat = reglages(), self.etat()
        if sauvegarde_due(etat, config, maintenant):
            try:
                resultat = str(self.sauvegarder())
                self._ecrire(derniere_sauvegarde=maintenant.isoformat(timespec="seconds"), sauvegarde_ok=True,
                             sauvegarde_resultat=resultat)
                self.journal(f"Sauvegarde automatique : {resultat}")
            except Exception as exc:                              # réessayée au passage suivant, et signalée
                self._ecrire(sauvegarde_ok=False, sauvegarde_resultat=f"ÉCHEC le {maintenant:%d/%m/%Y %H:%M} : {exc}"[:400],
                             derniere_sauvegarde=maintenant.isoformat(timespec="seconds"))
                self.journal(f"Sauvegarde automatique : ÉCHEC — {exc}")
        if verification_due(etat, config, maintenant):
            try:
                intacte, details = self.verifier()
            except Exception as exc:
                intacte, details = False, [f"vérification impossible : {exc}"[:300]]
            self._ecrire(derniere_verification=maintenant.isoformat(timespec="seconds"), verification_ok=intacte,
                         verification_details=list(details)[:10])
            self.journal(f"Vérification automatique de la base : {'aucune erreur' if intacte else 'ERREURS — ' + '; '.join(details[:3])}")

    def resume(self, maintenant=None):
        maintenant = maintenant or datetime.datetime.now()
        etat, config = self.etat(), reglages()
        return {**etat, "config": config, "prochaine": prochaine_sauvegarde(etat, config, maintenant),
                "derniere_sauvegarde_date": _date(etat.get("derniere_sauvegarde")),
                "derniere_verification_date": _date(etat.get("derniere_verification"))}
