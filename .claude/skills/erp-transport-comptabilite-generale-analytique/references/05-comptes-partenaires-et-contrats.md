# 05 — Propriétaires : historique, contrats, règlement et rapprochement

## Deux niveaux indissociables

1. **Compte d'exploitation analytique du véhicule** : produits affectés - charges affectées, avec clés et limites explicites.
2. **Compte financier du partenaire** : droits contractuels, factures/commissions, fonds collectés pour lui, avances, retenues autorisées, paiements et solde ; lié au sous-livre auxiliaire de comptabilité générale.

## Contrats datés obligatoires

Pour chaque véhicule : identité propriétaire ; date de début/fin ; nature de convention (partage CA, partage résultat défini, location/forfait, commission), pourcentage/forfait et assiette ; taxes et frais ; qui supporte carburant, péages, garage, assurances, équipage, dépenses centrales ; fréquences de règlement ; conditions d'annulation/correction ; rôle de la compagnie (principal ou mandataire) ; version des dispositions et approbation.

Ne pas déterminer le contrat applicable à un voyage ancien en lisant uniquement `vehicle.current_owner_id`. Les ventes futures affectées à un véhicule avant changement de propriétaire doivent être résolues à la date de prestation ou selon stipulation contractuelle explicite.

## Processus partenaire

1. Voyage clôturé et pièces contrôlées ; recettes/charges à jour pour ce véhicule.
2. Appliquer la **base de calcul contractuelle** (exemples : brut éligible, net de remboursements, net de catégories de charges). Calculer commissions/forfaits/partage et produire détail traçable.
3. Présenter un **décompte brouillon** ; comptable/gestionnaire valide.
4. Enregistrer la dette ou le solde partenaire selon les schémas comptables configurés et validés ; éviter toute comptabilisation de produit/dette en double.
5. Rapprocher avances, retenues, règlements effectifs par caisse/banque/Mobile Money.
6. Délivrer relevé période + historique du contrat + sous-totaux par véhicule ; verrouiller décompte validé, corriger par ajustement/reversement tracé.

## Exemples chiffrés PURE MISE EN SCÈNE

- Bus B-21 produit 1 000 000 FCFA, charges analytiques 400 000, résultat analytique 600 000.
- Convention A : le propriétaire perçoit 70 % d'une base contractuelle définie de 500 000 → droit brut 350 000, sous réserve de contrôles et taxes ; n'est pas égale aux 600 000 de résultat.
- Avance autorisée 100 000 déjà accordée, règlement ultérieur 200 000 → solde sur ce seul décompte de 50 000, à combiner avec les autres écritures du compte.

Ces montants ne sont PAS une règle standard de partage et ne suffisent pas à déterminer les écritures légales : examiner si la compagnie agit en son nom et pour son compte ou au nom/pour le compte du partenaire ; faire valider le traitement OHADA.

## Changement de propriétaire / plusieurs véhicules

- Propriétaire A possède B-01 et B-02 à la même période, puis cède B-02 au propriétaire B le 1er mois suivant. Un rapport historique couvre les périodes correspondantes, sans attribuer rétroactivement B-02 à B.
- Charges de garage engagées après la cession : responsabilité contractuelle du nouveau ou ancien propriétaire à déterminer selon la prestation et les clauses ; ne pas déduire automatiquement du propriétaire actuel.
- Partenaire avec contrat cessé conserve consultation de ses relevés passés autorisés, mais pas des résultats du nouveau propriétaire.
- Compagnie propriétaire de ses propres véhicules : agrégation possible dans "Véhicules de la compagnie", sans créer artificiellement une dette fournisseur/partenaire.

## Absences de données

Contrat manquant, source non synchronisée, frais non justifiés ou pourcentage inconnu → marquer « à régulariser », **ne pas calculer une dette définitive**. Produire état d'exception à valider, conserver estimation provisoire le cas échéant.
