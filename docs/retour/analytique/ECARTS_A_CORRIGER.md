# Écarts restants — comptabilité analytique (skill erp-transport-analytique-multiplans)

État au 26/10/2026, branche `ccr-5592a371-fusjt2`. « Fait » = codé et testé ; le reste est listé ici, sans prétendre
qu'il existe.

| # | Écart | Pourquoi ce n'est pas fait | Décision ou donnée attendue |
|---|---|---|---|
| 1 | **Ventilation fractionnée** (une ligne 100 000 → 60 000 car A + 40 000 car B dans un même plan ; refus de 100 % + 100 %) | Le moteur attribue une ligne à un seul élément par axe. Une table de ventilations dérivées (proposée par le skill) est un changement de structure : il faut d'abord savoir quelles charges répartir et selon quelles clés. | Liste des charges communes à répartir (assurance flotte, siège, loyers multi-gares…) et clés (km, voyages, places-km). Rien n'est réparti d'office en attendant. |
| 2 | ~~Canaux de vente~~ — **FAIT** (26/10) | Décision : le canal est le **point de vente** (guichet d'agence ou point rattaché à une agence). Axes Agences, Points de vente (recette répartie au prorata exact des billets) et Villes. | — |
| 3 | ~~Agence ≠ gare~~ — **FAIT** (26/10) | Gare de type « Agence » (plusieurs par grande ville) ou « Point de vente » rattaché. | — |
| 4 | ~~Droits par gare / par propriétaire~~ — **DÉCIDÉ** | Chaque agence a son propre serveur ; les droits sont réglés localement sur chaque serveur (Fichier › Autorisations d'accès). | — |
| 5 | **Fraîcheur des données par agence** sur chaque état | Visible dans Fichier › Échanges ; pas encore en bandeau sur les états du siège. Synchronisation : export / import de fichiers signés (existant), réseau (Internet ou tunnel) à décider. | Choix du mode de liaison direction ↔ agences. |
| 6 | **Exports PDF / Excel** | Impression navigateur (A4) et CSV ouvrable dans Excel disponibles ; pas de fichier PDF ou XLSX natif. | Format souhaité. |
| 7 | **Client bureau Windows** | La fenêtre « Comptabilité analytique » ouvre les états dans le navigateur (pas d'écran natif). | — |
| 8 | **Services : salaires répartis sur un véhicule** comptés « Conduite » | La ligne de paie ne garde pas l'employé ; un mécanicien imputé sur un véhicule serait compté en Conduite. | Accepter la règle, ou ajouter l'employé sur la ligne de paie. |
