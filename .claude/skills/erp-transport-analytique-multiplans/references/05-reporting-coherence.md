# Reporting = exploitation des états et du même moteur

## Une seule source des agrégats financiers

Ne PAS récupérer les chiffres en « lisant » les HTML, PDF ou CSV des états. Les comptes analytiques et le reporting doivent appeler un service commun `analytique_agreger` et des vues dérivées des écritures GL validées. Les filtres doivent partager la même sémantique : `date_du, date_au, plan, section(s), société, site/role, gamme, véhicule, propriétaire_historique, statut`.

## Rapports

- Évolution par jour/semaine/mois/année des produits, charges, résultats, marge, et comparatifs période N/N−1.
- Comparaisons entre agences/gares, véhicules, gammes, activités, itinéraires, propriétaires et contrats.
- Performance parc : recettes de billets, colis, bagages, coûts carburant, réparations, coût kilométrique, remplissage, résultat par véhicule/gamme (calculs des ratios en utilisant les données opérationnelles réellement disponibles).
- Pilotage partenaires : véhicules par propriétaire, rentabilité du portefeuille, rémunérations fixes/variables, retraits, paiements et restes dus — sans confondre résultat et dette.
- Écarts imputés/non affectés, indicateurs de fraîcheur de données par agence, statut de clôture; comparaisons empêchant un rang erroné sur données non synchronisées.
- Supporter impression et exports avec en-tête plan, période, filtres, source et date dernière synchronisation.

## Garde-fous

- Une ligne GL comptabilisée une fois au total société; vue par axe ne multiplie pas la comptabilité.
- Le rapprochement se calcule **par plan**. Si plan non exhaustif, sa somme ne doit pas être présentée comme le résultat société.
- Pas de « profit » d'agence gonflé par un virement de caisse ni par recette de billet vendu le mois précédent.
- Opérations en attente de comptabilisation peuvent être affichées dans une vue opérationnelle **provisoire** explicitement séparée du reporting comptable validé.
- Comptes tiers fournisseurs séparés des partenaires propriétaires même pour une même personne physique.
