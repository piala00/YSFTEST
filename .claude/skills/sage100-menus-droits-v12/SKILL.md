---
name: sage100-menus-droits-v12
description: Vérifier les menus, droits et comportements d’interface d’un ERP inspiré de Sage 100 V12 à partir de sources tracées, en distinguant faits documentaires, repères historiques et inconnues.
---

# Sage 100 — Menus et droits : lot 1, livraison documentaire partielle

Édition du 21 octobre 2026, révision 0.1. Traiter R1 à R4 uniquement. Ne pas déclencher les lots fiscalité, écrans métiers ou SQL.

## Utilisation

1. Lire `references/ETAT_DE_COUVERTURE.md` avant toute modification de code.
2. Consulter `references/SOURCES.csv` et vérifier la version portée par chaque source.
3. Utiliser `MENUS_COMPTABILITE.csv` et `MENUS_GESCOM_COMPLEMENT.csv` comme relevés ciblés, jamais comme une arborescence exhaustive prête à importer.
4. Lire `AUTORISATIONS.md`, `NIVEAUX_DROITS.csv`, `DROITS_PARTICULIERS.csv` et `ESPACE_DE_TRAVAIL.md` selon le changement envisagé.
5. Examiner `INCONNUES.csv` ; laisser une information inconnue ouverte. Ne jamais la convertir en fait par analogie avec Windows, Sage 50, Sage X3 ou une ancienne version de Sage 100.
6. Consulter `REPERES_HISTORIQUES.csv` uniquement pour orienter la vérification d’une installation V12.
7. Utiliser `PROTOCOLE_VERIFICATION_V12.md` pour compléter les preuves manquantes.

## Conventions et limites

- CSV UTF-8, séparateur point-virgule, en-tête unique.
- `preuve=DOC-OFFICIEL` signifie que Sage publie la source ; cela ne certifie ni une version V12 non mentionnée ni un emplacement écran non observé.
- `ordre` reste vide lorsque le rang dans le menu réel n’est pas établi. L’ordre des lignes suit le relevé documentaire sélectionné ; il ne comble pas les commandes omises.
- `niveau` décrit le chemin documentaire présenté, pas une profondeur de droits universellement certifiée.
- `edition=A-CONFIRMER` signifie que la disponibilité par édition n’est pas relevée. Ne pas interpréter cette valeur comme « toutes éditions ». La matrice officielle doit être consultée pour une décision de licence.
- Aucun séparateur ni raccourci non prouvé n’est ajouté. Une absence de ligne ne signifie pas absence de fonction.
- Les deux CSV de menus contiennent des références de versions différentes explicitement étiquetées. Exclure les lignes non V12 d’un import exigeant V12.
- Ne pas transférer automatiquement un onglet ou un champ de paramètres en sous-menu de la barre de menus.
- Aucune observation de l’ERP de démonstration ne prouve le comportement de Sage.
- Cette livraison est partielle. Ne pas annoncer R1-R4 terminées ni conformité ou équivalence de l’ERP avec Sage.

## Fichiers complémentaires

Lire `ETAT_DE_COUVERTURE.md` pour les acquis et limites, `PROTOCOLE_VERIFICATION_V12.md` pour les preuves attendues. Les fichiers SOURCES et INCONNUES constituent la traçabilité obligatoire. Conserver les URL officielles ; les PDF complets ne sont pas redistribués dans ce paquet.
