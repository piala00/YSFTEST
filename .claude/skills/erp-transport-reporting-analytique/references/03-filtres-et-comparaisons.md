# 03 — Filtres, comparaisons, périodes

## Filtres

- Société (tenant), agences de vente/exploitation, toutes ou sélection multiple ; Classique/VIP ; véhicule(s) ; propriétaire(s) **au moment du fait** ; voyages, lignes, activités, service source, contrat, période, statut comptable, qualité/fraîcheur.
- Restriction d'accès avant agrégation : la direction voit sa société, un responsable d'agence ses agences autorisées, un partenaire uniquement ses véhicules et ses écritures contractuelles.
- Option `groupe par`: agence, véhicule, propriétaire, gamme, ligne, mois, trimestre, exercice. La navigation Comptabilité analytique demeure véhicules/propriétaires ; les groupes supplémentaires sont propres à Reporting.

## Périodes

- Journée civil locale (Africa/Douala pour agences au Cameroun, pays/config pour expansion), semaine ISO paramétrable, mois, trimestre, exercice fiscal, intervalle libre ; dates affichées et bornes inclusives utilisateur, bornes SQL demi-ouvertes `[start,end)`.
- Deux périodes A/B : mois précédent, même mois N-1, période libre A/B, trimestre comparatif, cumul annuel, évolution séquentielle, 12 derniers mois.
- Ne pas mélanger `sold_at`, `departed_at`, `recognized_at`, `paid_at` : pour un même KPI, déclarer et imposer une règle de période claire.
- Comparaisons de mois partiels contre mois complets : avertissement et option de période comparable, afficher jours couverts.
- Pour changement de propriétaire, contrat ou catégorie de véhicule, attribuer les faits avec historiques à date d'effet et exposer l'effet de périmètre.

## Cas obligatoires

1. Comparer chiffre d'affaires passagers classique vs VIP entre N et N-1 à la même agence exploitante.
2. Comparer coût/km des véhicules 001 à 020 entre deux trimestres ; filtrer véhicules sans kilomètres utilisables.
3. Comparer résultat de l'agence de Yaoundé et Bertoua en séparant agence de vente et exploitation.
4. Comparer revenu d'un propriétaire avant/après acquisition d'un deuxième véhicule ; distinguer croissance organique et changement de périmètre.
5. Forcer le statut **provisoire** dès qu'une agence concernée ne s'est pas synchronisée ou qu'une clôture requise est manquante.
6. Imprimer un rapport comparatif avec les filtres appliqués dans son en-tête et les sources comptables accessibles par drill-down.

## Classements

- Classement de véhicules/agences selon résultat, marge, variation, coût/km, taux de remplissage, en filtrant population comparable et en exposant métrique explicite.
- Ne pas confondre « plus grande recette » avec « plus rentable » ; afficher charges et ratio en parallèle.
- États des propriétaires : résultats par véhicules + agrégation du portefeuille + montant contractuel dû et règlements ; états confidentiels, pas accessibles aux autres partenaires.
