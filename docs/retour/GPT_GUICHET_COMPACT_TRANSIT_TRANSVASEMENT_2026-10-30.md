# GPT — Guichet compact, transit et transvasement — 30/10/2026

Demande du propriétaire : réduire réellement le nouveau formulaire, rendre le transit et le transvasement accessibles,
livrer Transport et l'outil de licences téléchargeables. L'autorisation couvre développement, tests, PR et compilation ;
aucune fusion, aucun déploiement ni aucune écriture de production.

## Réutilisation

Branche empilée sur PR #16 f9cd26d : toutes les améliorations des PR #11–#16 sont conservées (licences simplifiées,
contacts téléphoniques, double soumission, stockage protégé, administration, dossiers de simulation, sauvegardes complètes).
Troncon.affecter, Billet.vendre et Incident.transborder restent les moteurs métier, sans nouvelle comptabilisation inventée.
La décision du propriétaire du 28/10 est conservée : agences hors ligne, une portion = un départ, consolidation au siège.

## Changements

- Formulaire en colonne, 340 px maximum ; fenêtre MDI initiale de 380 px, hauteur plafonnée à l'espace disponible.
  Déplacement/redimensionnement manuel et agrandissement restent possibles. Même dimension initiale pour les colis.
- Vente courante : départ, téléphone, nom, CNI, siège, prix, paiement. Bagages et autres réglages repliés.
- Billetterie > Billets en transit / correspondances : sélectionner le départ de l'agence puis vendre sur cette portion,
  vendre depuis un arrêt intermédiaire ou vendre un voyage avec changement de véhicule. Pour un billet déjà payé,
  placement du tronçon en attente et impression, sans nouvelle pièce ni second encaissement. Billets interagences reçus
  par les échanges existants ; aucun accès en direct à une autre agence hors ligne n'est prétendu.
- Mode montée intermédiaire : arrêt de montée obligatoire et valide, sièges réutilisables après un arrêt ; aucune réouverture
  d'un départ déjà parti. Mode correspondance : destination au-delà du premier terminus, second véhicule facultatif.
- Impression : chaque portion, véhicule/date/siège, ou mention « à choisir » à la gare de changement. Le prochain passager
  conserve le départ et le type de vente, jamais l'identité ni le siège du précédent.
- Billetterie > Transvasement (changement de car) : voyage parti/arrivé, secours, part restante, lieu, motif. Réutilise l'OD
  et l'historique du départ. La même demande réémise retrouve l'incident ; une demande différente sur le même départ est
  refusée pour éviter de répartir deux fois la recette initiale. Les transvasements successifs nécessitent une conception
  spécifique avant ouverture de cette possibilité. Les sièges du secours ne sont pas réattribués automatiquement.
- Droits serveur des nouvelles commandes, y compris anciens POST de fiche départ ; refus des départs distants et sièges
  hors plage. Verrouillage du départ pour les incidents et du tronçon pour le placement.

## Validation

Les tests Django sont exécutés par GitHub Actions (Django absent de l'atelier local). Contrôles locaux : syntaxe Python,
JavaScript et scénarios de dimensions du code livré. Suite intégrale SQLite/SQL Server, compilation native/Windows,
installateur/service et outil propriétaire en CI ; résultats et liens ajoutés à la PR après exécution.

La clé publique d'éditeur n'a pas été fournie : CLES reste vide. L'outil propriétaire conserve les améliorations #11 ;
le client reste utilisable en essai, l'activation commerciale personnalisée attend la seule clé publique. Ne jamais
placer le coffre privé de l'éditeur dans une installation cliente.
