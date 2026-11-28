# 03 — Colis, messagerie et expéditions inter-agences

## Services, postes et droits

Service expédition, agence départ, quai/chargement, équipage, agence arrivée, agent remise, caisse et supervision. Chaque service modifie uniquement les étapes qui lui appartiennent. Une agence destinataire ne peut pas changer rétroactivement les recettes originelles d'un colis expédié ailleurs.

## Référentiels et documents

- Expéditeur, destinataire, contacts, agences de départ/destination, identité du déposant et personne habilitée à retirer.
- Nature de marchandise, nombre de colis, poids, volume, catégorie de fragilité, valeur déclarée, emballage, photos autorisées, conditions de prise en charge, tarif, assurance et responsabilité selon contrat/droit.
- Expédition `shipment_id` globale ; unités `parcel_id` ; code QR/étiquette, référence unique, bordereau/lettre de voiture si applicable, paiement/facture.
- Étapes `shipment_leg` / `parcel_load` rattachées à chaque `trip_id` et `vehicle_id` réellement utilisés, manifestes de chargement/déchargement et agents signataires.

## Workflow étagé

1. **Dépôt** : créer expédition, calculer tarif et éventuelles assurances/options, enregistrer la preuve de réception, émission d'étiquette ; facturer avec décision explicite sur exigibilité/paiement.
2. **Préparation** : contrôle dimensions et catégories, tri par itinéraire et agence, mise en attente.
3. **Chargement** : scanner chaque unité ; rattacher au véhicule et voyage effectifs ; manifeste de quai ; validation du chef de quai/équipage.
4. **Transport** : départ, transit par agence intermédiaire (si nécessaire), changement de véhicule sous chaîne de custody.
5. **Réception** : scan des colis attendus, enregistrer écarts, manquants, avaries ; accepter la prise en charge de garde par agence.
6. **Remise** : contrôle de l'identité/autorisations du destinataire, signature ou OTP si configuré, preuve de livraison horodatée, statut final.
7. **Incident** : perte, avarie, refus, colis abandonné, réexpédition, retour, réclamation, indemnisation documentée.

## États

`ENREGISTRÉ`, `ACCEPTÉ`, `EN_ATTENTE`, `CHARGÉ`, `EN_TRANSIT`, `EN_TRANSFERT`, `ARRIVÉ`, `PRÊT_À_RETIRER`, `REMIS`, `RETOUR`, `LITIGE`, `PERDU`. Chaque transition de garde nécessite acteur et preuve. Prévoir événements tardifs et ordonnancement de réception : une agence peut recevoir physiquement un colis avant que la création initiale ne soit synchronisée ; prévoir rapprochement par identifiant sans inventer une seconde expédition.

## Finances et rattachement véhicules

Distinguer `agency_of_sale`, `agency_of_receipt`, `trip_leg.vehicle`, `agency_of_delivery`, débiteur, propriétaire économique de la vente. En cas de transport par V1 puis V2, appliquer une **règle de ventilation explicite** (par distance, tarif de tronçon, forfait, commission, autre), versionnée et approuvée ; ne pas attribuer toute la recette à V1 par facilité. Frais de garde, livraison, assurance et indemnisation représentent des composantes séparées.

La prestation facturée n'est pas forcément immédiatement encaissée. Séparer vente, créance, règlement, espèces confiées, contre-remboursement collecté pour tiers et reversement au bénéficiaire. Gestion des écarts de contre-remboursement et réclamations avec contrôle renforcé.

## Sécurité et conformité

Prendre en compte l'Acte uniforme OHADA relatif aux contrats de transport de marchandises par route **dans son champ d'application**, notamment lettre de voiture, responsabilité, livraison et contentieux. Vérifier exclusions, conditions nationales, marchandises interdites/réglementées, délais de conservation et politiques de données. Ne pas présumer que tout « colis » est automatiquement soumis au même régime ; solliciter validation juridique.

## Reporting

Nombre et valeur des expéditions par agence et destination, encaissements, colis transportés par véhicule/voyage, délais de transit, avaries, remises, litiges, paiements COD, colis non récupérés. Rapports comparant charge théorique des manifestes et scans de réception réels.

## Tests

Deux scan de chargement identiques, déchargement non déclaré, lien V1→V2, arrivage avant synchronisation départ, livraison double, destinataire non autorisé, colis parti hors manifestes, facturation à crédit, contre-remboursement, perte et compensation.
