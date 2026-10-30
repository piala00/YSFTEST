"""Diagnostic de structure sans écriture ; application des seules migrations connues de l'ERP."""
from django.apps import apps
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor


def analyser():
    attendues = {m._meta.db_table: m for m in apps.get_models(include_auto_created=True)
                 if m._meta.managed and not m._meta.swapped and m._meta.can_migrate(connection)}
    presentes = set(connection.introspection.table_names())
    etrangeres = sorted(presentes - set(attendues) - {"django_migrations"})
    anomalies = []
    with connection.cursor() as cur:
        for table, modele in sorted(attendues.items()):
            if table not in presentes:
                anomalies.append(f"Table absente : {table}.")
                continue
            colonnes = {c.name.casefold() for c in connection.introspection.get_table_description(cur, table)}
            for champ in modele._meta.local_fields:
                if champ.column and champ.column.casefold() not in colonnes:
                    anomalies.append(f"Colonne absente : {table}.{champ.column}.")
    executor = MigrationExecutor(connection)
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    migrations = [f"{m.app_label}.{m.name}" for m, retour in plan if not retour]
    details = [f"{len(presentes)} tables présentes ; {len(attendues)} tables attendues par cette version."]
    details += anomalies[:150]
    if len(anomalies) > 150:
        details.append(f"{len(anomalies) - 150} anomalie(s) supplémentaire(s).")
    if migrations:
        details.append("Migrations en attente : " + ", ".join(migrations))
    if etrangeres:
        details.append("Tables extérieures au modèle de cette version : " + ", ".join(etrangeres[:20]))
    if not anomalies and not migrations:
        details.append("Tables et colonnes attendues présentes, migrations à jour.")
    details.append("Cette analyse ne recrée pas les données perdues et ne valide pas à elle seule tous les types, index ou contraintes.")
    return {"ok": not anomalies and not migrations and not etrangeres, "details": details,
            "anomalies": anomalies, "migrations": migrations, "etrangeres": etrangeres}


def appliquer_migrations(sauvegarder):
    diagnostic = analyser()
    if diagnostic["etrangeres"]:
        raise ValueError("Présence de tables extérieures à l'ERP : aucune modification de structure autorisée.")
    if not diagnostic["migrations"]:
        if diagnostic["anomalies"]:
            raise ValueError("Des éléments déjà migrés sont absents : restauration d'une sauvegarde saine ou intervention de l'éditeur nécessaire.")
        return {"ok": True, "details": ["Aucune migration à appliquer ; aucune structure modifiée."]}
    from .base_donnees import verifier

    intacte, _ = verifier()
    if not intacte:
        raise ValueError("Intégrité en erreur : aucune migration appliquée. Restaurez d'abord une sauvegarde saine.")
    fichier = sauvegarder()  # L'échec de cette étape empêche toute migration.
    if not fichier:
        raise ValueError("La sauvegarde préalable n'a pas été confirmée.")
    call_command("migrate", database=connection.alias, interactive=False, verbosity=0)
    apres = analyser()
    apres["details"].insert(0, f"Sauvegarde préalable : {fichier}.")
    return apres
