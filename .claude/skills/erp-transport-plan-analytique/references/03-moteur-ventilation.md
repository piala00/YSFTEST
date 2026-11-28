# 03 — Moteur d'imputation, ventilation et rapprochements

## Décision métier : source d'autorité et calendrier

`Evénement métier validé → pièce source → montant comptable/reconnaissance → fait analytique → affectation directe ou lot ventilé → projections/reporting`.

La date de vente, d'encaissement et d'exécution du transport sont distinctes : **la date du fait analytique suit la politique de reconnaissance retenue**, documentée par type d'opération. Ne pas transformer une réservation non payée en produit encaissé. Si recette différée à la réalisation du transport, prévoir un rattachement futur clair au voyage/véhicule concerné.

## Classification des coûts (avant toute ventilation)

1. `DIRECT_VOYAGE` : carburant d'une rotation, péage, indemnité de déplacement validée, coût de location sur ce voyage.
2. `DIRECT_VEHICULE_NON_VOYAGE` : réparation, assurance, contrôle technique, amortissement éventuel selon nature juridique et règles retenues.
3. `DIRECT_ACTIVITE` : commission de vente de billets, prestation de manutention de colis.
4. `SERVICE_AGENCE` : loyer guichet, salaire fixe des agents, énergie des bureaux.
5. `FRAIS_SIEGE` : direction, audit, SI, fonctions partagées.
6. `NON_EXPLOITATION` : éléments à isoler et ne pas absorber de manière arbitraire dans la marge de route.
7. `TRANSIT_STOCK/TRESORERIE` : avance, achat stock, paiement de facture, transfert de fonds ; ne pas transformer automatiquement en charge véhicule.

## Règle de priorité d'imputation

**A. Affectation explicite fiable** (`maintenance_order.vehicle_id`, `fuel_issue.vehicle_id`, `trip_id`, `shipment_leg.vehicle_id`) ;
**B. Dérivation contrôlée** (voyage → véhicule + ligne + gamme ; véhicule/date → partenaire/contrat ; billet → voyage/activité/gamme/canal) ;
**C. Clé de ventilation validée** pour coûts mutualisés ;
**D. Non affecté + alerte**, pas de section fictive pour masquer les cas indécidables.

Sur chaque affectation : `origin`, `derived_from`, `rule_id/version`, `date_effect`, `confidence` limité à un état vérifiable (AUTO_DIRECT / AUTO_RULE / MANUAL_APPROVED / UNASSIGNED), `approved_by` si manuel. Pas d'imputation par simple similarité de texte ou devinette sur une plaque.

## Clés de répartition autorisées selon la dépense

| Dépense commune | Base admissible | À éviter |
|---|---|---|
| Loyer de guichet | m², postes ou clé de gestion approuvée | au hasard 50/50 |
| Salaires administratifs | temps effectivement consacré ou clé budgétaire approuvée | partage automatique par nombre de billets sans justification |
| Entretien atelier commun | heures main-d'œuvre par véhicule, ordres validés | répartition par prix des billets |
| Frais communs des flottes | km réellement roulés, véhicule-km ou sièges-km pondérés | mélange Classique/VIP sans contrat/règle |
| Coût d'un voyage multiservices | coûts directement mesurés ou méthode poids/volume/passager-km | enregistrer le même coût entier sur billets ET colis |
| Revenu d'un colis multi-tronçons | part contractuelle, distance/poids-km ou barème explicite | revenu intégral sur chaque véhicule |
| Assurance annuelle véhicule | couverture temporelle (périodes), éventuellement km selon politique | imputée au seul voyage de paiement |

**Calcul** : `part_i = montant_source * base_i / somme(base_eligible)` ; arrondi en devise en unités minimales et reliquat attribué selon règle déterministe (plus grand reste, ordre stable), somme exacte = montant admissible. Si dénominateur nul → lot bloqué/non affecté, jamais division par zéro. Les pourcentages contractuels appliqués aux recettes se calculent séparément des clés de répartition comptables.

## Calculs de rentabilité (vues distinctes)

`marge_directe_voyage = produits_imputables - charges_directes_voyage`

`marge_vehicule = somme(produits_vehicule) - somme(charges_directes_vehicule) - coûts_non_voyage_vehicule`

`résultat_vehicule_apres_repartition = marge_vehicule - quote_part_charges_communes`

`résultat_gamme_CLASSIQUE = somme(produits et coûts affectés CLASSIQUE, après affectation des coûts communs)` ; idem VIP.

`résultat_agence_exploitation = produits et charges attribuables à agence - frais communs selon politique`, distinct de `ventes_de_agence_guichet`.

`solde_partenaire = solde_initial + droits_approuvés - paiements - avances/compensations_juridiquement_applicables ± régularisations` ; **pas** automatiquement égal à `résultat_vehicule_apres_repartition`.

Respecter une vue `DIRECT` et une vue `FULL_COST` ; les frais généraux ne doivent pas disparaître ni faire doubler les charges de groupe. Faire apparaître la valeur non ventilée.

## Concilier axes multiples et non double-comptage

Pour un billet de 12 000 FCFA : `ACT-PAX`, `GAM-VIP`, `VEH-0004`, `VOY-123`, `LIG-YDE-BTA`, `AGC-BTA`, `CAN-GUICHET`, `PRT-...` décrivent **une seule unité économique de 12 000**, pas huit ventes. Chaque rapport agrège les **facts/slices distincts** ; éviter `JOIN` avec multiplication de lignes dimensionnelles. Une vue par axe peut totaliser 12 000, mais deux vues **ne sont pas des sources à additionner**.

## Exemple de répartition contrôlée

Charge commune de 200 000 FCFA, kilomètres éligibles constatés BUS-C1 : 300 km, BUS-V1 : 200 km.
- BUS-C1 Classique : 200 000 × 300/500 = 120 000 FCFA.
- BUS-V1 VIP : 200 000 × 200/500 = 80 000 FCFA.
- Total dans comptabilité générale : 200 000 FCFA ; total alloué dans la vue de coûts complets : 200 000 FCFA ; **pas 400 000 FCFA**.

## Alerte sur les amortissements

Un véhicule propre à la compagnie peut porter amortissement (selon référentiel et durée validée). Un véhicule de partenaire ne doit pas recevoir automatiquement un amortissement comme si la compagnie en était propriétaire ; tenir compte de la substance économique, du contrat et du traitement comptable approprié.

## Contrôles de rapprochement

- Par compagnie / période / famille de comptes : montant général attribuable = analytique imputé + reliquat non imputé (pour chaque vue).
- Par activité : produits billets + produits colis + autres = produits opérationnels admissibles après annulations/avoirs selon méthode.
- Par voyage : billets validés vs produits reconnus, affectation colis transportés vs manifeste, carburant vs bons.
- Par véhicule : charges garage et carburant vs sources, contrats datés, gammes cohérentes.
- Par partenaire : décompte approuvé vs mouvements auxiliaires, paiements vs trésorerie.
- Par agences : les mêmes encaissements ne sont pas comptés une seconde fois via transfert de caisse.
- Pour une agence déconnectée : fraîcheur, statut « PROVISOIRE », dernière synchro ; clôture globale définitive bloquée si données obligatoires absentes.
