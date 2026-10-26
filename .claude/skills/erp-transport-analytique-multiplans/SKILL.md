---
name: erp-transport-analytique-multiplans
description: Corriger dans l'ERP OHADA Transport le plan analytique complet (10 plans dont agences/gares, véhicules, propriétaires, services, activités, gammes VIP/Classique, lignes, voyages, contrats et canaux), proposer pour chaque plan balances/grands-livres/comptes d'exploitation et consultations par périodes; rendre le reporting dépendant du même moteur d'imputation des écritures générales validées. À utiliser lorsqu'on demande l'architecture, l'interface, les états, le filtrage ou l'implémentation de la comptabilité analytique.
---

# Réparation complète — Comptabilité analytique, plans, états et consultations

## Décision métier prioritaire (rectifie l'ancienne interface)

L'utilisateur corrige la décision antérieure « seulement deux familles analytiques visibles ». **Les DIX plans métiers doivent être accessibles dans la comptabilité analytique**, avec plusieurs états par plan. **Véhicules** et **Propriétaires** restent des rubriques privilégiées avec états spécialisés, mais ne sont plus les seules rubriques visibles. Le module Reporting utilise exactement le même moteur d'agrégation et les mêmes données, mais dispose de vues comparatives distinctes.

Plans : (1) Agences et gares (distinguer établissements administratifs et guichets/gares physiques), (2) Véhicules, (3) Partenaires propriétaires de véhicules, (4) Services/départements, (5) Activités, (6) Gammes CLASSIQUE et VIP, (7) Lignes/itinéraires, (8) Voyages/départs, (9) Contrats d'exploitation, (10) Canaux de vente. N'ajouter pas la catégorie fournisseur au plan « propriétaires » : fournisseur et propriétaire sont des rôles de tiers distincts.

## Doctrine comptable absolue

- La **comptabilité générale validée est la seule origine des montants monétaires analytiques**. Aucune écriture monétaire indépendante en analytique, pas de 2e comptabilité générale, aucun mouvement de caisse recréé.
- Les ventilations sont des **affectations de la ligne comptable d'origine**. Un montant imputé sur plusieurs plans ne s'additionne PAS entre plans. Pour **un plan donné**, la somme des ventilations sur ses sections ne doit pas dépasser le montant admissible de la ligne; signaler un résiduel « non affecté ».
- Répartitions multiples dans le même plan : autorisées et totalisées à 100 % au maximum pour chaque ligne lorsque plan applicable. Les frais généraux peuvent rester à imputer, mais ne doivent pas disparaître des rapprochements.
- Respecter correction/contrepassation, dates d'effet et statut validé; garder les liens écriture, ligne, pièce, agence source, date, journal, exercice, régime.
- Les informations non financières (places, kilomètres, colis, passagers) viennent des faits opérationnels, **sous réserve de traçabilité**, jamais présentées comme écritures financières.
- Plan comptable général **à 7 chiffres** pour les dossiers concernés. Respecter les numéros réels et les configurations de comptes : ne pas présumer qu'une simple chaîne de préfixe suffit pour identifier toutes les charges selon le contexte juridique.
- CLASSIQUE et VIP utilisent des véhicules dédiés et des tarifs distincts, avec éventuel historique de réaffectation, daté. Les recettes colis restent une activité messagerie même si le véhicule est VIP.
- Petites agences : 1 caisse mutualisée; siège/grandes agences : plusieurs caisses; distinct de l'axe service. Ventes, encaissements et transferts ne sont pas des concepts interchangeables.
- Les contrats des propriétaires peuvent prévoir fixe mensuel, variable, fixe + variable, ou avance déductible; résultat du véhicule ≠ solde disponible du partenaire. Leur compte financier reste en comptabilité générale.
- Hors connexion : provenance de chaque agence et statut de synchronisation visibles; ne pas afficher une période incomplète comme définitive.

## Plan de lecture

