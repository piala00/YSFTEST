# 02 — Parcours des services métier

## Billetterie (Classique/VIP)

1. Réservation/émission d'un billet : enregistrer dans le système opérationnel, avec montant, remise, statut, véhicule/voyage/tronçon, catégorie Classique/VIP, agence de vente/exploitation et caisse.
2. Déterminer le **fait générateur comptable** en fonction des règles SYSCOHADA et des paramètres commerciaux : vente avant voyage, prestation effectuée, avoir, annulation, remboursement, etc. Éviter de confondre réservation, facturation, transport réalisé et règlement.
3. Produire dans **Comptabilité générale** une écriture équilibrée, avec provenance billet/document et anti-doublon.
4. Après validation GL, répartir les lignes de produits éligibles sur voyage, véhicule, gamme, agence ; rapporter le montant seulement une fois.
5. Une annulation ou un remboursement provoque les écritures générales appropriées et, après validation, leurs incidences analytiques.

## Courrier/colis/bagages payants

Document de transport, destination, dépôt, véhicule effectivement transporteur, recette et mode de paiement → règle de comptabilisation dans GL → affectation du produit validé au véhicule ayant exécuté la prestation, avec prise en charge des expéditions multi-véhicules selon répartition justifiée. Ne pas dupliquer les montants à chaque relais/scan de colis.

## Garage et achats de pièces

- Commande et réception en stock : suivre stock et écritures correspondantes en générale ; l'achat de stock **n'est pas automatiquement une charge analytique d'un bus**.
- Sortie/consommation pour réparer BUS-004 : opération garage → écriture générale de consommation ou charge selon méthode comptable → analytique BUS-004 après posting.
- Réparation facturée directement pour BUS-004 : écriture générale de charge/dette ou règlement → affectation analytique (pas une deuxième dépense).
- Dépenses à immobiliser : traiter en générale comme immobilisation ; ne pas les transformer en charge d'exploitation immédiate. Les amortissements comptabilisés pourront être affectés selon politique.

## Exploitation, carburant et équipages

Carburant acheté mais non utilisé ≠ carburant consommé. Selon le circuit retenu, consommation imputée après mouvement et écriture de générale correspondante. Péage justifié/mandaté = règle de posting de dépense. Avance au chauffeur = mouvement de tiers/trésorerie, pas charge définitive ; le décompte de frais génère les charges GL validées.

## RH/Paie

Bulletin validé → génération/validation des charges sociales et salariales en GL → ventilation analytique vers équipage/voyage/véhicule/service selon feuille de temps ou barème documenté. Paiement du salaire = extinction de dette/banque/caisse, pas nouvelle charge.

## Caisses multi-agences

Petite agence : caisse commune ; siège/grande agence : caisses de billetterie, courrier, garage, centrale. Une opération de vente et son paiement peuvent relever de services et de caisses différents. Les transferts internes : GL mouvements de trésorerie le cas échéant, mais **aucun nouveau produit ni coût analytique**.

## Propriétaire de véhicule

Résultat véhicule calculé sur écritures GL imputées au véhicule. Calcul contractuel de droit du propriétaire : simulation/échéancier jusqu'à ce que les écritures de rémunération ou dette applicables soient validées dans GL. Relevé financier du propriétaire : droits/dettes et règlements **issus des comptes auxiliaires généraux**, distinct des résultats de gestion.
