# Matrice des exigences : agences, rapport commercial, fiche de stock, crédit et traçabilité

Source : skill `.claude/skills/erp-ohada-agences-hors-ligne-rapport-stock` (exigences E01–E44 de l'utilisateur et
propositions P01–P26). Pour chaque ligne : ce qui existe dans le code, l'écart restant et la preuve (test automatisé).

Statuts :
- **Couvert** : implémenté et testé.
- **Partiel** : une partie est livrée, l'écart restant est indiqué.
- **À faire** : rien n'est livré, la tranche est prévue.
- **Décision** : en attente d'un arbitrage (voir `references/DECISIONS_OUVERTES.csv`).

## Tâche 1 : sociétés, agences, hors ligne, gros et détail

| Id | Exigence (résumé) | Existant / adaptation | Écart restant | Preuve |
|---|---|---|---|---|
| E01 | Plusieurs sociétés distinctes | Une installation (base) par société ; paramètres société dans `core.Societe` | Pas de multi-sociétés dans une même base (choix : isolation physique) | — |
| E02 | Hors ligne, atout principal | Serveur Django local par agence (SQLite ou PostgreSQL), aucun service distant requis | Paquet d'installation Windows locale à fournir | — |
| E03 | Petites, moyennes, grandes entreprises | Options activables (TVA, analytique, dépôts, droits) | Assistant de paramétrage à la création (E12) | — |
| E04–E05 | Agences dans plusieurs villes ; une société, serveurs locaux sans interconnexion | `core.Agence` (agence locale + autres agences), compte de liaison 185NN créé automatiquement et modifiable | — | `tests_rapport_commercial.test_agence_et_compte_de_liaison` |
| E06–E07 | Stocks, clients, créances, états par agence | Chaque serveur d'agence tient ses propres données ; balance âgée, états de stock, bilan | Bilan d'agence avec charges communes : D15 | tests reporting |
| E08 | Vue regroupée | — | **À faire** : export / import des données des agences et consolidation (P04–P06), avec date de fraîcheur | — |
| E09–E11 | Gros, détail, carton de 15 L, conditionnements | Unité de vente par article | **À faire** : conditionnements (unité de base et conversions, prix par présentation, conversion conservée sur la pièce, P07–P08) ; D01, D14 | — |
| E12 | Options dès la création, évolutives | Paramètres société modifiables | **À faire** : assistant de création | — |

## Tâche 2 : rapport commercial, liaisons, commandes, fiche de stock

