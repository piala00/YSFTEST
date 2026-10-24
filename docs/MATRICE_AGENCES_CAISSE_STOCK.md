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
| E02 | Hors ligne, atout principal | Serveur local par agence, aucun service distant requis. Paquet Windows sans Internet (Python inclus). **Réseau local (24/10) :** un poste serveur (4-DEMARRER-SERVEUR-RESEAU.bat : accès des autres postes, pare-feu, adresse affichée et raccourci « poste utilisateur », démarrage automatique facultatif) ; les autres postes utilisent leur navigateur avec leur propre compte. SQLite configuré pour plusieurs postes (attente de verrou, WAL), SQL Server conseillé au-delà de 3 ou 4 postes. | Synchronisation avec la direction : tranche « échanges entre agences » | — |
| E03 | Petites, moyennes, grandes entreprises | Options activables (TVA, analytique, dépôts, droits) | Assistant de paramétrage à la création (E12) | — |
| E04–E05 | Agences dans plusieurs villes ; une société, serveurs locaux sans interconnexion | `core.Agence` (agence locale + autres agences), compte de liaison 185NN créé automatiquement et modifiable | — | `tests_rapport_commercial.test_agence_et_compte_de_liaison` |
| E06–E07 | Stocks, clients, créances, états par agence | Chaque serveur d'agence tient ses propres données ; balance âgée, états de stock, bilan | Bilan d'agence avec charges communes : D15 | tests reporting |
| E08 | Vue regroupée | — | **À faire** : export / import des données des agences et consolidation (P04–P06), avec date de fraîcheur | — |
| E09–E11 | Gros, détail, carton de 15 L, conditionnements | **Décision de l'utilisateur (24/10) :** la vente au détail est réservée à un ou deux dépôts désignés (boutiques), approvisionnés par transfert, pour ne pas « brûler » le stock des magasins de gros. Option société « vente au détail réservée aux dépôts désignés », avec la liste des boutiques. Elle se règle dans les Paramètres de la société et dès l'installation Windows. Hors boutique, une vente au détail est refusée : quantité fractionnée ou article de détail, sur devis, commande, préparation, BL, retour ou facture ; le message indique les boutiques. **Conversion automatique au transfert (24/10) :** un article de gros (ex. « Huile carton 15 L ») désigne son article de détail (« Huile bouteille 1 L ») et le nombre d'unités (15). Un transfert vers un dépôt de vente au détail fait sortir les cartons du magasin et entrer les bouteilles en boutique, valeur conservée (coût bouteille = coût carton / 15, CMUP recalculé). L'annulation défait la conversion, et elle est refusée si elle rendait un stock négatif. Un dépôt de détail peut être créé et activé à tout moment (fiche dépôt ou Paramètres de la société). | Conditionnements (unité de base, carton / litre, prix par présentation, P07–P08) : reportés à la demande de l'utilisateur. Alors, le contrôle portera sur les unités de détail. | `tests_gros_detail` |
| E12 | Options dès la création, évolutives | Paramètres société modifiables | **À faire** : assistant de création | — |

## Tâche 2 : rapport commercial, liaisons, commandes, fiche de stock

