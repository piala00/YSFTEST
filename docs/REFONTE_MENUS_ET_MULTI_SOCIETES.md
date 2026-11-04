# Refonte de l'interface : menus globaux vs modules, multi-sociétés, simulation

Conception validée avec le propriétaire (2026-11-04). Point de départ : notre logiciel est un
**ERP intégré** (tous les modules sur une seule plateforme), alors que les menus ont été repris de
Sage où chaque produit (Commercial, Comptabilité, Caisse…) est **installé séparément** et possède
donc ses propres menus complets. Résultat : des options **globales** (Sauvegarde, Import/Export,
Base, Licence…) sont aujourd'hui **dupliquées** dans le menu Fichier de chaque module ET dans
« Administration du poste ». Il faut séparer clairement **global** et **spécifique au module**.

Benchmark : Dolibarr = un gestionnaire de menu global unique, les modules y ajoutent leurs entrées ;
Odoo = chaque module contribue ses écrans mais la visibilité est filtrée par rôle. Principe retenu :
**les fonctions globales vivent à UN seul endroit global ; les modules ne gardent que leurs menus
métier ; la visibilité reste filtrée par droits.**

## 1. Architecture des menus

### Menu « Fichier » — GLOBAL, identique dans tous les modules (agit sur la société ouverte)
- **Nouvelle société** (assistant : identité → rôle → base → admin ; crée la base)
- **Ouvrir une société…** (écran Choix de la société ; bascule par bref redémarrage)
- **Fermer la société** (revient à l'écran Choix de la société)
- **Restaurer une société** (depuis une sauvegarde)
- **Sauvegarde et restauration** (de la société ouverte) — *retiré des menus de module*
- **Import / Export** (de la société ouverte) — *retiré des menus de module*
- **Autorisations d'accès** (utilisateurs/droits de la société)
- **Journal des événements** (audit de la société)
- **Clôturer l'exercice et ouvrir le suivant** (crée la base de l'année N+1 ; voir §2)
- **Imprimer…**, **Quitter**

### « Administration du poste » — CE POSTE (machine), pas la société
- **Base de données** (SQLite / SQL Server / les deux ; migration)
- **Licence** (activation, essai)
- **Synchronisation** direction ↔ agences (boîte aux lettres / relais)
- **Démarrage avec Windows** (service)
- **Simulations** (créer, ouvrir, arrêter, supprimer — voir §3)
- **Repartir à zéro** (effacer la société du poste)

### Menus des MODULES — inchangés, uniquement le métier
- **Comptabilité** : plan comptable, journaux, saisie d'écritures, **Exercices comptables**,
  **Clôture d'exercice**, états comptables, reports à nouveau, budgets…
- **Transport / Billetterie** : billets, colis, bagages, véhicules, voyages, caisses, embarquement…
- **Garage, Personnel/Paie, Magasin, Reporting** : leurs commandes propres.
- Chaque module garde ses onglets Structure / Traitement / État spécifiques.

### Règle de conception (à appliquer et à maintenir)
Une commande va dans **Fichier (global)** si elle agit sur **toute la société** ou le **logiciel**
(sauvegarde, import/export, société, droits, journal). Elle va dans **Administration du poste** si
elle concerne **la machine/le poste** (base, licence, service, synchro, simulation). Elle reste
dans le **module** seulement si elle est **métier** et propre à ce module. Aucune de ces trois
familles ne doit réapparaître dans une autre (fin des doublons).

## 2. Multi-sociétés et exercices (une base par année)

Modèle retenu (conforme à la pratique réelle du propriétaire et à sa crainte n°1 : ne jamais tout
perdre). Chaque **exercice (année)** d'une société/agence = **sa propre base** (SQLite ou SQL
Server au choix à la création). Isolement : une base corrompue ne touche que cette année-là.

- **Écran « Choix de la société » au lancement** : liste des bases **regroupées par Société /
  Agence**, avec les **années** dessous ; **recherche** (nom ou année) ; **exercices clôturés
  masqués par défaut** (case « Afficher les exercices clôturés »). Chaque base porte ses
  métadonnées (société, agence, année, statut ouvert/clôturé) pour un regroupement fiable.
