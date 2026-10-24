# Dossier de travail commun pour Claude

## Rôle de cette transmission

L’utilisateur a donné les deux mêmes tâches à Claude et à l’assistant qui a constitué ce Skill. Ce dossier contient les exigences recueillies et une proposition de conception, pas le résultat d’une revue du code de Claude. Aucun contact direct entre leurs sessions n’a été établi.

Claude dispose potentiellement du code et de son propre avancement. Lui demander de commencer par le confronter au présent dossier, au lieu de recréer les modules. Ne pas affirmer que des écarts existent avant d’avoir lu ses livrables.

## Répartition proposée

- Utilisateur : arbitre les points métier non tranchés et valide les exemples de réception.
- Ce Skill : mémoire commune des besoins, invariants proposés et cas limites.
- Claude : inspecte le dépôt, cartographie l’existant, propose les adaptations compatibles, implémente et exécute les contrôles disponibles.
- Revue complémentaire : peut utiliser le compte rendu de Claude fourni par l’utilisateur ; ne pas annoncer cette revue avant réception des éléments.

## Première action de Claude

Lire les instructions locales du dépôt, puis examiner société/agence/dépôt/caisse, droits, commandes, BL, factures, règlements, mouvements, rapports et éventuelle synchronisation. Identifier les contrats et données existants ; ne pas supposer qu’ils portent les noms de MODELE_CONCEPTUEL.csv.

Rendre une matrice avec les colonnes : exigence_id, état (existant vérifié / partiel / absent / non vérifié), fichiers ou écrans concernés, écart précis, adaptation envisagée, décision nécessaire, test et preuve. Une fonctionnalité décrite dans une réponse n’est pas un existant vérifié.

Conserver toutes les exigences E01–E44 et tracer chaque couverture, y compris le complément U4 sur règlements/crédit et auteurs visibles. Traiter les propositions P01–P26 comme des moyens proposés : adapter la réalisation technique, justifier les alternatives et conserver les contrôles métier. Les décisions ouvertes ne sont pas toutes bloquantes ; éviter de redemander ce que l’utilisateur a déjà expliqué.

## Ordre d’intégration proposé

1. Auditer l’existant et figer les définitions du rapport, unités et identifiants d’agence.
2. Sécuriser les rattachements, les reçus et les calculs locaux ; relier BC/BL/factures/avances.
3. Ajouter le rapport commercial et les liaisons avec preuve locale, puis la saisie magasin indépendante.
4. Intégrer la synchronisation et les contrôles globaux en conservant les opérations locales autonomes.
5. Vérifier scénarios de reprise, droits et régression ; documenter les décisions restantes.

Cet ordre est une proposition et n’autorise pas à passer outre des prérequis techniques découverts dans le dépôt.

## Compte rendu à renvoyer

Préciser : version/commit, exigences traitées, fichiers modifiés, migrations, fonctionnalités conservées, captures ou sorties vérifiables, scénarios réellement exécutés, limites hors ligne, décisions ouvertes et prochaine tranche proposée. Ne pas écrire « tout fonctionne » si les tests n’ont pas été exécutés.

Éviter les changements de menus, suppression de calculs ou réécriture générale sans lien avec une exigence. Ne pas modifier le serveur Sage de production ni reprendre ses données en écriture pour réaliser ce projet privé ERP.

## Message de transmission utilisable

« Utilise le Skill erp-ohada-agences-hors-ligne-rapport-stock pour les deux tâches que je t’ai confiées et leur complément sur les règlements. Commence par comparer ses exigences à ton travail et au code existant. Conserve les fonctions déjà présentes. Distingue les besoins confirmés, les propositions et les décisions ouvertes. Fournis ensuite les adaptations et les preuves de recette, en priorité le hors-recettes interagences, le reçu lié à une facture, les avances sans double encaissement, l’auteur visible sur tous les documents et la fiche magasin sans quantités attendues ni double sortie de stock. »
