# GPT — simulation métier, propriétaires et conséquences comptables — 30 octobre 2026

Demande propriétaire : transits/correspondances et transvasements, colis perdus/abîmés/sans trace, garage interne,
stock de pièces et imputation aux véhicules, comptes de propriétaires tiers (sans capital), retraits en espèces.
Commission évoquée à 15 %, base non confirmée : recettes ou résultat. Ces deux hypothèses sont distinctes.

## Réutilisation et décisions

PR #19 recherche progressive VIP/Classique, dépendant de #17. Ce lot conserve les PR #11–#17 : licences,
saisie rapide et contacts, stockage protégé, administration, sauvegardes et dossiers de simulation importables.
Moteurs Billet/Troncon/Incident, AchatMagasin/sortir/OrdreReparation, Decompte/DemandeRetrait réutilisés.
Une portion = un départ, agences hors ligne ; cette démonstration rassemble leurs événements dans un dossier fictif,
elle ne simule pas une communication en temps réel entre agences déconnectées.

## Fonctionnement

- Nombre exact de départs par journée pour TOUTES les agences (250 signifie 250 au total). Planning fictif de portions
  de six heures, jusqu'à quatre par véhicule ; flotte ajustée si nécessaire. Un départ n'est jamais rouvert.
- Profil complet optionnel, activé par défaut dans Administration > Simulation : correspondance payée une fois,
  placement gratuit du tronçon, montée intermédiaire, reconnaissance de chaque portion, transvasement et dépannage.
- Transvasement : répartition des produits billets, bagages, colis et fret déjà constatés. Le port dû reconnu plus tard
  à la livraison est réparti entre véhicule initial et secours selon le même pourcentage ; aucun second encaissement.
  Un seul transvasement par départ et pas de réattribution automatique des sièges, conformément au lot précédent.
- Colis : incident perdu/endommagé/sans trace avec lieu et constat, résolution tracée, chargement/livraison bloqués
  tant que l'incident reste ouvert. Un signalement n'a pas d'écriture ; indemnité soumise à permission et autorisation,
  puis paiement espèces équilibré, réémission idempotente. Montants fictifs explicites, aucun tarif d'indemnisation inventé.
  Les nouvelles déclarations sont locales ; leur échange automatique entre agences n'est pas ajouté par ce lot.
- Garage interne : achat pour stock (actif), achat directement consommé par véhicule (charge), consommation de stock
  en réparation (stock vers charge), matériel durable (classe 2), mécanicien interne pour mémoire sans double paie.
  Il n'est pas créé de vente ni de TVA interne fictive entre services d'une même société.
- Partenaire : tiers distinct du capital ; un propriétaire peut avoir plusieurs véhicules. Assiette commission explicite
  sur le contrat, historique conservé sur recettes ; le formulaire d'un nouveau contrat propose « À confirmer ».
  Un contrat avec cette base ne peut être activé. La simulation compare 15 % recettes et 15 % marge SIGNÉE ; une seule
  hypothèse fictive est comptabilisée par contrat, aucune différence comparative n'est comptabilisée deux fois.
  La répartition des pertes dans l'hypothèse marge reste également à convenir pour les vrais contrats.
- Le « salaire propriétaire » de 100 000 est un retrait de son compte, plafonné au disponible, jamais un fixe ajouté au
  résultat ni une paie salariée. Décompte et retrait restent des écritures distinctes. Réémission depuis un objet périmé
  du retrait refusée après verrouillage ; un règlement ne peut viser le décompte d'un autre propriétaire.

## Preuves fournies

Chaque cas critique conserve les numéros de pièces et les IDs de lignes générales validées dans un rapport JSON,
avec débit/crédit, compte, véhicule et tiers. Bilan lisible et JSON sont inclus dans .erpsim, nettoyé des identifiants
et licences d'origine, avec empreintes des rapports vérifiées à l'import. Critères et temps journalier mesurés conservés.
Une simulation courte n'est pas une statistique de fréquence réelle des incidents, ni un benchmark du mois complet.

Tests locaux : syntaxe Python/JS, recherche par préfixes et 12 tests de dossiers portables effectivement exécutés.
Django absent localement : exécution des tests fonctionnels et compilations Windows via CI, résultats dans la PR.
Un essai 250 départs à 5 % de remplissage est prévu dans le workflow, avec rapport et exemple importable.

Aucune fusion, aucun déploiement et aucune donnée de production. Clé publique d'éditeur toujours manquante : le
programme client demeure en essai ; ne jamais incorporer le coffre privé d'émission au poste client.
