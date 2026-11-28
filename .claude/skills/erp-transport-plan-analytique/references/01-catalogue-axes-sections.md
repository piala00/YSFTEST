# 01 — Plans, sections et classifications métier

## Terminologie

- **Plan/axe analytique** : dimension d'observation (véhicule, agence, activité, etc.).
- **Section** : membre d'un plan (VEH/BUS-0007, GAM/VIP, AGC/BERTOUA).
- **Centre de coût** : unité à laquelle rattacher une charge ; pas obligatoirement un plan distinct. Les services, ateliers et flotte peuvent être centres de coût.
- **Centre de profit** : unité dont les produits et charges permettent de calculer une marge (voyage, véhicule, gamme, ligne, agence d'exploitation).
- **Clé de répartition** : règle documentée de partage d'une charge commune, avec base, bénéficiaires, dates, arrondis et justification.
- **Compte comptable général** : nature OHADA de l'opération ; **indépendant** de la section analytique.

## Catalogue initial (10 plans)

| Code plan | Libellé | Sections initiales / format | Quand remplir |
|---|---|---|---|
| AGC | Agence | AGC-YDE, AGC-DLA, AGC-BTA, AGC-GBL... | toute opération agence ; conserver `agency_sales_id` et `agency_operating_id` comme rôles distincts |
| VEH | Véhicule | VEH-0001, VEH-0002 ; immatriculation comme attribut, pas clé pérenne | tout voyage, frais directs et réparations |
| PRT | Partenaire | PRT-0001, PRT-0002 ; société/particulier ; `not_applicable` pour véhicule propre selon rapports | opérations affectables au contrat partenaire à date |
| DEP | Département | DEP-BIL, DEP-COL, DEP-EXP, DEP-GAR, DEP-STO, DEP-RH, DEP-CPT, DEP-DIR, DEP-TRE | production et consommation de ressources |
| ACT | Activité | ACT-PAX, ACT-COL, ACT-LOC, ACT-AFF, ACT-AUT | produit métier et charges directes attribuables |
| GAM | Gamme | GAM-CLASSIQUE, GAM-VIP, hors champ pour charges non pertinentes | transport de personnes/ressources partagées de flotte |
| LIG | Ligne | LIG-YDE-BTA, LIG-BTA-GBL (codes indicatifs) | voyages et leurs coûts |
| VOY | Voyage/départ | VOY-2026-... (identifiant stable et unique) | billets sur voyage réel, carburant, équipage, colis par étape |
| CTR | Contrat exploitation | CTR-00001/version datée ; groupe contrat | propriétaire/partenaire et modes de rémunération |
| CAN | Canal vente | CAN-GUICHET, CAN-WEB, CAN-APP, CAN-REVENDEUR | réservations, ventes et remises/commissions liées au canal |

**Règle de codification** : la clé technique est un UUID/ID immuable. Le code affiché est unique dans le contexte de compagnie et de plan ; jamais réutilisé après archivage. Éviter de stocker les noms de villes et plaques comme identifiants primaires. Lier chaque section à `tenant_id`, `legal_entity_id` si applicable, dates d'effet, état actif/inactif, parent optionnel, et historique d'audit.

## Distinction des rôles d'agence

Exemple : le guichet de Douala vend un billet pour un départ exploité par Yaoundé. Enregistrer sans écrasement :

- `selling_agency_id = DOUALA` : productivité guichet, encaissement et contrôle caisse ;
- `operating_agency_id = YAOUNDE` : exploitation économique / marge d'agence, selon schéma validé ;
- `trip_id`, `vehicle_id`, `route_id`, `fare_class` : compte du transport et rentabilité ;
- un unique document commercial/source et une unique reconnaissance de produit.

Le tableau « CA par agence vendeuse » et « CA par agence exploitante » sont **deux regroupements différents** d'un même ensemble de faits ; ne jamais additionner ces deux tableaux entre eux.

## CLASSIQUE / VIP — règle ferme et testable

1. `vehicle_fare_class_assignment`: `vehicle_id`, `fare_class` (CLASSIQUE ou VIP), `valid_from`, `valid_to`, `approved_by`, `reason`.
2. Pas de chevauchement entre deux affectations de gamme incompatibles pour le même véhicule. Historique impératif, même si le paramétrage initial interdit tout changement.
3. `trip.fare_class` obligatoire pour voyage passagers ; `trip_vehicle_assignment` doit confirmer la même gamme sur tout l'intervalle du voyage.
4. `fare_table` indexée au minimum par `origin_stop`, `destination_stop`, `fare_class`, dates d'effet, devise, version tarifaire et autorisations/remises ; ne pas supposer un prix fixe par axe.
5. Aucun billet CLASSIQUE vendu sur un `trip` VIP ni inversement, même hors ligne et lors d'un report. Recontrôle au moment d'émettre/embarquer.
6. Les dépenses directes d'un véhicule héritent de sa gamme **à la date d'effet de la dépense**. Une réparation postérieure à un changement de gamme suit une politique claire, pas un simple rattachement à la gamme courante sans vérification.
7. Les coûts de siège, de garage collectif, de personnel partagé peuvent être imputés à Classique et VIP via une clé documentée. Ne pas ventiler une facture de véhicule CLASSIQUE vers VIP sans motif exceptionnel.

## Activité « colis » vs gamme du bus

Un colis chargé à bord d'un bus VIP reste une recette `ACT-COL`, et non une vente `ACT-PAX`/GAM-VIP. Deux lectures possibles, distinctes :
- résultat `ACT-COL` par compagnie/agence ;
- contribution colis à la rentabilité du véhicule VIP qui l'a effectivement transporté.

S'il passe par plusieurs véhicules, créer un `shipment_leg` pour chaque étape et ventiler selon la politique de marge (distance, prix de l'étape, poids-km ou barème), **sans multiplier les revenus de l'expédition**.

## Compléments à ne pas confondre avec de nouveaux plans

Employés/équipages, fournisseurs, clients, numéro de caisse, modalités de paiement, dépôt de pièces, réparateur, compteur kilométrique, justificatifs et centres géographiques sont des attributs utiles. Ajouter comme **dimensions analytiques facultatives** seulement si un vrai besoin de ventilation indépendante est identifié.
