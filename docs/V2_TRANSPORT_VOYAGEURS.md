# Version 2 — Transport interurbain de voyageurs

Logiciel de gestion et de comptabilité pour les agences de voyage africaines au sens courant au Cameroun : les
**compagnies de transport interurbain par car**, qui exercent souvent trois activités à la fois :

1. **Billetterie** : vente des places sur les départs des lignes (Douala → Yaoundé…) ;
2. **Colis et courrier** : envois confiés en gare, remis au destinataire dans la gare d'arrivée ;
3. **Logistique** : fret (marchandises) et gestion de la flotte.

Tout est lié à la **comptabilité OHADA** commune : chaque opération passe son écriture au moment où elle a lieu.

## Choix de construction

- **Même socle que la version 1** (décision de l'utilisateur) : nouveau logiciel « Transport de voyageurs » à côté
  de la Gestion commerciale, de la Comptabilité et du Reporting. Il reprend le plan comptable, les journaux, les
  clients en compte, la caisse, les règlements, les agences, les droits d'accès, le bureau à fenêtres, l'installation
  Windows, le réseau local et la sauvegarde.
- **Activité de la société** (Paramètres société, ou question de l'installateur) : *Commerce*, *Transport de
  voyageurs* ou *Les deux*. Le portail ne propose que les logiciels utiles (en transport, le logiciel Transport en premier).

## Données de base (menu Structure)

| Fiche | Contenu | Lien comptable |
|---|---|---|
| Gare | code, nom, ville, agence, journal de caisse | section analytique « G-code » (plan *Gares*) |
| Ligne | gare de départ → gare d'arrivée, distance, durée, prix du billet, tarif colis (forfait, prix au kg) | — |
| Véhicule | immatriculation, désignation, type (car, minibus, camion), places | section analytique « V-immatriculation » (plan *Véhicules*) |
| Chauffeur | nom, téléphone, n° de permis | — |
| Paramètres transport | comptes de produits, compte des contre-remboursements, taxes, retenue d'annulation | — |

## Processus

### Billetterie
1. **Programmer un départ** : ligne, date, heure, véhicule, chauffeur ; places = celles du véhicule (modifiable).
2. **Vendre un billet** (guichet) : départ, voyageur, téléphone, pièce d'identité, siège (plan des sièges cliquable),
   prix (celui de la ligne par défaut), paiement *Espèces*, *Mobile Money* ou *En compte* (entreprise, administration).
   Contrôles : départ programmé, places libres, siège libre, client en compte autorisé au crédit.
3. **Reporter** un billet sur un autre départ de la même ligne : sans frais, sans écriture.
4. **Annuler** un billet vendu : remboursement du prix moins la **retenue** (pourcentage par défaut, modifiable).
5. **Départ effectué** : les voyageurs passent *embarqués*, les colis chargés *en route* ; plus de vente sur ce départ.
6. **Arrivée** : les colis deviennent disponibles en gare d'arrivée.
7. **Manifeste** imprimable : voyageurs (siège, nom, pièce, téléphone) et envois chargés, signatures.

### Colis, courrier et fret
1. **Enregistrer** : nature (colis, courrier, fret), gares, expéditeur, destinataire, contenu, pièces, poids, valeur
   déclarée, prix (tarif de la ligne par défaut), **port payé** ou **port dû**, **contre-remboursement** éventuel.
   Un **code de retrait** à 6 chiffres est généré ; l'expéditeur le communique au destinataire. Bordereau imprimable.
2. **Charger** sur un départ allant de la gare de départ à la gare d'arrivée.
3. **Remettre** au destinataire : code de retrait obligatoire, nom et pièce de la personne qui retire ; encaissement
   du port dû et du contre-remboursement.
4. **Reverser** le contre-remboursement à l'expéditeur.
5. **Annuler** un envoi non chargé : remboursement du port payé.

### Logistique (hypothèse à confirmer)
- **Fret** : envoi de nature « fret », produit sur un compte distinct.
- **Flotte** : dépenses de véhicules (carburant, entretien, réparation, péage, frais de route, assurance), rattachées
  au véhicule (section analytique) et, pour les frais de route, au départ.

## Schémas comptables

Comptes créés au premier usage, **à valider par l'expert-comptable** et modifiables dans *Paramètres transport*.

| Opération | Débit | Crédit |
|---|---|---|
| Billet au comptant | Caisse de la gare (5711…) | 70611 Transport de voyageurs (section de la gare) |
| Billet en compte | 411 client (journal VT) | 70611 |
| Annulation (remboursement) | 70611 (prix − retenue) | Caisse ou 411 — la retenue reste acquise |
| Colis / courrier port payé | Caisse de la gare de départ (ou 411) | 70612 Colis et courrier (70613 pour le fret) |
| Colis port dû, à la remise | Caisse de la gare d'arrivée | 70612 / 70613 |
| Contre-remboursement encaissé | Caisse de la gare d'arrivée | 4718 Envois contre remboursement à reverser |
| Contre-remboursement reversé | 4718 | Caisse de la gare de départ |
| Dépense de véhicule | 6053 carburant, 624 entretien et réparation, 625 assurance, autre compte au choix (section du véhicule) | Caisse |

**Taxes** : aucune par défaut (comme la version 1). Une taxe peut être choisie pour les billets et pour les colis ;
les prix étant toutes taxes comprises, l'écriture sépare alors le hors taxe et la taxe.

## États
- **Recette journalière par gare** : billets encaissés, remboursements, colis au départ, port dû et
  contre-remboursements encaissés, contre-remboursements reversés, net de caisse ; billets en compte à part.
- **Rentabilité** par ligne, par véhicule ou par départ : départs, voyageurs, remplissage, recettes billets et colis,
  dépenses, marge.
- Comptabilité : balance, grand livre, analytique par gare et par véhicule (logiciel Comptabilité).

## Points à confirmer avec l'utilisateur

1. **Logistique** : précisé par l'utilisateur (25/10) — le fret est rare, les colis sont l'activité secondaire ;
   le fret reste une nature d'envoi, sans module dédié.
2. **Gares dans plusieurs agences** (serveurs séparés hors ligne) : **fait** (25/10) — échanges par fichiers signés
   envoyés par WhatsApp ou Telegram, consolidation au siège, colis remis dans une autre agence avec comptes de
   liaison 185 ; voir `docs/ECHANGES_AGENCES.md`.
3. **Comptabilisation des billets vendus d'avance** : produit constaté à la vente (actuel) ; à la clôture, les billets
   d'un départ de l'exercice suivant pourraient passer en produits constatés d'avance (477).
4. **Fiscalité du transport de voyageurs** (TVA, droits, taxes communales, assurance voyageurs) : rien n'est imposé ;
   à vérifier avec le CGI et l'expert-comptable avant de régler une taxe.
5. **Billets ouverts** (sans date), **tarifs enfants / réductions**, **bagages en supplément**, **arrêts
   intermédiaires** (Douala → Édéa → Yaoundé) : non traités dans cette première tranche.
6. **Mobile Money** : aujourd'hui encaissé dans la caisse de la gare ; un journal Mobile Money par gare est possible.
7. **Contrôle du chef de gare** : clôture de caisse par guichetier, comme la fiche de stock de la version 1 ?

## Tests
`python manage.py test apps.transport` : 22 tests (comptabilisation de chaque opération, contrôles, cycle complet
départ → arrivée → remise, écrans, portail selon l'activité). Suite complète : 206 tests.


## Recettes et dépenses par véhicule (26/10)

Le véritable défi du métier : **chaque véhicule a son compte**, dans toutes les agences.

- **Le véhicule est une dimension des écritures**, comme le tiers : chaque ligne d'écriture peut porter un véhicule
  (saisie comptable comprise). D'où le **grand-livre des véhicules** et la **balance des véhicules** (recettes
  voyageurs, colis, autres ; carburant, entretien, autres dépenses ; résultat), dans le logiciel Transport (Etat ›
  Comptes des véhicules) et dans la Comptabilité (Etat › Etats des véhicules). Au siège, toutes les agences sont comprises.
- **Fiche du véhicule** : type, places, propriétaire (société ou partenaire), carte grise, mise en service, échéances
  d'assurance et de visite technique (alerte 30 jours avant), recettes, dépenses, résultat, départs, remplissage.
- **La recette est constatée au départ du véhicule, pas à la vente** :

| Opération | Débit | Crédit |
|---|---|---|
| Vente du billet | Caisse (ou 411 client) | 41911 Billets vendus, voyage à effectuer |
| Départ du véhicule | 41911 (part de chaque voyageur) | 70611 Transport de voyageurs **sur le véhicule** (+ taxe si réglée) |
| Annulation avant le voyage | 41911 (prix) | Caisse (remboursé) / 70611 (retenue) |

- **Correspondance** (ex. Douala → Garoua-Boulaï avec changement à Bertoua) : le billet comprend un **tronçon par
  véhicule**. Le prix est partagé au prorata des tarifs des tronçons (Douala → Bertoua, Bertoua → Garoua-Boulaï), sinon
  des distances, sinon à parts égales. Chaque véhicule reçoit sa part à son départ. Le véhicule de correspondance se
  choisit à la vente ou **à Bertoua** (fiche du départ › « Voyageurs en correspondance à placer »). Les places sont
  comptées tronçon par tronçon.
- **Correspondance dans une autre agence** (Bertoua a son propre serveur) : Bertoua place le voyageur et fait partir
  son car ; la part va à son véhicule (D 185 Douala / C 70611 véhicule de Bertoua). Douala l'apprend par le siège et
  solde l'avance du voyageur (D 41911 / C 185 Bertoua). Au siège, les liaisons s'annulent, l'avance est soldée et
  chaque véhicule a sa recette (vérifié sur quatre bases séparées : `apps/echanges/scenario.py`).

Points à confirmer :
- Comptes **41911** (avance du voyageur) et **70611** : à valider par l'expert-comptable.
- **Colis** : leur recette reste constatée à l'enregistrement, sans véhicule. Faut-il aussi l'attribuer au véhicule
  qui les transporte (constatée au départ, comme les billets) ?
- **Véhicules de partenaires** : le propriétaire est noté sur la fiche ; faut-il calculer et payer sa part
  (reversement au propriétaire, commission de l'agence) ?
- Billets vendus avant cette version : leur recette a déjà été constatée à la vente ; ils ne passent pas par 41911.

## Un logiciel par service, regroupement automatique (26/10)

Chaque service travaille dans **son logiciel**, selon ses droits (Fichier › Autorisations d'accès : accès par
utilisateur et par logiciel, droits par menu). Un utilisateur ne voit sur le portail que ses logiciels ; s'il n'en a
qu'un (ex. un guichetier), il y arrive directement.

| Logiciel | Qui | Ce qu'on y fait |
|---|---|---|
| **Billetterie** | guichetiers, chef de gare | départs, vente des billets, correspondances, annulations, reports, recette du guichet |
| **Colis et expéditions** | agents colis | enregistrement (colis, courrier, fret), chargement, arrivée, remise contre code, contre-remboursements |
| **Garage** | chef de garage, mécaniciens | fiches véhicules, pleins de carburant (litres, compteur, consommation), ordres de réparation (pièces, main d'œuvre extérieure ou interne, fournisseur), autres dépenses, papiers (assurance, visite) |
| **Personnel et paie** | gestionnaire du personnel | employés par service et par agence, véhicule affecté, rubriques de paie paramétrables, avances, paie du mois, bulletins, paiement |
| **Direction de l'agence** | chef d'agence | **rapport journalier de toute l'agence**, comptes des véhicules, rentabilité, lignes et tarifs, paramètres, échanges |
| Comptabilité, Reporting | comptables, direction | tout arrive déjà comptabilisé |

**Tout se regroupe sur chaque véhicule, automatiquement :**

| Fait (service) | Écriture | Sur le véhicule |
|---|---|---|
| Départ du car (billetterie) | D 41911 / C 70611 | recette des voyageurs (part de chaque billet) |
| Départ du car (colis chargés, port payé) | D 41912 / C 70612 ou 70613 | recette des colis transportés |
| Remise d'un colis en port dû (colis) | D caisse / C 70612 | recette du car qui l'a transporté |
| Plein (garage) | D 6053 / C caisse ou 401 station | carburant |
| Réparation terminée (garage) | D 624 / C caisse ou 401 fournisseur | pièces et main d'œuvre extérieure (la main d'œuvre interne est dans la paie) |
| Paie validée (personnel) | D 661, 664… / C 422, 431… | salaire et charges du chauffeur affecté au véhicule |

Le **rapport journalier** (Direction › Etat) donne pour la journée : la billetterie par guichetier (espèces, Mobile
Money, en compte, remboursements), les colis (enregistrés, remis, contre-remboursements), **chaque véhicule** (voyages,
voyageurs, colis, litres, recettes, carburant, réparations, personnel, autres dépenses, résultat), le garage et les
caisses. La **fiche du véhicule** et la **balance des véhicules** donnent la même vue sur une période ; au siège, toutes
les agences sont comprises (écritures, pleins et réparations remontent par les échanges).

**Paie** : le logiciel n'impose aucun taux. Créez les rubriques de la société (cotisations sociales, impôts sur salaire,
primes…) avec les taux et plafonds fixés par l'expert-comptable.

Points à confirmer :
- Pièces de rechange : achat direct sur la réparation (actuel) ou **magasin de pièces** avec stock (Gestion commerciale) ?
- Comptes proposés (6053 carburant, 624 réparations, 41912 colis encaissés d'avance, 661/664/422/431 paie) : à valider.
- ~~Clôture de caisse par guichetier~~ : faite (étape P1 ci-dessous).

## Étapes P0 à P4 de l'audit du skill transport

Plan dans `docs/AUDIT_SKILL_TRANSPORT_2026-10-26.md`. Les comptes proposés restent **à valider par l'expert-comptable**.

**P0 — Corrections.** Numéros préfixés par le code de l'agence (`DLA-BIL2026-000001`) dès que les échanges sont
configurés : plus de collision entre agences. Billet payé en Mobile Money porté au journal Mobile Money de la gare.

**P1 — Caisses et clôtures.** Session de caisse par guichetier ou agent colis (fonds de départ, encaissements,
comptage, écart), approuvée par un autre utilisateur ; écart en 658 / 421 (manquant) ou 758 (excédent). Transferts de
fonds via 585 (en transit jusqu'à la réception). Clôture de la journée par service et pour l'agence, refusée tant
qu'il reste un point bloquant (caisse ouverte ou non approuvée) ; les autres anomalies sont listées dans le rapport.
Option « caisse ouverte obligatoire pour encaisser » dans les Paramètres transport.

**P2 — Exploitation.** Convoyeur, kilomètres au départ et à l'arrivée, refus d'un véhicule déjà programmé à la même
heure ou encore sur la route, refus du départ si l'assurance ou la visite technique est expirée (réglable). Avance de
mission à l'équipage (47121), justifiée au retour (péage 638, frais de route 6181, carburant, dépannage 624) ; le
voyage se clôture quand l'avance est justifiée.

**P3 — Véhicules des partenaires** (Direction › Traitement › Véhicules des partenaires).

| Modèle de contrat | Ce qui revient au propriétaire sur la période |
|---|---|
| Commission sur recettes | recettes du véhicule − commission de l'agence (%) − dépenses mises à sa charge |
| Location forfaitaire | forfait par jour, ou par mois au prorata des jours − dépenses mises à sa charge |

- Le contrat dit quelles dépenses sont à la charge du propriétaire : carburant, réparations, équipage, péages et
  frais de route, autres. Un **avenant** crée une nouvelle version datée ; l'ancienne reste dans l'historique.
- Le **décompte** se calcule depuis les comptes du véhicule (au siège, une fois les fichiers des agences importés) et
  garde la version du contrat appliquée. Une période ne se décompte qu'une fois.
- À l'approbation : D 622 (sur le véhicule) / C 401 du partenaire. Si le résultat est négatif, le propriétaire doit la
  différence à l'agence (sens inverse).
- Les **règlements** (D 401 / C caisse ou banque) peuvent être partiels. Le **relevé** montre le dû, les paiements et
  le reste à payer.
- Le résultat du véhicule pour l'agence, le décompte du partenaire et le solde de son compte restent distincts.

**P4 — Billetterie avancée.**
- **Arrêts intermédiaires** : sur la fiche de la ligne, codes des gares desservies en route (ex. `EDE, PKL`). On peut
  vendre un billet qui monte ou descend à un arrêt. Le siège est compté **par tronçon** : libéré à Edéa, il se revend
  pour Edéa → Yaoundé. Le prix vient de la ligne-tarif entre les deux gares, sinon il se saisit. Les arrêts sont
  transmis aux agences.
- **Embarquement sur la liste** (fiche du départ) : le contrôleur coche les voyageurs à bord, puis valide la liste.
  Au départ du car, les non-cochés sont **absents** : pas de recette pour ce car, avance du voyageur gardée (41911),
  billet à reporter ou à rembourser (signalé au rapport). Sans liste validée, tout le monde est considéré parti (comme
  avant). Le manifeste imprimé a une case « à bord » et la montée et la descente de chaque voyageur.
- **Remboursement séparé de l'annulation** : à l'annulation, choisir « rembourser maintenant » (comme avant) ou
  « autoriser seulement ». Le remboursement autorisé est une dette envers le voyageur (41913, proposé). Il se paie
  ensuite en caisse (Billetterie › Remboursements à payer) et compte dans la session du guichetier qui paie.
- **Historique du billet** : vente, placement ou report, pointage, départ, absence, annulation, remboursement, avec
  l'auteur et l'heure ; jamais modifié.

Reste du plan : quotas de sièges pour vendre sur les départs d'une autre agence (P4, à faire avec la synchronisation),
magasin du garage (P5), RH (P6), socle de sécurité et de contrôle (P7).

## Rapport journalier à imprimer (A4 portrait)

Direction › Etat › *Rapport journalier à imprimer (A4)*, ou bouton « Imprimer (A4 portrait) » du rapport journalier.
Mise en page A4 portrait, en tableaux simples (skill `erp-transport-rapport-journalier-agence`) :

1. **Billetterie — départs effectués** : véhicule, trajet, départ, places, prix unitaire, montant ; une ligne par
   trajet et par prix réellement pratiqué (part du billet revenant au car).
2. **Bagages payants** : tableau présent, « Aucune opération » tant que la saisie des bagages n'existe pas.
3. **Colis, courriers et fret encaissés**, par bordereau.
4. **Sorties payées** ce jour (pièce, désignation, véhicule ou agence, moyen de paiement).
5. **Caisse et montant à reverser** : encaissements (billets, colis, autres ; dont espèces / Mobile Money et banque),
   remboursements, sorties, recette nette tous moyens, puis le calcul des espèces (ouverture, entrées, sorties,
   versements, écarts, solde de fin).
6. **Situation par caisse** (une ligne par caisse, Mobile Money, banque) et total agence ; signatures.

Les tableaux 1 (date de départ) et 5 (date de paiement) ne s'additionnent pas : un billet payé la veille est dans les
départs du jour, pas dans la caisse du jour. La caisse est lue sur les comptes de trésorerie : chaque paiement compte
une fois ; les versements à la banque ou au siège ne sont ni recettes ni dépenses. En-tête : n° `RJ-agence-date`,
état (provisoire / clôturé), synchronisation ; pied de page : n° et « Page x / y ». Au siège, choix de l'agence
(données reçues par les échanges).
