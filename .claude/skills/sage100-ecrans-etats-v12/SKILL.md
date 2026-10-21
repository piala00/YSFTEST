---
name: sage100-ecrans-etats-v12
description: Vérifier les champs, onglets, transformations et états Sage 100 avant de concevoir des écrans d’ERP, en séparant les preuves V12.20, les aides sans version et les témoins historiques.
---

# Sage 100 — écrans, transformations et états

Traiter R9 à R11 du cahier ERP OHADA du 21 octobre 2026. Livraison documentaire partielle, version 0.1. Ne pas présenter ce paquet comme une reproduction exhaustive des écrans V12.

## Lire dans cet ordre

1. Lire `references/LECTURE_ET_LIMITES.md`, `COUVERTURE.csv`, `SOURCES.csv` et `INCONNUES.csv`.
2. Charger `ECRANS_GESCOM.csv` ou `ECRANS_COMPTABILITE.csv` **avec** `STATUT_CHAMPS.csv`. Utiliser `ONGLETS.csv` pour les onglets et `FONCTIONS_ECRANS.csv` pour les boutons ; ne pas mélanger champs et fonctions.
3. Lire `TRANSFORMATIONS.csv` **avec** `STATUT_TRANSFORMATIONS.csv`, puis `PROCESSUS_V12.csv` et `TRANSFORMATIONS_ET_CONTROLES.md`.
4. Lire `ETATS_STANDARDS.csv` **avec** `STATUT_ETATS.csv`. Une variante d’état n’est pas une colonne imprimée.
5. Consulter `COMPORTEMENTS.csv` pour les règles de saisie et `CAS_DE_REVUE.csv` pour préparer une vérification fonctionnelle. Ces cas sont proposés, pas exécutés sur un Sage V12.
6. Consulter `FORMAT_IMPORT_V5_TEMOIN.csv` seulement pour un ancien format V5 explicitement identifié. Ne jamais le convertir en schéma d’écran V12.

## Appliquer les limites

- Préserver les douze colonnes des catalogues d’écrans et les six colonnes de transformations, en UTF-8 et CSV point-virgule.
- Interpréter un ordre vide comme inconnu. Ne pas attribuer des rangs d’écran à partir de l’ordre narratif d’une page.
- Traiter NON_ETABLI comme une question ouverte, jamais comme Non, facultatif, illimité, zéro ou valeur vide.
- Distinguer origine officielle, précision de version et précision de chaque cellule. DOC-OFFICIEL ne certifie pas à lui seul V12, l’édition, les longueurs ou les valeurs par défaut.
- Garder les termes narratifs comme repères de recherche ; ne pas les traiter comme des libellés d’écran exacts tant que STATUT_CHAMPS ne les confirme pas.
- Ne pas déduire tous les champs d’une fiche à partir de la structure SQL, d’un format d’import ou d’une autre gamme Sage (50, FRP 1000, X3).
- OUI_SOUS_CONDITIONS confirme une possibilité dans sa portée. NON_FONCTION_UI décrit l’absence du bouton documentée. INCONNU n’interdit ni n’autorise une transformation. Exiger une décision explicite du moteur pour ces cas.
- Ne pas modifier l’ERP, les données Sage ou leurs documents à partir de ce catalogue seul. Livrer les éléments établis et les questions à résoudre.
- Ne pas commencer R12/R13, SQL ou hébergement sans nouvelle instruction.
