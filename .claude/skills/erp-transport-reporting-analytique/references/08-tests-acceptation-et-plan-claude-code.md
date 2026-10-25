# 08 — Plan Claude Code et tests de réception

## Étape 0 : inventaire (obligatoire)

Rechercher le code de tous les modules, vrais schémas, migrations, APIs, permissions, écrans, tables de GL/analytique, contrats, cache, sync et tests. Livrer liste des fichiers inspectés et matrice : `Existant / Partiel / Absent / Contradictoire`. Ne pas inventer les noms de tables d'un projet non fourni. Proposer un plan et distinguer changements sûrs de ceux soumis à validation comptable.

## Étapes d'implémentation

1. **Définition** : inventorier KPI, grain, date de référence, statut, source, filtres et règles de version ; valider avec responsable finance/exploitation.
2. **Données** : aligner plan analytique, lignes GL, pièces métier et contrat daté ; migrations additives réversibles + sauvegarde.
3. **API** : agrégats, comparaison A/B, KPI techniques, règles de filtre RBAC, drill-down, statut sync ; stratégies de cache.
4. **Interface** : reporting transverse, tableaux période A/B, listes véhicules/agences, classes, propriétaires, tableaux journaliers simples préservés.
5. **Rapprochements** : non affecté, répartitions, écarts, relecture des états clos, comptes partenaires.
6. **Sécurité et recette** : tests fonctionnels, charge, isolation, hors connexion et vérification des exports.

## Tests à automatiser

- `T01` Billet émis et encaissé : un seul produit admissible ; pas de duplication par mouvement de caisse.
- `T02` Même billet plusieurs scans : pas d'augmentation de recette ni du nombre de passagers uniques.
- `T03` Billet vendu J-1, voyage J : encaissement J-1, prestation J selon règles ; les états quotidiens ne doublent rien.
- `T04` Achat de pièces stock J, sortie au garage J+2 : coût véhicule une fois selon fait éligible.
- `T05` Colis vendu agence A, transporté par véhicule de B : agences vente/exploitation distinctes, revenu compagnie non doublé.
- `T06` Caisse unique vs multi-caisses et transfert interne : montant total entreprise inchangé.
- `T07` Véhicule VIP dédié ne ressort pas en Classique sur même période d'affectation ; changement daté fonctionne.
- `T08` Changement de propriétaire à date J : historiques attribués selon contrats et droits contractuels, pas uniquement propriétaire actuel.
- `T09` Partenaire à trois véhicules : résultat véhicule individuel et total partenaire cohérents, solde payable distinct.
- `T10` Charge du siège non répartie : apparaît GL et rapprochement non affecté, pas dans véhicule sans règle.
- `T11` Comparaisons A/B avec référence zéro : variation N/A, aucun infini ni division zéro ; taux pondérés.
- `T12` Mois incomplet vs complet : avertissement affiché ; mois libre et exercice fiscal correctement bornés.
- `T13` Sync du même lot 3 fois : agrégats strictement identiques et une seule ligne comptable par événement.
- `T14` Une agence non synchronisée : badge provisoire, fraîcheur et agence manquante visibles ; remontée restaure chiffre correct.
- `T15` Utilisateur agence/partenaire ne peut accéder via API/export à une autre agence/compagnie/propriétaire.
- `T16` Avoir, annulation, remboursement, correction de coût après clôture : retraitement traçable, pas suppression silencieuse.
- `T17` Somme des allocations d'une écriture éligible = valeur comptable admissible, compte tenu de non affecté et arrondis ; la somme sur plusieurs axes n'est jamais agrégée.
- `T18` Export et impression : mêmes valeurs et filtres qu'à l'écran, unités, devise, dates, statut, pas de colonnes coupées.

## Critères de livraison

Démontrer sur données test réalistes : `GL société` → `rattachements analytiques` → `états véhicule et propriétaire` → `reporting agences/véhicules/périodes` → `opérations sources`, avec sommes traçables. Fournir logs des tests exécutés, migrations et défauts connus. Ne pas déclarer des tests réussis sans exécution.
