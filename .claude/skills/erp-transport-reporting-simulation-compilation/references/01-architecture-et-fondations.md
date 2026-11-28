# 01 — Architecture de référence et invariants

## Flux
Services (billetterie, colis, garage, flotte, achats/stock, RH/paie, caisses) → journal de faits opérationnels et validations → écritures GL en partie double (SYSCOHADA) → 10 plans analytiques ventilés → moteur de restitution commun → Comptabilité générale / Comptabilité analytique / Reporting.

`ReportQuery` proposé : `{company_id, plan_code, section_ids, date_start, date_end, state, accounting_basis, currency, axes_filters, comparator}`. Mêmes bornes, droits, arrondis et filtres pour toutes les interfaces (web/bureau/impression/API). Utiliser des colonnes montants Decimal et un calcul centralisé de l'agrégation.

### Source et statut
- Montants COMPTABILISÉS : uniquement écritures validées GL ; FK obligatoire vers `LigneEcriture`, éventuellement réparties entre plusieurs sections.
- Montants PRÉVISIONNELS / À VALIDER : opérations métier encore hors GL, visibles seulement dans une vue séparée, ne jamais les confondre avec les états financiers.
- Les écritures en brouillard ne figurent pas parmi les résultats définitifs.
- Dépenses garage : facture d'achat/stock ≠ consommation de pièce. La charge véhicule naît avec la consommation comptabilisée (ou autre traitement comptable validé).
- Pour chaque somme globale, afficher décomposition `{affecté, non_affecté, exclu_justifié}`, sans trou silencieux.
- Une ligne GL de 100 FCFA ventilée en plusieurs sections sur UN MÊME AXE doit totaliser 100 FCFA sur cet axe, pas 200 ; une ventilation sur des axes différents ne double pas le GL consolidé.

### Rapprochements automatiques
1. Débit GL = crédit GL, à chaque pièce et par période.
2. Pour chaque axe activé : `montant GL éligible = affectations de cet axe + non affecté + exclusions documentées`.
3. Ensemble des agences consolidées : exclure transferts internes de caisse des produits et charges ; ne pas compenser sans preuve les transferts en transit.
4. Par véhicule et contrat : attribution historique à la date d'effet (jamais au seul propriétaire courant).
5. Les états analytique et reporting s'appuient sur la **même requête de référence**, pas deux calculs indépendants.

### Multi-agence offline
Chaque agence est autonome dans son périmètre ; journalisation durable, idempotence de synchronisation, identifiants globaux, transferts inter-agences distincts de produits. Afficher fraîcheur des données par agence et statut `provisoire / synchronisation incomplète / clôturé`. Les comparaisons du siège ne doivent pas faire passer des chiffres partiels pour définitifs.

### Sécurité
RBAC par rôle + agence + opération + société ; restrictions des propriétaires à leurs droits ; exports et journaux auditables. Une base démo ne doit jamais contenir des données privées réelles.
