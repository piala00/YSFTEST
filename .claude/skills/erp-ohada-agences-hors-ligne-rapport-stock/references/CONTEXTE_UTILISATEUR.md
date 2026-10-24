# Contexte métier fourni par l’utilisateur

Ce document restitue les demandes exprimées dans la conversation. Les propositions techniques sont dans les autres références. La date de constitution est le 24 octobre 2026 ; ce n’est pas la date certifiée de chaque message.

## U1 — Paramétrage, hors ligne et diversité des entreprises

L’utilisateur développe avec Claude un logiciel ERP OHADA. Plusieurs sociétés pourront utiliser le logiciel, en ligne ou hors ligne. Le fonctionnement hors ligne est présenté comme son principal atout.

Certaines sociétés ont plusieurs agences dans différentes villes et veulent consulter l’activité des autres agences, regrouper stocks, créances, analyses et bilan, tout en conservant une analyse par agence.

Le logiciel vise grandes, petites et moyennes entreprises. Les exemples décrivent des entreprises achetant en gros auprès d’usines puis revendant en gros, ainsi que des entreprises achetant auprès de grossistes et revendant en gros ou au détail. Une même petite structure peut posséder un magasin de gros et des boutiques de détail. Ne pas interpréter ces exemples comme une classification exhaustive ni comme l’interdiction du détail pour une grande entreprise.

L’utilisateur cite de l’huile en carton contenant 15 litres, vendable en carton, litres ou petits bidons, et des produits vendables en petits sacs. Les expressions transcrites « 500 litres » et « 500 kilos » restent ambiguës : ne pas les corriger silencieusement en 500 ml/500 g. Les exemples en 500 ml figurant ailleurs dans ce dossier sont des hypothèses pédagogiques à confirmer.

Le paramétrage initial doit adapter le logiciel à la société ; les options utiles doivent rester disponibles après le démarrage, lorsque l’activité évolue.

## U2 — Une société, plusieurs agences autonomes

Le cas détaillé concerne une seule et même société. Chaque agence possède actuellement son serveur Sage local. Les agences ne sont pas interconnectées. Chaque agence gère localement stock, clients et créances, et produit en fin de mois ses états, bilan et analyses.

Chaque jour, le « rapport commercial » comprend :

1. Les ventes du jour.
2. Les encaissements du jour.
3. Les sorties et dépenses journalières.
4. Le solde de caisse.

Un client rattaché à une agence peut effectuer un versement dans une autre agence pour régler son compte dans son agence d’origine. Ces opérations utilisent des comptes de liaison. Les encaissements pour le compte d’autres agences sont appelés « hors-recettes » et disposent d’un espace dans le rapport de caisse. Il existe aussi des sorties payées pour le compte d’autres agences.

Les noms d’agences sont affectés par la transcription orale. Les exemples utilisent Bertoua et Garoua-Boulaï comme repères contextuels ; leurs codes et libellés exacts doivent être configurés, jamais imposés comme limites du produit.

## U2 — Ventes, commandes et paiements

L’utilisateur souhaite automatiser le rapport à partir des pièces : factures, ventes comptant, ventes en compte ou à crédit, commandes comptant et commandes en compte.

Une commande peut être payée avant récupération de la marchandise. Une commande établie et livrée le même jour doit être transformée automatiquement en facture le même jour ; sinon la transformation intervient plus tard. Le traitement exact des livraisons partielles, retours, annulations et validations est à préciser. Le besoin n’autorise pas à présenter commande et facture comme deux ventes indépendantes.

## U2 — Fiche de stock et fichiste

L’utilisateur décrit ensuite le contrôle sur fiches papier, après avoir corrigé oralement sa première mention de fiches numériques. Le magasin remet le BL au fichiste ; celui-ci reporte les sorties article par article sur ses fiches. Des comptables rapprochent périodiquement, par exemple le samedi, le stock de gestion et les fiches du magasin.