- **Bascule** : ouvrir/fermer une société via le mécanisme de redémarrage existant ; login par société.
- **Clôturer l'exercice et ouvrir le suivant** (un seul bouton, aucune manipulation manuelle) :
  1. fige l'exercice courant (consultation seule) ;
  2. crée la **base de l'année N+1** (même société/agence) ;
  3. y **recopie la configuration** (plan, journaux, tiers, véhicules, paramètres, utilisateurs),
     sans les mouvements ;
  4. y passe les **reports à nouveau** (soldes d'ouverture) depuis la balance clôturée ;
  5. **relie** N+1 à N (pointeur « exercice précédent ») pour la traçabilité et la consultation.
- Sauvegarde **par base/année** ; une année clôturée ne bouge plus → une sauvegarde suffit.

S'appuie sur l'existant : modèle `Exercice` (champ `cloture`), service `cloturer_exercice`
(résultat + reports à nouveau), et le mécanisme de changement de base (`base_donnees.lancer_changement`,
action `redemarrage`). La nouveauté : la clôture **sème une nouvelle base** au lieu d'un exercice
dans la même base.

## 3. Simulation : options manquantes (benchmark sandbox)

Principes repris des environnements sandbox : garder les données **hors** de l'environnement,
« pause = reprendre le même environnement », « instantané = cloner », et prévoir que les connexions
se coupent à la reprise. Chez nous, la simulation tourne **déjà dans son propre dossier** (donnée
isolée). Manquent :
- **Arrêter** une simulation en cours (annuler la génération proprement ; le dossier partiel reste
  listé, supprimable).
- **Ouvrir / Fermer** une simulation **comme une société** (elle apparaît dans l'écran Choix de la
  société, marquée « simulation ») → c'est le « reprendre » : on ferme le logiciel, on le rouvre,
  on rouvre le dossier de simulation pour consulter/continuer.
- **Reprise d'une génération longue** : la génération est un traitement par lots ; plutôt que mettre
  en pause le calcul, on **génère par tranches** (déjà mois par mois) et chaque tranche terminée est
  consultable — on peut arrêter après une tranche et relancer la suivante plus tard.
- **État visible** (en cours / terminé / interrompu) et journal, déjà partiellement présents.

## 4. UX / ergonomie (benchmark, à intégrer progressivement)
- **Barre globale constante** (Fichier société + Administration + aide) identique quel que soit le
  module ouvert ; les onglets métier changent selon le module.
- **Visibilité par droits** (comme Odoo) : chaque entrée n'apparaît qu'aux rôles concernés.
- **Fil d'Ariane** « Société · Exercice · Module » toujours visible (on sait dans quelle société et
  quelle année on travaille — crucial en multi-sociétés).
- **Indicateur licence / essai / lecture seule** déjà présent, à garder visible.

## 5. Plan de réalisation (étapes vérifiables, compilées et testées une par une)
1. Écran **Choix de la société** + liste regroupée/filtrée + bascule (redémarrage) + login par société.
2. **Menu Fichier global** dédupliqué (sortir Sauvegarde/Import/Export des modules ; régler la
   frontière Fichier / Administration du poste / module).
3. **Clôture → nouvelle base** (config + reports à nouveau + lien N↔N+1).
4. **Simulation** : Arrêter + ouvrir/fermer comme une société.
5. UX transverse (fil d'Ariane, visibilité par droits) au fil de l'eau.

Sources benchmark : Dolibarr (système de menus), Odoo (menus/réglages par module, visibilité par
rôle), principes sandbox pause/instantané (Inngest, E2B).


### Configuration de l'ouverture SQL Server (implémentation P0)

Le catalogue JSON conserve uniquement l'identifiant, le moteur `mssql` et le nom de la base.
Pour une entrée d'identifiant `transport_2026`, définir sur le **poste serveur** :
`ERP_SOCIETE_SQL_TRANSPORT_2026_HOST`, éventuellement
`ERP_SOCIETE_SQL_TRANSPORT_2026_USER`, `ERP_SOCIETE_SQL_TRANSPORT_2026_PASSWORD`
et `ERP_SOCIETE_SQL_TRANSPORT_2026_PORT`. Sans utilisateur, l'authentification Windows
est utilisée. Les secrets ne doivent jamais être ajoutés au catalogue ni au dépôt.
La base doit exister et contenir une société ERP initialisée ; l'ouverture ne crée ni ne migre
la base. La vérification précède toute modification de la configuration active ; puis le
poste redémarre et l'utilisateur doit se reconnecter dans la base choisie.
**Reste à valider sur un poste Windows réel** : connexion SQL Server, redémarrage,
isolation des sessions et conservation des paramètres après redémarrage.
