# Collaboration utilisateur — Claude Code — ChatGPT : contrat de retour

Le maître d'ouvrage veut nous renvoyer le résultat **et une copie complète du code de son ERP** pour ré-analyse. Claude Code doit donc préparer un dossier clair, NON un simple « tout est terminé ».

## À remettre dans `RETOUR_CLAUDE_CODE_ERP_TRANSPORT.zip`
1. **Code complet du projet** : sources, front/back, modèles, configurations exemple expurgées, migrations, écrans et ressources nécessaires à reconstruire l'ERP, scripts de démarrage, tests ; fournir un manifeste des chemins et versions ; exclure `node_modules`, caches, grosses dépendances réinstallables.
2. `RETOUR_POUR_CHATGPT.md` : architecture constatée, stack réelle, nouvelles fonctionnalités faites/pas faites, écarts, état par module, choix de design, fichiers modifiés, tests exécutés et résultats (avec erreurs), suivi des anomalies (notamment RJ).
3. `SCHEMA_BASE.md` / diagrammes/DDL sans données réelles ; `MAPPING_JOURNAUX_ET_ANALYTIQUE.md` ; `LISTE_DES_ROUTES_API.md` ; migrations et procédures rollback.
4. `BILAN_SIMULATION_SEPTEMBRE_2026.md` : données importées, balances, grands livres, paie, stocks, dettes fournisseur et partenaires, reporting agence/véhicule et résultats validés ou divergents.
5. `AUDIT_ECARTS.md` ; `TESTS_EXECUTES.md` (commandes, sorties, versions, date), éventuellement captures d'écran **sanitisées** de l'interface et du rapport RJ.
6. `SECURITE_ET_EXPORT.md` : liste des fichiers exclus, confirmation de revue des secrets, mention si code contient encore des credentials cachés et EXPORT BLOQUÉ jusqu'à nettoyage.

## Procédure (ne pas envoyer automatiquement le ZIP ailleurs)
- Audit des fichiers et des secrets potentiels ; **ne pas copier `.env`, secrets, clés privées, tokens, mots de passe, bases utilisateur/client ou données personnelles**. Exemple `.env.example` sans valeurs.
- Un snapshot de code propre via dépôt Git excluant secrets; si besoin, créer un ZIP en local après expurgation. Inclure le PDF fictif `rj-1.pdf` pour test, pas des factures réelles sensibles.
- Ne pas diffuser sur repo public ni URL de partage ouvert par défaut ; l'utilisateur choisit explicitement ce qu'il transmet à ChatGPT.
- Pour les données de démonstration, conserver uniquement `examples/demo_2026_09` fictif. Une base réelle nécessite consentement + suppression exhaustive des données sensibles.
- Si la taille du projet est trop élevée, fournir `CODE_SOURCE_COMPLET.zip` plus `ANNEXES_SIMULATION.zip`, avec manifeste de partition ; ne pas omettre le code central sans expliquer.
- Toujours garder la version pré-modification et un `git diff`; NE PAS affirmer que ChatGPT a déjà reçu/analyse le projet avant que le maître d'ouvrage l'ait partagé.

## Message que Claude doit inclure dans son retour
« Voici l'ERP Transport après audit et éventuelles modifications. Les fichiers ci-joints représentent le code source complet expurgé des secrets, avec les migrations et les tests. Voici les fonctionnalités réellement vérifiées, les résultats de septembre 2026 et les anomalies restantes. Merci d'examiner la cohérence GA → analytique → reporting et les achats / stocks / paie / partenaires. »
