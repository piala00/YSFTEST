# Écarts restants — comptabilité analytique (skill erp-transport-analytique-multiplans)

État au 28/11/2026, branche de travail GPT issue de `ccr-5592a371-fusjt2`. « Fait » = codé et testé ; le reste est listé ici, sans prétendre
qu'il existe.

| # | Écart | Pourquoi ce n'est pas fait | Décision ou donnée attendue |
|---|---|---|---|
| 1 | **Ventilation fractionnée** (une ligne 100 000 → 60 000 car A + 40 000 car B dans un même plan ; refus de 100 % + 100 %) | Le moteur attribue une ligne à un seul élément par axe. Une table de ventilations dérivées (proposée par le skill) est un changement de structure : il faut d'abord savoir quelles charges répartir et selon quelles clés. | Liste des charges communes à répartir (assurance flotte, siège, loyers multi-gares…) et clés (km, voyages, places-km). Rien n'est réparti d'office en attendant. |
| 2 | ~~Canaux de vente CAN~~ — **FAIT** (27/11) | CAN est distinct du point de vente : GUICHET, WEB, APP, REVENDEUR. Billets, colis payés, retenues d'annulation et ports dus ; le canal source est conservé pour les pièces reçues d'une autre agence. Tests SQLite et SQL Server. | — |
| 3 | ~~Agence ≠ gare~~ — **FAIT** (26/10) | Gare de type « Agence » (plusieurs par grande ville) ou « Point de vente » rattaché. | — |
| 4 | ~~Droits par gare / par propriétaire~~ — **DÉCIDÉ** | Chaque agence a son propre serveur ; les droits sont réglés localement sur chaque serveur (Fichier › Autorisations d'accès). | — |
| 5 | ~~Fraîcheur des données par agence~~ — **FAIT** (27/11) | Bandeau sur le plan, les balances, les états détaillés, les budgets et les états véhicules/propriétaires au siège. Source : `Agence.derniere_reception` et `sequence_integree`, mises à jour à l'import d'un lot. Les agences sans lot sont visibles sans être déclarées hors ligne ; aucune sonde réseau ni seuil arbitraire n'est utilisé. | — |
| 6 | ~~Export Excel XLSX et PDF natif~~ — **FAIT** (27/11) | Les balances d'axe et états détaillés exportent CSV, XLSX et PDF natif multipage (A4 paysage, A3 pour les journaux larges), avec en-têtes répétés, période et pagination. Les montants et pièces proviennent des mêmes états que l'écran ; l'export ne crée aucune écriture. | Tests : `apps.comptabilite.tests_analytique_exports`. |
| 7 | **Client bureau Windows** | La fenêtre « Comptabilité analytique » ouvre les états dans le navigateur (pas d'écran natif). | — |
| 8 | **Correction soumise — PR #44, validation CI en cours** : service réel des salaires répartis sur véhicule | La paie conserve désormais la section historique `SV-{service}` sur chaque charge, même si `vehicule_id` est renseigné. Le véhicule et le service sont ainsi deux dimensions simultanées ; une modification ultérieure de la fiche salarié ne reclasse pas les paies déjà validées. | Test ajouté : mécanicien fictif affecté à un car, rapprochement Services + Véhicules, puis changement du service courant. Résultat final à confirmer par CI. |