1. `references/01-audit-code-existant.md` — observations vérifiées sur le code du ZIP Windows transmis.
2. `references/02-catalogue-plans-etats.md` — catalogue complet et matrice des états.
3. `references/03-moteur-donnees-migrations.md` — modèle de données multiaxes, migration et invariants comptables.
4. `references/04-interface-periodes-et-navigation.md` — UX de consultation, filtres, fenêtres, périodes et exports.
5. `references/05-reporting-coherence.md` — services de calculs communs, indicateurs, rapprochements, permissions et contrats.
6. `references/06-tests-recette-claude.md` — tests de bout en bout et protocoles de retour.
7. `examples/maquette_consultation_analytique.html` — exemple visuel interactif avec valeurs fictives, **NON connecté** à la base ERP.

## Ordre d'exécution demandé à Claude Code

1. Vérifier les versions du dépôt et des migrations et comparer avec l'audit fourni. Ne jamais considérer l'archive comme identique sans inspection. Ne pas modifier la base de production pendant l'audit.
2. Cartographier écrans, menus, modèles, vues, APIs, exports et reporting réels; produire un inventaire existant/partiel/absent.
3. Ajouter un modèle de ventilations **multiaxes** dérivées des lignes d'écriture validées; prévoir schéma d'évolution *additif* et compatibilité des champs `LigneEcriture.section` / `.vehicule` hérités. Protéger données et contrepassations, gérer les plans existants « Gares » et « Agences » sans perte.
4. Créer un catalogue des dix plans, sections et hiérarchie agence→gare, statuts et historiques; n'initialiser aucune affectation monétaire arbitraire. Afficher clairement les plans sans affectations suffisantes.
5. Construire une **API/service unique** `analytique_consulter(plan, section, periode, type_etat, filtres, statut)` réutilisée par les états et le reporting. Les rapports partagent ses agrégats validés, pas des copies de chiffres ni des PDF.
6. Produire les états standard de chaque plan : compte d'exploitation, balance, grand-livre, journal d'imputation, détails produits/charges, répartition des coûts, comparaison N/N-1, anomalies; développer les états spécifiques véhicules et propriétaires (voir catalogue).
7. Intégrer une interface simple : choix Plan → Section → État, navigation des périodes par boutons et calendrier, changement de mois indépendant, filtres combinés, recherche, détail d'écritures, export CSV/XLSX/PDF quand disponible.
8. Activer autorisations par agence/service/société; empêcher un partenaire de lire les autres comptes; historique des propriétaires selon date du contrat, non propriétaire « actuel » pour tout le passé.
9. Exécuter tests complets, contrôler la non-duplication, la somme des ventilations, le rattachement aux pièces et la cohérence reporting. Renvoyer captures et preuves de tests, puis archive du projet complète mais nettoyée des secrets.

## Résultat attendu à l'écran

**COMPTABILITÉ ANALYTIQUE** → `Plans analytiques` (10 plans) → `Choisir plan` → `Choisir section` → `Choisir état` → `Période` → `Afficher`, `Comparer`, `Imprimer`, `Exporter`, `Ouvrir détail`.

Le module principal peut présenter des raccourcis « Véhicules » et « Propriétaires », mais le menu **Plans & états** doit exposer tous les autres plans. La même règle s'applique au client web et bureau Windows.

## Ne PAS faire

- Ne pas simplement ajouter dix boutons pointant vers la balance existante mono-section : cela ne garantit PAS une ventilation correcte.
- Ne pas dupliquer les lignes d'écriture générale ni créer dix montants de charge dans la société.
- Ne pas présenter le résultat de tous les véhicules comme la somme du solde financier de leurs propriétaires.
- Ne pas calculer les soldes de caisse depuis les seules ventes de voyages ni mélanger dépôts, transferts, ventes et fonds reversés.
- Ne pas déclarer la correction terminée après seulement un contrôle syntaxique ou une maquette HTML.
