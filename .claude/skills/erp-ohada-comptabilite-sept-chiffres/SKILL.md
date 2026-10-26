---
name: erp-ohada-comptabilite-sept-chiffres
description: "Appliquer ou auditer dans un ERP OHADA Django + client Windows une numérotation des comptes à sept chiffres et deux modules visibles, Comptabilité générale et Comptabilité analytique, sans doubler la comptabilité. Utiliser pour les versions Commercial, Transport et Mixte."
---

# ERP OHADA — sept chiffres / deux modules comptables

## Mission

Lorsqu'on me demande d'appliquer les décisions de l'utilisateur à son ERP, **je vérifie d'abord le dépôt réel**, puis j'effectue un changement limité et testable. Ne pas reconstruire un ERP à partir de cette archive : le Skill décrit des exigences et contient le patch des modifications entre les deux archives Windows reçues le 26/10/2026.

**Règles prioritaires** :

1. Chaque compte d'entreprise utilise **exactement 7 chiffres** dans les nouveaux dossiers et les dossiers existants une fois convertis et validés, par complétion par des zéros **à droite** (exemple : `4111` → `4111000`). Ne pas modifier les intitulés, soldes, écritures ni pièces.
2. Écran d'accueil **deux modules distincts** : `Comptabilité générale` et `Comptabilité analytique`. Deux entrées UX et permissions, **une seule comptabilité financière**, une seule base de pièces et d'écritures.
3. Analytique commerciale : sections et ventilation analytique ; analytique transport : deux **rubriques principales de restitution** `Véhicules` et `Propriétaires de véhicules`. Les autres axes servent à l'affectation et aux filtres.
4. Aucune imputation double. Les produits et charges analytiques proviennent des **écritures comptables générales validées**, pas d'un deuxième grand-livre financier. Le résultat économique du véhicule est distinct du solde financier dû au propriétaire.
5. Ne jamais convertir un dossier sans sauvegarde vérifiée, simulation, contrôle des collisions, fenêtre de maintenance et validation explicite. Refuser une conversion incompatible ; jamais fusionner automatiquement deux comptes.
6. Toute interface web et toute interface Windows doivent afficher les modules pertinents conformément aux droits et à l'activité. Vérifier les API et la navigation ; ne pas laisser une simple tuile sans écran réel.
7. Les modifications déjà présentes dans le projet sont conservées. Ne pas écraser de changements récents pour forcer le patch ; produire un diff réconcilié.

## Comment utiliser ce Skill

- Lire `references/REGLES_METIER.md` pour la décision fonctionnelle.
- Lire `references/ETAT_DU_CODE_ET_LIMITES.md` pour identifier ce qui préexistait et le périmètre exact du correctif.
- Lire `references/PROCEDURE_TECHNIQUE.md` pour une intégration sûre et les migrations.
- Lire `references/TESTS_ACCEPTATION.md` pour des tests fonctionnels, comptables et de sécurité.
- **Optionnel** : `references/PATCH_CODE_COMMERCE.patch` est un patch précis des fichiers Django/Windows par rapport à l'archive d'origine. **Ne l'appliquer que si son pré-contrôle réussit** et que le dépôt correspond à la version de référence.
- `references/NOTE_CORRECTIF_ORIGINAL.txt` est la note incluse dans l'archive modifiée ; le fichier du code n'est pas requis pour lire ce Skill.
- Lire `references/INCONNUES.md` avant de déclarer une fonctionnalité achevée.

## Processus attendu de Claude

1. Explorer la structure du dépôt GitHub (ou copie locale), **sans demander ni exposer de secrets**. Identifier les applications Django `apps/core`, `apps/comptabilite`, `apps/transport`, les clients `desktop/` et leurs variantes.
2. Comparer la version actuelle aux exigences et au patch ; identifier les éléments déjà présents. Distinguer les deux ERP si ce sont deux dépôts séparés.
3. Appliquer le plus petit correctif compatible. Préserver les migrations et la cohérence du modèle. Vérifier les codes d'activités (`COMMERCE`, `TRANSPORT`, `MIXTE`), les droits et l'aiguillage des URLs.
4. Produire tests automatisés et parcours de validation, puis les exécuter quand l'environnement le permet. Ne pas inventer un résultat de test.
5. Avant production : simuler la conversion de comptes sur une **copie** de base et communiquer les collisions et conséquences. Aucune modification de base réelle sans décision explicite de l'utilisateur.
6. Livrer un résumé des fichiers touchés, ce qui fonctionne / reste non vérifié, commandes à lancer, et une stratégie de retour arrière.

## Limites

Ce ZIP est **un Skill de transfert de connaissances et un patch**, pas le logiciel complet, pas une base de données et pas une version déployée. Son patch concerne l'archive `ERP-OHADA-Commerce-Windows.zip`, qui contient déjà du code transport ; il ne prouve pas l'état d'un éventuel dépôt ERP Transport autonome. Une archive compressée ne fournit pas de connexion à Render ou GitHub.

Sources : comparaison locale des deux archives fournies dans cette conversation ; décision métier de l'utilisateur. **Aucune validation réglementaire du plan SYSCOHADA complet n'est revendiquée.**
