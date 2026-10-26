# 04 — Périodes, états comparatifs et performances

## Sélecteur temporel universel
- Jour exact, intervalle de jours, semaine, mois libre, trimestre, semestre, exercice, année, période glissante 3/6/12 mois, N et N−1.
- Dates personnalisées sans modifier l'exercice global ; chacun des écrans conserve ses filtres, dates et société dans l'état d'interface, sans les imposer aux autres fenêtres.
- Comparer P1/P2 (durées identiques ou afficher l'avertissement si différentes), P année précédente, variation absolue et %, moyennes/jour, par départ, par passager, par kilomètre. Ne pas diviser par zéro.
- Saison, calendrier des jours ouvrés, jours fériés si pertinents ; ne pas prétendre comparer des mois de 28 et 31 jours à durée égale sans normalisation.
- Prendre en charge soldes à date versus flux entre dates. Un solde de caisse au 31 mars n'est pas la somme des soldes de janvier/février/mars.

## Indicateurs du reporting direction
Billetterie, colis, bagages, taux remplissage, coût/km, coût/voyage, marge, variations mensuelles, comparaison gares, Classement véhicules Classique/VIP, rentabilité par ligne, partenaire, contrat, canal de vente, dépenses garage, péages, stocks et paie.

## Navigation proposée
`Reporting → Vue direction / Comptabilité générale / Analyses des 10 plans / Comparatifs / Tendances / États et impressions / Contrôles qualité des données`.

Chaque indicateur : titre, période, société/agences, source et statut. Clic sur chiffre → section → compte analytique → ligne GL → pièce d'origine (permission contrôlée).

## Consolidation sans doublons
Un billet peut être encaissé le 5 et transporté le 8 ; afficher séparément `CA gagné à date de prestation` et `encaissement caisse à date règlement`. En multi-agences distinguer `agence vendeuse` et `agence du départ` ; colis affectés au véhicule transporteur réel. Transferts internes non comptés comme produits. Les propriétaires ne sont pas confondus avec les fournisseurs.

## Qualité des données
Ne jamais masquer une agence non synchronisée ; afficher `N agences reçues / N attendues` et horodatages. Refuser les comparaisons trompeuses de périodes incomplètes sans alerte visible.
