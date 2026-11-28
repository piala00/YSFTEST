# 01 — Contrat de cohérence : grand livre → analytique

## Énoncé de vérité

La comptabilité générale de chaque personne morale est le **référentiel unique** des écritures comptables. Une ligne analytique monétaire est une *projection* ou *affectation* d'une ligne du grand livre comptabilisée (ou d'une distribution de lignes source vérifiable). Jamais une deuxième saisie de dépenses ou produits.

Invariants :

- `ANALYTIC.source_gl_line_id` référence `GL_LINE.id` existant ; lien non nullable pour les écritures monétaires.
- Source `GL_ENTRY.status == POSTED` / `VALIDATED` (définir le statut exact dans l'existant), avec date, société et journal valides ; ne pas utiliser les brouillards.
- Société/tenant, devise, période, signe et base monétaire compatibles avec la ligne GL ; les allocations ne créent pas une nouvelle devise ou valeur comptable.
- Une GL_LINE produit 0..n affectations analytiques selon son éligibilité. Si obligatoire mais non affectée, conserver un **écart « non ventilé » identifiable** ; jamais inventer une imputation silencieuse.
- Une ventilation modifie la destination **sans changer** la valeur GL ni sa justification.
- Toutes modifications de répartition sont versionnées, horodatées et autorisées ; si période clôturée, appliquer une correction sur une période ouverte selon politique validée.
- Un mouvement correctif GL implique une projection analytique corrective liée à la source GL de correction ; interdiction des modifications monétaires directes de l'analytique.
- Les écritures comptables de chaque société restent séparées ; les transferts inter-agences d'une même société ne créent pas de revenus additionnels.
- Ne pas afficher comme “bilan comptable SYSCOHADA” un état d'exploitation par véhicule ; titrer “Compte de résultat d'exploitation analytique”, “État d'exploitation” ou “Situation analytique”.

## Statuts

- `OPERATIONAL`: fait saisi et vérifié côté service.
- `GL_DRAFT`: écriture de comptabilité générale préparée, pas encore intégrée aux états analytiques définitifs.
- `GL_POSTED`: écriture équilibrée, autorisée et comptabilisée ; peut entrer en analytique.
- `ANALYTIC_ALLOCATED`: affectation créée à partir de GL_POSTED.
- `RECONCILED`: ventilation contrôlée, somme des sections + non ventilé = montant général éligible.
- `CLOSED`: écriture/période figée selon politique de clôture.

Ne jamais transformer un statut “réservation”, “encaissé”, “transporté” ou “facture émise” en “GL_POSTED” sans processus de comptabilisation.

## Périmètre de comptabilisation

La règle d'inclusion analytique doit être **documentée par familles de comptes**, par activité et selon la période. En principe les produits et charges pertinents sont les mesures financières de résultat ; avances, dépôts, décaissements, TVA, achats d'immobilisations ou de stock et transferts de caisse ne doivent pas être mélangés automatiquement à la marge véhicule.

Les états financiers (grand livre, bilan, balance) restent dans la générale. Les KPIs non financiers peuvent provenir directement de données opérationnelles, à condition d'être affichés comme tels. Les simulations/budgets peuvent exister, mais dans un périmètre prévisionnel clairement séparé, sans se faire passer pour des écritures réelles.
