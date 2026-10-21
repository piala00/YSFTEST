---
name: sage100-sql-hebergement
description: Préparer une reprise en lecture seule de Sage 100 SQL Server à partir des colonnes documentées V12.20 et comparer l’hébergement Django/PostgreSQL, ses coûts, sa persistance et ses sauvegardes. Utiliser pour confirmer les champs tiers, comptes, articles, journaux et écritures, choisir les filtres de norme et cadrer un hébergement économique.
---

# Sage 100 : reprise SQL et hébergement

Version 0.1 — étape 4, recherches R12 et R13 du cahier ERP OHADA du 21/10/2026.

## Procédure

1. Lire [PORTEE_ET_TYPES.md](references/PORTEE_ET_TYPES.md). Distinguer structure logique V12.20, schéma SQL effectivement observé et choix d’ERP.
2. Charger [COLONNES_SQL_SAGE.csv](references/COLONNES_SQL_SAGE.csv) avec [STATUT_COLONNES.csv](references/STATUT_COLONNES.csv). La colonne `type` contient le type du manuel, jamais une transcription SQL Server présumée.
3. Lire [CONTRAINTES_DOCUMENTAIRES.csv](references/CONTRAINTES_DOCUMENTAIRES.csv), [JOINTURES_REPRISE.csv](references/JOINTURES_REPRISE.csv) et [FILTRES_ET_PIEGES.csv](references/FILTRES_ET_PIEGES.csv) avant de concevoir l’extracteur. Ne pas transformer un lien logique en FK SQL observée.
4. Suivre [PROTOCOLE_REPRISE.md](references/PROTOCOLE_REPRISE.md). Utiliser les modèles [01_metadata_lecture_seule.sql](scripts/01_metadata_lecture_seule.sql) puis [02_profil_ecritures.sql](scripts/02_profil_ecritures.sql) seulement après vérification des schémas et des colonnes. Ces requêtes n’ont pas été exécutées sur Sage pendant la recherche.
5. Pour héberger, lire [HEBERGEMENT_2026.md](references/HEBERGEMENT_2026.md), [OFFRES_HEBERGEMENT_2026.csv](references/OFFRES_HEBERGEMENT_2026.csv) puis [SAUVEGARDE_ET_RESTAURATION.md](references/SAUVEGARDE_ET_RESTAURATION.md). Actualiser les tarifs avant tout engagement.
6. Résoudre les limites dans [INCONNUES.csv](references/INCONNUES.csv) ; retrouver les URL dans [SOURCES.csv](references/SOURCES.csv). Utiliser [CAS_DE_REVUE.csv](references/CAS_DE_REVUE.csv) pour préparer la recette.

## Garde-fous

- Garder Sage en lecture seule et la zone d’import ERP séparée. Ne pas modifier une base Sage par SQL avec ce skill.
- Ne pas copier les schémas d’un autre produit Sage ni certifier V9 à partir de V12.20.
- Conserver `EC_Norme=0` dans les vues nationale et IFRS concernées ; ne pas additionner ensuite ces deux vues.
- Ne pas appeler `EC_CType`, `EC_Cloture` ou `EC_Impression` un marqueur de simulation.
- Préserver les codes d’unité et de catégorie avec leurs libellés ; ne pas inventer leur colonne physique d’indice.
- Garder les numéros de compte et références en chaînes, les anomalies en quarantaine et la traçabilité par dossier source.
- Traiter Neon et Supabase comme services de base/backend : chiffrer séparément le serveur Django.
- Ne pas présenter une offre gratuite, un déploiement réussi ou un fichier de sauvegarde présent comme une restauration vérifiée.

Tous les CSV sont UTF-8 à séparateur `;`. `NON_RELEVE` signifie non observé, pas absence de colonne. `A-CONFIRMER` ne permet pas une activation automatique. Aucun identifiant d’accès ni donnée d’entreprise n’est inclus.
