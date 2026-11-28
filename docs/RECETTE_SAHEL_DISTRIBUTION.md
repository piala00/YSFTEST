# Cahier de recette SAHEL DISTRIBUTION

Source : skill `sage-100-gescom-v12-formateur-expert` (installé dans `.claude/skills/`), fichiers
`exercices/01-societe-fictive.md` et `exercices/02-cas-pratiques-corriges.md`, plus les ateliers 2.2, 5.4 et 6.2.
Données entièrement fictives.

- **Rejouer la recette :** `python manage.py test apps.commercial.tests_recette`
- **Faire les exercices à la main dans l'ERP :** sur une base vierge, `python manage.py init_erp --sahel --admin <mot_de_passe>`

## Société fictive chargée

- **Dépôts :** DPT-PRINCIPAL, DPT-BOUTIQUE, DPT-BOISSONS, DPT-TRANSIT.
- **Familles :** BOISSONS, ALIMENTAIRE, SERVICES.
- **Articles :** JUS-001, EAU-001, RIZ-025, et TRANS-001 (prestation sans stock).
- **Catégories tarifaires :** GROS et DÉTAIL, avec les prix de l'exercice (JUS-001 à 1 200 / 1 500, EAU-001 à 350 / 450, RIZ-025 à 15 500 / 16 000).
- **Clients :**
  - CLI-GROS-01 : catégorie GROS, crédit 30 jours, plafond 300 000 ;
  - CLI-DETAIL-01 : catégorie DÉTAIL, comptant ;
  - CLI-ENC-01 : plafond 100 000, code risque « blocage ».
- **Fournisseurs :** FOU-BOIS-01 et FOU-ALIM-01, fournisseurs principaux des articles.
- **Stocks initiaux :** saisis par des **mouvements d'entrée**, comme le demande le formateur, jamais en écrivant la quantité dans la fiche.

## Résultats

| Cas | Mission du formateur | Preuve vérifiée par la recette | Résultat |
|---|---|---|---|
| 01 | Comparer Structure › Articles dans deux profils | Non automatisable : droits par profil non développés | À faire |
| 02 | Retrouver souches, taxes, règlements | Non automatisable : consultation | À faire |
| 03 | Créer JUS-001 dans BOISSONS | Famille, suivi de stock, compte 701, CMUP alimenté par les entrées | ✅ |
| 04 | Catégories GROS / DÉTAIL | Devis à 1 200 (GROS) et 1 500 (DÉTAIL) ; source du prix tracée (« catégorie tarifaire Gros », « fiche article ») | ✅ |
| 05 | Entrer 100 JUS-001 au dépôt principal | Stock +100, un mouvement, aucune écriture comptable | ✅ |
| 06 | Transfert de 25 du principal vers la boutique | Principal −25, boutique +25, total inchangé, aucune facture | ✅ |
| 07 | Devis → BC → BL → facture (10 unités) | Stock relevé à chaque étape : 100, 100, **90**, 90. Seul le BL mouvemente ; la créance naît de la facture | ✅ |
| 08 | Livrer 6 sur une commande de 10 | Reliquat 4, commande « partiellement transformée » | ✅ |
| 09 | Commande 30, réception 20, facture | Commande sans effet sur le stock, réception +20, reliquat 10, facture de 20 sans double entrée, dette fournisseur | ✅ |
| 10 | Inventaire : théorique 75, compté 73 | Écart −2, mouvement de sortie tracé avec le n° d'inventaire | ✅ |
| 11 | Facture de 150 000, encaissement de 50 000 | Reste 100 000, solde client 100 000, stock inchangé ; second règlement : facture soldée | ✅ |
| 12 | Dépasser le plafond d'encours | « Blocage » : validation refusée, pièce restée en brouillon. « Avertissement » : validée et signalée. Devis non contrôlés | ✅ |
| 13 | Retour de 2 unités et avoir | Bon de retour : +2 en stock sans effet financier. Facture de retour : créance réduite sans double entrée. Facture d'avoir : créance réduite, stock inchangé. Un avoir n'est pas un règlement | ✅ |
| 14 | Concilier un état de vente avec 3 pièces | CA = 2 factures − 1 avoir = 18 600 ; le devis et la facture en brouillon sont exclus ; palmarès par client identique | ✅ |
| 15 | Checklist de sauvegarde et de clôture | Non automatisable : procédure, **aucune clôture réelle** | À faire |
| Atelier 5.4 | Réapprovisionnement mini/maxi par dépôt | Seul le dépôt sous son mini est proposé (60 − 20 = 40) ; bon de commande en brouillon chez le fournisseur principal ; article sans fournisseur signalé | ✅ |

## Fonctions ajoutées à l'ERP à l'occasion de cette recette

| Fonction Sage (skill formateur) | Dans l'ERP |
|---|---|
| Catégories tarifaires (atelier 2.2, cas 04) | Fichier › Paramètres société › Tiers › Catégories tarifaires ; fiche client ; tarifs par catégorie dans la fiche article ; prix proposé en saisie, avec sa source |
| Code risque et plafond d'encours (atelier 6.2, cas 12) | Fiche client : « pas de contrôle », « avertissement » ou « blocage », appliqué à la validation des commandes, préparations, BL et factures |
| Seuils mini/maxi par dépôt et réapprovisionnement (atelier 5.4) | Fiche article › Stock et seuils par dépôt, fournisseur principal ; Traitement › Gestion des besoins génère les bons de commande en brouillon |

## Ce que la recette ne prouve pas

Comme le rappelle le skill, ces tests montrent que **l'ERP** respecte les règles métier des corrigés. Ils ne prouvent pas que ses écrans sont identiques à ceux de Sage 100 V12 : pour cela, il faut des captures de votre installation (voir `docs/SAGE_V12_POINTS_A_VERIFIER.md`).
