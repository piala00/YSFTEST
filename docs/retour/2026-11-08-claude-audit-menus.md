# Audit menus (#72) — global vs module, dé-duplication — Claude, 2026-11-08

Objectif (propriétaire) : notre ERP est **intégré**, pas des produits Sage séparés ; les commandes
**globales** (sauvegarde, import/export, licence, base) sont aujourd'hui **dupliquées** entre le
menu Fichier de chaque module ET « Administration du poste ». Séparer clairement global / machine /
métier (cf. `docs/REFONTE_MENUS_ET_MULTI_SOCIETES.md`).

## Constat (code réel : `apps/core/navigation.py`, ~1311 lignes)

Doublons confirmés — les mêmes commandes réapparaissent dans le menu **Fichier** de plusieurs
modules (`menu_fichier()` générique + les onglets Fichier propres à `commercial` et `comptabilite`) :

| Commande | Où elle apparaît aujourd'hui | Nature |
|---|---|---|
| Autorisations d'accès | Fichier de chaque module | **global** (droits de la société) |
| Journal des événements | Fichier de chaque module | **global** |
| Sauvegarde et restauration | Fichier de chaque module | **global** |
| Import / Export | Fichier de chaque module | **global** |
| Échanges entre agences | Fichier (commercial, transport, compta) | **global** |
| Reprise d'un dossier | Fichier (commercial, compta) | **global** |
| **Administration du poste** (`core:poste`) | **imbriqué dans le Fichier de chaque module** | **machine** |

→ Conforme au diagnostic du propriétaire : le même bloc global est recopié par module, et l'écran
machine (« Administration du poste ») est accroché sous chaque module au lieu d'être à part.

## Cible (rappel `REFONTE_MENUS_ET_MULTI_SOCIETES.md`)
- **Fichier (global, identique partout)** : Nouvelle/Ouvrir/Fermer société, Restaurer, Sauvegarde,
  Import/Export, Autorisations, Journal, **Clôturer l'exercice**, Imprimer, Quitter.
- **Administration du poste (machine)** : Base de données, Licence, Synchronisation, Démarrage
  Windows, Simulations, Repartir à zéro.
- **Modules** : uniquement le métier.

## Chevauchement avec GPT (important)
Plusieurs entrées cibles du Fichier global — **Nouvelle / Ouvrir / Fermer société** et
**Clôturer l'exercice et ouvrir le suivant** — relèvent du **multi-société / clôture N+1**, chantier
**actif de GPT** (`apps/core/reports_annuels_sqlite.py`, fixtures de clôture). Refondre le Fichier
global en même temps que GPT touche ces écrans = risque de collision sur une branche partagée.

## Plan proposé (incrémental, à valider par le propriétaire)

**Étape A — dé-duplication pure (faible risque, sans attendre GPT)** : extraire **un seul**
constructeur du bloc global (`bloc_fichier_global()`) et **un seul** point d'entrée machine, puis
les réutiliser dans tous les modules en **retirant les doublons**. Aucune commande nouvelle, aucun
changement de comportement : juste « défini une fois, réutilisé partout ». Testable (un test vérifie
que chaque commande globale n'apparaît qu'à un seul endroit par module).

**Étape B — frontière Fichier / Administration du poste** : sortir les commandes **machine**
(Base, Licence, Synchro, Démarrage Windows, Simulations, Repartir à zéro) du Fichier vers
« Administration du poste », et n'y laisser que le **global**.

**Étape C — multi-société dans Fichier** (Nouvelle/Ouvrir/Fermer société, Clôturer l'exercice) :
**à faire avec GPT** (son chantier), pas unilatéralement.

## Décision demandée au propriétaire
1. Je lance **l'étape A** (dé-duplication pure, sans risque, sans attendre GPT) ? (recommandé)
2. L'étape B (frontière machine) : je l'enchaîne, ou je te montre d'abord le rendu ?
3. L'étape C (société/exercice dans Fichier) : je me coordonne avec GPT — ok ?

En attendant ta réponse, je ne touche pas à `navigation.py` (fichier partagé, gros impact).
