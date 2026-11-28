# Scénarios de qualification ERP / Sage

**Tous les cas doivent s'exécuter sur une copie/société fictive.** Relever paramètres de départ, écritures, stocks et traces attendues, puis comparer avant/après.

| ID | Scénario | Contrôles essentiels |
|---|---|---|
| C01 | Création client → facture commerciale → transfert comptable | Pièce créée, catégorie de TVA, journal, compte tiers, équilibre, doublons |
| C02 | Bon commande → livraison → facture | Transformations autorisées, quantités cumulées, état de livraison, impact stock |
| C03 | Retour client → avoir | Traçabilité des pièces, réintégration stock conditionnelle, avoir et règlements |
| C04 | Achat → réception → facture fournisseur | Entrée stock, valorisation, engagement fournisseur, lettrage selon paramétrage |
| C05 | Dépôt A → dépôt B | Sortie/entrée cohérentes, transit, neutralité stock global, historique |
| C06 | Saisie inventaire → régularisation | Écarts, droits et validation, horodatage, imputation analytique éventuelle |
| C07 | Paiement partiel → échéances → lettrage | Soldes, pénalités/rappels éventuels, lettrage partiel/manuel/auto |
| C08 | Annulation facture ou inversion | États autorisés, conservation des liens, compta et stock, audit |
| C09 | Modification article/tiers/tarif | Effet sur pièces historiques, futur calcul et éditions |
| C10 | Analytique multi-agences | Imputation, consolidation sans double-compte, devise, exercice |
| C11 | BI : revenus / marges / recouvrement | Sources, granularité, calcul par document, doublons, rapprochement Sage |
| C12 | Écriture via Objets Métiers | Prévalidation, droits, rollback, idempotence, événements, erreurs HRESULT |
| C13 | Migration V5→V12 | Diff schéma, paramètre, fonction supprimée, résultat comptable et stock |
| C14 | X3 dictionnaire → fiche écran | Code fenêtre, onglet, champ, action et table référencée, code activité |
| C15 | Gestion des droits | Bouton visible vs interdit, consultation vs saisie, audit permissions |

**Critère de réussite** : constat d'exécution + preuve source + absence d'anomalie métier + contrôle comptable/stock adéquat. Ne pas déclarer une opération identique entre versions sans test.