Le besoin est un module intégré nommé « fiche de stock ». Le fichiste saisit la référence du BL déjà généré ; les articles se chargent automatiquement. Il ne doit pas voir les quantités attendues à l’ordinateur. Il saisit lui-même les quantités à partir de son document physique. Le logiciel rapproche sa saisie et les données de gestion, afin de détecter les différences sans attendre le rapprochement manuel de fin de semaine.

Cette saisie d’un document et un comptage physique sont deux preuves différentes. Le contrôle de stock complet doit couvrir les autres mouvements et une situation de départ ; ces compléments sont des propositions, pas des exigences détaillées déjà validées par l’utilisateur.

## U3 — Transmission et collaboration avec Claude

L’utilisateur demande un Skill contenant toutes ces informations pour Claude. Il précise avoir confié les deux mêmes tâches à Claude et souhaite une collaboration. Sa préférence exprimée dans ce fil est un ZIP unique. La collaboration doit donc s’appuyer sur un dossier commun d’exigences, des écarts identifiés et une transmission des résultats ; aucun canal direct avec sa session Claude n’est établi.

## U4 — Règlements clients, crédit et auteurs

L’utilisateur ajoute deux profils : clients achetant au comptant et clients achetant à crédit. Les clients à crédit ont un compte dans la société, un plafond de crédit accordé et un délai de règlement pour chaque facture. Lors de leurs versements, la société établit un reçu.

Pour améliorer le suivi des créances, la personne qui crée le reçu doit le rattacher à une facture : le reçu indique quelle facture il règle. L’utilisateur insiste sur « chaque reçu doit être rattaché à une facture ». Cette exigence concerne le règlement des factures à crédit ; elle doit être conciliée avec l’exigence antérieure d’avance avant livraison/facturation, sans inventer une facture. Cette formulation appartient à U4. La clarification U5 ci-dessous autorise explicitement plusieurs factures et l’attente de rattachement ; elle prévaut sur cette règle historique.

La personne ayant généré le reçu doit être identifiable. Cette exigence est étendue explicitement à tous les documents (factures, commandes, reçus), écritures et opérations. À l’ouverture d’un document, son auteur doit être affiché et les traces doivent être conservées. La forme exacte des informations et la séparation créateur/modificateur/valideur sont des propositions détaillées dans la référence dédiée.

## U5 — Fenêtres indépendantes et nouvelle saisie des règlements

L’utilisateur constate qu’ouvrir « ajouter/saisir un règlement » depuis une facture fait disparaître la facture. Il demande que chaque formulaire reste ouvert dans sa propre fenêtre : facture conservée en arrière-plan, règlement dans une autre fenêtre, possibilité de remettre chacun au premier plan, d’ouvrir plusieurs documents et de fermer uniquement celui choisi. Il ne demande pas un simple retour arrière remplaçant les écrans.

Le parcours demandé est Traitement → gestion de règlement → saisie de règlement client (vocabulaire utilisateur, casse et libellés définitifs à adapter). Le formulaire s’ouvre ; l’utilisateur choisit d’abord le client. Le logiciel propose automatiquement les factures non soldées de ce client. L’utilisateur choisit la facture ou les factures auxquelles affecter le règlement. S’il n’y en a pas, il peut enregistrer le règlement en attente de facture pour un rattachement ultérieur.

U5 remplace donc le blocage historique « un reçu, une facture obligatoire » par un règlement client avec zéro, une ou plusieurs factures affectées selon la situation. Les contrôles de montant et les règles comptables détaillées sont des propositions techniques distinctes, pas des champs d’en-tête déjà approuvés.

L’utilisateur annonce une feuille illustrant la saisie et précise que l’en-tête de l’ERP sera différent de celui du modèle Sage. Cette feuille n’a pas encore été reçue au moment de la version 2 ; aucun champ, position ni bouton non fourni n’est présenté comme confirmé.


## U6 — Captures et fonctionnement général des fenêtres
Deux captures Sage reçues le 24/10/2026. L’utilisateur précise un besoin transversal pour les fenêtres de comptabilité et gestion commerciale. Voir FONCTIONNEMENT_FENETRES_U6.md ; la réception des captures ne vaut pas validation d’un en-tête ERP identique.
