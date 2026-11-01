# État des lieux — LOGICIEL TRANSPORT (réconciliation Claude, 01/11/2026)

**Portée : UNIQUEMENT l'ERP Transport Afrique Centrale.** Décision du propriétaire du 01/11 :
on finit d'abord le Transport ; le Commercial sera **adapté ensuite** à partir de l'expérience acquise
(les deux logiciels partageront l'essentiel de ce qui est développé ici).

**Nature du document :** consolidation vérifiable, **pas une certification d'exhaustivité**. Branche de
référence : `ccr-5592a371-fusjt2` (jamais `main`). Rédigé par Claude en complément du plan directeur
**issue #24** et du registre Codex **PR #26** (qu'il ne remplace pas). Aucune fusion, aucun déploiement.

**Légende des statuts :**
- `SUR-CCR` : présent et testé (CI verte) sur la branche de référence.
- `BROUILLON` : codé par Codex dans une PR **ouverte, non fusionnée** → **pas intégré**.
- `À-CLARIFIER` : demande reçue, décision/périmètre à trancher par le propriétaire.
- `À-FAIRE` : demandé, pas encore commencé (ou pas de preuve trouvée).
- `DOUBLON` : fait des deux côtés (Claude sur ccr **et** Codex en brouillon) → à arbitrer.

---

## 1. Décisions d'architecture consignées (journal)

| ID | Décision | Détail | Source |
|---|---|---|---|
| DEC-T01 | **Interconnexion = Tailscale**, pas Sage X3 | X3 étudié puis **écarté** car impose une connexion Internet permanente. Retenu : **Tailscale Serve HTTPS privé** pour lever la contrainte Internet et fonctionner hors ligne / réseau privé. | issue #18, échange 01/11 |
| DEC-T02 | SQLite local + miroir SQL Server | Base de travail SQLite ; copie miroir automatique sens unique vers SQL Server. | AGENTS.md |
| DEC-T03 | Compta générale = **source unique** | Toute écriture analytique dérive d'une écriture générale validée ; jamais « la dernière écriture gagne ». | #24 §D |
| DEC-T04 | Une portion = un départ (hors ligne) | Chaque agence indépendante hors ligne ; consolidation au siège par synchro. | CONCEPTION_DEPART_COMPTABILISATION.md §6 |
| DEC-T05 | Installation **deux méthodes** | Clé signée **OU** fichier `.erpinst`, puis licence d'exploitation distincte. Jamais de code court non signé à la place de la crypto. | #24 §H, #37 |

---

## 2. Socle Transport déjà sur la branche de référence  `SUR-CCR`

Construit avant cette phase de pilotage, présent et testé sur `ccr` (suite transport+reporting verte) :

| ID | Fonction | Statut |
|---|---|---|
| T-01 | Agences/gares, lignes, rattachement point de vente | SUR-CCR |
| T-02 | Billetterie : vente, sièges par tronçon, arrêts, transit/correspondance | SUR-CCR |
| T-03 | Embarquement pointé sur liste, absents, report, remboursement | SUR-CCR |
| T-04 | Colis/courrier/fret, port payé/dû, contre-remboursement, livraison par code | SUR-CCR |
| T-05 | Recette constatée **au départ par véhicule** (tronçons, correspondances) | SUR-CCR |
| T-06 | Bagages payants à la vente du billet | SUR-CCR |
| T-07 | Garage : carburant, ordres de réparation, pièces | SUR-CCR |
| T-08 | Personnel et paie | SUR-CCR |
| T-09 | Propriétaires de véhicules : compte distinct, fixe+variable, avances, retraits | SUR-CCR |
| T-10 | Caisses par agence, sessions, clôtures de journée | SUR-CCR |
| T-11 | Exploitation : clôture voyage, km, convoyeur, papiers, avance de mission | SUR-CCR |
| T-12 | Sorties autorisées par le siège, payées par toute agence | SUR-CCR |
| T-13 | Imprévus de voyage et leurs écritures | SUR-CCR |
| T-14 | Comptabilité générale + analytique, **10 plans**, plan à 7 chiffres | SUR-CCR |
| T-15 | Reporting comparatif, états + graphiques, budget/réel | SUR-CCR |
| T-16 | Échanges direction↔agences : lots signés, idempotence, consolidation siège | SUR-CCR |
| T-17 | Rapport journalier d'agence ; numéros par agence ; Mobile Money | SUR-CCR |
| T-18 | Compilation exécutable (Linux validé ; **Windows réel non prouvé**) | SUR-CCR (Linux) |

### Travaux de cette session (Claude), sur `ccr`, CI verte
| ID | Fonction | Statut | Remarque |
|---|---|---|---|
| T-19 | Saisie billet **et** colis en **portrait rapide** (Entrée → champ suivant) | SUR-CCR | **DOUBLON** avec PR #12 Codex |
| T-20 | État « Colis arrivés non livrés » (souffrance, seuil, CSV) | SUR-CCR | **DOUBLON** avec PR #29 Codex |
| T-21 | **Report automatique** des voyageurs non partis (option Paramètres) | SUR-CCR | Décision Q2 du propriétaire |

---

## 3. Raffinements Transport codés par Codex — `BROUILLON` (non intégrés)

PR ouvertes, **empilées** (chaîne de dépendances), **aucune fusionnée** :

| PR | Objet Transport | Statut | Remarque / dépendance |
|---|---|---|---|
| #9 | Reprise Transport : source des montants (TR-01), recette P0 | BROUILLON (doc) | TR-01 déjà corrigé sur ccr |
| #12 | Saisie rapide billets/colis, coordonnées retrouvées, impression en série | BROUILLON | **DOUBLON** T-19 ; + « contacts mémorisés » et impression série à récupérer |
| #17 | Guichet compact, billets en transit, transvasement | BROUILLON | base de la chaîne empilée |
| #19 | Billetterie : saisie progressive du véhicule, filtres VIP/Classique | BROUILLON | véhicules dédiés par gamme |
| #20 | Simulation complète : transit, incidents colis, garage, comptes propriétaires | BROUILLON | à rapprocher du chantier Simulation |
| #32 | Incidents de colis entre agences sans nouveau paiement (F03.1) | BROUILLON | |
| #33 | Empêcher frais répétés / écritures sur un départ distant (P004.2) | BROUILLON | P0 comptable |
| #34 | Conserver la répartition du **port dû** après transvasement (F03.2) | BROUILLON | |
| #36 | Une seule validation comptable et stock par pièce de garage (P004.3) | BROUILLON | P0 comptable |
| #29 | Catalogue Transport → lien état colis non livrés (Reporting03.1) | BROUILLON | **DOUBLON** T-20 |
| #35 | Exports **.xlsx** des vues d'analyse (Reporting03.2) | BROUILLON | demande export Excel |
| #8 | Audit boutons Comptabilité/Transport (lot 02) | BROUILLON (doc) | audit, pas du code |
| #22 | P0 comptable agences : droits, validation atomique, clôtures uniques | BROUILLON | transverse |

**Risque :** chaîne #11→…→#40 empilée ; bases réelles à vérifier avant toute intégration. Doublons T-19/#12 et
T-20/#29 à arbitrer (garder une seule version).

---

## 4. Licences / Installation / Distribution (transverse, requis pour livrer le Transport)

| ID | Demande | Statut | Source |
|---|---|---|---|
| H-01 | Clé publique éditeur **gravée** dans les binaires (non remplaçable) ; privée jamais livrée | BROUILLON (#23) ; `CLES` **vide** sur ccr | #1, #10 |
| H-02 | Activation unifiée : `.erplic` **ou** clé texte signée, un seul moteur, Hardware ID | BROUILLON (#23) | #1 (validation 31/10) |
| H-03 | Installation deux méthodes : clé signée **ou** `.erpinst` ; licence d'exploitation distincte | BROUILLON (#40) | #37 |
| H-04 | **P0 #37** : bouton « Copier le code » + corriger refus `.erpinst` « signature incorrecte » | BROUILLON (#38/#39) ; CI Windows #38 **en échec** (SetFocus) | #37 |
| H-05 | Réinstallation exige une autorisation ; désinstallation complète **sans perte de données** | BROUILLON (#25) | #1 (31/10) |
| H-06 | Licences simplifiées : code **4×6**, activation par fichier, `LIRE-MOI.txt`, noms neutres | BROUILLON (#11/#21) | #10 |
| H-07 | Gestionnaire de licences **séparé et compact**, coffre privé, déverrouillage par session | BROUILLON (#11/#21) | #10 |

**Cause racine probable du #37 (avis relecteur Claude) :** la clé publique gravée dans l'installateur ne
correspond pas à la clé privée du générateur quand les deux binaires viennent de **runs CI différents**
(`CLES` vide sur ccr → paire fabriquée à la volée par build). Correctif : **une seule paire par release**,
même clé gravée dans générateur **et** installateur du même run. Le bouton « Copier » est trivial/orthogonal.

---

## 5. Demandes NOUVELLES du 01/11 (captées, à intégrer au plan)

| ID | Demande | Statut | Dépendances |
|---|---|---|---|
| A-IMPEX-01 | Menu **Fichier → Import/Export** + **Paramètres d'import/export** (façon Sage) — **manque critique** | À-FAIRE | socle des suivantes |
| G-SIM-02 | La **simulation = un fichier société** qu'on importe/restaure dans le **vrai logiciel** (lancer sur une machine, importer sur une autre) | À-CLARIFIER | A-IMPEX-01 |
| F-BKP-03 | **Sauvegarde fin de journée par agence envoyée à la direction** (hors synchro auto) ; en cas de panne, la direction synchronise le serveur central. Le menu Import/Export sert à **tester** ce backup | À-CLARIFIER | A-IMPEX-01, T-16 |
| G-SIM-04 | **Logiciel de simulation autonome** (détaché, comme le gestionnaire de licences) : simuler direction + agences, exporter/réimporter par agence, **multi-agences / multi-simulations** | À-CLARIFIER | A-IMPEX-01, G-SIM-02 |
| G-SIM-05 | La simulation autonome doit **simuler le terrain réel** : imprévus, incidents, retards, pannes, fraudes, réseau coupé, tous les mouvements | À-CLARIFIER | G-SIM-04 |

**Fil conducteur :** une **seule fonction Import/Export réutilisée partout** → (1) menu Sage manquant,
(2) simulation importable comme société, (3) test du backup agence→direction, (4) simulateur autonome.
Cohérent avec « réutiliser les vrais moteurs, pas de doubles règles ».

**2 points à trancher (bloquent le codage) :**
1. **Format du fichier** : un format unique (sauvegarde société = export simulation = envoi agence→direction) ? ou distinguer « sauvegarde complète » et « lot de synchro » ?
2. **Import** : deux actions distinctes dans le même menu → **Restaurer** (remplace la société) et **Recevoir** (fusion HQ sans écraser) ?

---

## 6. Autres demandes Transport encore ouvertes / à clarifier

| ID | Demande | Statut | Source |
|---|---|---|---|
| T-22 | Billetterie : **plusieurs départs ouverts côte à côte** (fenêtres portrait déplaçables) | À-CLARIFIER (« sauf si ça crée des problèmes ») | échange ergonomie |
| T-23 | Écran **« Comptabilisation / transfert en comptabilité » façon Sage** + barre de progression | À-CLARIFIER (contrôle+rattrapage vs transfert à la demande) | Q3 |
| T-24 | Recette d'un **point de vente intermédiaire** → agence suivante encore ouverte qui encaisse | À-FAIRE / à affiner | Q4 (Bertoua→Ndokayo) |
| T-25 | Absents : distinguer **raté** (pas de remboursement) vs **présent non parti** (remboursement ou report) | PARTIEL (report auto fait T-21) | Q2 |
| T-26 | Contacts passagers **mémorisés** + **impression en série** des billets | BROUILLON (#12) | #12 |
| T-27 | Déploiement recette **Windows + Tailscale** (propriétaire + expert-comptable, Android/PC) | À-FAIRE (P1) | #18 |
| T-28 | **Recette Windows réelle** du .exe (installeur, démarrage, licence) + SQL Server | À-FAIRE / non prouvé | #24 Q |

---

## 7. Ce qu'il reste à faire, priorisé (Transport)

- **P0** : H-04 (#37 installateur `.erpinst` + Copier le code) ; H-01/H-02/H-05 (activation/identité/désinstallation) ; #33/#36/#22 (intégrité comptable P0).
- **P1** : arbitrer les **doublons** T-19/#12 et T-20/#29 ; stratégie d'**intégration des PR empilées** (après autorisation) ; A-IMPEX-01 (socle import/export) une fois les 2 points tranchés.
- **P2** : G-SIM-02/04/05 (simulation importable + simulateur autonome) ; T-23 (écran comptabilisation) ; T-24 (recette point de vente) ; T-27 (Tailscale).
- **P3** : T-22 (multi-fenêtres guichet).

## 8. Décisions attendues du propriétaire
1. Format du fichier d'échange unique **oui/non** (point 1 du §5).
2. Import = **deux actions** Restaurer / Recevoir **oui/non** (point 2 du §5).
3. Doublons : on garde **la version sur `ccr`** (T-19, T-20) et on écarte #12/#29, ou l'inverse ?
4. Autorise-t-on une **stratégie d'intégration** des PR Codex empilées (une fois relues) — sachant qu'aucune fusion ne se fait sans ton accord explicite PR par PR ?

---
*Sources : issues #1, #10, #18, #24, #27, #37 ; PR #2–#40 ; `docs/` et `docs/retour/` ; skill de pilotage 01/11.
Non recoupées : conversations privées ChatGPT/Codex non publiées sur GitHub (marquées « source à récupérer »).*
