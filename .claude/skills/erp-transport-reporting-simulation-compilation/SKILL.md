---
name: erp-transport-reporting-simulation-compilation
description: Auditer et améliorer ERP OHADA Transport : reporting unifié comptabilité générale et dix plans analytiques, simulations multi-mois et compilation complète Windows. À appliquer sur le code existant sans modifier les données de production.
---

# ERP Transport — Reporting unifié, simulation pluri-mois et compilation Windows

**Édition validée : 26 octobre 2026.** Utiliser ce Skill avec le projet ERP-OHADA-Transport fourni et avec les Skills historiques. **Cette version prévaut** en cas de divergence sur les plans analytiques : **10 plans visibles**, pas uniquement Véhicules et Propriétaires.

## But / ordre impératif
1. Analyser le projet réellement présent (Django, Desktop CustomTkinter, WSGI, modules, modèles, permissions et base).
2. Sauvegarder, versionner et préparer une base de TEST indépendante. **Aucune migration destructive ni simulation sur base réelle.**
3. Construire **un moteur de reporting unique** : sources GL validées + ventilation analytique traçable + informations non financières des opérations ; dix plans consultables, états GL officiels et états analytiques exhaustifs.
4. Ajouter les états comparatifs, filtres de périodes et drill-down vers pièces comptables ; distinguer activité, comptabilité, encaissements et prévisions.
5. Étendre le simulateur du logiciel sur 1/3/6/12/24/36 mois sans réinitialiser la société à chaque période ; clôture et paie pour chacun des mois.
6. Ajouter l'option de compilation pour le logiciel complet : **clients desktop et serveur Django séparés** dans un livrable installable Windows ; compiler et tester sur une machine Windows. Ne jamais dire que les `.exe` existent sans les avoir réellement construits.
7. Rendre le projet complet, des tests, les résultats, anomalies et un rapport à l'utilisateur pour vérification collaborative.

## Sources de vérité
- Comptabilité générale validée = unique origine des montants comptables. Chaque ligne analytique monétaire référence une ligne de GL validée ; ventilation sans multiplier la charge ou le produit. Aucun calcul propre au reporting ne peut créer de nouvelle écriture.
- Les données non monétaires (voyageurs, km, poids de colis, sièges) viennent des modules opérationnels et portent explicitement leur statut.
- La comptabilité analytique expose dix plans ; les vues **Véhicules et Propriétaires** demeurent des favoris, pas une restriction.
- Un véhicule a une gamme Classique **ou** VIP pendant une période d'affectation. Le propriétaire se définit par contrat daté. Le solde disponible du propriétaire n'est pas le résultat du véhicule.
- Plan comptable général 7 chiffres pour les nouveaux dossiers ; conversion seulement après simulation de collisions, sauvegarde et autorisation.

## Lire ces références dans l'ordre
1. `references/01-architecture-et-fondations.md`
2. `references/02-catalogue-reporting-general.md`
3. `references/03-catalogue-analytique-10-plans.md`
4. `references/04-periodes-comparaisons.md`
5. `references/05-simulation-multimois.md`
6. `references/06-compilation-windows.md`
7. `references/07-tests-recette.md`
8. `references/08-retour-collaboratif.md`
9. `references/09-audit-code-analyse.md`

## Implémentation accompagnant ce Skill
`implementation_proposee/` contient une commande Django de simulation pluri-mois et un point d'entrée de serveur Windows, des scripts de compilation et notices. **Comparer aux fichiers du dépôt avant tout remplacement** ; ce sont des propositions adaptées au code inspecté, et non une garantie d'exécution en production.

## Séquence de retour attendue
Répondre à l'utilisateur : constat des fonctionnalités réellement présentes, chantiers accomplis, preuves de tests, chiffres reproductibles de simulation (par mois), captures et fichiers d'export, écarts bloquants, chemins exacts des binaires *effectivement* construits et de la sauvegarde de code. Ne jamais masquer une erreur de rapprochement ou une absence de test Windows.
