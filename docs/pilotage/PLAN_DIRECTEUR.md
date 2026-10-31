# Plan directeur — registre initial du 31 octobre 2026

Pilotage : [issue #24](https://github.com/piala00/YSFTEST/issues/24). Coordination historique : [issue #1](https://github.com/piala00/YSFTEST/issues/1). Codex prépare les lots et les PR ; Claude assure la revue croisée demandée, sans présumer qu’elle est déjà faite.

Les urgences H-005/H-006/H-008/H-009 et Q-001 restent prioritaires. La réconciliation documentaire avance sans les interrompre. Les autres demandes restent conservées dans le registre ; une nouvelle demande non urgente ne remplace pas la tâche active.

Consigne confirmée par le propriétaire le 31/10 : organiser les tâches depuis GitHub et poursuivre les développements,
corrections, tests et PR sans confirmation courante (Q-003, DEC-010). Les limites de production restent celles de DEC-001.
Après la qualification fictive des P0 #23/#25, la personnalisation réelle reste bloquée ; le lot indépendant Documents
#27/#28 poursuit D-002/Q-001. Les résultats du tableau d'avancement fixent le prochain point de reprise.

## Sources et portée

Sources consultées : conversation du propriétaire (dates individuelles non conservées), AGENTS.md, issues #1/#10/#18/#24, métadonnées des PR et rapports existants de docs/retour/. Le programme de travail du 30 octobre est réutilisé, pas remplacé. Ce registre initial n’est **pas encore un inventaire exhaustif prouvé** des demandes antérieures externes ni une réconciliation finale de toutes les transmissions antérieures. Toute omission identifiée doit recevoir un ID sans effacer l’historique.

## Lecture des statuts

Une demande reçue n’est pas une spécification validée. « PR en revue » signifie code proposé, sans fusion ni acceptation utilisateur. Les preuves CI/Windows ont leur propre SHA et leur périmètre. Aucun champ accepté/fusionné n’est déduit d’un succès CI. Priorités P1/P2 du registre : classement provisoire sauf décision source explicite.

## Ordre de travail

1. Fermer techniquement les P0 actifs par correctifs, essais et limites explicites ; personnalisation réelle encore bloquée sans identité publique existante.
2. Réconcilier les exigences et dépendances, faire relire les contradictions sans réauditer les défauts déjà corrigés.
3. Préparer l’intégration progressive après autorisation distincte, sans supprimer les lots empilés.
4. Reprendre uniquement les écarts des lots 03 Reporting, 04 tests P0 et 05 menus. Sources, mappings et matrices déjà livrés sont réutilisés.
5. Poursuivre SN/SMT, métier Transport, échanges, simulation, recette et distribution selon dépendances. Les sources fiscales officielles et décisions comptables précèdent leurs règles codées.

Chaque lot indique : exigences couvertes, responsable, dépendances, critères, tests exécutés, anomalies, limites et décisions nécessaires. Aucune promesse de travail continu hors session sans exécuteur configuré.

## Documents associés

[Exigences](REGISTRE_EXIGENCES.md) · [PR et dépendances](MATRICE_PR_DEPENDANCES.md) · [Décisions](JOURNAL_DECISIONS.md) · [Avancement](TABLEAU_AVANCEMENT.md) · [Anomalies](REGISTRE_ANOMALIES.md).