| Id | Exigence (résumé) | Existant / adaptation | Écart restant | Preuve |
|---|---|---|---|---|
| E13 | Ventes du jour automatiques | `reporting.services.rapport_commercial` : factures (comptant, payée d'avance, en compte, client au comptant non soldé) et bons de commande | Sens de « en compte » / « à crédit » : D04 | `test_rapport_complet_du_jour` |
| E14 | Encaissements du jour | Reçus de la caisse du jour, nature (créance / avance) | — | idem |
| E15 | Sorties et dépenses | `OperationCaisse` : dépense, sortie pour agence, autre sortie, plus règlements fournisseurs | — | idem |
| E16 | Solde de caisse | Ouverture + entrées − sorties, contrôle contre le compte de trésorerie | — | idem |
| E17–E20 | Versement dans une autre agence, liaison, libellé « hors recettes », rubrique dédiée | **Côté agence qui encaisse** : `OperationCaisse HORS_RECETTE` (caisse au débit, liaison au crédit), rubrique du rapport, hors ventes propres. **Côté agence propriétaire** : `Reglement.agence_encaissement` + n° du reçu d'origine, sans caisse locale, liaison au débit, facture soldée, rubrique « versements reçus par d'autres agences » | Transmission entre agences manuelle (pas d'interconnexion) | `test_versement_recu_par_une_autre_agence` |
| P11–P12 | Hors-recettes dans la caisse d'exécution, affectation unique | Un reçu d'agence ne peut être saisi qu'une fois (agence + n° de reçu unique) ; pas d'agence locale | — | idem (doublon refusé) |
| E21 | Sorties pour d'autres agences | `OperationCaisse SORTIE_AGENCE` (liaison au débit) | — | `test_rapport_complet_du_jour` |
| E22 | Sources : factures, comptant / en compte / crédit | Voir E13 | D04 | idem |
| E23–E24 | Commandes comptant / en compte, payées avant enlèvement | Avance `Reglement.commande`, imputée à la facture issue de la commande à sa validation (pas de double encaissement) | Remboursement ou annulation d'avance : D07 | tests acomptes |
| E25 | BC livré le jour → facture le jour | Transformation BC → BL → facture en un clic ; le rapport indique « livré et facturé ce jour » | **Décision D06** : quel événement prouve la livraison avant la facturation automatique | — |
| E26 | Transformation ultérieure | Transformation possible à tout moment ; avance reportée sur la facture | — | tests transformation |
| P10 | Pas de double compte BC + facture | Le rapport sépare bons de commande (suivi) et factures (ventes) | — | `test_rapport_complet_du_jour` |
| E27–E31 | Fiche de stock : n° de BL, articles chargés sans quantité, saisie par le fichiste | `PointageFiche` : recherche du bon par numéro complet ou fin de numéro non ambiguë ; quantités de l'ordinateur jamais envoyées à la page du fichiste | — | `test_saisie_a_l_aveugle_par_le_fichiste` |
| E32–E33 | Rapprochement immédiat, écarts signalés | Statut conforme / écart dès l'enregistrement ; écarts, bons à pointer, stock de la fiche par article | — | `test_pointage_conforme_et_ecart` |
| P14 | Pas de deuxième sortie de stock | Le pointage ne crée aucun mouvement de stock | — | idem (stock ordinateur inchangé) |
| P15 | Rien qui permette de déduire l'attendu | Le fichiste voit seulement conforme / écart ; les quantités sont réservées aux contrôleurs | — | idem |
| P16 | Déclarations originales, corrections motivées | Une correction exige un motif ; la déclaration précédente est conservée (révision, date, fichiste, quantités) ; historique affiché aux contrôleurs | Versions successives d'un BL modifié : non gérées (un BL validé n'est pas modifiable) | `test_correction_avec_motif_et_historique` |
| P17–P18 | Mouvements ≠ comptage ; tous les flux | Le pointage couvre tout bon qui fait bouger le stock (BL, réception, transfert, entrée, sortie) ; l'inventaire physique est séparé | Ouverture de fiche (stock initial) : D11 | `test_bons_a_pointer` |

## Complément U4 : crédit, reçus et auteurs

| Id | Exigence (résumé) | Existant / adaptation | Écart restant | Preuve |
|---|---|---|---|---|
| E35 | Clients au comptant / à crédit | `Tiers.vente_credit` (coché par défaut). Un client au comptant reçoit un avertissement à la saisie et est signalé « non soldé » au rapport, jamais bloqué | Choix de bloquer : à décider | `test_client_au_comptant_signale` |
| E36 | Compte pour les clients à crédit | Compte tiers (collectif 411) et compte de liaison client | — | tests comptabilité |
| E37 | Plafond accordé | `plafond_credit` et code risque (avertir / bloquer), contrôlés sur le tiers payeur | Plafond global entre agences : D18 / P26 (non garanti hors ligne) | `tests_payeur.test_encours_controle_sur_le_payeur` |
| E38 | Délai par facture | `date_echeance` de chaque facture (délai du client, modifiable) ; balance âgée | Fin de mois, échéances multiples : D17 | tests reporting |
| E39–E41 | Reçu au versement, rattaché obligatoirement à une facture, détails conservés | `Reglement.facture` obligatoire pour un reçu de créance client (facture validée, du client ou de son payeur, pas d'avoir, montant ≤ reste dû) ; l'avance sur BC reste un circuit séparé ; reçu imprimable avec la facture réglée | Plusieurs factures par versement : D16 (un reçu par facture) | `commercial.tests` (reçu sans facture, dépassement), `test_recu_sans_facture_refuse` |
| E42–E44 | Auteur identifiable, visible à l'ouverture, traçabilité | `cree_par` posé côté serveur (jamais choisi dans une liste) sur pièces, reçus, écritures, opérations de caisse, inventaires, pointages ; `valide_par/le`, `annule_par/le` sur les pièces ; bandeau « Créé / Validé / Annulé / Modifié par » à l'ouverture ; journal des événements pour les modifications | Auteur sur les impressions : D20 | `test_auteurs_enregistres`, `test_correction_avec_motif_et_historique`, `core.tests_journal` |
| P22–P24 | Un reçu → une facture ; reste dû calculé ; avance ≠ reçu | Voir E39–E41 | — | idem |
| P25 | Auteur côté serveur, agence, site | Auteur et date côté serveur | Agence d'exécution sur chaque pièce : à ajouter avec la synchronisation | — |

## Propositions d'architecture non encore traitées

- **P01–P06, P20–P21 :** synchronisation, consolidation, transit interagences, sauvegarde centrale. C'est la prochaine tranche « vue regroupée » (E08) ; voir D03, D09, D13.
- **P07–P08 :** conditionnements (E09–E11).
- **P09 :** droits par agence et par rôle. Les autorisations par groupe existent ; il manque la dimension agence.

## Tests exécutés

Commande : `python manage.py test`. Résultat : **154 tests, tous réussis** (à la date de la livraison).
