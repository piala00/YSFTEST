# 02 — Contrats, rémunérations fixes et variables, avances

## Modes contractuels paramétrables
- `FIXE_SEUL`: somme fixe exigible selon échéance et conditions contractuelles.
- `VARIABLE_SEUL`: quote-part de produits ou marge éligible avec base définie.
- `FIXE_GARANTI_PLUS_VARIABLE`: fixe dû + **complément distinct** calculé sur la base convenue ; prévoir si la base variable exclut le fixe.
- `FIXE_AVANCE_SUR_VARIABLE`: versement périodique de trésorerie déduit du droit variable final, **pas une charge distincte supplémentaire**. Si variable inférieur aux avances : solde débiteur, report ou mécanisme de garantie exclusivement selon contrat.
- `FORFAIT_LOCATION` et autres clauses : nature juridique, assiette et schéma comptable validés explicitement ; ne pas préjuger la classe de charge.

## Champs contractuels minimum
`contract_id`, `owner_id`, `vehicle_id`, `valid_from`, `valid_to`, `version`, `pricing_mode`, `fixed_amount`, `fixed_period`, `fixed_guaranteed`, `fixed_is_advance`, `variable_rate`, `variable_basis` (après quoi), `eligible_revenue_rules`, `eligible_expense_rules`, `allocation_key`, `loss_carryforward`, `withdrawal_policy`, `minimum_cash_buffer`, `withholding_policy`, `currency`, `status`, `approved_by`, `approved_at`, `posted_gl_scheme_version`.

**Historiser les conventions** (nouvelle version, ne pas modifier les calculs passés). Un véhicule peut changer de propriétaire et un propriétaire posséder plusieurs véhicules. Les propriétaires et véhicules éligibles doivent être déterminés à la date contractuellement définie, pas via l'affectation actuelle.

## Exemple A : fixe garanti + complément
Produit du véhicule : 1 000 000 FCFA ; frais d'exploitation hors partenaire : 400 000 ; marge avant rémunération propriétaire : 600 000. Fixe garanti : 150 000. Complément : 40 % de la base résiduelle `600 000 − 150 000 = 450 000`, soit 180 000. Droit total propriétaire = 330 000. Résultat analytique après charge du propriétaire = 270 000. Si le fixe payé est 150 000 et qu'un retrait supplémentaire de 100 000 est approuvé et payé : solde dû = 80 000. Tout cela est **fictif et dépend du contrat**.

## Exemple B : avance imputable
Produit 1 000 000 ; frais 400 000 ; droit variable 40 % de la marge avant rémunération (600 000) = 240 000. L'« allocation mensuelle » de 150 000 est une **avance imputée** sur ces 240 000 (pas 150 000 + 240 000). Reste dû = 90 000, avant tout autre règlement/ajustement. Écritures de charge et d'avance selon le schéma juridique retenu.

## Arrêt d'activité et pertes
Véhicule immobilisé, sinistre, départ reporté, marge nulle ou négative : ne pas suspendre automatiquement un fixe `guaranteed=true`, mais vérifier date d'exigibilité, cas contractuels de suspension, retenues et exceptions. Si le variable est négatif : plancher à zéro **uniquement si contractuellement prévu** ; ne pas inventer de perte reportable sans clause. Toute écriture doit être GA-first.
