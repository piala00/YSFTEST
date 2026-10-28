# Départ d'un véhicule : cycle, absents, agences successives et comptabilisation (à valider)

Suite à votre question. Méthode : d'abord **ce que le logiciel fait déjà** (vérifié dans le code), puis le mécanisme
des agences, puis **ce qui reste à décider**, et enfin l'alignement de la comptabilisation sur **Sage**.

## 1. Le cycle d'un départ — déjà en place [DÉJÀ FAIT]

Un départ (`apps/transport/models.Depart`) passe par les états : **Programmé → Parti → Arrivé → Clôturé** (ou Annulé).

1. **Programmer** le départ (ligne, date/heure, véhicule, chauffeur, convoyeur). Tant qu'il est *Programmé*, la
   billetterie vend.
2. **Vendre les billets** : chaque vente crée des **tronçons** (parties du trajet faites par un même véhicule) ;
   le siège est géré **place par place et par tronçon** (une place libérée à un arrêt peut être revendue pour la
   suite).
3. **Charger et pointer la liste (manifeste)** : `pointer_embarquement` coche qui est à bord.
4. **Faire partir le car** (`partir()`) : le départ passe *Parti* et **se verrouille** (plus de vente possible) ;
   les écritures sont comptabilisées (voir §4), **uniquement pour les voyageurs réellement à bord**.
5. **Arrivée** puis **clôture** (km compteur, observations, avances de mission justifiées).

## 2. Les absents — déjà en place [DÉJÀ FAIT]

Au départ du car, les voyageurs **non cochés** sur la liste deviennent **absents** :
- leur part **n'est pas comptabilisée** en recette du véhicule ;
- leur billet est **détaché du départ** et marqué « à reporter ou à rembourser » (tracé dans l'historique) ;
- l'écran du départ liste les absents et propose de **reporter** le billet sur un autre départ programmé de la même
  ligne, ou de **rembourser** (immédiatement ou plus tard). `annuler_par_la_compagnie` fait de même pour un départ
  annulé.

**À décider [À DÉCIDER]** : à l'expiration d'un billet non utilisé et non remboursé au bout de N jours, que fait-on
(produit acquis « billets périmés », ou remboursement obligatoire) ? Aucune règle n'est inventée ; votre choix.

## 3. Une même voiture, plusieurs agences — déjà en place, à confirmer [DÉJÀ FAIT / À CONFIRMER]

Le trajet A → B → C est traité ainsi :
- Chaque agence **programme son propre départ** (sa portion) pour le véhicule ; l'agence de départ **boucle** (fait
  partir, comptabilise) **sa** portion, et la recette de cette portion lui est **rattachée** (section analytique =
  agence de départ ; le véhicule porte la recette).
- Un voyageur qui continue au-delà (correspondance ou même véhicule) a **un tronçon par portion** ; la fonction
  `correspondances_a_affecter` propose, à une agence suivante, les voyageurs qui **attendent un véhicule** pour la
  suite, à rattacher au départ de cette agence.
- Entre deux gares, une vente faite à un **point de vente** est **rattachée à son agence** (`Gare.rattachement`) :
  les places apparaissent donc sur le **rapport journalier de l'agence de rattachement** (`site_effectue`).

**Ce que vous décrivez — « boucler pour l'agence A, puis rouvrir la même voiture à l'agence B pour compléter » — est
donc possible, mais aujourd'hui sous la forme de deux départs (deux portions) du même véhicule**, pas d'un seul
départ rouvert. **À décider [À DÉCIDER]** : garde-t-on « une portion = un départ » (simple, chaque agence maîtrise et
comptabilise la sienne), ou voulez-vous **un seul départ « multi-agences »** qu'on rouvre et reboucle agence par
agence (plus proche de votre description, mais plus complexe : verrouillage partiel par agence) ? Je recommande de
**garder une portion = un départ** et d'améliorer surtout l'écran pour que l'enchaînement soit évident (bouton
« continuer ce véhicule depuis l'agence suivante »).

## 4. Comptabilisation — aujourd'hui, et à la manière de Sage

**Aujourd'hui [DÉJÀ FAIT]** : au départ (`partir()`), une écriture est générée au journal OD :
- **Débit** « billets à voyager » (ou le compte de liaison de l'agence vendeuse si le billet a été vendu ailleurs) ;
- **Crédit** les comptes de **produits** (billets, bagages, colis port payé), taxe éventuelle ;
- avec **véhicule** et **section analytique = agence de départ** sur chaque ligne ;
- `reference = origine = numéro du départ` : **empêche tout double** (une pièce n'est comptabilisée qu'une fois).

**Ce que fait Sage [DOC-SAGE]** (gestion commerciale → comptabilité) : les pièces validées sont transférées en
comptabilité par un **traitement de comptabilisation** paramétrable — **catégories comptables** ventes/achats/stock
(quel compte pour quel produit), gestion des **écarts** et de la **TVA**, **prévention des doublons**, et une
**boîte de dialogue** (période, journal, options) pour lancer le transfert.

**Proposition [À DÉCIDER]**, pour « les mêmes interfaces et boîtes de dialogue » que Sage, adaptées au transport :
- garder la comptabilisation **automatique au départ** comme aujourd'hui (rien ne se perd) ;
- **et** ajouter un écran **« Comptabilisation / transfert en comptabilité »** à la Sage : il liste les départs
  (et colis, et sorties) d'une **période** avec leur état *comptabilisé / à comptabiliser*, et un bouton lance (ou
  re-contrôle) le transfert, avec la même **boîte de dialogue** (période, journal, aperçu), les **catégories
  comptables** paramétrables (déjà présentes : `ParametresTransport` porte les comptes), et la **prévention des
  doublons** (déjà assurée par `reference/origine`).
- les écrans de **saisie** et de **validation** reprennent déjà l'ergonomie commune ; on alignera les **libellés et
  la boîte de dialogue** sur ceux de Sage.

## 5. Décisions attendues de votre part

1. **Portion = un départ** (recommandé) ou **un seul départ multi-agences rouvrable** ?
2. Billets d'**absents** non remboursés au bout de N jours : produit acquis ou remboursement ? (et N = ?)
3. Comptabilisation : **garder l'automatique + ajouter l'écran de transfert façon Sage** (recommandé), ou passer à
   un **transfert uniquement à la demande** comme Sage ?
4. Confirmez-vous que la recette d'une portion doit rester **rattachée à l'agence qui a fait partir le véhicule**
   (section analytique = agence de départ) ?

Dès vos réponses, je code par étapes testées, en commençant par l'écran de comptabilisation façon Sage et la
clarification de l'enchaînement multi-agences, sans rien casser de l'existant (comptabilisation au départ,
rattachement au point de vente, absents).

---
*Références : code `apps/transport/models.py` (Depart, Troncon, Billet) ; Sage via les compétences
`sage100-gescom-v5-v12-expert` et `sage100-comptabilite-v5-v12-expert` [DOC-SAGE]. Aucune règle fiscale ou de compte
inventée ; les comptes et taux restent ceux paramétrés par la société / validés par l'expert-comptable.*
