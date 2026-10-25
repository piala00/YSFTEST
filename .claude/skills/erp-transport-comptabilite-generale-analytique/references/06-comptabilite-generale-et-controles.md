# 06 — Comptabilité générale, rapprochements et normes

## Objet

Comptabilité générale par entité juridique, multi-agences, avec un plan comptable SYSCOHADA révisé configuré et validé pour la juridiction applicable, journaux, tiers, pièces, écritures équilibrées, situations et états de synthèse, déclaration/suivi fiscal selon modules disponibles. Aucune fonction analytique ne remplace les états légaux.

## Règles de comptabilisation

- Chaque mouvement financier/journal de vente/achat/paye provient d'un document et d'un événement identifié.
- Une opération validée ne peut pas être supprimée silencieusement ; correction par avoir/contrepassation/écriture d'ajustement datée selon procédure.
- Journal débité/crédité en équilibre, date, période, devise, numéro de pièce, origine, acteur, version règle, validation.
- Écritures en attente ou brouillon révisables par personnes habilitées ; clôture empêche modification rétroactive.
- Enregistrement de CA/produit dépend de réalisation et de rôle principal/agent. Une réservation n'est pas un produit, une avance du passager n'est pas nécessairement du chiffre d'affaires réalisé. Paramétrer les schémas et les faire valider.
- Le niveau société agrège journaux et sous-livres de toutes les agences **sans compter deux fois** les transferts de fonds ou les reventilations.

## Rapprochements systématiques

- GL recettes passagers/colis/bagages contre sous-livres métiers, avec distinction date de vente/prestation/caisse.
- Comptes de tiers contre auxiliaires et règlements réels.
- Caisses d'agence : solde ouverture + encaissements espèces - décaissements espèces +/- transferts = solde théorique ; rapprochement solde compté, erreurs et écarts justifiés.
- Banque/Mobile Money : flux externes vs rapprochement bancaire ou relevés opérateurs, distincts des espèces.
- Stock pièces : entrées factures ≠ consommation garage ; stock vs inventaire et coût de sortie.
- Paie : salaires et cotisations dus vs paiements ; ventilations RH vers véhicules qui ont réellement bénéficié des prestations.
- Partenaires : règlement/avance/commission vs compte auxiliaire du propriétaire ; comparer à décompte approuvé.
- GL vs analytiques : rapprocher **uniquement le périmètre éligible aux véhicules** (ne pas imposer montant de bilan société = compte d'exploitation parc).

## Plans, journaux, nomenclatures

Conserver paramétrage des comptes, journaux, exercices, périodes, taux ou régimes par pays sans inventer chiffres réglementaires. Comptes symboliques d'exemple : `PRODUITS_TRANSPORT`, `PRODUITS_BAGAGES`, `PRODUITS_MESSAGERIE`, `CHARGES_GARAGE`, `CHARGES_CARBURANT`, `DETTES_TIERS`, `COMPTE_CAISSE`, `BANQUE`, `CHARGES_RH`. Ne pas forcer les comptes d'immobilisations/stock vers charges.

## Gestion des différences temporelles

- La caisse indique **quand l'argent a été reçu/sorti**.
- Le voyage indique **quand le service de transport a été exécuté**.
- L'écriture comptable indique **quand la reconnaissance est autorisée** selon la méthode retenue.
- Le rapprochement explicite toute différence de période et de synchronisation.

## Responsabilité et conformité

Le développeur applique des schémas configurables et traçables ; un professionnel qualifié valide plan comptable, règles fiscales, traitements des contrats propriétaires, immobilisations et rémunérations. Une société multi-agences = centralisation par établissement ; plusieurs sociétés distinctes = consolidation légale éventuelle selon règles applicables, hors simple somme de caisses.
