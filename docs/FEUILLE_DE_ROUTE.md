# Feuille de route de l'ERP OHADA

Objectif fixé par le propriétaire : un logiciel qui aide vraiment les commerçants, qui reprend **toute
l'expérience de Sage 100** (que les utilisateurs connaissent), **comble ses manquements** et ajoute des **idées
adaptées à l'Afrique, d'abord au Cameroun**. Méthode : structurer d'abord comme Sage, améliorer ensuite ; retirer ce
qui ne sert pas.

## Phase 1 — Reproduire Sage 100 (en cours)

| Domaine | État | Source attendue |
|---|---|---|
| Menus Gestion commerciale | ✅ découpage officiel V11/V12 | — |
| Menus Comptabilité | 🟡 menu Etat officiel ; reste à vérifier | GPT, suite du lot 1 (découpage Comptabilité complet) |
| Autorisations d'accès | 🟡 fonctionnelles ; libellés V12 à confirmer | GPT R3 / captures Sage |
| Espace de travail (fenêtres, barre verticale, accueil) | 🟡 fait ; détails V12 à confirmer | GPT R4 |
| Fenêtres de sélection des états | 🟡 fait pour tous les états ; critères exacts et formats de sélection à faire | GPT R14 / captures Sage |
| Transformations et règles de saisie | 🟡 règles officielles V12.20 appliquées (encours, compte bloqué, achats) | GPT lot 3 (suite) |
| Listes, fiches, saisie, raccourcis, messages | 🔴 à aligner | GPT R9, R10, R14 |
| Fiscalité Cameroun / SYSCOHADA | 🟡 TVA facultative, CAC, régimes ; plan complet et AIR / précompte à venir | GPT lot 2 (suite) |
| Reprise des données Sage | ✅ outil en lecture seule | GPT R12 pour confirmer les colonnes |

### Écarts connus avec Sage (sources : skills GPT)

- **Avoirs financiers d'achat** (bon d'avoir financier, facture d'avoir) : Sage corrige la **valeur** du stock (mouvement
  « en montant », sans quantité) ; l'ERP ne le fait pas encore. Test de conformité : `apps/commercial/tests_conformite_sage.py`.
- **Adresses de livraison et de facturation** distinctes sur la fiche client (C11) : une seule adresse dans l'ERP.
- **Centrale d'achat** et tarifs particuliers (C13), **calendriers fournisseurs** (C14) : absents.

## Phase 2 — Combler les manquements de Sage (à prioriser avec le propriétaire)

- Version web consultable partout, en plus du poste Windows.
- Journal des événements (qui a fait quoi) et sauvegarde / restauration simples. ✅
- Indicateurs à l'accueil, contrôles et alertes compréhensibles.
- Facture PDF propre, envoi par e-mail ou WhatsApp.

## Phase 3 — Adapter à la réalité camerounaise (idées à valider)

- Encaissements **Mobile Money** (MTN MoMo, Orange Money) et rapprochement.
- **Relances clients par SMS / WhatsApp**.
- Ventes à crédit, suivi des petits clients et de leur encours.
- **Fonctionnement malgré les coupures** (réseau, électricité) puis synchronisation.
- Plusieurs agences / dépôts éloignés, consolidation.
- Rien d'imposé : TVA, NIU, RCCM facultatifs (réalité des PME). ✅

Les livraisons de GPT alimentent la phase 1 ; chaque point est intégré seulement s'il est sourcé.
