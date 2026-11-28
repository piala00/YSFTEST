# Revue du chantier clôture N→N+1 + reprise du plan — Claude, 2026-11-08

Le propriétaire me demande de **reprendre tout le chantier**, de **revoir le travail de GPT de la
semaine** (corriger si besoin) et d'**avancer**, en repartant du plan que j'avais laissé
(`docs/REFONTE_MENUS_ET_MULTI_SOCIETES.md`, §2 multi-sociétés / une base par année).

## Verdict de revue (travail GPT du 5 au 8 nov)

Tout le travail de GPT de la semaine porte sur **un seul sujet** : le moteur de **clôture annuelle
N→N+1** (une base par année). **Qualité excellente, aucune correction nécessaire**, et **suite
complète verte : 739 tests OK (15 skipped)** le 2026-11-08.

Points vérifiés et conformes (`AGENTS.md`, OHADA) :
- `cloture_annuelle_sqlite.preparer_exercice_sqlite` : base N+1 créée en **exclusif**, source N en
  **lecture seule**, transaction `BEGIN IMMEDIATE`, `foreign_key_check`, **rollback + suppression**
  de N+1 sur échec.
- `reports_annuels_sqlite.reporter_balance_validee` : **chaque pièce validée** doit être équilibrée
  (refus des compensations — pas de « dernière écriture gagne »), **comptes de gestion (6/7/8)
  soldés en N obligatoires**, **dimensions analytiques** (tiers/section/véhicule) préservées,
  écritures non validées refusées, pièce AN datée 1er janvier et cohérente avec l'année N+1.
- `catalogue_societes` : écriture **atomique** (`os.replace`), N marqué **clôturé** + lien
  **`exercice_precedent`** N→N+1, contrôles d'unicité (identifiant, inode, société/agence/année).
- `adaptateur_cloture_transport_sqlite.preparer_dossier_transport_sqlite` : migration N+1 via
  **Django en sous-processus isolé**, reprise des référentiels, reports, publication catalogue.
- Écran **« Choix de la société »** (`views_societes.choix_societe` + `choix_societe.html`) : liste
  regroupée Société→Agence→exercices, recherche, masquage des clôturés, ouverture via le poste
  compilé (redémarrage), réservé administrateur.

## Le seul manque pour « utiliser » : aucun déclencheur

Le moteur est **complet et testé** mais **n'est relié à rien** dans l'application : pas de commande,
pas de bouton. Seul l'ancien bouton « clôture dans la même base » (`comptabilite:cloture_exercice`)
existe — il ne sème pas de nouvelle base.

## Avance livrée ce jour (Claude, sans toucher au code de GPT)

- **Commande `python manage.py cloturer_exercice <identifiant>`**
  (`apps/core/management/commands/cloturer_exercice.py`) : enveloppe le moteur testé, déduit l'année
  N+1, le chemin et l'identifiant de la base N+1 depuis le catalogue, refuse proprement (messages
  français) un exercice inconnu / non SQLite / déjà clôturé / catalogue absent. 7 tests
  (`apps/core/tests_commande_cloture.py`). **Nouveau fichier : aucune collision avec GPT.**

## Roadmap reprise (plan §5, ordre proposé)

1. **Choix de la société** (§5-1) : ✅ écran fait. Reste : **peupler/entretenir le catalogue**
   (où le poste écrit `ERP_CATALOGUE_SOCIETES`, l'inscription de la base courante au 1er démarrage).
2. **Bouton « Clôturer l'exercice et ouvrir le suivant »** (§5-3, suite de ma commande) : vue +
   entrée de menu, exécutée via le poste compilé (comme `choix_societe`), avec confirmation.
3. **Menu Fichier global dédupliqué** (§5-2, mon #72) : étape A dé-duplication (audit déjà fait,
   `docs/retour/2026-11-08-claude-audit-menus.md`) — en attente du feu vert du propriétaire.
4. **Simulation : Arrêter + ouvrir/fermer comme une société** (§5-4).
5. **UX transverse** (fil d'Ariane Société·Exercice·Module, visibilité par droits) (§5-5).

## Coordination GPT
Je n'ai **pas** modifié les fichiers de clôture de GPT (`cloture_annuelle_sqlite.py`,
`reports_annuels_sqlite.py`, `reprise_configuration_sqlite.py`,
`adaptateur_cloture_transport_sqlite.py`, `catalogue_societes.py`). J'ai seulement **ajouté** une
commande qui les appelle. Le branchement du bouton (point 2) et le peuplement du catalogue (point 1)
sont à se répartir : je peux les prendre.
