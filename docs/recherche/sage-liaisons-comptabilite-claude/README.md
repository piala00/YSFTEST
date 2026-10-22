# Liaisons avec la comptabilité Sage — dossier pour Claude

Version 0.1 — recherche documentaire du 21 octobre 2026.

Objet : comprendre les liens entre modules et l’impact de la création des tiers, des paramètres société et des autorisations pour concevoir l’ERP OHADA privé de l’utilisateur.

Ce dossier thématique est distinct des étapes 3 (écrans/états) et 4 (reprise SQL/hébergement). Il n’ajoute pas une étape numérotée et ne remplace aucun livrable précédent. Aucun accès à une installation Sage ou modification de l’ERP n’a été réalisé.

## Lecture recommandée

1. Lire `RAPPORT.md` pour les distinctions et les résultats.
2. Lire `references/FAITS_DOCUMENTES.csv` avec `SOURCES.csv` : chaque fait conserve produit et version de sa source.
3. Utiliser `CARTOGRAPHIE_LIAISONS.csv` pour déterminer quel flux existe et par quel canal.
4. Examiner `IMPACTS_PARAMETRAGE.csv`, `DROITS_ET_AUTORISATIONS.csv` et `CYCLE_TIERS.md`.
5. Pour l’ERP, lire `CONTRAT_ERP_PROPOSE.md`, puis les scénarios de recette. Ces éléments sont des propositions, pas des comportements Sage certifiés.
6. Transmettre `PROMPT_CLAUDE.md` avec l’ensemble du ZIP.

## Niveau de couverture

Le cœur Sage 100 est étudié avec des sources officielles. Les flux Paie, Batigest, CRM, automatisation, recouvrement et reporting sont différenciés. X3, FRP 1000 et Sage 50 sont abordés comme familles distinctes, sans leur inventer une liaison universelle avec Sage 100 Comptabilité. SCD, GPAO et certains produits périphériques restent à approfondir.

La structure V12.20 est attestée ; beaucoup d’aides fonctionnelles ne portent pas de build. Une date de mise à jour ou la mention ©2026 ne prouve pas à elle seule une version V12. Les guides CRM de 2016/2017 et le manuel de fonctions communes 2016 sont historiques.

CSV UTF-8 avec BOM, séparateur point-virgule. `NON_RELEVE` n’est ni « absent » ni « interdit ». Les scénarios sont NON_EXECUTE : aucun résultat de test dans Sage n’est revendiqué. Aucun secret ni donnée d’entreprise n’est inclus. Les documents officiels complets ne sont pas redistribués.
