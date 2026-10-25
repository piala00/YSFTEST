# 06 — Véhicules appartenant aux partenaires : contrats, comptes et relevés

## Concepts impératifs

1. **Propriétaire juridique** d'un véhicule à une date donnée.
2. **Compagnie exploitante** du véhicule pendant une période ; elle peut ne pas être propriétaire.
3. **Contrat partenaire** détermine le partage des revenus, commission, frais supportés, garanties, responsabilités, avances, retenues et calendrier des paiements.
4. **Compte analytique véhicule** = recettes et coûts d'exploitation attribués à l'actif, quelle que soit la personne qui a encaissé.
5. **Décompte contractuel** = créance/obligation théorique due au partenaire après application des règles du contrat.
6. **Compte auxiliaire partenaire** = mouvements de facturation, dettes/créances, retenues, acomptes et règlements selon le modèle juridique/comptable validé.

**Ne jamais présenter la marge du véhicule comme le « solde bancaire du propriétaire ».**

## Contrats versionnés

Données : `contract_id`, `partner_id`, `vehicle_id`, société exploitante, agence de rattachement, début/fin, condition d'effet, modèle économique, base de calcul, pourcentage/montant fixe, barème des dépenses déductibles, propriétaire des pneus/réparations/carburant/assurance, limites, périodicité, garanties, clause de litige, autorité d'approbation, documents signés. Tout avenant produit une nouvelle version datée, jamais un écrasement du contrat historique.

**Modèles paramétrables** : (a) commission de gestion prélevée sur recettes éligibles ; (b) partage du produit net/marge contractuelle ; (c) forfait ou location ; (d) affrètement/prestation transporteur. La nature du contrat détermine si l'exploitant est principal ou mandataire dans la comptabilité et dans l'assiette des revenus ; validation nécessaire.

## Cycle de décompte

1. Délimiter période et liste des voyages/charges éligibles du véhicule.
2. Reconstituer par source traçable billets, segments, colis, autres prestations, annulations et remboursements.
3. Déduire dépenses imputables selon clauses et pièces validées : carburant, garage, péages, chauffeur, commission, assurance, etc.
4. Calculer les droits et retenues contractuelles : assiette, taux, dates et montant ; **geler l'extrait avec version des règles**.
5. Soumettre au gestionnaire partenaires et au comptable selon droits ; présenter les contestations possibles.
6. Comptabiliser uniquement selon le schéma juridique et SYSCOHADA approuvés (principal/agent) ; enregistrer dette/créance auxiliaire et éventuels impôts/retenues.
7. Émettre relevé partenaire par véhicule et relevé consolidé de ses véhicules.
8. Paiements partiels/totaux et avances : mouvements distincts, rapprochement, solde restant dû, historique des justificatifs.
9. En cas de correction tardive, générer une **régularisation au décompte suivant** ou une note de rectification ; ne pas modifier un décompte signé en silence.

## Vue portail partenaire

Page d'accueil : liste de ses véhicules, derniers voyages, montant à recevoir ou à régulariser, avances, paiements, incidents, relevés téléchargeables. Drill-down véhicule → voyage → ventes/colis/dépenses avec anonymisation nécessaire des données passagers et des salariés. Pas d'accès aux informations des autres partenaires ni au plan de rémunération de l'équipe.

## Exemple calculable (simulation non réglementaire)

Pour un véhicule V-101, période M : recettes éligibles 1 200 000 FCFA ; commission de gestion à 15 % de ces recettes = 180 000 FCFA ; frais contractuellement supportés par le propriétaire 400 000 FCFA ; montant théorique avant avances et paiements = 620 000 FCFA. À titre d'illustration si une avance de 100 000 FCFA a déjà été versée et est juridiquement imputable, solde théorique de règlement = 520 000 FCFA. Les chiffres ne constituent ni un bilan comptable légal ni une règle obligatoire de partage.

## Contrôles essentiels

- Véhicule à deux contrats chevauchants incompatibles : refus ou résolution d'avenants contrôlée.
- Mutation propriétaire le 15 du mois : rémunération selon dates de service/contrats applicables, pas selon propriétaire actuel.
- Pièce garage imputée à V-101 mais frais supporté par la compagnie : reste dans analytique véhicule, **pas** automatiquement déductible du décompte partenaire.
- Billet encaissé dans une autre agence : reste attribuable à l'exploitation du véhicule correct sans enregistrer un deuxième encaissement.
- Paiement partenaire partiel : n'altère pas résultat d'exploitation déjà calculé.
- Colis avec plusieurs véhicules : appliquer règle de ventilation documentée.

## Sorties

Relevé grand livre auxiliaire par partenaire ; état des commissions ; résultat par véhicule ; décompte de période ; solde initial/mouvements/solde final ; historique de règlements ; balance auxiliaire de partenaires ; montants en litige ; états signés/exportables PDF/XLSX.
