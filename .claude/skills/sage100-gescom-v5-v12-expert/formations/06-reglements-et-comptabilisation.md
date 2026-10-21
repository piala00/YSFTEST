# Traitement — Échéances, encours, règlements et transfert comptable

Sources : S1, S7, S12 ; `references/05-menu-traitement.md` et `references/04-menu-structure.md`.

## Comprendre les distinctions

- **Facture** : créance ou dette documentée, pas preuve d'encaissement.
- **Échéance** : date(s) prévue(s) de règlement ; une facture peut avoir plusieurs échéances.
- **Règlement** : encaissement ou décaissement, à rapprocher de la bonne pièce/échéance.
- **Acompte** : règlement en amont/partiel suivant conditions.
- **Encours** : indicateur dépendant des critères et du dossier, distinct du seul montant échus.
- **Comptabilisation** : transmission aux écritures comptables selon paramétrage et validation.

## Atelier 6.1 — Vente à crédit et règlement partiel

1. Facture fictive TTC de 150 000 FCFA avec règlement à 30 jours ; vérifier sa date et son échéancier.
2. Avant règlement : relever solde de la facture, total client, part échue/non échue selon date.
3. Enregistrer un règlement partiel fictif de 50 000 FCFA en mode de règlement autorisé.
4. Contrôler la pièce visée, le montant imputé, le solde restant ; ne pas assimiler encaissement à mouvement de stock.
5. Éditer un relevé d'échéance et comparer avant/après : solde attendu de 100 000 FCFA **si aucune autre pièce/condition n'intervient**.
6. Faire un second règlement sur le solde, vérifier état soldé et tracabilité.

## Atelier 6.2 — Crédits et solvabilité

1. Réglage dans fiche client/solvabilité et paramètres tiers/logistique.
2. Créer un client à encours maximum fictif 200 000 FCFA.
3. Comparer comportement lors d'une nouvelle commande/livraison lorsque le total dépasse le plafond.
4. Préciser si le dossier avertit, bloque ou continue ; rattacher au code risque et aux règles activées.
5. Tester avec un profil vendeur et un profil autorisé : vérifier droits.

## Atelier 6.3 — Comptabilisation contrôlée

1. Identifier configuration dans `Fichier > Paramètres société > Comptabilisation`.
2. Examiner journal, catégories comptables, comptes et taxes.
3. Vérifier qu'une facture de test répond aux conditions de **validation** requises ; Sage S7 rappelle que certaines versions imposent une validation avant transfert.
4. Prévisualiser journaux/états en vue d'identifier les pièces concernées.
5. Exécuter uniquement dans base de test et si dispositif Sage Comptabilité présent ; observer dates, numéros et écriture résultante.
6. Rechercher les rejets/avertissements et corriger par l'application, jamais par écriture SQL directe dans tables Sage.

## Avoirs et rapprochement

Une **facture d'avoir** n'est pas automatiquement un règlement. Le cas Sage S12 expose l'utilisation de la notion de « bon d'achat » ou l'imputation à des échéances spécifiques. Ne pas traiter cela comme universel : préciser états, méthode, règles de caisse et taxes applicables.

## Checklist de diagnostic des créances

Client/compte correct ? Périmètre des agences et sociétés ? Date de référence ? Factures comptabilisées ou pas ? Échéances ? Avoirs ? Règlements affectés ou non ? Solde antérieur ? Multidevises ? Écritures d'ouverture ? Statut facture ? Filtrage par représentant ? Droits ?

Ne jamais conclure qu'un « recouvrement à 0 % » est réel avant d'avoir comparé numérateur, dénominateur, fenêtre temporelle, pièces et imputations.
