# Audit du projet face au skill « ERP Transport Afrique Centrale »

Date : 26/10/2026. Skill installé dans `.claude/skills/erp-transport-afrique-centrale/` (SKILL.md + 14 références).
Méthode : lecture des 14 références, inspection du code (Django, `apps/*`), des tests (219 réussis) et reproduction
d'un défaut. **Aucun code n'a été modifié pour cet audit** (règle du skill, § 4 et réf. 13).

Légende : ✅ existant · 🟡 partiel · ❌ absent · ⚠️ incohérent ou défaut.

## 0. Défaut à corriger en priorité

⚠️ **Collision des numéros entre agences.** Les numéros des pièces (départs `DEP`, billets `BIL`, colis `COL`,
dépenses `DV`, pleins `CARB`, réparations `OR`) viennent d'un compteur local par année (`Sequence.suivant`,
`apps/transport/models.py:313, 559, 783, 960`, `apps/garage/models.py:93, 135`), alors que le champ `numero` est
unique (`apps/transport/models.py:289, 453, 711, 920`). Deux agences produisent donc les mêmes numéros. Effets :
- au siège, le 2e billet `BIL2026-000001` reçu est mis en **conflit** (copie non intégrée) ;
- dans une agence qui a reçu un départ d'une autre agence, la création d'un départ local peut **échouer**
  (reproduit : `IntegrityError UNIQUE constraint failed: transport_depart.numero`).
Le scénario sur 4 bases ne l'a pas détecté par hasard des numéros. Contraire au skill (réf. 01 « numéro métier propre
à son espace `agence + type + série` », réf. 09 « séries par agence »).
**Correction proposée** : préfixer les numéros par le code de l'agence dès que les échanges sont configurés
(`DLA-BIL2026-000001`), migration sans renumérotation des pièces existantes, test de collision sur deux agences.

## 1. Matrice existant / référentiel

