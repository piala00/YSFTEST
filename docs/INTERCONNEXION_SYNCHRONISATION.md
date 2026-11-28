# Interconnexion et synchronisation des logiciels ERP OHADA

> Document d'architecture de référence (propriétaire + Claude + Codex).
> But : décrire **comment les postes, agences et la direction sont reliés**, et comment les
> données circulent entre eux. À lire avant toute évolution touchant la synchronisation.

## 1. Principe directeur : un seul moteur, trois canaux

Il n'y a **pas trois logiciels de synchronisation différents**. Il y a **un seul moteur**
d'échange, et **trois canaux de transport** pour le même lot de données. On choisit le canal
selon la connectivité réelle de chaque site — et on peut les **mélanger** dans la même société.

Le moteur repose sur trois garanties (la partie difficile, **déjà codée et testée**) :

- **Identités stables** : chaque donnée porte un identifiant unique mondial (uid) et son
  `site_origine` (l'agence qui l'a créée). Rien n'est identifié par un simple numéro local.
- **Lots signés et idempotents** : un envoi est un paquet signé numériquement ; on peut le
  rejouer plusieurs fois **sans créer de doublon** (`apps/echanges`, numéro de fait `--depuis`).
- **Règle d'or comptable** : jamais « la dernière écriture gagne ». Toute écriture analytique
  provient d'une écriture générale validée ; on ne fusionne jamais deux versions d'un même
  montant en écrasant l'une par l'autre. La consolidation est une **projection**, pas un écrasement.

C'est grâce à ces trois garanties que les trois canaux ci-dessous sont sûrs et réconciliables
sans conflit.

## 2. Les trois modes d'interconnexion

### Mode 1 — Serveur central en ligne (style « tout navigateur »)

Un seul serveur, hébergé en ligne. Chacun ouvre **juste un navigateur**, où qu'il soit, et
travaille directement sur la base centrale. Côté agence : rien à installer (rôle **poste**).

- **Pour qui** : le siège, les villes bien connectées, et surtout les **rôles mobiles de la
  direction** — un chef comptable ou un expert-comptable peut se connecter **depuis n'importe où
  avec Internet** pour contrôler, consolider ou valider des écritures, sans être au siège.
- **Avantages** : une seule source de vérité, **aucune synchronisation**, consolidation
  instantanée, maintenance d'un seul serveur.
- **Limites** : exige **Internet permanent**. Si le réseau tombe dans une agence, elle **ne peut
  plus vendre**. Inacceptable comme **seul** mode pour le transport interurbain (réseau irrégulier).
- **État** : le mécanisme marche déjà (rôle **poste** = navigateur vers un serveur). Reste à
  **héberger le serveur en ligne et le sécuriser** (HTTPS, authentification, licence par serveur).

### Mode 2 — Serveur local par agence, synchronisé au central (hors-ligne d'abord)

Chaque agence a **son propre serveur local** (rôle **agence**) qui fonctionne **même sans
Internet**, et se **synchronise automatiquement** avec le siège (rôle **siège**) dès qu'une
liaison est disponible.

- **Pour qui** : toutes les agences d'exploitation (guichets, caisses) — le cœur du réseau.
- **Avantages** : l'agence **ne s'arrête jamais** faute de réseau ; la synchro **rattrape** au
  retour de la liaison. Résilience maximale.
