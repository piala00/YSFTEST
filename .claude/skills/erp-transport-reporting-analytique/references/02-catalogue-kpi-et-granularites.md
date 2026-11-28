# 02 — Catalogue des indicateurs (KPI) avec formules et grains

Chaque KPI doit déclarer : `metric_id`, libellé métier, unité, devise, base HT/TTC, grain minimal, date de référence, événements exclus/inclus, statut comptable, règle de ventilation, sens du montant, source, autorisations, version de calcul. Définir explicitement la population et les limites.

| Indicateur | Définition conseillée | Grain/source | Précautions |
|---|---|---|---|
| Produits transport passagers | Montants nets reconnus pour prestations de transport de passagers | écriture produit + trajet/voyage | ne pas assimiler automatiquement vente encaissée au produit réalisé ; annulations/avoirs |
| Produits bagages payants | Produits des suppléments bagages de voyageurs | opération bagage, écriture et véhicule | distinct colis indépendants |
| Produits messagerie | Produits colis pour prestations effectuées | expédition/tronçon, écriture | liaison au(x) véhicule(s) réellement transporteur(s), règles de partage explicites |
| Total produits analytiques véhicule | Somme des produits imputés éligibles | allocation/vehicle_id | exclusions et non-affectés affichés |
| Charges directes véhicule | Carburant consommé, péage, garage, pièces consommées, équipage directement attribuable | allocations GL par véhicule | facture d'achat stock ≠ consommation |
| Charges communes réparties | Ventilations de charges indirectes documentées | règle + version + allocations | clés justifiées, total distribué contrôlé |
| Résultat véhicule | Produits analytiques − charges directes − indirectes attribuées | véhicule, période | préciser avant/après amortissement et taxes selon paramétrage |
| Nombre de voyages | Départs réellement effectués, statut validé | voyage | éviter compter les reports/annulations |
| Places offertes | Somme capacités effectivement offertes sur le périmètre ; distinguer places/tronçons | voyage/tronçon | places par segment si départ intermédiaire |
| Places occupées | places vendues et embarquées selon définition choisie | billet-embarquement/tronçon | préciser vendu vs embarqué |
| Taux de remplissage | passagers-sièges-km / sièges-km offerts recommandé pour comparaisons multi-tronçons ; sinon nombre occupé/places offertes sur tronçon homogène | voyage/tronçon | zéro au dénominateur → non applicable |
| Prix moyen passager | produit passagers / unités passagers définies | voyage/tronçon | préciser voyageurs-voyages vs segments |
| Coût au km | charges véhicules éligibles / kilomètres vérifiés | véhicule, période | km=0 → non applicable ; charges fixes/mobiles explicités |
| Marge / taux de marge | résultat / produits du périmètre | véhicule/activité | si produits 0, N/A ; ne pas confondre pourcentage de variation |
| Recettes encaissées | mouvements réels de trésorerie externes, par caisse/mode de paiement | mouvement caisse/banque | pas assimilées automatiquement aux ventes/prestations |
| Montant dû partenaire | solde contractuel calculé depuis événements droits + corrections - retenues - paiements | contrat + compte auxiliaire | ne se confond jamais avec résultat véhicule |

### Calculs des comparaisons

- `écart_absolu = valeur_période_B - valeur_période_A`.
- `%_évolution = écart_absolu / abs(valeur_période_A) × 100` uniquement si référence non nulle et comparaison économiquement interprétable ; sinon `N/A`.
- Moyenne pondérée pour tarifs, coûts unitaires et taux ; **ne jamais additionner des taux** ou faire la moyenne simple de taux issus de volumes différents.
- Pour marges et taux de remplissage, proposer en priorité un écart en **points de pourcentage** et, si pertinent, une évolution relative séparée.
- Comparer les mêmes devises ; conversion documentée si multi-pays/devises. Franc CFA XAF applicable au Cameroun, ne pas fusionner automatiquement avec XOF.
- Montrer toujours périmètre, statut provisoire/définitif, date de dernière mise à jour et référence des formules.

### Distinction critique des grains

Un billet est un fait de vente, un contrôle d'embarquement est un événement, un voyage est une exécution, et une écriture est un fait comptable. Les tables peuvent être liées, mais **une jointure directe billet × billet_scans × ledger_lines multipliera les montants**. Agréger par fait/identifiant pertinent en premier, puis joindre dimensions 1:1 ou tables-ponts contrôlées.
