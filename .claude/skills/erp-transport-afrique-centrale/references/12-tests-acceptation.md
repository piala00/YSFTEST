# 12 — Critères d'acceptation / tests end-to-end interservices

## Principes d'essai

Créer des fixtures isolées, migrations testables, horloge simulée et deux serveurs agences + siège + contrôleur d'embarquement. Observer **les effets métier et comptables**, pas uniquement le succès HTTP. Un test ne valide pas la conformité légale par lui-même. Équilibrer somme des écritures, stock, cash, droits contrats, synchro et logs.

## Scénario de référence : journée multi-services sur V-101

Préparer : société A, agences Bertoua/Douala, service billets/colis/garage/RH/caisse/comptabilité, véhicule V-101 appartenant au partenaire P-9 sous contrat effectif, équipage C-1, voyage T-1, plan de sièges, quotas hors ligne.

| Étape | Opération testée | Résultat attendu |
|---|---|---|
| 1 | Exploitation programme T-1 sur V-101 | voyage actif, autres services voient T-1, pas de produit |
| 2 | Billetterie vend 10 billets payés à Bertoua | 10 billets, 10 capacités allouées, reçus, mouvements caisse, événement par action, pas de doublon |
| 3 | Guichet B vend une place sur le même tronçon | soit place distincte attribuée à B, soit refus ; jamais double siège incompatible |
| 4 | Colis saisit 5 expéditions, en charge 3 sur T-1 | 5 ventes commerciales selon statut, 3 unités attribuées physiquement à V-101 |
| 5 | Carburant délivre 60 litres et pièce justificative | coût par V-101 et éventuellement T-1, fournisseur/caisse cohérent, pas deux décaissements |
| 6 | Garage consomme une pièce pour V-101 | stock diminue une seule fois, charge analytique de V-101, traçabilité OR |
| 7 | Comptable règle facture garage | trésorerie diminue, dette apurée, charge **non doublée** |
| 8 | RH valide paie chauffeur et avance de mission | salaire dû et avance mission distincts, accès RH restreints |
| 9 | Contrôleur embarque 9 billets puis tente double scan | 9 scans autorisés, 1 non-présenté, 2e scan refusé, aucune seconde recette |
| 10 | Chauffeur déclare péages puis restitue fonds non utilisés | avance soldée avec justification, dépenses attribuées sans double charge |
| 11 | Exploitation clôture T-1 | voyage lisible avec recettes et coûts, pièces justificatives, anomalies signalées |
| 12 | Gestionnaire émet décompte P-9 | contrat historique appliqué, droits distincts de rentabilité du véhicule |
| 13 | Caisse paie partiellement P-9 | solde à payer diminué, profit véhicule inchangé |
| 14 | Agence coupe son WAN pendant les étapes 1–12 | tous services locaux autorisés continuent via LAN ; site central se dit incomplet |
| 15 | La connexion revient et mêmes événements sont envoyés 3 fois | application idempotente : un seul billet, mouvement caisse, posting et charge |
| 16 | Siège génère le rapport de V-101 et d'agence | correspond aux documents sources ; exact après sync, fraîcheur exposée |

## Scénarios de sécurité et concurrence

- Un vendeur tente de visualiser paies ou contrats partenaires via une URL/API directe → refus.
- Un partenaire connecté tente d'appeler le relevé du voisin avec un autre `partner_id` → refus et audit.
- Deux agents font simultanément la même vente de siège/tronçon → une transaction seule réussit.
- Un scanner compromis présente un QR modifié → signature invalide, refus.
- Deux contrôleurs sur le même LAN scannent simultanément le même billet → une seule validation.
- Un caissier ferme une session sans justifier un écart → fermeture en état `à approuver` selon politique ; audit.
- Une paie validée est rééditée depuis un écran → correction documentée, jamais UPDATE silencieux.
- Une opération issue de `tenant B` est injectée avec `tenant A` → erreur d'authenticité/périmètre.

## Scénarios synchronisation

Perte d'ACK ; envoi désordonné ; paquet dupliqué ; dépendance colis absente temporairement ; conflit d'avenant de contrat ; horloge agence fausse ; réouverture après crash ; sauvegarde locale restaurée plus ancienne ; service comptable central indisponible ; reprise sur backlog volumineux. Mesurer exactement les pertes, doublons et écarts, puis exiger **zéro doublon financier accepté**.

## Cas particuliers de financement / analytique

Un billet encaissé par l'agence A sur voyage parti de B doit créditer le bon responsable de caisse et le bon véhicule d'exploitation, sans assimiler CA de l'agence et produit attribué au véhicule. Un véhicule change de propriétaire en milieu de période ; un colis voyage avec deux véhicules ; un mécanicien répare simultanément deux véhicules ; un équipement acheté devient une immobilisation, pas charge immédiate par défaut ; un paiement différé ne crée aucun flux de caisse avant son règlement.

## Checklist d'une fonctionnalité « terminée »

- [ ] Métier : commande et statuts documentés, validations réelles.
- [ ] Sécurité : RBAC + scope agence/société/partenaire, tests négatifs.
- [ ] Transactions : idempotence, contraintes, intégrité, audit.
- [ ] Interservices : événement fiable, projections conformes, messages de rattrapage.
- [ ] Comptabilité : règle validée et écriture équilibrée, rapprochement.
- [ ] Analytique : affectations exactes et transparence des coûts non ventilés.
- [ ] Hors ligne : test LAN isolé puis reconnexion.
- [ ] UX : formulaires, erreurs compréhensibles, recherche, impression, rôles.
- [ ] Reporting : agence, véhicule, voyage, siège mis à jour et source explicable.
- [ ] Migration : upgrade réversible documenté, sauvegarde et reprise.
- [ ] Exploitation : monitoring, sauvegardes, documentation opérationnelle.
