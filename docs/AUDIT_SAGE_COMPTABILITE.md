# Matrice de traçabilité — Comptabilité OHADA

Générée par `python manage.py audit_navigation` à partir de `apps/core/navigation.py`.
Méthode : skill `sage-100-gescom-v12-ui` (référence 10, phase D) — élément Sage → écran ERP → état → preuve.

## Synthèse

| État | Commandes |
|---|---|
| ✅ Réalisé | 52 |
| ✅ Commande d'interface | 14 |
| ↗ Autre logiciel de l'ERP | 6 |
| ⬜ Grisé (non développé) | 53 |
| **Total des commandes** | **125** |

| Niveau de preuve | Commandes | Signification |
|---|---|---|
| AJOUT-ERP | 6 | Ajout propre à l'ERP OHADA (absent de Sage) |
| ERG-CLASSIQUE | 99 | Ergonomie Sage classique, à vérifier sur une installation V12 |
| INDICATIF | 20 | Proposition fonctionnelle, non vérifiée sur une capture V12 |

## Détail par menu

| Chemin | Élément | Preuve | État dans l'ERP | Écran / action |
|---|---|---|---|---|
| **Fichier** | | | | |
| Fichier | Nouveau | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Fichier | Ouvrir | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Fichier | Fermer | ERG-CLASSIQUE | ✅ Commande d'interface | `action « fermer »` |
| Fichier | **À propos de votre société** | ERG-CLASSIQUE | ▸ Sous-menu |  |
| Fichier › À propos de votre société | Identification | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/societe/` |
| Fichier › À propos de votre société | Exercices comptables | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/exercices/` |
| Fichier › À propos de votre société | Comptes | INDICATIF | ⬜ Grisé (non développé) |  |
| Fichier › À propos de votre société | Tiers | INDICATIF | ⬜ Grisé (non développé) |  |
| Fichier › À propos de votre société | Taxes | INDICATIF | ✅ Réalisé | `/comptabilite/structure/taxes/?vue=parametres` |
| Fichier › À propos de votre société | Analytique | INDICATIF | ⬜ Grisé (non développé) |  |
| Fichier › À propos de votre société | Devises | INDICATIF | ⬜ Grisé (non développé) |  |
| Fichier › À propos de votre société | Banques | INDICATIF | ✅ Réalisé | `/comptabilite/structure/banques/?vue=parametres` |
| Fichier › À propos de votre société | Éditions | INDICATIF | ⬜ Grisé (non développé) |  |
| Fichier | Lire les informations | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Fichier | Autorisations d'accès | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/autorisations/` |
| Fichier | Importer | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Fichier | Exporter | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Fichier | Format import/export paramétrable | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Fichier | Mise en page | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Fichier | Imprimer… | ERG-CLASSIQUE | ✅ Commande d'interface | `action « imprimer »` |
| Fichier | Impression différée | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Fichier | **Outils** | ERG-CLASSIQUE | ▸ Sous-menu |  |
| Fichier › Outils | Maintenance | INDICATIF | ⬜ Grisé (non développé) |  |
| Fichier › Outils | Sauvegarde | INDICATIF | ⬜ Grisé (non développé) |  |
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
| Structure | Plan comptable | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/plan/` |
| Structure | **Plan tiers** | ERG-CLASSIQUE | ▸ Sous-menu |  |
| Structure › Plan tiers | Clients | ERG-CLASSIQUE | ↗ Autre logiciel de l'ERP | `/commercial/clients/` |
| Structure › Plan tiers | Fournisseurs | ERG-CLASSIQUE | ↗ Autre logiciel de l'ERP | `/commercial/fournisseurs/` |
| Structure | Plan analytique | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/structure/sections/` |
| Structure | Plan reporting | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Structure | Taux de taxes | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/structure/taxes/` |
| Structure | Codes journaux | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/journaux/` |
| Structure | Codes journaux analytiques | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Structure | Postes budgétaires | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Structure | Devises | INDICATIF | ⬜ Grisé (non développé) |  |
| Structure | Banques | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/structure/banques/` |
| Structure | Modèles de saisie | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Structure | Modèles de grille | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Structure | Modèles de règlement | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| **Traitement** | | | | |
| Traitement | **Saisie des journaux** | ERG-CLASSIQUE | ▸ Sous-menu |  |
| Traitement › Saisie des journaux | Tous les journaux | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/ecritures/` |
| Traitement › Saisie des journaux | AC - Journal des achats | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/ecritures/?journal=AC` |
| Traitement › Saisie des journaux | AN - À-nouveaux | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/ecritures/?journal=AN` |
| Traitement › Saisie des journaux | BQ - Journal de banque | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/ecritures/?journal=BQ` |
| Traitement › Saisie des journaux | CA - Journal de caisse | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/ecritures/?journal=CA` |
| Traitement › Saisie des journaux | MM - Journal Mobile Money | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/ecritures/?journal=MM` |
| Traitement › Saisie des journaux | OD - Opérations diverses | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/ecritures/?journal=OD` |
| Traitement › Saisie des journaux | VT - Journal des ventes | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/ecritures/?journal=VT` |
| Traitement | Saisie par pièce | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/ecritures/saisie/` |
| Traitement | Saisie des opérations bancaires | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Traitement | Saisie par lot | INDICATIF | ⬜ Grisé (non développé) |  |
| Traitement | Saisie des écritures analytiques | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/analytique/ventilation/` |
| Traitement | Écritures au brouillard | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/ecritures/?statut=BROUILLARD` |
| Traitement | Interrogation et lettrage | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/lettrage/` |
| Traitement | Lettrage automatique | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/lettrage/automatique/` |
| Traitement | Recherche d'écritures | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/ecritures/?vue=recherche` |
| Traitement | Rapprochement bancaire manuel | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/rapprochement/` |
| Traitement | Rapprochement bancaire automatique | INDICATIF | ⬜ Grisé (non développé) |  |
| Traitement | Gestion des extraits | INDICATIF | ⬜ Grisé (non développé) |  |
| Traitement | Règlement tiers | ERG-CLASSIQUE | ↗ Autre logiciel de l'ERP | `/commercial/reglements/nouveau/` |
| Traitement | Rappel / relance clients | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/balance-agee/?type=CLIENT&vue=relance` |
| Traitement | Déclaration de taxes | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/tva/` |
| Traitement | Révision par cycle | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Traitement | Abonnements | INDICATIF | ⬜ Grisé (non développé) |  |
| Traitement | **Fin d'exercice** | ERG-CLASSIQUE | ▸ Sous-menu |  |
| Traitement › Fin d'exercice | Nouvel exercice | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/exercices/nouveau/` |
| Traitement › Fin d'exercice | Clôture de l'exercice et reports à nouveau | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/cloture/exercice/` |
| Traitement › Fin d'exercice | Clôture des journaux | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/cloture/journaux/` |
| Traitement › Fin d'exercice | Archivage | INDICATIF | ⬜ Grisé (non développé) |  |
| **Etat** | | | | |
| Etat | Brouillard | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/journal/?statut=BROUILLARD` |
| Etat | **Journaux** | ERG-CLASSIQUE | ▸ Sous-menu |  |
| Etat › Journaux | Journal général | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/journal/` |
| Etat › Journaux | **Journaux auxiliaires** | ERG-CLASSIQUE | ▸ Sous-menu |  |
| Etat › Journaux › Journaux auxiliaires | AC - Journal des achats | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/journal/?journal=AC` |
| Etat › Journaux › Journaux auxiliaires | AN - À-nouveaux | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/journal/?journal=AN` |
| Etat › Journaux › Journaux auxiliaires | BQ - Journal de banque | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/journal/?journal=BQ` |
| Etat › Journaux › Journaux auxiliaires | CA - Journal de caisse | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/journal/?journal=CA` |
| Etat › Journaux › Journaux auxiliaires | MM - Journal Mobile Money | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/journal/?journal=MM` |
| Etat › Journaux › Journaux auxiliaires | OD - Opérations diverses | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/journal/?journal=OD` |
| Etat › Journaux › Journaux auxiliaires | VT - Journal des ventes | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/journal/?journal=VT` |
| Etat | Grand-livre des comptes | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/grand-livre/` |
| Etat | Balance des comptes | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/balance/` |
| Etat | **Etats tiers** | ERG-CLASSIQUE | ▸ Sous-menu |  |
| Etat › Etats tiers | Grand-livre des tiers | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/grand-livre/?compte_debut=4&compte_fin=4` |
| Etat › Etats tiers | Balance des tiers | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/balance/?compte_debut=4&compte_fin=4` |
| Etat › Etats tiers | Echéancier | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/balance-agee/?type=CLIENT&vue=echeancier` |
| Etat › Etats tiers | Balance âgée | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/balance-agee/?type=CLIENT` |
| Etat › Etats tiers | Justificatif de solde à date | INDICATIF | ⬜ Grisé (non développé) |  |
| Etat › Etats tiers | Statistiques tiers | INDICATIF | ⬜ Grisé (non développé) |  |
| Etat › Etats tiers | Historique des rappels | INDICATIF | ⬜ Grisé (non développé) |  |
| Etat | **Etats analytiques** | ERG-CLASSIQUE | ▸ Sous-menu |  |
| Etat › Etats analytiques | Journal analytique | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Etat › Etats analytiques | Grand-livre analytique | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Etat › Etats analytiques | Balance analytique | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/analytique/balance/` |
| Etat | Etats budgétaires | INDICATIF | ⬜ Grisé (non développé) |  |
| Etat | **Bilan / Compte de résultat** | ERG-CLASSIQUE | ▸ Sous-menu |  |
| Etat › Bilan / Compte de résultat | Bilan | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/bilan/` |
| Etat › Bilan / Compte de résultat | Compte de résultat | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/compte-de-resultat/` |
| Etat › Bilan / Compte de résultat | Soldes intermédiaires de gestion | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/compte-de-resultat/?vue=sig` |
| Etat | **Déclarations** | AJOUT-ERP | ▸ Sous-menu |  |
| Etat › Déclarations | Déclaration de TVA | AJOUT-ERP | ✅ Réalisé | `/comptabilite/tva/?vue=etat` |
| Etat › Déclarations | Déclaration statistique et fiscale (DSF) | AJOUT-ERP | ⬜ Grisé (non développé) |  |
| Etat | Analyse et contrôles | INDICATIF | ⬜ Grisé (non développé) |  |
| **Fenêtre** | | | | |
| Fenêtre | Réorganiser | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Fenêtre | Actualiser | ERG-CLASSIQUE | ✅ Commande d'interface | `action « actualiser »` |
| Fenêtre | Personnaliser | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Fenêtre | Personnaliser les écrans | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Fenêtre | Personnaliser la liste | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Fenêtre | Ajustement automatique des colonnes | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Fenêtre | Préférences | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Fenêtre | Barre verticale | ERG-CLASSIQUE | ✅ Commande d'interface | `action « barre_verticale »` |
| Fenêtre | Mode assistant | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Fenêtre | Mode personnalisé | ERG-CLASSIQUE | ⬜ Grisé (non développé) |  |
| Fenêtre | Page d'accueil | AJOUT-ERP | ✅ Réalisé | `/comptabilite/` |
| Fenêtre | Portail ERP OHADA | AJOUT-ERP | ↗ Autre logiciel de l'ERP | `/` |
| Fenêtre | Gestion commerciale | AJOUT-ERP | ↗ Autre logiciel de l'ERP | `/commercial/` |
| Fenêtre | Reporting | AJOUT-ERP | ↗ Autre logiciel de l'ERP | `/reporting/` |
| **?** | | | | |
| ? | À propos de l'ERP OHADA | ERG-CLASSIQUE | ✅ Réalisé | `/comptabilite/a-propos/` |
