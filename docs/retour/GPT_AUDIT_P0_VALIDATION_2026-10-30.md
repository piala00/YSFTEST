# GPT — audit P0 de validation et clôture — 30 octobre 2026

Source auditée : 0af32c298f2300803ae0b68ecb3d68169430da5e (PR #21, licences 3.1).
Périmètre de ce premier lot : moteur commun Ecriture, clôture d'exercice, droits des actions HTTP et publication
outbox. Les scénarios s'exécutent uniquement sur une société et une agence fictives. Aucun schéma fiscal nouveau.
Ce lot ne prétend pas achever la recette exhaustive de tous les modules.

## Réutilisation et preuves initiales

Reprise de l'audit source unique du 26/10, des tests comptables/échanges existants et de la simulation de #20.
La base 0af32c2 a 523 tests verts en CI SQLite/SQL Server ; la copie Git complète a aussi passé les 523 tests
localement (443,055 s, 2 ignorés). Une première copie exécutée sans autorisation de sockets a eu quatre erreurs
EPERM dans les essais de serveurs locaux : ces erreurs d'environnement n'ont pas été qualifiées de défauts ERP.

Nouveaux scénarios reproduits avant correction : journal local P0_REPRO_AVANT_PROPRE.log, 11 tests,
12 échecs d'assertions/sous-cas en 6,129 s. Les sous-cas ne sont pas 12 anomalies indépendantes.
Le test de profil a ensuite été précisé pour utiliser une pièce distincte par action, sans effet de bord entre
validation et suppression. Deux tests SQL concurrents supplémentaires complètent la suite finale.

## Constats vérifiés et corrections

| Réf. | Priorité | Reproduction sur l'ancienne version | Correction de ce lot |
|---|---|---|---|
| P0-01 | P0 | Un profil LECTURE sur Traitement obtient une redirection au lieu de 403 sur les actions de validation/suppression ; la validation publie réellement une écriture. | Rattacher explicitement ecriture_valider/supprimer au menu ecritures dans le moteur de droits. |
| P0-02 | P0 | Une exception après la publication laisse la pièce VALIDEE malgré l'erreur ; la reprise ne peut pas garantir l'atomicité entre pièce et outbox. | Transaction unique autour du contrôle, du passage VALIDEE et de la publication ; rollback des deux en cas d'échec. |
| P0-03 | P1 | Deux instances chargées avant la première validation publient deux événements pour la même pièce. | Relire et verrouiller l'exercice et la pièce ; décider sur le statut stocké, et non le cache de l'instance. |
| P0-04 | P0 | Une seconde clôture depuis une instance d'exercice périmée génère un second à-nouveau. | Verrouiller et relire l'exercice avant les préconditions et le calcul des reports. |
| P0-05 | P0 | Une pièce attachée à N mais datée au-delà de sa fin est validée. | Contrôler date_debut <= date <= date_fin sur l'exercice réellement stocké. |
| P0-06 | P0 | Un exercice ou journal fermé après le chargement de l'objet reste considéré ouvert par son cache. | Relire les états de clôture avec verrou avant validation ; verrouiller aussi les références dans creer_ecriture. |
| P0-07 | P1 | Des totaux équilibrés peuvent contenir une ligne négative, débit et crédit simultanés, ou une ligne entièrement nulle. | Appliquer clean de chaque LigneEcriture avant validation ; conserver la normalisation des signes de creer_ecriture. |

Les modèles sont rechargés pour les décisions sensibles. La publication d'une écriture utilise le même alias
de base que la pièce ; site, séquence et événement sortant suivent cet alias. Les autres appelants conservent
le défaut existant. Aucune migration de données n'est introduite.

## Recette ajoutée

apps/comptabilite/tests_p0_validation.py :

- date hors exercice, lignes invalides, exercice/journal clôturés après chargement ;
- validation deux fois depuis deux objets périmés, publication réelle unique ;
- panne injectée après écriture réelle dans l'outbox : état, événement et reprise cohérents ;
- scénario nominal équilibré ; GET refusé pour les seules routes d'action ;
- profil lecture refusé en POST et pièce validée non supprimable ;
- double clôture depuis un ancien objet sans double report ;
- deux connexions et deux threads réels pour validation et clôture sur moteurs supportant select_for_update,
  notamment SQL Server : verrou borné, un événement ou report. SQLite ignore ces deux tests de verrous de lignes,
  sa concurrence ne doit pas être assimilée à celle de SQL Server.

Les pages GET qui affichent un formulaire de vente ou de clôture ne sont pas supprimées : le critère pertinent
est l'absence de mutation financière en GET, et le refus des routes de mutation en GET. Un refus global de toutes
les pages de formulaire casserait le parcours utilisateur.

Résultat ciblé après correction : 13 tests, OK, 2 ignorés sur SQLite. Les tests concurrents doivent effectivement
passer sur SQL Server avant de les annoncer validés. Suite complète locale effectivement exécutée :
536 tests en 436,817 s, OK (4 ignorés : deux existants et les deux essais de verrous de lignes).
Commande : python manage.py test --noinput --parallel 4 -v1, environnement de test SQLite fictif,
autorisation réseau limitée au cadre des essais pour les serveurs locaux. Journaux : P0_CIBLE_APRES.log et
P0_COMPLET_APRES.log dans l'espace de travail ; les résultats SQL Server/Windows seront ajoutés dans la PR.

## Limites et suite

Cette recette n'est ni une certification OHADA, ni une simulation de toute charge multi-caisses. Restent à
étendre : documents, règlements, billetterie, journée de caisse, décomptes et incidents, erreurs transitoires et
retries SQLite, actions fines par journal et origine d'agence, matrice complète par système/exercice.
Les analyses et journaux existants sont conservés ; les règles contractuelles de commission et de pertes restent
à confirmer. Aucun merge, déploiement ou basculement de production n'est réalisé.
