# Liaison Gestion commerciale ↔ Comptabilité : correspondance avec le dossier de recherche

Source : dossier `docs/recherche/sage-liaisons-comptabilite-claude/` (recherche documentaire GPT du 21/10/2026, version 0.1).
Les propositions de ce dossier sont des **choix de conception**, pas des comportements Sage certifiés. Ses questions
ouvertes (INCONNUES U01–U18) restent ouvertes ; ses scénarios n'ont pas été exécutés sur Sage.

## 1. Correspondance exigence / code existant / manque / décision

| Exigence du dossier | Code existant | Manque | Modification / décision ERP |
|---|---|---|---|
| Société juridique ≠ dossier technique ≠ nom affiché | Une base = une société (`Societe.get()`) ; Gestion commerciale, Comptabilité et Reporting dans la même base | Pas de multi-société dans une base | **Décision** : une base par société (pas de risque d'écrire chez la mauvaise société). Le bloc « Fichiers liés » affiche la société réellement liée. |
| Référentiel commun plutôt que copies synchronisées | Tiers, comptes, journaux, banques, taxes : une seule fiche pour tous les logiciels | — | Rien à synchroniser : vue commune contrôlée (contrat, § Référentiels). |
| Code tiers unique (T12, T13) | `Tiers.code` unique en base | Recherche de doublon par nom | Unicité garantie par la base (deux créations simultanées : une seule réussit). Doublon par nom : à proposer en revue manuelle (à faire). |
| Collectif choisi et validé (T14) | `Tiers.compte_collectif`, défaut 411 / 401 | — | Les écritures gardent le compte appliqué ; changer le collectif ne réécrit pas l'historique. |
| Tiers payeur distinct | — | Absent | **À faire** (Sage : tiers payeur sur la fiche). Non bloquant. |
| Sommeil / blocage / encours (T18) | `actif`, `compte_bloque`, code risque (Avertir / Bloquer) | — | Comportements distincts déjà en place et testés. |
| Suppression d'un tiers utilisé (T19) | Liens protégés (documents, règlements, écritures) | — | Suppression refusée ; désactivation à la place. Testé. |
| Chaîne brouillon → validé → comptabilisé | Validation = comptabilisation immédiate, dans une seule transaction | Pas de lot différé (Sage : Mise à jour comptable) | **Décision** : comptabilisation à la validation (tout ou rien). Un lot différé façon Sage pourra être ajouté en option. |
| Brouillon jamais comptabilisé (T21) | Seule la validation crée l'écriture | — | Testé. |
| Période ou journal fermé (T25) | `Journal.verifier_periode` | — | La validation est refusée en entier : ni écriture, ni stock, ni changement de statut. Testé. |
| Pas de doublon au rejeu (T28, T40) | `comptabiliser_document` / `_reglement` : une pièce = une écriture (lien un-à-un) | — | Testé. |
| Écriture comptabilisée non effaçable | Écriture validée non supprimable | — | Corrections par avoir ou écriture d'extourne. |
| **Rapprochement des flux avant clôture (T44)** | — | **Absent** | **Ajouté** : Etat › Analyse et contrôles › **Contrôle de la liaison commerciale**. La clôture est bloquée tant qu'il reste une anomalie. |
| Droits séparés : consulter, créer, valider, comptabiliser, payer (D02–D07) | Droits par menu, 4 niveaux, contrôlés côté serveur (web et API) ; accès Utilisateur / Invité / Aucun par logiciel | Pas de droit « comptabiliser » distinct de « valider une facture » | **Décision** : valider une facture vaut comptabilisation (validation immédiate). Restreindre « Factures » à la consultation empêche donc aussi de comptabiliser. |
| Journal des opérations | Journal des événements (création, modification, validation, suppression, connexion) | — | Utilisateur demandeur tracé. |
| Connecteur vers un Sage réel (lots, boîte d'envoi, idempotence distante) | Reprise Sage en **lecture seule** uniquement | Aucun envoi vers Sage | **Hors périmètre** : aucune écriture dans une base Sage. Un connecteur exigerait d'abord la version, le canal et les droits relevés (U01, U07, U17). |

## 2. Contrôle de la liaison commerciale (ajout ERP)

Pour la période choisie :
- **flux** : nombre de factures / avoirs de vente et d'achat, règlements, totaux HT, taxes, TTC, et nombre de pièces conformes ;
- **anomalies** :
  - pièce validée sans écriture ;
  - écriture non validée ;
  - montant différent sur le compte du tiers ;
  - écriture VT / AC qui cite une pièce commerciale introuvable (doublon ou pièce supprimée).

Une balance équilibrée ne révèle ni une facture oubliée ni une facture passée deux fois : ce contrôle le fait.

## 3. Ce qui exige encore une observation sur Sage

U02 (égalité des noms de société), U04 (visibilité immédiate de chaque champ créé depuis chaque module), U06 (noms
et héritage exacts des droits V12), U12 (règlements unifiés), U16 (effet d'un renommage sur l'historique), U17
(idempotence native des transferts Sage).
