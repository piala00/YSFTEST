"""Copie miroir : reporte toute la base de travail (SQLite) dans la base « miroir » (SQL Server, PostgreSQL…).

    python manage.py miroir            copie complète, puis contrôle table par table (nombre de lignes identique)

La société travaille sur SQLite ; la copie miroir est une seconde base complète, à jour à chaque passage (le
programme .exe la refait automatiquement, par défaut toutes les heures). Sens unique : on n'écrit jamais dans
la base de travail. Tout ou rien : en cas d'erreur, la base miroir reste comme au passage précédent.
Sécurité : refuse une base miroir qui contient des tables étrangères à l'ERP (jamais une base Sage).
"""
import time

from django.apps import apps
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.core.serializers import sort_dependencies
from django.db import connections, transaction


def modeles_dans_l_ordre():
    """Tous les modèles (tables de liaison comprises), chaque table après celles qu'elle référence."""
    ordre = sort_dependencies([(a, None) for a in apps.get_app_configs()], allow_cycles=True)
    liaisons = [m for m in apps.get_models(include_auto_created=True) if m._meta.auto_created and m not in ordre]
    return [m for m in ordre + liaisons if m._meta.managed and not m._meta.proxy]


class Command(BaseCommand):
    help = "Copie complète de la base de travail dans la base miroir (MIROIR_DB_ENGINE), puis contrôle"
    requires_system_checks = []            # la base miroir peut ne pas exister encore (créée par la commande)

    def handle(self, *args, **options):
        if "miroir" not in connections.databases:
            raise CommandError("Aucune base miroir configurée (MIROIR_DB_ENGINE=mssql et MIROIR_DB_HOST, MIROIR_DB_NAME…).")
        source, cible = connections.databases["default"], connections.databases["miroir"]
        if source["ENGINE"] == cible["ENGINE"] and str(source["NAME"]) == str(cible["NAME"]) \
                and source.get("HOST", "") == cible.get("HOST", ""):
            raise CommandError("La base miroir est la base de travail elle-même.")
        debut = time.monotonic()
        if cible["ENGINE"] == "mssql":
            self._creer_base_sqlserver(cible)
        self._controler_tables()
        call_command("migrate", database="miroir", interactive=False, verbosity=0)
        modeles = modeles_dans_l_ordre()
        miroir = connections["miroir"]
        # Une seule photographie de la base de travail (le logiciel continue de servir pendant la copie)
        with transaction.atomic(using="default"):
            lignes = self._copier(modeles, miroir)
        self.stdout.write(self.style.SUCCESS(
            f"Miroir à jour : {len(modeles)} tables, {lignes} lignes identiques ({time.monotonic() - debut:.0f} s) "
            f"→ {cible['ENGINE'].rsplit('.', 1)[-1]} {cible.get('HOST') or ''} {cible['NAME']}".rstrip()))

    def _copier(self, modeles, miroir):
        with transaction.atomic(using="miroir"):
            miroir.disable_constraint_checking()
            try:
                for m in reversed(modeles):
                    m._base_manager.using("miroir").all()._raw_delete("miroir")
                for m in modeles:
                    lot = []
                    for objet in m._base_manager.using("default").order_by("pk").iterator(chunk_size=2000):
                        lot.append(objet)
                        if len(lot) >= 2000:
                            m._base_manager.using("miroir").bulk_create(lot)
                            lot = []
                    if lot:
                        m._base_manager.using("miroir").bulk_create(lot)
            finally:
                miroir.enable_constraint_checking()
            sequences = miroir.ops.sequence_reset_sql(self.style, modeles)
            if sequences:                                        # PostgreSQL : compteurs d'identifiants à jour
                with miroir.cursor() as cur:
                    for sql in sequences:
                        cur.execute(sql)
        ecarts, lignes = [], 0
        for m in modeles:
            n, n_miroir = m._base_manager.using("default").count(), m._base_manager.using("miroir").count()
            lignes += n
            if n != n_miroir:
                ecarts.append(f"{m._meta.db_table} : {n} ≠ {n_miroir}")
        if ecarts:
            raise CommandError("Copie incomplète : " + " ; ".join(ecarts))
        return lignes

    def _creer_base_sqlserver(self, reglage):
        nom = reglage["NAME"]
        if not str(nom).replace("_", "").isalnum():
            raise CommandError(f"Nom de base miroir incorrect : « {nom} » (lettres, chiffres et _ seulement).")
        connections.settings["miroir_maitre"] = {**reglage, "NAME": "master"}
        maitre = connections["miroir_maitre"]
        try:
            with maitre.cursor() as cur:
                cur.execute("SELECT 1 FROM sys.databases WHERE name = %s", [nom])
                if cur.fetchone() is None:
                    cur.execute(f"CREATE DATABASE [{nom}]")
                    self.stdout.write(f"Base miroir {nom} créée sur {reglage['HOST']}.")
        finally:
            maitre.close()

    def _controler_tables(self):
        prefixes = tuple(f"{a.label}_" for a in apps.get_app_configs()) + ("django_",)
        tables = connections["miroir"].introspection.table_names()
        etrangeres = [t for t in tables if not t.startswith(prefixes)]
        if etrangeres:
            raise CommandError(f"La base miroir contient d'autres tables ({', '.join(sorted(etrangeres)[:5])}…) : ce n'est pas "
                               "une base de l'ERP. Choisissez une base vide ou dédiée (jamais une base Sage).")
