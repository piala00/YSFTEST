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
