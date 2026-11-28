# Gestion des données : Sauvegarde/Restauration vs Import/Export vs Ouvrir une société

Décision de cadrage (propriétaire, 2026-11-08). But : définir **sans ambiguïté** ce que fait chaque
commande, pour ne garder qu'un sens par mot et ranger les menus en conséquence (#72).

## Les trois opérations (distinctes, à ne jamais confondre)

### 1. Sauvegarde / Restauration — **se protéger de la perte**
- **Sauvegarde** = instantané **intégral** de toute la base d'un poste (société, exercices,
  utilisateurs/droits, comptabilité, transport…). Deux formes :
  - fichier `.json` (clair) ;
  - fichier **`.erpcoffre` chiffré** par mot de passe (anti-vol, clé USB) — livré.
- **Restauration** = on **efface tout** puis on recharge l'instantané (`flush` + `loaddata`).
  → C'est un **retour arrière complet**.
- **Règle** : on restaure **SA PROPRE base**, sur **SON PROPRE poste**, après un sinistre
  (vol, incendie, disque mort, rançongiciel, erreur massive).
- Code : `apps/core/sauvegarde.py`, `apps/core/coffre_sauvegarde.py`, écran « Sauvegarde et
  restauration ».

### 2. Import / Export entre agences (échanges) — **faire circuler et consolider**
- **Export** = une agence fabrique un **lot** `.erpx` **signé** de ses **faits/mouvements** sur une
  plage (billets, colis, écritures…).
- **Import** = la direction (ou une autre agence) **fusionne** ces faits dans sa base, **sans rien
  effacer** : import **idempotent** (chaque fait a une identité stable → pas de doublon même si on
  réimporte).
- **Règle** : les bases restent **distinctes** ; l'import **ajoute**, il n'écrase jamais.
- Code : `apps/echanges/` (lots, publication, relais), « Import et export agences »,
  « Sauvegarde de fin de journée agence → direction » (F-BKP-03, qui est un **lot**, pas une
  restauration intégrale).

### 3. Ouvrir / Nouveau une société (multi-société) — **choisir la base dans laquelle TRAVAILLER**
C'est le fonctionnement **normal** d'entrée dans le logiciel, **exactement comme Sage** (et non une
simple consultation) :
- Menu **Fichier → Ouvrir** = choisir la base (société / agence / **année**) dans laquelle
  travailler ; **Fichier → Nouveau** = créer une société.
- On **sélectionne la base** (ex. 2026) → l'écran **login** (utilisateur + mot de passe) apparaît →
  on se connecte → on **travaille**.
- Pour changer d'année/société : on se **déconnecte**, **Fichier → Ouvrir**, on choisit l'autre base
  (ex. 2025), login, et on y travaille. Une année **clôturée** s'ouvre en **lecture seule**
  (consultation) ; une année ouverte s'ouvre pour **travailler**. L'action « Ouvrir » est la même.
- Chez le propriétaire, **chaque année = une base séparée** (une base par exercice) — d'où
  l'importance de ce sélecteur.
- Code : « Choix de la société » (`views_societes`), catalogue multi-sociétés, une base par année.
  La bascule passe par un **redémarrage + login sur la nouvelle base** (déjà en place).

> Lien avec la question « agence → direction » : si la direction veut seulement **regarder** la
> base complète d'une agence, elle l'**ouvre** comme une société à part (lecture), au lieu de la
> **restaurer** (qui écraserait sa propre base). Mais l'usage premier de « Ouvrir » reste de
> **choisir la base de travail**, pas la consultation.

## Réponse à la question « agence sauvegarde → direction restaure »

| Intention réelle | Bonne opération | Mauvaise opération (danger) |
|---|---|---|
| Faire **remonter les données** d'une agence au siège (les ajouter à la consolidation) | **Import de lot** (fusion additive) | ❌ Restauration intégrale (écrase la base direction) |
| **Consulter** la base d'une agence telle quelle | **Ouvrir comme société séparée** | ❌ Restauration intégrale |
| Une agence **récupère son poste** après sinistre | **Restauration intégrale** de **sa** sauvegarde | — |

**Règle d'or : la direction ne restaure JAMAIS la sauvegarde d'une agence par-dessus sa base.**
Pour recevoir une agence au siège, on **importe un lot** (fusion). La restauration intégrale est
réservée au poste qui avait fait la sauvegarde.

## Rangement des menus qui en découle (#72 étape B — à valider)

- **Fichier (global, agit sur la société) :**
  - **Sauvegarde et restauration** (intégrale : `.json` / `.erpcoffre` chiffré).
  - **Import / Export** (lots d'échange entre agences/direction).
  - **Ouvrir / Fermer une société**, **Restaurer une société** (depuis une sauvegarde, dans un
    dossier séparé).
- **Administration du poste (machine) :**
  - **Base de données** (moteur SQLite / SQL Server + **miroir** automatique) — configuration du
    stockage, **pas** une deuxième sauvegarde.
  - **Synchronisation agences ↔ direction** (le canal **automatique** des lots : boîte aux lettres /
    relais) — le « tuyau », l'Import/Export manuel restant dans Fichier.
  - **Licence**, **Simulation**, **Repartir à zéro**.

### Le doublon à trancher
Aujourd'hui « Sauvegarde et restauration » apparaît **deux fois** : dans le menu Fichier (écran
société, chiffré) **et** dans Administration du poste (onglet lié à la base + miroir SQL Server).
**Proposition** : n'en garder qu'un seul sens —
- « **Sauvegarde et restauration** » = **intégrale société**, dans **Fichier** uniquement ;
- l'onglet d'Administration devient « **Base de données** » (moteur + miroir), **sans** le mot
  « sauvegarde » (le miroir SQL Server n'est pas une sauvegarde de restauration, c'est une copie
  synchrone de secours). À valider par le propriétaire.