| Id | Exigence (résumé) | Existant / adaptation | Écart restant | Preuve |
|---|---|---|---|---|
| E13 | Ventes du jour automatiques | `reporting.services.rapport_commercial` : factures (comptant, payée d'avance, **à crédit**, client au comptant non soldé) et bons de commande. **Décision de l'utilisateur (24/10) :** « en compte », « à terme » et « à crédit » sont synonymes, d'où le libellé unique « À crédit ». | — | `test_rapport_complet_du_jour` |
| E14 | Encaissements du jour | Reçus de la caisse du jour, nature (créance / avance) ; encaissements des autres trésoreries (banque, Mobile Money) montrés à part, par journal et par mode | — | `tests_revue_gpt.test_A07…` |
| E15 | Sorties et dépenses | `OperationCaisse` : dépense, sortie pour agence, autre sortie, plus règlements fournisseurs | — | idem |
| E16 | Solde de caisse | Ouverture + entrées − sorties, contrôle contre le compte de trésorerie ; virement et Mobile Money refusés sur une caisse espèces (compte 57) — A07 ; rapport d'un jour passé figé à sa date (règlements ultérieurs exclus) — A05 | Photographie de clôture et réouverture : D05 | `test_A05…`, `test_A07…` |
| E17–E20 | Versement dans une autre agence, liaison, libellé « hors recettes », rubrique dédiée | **Côté agence qui encaisse** : `OperationCaisse HORS_RECETTE` (caisse au débit, liaison au crédit), rubrique du rapport, hors ventes propres. **Côté agence propriétaire** : `Reglement.agence_encaissement` + n° du reçu d'origine, sans caisse locale, liaison au débit, facture soldée, rubrique « versements reçus par d'autres agences » | Transmission entre agences manuelle (pas d'interconnexion) | `test_versement_recu_par_une_autre_agence` |
| P11–P12 | Hors-recettes dans la caisse d'exécution, affectation unique | Un reçu d'agence ne peut être saisi qu'une fois (agence + n° de reçu unique) ; pas d'agence locale | — | idem (doublon refusé) |
| E21 | Sorties pour d'autres agences | `OperationCaisse SORTIE_AGENCE` (liaison au débit) | — | `test_rapport_complet_du_jour` |
| E22 | Sources : factures, comptant / en compte / crédit | Voir E13 | D04 | idem |
| E23–E24 | Commandes comptant / en compte, payées avant enlèvement | Avance `Reglement.commande`, imputée à la facture issue de la commande à sa validation (pas de double encaissement) | Remboursement ou annulation d'avance : D07 | tests acomptes |
| E25 | BC livré → facture le jour même | **Décision de l'utilisateur (24/10) :** c'est le magasin qui transforme le BC en BL, et la validation du BL prouve la livraison. À cette validation, la facture des quantités livrées est établie automatiquement et validée, avec imputation des avances. Option de la fiche Société : validée, brouillon ou aucune. Si la facture ne peut pas être validée (plafond bloquant), elle reste en brouillon et la livraison reste validée. | Droits du magasin à configurer par groupe (transformation BC → BL) | `test_chaine_devis_commande_livraison_facture`, `test_R13…`, `test_acompte_impute…` |
| E26 | Transformation ultérieure | Transformation possible à tout moment ; avance reportée sur la facture | — | tests transformation |
| P10 | Pas de double compte BC + facture | Le rapport sépare bons de commande (suivi) et factures (ventes) | — | `test_rapport_complet_du_jour` |
| E27–E31 | Fiche de stock : n° de BL, articles chargés sans quantité, saisie par le fichiste | `PointageFiche` : recherche du bon par numéro complet ou fin de numéro non ambiguë ; quantités de l'ordinateur jamais envoyées à la page du fichiste | — | `test_saisie_a_l_aveugle_par_le_fichiste` |
| E32–E33 | Rapprochement immédiat, écarts signalés | Statut conforme / écart dès l'enregistrement ; écarts, bons à pointer ; alerte des bons non pointés au-delà d'un délai réglable (paramètres société) — R18 | — | `test_pointage_conforme_et_ecart`, `test_R18…` |
| P14 | Pas de deuxième sortie de stock | Le pointage ne crée aucun mouvement de stock | — | idem (stock ordinateur inchangé) |
| P15 | Rien qui permette de déduire l'attendu | Écran : conforme / écart seulement. API : listes de pièces et de tiers filtrées par droits effectifs (un type interdit n'apparaît ni en liste ni en détail) ; états de l'API (balance, bilan, balance âgée, tableau de bord) soumis aux droits des pages — A01 | Exports d'états à revoir avec le même contrôle | `test_A01…` |
| P16 | Déclarations originales, corrections motivées | Vide ≠ 0 (le zéro doit être saisi), négatif refusé, 3 décimales au plus, contrôlés dans le modèle — A02/A03 ; correction motivée ; l'ancienne déclaration garde SON fichiste, le correcteur est noté à part (`corrige_par`) — A04 ; historique visible des contrôleurs | Versions d'un BL modifié : non gérées (BL validé non modifiable) | `test_A02…`, `test_A03…`, `test_A04…` |
| P17–P18 | Mouvements ≠ comptage ; tous les flux ; registre indépendant | Le pointage couvre tout bon qui fait bouger le stock ; la fiche ne contient que les déclarations du fichiste (et les inventaires physiques) : les bons non pointés sont montrés « en attente » avec un solde projeté distinct, jamais recopiés — A06 | **Décision de l'utilisateur (24/10) :** la fiche commence à l'entrée des stocks dans le logiciel (champ « Début de la fiche de stock » du dépôt, vide = première entrée ; le stock antérieur sert d'ouverture) — `test_debut_de_la_fiche…` | `test_A06…` |

## Complément U4 : crédit, reçus et auteurs

| Id | Exigence (résumé) | Existant / adaptation | Écart restant | Preuve |
|---|---|---|---|---|
| E35 | Clients au comptant / à crédit | `Tiers.vente_credit` (coché par défaut). Un client au comptant reçoit un avertissement à la saisie et est signalé « non soldé » au rapport, jamais bloqué | Choix de bloquer : à décider | `test_client_au_comptant_signale` |
| E36 | Compte pour les clients à crédit | Compte tiers (collectif 411) et compte de liaison client | — | tests comptabilité |
| E37 | Plafond accordé | `plafond_credit` et code risque (avertir / bloquer), contrôlés sur le tiers payeur | Plafond global entre agences : D18 / P26 (non garanti hors ligne) | `tests_payeur.test_encours_controle_sur_le_payeur` |
| E38 | Délai par facture | `date_echeance` de chaque facture (délai du client, modifiable) ; balance âgée | Fin de mois, échéances multiples : D17 | tests reporting |
| E39–E41 | Reçu rattaché à des factures, détails conservés | **Décision de l'utilisateur (24/10) :** un reçu se rattache à une ou plusieurs factures du client (ou de son payeur), réglées de la plus ancienne à la plus récente, totalement ou partiellement. Le reste éventuel est **en attente de rattachement** à une prochaine facture (bouton « Rattacher » sur le reçu, rappel sur la facture), et l'auteur du rattachement est conservé. Une facture déjà soldée, d'un autre client ou un avoir est refusé ; l'avance sur BC reste un circuit distinct. | — | `test_reglement_impute_et_comptabilise`, `test_reste_du_recu_en_attente_puis_rattache`, `test_formulaire_recu_plusieurs_factures_et_rattachement` |
| E42–E44 | Auteur identifiable, visible à l'ouverture, traçabilité | `cree_par` posé côté serveur (jamais choisi dans une liste) sur pièces, reçus, écritures, opérations de caisse, inventaires, pointages ; `valide_par/le`, `annule_par/le` sur les pièces ; bandeau « Créé / Validé / Annulé / Modifié par » à l'ouverture ; journal des événements pour les modifications | Auteur sur les impressions : D20 | `test_auteurs_enregistres`, `test_correction_avec_motif_et_historique`, `core.tests_journal` |
| P22–P24 | Un reçu → une facture ; reste dû calculé ; avance ≠ reçu | Voir E39–E41 | — | idem |
| P25 | Auteur côté serveur, agence, site | Auteur et date côté serveur | Agence d'exécution sur chaque pièce : à ajouter avec la synchronisation | — |

## Propositions d'architecture non encore traitées

- **P01–P06, P20–P21 :** synchronisation, consolidation, transit interagences, sauvegarde centrale. C'est la prochaine tranche « vue regroupée » (E08) ; voir D03, D09, D13.
- **P07–P08 :** conditionnements (E09–E11).
- **P09 :** droits par agence et par rôle. Les autorisations par groupe existent ; il manque la dimension agence.

## Tests exécutés

Commande : `python manage.py test`. Résultat : **173 tests, tous réussis** (dont les tests de la revue GPT du 24/10) (à la date de la livraison).


## Complément U5 / U6 : fenêtres et règlements (skill v3)

| Exigence | Réalisation | Preuve |
|---|---|---|
| Fenêtres indépendantes (facture → règlement, et tout autre écran) | Un lien vers un autre écran ouvre une nouvelle fenêtre interne ; la fenêtre d'origine reste ouverte. Le même écran et les sous-pages du même objet restent dans la même fenêtre. | Essai navigateur : 2 fenêtres après « Saisir un règlement » |
| Saisie non enregistrée protégée | Fermer une fenêtre dont le formulaire est modifié demande confirmation (revenir / abandonner) ; quitter la page aussi | Essai navigateur |
| Actualisation après règlement | Les fenêtres ouvertes sur les factures réglées ou rattachées se rechargent, sauf si elles contiennent une saisie en cours | Essai navigateur |
| Saisie des règlements guidée par le client | Choix du tiers, factures non soldées proposées, sélection multiple avec montant imputé, règlement « en attente de facture » si aucune ; liste des règlements du tiers, filtres et totaux | `test_formulaire_recu_plusieurs_factures_et_rattachement`, `test_reglement_en_attente_de_facture`, `test_montants_imputes_saisis_par_facture` |

## Complément U7 : synchronisation du dossier d'origine, puis bascule (skill v4)

| Exigence | Réalisation | Preuve |
|---|---|---|
| E53 — Synchronisation complète (gestion commerciale et comptabilité) | Lecture seule de la base SQL Server (SELECT uniquement, ApplicationIntent=ReadOnly) ou CSV ; passages répétables qui reportent créations, modifications et suppressions ; chaque passage consigné (lot) ; synchronisation automatique horaire possible | `test_synchronisation_incrementale`, `test_copie_synchronisee_puis_bascule`, `test_synchronisation_planifiee` ; essai sur base fictive SQL Server |
| E54 — Comptabilité et analytique | Plan comptable, plan tiers, journaux, taxes, plans et sections analytiques, écritures ligne à ligne avec lettrage et ventilations (premier plan) | `test_comptabilite_reprise` |
| E55 — Autonomie après la bascule | Pendant la transition, saisies refusées dans l'ERP (pas de doublon) ; bascule confirmée (BASCULER) après une dernière synchronisation conforme ; ensuite synchronisation arrêtée et saisie ouverte | `test_ecran_en_copie_synchronisee_puis_bascule`, `test_continuer_dans_l_erp` |
| Limites | Non synchronisés : pièces jointes et PDF, utilisateurs et droits, gammes, lots et séries, budgets, fabrication ; colonnes « à confirmer » sur une version antérieure à V12.20 | — |
