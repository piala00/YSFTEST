# Premier rapport de réconciliation — Codex, 31 octobre 2026

Source de la mission : [coordination](https://github.com/piala00/YSFTEST/issues/24#issuecomment-6543059283),
[continuité](https://github.com/piala00/YSFTEST/issues/24#issuecomment-6543082601) et
[ordre de reprise](https://github.com/piala00/YSFTEST/issues/24#issuecomment-6543092933).
Index directeur : #24. Ce rapport est une première réconciliation traçable, pas une acceptation utilisateur ni une
preuve d'exhaustivité de toutes les demandes historiques. Les six documents de pilotage sont conservés et complétés.

## Résultat du rapprochement

Les 46 ID initiaux restent inchangés. Neuf détails historiques sont ajoutés : sociétés et paramétrage évolutif (A-004),
auteurs d'origine (A-005), règlements multi-factures/en attente (B-002), crédit (B-003), contrôle fichiste (B-004),
conditionnements (B-005), commandes/avances/facturation (B-006), rapport commercial à quatre volets (E-004) et
synchronisation complète Sage puis autonomie ERP (F-004). Total :55 entrées, dont des familles et leurs détails ; ce
total ne sert pas de dénominateur de couverture logicielle.

La [correspondance de transmission](CORRESPONDANCE_TRANSMISSION.csv) conserve les formulations et ID source :
55 demandes confirmées E01–E55 et26 propositions P01–P26, soit81 lignes rattachées aux ID ERP. Une proposition reste
une proposition, même lorsqu'elle est reliée à une exigence. Un rattachement documentaire n'est pas un test.
Source exacte : `skill://user/6adc59caed3c819191a92d28d20a7a4b/erp-ohada-agences-hors-ligne-rapport-stock/references/EXIGENCES.csv`,
SHA256 du contenu consulté : `51cac60ec76e40ef05f18dea5e055999f98265541c4162a18bf86f030b108605`.

Les besoins déjà couverts par une entrée ne reçoivent pas un nouvel ID : Q-003 est précisé par la consigne d'autonomie ;
A-003 conserve les fenêtres transversales U5/U6 ; E-002 retrouve explicitement l'engagement Excel. B-001 reste la famille
Commercial et les sous-besoins B-002–B-006 conservent un rattachement explicite. Aucun ancien ID n'est réutilisé.

## Sources et limites de lecture

- AGENTS.md sur `ccr-5592a371-fusjt2`, historique de #1, issues #10/#18/#24, métadonnées des PR et transmissions déjà livrées.
- PR #26 et ses six fichiers ; rapports #22/#23/#25/#28 et leurs journaux CI, sans réexécuter les anciens diagnostics.
- Fiches ERP agences hors ligne et retour de revue : U1–U7, exigences/propositions, bilan et A01–A07 de la copie du24/10.
  Cette copie historique n'est pas assimilée au SHA courant. Les captures réelles ne sont pas republiées dans le dépôt.
- Catalogue/menus/tests de l'état colis non livrés, catalogue budget/trésorerie, CSV d'audit existants.
- Le rapprochement ligne à ligne de tous les commentaires, anciennes spécifications et chaque commande reste à compléter.
  Les deux anciens skills Reporting Transport non présents au catalogue actif ne sont pas déclarés lus.

## État réel et preuves

| Lot | État vérifié | Preuve et limites |
|---|---|---|
| #2–#7 | Fusions historiques observées | Réutiliser leurs correctifs ; aucune fusion effectuée dans cette session |
| #8/#9 | Brouillons documentaires | TR-01 déjà corrigé et vérifié antérieurement ; ne pas réannoncer l'ancien défaut ni le recoder |
| #11–#21 | Propositions en chaîne, fonctions déjà développées | Garder leurs SHA/preuves ; pas d'intégration ou acceptation globale inférée |
| #22 | P0 comptable proposé et testé | 536 tests SQL sans ignoré ; audit d'architecture déjà livré |
| #23 | Qualification CI acquise sur identité fictive | [Run41152023209](https://github.com/piala00/YSFTEST/actions/runs/41152023209), huit contrôles ; personnalisation réelle non acquise |
| #25 | Qualification CI acquise dans son périmètre | [Run41196187906](https://github.com/piala00/YSFTEST/actions/runs/41196187906), SHA dea6c916 : 558 SQLite/SQL, Windows Server2025, parcours installateur et nettoyage fictifs |
| #28 | Correction Documents proposée pour revue | [Run41201383014](https://github.com/piala00/YSFTEST/actions/runs/41201383014), SHA ae724335 : 574 SQLite (6 ignorés), 574 SQL (aucun ignoré), deux connexions concurrentes, huit contrôles réussis |
| #26 | Pilotage documentaire en brouillon | 55 entrées, correspondance et demandes non vérifiées ; revue de réconciliation non acceptée à ce stade |

Les PR #22/#23/#25/#28 sont qualifiées pour leur revue dans les limites citées, pas autorisées à être fusionnées.
La relecture croisée de Claude n'est pas déclarée faite. Les contrôles du modèle Documents sont ceux des suites source
et SQL ; compilation/démarrage des deux EXE ne vaut pas recette métier native exhaustive, Windows10/11 distincts ou PC réel.

## Écarts de suivi et travaux à réutiliser

- Matrice globale `docs/retour/MATRICE_AUDIT_GLOBAL_ERP_SAGE.csv` au SHA ae724335 : en-tête seul, zéro ligne de données.
  Recensement Commercial `RECENSEMENT_BOUTONS_COMMERCIAL.csv` :427 lignes et427 ID distincts. Ces comptages ont été lus
  avec le séparateur propre à chaque fichier ; ils ne prouvent pas que427 commandes fonctionnent. L'audit global reste ouvert.
- L'état colis non livrés existe avec seuil/ancienneté/CSV, menu `transport.recettes.colis_non_livres`, graphique par gare
  et test nominal. Le catalogue statique `apps/reporting/analyses.py::catalogue` n'inclut pas son lien. Compléter ce point
  de découverte permettra de réutiliser l'état au lieu de le reconstruire.
- Budget/réel et trésorerie projetée figurent déjà au catalogue. Scénarios financiers multipériodes, export.xlsx et autres
  états doivent être qualifiés individuellement. L'ancien engagement Excel demeure visible dans E-002.
- Les défauts Documents de #27 sont reproduits et corrigés dans #28 ; ne pas refaire cet audit. Les autres actions,
  notamment règlements, transformations et concurrence SQLite, gardent leurs propres critères de recette.

## Contradictions et décisions conservées

1. « Fusionner quand vert » dans l'ancienne coordination ne respecte pas DEC-001 : non appliqué.
2. U5 remplace U4 et la recommandation ancienne d'une facture unique obligatoire : zéro/une/plusieurs affectations et
   attente de rattachement sont préservées (DEC-011), avec un seul encaissement.
3. #26 est documentaire, en parallèle de #28, tous deux sur #25. L'ordre d'intégration produit est la chaîne jusqu'à
   #25 puis #28 ; une chaîne textuelle passant par #26 ne doit pas servir de base de distribution.
4. Simulation intégrée, gestionnaire indépendant et simulation financière sont conservés distincts ; aucune suppression
   de l'existant ni déclaration de livraison du simulateur autonome sur la seule présence de .erpsim.
5. Dix plans visibles/onze axes, assiette des15%, champs d'en-tête non fournis et conditions de bascule restent à qualifier.
   Les sources ne justifient ni taux fiscal inventé, ni renommage destructif, ni conversion silencieuse.

## Prochaine séquence exécutable

| Étape | Périmètre borné et critère de sortie | Dépendance |
|---|---|---|
| Pilotage02 | Rapprocher les autres sources historiques avec les ID ; relier chaque omission au registre des demandes non vérifiées | Réutiliser cette correspondance, sans réécrire les 46 entrées initiales |
| Reporting03.1 | Ajouter le lien de l'état colis existant au catalogue Transport et vérifier découverte/filtrage ; conserver menu, CSV et graphique existants | Branche/PR distincte, pas de nouveau moteur ; ensuite qualifier les quatre autres cibles historiques |
| Menus05.1 | Peupler/dédupliquer la matrice globale à partir des427 entrées et correctifs #2/#4/#5/#7/#8 ; commande→fonction→implémentation→test→écart→correctif→validation | N'annoncer la clôture qu'après couverture/exceptions vérifiables |
| Recette04.2 | Étendre aux autres mutations prioritaires les critères GET/droits/période/double envoi/atomicité ; corriger seulement les défauts reproduits | Réutiliser #22/#28, lot autonome si un nouveau P0 est confirmé |
| Intégration préparatoire | Garder parents/SHA, examiner conflits et proposer le résultat à intégrer | Aucune fusion ou mise à jour de machine réelle sans autorisation distincte |

Les blocages et couvertures manquantes sont dans [DEMANDES_NON_VERIFIEES](DEMANDES_NON_VERIFIEES.md). Les tâches
indépendantes continuent sans nouvelle confirmation. Aucune exécution permanente hors session n'est établie par un
commentaire ; aucun besoin de reconfigurer la session actuellement disponible n'a été constaté.

Ce lot de pilotage modifie seulement la documentation. Contrôles : IDs ERP/source uniques, références de correspondance,
formats CSV, noms et périmètres des PR. Aucun nouveau test logiciel, fusion, déploiement ou donnée de production.
