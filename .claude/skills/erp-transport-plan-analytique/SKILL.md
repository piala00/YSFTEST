---
name: erp-transport-plan-analytique
description: Auditer et mettre à jour dans le projet ERP Transport Afrique Centrale les plans/sections analytiques, les imputations automatiques entre billetterie Classique/VIP, colis, garage, voyages, paie et comptes partenaires, avec reporting agence/véhicule, OHADA et synchronisation offline-first. Utiliser pour toute demande de comptabilité analytique, rentabilité ou ventilation dans ce projet.
---

> **DÉCISION COMPTABLE PRIORITAIRE (25/10/2026) :** toute ligne analytique MONÉTAIRE doit obligatoirement dériver d'une ligne comptable GÉNÉRALE préalablement validée/postée, avec référence traçable. La comptabilité analytique ne peut créer des recettes, dépenses, dettes ni créances indépendantes. Voir `/erp-transport-comptabilite-source-unique` ; il prévaut sur les anciennes formulations contraires. Les KPI non monétaires restent issus de l'exploitation.


# Skill opérationnel — Plan analytique ERP Transport Afrique Centrale

> **Mise à jour métier ultérieure — à appliquer prioritairement :** la navigation Gestion comptable est séparée en Comptabilité générale (société entière) et Comptabilité analytique (restitution exclusivement par **Véhicules** et **Propriétaires**). Les 10 axes décrits ci-dessous demeurent dans le moteur d'imputation et les filtres, mais ne créent plus dix rubriques majeures de reporting. Voir `/erp-transport-comptabilite-generale-analytique` et ses références.



## Objectif concret

À partir du **dépôt de code existant**, auditer, concevoir, implémenter et tester une comptabilité analytique **multiaxes et traçable**, sans casser les modules déjà développés. Ce skill est un complément au skill `/erp-transport-afrique-centrale`, et il ne prouve **pas** que le code applicatif a été modifié. Ne pas présenter les documents comme des migrations déjà exécutées.

## Règles métier CONFIRMÉES

1. **CLASSIQUE et VIP ont des véhicules dédiés distincts**. Un véhicule ne doit pas être engagé simultanément comme Classique et VIP sur une même période. Chaque voyage passagers n'a qu'une seule gamme ; la gamme d'exploitation est cohérente avec l'affectation historique du véhicule à la date du départ. Une réaffectation future, si autorisée, est datée et auditée, jamais rétroactive.
2. L'ERP couvre **billetterie, colis/messagerie, exploitation/voyages, garage, carburant, stocks/achats, RH/paie, trésorerie, comptabilité et partenaires**. Chaque service saisit uniquement ses événements métier ; **pas de ressaisie comptable/analytique redondante**.
3. **Agence de vente ≠ agence d'exploitation** ; elles doivent être préservées indépendamment. L'encaissement dans une agence ne signifie pas que toute la recette lui appartient économiquement.
4. **Propriétaire du véhicule ≠ compagnie exploitante** ; contrats et affectations datés. Le résultat analytique d'un véhicule ne donne **pas** automatiquement le solde payable au partenaire.
5. **Comptabilité générale ≠ analytique ≠ caisse** : les ventilations analytiques ne créent pas une deuxième charge/revenu ni un deuxième paiement.
6. Les recettes passagers VIP/Classique appartiennent à des gammes distinctes ; les **recettes colis restent dans l'activité COLIS** même si elles sont transportées dans un véhicule VIP ou Classique. Des vues croisées permettent d'analyser l'activité colis par gamme et véhicule sans la rebaptiser « billet VIP ».
7. **Offline-first** : opérations locales et événements synchronisés idempotemment ; un siège temporairement non synchronisé affiche « provisoire/incomplet ». Pas de résolution « last write wins » sur les montants et affectations financières.
8. **SYSCOHADA** : les comptes, règles de reconnaissance, fiscalité et écritures légales sont paramétrables et soumis à validation professionnelle ; ne jamais inventer les numéros de comptes ni des règles impératives de commission.

## Plans analytiques retenus (catalogue initial)

| Code | Plan | Usage | Source d'affectation | Obligation |
|---|---|---|---|---|
| AGC | Agences | résultats par établissement | agence exploitation, et rôle vente séparément | selon nature |
| VEH | Véhicules | compte d'exploitation véhicule | affectation réelle du voyage / bon garage | pour coûts/produits véhicule |
| PRT | Partenaires / propriétaires | rentabilité par propriétaire/contrat | historique de contrat à la date du fait | si partenaire |
| DEP | Services/départements | coûts des équipes | service producteur/bénéficiaire | pour charges concernées |
| ACT | Activités | transport passagers, messagerie, location… | ligne commerciale d'origine | pour produits opérationnels |
| GAM | Gammes | CLASSIQUE ou VIP | voyage passagers et véhicule affecté | pour voyages passagers |
| LIG | Lignes/itinéraires | comparer les axes géographiques | itinéraire du voyage | si voyage |
| VOY | Voyages/départs | résultat d'une rotation | voyage / jambe de transport | si transport |
| CTR | Contrats d'exploitation | règles économiques appliquées | contrat daté et en vigueur | si sous contrat |
| CAN | Canaux de vente | guichet, en ligne, revendeur | origine de transaction | lors des ventes |

