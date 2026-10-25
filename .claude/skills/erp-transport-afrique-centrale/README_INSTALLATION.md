# Skill Claude Code — ERP Transport Afrique Centrale

## À quoi sert ce dossier ?

Il donne à Claude Code un référentiel complet pour développer progressivement un ERP multi-agences et multi-services : billetterie/booking, colis, garages, véhicules et voyages, personnel et paie, partenaires propriétaires, comptabilité OHADA, caisse, reporting, synchro locale/siège.

Le fichier `SKILL.md` est volontairement court ; les spécifications métier détaillées sont rangées sous `references/`, afin que Claude charge seulement les parties concernées.

## Installation dans votre projet Claude Code existant

1. Faites d'abord une sauvegarde de votre dépôt de code.
2. Décompressez **cette archive à la racine du projet**, là où se trouve normalement votre `README` ou votre `CLAUDE.md`. Si le dossier `.claude` existe déjà, fusionnez les dossiers (sans supprimer les autres skills).
3. Vérifiez la présence de ce fichier :

   `.claude/skills/erp-transport-afrique-centrale/SKILL.md`

4. Ouvrez Claude Code depuis la racine du projet.
5. Dans Claude Code, utilisez :

   `/erp-transport-afrique-centrale`

   Puis demandez : « Commence par auditer le projet actuel, sans modifier le code. Compare ce qui existe avec les référentiels du skill, puis propose un plan de développement par étapes pour que chaque service alimente automatiquement les rapports d'agence, la comptabilité, les comptes de véhicules et le siège. »

## Installation globale facultative

Copiez uniquement le dossier `erp-transport-afrique-centrale` (avec ses `references`) dans :

`~/.claude/skills/erp-transport-afrique-centrale/`

Cette installation rend le skill accessible dans d'autres projets ; l'installation par projet reste préférable pour garder ce référentiel lié au bon dépôt.

## Limites / précautions

- Ce package est un **Skill de conception et développement** ; ce n'est pas encore l'application exécutable.
- Il n'a pas audité votre dépôt de code puisque le projet source n'a pas été fourni ici.
- Les schémas comptables, règles fiscales, calculs de paie et paramètres nationaux doivent être validés par des professionnels habilités avant usage réel.
- Le fonctionnement offline exige un serveur local, un LAN et une alimentation de secours quand l'électricité fait défaut.
- Le mode multi-agences hors ligne impose des quotas de sièges/autorités exclusives pour éviter les doubles réservations.
