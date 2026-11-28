# 08 — Retour à fournir par Claude Code pour analyse collaborative

Préparer `RETOUR_CLAUDE_ERP_REPORTING_SIMULATION_WINDOWS.zip`, après les travaux réellement réalisés, avec :

1. `README-RETOUR.md` : branche/commit, environnement, résumé, modules achevés/inachevés.
2. `AUDIT_EXISTANT.md` : fichiers, modèles, routes, écrans et bugs constatés ; preuve source.
3. `DIFF_MODIFICATIONS.patch` ou code source modifié complet (sans environnements virtuels, secrets, comptes utilisateurs, données clients, archives gigantesques).
4. `MIGRATIONS_ET_ROLLBACK.md` : migrations, plan de sauvegarde, retour arrière, aucune modification silencieuse.
5. `CONTROLES_GL_ANALYTIQUE.md` : tests débit/crédit, imputations des 10 plans, non-affectés, synthèses d'agences et états propriétaires.
6. `SIMULATION_3_MOIS.md`, `SIMULATION_12_MOIS.md`, fichiers JSON/CSV contrôlés, paramètres `seed`, dates, echelle et taux fictifs ; si non exécutés, indiquer clairement **NON TESTÉ**.
7. `CATALOGUE_REPORTING.md` : liste d'états et filtres réellement disponibles, endpoints, captures ou exports.
8. `BUILD_WINDOWS.md` : commandes, environnement, exe réellement construits, hash SHA256, test de lancement et captures ; sinon **COMPILATION NON RÉALISÉE**.
9. `BUGS_ET_LIMITES.md` classés par criticité et étapes pour reproduire.

Rendre le ZIP prêt à être transmis au consultant assistant pour une seconde revue ; séparer **spécification**, **code ajouté**, **tests réussis**, **reste à développer**.
