# Administration du poste en onglets — Codex, 30 octobre 2026

Lot dépendant du durcissement de la distribution (#13). Les onglets communs sont Ce poste, Licence, Base de données, Sauvegarde et restauration, Import et export agences, Simulation. Les pages gardent un accès direct et leur onglet actif ; les fonctions ne sont pas affichées toutes en vrac.

Réutilisation : `views_poste.base_donnees`, sauvegardes et restauration natives, planification, `echanges.views.echanges` et ses lots chiffrés/idempotents existants. Le nouvel accès aux échanges depuis l'administration est réservé au superutilisateur ; les parcours de service existants restent disponibles. Les règles de licence existantes pour la gestion de base et les sauvegardes sont conservées.

L'analyse de structure compare les tables et colonnes attendues et les migrations appliquées, sans écriture. Elle complète l'intégrité SQLite / DBCC CHECKDB existante ; elle ne prétend pas valider chaque type/index/contrainte. Les tables extérieures à l'ERP sont signalées et interdisent l'application des migrations. Une table ou colonne absente alors que sa migration est déjà appliquée n'est pas recréée par devinette : restauration saine ou intervention nécessaire.

Sur le poste serveur, après fin des saisies et confirmation METTRE A JOUR, seules les migrations officielles en attente peuvent être appliquées, après vérification de l'intégrité et sauvegarde réussie. Réparation des index et optimisation imposent aussi le poste serveur et une sauvegarde préalable. Aucun mécanisme de réparation acceptant une perte de données n'a été ajouté.

Tests ajoutés : navigation et onglet actif, droits GET/POST, diagnostic réel, colonne manquante, refus de réparation arbitraire, tables étrangères, sauvegarde en échec, confirmation et accès distant. Compilation syntaxique locale exécutée ; suite complète soumise à la CI (Django local indisponible). Aucune production manipulée, aucune fusion ni déploiement.
