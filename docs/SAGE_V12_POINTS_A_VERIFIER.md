# Sage 100 Gestion commerciale V12 : ce qui reste à vérifier sur une installation réelle

Référence : skill `sage-100-gescom-v12-ui` (installé dans `.claude/skills/`), découpage officiel V12.10.
La matrice détaillée est dans `docs/AUDIT_SAGE_V12_GESCOM.md`. Pour la régénérer :

```bash
python manage.py audit_navigation --sortie docs/AUDIT_SAGE_V12_GESCOM.md
```

## Ce qui est établi

| Élément | Niveau de preuve | Dans l'ERP |
|---|---|---|
| Menus Fichier, Structure, Traitement, Etat, Fenêtre et leurs entrées | **DOC-V12** (découpage V12.10) | Repris dans le même ordre, avec les mêmes libellés |
| Types de documents des ventes, des achats et des stocks | **DOC-V12** | 9 + 9 + 3 types réalisés ; dépréciation et fabrication grisées |
| Menu Édition (Annuler, Couper, Copier, Coller…) | **ERG-CLASSIQUE** | Repris de l'ergonomie classique ; **non détaillé** par la V12.10 |
| Menu ? (aide) | **ERG-CLASSIQUE** | Seulement « À propos » : le découpage ne le détaille pas |
| Barre d'outils sous les menus | **INDICATIF** | Icônes choisies pour l'ERP, à aligner sur la V12 réelle |
| « Tous les documents… », accès aux autres logiciels, variation de stock | **AJOUT-ERP** | Propres à l'ERP OHADA |

## Captures nécessaires pour une reproduction fidèle

Le découpage V12.10 liste des **fonctions**, pas les écrans. Il faut donc des captures pour :

1. **Les 7 menus déroulés** : Fichier, Édition, Structure, Traitement, État, Fenêtre et ?. Cela permet de confirmer l'ordre, les séparateurs, les libellés exacts et les raccourcis clavier affichés.
2. **La barre d'outils et la barre verticale** : icônes, ordre et regroupements.
3. **Les fiches**, avec une capture par onglet réellement visible :
   - Structure › Clients : la matrice cite les rubriques Identification, Tarifs, Adresses/Banques, Champs libres, Solvabilité, Agenda et Paramètres, mais ce ne sont **pas forcément des onglets** ;
   - Structure › Articles : Identification, Tarifs, Descriptif, Champs libres, Paramètres, Logistique, Dépôt, Comptabilité ;
   - Structure › Fournisseurs et Structure › Dépôts de stockage.
4. **Un document de vente ouvert**, par exemple une facture : zones d'en-tête, colonnes des lignes, pied (totaux, acomptes) et boutons (Transformer, Valider, Actions…).
5. **Un document de stock**, par exemple un mouvement de transfert : en-tête, dépôt d'origine et de destination, colonnes.
6. **Les fenêtres de critères des états** : période, tri, sélection, sortie.
7. **Édition dans quatre contextes** : fenêtre principale vide, liste des clients, fiche article et facture ouverte. Pour chaque contexte, relever les commandes actives et grisées.

Pour chaque capture, noter la **version exacte** (? › À propos), l'**édition** (Essentials, Standard ou Premium), les **options** (Logistique, Fabrication, Services, Traçabilité, Gamme) et les **droits** de l'utilisateur.

## Précautions retenues

- L'interface de l'ERP est une **reproduction fonctionnelle**, pas une copie officielle de Sage au pixel près.
- Les mentions de facturation électronique (Sage Connect, Sage eFacture, Factures électroniques) proviennent de la matrice Sage **France**. Elles ne signifient pas que ces obligations s'appliquent au Cameroun ou dans l'espace OHADA. Ces entrées restent grisées.
- Les commandes Fichier › Outils (purge, réorganisation, réinitialisation…) modifient massivement les données. Elles ne sont pas développées et devront demander une confirmation explicite.
