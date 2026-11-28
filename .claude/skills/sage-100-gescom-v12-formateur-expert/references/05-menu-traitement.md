# 05 — Menu Traitement [DOC-V12]

**Source majeure : S1, pages 11 à 13.** Menu central des transactions. Les types de documents sont confirmés dans le découpage ; les colonnes/actions précises dépendent du contexte et du profil.

## Documents des ventes

Chemin de regroupement : `Traitement > Documents des ventes`.

- Devis.
- Bon de commande.
- Préparation de livraison.
- Bon de livraison.
- Bon de retour.
- Bon d'avoir financier.
- Facture.
- Facture de retour.
- Facture d'avoir.

À auditer dans les listes et fiches : pièces/souches, dates, client, représentant, devise, dépôt, lignes articles, quantités, remises, prix, taxes, totaux, règlements, validation, impression, historique, transformation et droits.

## Documents des achats

Chemin : `Traitement > Documents des achats`.

- Demande d'achat ; Préparation de commande ; Bon de commande.
- Bon de livraison ; Bon de retour ; Bon d'avoir financier.
- Facture ; Facture de retour ; Facture d'avoir.
- Gestion de l'acheteur en en-tête et sur les lignes, gestion du bon à payer : dépendances d'édition.

À auditer : fournisseur, commande, réception, facturation, règlement, rapprochements et différences entre types de documents.

## Documents des stocks

Chemin : `Traitement > Documents des stocks`.

- Mouvement d'entrée.
- Mouvement de sortie.
- Dépréciation de stock (selon édition).
- Mouvement de transfert.
- Préparation de fabrication.
- Ordre de fabrication (option Fabrication).
- Bon de fabrication.

À auditer : numéro/type de mouvement, date, origine, dépôt source/destination, article, quantité, valorisation, lot/série, motif, contrôle/validation.

## Autres branches de Traitement

| Ensemble | Fonctions principales / remarques |
|---|---|
| Documents internes | Option Services selon édition |
| Sage Connect / Sage eFacture | Transmission/réception et intégrations, selon configuration, période et service connecté |
| Gestion des affaires | Projets, avancement, réalisé, facturation à l'affaire, interrogation du compte affaire (option Services) |
| Gestion des fabrications | Documents/projets, avancement, simulations, calcul d'approvisionnement, consultations (option Fabrication) |
| Gestion des livraisons clients | Préparation, validation, livraison des commandes ; préparation et validation avancées selon option Logistique |
| Gestion des réceptions fournisseurs | Réceptions avancées, option Logistique |
| Contrôle qualité | Option Logistique |
| Traitement par lot | Facturation périodique, réapprovisionnement, envoi commandes fournisseurs, réception devis confirmés |
| Planning des ressources | Réservations, affectations, consultation/contrôle selon options |
| Gestion du bon à payer | Selon édition |
| Gestion des règlements | Saisie règlements clients, fournisseurs, génération et paiements en ligne |
| Modèles et prestations types | Option Services |
| Abonnements | Clients/fournisseurs, génération, reconduction, mise à jour des pièces : option Services |
| Contremarque | Commandes fournisseurs, préparations fabrication, affectations livraisons / fabrications : options |
| Gestion des comptes | Clients, fournisseurs, articles, affaires, collaborateurs et ressources |
| Suivi traçabilité série/lot | Option Traçabilité |
| Gestion des besoins | Besoins / approvisionnement |
| Traçabilité des documents | Chaîne documentaire |
| Recherche de documents | En-têtes et lignes de documents |
| Saisie d'inventaire | Comptages et ajustements |
| Événements agenda | Événements / suivi |
| Mise à jour de la comptabilité | Factures achat/vente, règlements, engagements selon édition |
| Archivage | Report de stock, archives, suppressions encadrées |
| Clôture période | Clôture des périodes |
| Sauvegarde fiscale des données | Génération réglementaire |

## Règles d'analyse des documents

1. **Type de pièce ≠ numéro de pièce** : distinguer le type métier de sa souche.
2. **Commande ≠ livraison ≠ facture** : ne pas déduire le même impact stock ou comptabilité pour tous les états sans analyse des paramètres Sage.
3. **Retour / avoir ≠ document d'origine** : contrôler effet, validation, liens et états.
4. **Mouvement inter-dépôts** : relever source et destination, sans l'interpréter par défaut comme une vente.
5. **Réglages** : le contenu exact de la fenêtre peut changer selon domaine, édition, options et droits.
6. **Actions sensibles** : ne pas réaliser validation, purge, transfert comptable, clôture ou suppression lors d'un inventaire de l'interface.