**Important** : ces dix plans sont un référentiel métier cible, pas une limite technique. Le référentiel `AGC` doit conserver deux **rôles** (vente / exploitation) sans transformer les encaissements en produits dupliqués. Des dimensions supplémentaires (ex. agence de vente autonome) peuvent être introduites si le moteur existant impose un axe distinct ; documenter ce choix. Les personnes, le mode de paiement et le numéro de pièce peuvent rester des attributs de faits et filtres de rapports plutôt que des plans comptables.

## Documents à lire selon le chantier

1. [Catalogue, sections, Classique/VIP](references/01-catalogue-axes-sections.md)
2. [Modèle de données, contraintes, migrations](references/02-donnees-migrations.md)
3. [Moteur d'imputation et clés de répartition](references/03-moteur-ventilation.md)
4. [Flux métier interservices](references/04-flux-metiers.md)
5. [Comptes partenaires et restitution](references/05-partenaires-reporting.md)
6. [Écrans, autorisations et tableaux de bord](references/06-interfaces-rbac.md)
7. [Tests, recette, déploiement et reprise](references/07-tests-deploiement.md)
8. [Sources officielles et limites](references/08-sources-et-limites.md)

## Procédure de mise à jour du projet réel

1. **Inspecter sans écrire** : arborescence, stack, ORM/SQL, migrations, modules, comptes/axes existants, API, rapports, tests, logique de flotte Classique/VIP, éventuelles dépendances Sage. Repérer les écrans/tableaux existants et préserver leurs habitudes de navigation.
2. Construire une matrice `existant / partiel / manquant / conflit / tests` et localiser précisément les fichiers concernés.
3. Définir un **schéma d'écritures analytiques de gestion** dérivé de transactions comptables/événements validés ; fixer la vérité métier pour chaque champ. Proposer des migrations **additives, rétrocompatibles et sauvegardables** ; ne pas réinitialiser la base.
4. Faire une implémentation incrémentale : catalogue des axes → sections/versionnement → classification historique des véhicules → données d'imputation → moteur de ventilation → intégration billetterie/colis/garage/paie → vues de gestion → tests → UI/reporting. Tester chaque étape.
5. Autoriser les saisies analytiques manuelles uniquement dans un circuit contrôlé (motif, approbation, historisation) ; ne pas masquer les imputations manquantes : file d'anomalies.
6. Définir les **règles d'imputation** `source_event_type + entity + date_effet + rule_version` ; garantir idempotence et ordre fonctionnel de rapprochement après sync.
7. Séparer `produits/charges comptables`, `marges analytiques`, `droits du partenaire`, `paiements`. Toute restitution doit pouvoir expliquer sa formule et ses sources.
8. Exécuter réellement les tests adaptés au dépôt. Produire inventaire des fichiers modifiés, migrations, tests passés/échoués/non exécutés et limites. Ne **jamais** annoncer un développement terminé si seules les spécifications ont été produites.
9. Pas de modifications destructives, de refonte d'interface ou d'envoi de données de production sans consentement explicite. Prévoir plan de repli et sauvegarde avant migrations.

## Définition de terminé

- Chaque service enregistre son travail habituel ; les dimensions pertinentes sont déduites automatiquement.
- Un billet **VIP** ne peut être affecté à un départ **Classique** ; véhicule et gamme cohérents, y compris après synchronisation.
- Une opération enregistrée dans plusieurs rapports ne compte **qu'une seule fois** dans le résultat global.
- Une réparation ou consommation d'une pièce est imputée au bon véhicule, sans double charge d'achat/consommation.
- Les résultats **voyage → véhicule → agence → compagnie** se rapprochent de la comptabilité selon des règles explicites, avec écarts documentés.
- Un propriétaire multi-véhicules obtient le détail analytique de ses véhicules ET son relevé financier contractuel distinct.
- En cas de coupure/reprise Internet, aucune écriture n'est perdue ou comptée deux fois ; le statut de fraîcheur est visible.
- Les 12 cas minimum du document `07-tests-deploiement.md` passent avec preuves d'exécution.

## Commande typique

« Applique le skill `/erp-transport-plan-analytique` à mon dépôt. Commence par auditer l'existant, puis mets à jour progressivement les modèles, les règles métier, les écrans, les imputations automatiques et les rapports. Ne supprime aucune fonctionnalité existante ; préserve les données et exécute les tests. Les véhicules CLASSIQUE et VIP sont des flottes distinctes. »