| Domaine (réf.) | État | Constat dans le code | Écart principal |
|---|---|---|---|
| Un module par service, droits (01, 10) | ✅ | 5 logiciels de service + Comptabilité/Reporting (`apps/core/navigation.py`), accès par utilisateur et logiciel (`AccesLogiciel`), droits par menu (`DroitAcces`), contrôle serveur par URL (`apps/core/middleware.py`), portail filtré | Pas de **périmètre agence** (ABAC) : un utilisateur habilité voit les pièces de toutes les agences du dossier ; pas de profils types (guichetier, contrôleur…) prêts à l'emploi ; séparation saisie / approbation non systématique |
| Multi-compagnies, société juridique (01, 10) | 🟡 | Une base = une société (`Societe` unique) ; agences = sites | Isolation par base séparée (acceptable) ; pas de `legal_entity` multiple dans un dossier |
| Identifiants globaux (09, 10) | 🟡 ⚠️ | UUID sur écritures, transport, garage ; numéros locaux | Collision des numéros (§ 0) |
| Billetterie (02) | 🟡 | Départs, plan des sièges, vente, tronçons et correspondances avec partage du prix, report, annulation avec retenue, manifeste, billet imprimé | Pas de réservation temporaire, pas de **QR signé ni scan d'embarquement** (le statut « embarqué » est posé au départ), pas d'historique des statuts, remboursement non séparé de l'annulation, lignes sans arrêts intermédiaires, pas de quotas de sièges pour vendre sur le départ d'une autre agence |
| Reconnaissance des recettes (02, 07) | ✅ | Encaissement en 41911 / 41912, recette constatée au départ sur le véhicule (`Depart.partir`) | Comptes proposés à valider |
| Moyens de paiement (07) | ⚠️ | Billet payé en **Mobile Money passé dans la caisse espèces** de la gare (`apps/transport/models.py:519`) | Journal Mobile Money distinct (journal `MM` déjà créé) et confirmation de l'opérateur |
| Caisses, sessions, clôtures (07, 11) | ❌ | Opérations de caisse et rapport du jour | Pas de session de caisse par guichetier, de comptage, d'écart, de versement au chef de gare ni de fonds en transit entre agences |
| Colis (03) | 🟡 | Enregistrement, chargement, arrivée, remise par code, contre-remboursement entre agences (185), bordereau, recette au véhicule | Pas d'unités par colis ni de scans, pas d'états litige / perte / retour, un seul véhicule par envoi (pas de transbordement), pas d'arrivée avant synchronisation |
| Exploitation, voyages (04) | 🟡 | Départ, véhicule, chauffeur, partir / arriver, dépenses de route | Pas de clôture de voyage, de kilomètres départ/arrivée, de convoyeur, de contrôle de chevauchement d'un véhicule ni de contrôle bloquant des papiers ; **avance de mission du chauffeur** absente (les frais de route sont passés directement en charge) |
| Garage (04) | 🟡 | Ordres de réparation (pièces, MO interne/externe, fournisseur), pleins (compteur, consommation, station en compte), échéances des papiers | Pas de **magasin de pièces** (stock, sorties sur OR, pneus), ni de diagnostic / approbation |
| RH et paie (05) | 🟡 | Employés, rubriques sans taux imposé, avances, bulletins, validation, paiement, salaire du chauffeur sur son véhicule | Pas de contrats ni d'historique, de présences / congés, de rubriques datées et versionnées, de double validation RH → finance, de paiement par employé ; **imputation à 100 % du salaire au véhicule affecté** sans règle de ventilation écrite (le skill l'interdit sans politique validée) |
| Partenaires propriétaires (06) | ❌ | Champ `Vehicule.proprietaire` seulement | Contrats versionnés, décompte, compte auxiliaire, règlements, relevé, portail |
| Comptabilité (07) | 🟡 | Écritures équilibrées automatiques, comptes réglables (Paramètres transport), dimension **véhicule** sur les lignes, grand-livre et balance des véhicules, idempotence par uid | Règles de comptabilisation **dans le code** (pas de table versionnée à dates d'effet) ; écritures validées d'office (pas d'étape de validation comptable) ; pas de ventilation des frais communs |
| Synchronisation (08, 09) | 🟡 | Outbox dans la transaction, lots signés HMAC, inbox idempotente, manques détectés, attente de dépendance, relais par le siège, 4 bases testées | Pas d'**accusé de réception** renvoyé à l'agence, transport manuel (fichiers), pas de reprise après restauration d'une sauvegarde ancienne, monitoring limité |
| Rapports et clôtures (11) | 🟡 | Rapport journalier d'agence (billetterie par guichetier, colis, véhicules, garage, caisses), fiche et balance des véhicules, rentabilité | Pas de statut **complet / provisoire / partiellement synchronisé**, ni de clôtures (service, caisse, voyage, agence) et signatures, ni de rubrique anomalies |
| Audit (10) | 🟡 | Journal des événements, auteurs des pièces | Pas de trace des refus d'accès ni des lectures sensibles |
| Tests (12) | 🟡 | 219 tests, scénario 4 bases (billets, colis, correspondance, consolidation) | Tests de concurrence, de sécurité négative (IDOR), de perte d'ACK et de restauration à écrire |

## 2. Plan de développement proposé (chaque étape testée avant la suivante)

| Étape | Contenu | Pourquoi d'abord |
|---|---|---|
| **P0 — Corrections** | Numéros préfixés par l'agence (§ 0) ; Mobile Money vers son journal ; test de collision sur deux agences | Défauts qui faussent la consolidation |
| **P1 — Caisses et clôtures** | Session de caisse par guichetier (ouverture, encaissements, comptage, écart, approbation), versement au chef de gare, fonds en transit vers le siège ; clôture du service et de l'agence avec statut complet / provisoire et anomalies dans le rapport journalier | Contrôle des recettes au quotidien |
| **P2 — Exploitation** | Clôture du voyage, kilomètres, convoyeur, contrôle de chevauchement et des papiers, **avance de mission du chauffeur** à justifier au retour | Coût réel par voyage et par véhicule |
| **P3 — Partenaires propriétaires** | Contrats versionnés, décompte de période (commission, dépenses à la charge du propriétaire), compte auxiliaire, règlements partiels, relevé ; le portail viendra ensuite | Besoin métier fort, aujourd'hui absent |
| **P4 — Billetterie avancée** | QR signé et scan d'embarquement, historique des statuts, remboursement séparé, arrêts intermédiaires et sièges par tronçon, quotas pour vendre sur les départs d'autres agences | Anti-fraude et ventes inter-agences |
| **P5 — Magasin du garage** | Articles, entrées, sorties sur ordre de réparation, pneus, inventaires (réutiliser la Gestion commerciale si possible) | Coût exact des pièces |
| **P6 — RH** | Contrats et historique, présences / congés, rubriques datées, double validation, paiement par employé, **règle de ventilation** du salaire des chauffeurs (par voyage ou par jour) | Conformité et coûts équipages |
| **P7 — Socle** | Périmètre par agence (ABAC), accusés de réception des lots, monitoring de synchronisation, règles de comptabilisation versionnées, étape de validation comptable | Sécurité et contrôle interne |

Hypothèses retenues sans arbitrage : chaque agence garde sa base, le siège consolide ; les comptes, taux et règles
fiscales ou sociales restent à valider par l'expert-comptable (réf. 07, 14).

## 3. Points à arbitrer par l'utilisateur

1. Ordre des étapes P1 à P7 (je recommande P0, puis P1, P2, P3).
2. Partenaires : les modèles de contrat réellement pratiqués (commission sur recettes, partage de la marge, location
   forfaitaire) et les dépenses à la charge du propriétaire.
3. Salaire des chauffeurs : imputation au véhicule habituel (actuel) ou ventilation par voyage effectué.
4. Embarquement : un contrôleur avec un appareil qui scanne le QR, ou contrôle sur liste (manifeste) ?

## 4. Avancement (27/10/2026)

Choix de l'utilisateur :
- étapes P1, P2, P3 et P4, après P0 ;
- partenaires payés par **commission sur recettes** ou **location forfaitaire** ;
- salaire du chauffeur : **plusieurs options** selon l'accord (ventilation habituelle, par voyage, par jour, agence) ;
- embarquement : **contrôle sur liste** (manifeste), sans scanner QR.

| Étape | État | Où |
|---|---|---|
| P0 | ✅ | `Sequence.piece` (numéros par agence), journal Mobile Money |
| P1 | ✅ | `apps/transport/models_caisse.py` (sessions, transferts, clôtures, anomalies) |
| P2 | ✅ | `apps/transport/models_exploitation.py`, `Depart.partir` / `cloturer` |
| P3 | ✅ | `apps/partenaires` (contrats versionnés, décomptes, règlements, relevés) |
| P4 | 🟡 | arrêts et sièges par tronçon, embarquement sur liste, remboursement séparé, historique ; **quotas inter-agences à faire** |
| P5 à P7 | ❌ | à planifier |

Détail fonctionnel : `docs/V2_TRANSPORT_VOYAGEURS.md`, section « Étapes P0 à P4 ».