- **Limites** : plusieurs serveurs à installer et entretenir ; synchro **différée** (pas instantanée).
- **État** : **c'est le design construit**. Rôles siège/agence, déclaration d'agence, fichier
  d'installation d'agence (contient sa clé), boîte aux lettres. Transport privé retenu :
  **Tailscale** (réseau privé, sans exposer le serveur sur l'Internet public).

### Mode 3 — Import / Export de fichiers

L'agence **exporte** un lot signé (ou une sauvegarde complète de société), l'envoie par le moyen
disponible (USB, WhatsApp, e-mail), et le central **importe** ; et inversement.

- **Pour qui** : les agences **sans aucun réseau**, et comme **filet de sécurité universel**.
- **Avantages** : marche avec **zéro connexion** — il suffit de déplacer un fichier. C'est aussi
  le mécanisme de **sauvegarde de fin de journée** (agence → direction) et la base de la
  **simulation importable comme une restauration de société**.
- **Limites** : manuel, plus lent, une personne dans la boucle.
- **État** : **construit** — `echanges exporter` / `echanges importer`, lots signés idempotents,
  export/import de société complète, sauvegarde.

## 3. Les canaux de transport (le même lot, trois chemins)

Le moteur produit **un lot signé** ; ce lot peut voyager par n'importe lequel de ces chemins,
sans changer le contenu :

| Canal | Commande / mécanisme | Réseau requis |
|---|---|---|
| **Dossier partagé** (LAN, disque commun) | `echanges synchroniser --dossier-partage <dossier>` (ou `ECHANGES_DOSSIER_PARTAGE`) | réseau local |
| **Relais en ligne** (Internet / Tailscale) | `echanges synchroniser --relais-url <url> --relais-jeton <jeton>` ; API `apps/relais` : `POST/GET/DELETE /relais/v1/boites/<code>/…` (actif seulement si `RELAIS_ACTIF=1`) | Internet ou Tailscale |
| **Fichier porté** (import/export) | `echanges exporter --vers <code>` → fichier `.erpx` → `echanges importer <fichiers>` | aucun |

Le relais ne stocke que des **lots chiffrés** déposés dans la boîte du destinataire ; il ne lit
pas les données. Un site inconnu du relais est refusé (404).

## 4. Topologie recommandée (société transport type)

- **Épine dorsale = Mode 2** (hors-ligne d'abord) : chaque agence a son serveur local + Tailscale.
  Une agence ne doit **jamais** s'arrêter faute de réseau.
- **Mode 1 en option** pour le **siège** et les postes bien connectés : le serveur du siège est
  aussi accessible en ligne, pour que la **direction** (chef comptable, expert-comptable) se
  connecte **de n'importe où** par navigateur.
- **Mode 3 comme filet universel** : pour une agence sans réseau, et comme **sauvegarde** de fin
  de journée vers la direction.

Un même réseau peut donc **mélanger** les trois : agence bien connectée en navigateur pur
(mode 1), agence à Internet instable en serveur local + Tailscale (mode 2), agence isolée en
import/export (mode 3). Le siège consolide tout, quel que soit le canal d'arrivée.

## 5. Sécurité

- **Lots chiffrés et signés** : le contenu ne circule jamais en clair ; un lot altéré est rejeté.
- **Licence par serveur** : liée à l'empreinte de la machine, à l'édition et au site. La version
  expirée passe en **lecture seule** sans jamais bloquer consultation, états, exports ni sauvegardes.
- **Mise en ligne (Mode 1)** : à sécuriser avant exposition — HTTPS obligatoire, authentification
  forte, et préférer **Tailscale** à l'exposition directe sur l'Internet public quand c'est possible.
- **Jamais de clé privée** (coffre de l'éditeur) dans le dépôt, l'exécutable ni l'installateur.

## 6. État et travaux restants

**Déjà codé et testé**
- Moteur d'échange : identités stables, lots signés idempotents, consolidation au siège.
- Canaux : dossier partagé, relais en ligne (`apps/relais`), import/export.
- Rôles à l'installation : seul / siège / agence / poste.
- Sauvegarde / restauration de société (base de la simulation importable).

**À finir**
- **Mode 1 — mise en ligne du serveur central** : procédure d'hébergement sécurisé (HTTPS,
  authentification, licence), documentée et testée, pour l'accès navigateur de la direction
  depuis n'importe où.
- **F-BKP-03** : sauvegarde de fin de journée agence → direction, en un geste, via le canal 3.
- **Simulateur autonome** (G-SIM-04/05) : rejouer le terrain réel (plusieurs agences, imprévus)
  à travers ces mêmes canaux.

## 7. En résumé

Un **seul logiciel**, un **seul moteur** de synchronisation, **trois canaux** (dossier partagé,
relais en ligne, fichier porté) et **trois modes d'usage** (serveur central en ligne, serveur
local synchronisé, import/export) — choisis par site selon la connectivité, et **combinables**.
La direction peut travailler en ligne de partout ; les agences ne s'arrêtent jamais faute de réseau.
