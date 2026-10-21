# Matrice de traçabilité — Gestion commerciale

Générée par `python manage.py audit_navigation` à partir de `apps/core/navigation.py`.
Méthode : skill `sage-100-gescom-v12-ui` (référence 10, phase D) — élément Sage → écran ERP → état → preuve.

## Synthèse

| État | Commandes |
|---|---|
| ✅ Réalisé | 73 |
| ✅ Commande d'interface | 14 |
| ↗ Autre logiciel de l'ERP | 14 |
| ⬜ Grisé (non développé) | 110 |
| **Total des commandes** | **211** |

| Niveau de preuve | Commandes | Signification |
|---|---|---|
| AJOUT-ERP | 9 | Ajout propre à l'ERP OHADA (absent de Sage) |
| DOC-V12 | 182 | Cité dans le découpage officiel Sage 100 Gestion commerciale V12.10 |
| ERG-CLASSIQUE | 20 | Ergonomie Sage classique, à vérifier sur une installation V12 |

## Détail par menu

| Chemin | Élément | Preuve | État dans l'ERP | Écran / action |
|---|---|---|---|---|
| **Fichier** | | | | |
| Fichier | Nouveau | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier | Ouvrir | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier | Favoris | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier | Fermer | DOC-V12 | ✅ Commande d'interface | `action « fermer »` |
| Fichier | **Paramètres société** | DOC-V12 | ▸ Sous-menu |  |
| Fichier › Paramètres société | Identification | DOC-V12 | ✅ Réalisé | `/commercial/societe/` |
| Fichier › Paramètres société | Vos contacts | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier › Paramètres société | Sécurité | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier › Paramètres société | Articles | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier › Paramètres société | Comptes généraux | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier › Paramètres société | **Tiers** | DOC-V12 | ▸ Sous-menu |  |
| Fichier › Paramètres société › Tiers | Catégories tarifaires | DOC-V12 | ✅ Réalisé | `/commercial/categories-tarifaires/` |
| Fichier › Paramètres société | Ressources | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier › Paramètres société | Analytique | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier › Paramètres société | Tva et taxes | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier › Paramètres société | Contacts | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier › Paramètres société | International | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier › Paramètres société | Banques | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier › Paramètres société | Documents | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier › Paramètres société | Logistique | DOC-V12 | ✅ Réalisé | `/commercial/societe/?section=logistique` |
| Fichier › Paramètres société | Comptabilisation | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier › Paramètres société | Echanges de données | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier › Paramètres société | Agenda | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier › Paramètres société | Factures électroniques | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier › Paramètres société | Colonnage | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier | Lire les informations | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier | Configuration système et partage | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier | Autorisations d'accès | DOC-V12 | ✅ Réalisé | `/commercial/autorisations/` |
| Fichier | Journal des événements | AJOUT-ERP | ✅ Réalisé | `/commercial/journal-evenements/` |
| Fichier | Importer | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier | Exporter | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier | Format import/export paramétrable | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier | Communication site à site | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier | Paiement en ligne | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier | Mise en page | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier | Imprimer… | ERG-CLASSIQUE | ✅ Commande d'interface | `action « imprimer »` |
| Fichier | Format d'impression | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier | Impression différée | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier | Outils | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fichier | Quitter | ERG-CLASSIQUE | ✅ Commande d'interface | `action « quitter »` |
| **Édition** | | | | |
| Édition | Annuler | ERG-CLASSIQUE | ✅ Commande d'interface | `action « annuler »` |
| Édition | Couper | ERG-CLASSIQUE | ✅ Commande d'interface | `action « couper »` |
| Édition | Copier | ERG-CLASSIQUE | ✅ Commande d'interface | `action « copier »` |
| Édition | Coller | ERG-CLASSIQUE | ✅ Commande d'interface | `action « coller »` |
| Édition | Effacer | ERG-CLASSIQUE | ✅ Commande d'interface | `action « effacer »` |
| Édition | Sélectionner tout | ERG-CLASSIQUE | ✅ Commande d'interface | `action « selectionner_tout »` |
| Édition | Ajouter | ERG-CLASSIQUE | ✅ Commande d'interface | `action « ajouter »` |
| Édition | Voir/Modifier | ERG-CLASSIQUE | ✅ Commande d'interface | `action « modifier »` |
| Édition | Supprimer | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Édition | Dupliquer | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Édition | Précédent | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Édition | Suivant | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Édition | Rechercher | ERG-CLASSIQUE | ✅ Commande d'interface | `action « rechercher »` |
| Édition | Atteindre | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Édition | Inverseur | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Édition | Calculette Sage | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Édition | Journal de traitement | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| **Structure** | | | | |
| Structure | Familles | DOC-V12 | ✅ Réalisé | `/commercial/familles/` |
| Structure | Articles | DOC-V12 | ✅ Réalisé | `/commercial/articles/` |
| Structure | Nomenclatures | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure | **Comptabilité** | DOC-V12 | ▸ Sous-menu |  |
| Structure › Comptabilité | Plan comptable | DOC-V12 | ↗ Autre logiciel de l'ERP | `/comptabilite/plan/` |
| Structure › Comptabilité | Plan analytique | DOC-V12 | ↗ Autre logiciel de l'ERP | `/comptabilite/structure/sections/` |
| Structure › Comptabilité | **Taux de taxes** | DOC-V12 | ▸ Sous-menu |  |
| Structure › Comptabilité › Taux de taxes | TVA/ débit - Vente de biens | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure › Comptabilité › Taux de taxes | TVA/ encaissement - Prestation de services | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure › Comptabilité › Taux de taxes | TP/ HT | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure › Comptabilité › Taux de taxes | TP/ TTC | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure › Comptabilité › Taux de taxes | TP/ poids | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure › Comptabilité › Taux de taxes | Surtaxe | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure › Comptabilité | Codes journaux | DOC-V12 | ↗ Autre logiciel de l'ERP | `/comptabilite/journaux/` |
| Structure › Comptabilité | Banques | DOC-V12 | ↗ Autre logiciel de l'ERP | `/comptabilite/structure/banques/` |
| Structure › Comptabilité | Modèle de règlement | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure › Comptabilité | Modèle de grille | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure | Codes affaires | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure | Clients | DOC-V12 | ✅ Réalisé | `/commercial/clients/` |
| Structure | Fournisseurs | DOC-V12 | ✅ Réalisé | `/commercial/fournisseurs/` |
| Structure | **Barèmes** | DOC-V12 | ▸ Sous-menu |  |
| Structure › Barèmes | Commissions représentants | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure › Barèmes | Rabais, remises et ristournes clients | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure › Barèmes | Rabais, remises et ristournes fournisseurs | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure › Barèmes | Soldes et promotions clients | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure › Barèmes | Soldes et promotions fournisseurs | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure | Glossaires | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure | Modèles enregistrement | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure | Ressources | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure | Centre de charges | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure | Collaborateurs | DOC-V12 | ⬜ Grisé (non développé) |  |
| Structure | Dépôts de stockage | DOC-V12 | ✅ Réalisé | `/commercial/depots/` |
| **Traitement** | | | | |
| Traitement | **Documents des ventes** | DOC-V12 | ▸ Sous-menu |  |
| Traitement › Documents des ventes | Tous les documents des ventes | AJOUT-ERP | ✅ Réalisé | `/commercial/documents/ventes/` |
| Traitement › Documents des ventes | Devis | DOC-V12 | ✅ Réalisé | `/commercial/documents/ventes/?type=DEVIS` |
| Traitement › Documents des ventes | Bon de commande | DOC-V12 | ✅ Réalisé | `/commercial/documents/ventes/?type=COMMANDE` |
| Traitement › Documents des ventes | Préparation de livraison | DOC-V12 | ✅ Réalisé | `/commercial/documents/ventes/?type=PREPARATION` |
| Traitement › Documents des ventes | Bon de livraison | DOC-V12 | ✅ Réalisé | `/commercial/documents/ventes/?type=LIVRAISON` |
| Traitement › Documents des ventes | Bon de retour | DOC-V12 | ✅ Réalisé | `/commercial/documents/ventes/?type=RETOUR` |
| Traitement › Documents des ventes | Bon d'avoir financier | DOC-V12 | ✅ Réalisé | `/commercial/documents/ventes/?type=AVOIR_FINANCIER` |
| Traitement › Documents des ventes | Facture | DOC-V12 | ✅ Réalisé | `/commercial/documents/ventes/?type=FACTURE` |
| Traitement › Documents des ventes | Facture de retour | DOC-V12 | ✅ Réalisé | `/commercial/documents/ventes/?type=FACTURE_RETOUR` |
| Traitement › Documents des ventes | Facture d'avoir | DOC-V12 | ✅ Réalisé | `/commercial/documents/ventes/?type=AVOIR` |
| Traitement | **Documents des achats** | DOC-V12 | ▸ Sous-menu |  |
| Traitement › Documents des achats | Tous les documents des achats | AJOUT-ERP | ✅ Réalisé | `/commercial/documents/achats/` |
| Traitement › Documents des achats | Demande d'achat | DOC-V12 | ✅ Réalisé | `/commercial/documents/achats/?type=ACHAT_DEMANDE` |
| Traitement › Documents des achats | Préparation de commande | DOC-V12 | ✅ Réalisé | `/commercial/documents/achats/?type=ACHAT_PREPARATION` |
| Traitement › Documents des achats | Bon de commande | DOC-V12 | ✅ Réalisé | `/commercial/documents/achats/?type=ACHAT_COMMANDE` |
| Traitement › Documents des achats | Bon de livraison | DOC-V12 | ✅ Réalisé | `/commercial/documents/achats/?type=ACHAT_RECEPTION` |
| Traitement › Documents des achats | Bon de retour | DOC-V12 | ✅ Réalisé | `/commercial/documents/achats/?type=ACHAT_RETOUR` |
| Traitement › Documents des achats | Bon d'avoir financier | DOC-V12 | ✅ Réalisé | `/commercial/documents/achats/?type=ACHAT_AVOIR_FINANCIER` |
| Traitement › Documents des achats | Facture | DOC-V12 | ✅ Réalisé | `/commercial/documents/achats/?type=ACHAT_FACTURE` |
| Traitement › Documents des achats | Facture de retour | DOC-V12 | ✅ Réalisé | `/commercial/documents/achats/?type=ACHAT_FACTURE_RETOUR` |
| Traitement › Documents des achats | Facture d'avoir | DOC-V12 | ✅ Réalisé | `/commercial/documents/achats/?type=ACHAT_AVOIR` |
| Traitement › Documents des achats | Gestion acheteur entête et ligne de document | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement › Documents des achats | Gestion du Bon à payer | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | **Documents des stocks** | DOC-V12 | ▸ Sous-menu |  |
| Traitement › Documents des stocks | Tous les documents des stocks | AJOUT-ERP | ✅ Réalisé | `/commercial/documents/stocks/` |
| Traitement › Documents des stocks | Mouvement d'entrée | DOC-V12 | ✅ Réalisé | `/commercial/documents/stocks/?type=STOCK_ENTREE` |
| Traitement › Documents des stocks | Mouvement de sortie | DOC-V12 | ✅ Réalisé | `/commercial/documents/stocks/?type=STOCK_SORTIE` |
| Traitement › Documents des stocks | Mouvement de transfert | DOC-V12 | ✅ Réalisé | `/commercial/documents/stocks/?type=STOCK_VIREMENT` |
| Traitement › Documents des stocks | Dépréciation de stock | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement › Documents des stocks | Préparation de fabrication | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement › Documents des stocks | Ordre de fabrication | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement › Documents des stocks | Bon de fabrication | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | Documents internes | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | **Sage Connect** | DOC-V12 | ▸ Sous-menu |  |
| Traitement › Sage Connect | Accéder à la société | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement › Sage Connect | Transmission des factures clients | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement › Sage Connect | Réception des factures fournisseurs | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | Facture électronique | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | Gestion des affaires | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | Gestion des fabrications | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | Gestion des livraisons clients | DOC-V12 | ✅ Réalisé | `/commercial/documents/ventes/?type=COMMANDE&statut=VALIDE` |
| Traitement | Gestion des réceptions fournisseurs | DOC-V12 | ✅ Réalisé | `/commercial/documents/achats/?type=ACHAT_COMMANDE&statut=VALIDE` |
| Traitement | Contrôle qualité | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | Traitement par lot | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | Gestion du planning des ressources | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | Gestion du bon à payer | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | **Gestion des règlements** | DOC-V12 | ▸ Sous-menu |  |
| Traitement › Gestion des règlements | Gestion des règlements clients | DOC-V12 | ✅ Réalisé | `/commercial/reglements/?sens=E` |
| Traitement › Gestion des règlements | Gestion des règlements fournisseurs | DOC-V12 | ✅ Réalisé | `/commercial/reglements/?sens=D` |
| Traitement › Gestion des règlements | Génération des règlements | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement › Gestion des règlements | Intégration des paiements en ligne | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | Modèles et prestations types | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | Abonnements | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | Contremarque | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | **Gestion des comptes** | DOC-V12 | ▸ Sous-menu |  |
| Traitement › Gestion des comptes | Gestion des clients | DOC-V12 | ✅ Réalisé | `/commercial/clients/?vue=comptes` |
| Traitement › Gestion des comptes | Gestion des fournisseurs | DOC-V12 | ✅ Réalisé | `/commercial/fournisseurs/?vue=comptes` |
| Traitement › Gestion des comptes | Gestion des articles | DOC-V12 | ✅ Réalisé | `/commercial/stock/?vue=comptes` |
| Traitement › Gestion des comptes | Gestion des affaires | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement › Gestion des comptes | Gestion des collaborateurs | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement › Gestion des comptes | Gestion des ressources | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement › Gestion des comptes | Suivi traçabilité série/ lot | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | Gestion des besoins | DOC-V12 | ✅ Réalisé | `/commercial/besoins/` |
| Traitement | Traçabilité des documents | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | **Recherche de documents** | DOC-V12 | ▸ Sous-menu |  |
| Traitement › Recherche de documents | Entêtes de documents | DOC-V12 | ✅ Réalisé | `/commercial/recherche/entetes/` |
| Traitement › Recherche de documents | Lignes de documents | DOC-V12 | ✅ Réalisé | `/commercial/recherche/lignes/` |
| Traitement | Saisie d'inventaire | DOC-V12 | ✅ Réalisé | `/commercial/stock/inventaires/` |
| Traitement | Evénements agenda | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | **Mise à jour de la comptabilité** | DOC-V12 | ▸ Sous-menu |  |
| Traitement › Mise à jour de la comptabilité | Factures de ventes (journal VT) | DOC-V12 | ↗ Autre logiciel de l'ERP | `/comptabilite/ecritures/?journal=VT` |
| Traitement › Mise à jour de la comptabilité | Factures d'achats (journal AC) | DOC-V12 | ↗ Autre logiciel de l'ERP | `/comptabilite/ecritures/?journal=AC` |
| Traitement › Mise à jour de la comptabilité | Règlements achats/ ventes | DOC-V12 | ↗ Autre logiciel de l'ERP | `/comptabilite/journal/` |
| Traitement › Mise à jour de la comptabilité | Variation de stock (inventaire permanent) | AJOUT-ERP | ✅ Réalisé | `/commercial/stock/?vue=variation` |
| Traitement › Mise à jour de la comptabilité | Engagements achats/ ventes | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | Archivage | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | Clôture période | DOC-V12 | ⬜ Grisé (non développé) |  |
| Traitement | Sauvegarde fiscale des données | DOC-V12 | ⬜ Grisé (non développé) |  |
| **Etat** | | | | |
| Etat | Etats personnalisés | DOC-V12 | ⬜ Grisé (non développé) |  |
| Etat | **Analyse clients** | DOC-V12 | ▸ Sous-menu |  |
| Etat › Analyse clients | Activité clients | DOC-V12 | ✅ Réalisé | `/commercial/etats/activite_clients/` |
| Etat › Analyse clients | Rentabilité clients | DOC-V12 | ✅ Réalisé | `/commercial/etats/rentabilite_clients/` |
| Etat › Analyse clients | Risque clients | DOC-V12 | ✅ Réalisé | `/commercial/etats/risque_clients/` |
| Etat | Cadencier clients | DOC-V12 | ⬜ Grisé (non développé) |  |
| Etat | **Statistiques clients** | DOC-V12 | ▸ Sous-menu |  |
| Etat › Statistiques clients | Statistiques par familles d'articles | DOC-V12 | ✅ Réalisé | `/commercial/etats/ventes_familles/` |
| Etat › Statistiques clients | Statistiques par articles | DOC-V12 | ✅ Réalisé | `/commercial/etats/ventes_articles/` |
| Etat › Statistiques clients | Palmarès des clients | DOC-V12 | ✅ Réalisé | `/commercial/etats/palmares_clients/` |
| Etat | Mouvements clients | DOC-V12 | ↗ Autre logiciel de l'ERP | `/comptabilite/grand-livre/?compte_debut=411&compte_fin=411` |
| Etat | **Analyse fournisseurs** | DOC-V12 | ▸ Sous-menu |  |
| Etat › Analyse fournisseurs | Activité fournisseurs | DOC-V12 | ✅ Réalisé | `/commercial/etats/activite_fournisseurs/` |
| Etat › Analyse fournisseurs | Chiffre d'affaires fournisseurs | DOC-V12 | ✅ Réalisé | `/commercial/etats/ca_fournisseurs/` |
| Etat | Cadencier fournisseurs | DOC-V12 | ⬜ Grisé (non développé) |  |
| Etat | **Statistiques fournisseurs** | DOC-V12 | ▸ Sous-menu |  |
| Etat › Statistiques fournisseurs | Statistiques par familles d'articles | DOC-V12 | ✅ Réalisé | `/commercial/etats/achats_familles/` |
| Etat › Statistiques fournisseurs | Statistiques par articles | DOC-V12 | ✅ Réalisé | `/commercial/etats/achats_articles/` |
| Etat | Mouvements fournisseurs | DOC-V12 | ↗ Autre logiciel de l'ERP | `/comptabilite/grand-livre/?compte_debut=401&compte_fin=401` |
| Etat | **Statistiques articles** | DOC-V12 | ▸ Sous-menu |  |
| Etat › Statistiques articles | Statistiques articles | DOC-V12 | ✅ Réalisé | `/commercial/etats/articles/` |
| Etat › Statistiques articles | Statistiques familles | DOC-V12 | ✅ Réalisé | `/commercial/etats/familles/` |
| Etat › Statistiques articles | Palmarès des ventes | DOC-V12 | ✅ Réalisé | `/commercial/etats/palmares_ventes/` |
| Etat | Mouvements de stock | DOC-V12 | ✅ Réalisé | `/commercial/stock/mouvements/?vue=etat` |
| Etat | **Inventaire** | DOC-V12 | ▸ Sous-menu |  |
| Etat › Inventaire | Etat préparatoire | DOC-V12 | ✅ Réalisé | `/commercial/stock/etat-inventaire/?vue=preparatoire` |
| Etat › Inventaire | Livre d'inventaire | DOC-V12 | ✅ Réalisé | `/commercial/stock/etat-inventaire/?vue=livre` |
| Etat | Cadencier de livraison | DOC-V12 | ⬜ Grisé (non développé) |  |
| Etat | Statistiques collaborateurs | DOC-V12 | ⬜ Grisé (non développé) |  |
| Etat | Statistiques ressources | DOC-V12 | ⬜ Grisé (non développé) |  |
| Etat | Commissions représentants | DOC-V12 | ⬜ Grisé (non développé) |  |
| Etat | Tableaux de bord | DOC-V12 | ↗ Autre logiciel de l'ERP | `/reporting/` |
| Etat | Journaux comptables | DOC-V12 | ↗ Autre logiciel de l'ERP | `/comptabilite/journal/` |
| Etat | Etats libres | DOC-V12 | ⬜ Grisé (non développé) |  |
| Etat | Étiquettes de colisage | DOC-V12 | ⬜ Grisé (non développé) |  |
| Etat | **Relevés de factures** | DOC-V12 | ▸ Sous-menu |  |
| Etat › Relevés de factures | Clients | DOC-V12 | ✅ Réalisé | `/commercial/etats/releve_factures_clients/` |
| Etat › Relevés de factures | Fournisseurs | DOC-V12 | ✅ Réalisé | `/commercial/etats/releve_factures_fournisseurs/` |
| Etat | **Listes des documents** | DOC-V12 | ▸ Sous-menu |  |
| Etat › Listes des documents | Documents de vente | DOC-V12 | ✅ Réalisé | `/commercial/etats/liste_documents_ventes/` |
| Etat › Listes des documents | Documents d'achat | DOC-V12 | ✅ Réalisé | `/commercial/etats/liste_documents_achats/` |
| Etat | **Relevés d'échéances** | DOC-V12 | ▸ Sous-menu |  |
| Etat › Relevés d'échéances | Clients | DOC-V12 | ✅ Réalisé | `/commercial/etats/echeances_clients/` |
| Etat › Relevés d'échéances | Fournisseurs | DOC-V12 | ✅ Réalisé | `/commercial/etats/echeances_fournisseurs/` |
| Etat | **Étiquettes et mailing** | DOC-V12 | ▸ Sous-menu |  |
| Etat › Étiquettes et mailing | Clients | DOC-V12 | ⬜ Grisé (non développé) |  |
| Etat › Étiquettes et mailing | Fournisseurs | DOC-V12 | ⬜ Grisé (non développé) |  |
| Etat › Étiquettes et mailing | Étiquettes articles | DOC-V12 | ⬜ Grisé (non développé) |  |
| Etat | **Listes** | DOC-V12 | ▸ Sous-menu |  |
| Etat › Listes | Liste des clients | DOC-V12 | ✅ Réalisé | `/commercial/etats/liste_clients/` |
| Etat › Listes | Liste des fournisseurs | DOC-V12 | ✅ Réalisé | `/commercial/etats/liste_fournisseurs/` |
| Etat › Listes | Liste des articles | DOC-V12 | ✅ Réalisé | `/commercial/etats/liste_articles/` |
| **Fenêtre** | | | | |
| Fenêtre | Réorganiser | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fenêtre | Actualiser | DOC-V12 | ✅ Commande d'interface | `action « actualiser »` |
| Fenêtre | Personnaliser | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fenêtre | Personnaliser les écrans | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fenêtre | Personnaliser la liste | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fenêtre | Ajustement automatique des colonnes | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fenêtre | Préférences | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fenêtre | Barre verticale | DOC-V12 | ✅ Commande d'interface | `action « barre_verticale »` |
| Fenêtre | Mode assistant | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fenêtre | Mode personnalisé | DOC-V12 | ⬜ Grisé (non développé) |  |
| Fenêtre | Page d'accueil | AJOUT-ERP | ✅ Réalisé | `/commercial/` |
| Fenêtre | Portail ERP OHADA | AJOUT-ERP | ↗ Autre logiciel de l'ERP | `/` |
| Fenêtre | Comptabilité OHADA | AJOUT-ERP | ↗ Autre logiciel de l'ERP | `/comptabilite/` |
| Fenêtre | Reporting | AJOUT-ERP | ↗ Autre logiciel de l'ERP | `/reporting/` |
| **?** | | | | |
| ? | À propos de l'ERP OHADA | ERG-CLASSIQUE | ✅ Réalisé | `/commercial/a-propos/` |
