# Administration — Autorisations, intégrité, maintenance, sauvegardes

Sources : S1 et S14 ; `references/02-menu-fichier.md`, `references/09-disponibilite-et-droits.md`.

## Domaines à maîtriser

- Gestion utilisateurs : identifier chaque opérateur, contrôler autorisations et préférences.
- Gestion des droits : menus, actions, création, modification, suppression, validation, statistiques et impression, suivant version/édition.
- Configuration : SQL Server, connexion, application et société ; ne pas confondre mot de passe Windows/SQL/Sage.
- Sauvegardes : cohérence base Sage et annexes/documents associés, plan de restauration testé.
- Maintenance : contrôles, recalculs/réajustements, journaux de traitement ; à lancer seulement sous conditions documentées.
- Clôture : période commerciale, archivage, purge, sauvegarde fiscale des données ; opérations potentiellement irréversibles.

## Atelier 9.1 — Matrice des autorisations

1. Relever les profils réellement disponibles : administrateur, commercial, magasinier, comptable, direction (profils fictifs).
2. Choisir une action **non destructive** telle que consulter un article ou un état.
3. Tester par rôle autorisé, comparer accès à menu/liste/fiche, visibilité des données et capacité de modifier.
4. Relever les différences sans utiliser le compte administrateur comme indicateur unique.
5. Produire table : action → rôle → autorisation attendue → observation → correction proposée.

## Atelier 9.2 — Plan de sauvegarde et restauration

- Lister les bases pertinentes et ressources annexes ; utiliser les outils recommandés par l'éditeur et un administrateur SQL qualifié.
- Décrire fréquence, destination protégée, chiffrement/accès, durée de conservation, procédure de reprise, personne responsable.
- Exécuter un **test de restauration isolé** sans écraser la production ; prouver l'ouverture du dossier restauré et le contrôle d'intégrité.

## Atelier 9.3 — Pré-clôture

Contrôler pièces en attente, mouvements, stocks négatifs éventuels, inventaires, documents non validés, factures à transférer, états et sauvegardes. Rédiger une check-list de clôture adaptée au dossier, **sans valider ni archiver** à la place de l'utilisateur sans consentement explicite et plan de retour.

## SQL Server — limite de responsabilité

Les commandes en écriture directement sur tables métiers Sage (`UPDATE`, `DELETE`, `INSERT`) sont exclues des exercices. Une requête `SELECT` de diagnostic peut être présentée si la structure est officiellement documentée et que le jeu de données est sécurisé. Préférer l'application/Objets Métiers lorsque requis par le workflow.
