# Journal du lot 03 — contrôles HTML, premier échantillon

Le préremplissage de la matrice a été étendu de **453 à 515 lignes** (62 nouvelles occurrences statiques), à partir des sources suivantes :
- `templates/commercial/document_detail.html` : 21 balises interactives détectées.
- `templates/comptabilite/ecriture_detail.html` : 7.
- `templates/transport/billet_detail.html` : 8.
- `templates/base.html` : 26.

**Méthode** : détection textuelle des balises HTML `button`, `a`, et `input` de type submit/button/reset. Ce n'est **pas** un décompte exhaustif ni un inventaire des seuls boutons métier : des liens de navigation sont inclus, des composants multilignes ou JS peuvent être omis, et les libellés internes aux balises ne sont pas encore extraits. Le contexte des conditions Django n'est pas résolu. Les 515 lignes peuvent inclure des doublons de fonctionnalités entre menus et templates.

## Prochain lot exécutable par Claude

1. Remplacer l'extraction regex par un extracteur vérifié (AST pour `navigation.py`, analyseur HTML et JS), avec tests unitaires de l'extracteur.
2. Parcourir **tous** les `templates/**/*.html` et scripts JS, sans se limiter aux quatre écrans de ce lot ; identifier les formulaires, événements JS, contrôles dynamiques et menus contextuels.
3. Relier les commandes aux URL Django, vues, services, permissions, méthodes HTTP, états de documents et effets métier.
4. Produire des parcours de recette sur données de démonstration pour chaque rôle/agence et statut. Pour chaque anomalie prouvée, fournir reproduction, capture, test et correctif en PR séparée.
5. Ne jamais classer conforme à Sage 100 V12 sans source officielle ou preuve d'installation, édition et version exactes.
6. Publier un bilan par module distinguant commandes statiques, contrôles rendus, fonctions testées, écarts prouvés et exceptions approuvées.

**Aucune action en production, aucun merge, aucun déploiement.**
