# 01 — Sources de vérité et frontière entre les comptabilités

## Positionnement

- **Comptabilité générale (GL)** : écritures à partie double, comptes et tiers, journaux, pièces, clôtures et états SYSCOHADA. S'applique à l'ensemble des activités, y compris les dépenses de siège non attribuées aux véhicules.
- **Plan analytique / moteur d'imputation** : dimensions et sections à dates d'effet ; allocations et clés de répartition ; liaison auditée avec les lignes comptables éligibles. Permet des coûts de gestion, des budgets et des comparaisons, sans créer une deuxième balance réglementaire.
- **Comptabilité analytique (présentation)** : comptes d'exploitation véhicules et situations propriétaires ; ses deux seuls pivots principaux restent Véhicules/Propriétaires.
- **Reporting transversal** : vues multidimensionnelles à partir des données analytiques, financières et opérationnelles ; ses comparaisons sont des filtres/requêtes, pas des saisies comptables.

## Flux source typique

1. Service opérationnel enregistre une pièce : billet, bagage, colis, bon de garage, sortie de pièce, carburant, paie, etc.
2. Le service crée l'événement de gestion idempotent, les liens agence/ligne/voyage/véhicule/caisse et le statut.
3. Le moteur d'intégration génère, sous contrôle, les écritures comptables appropriées, suivant l'événement taxable/comptable et les règles de dates.
4. Les lignes éligibles sont ventilées analytiquement par sections selon les règles à date d'effet.
5. Reporting calcule les agrégats et KPI, avec références vers écritures + événements sources ; certaines métriques purement physiques viennent directement de l'exploitation.

## Règles pour éviter doubles comptes

- Un ticket vendu avec paiement ne doit pas créer *deux produits* parce qu'il existe à la fois un billet et une entrée de caisse.
- Une recette de colis encaissée dans une agence et transportée par un véhicule ne devient pas deux produits : transaction unique, axes agence-vente et véhicule-exploitation distincts.
- Un mouvement de fonds caisse A → caisse B est un transfert de trésorerie interne, jamais un produit ni une nouvelle dépense externe.
- Les achats de pièces en stock et leurs consommations par garage ont un traitement distinct ; ne pas enregistrer une charge du véhicule deux fois pour la même pièce.
- Une avance chauffeur n'est pas automatiquement une charge définitive ; régulariser avec pièces et reddition des comptes.
- Comptes de produits/charges: plan analytique optionnel/obligatoire selon type, dérogation et contrôles ; comptes de trésorerie et de tiers n'entrent pas directement dans les marges opérationnelles du véhicule.
- Les allocations de gestion ne modifient pas le journal de comptabilité générale ; toutes les règles sont datées, versionnées et justifiables.

## Dimensions (internes, filtres)

- société/tenant ; agence de vente et agence exploitante ; service à l'origine ; activité passagers/bagages/colis ; gamme CLASSIQUE/VIP ; véhicule ; voyage ; ligne ; tronçon ; partenaire propriétaire ; contrat ; canal ; dates événement/prestation/encaissement/comptable.
- Un véhicule peut connaître des changements d'affectation/propriétaire, mais aucun nouveau propriétaire ne reçoit rétroactivement le résultat des périodes antérieures.

## Vocabulaire

- « Bilan véhicule » en interface = **état d'exploitation/gestion**, pas bilan légal SYSCOHADA autonome.
- « Solde propriétaire » = solde du compte contractuel/auxiliaire, distinct de la marge analytique des véhicules.
- « Consolidation des agences » d'une seule personne morale = centralisation/reporting par établissement, distinct de la consolidation légale de plusieurs sociétés.
