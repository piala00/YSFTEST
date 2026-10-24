"""Crée la base SQL Server de l'ERP si elle n'existe pas (installation sur un poste Windows).

Sécurité : refuse une base existante qui contient des tables étrangères à l'ERP (par exemple une base Sage,
dont les tables commencent par F_ ou P_). L'ERP n'écrit jamais dans une autre base que la sienne.
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import connections


class Command(BaseCommand):
    help = "Crée la base SQL Server de l'ERP (DB_NAME) si elle n'existe pas, après contrôle de sécurité."
    requires_system_checks = []            # les contrôles interrogent la base, qui n'existe pas encore

    def handle(self, *args, **options):
        reglage = connections.databases["default"]
        if reglage["ENGINE"] != "mssql":
            raise CommandError("La base configurée n'est pas SQL Server (DB_ENGINE=mssql).")
        nom = reglage["NAME"]
        if not nom.replace("_", "").isalnum():
            raise CommandError(f"Nom de base incorrect : « {nom} » (lettres, chiffres et _ seulement).")
        connections.settings["maitre"] = {**reglage, "NAME": "master"}
        maitre = connections["maitre"]
        try:
            with maitre.cursor() as cur:
                cur.execute("SELECT 1 FROM sys.databases WHERE name = %s", [nom])
                existe = cur.fetchone() is not None
                if not existe:
                    cur.execute(f"CREATE DATABASE [{nom}]")
                    self.stdout.write(self.style.SUCCESS(f"Base {nom} créée sur {reglage['HOST']}."))
                    return
        finally:
            maitre.close()
        with connections["default"].cursor() as cur:
            cur.execute("SELECT name FROM sys.tables")
            tables = [t[0] for t in cur.fetchall()]
        etrangeres = [t for t in tables if not t.startswith(("django_", "auth_", "core_", "commercial_", "comptabilite_",
                                                              "reporting_", "authtoken_"))]
        if etrangeres:
            raise CommandError(f"La base {nom} existe déjà et contient d'autres tables ({', '.join(sorted(etrangeres)[:5])}…). "
                               "Ce n'est pas une base de l'ERP : choisissez un autre nom (jamais une base Sage).")
        self.stdout.write(f"Base {nom} déjà présente ({len(tables)} tables de l'ERP) : elle est conservée.")
