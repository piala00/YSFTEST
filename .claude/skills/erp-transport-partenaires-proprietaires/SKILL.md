---
name: erp-transport-partenaires-proprietaires
description: Mettre à jour l’ERP transport pour séparer les propriétaires de véhicules des fournisseurs, salariés et tiers divers ; gérer les conventions de rémunération fixe et variable, les avances, les retraits autorisés, les sous-comptes propriétaires, les imputations comptables générales et analytiques, et la simulation contrôlée de septembre 2026.
---

# ERP Transport Afrique Centrale — Propriétaires de véhicules : identité, contrats, rémunérations et retraits

## Mission
**Auditer d’abord le code, les données et les schémas du vrai projet.** Préserver le socle déjà validé (huit agences, 300 employés, 60 véhicules voyageurs dont 15 privés, cinq véhicules de fret, achats, caisses locales/centrales, comptabilité générale unique, états analytiques Véhicules/Propriétaires, simulation mensuelle). Faire une mise à jour additive non destructive, sans supposer que les entités actuelles correspondent à ces règles.

## Règles prioritaires
1. Le rôle de **partenaire propriétaire de véhicule** n’est ni le rôle fournisseur, ni celui d’un salarié, ni la catégorie générique des créditeurs/débiteurs divers. Une même personne morale/physique peut cumuler des rôles, mais **chaque relation et son sous-livre comptable restent distincts**. Voir [01](references/01-typologie-identite-et-comptes.md).
2. Contrat versionné et daté : propriétaire, véhicule(s), période d’effet, rémunération fixe, variable, fixe + variable, avance imputable, assiette, conditions d’ouverture de droits, charges supportées, clause de retrait et approbations. Voir [02](references/02-contrats-remunerations-et-avances.md).
3. « Salaire de propriétaire » est un **libellé métier** ; sans véritable contrat de travail, **ne jamais l’intégrer automatiquement dans la paie salariale**. Le traitement de charge, avance, rémunération de mandat, location ou autre doit être configuré après analyse juridique, comptable et fiscale. Ne jamais assimiler un retrait de compte à un salaire ou un nouveau résultat. Voir [03](references/03-comptabilite-generale-analytique.md).
4. Toute créance/dette/rémunération/payement propriétaire doit être ancrée dans une **écriture générale comptabilisée** avant de devenir monétaire dans les états analytiques. Toute ventilation analytique a `source_gl_line_id` vers la ligne générale validée ; zéro écriture analytique orpheline.
5. **Résultat analytique d’un véhicule ≠ droit contractuel du propriétaire ≠ montant disponible au retrait ≠ paiement effectué**. Un résultat positif n’ouvre pas automatiquement le droit de décaisser : dette comptabilisée, échéance, approbations, éventuelles retenues et trésorerie sont contrôlées.
6. Deux rubriques analytiques visibles : **Véhicules** et **Propriétaires de véhicules** ; les agences, gammes Classique/VIP, lignes, voyages et contrats sont des dimensions et filtres.
7. Fonds hors ligne : demandes et autorisations sensibles de paiement non dupliquées ; contrôle de limite de retrait par l’autorité compétente, rapprochement central et audit ; pas de double décaissement en concurrence entre agences. Voir [05](references/05-donnees-api-permissions-offline.md).

## Références spécialisées
- [01 Typologie, identité unique, rôles et comptes auxiliaires](references/01-typologie-identite-et-comptes.md)
- [02 Contrats, garanties, variable, avances, périodicité](references/02-contrats-remunerations-et-avances.md)
- [03 Écritures générales, imputations analytiques, absence de double charge](references/03-comptabilite-generale-analytique.md)
- [04 États, relevés et calcul des droits et retraits](references/04-etats-et-simulation.md)
- [05 Modèle de données, API, sécurité, offline](references/05-donnees-api-permissions-offline.md)
- [06 Plan de migration, tests et retour à ChatGPT](references/06-implementation-tests-retour-claude.md)

## Démonstration comptable autonome
Le dossier `examples/` contient des **données de démonstration indépendantes**, avec une écriture générale équilibrée par événement, quatre imputations analytiques liées aux lignes de la GA et un relevé propriétaire. Il n’altère **pas** les montants de la simulation principale de septembre 2026. L’exemple teste un contrat **fixe garanti + variable complémentaire**, et des paiements déjà comptabilisés. Exécuter : `python .claude/skills/erp-transport-partenaires-proprietaires/scripts/validate_exemple.py`.

## Livrables exigés de Claude Code
Audit réel EXISTANT / PARTIEL / ABSENT / RISQUE ; modèle de données et migration additive ; composants GUI/API et permissions ; moteur contractuel + validation/approbation + rapprochement GL/analytique ; rapports véhicules et propriétaires ; tests exécutés avec résultats ; analyse de l’incidence sur la simulation existante ; compte rendu `RETOUR_POUR_CHATGPT.md` et export anonymisé du projet complet. **Ne jamais prétendre qu’une fonctionnalité est déjà développée sans l’avoir vérifiée.**
