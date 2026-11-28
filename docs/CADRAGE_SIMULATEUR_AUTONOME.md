# Cadrage du simulateur autonome (G-SIM-04/05) — Claude, 2026-11-10

But : un simulateur « terrain réel » multi-agences, utilisable pour **tester et démontrer** le
logiciel sans saisie, dans un **dossier séparé** (jamais la vraie société). Chantier commencé par le
propriétaire (point 3 du tableau d'avancement, ~15 %).

## Ce qui existe déjà (ne pas refaire)
- **Génération métier** : `apps/transport/management/commands/simulation.py` joue des mois complets
  (8 gares, 60 cars dont 15 partenaires, 300 salariés, billets, bagages, colis, garage, magasin,
  paie, décomptes propriétaires…), **mois par mois**, chaque jour « à sa date ». Scénarios complets
  (transit, transvasement, incidents, retraits) en option.
- **Dossier séparé portable** : `apps/core/dossiers_simulation.py` (base `simulation.sqlite3`,
  manifeste `dossier.json`, **verrou de génération**, état « preparation/prete »).
- **UI Administration du poste → Simulation** : créer / supprimer une simulation, et **exporter**
  une ancienne simulation en dossier société importable (G-SIM-01/02/03 faits).

## Manques identifiés (REFONTE_MENUS §3)
1. **Arrêter une génération en cours** proprement (après la tranche en cours ; données déjà
   consultables ; marquée « interrompue »). ← **socle livré ce jour**.
2. **Ouvrir / Fermer une simulation comme une société** : la simulation apparaît dans
   « Choix de la société » marquée « simulation », on l'ouvre pour consulter/continuer.
3. **État visible** (en cours / terminé / interrompu) et reprise d'une génération longue par tranches.

## Livré ce jour (socle de l'arrêt coopératif)
- `apps/core/dossiers_simulation.py` : `demander_arret(dossier)`, `arret_demande(dossier)`,
  `effacer_arret(dossier)` (marqueur `.arreter`, protégé contre les liens symboliques).
- `apps/transport/.../simulation.py` : la génération efface le marqueur au départ, puis **vérifie
  l'arrêt à la fin de chaque mois** ; si demandé, elle **termine la tranche en cours** et s'arrête
  (`interrompu=True`), sans rien effacer. 5 tests (`tests_simulation_arret`).

## Logiciel autonome portable (livré)
Demande du propriétaire : un **logiciel de simulation autonome séparé**, en **dossier portable**
(zip, sans installation), qui **ouvre directement l'atelier de simulation**.
- Mode `ERP_SIMULATEUR=1` du lanceur (`deploy/executable/erp_ohada.py`) : licence désactivée,
  compte par défaut `simulateur` / `simulateur`, ouverture du navigateur directement sur
  l'écran Simulation (`/poste/?onglet=simulation`), données dans un dossier portable à côté du
  programme (`donnees-simulateur`).
- `deploy/windows/SIMULATEUR.bat` (+ `LISEZ-MOI-SIMULATEUR.txt`) : on décompresse et on
  double-clique ; aucun installateur, aucun service, aucune licence.
- CI : nouvel artefact **`ERP-OHADA-Simulateur`** (le programme Transport compilé + le .bat +
  la notice), à télécharger et lancer. **À valider sous Windows par le propriétaire.**

## Reste à faire (prochaines tranches)
- **Bouton « Arrêter »** dans Administration du poste → Simulation, actif pendant une génération
  (`generation_active`), qui appelle le poste pour déposer `demander_arret` dans le dossier.
  Action `simulation_arreter` côté poste compilé (`deploy/executable`), à valider sous Windows.
- **État « interrompue »** écrit dans le manifeste `dossier.json` + affiché (en cours / terminé /
  interrompu), et **reprise** (relancer les mois restants) depuis l'écran.
- **Ouvrir/Fermer la simulation comme une société** via le catalogue multi-sociétés
  (entrée marquée « simulation », lecture/continuation), en s'appuyant sur le travail multi-sociétés.
- Décider avec le propriétaire du **profil « terrain réel »** par défaut (nombre d'agences,
  véhicules, volume, scénarios) pour un bouton « Simulation réaliste » en un clic.
