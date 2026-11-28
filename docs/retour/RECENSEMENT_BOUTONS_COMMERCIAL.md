# Recensement des boutons — ERP Gestion commerciale

Généré automatiquement depuis la version de code utilisée pour exécuter la commande.
Attention : INVENTAIRE STATIQUE. Les droits réels, les fenêtres affichées et les fonctions
Sage 100 V12 restent à vérifier dans des sessions de test et avec des preuves.

## Résultat reproductible

| Mesure | Nombre |
|---|---:|
| Commandes terminales des menus | 227 |
| Entrées ouvrant un sous-menu (non terminales) | 25 |
| Occurrences HTML dans les écrans Commercial + communs sélectionnés | 175 |
| HTML avec action déclarée (y compris conditions) | 159 |
| HTML inactifs / désactivés dans le code | 16 |
| Fichiers HTML analysés | 32 |
| Types de documents ventes / achats / stocks | 9 / 9 / 3 |

## Répartition détaillée par menu principal

| Menu | Commandes terminales | Avec cible / action | Grisées sans cible |
|---|---:|---:|---:|
| Fichier | 42 | 12 | 30 |
| Édition | 17 | 9 | 8 |
| Structure | 29 | 9 | 20 |
| Traitement | 75 | 43 | 32 |
| Etat | 43 | 31 | 12 |
| Fenêtre | 20 | 13 | 7 |
| ? | 1 | 1 | 0 |

## Répartition des contrôles HTML par fenêtre / template

| Template | Occurrences source |
|---|---:|
| templates/base.html | 27 |
| templates/commercial/agence_list.html | 3 |
| templates/commercial/article_detail.html | 3 |
| templates/commercial/article_list.html | 3 |
| templates/commercial/besoins.html | 5 |
| templates/commercial/categorie_list.html | 1 |
| templates/commercial/depot_list.html | 3 |
| templates/commercial/document_detail.html | 24 |
| templates/commercial/document_form.html | 11 |
| templates/commercial/document_list.html | 19 |
| templates/commercial/etat_inventaire.html | 3 |
| templates/commercial/famille_list.html | 2 |
| templates/commercial/fiche_rapprochement.html | 3 |
| templates/commercial/inventaire_detail.html | 5 |
| templates/commercial/inventaire_list.html | 2 |
| templates/commercial/mouvement_list.html | 3 |
| templates/commercial/operation_caisse_list.html | 4 |
| templates/commercial/pointage.html | 4 |
| templates/commercial/pointage_detail.html | 2 |
| templates/commercial/pointage_list.html | 4 |
| templates/commercial/recherche.html | 7 |
| templates/commercial/reglement_detail.html | 6 |
| templates/commercial/reglement_form.html | 13 |
| templates/commercial/reglement_list.html | 2 |
| templates/commercial/stock.html | 4 |
| templates/commercial/tiers_detail.html | 8 |
| templates/commercial/tiers_list.html | 2 |
| templates/pagination.html | 2 |

## État statique des commandes et contrôles

| État | Occurrences |
|---|---:|
| action_interface_declaree | 15 |
| autre_logiciel_declare | 20 |
| conditionnel_a_verifier | 98 |
| desactive_html | 3 |
| grise_sans_cible | 109 |
| inactif_html | 13 |
| interactif_declare_non_teste | 61 |
| lien_declare_non_teste | 83 |
| sous_menu | 25 |

## Types de documents couverts par les fenêtres génériques

| Famille | Code interne | Document |
|---|---|---|
| vente | DEVIS | Devis |
| vente | COMMANDE | Bon de commande |
| vente | PREPARATION | Préparation de livraison |
| vente | LIVRAISON | Bon de livraison |
| vente | RETOUR | Bon de retour |
| vente | AVOIR_FINANCIER | Bon d'avoir financier |
| vente | FACTURE | Facture |
| vente | FACTURE_RETOUR | Facture de retour |
| vente | AVOIR | Facture d'avoir |
| achat | ACHAT_DEMANDE | Demande d'achat |
| achat | ACHAT_PREPARATION | Préparation de commande |
| achat | ACHAT_COMMANDE | Bon de commande fournisseur |
| achat | ACHAT_RECEPTION | Bon de livraison fournisseur |
| achat | ACHAT_RETOUR | Bon de retour fournisseur |
| achat | ACHAT_AVOIR_FINANCIER | Bon d'avoir financier fournisseur |
| achat | ACHAT_FACTURE | Facture fournisseur |
| achat | ACHAT_FACTURE_RETOUR | Facture de retour fournisseur |
| achat | ACHAT_AVOIR | Facture d'avoir fournisseur |
| stock | STOCK_ENTREE | Mouvement d'entrée |
| stock | STOCK_SORTIE | Mouvement de sortie |
| stock | STOCK_VIREMENT | Mouvement de transfert |

## Méthode et exclusions indispensables

- Une entrée de sous-menu ne s'additionne pas aux commandes terminales pour mesurer des actions.
- Une occurrence HTML dans un template commun n'est comptée qu'une fois, même si son
  affichage est répliqué sur 21 types de pièces ou des milliers de documents.
- Les commandes des menus rendues via core/_menu.html, core/_arbre.html et la barre verticale
  sont comptées UNE fois depuis navigation.py, pour éviter les doublons visuels.
- Inclut les templates/commercial/**/*.html et base.html, pagination.html, core/_auteurs.html.
- Les formulaires HTML produits indirectement par Django ({{ form }}, champs de formsets,
  boutons JavaScript créés à l'exécution) ne sont PAS tous quantifiés statiquement.
- Les états disabled, HTML inactif ou URL/action déclarée ne garantissent pas le comportement
  à l'exécution ni les droits. Les éléments sous {% if %}/{% for %} restent conditionnels.
- Les 21 types de pièces ont des boutons variables selon brouillon/validé/annulé,
  droits, encours, règlements, types de transformations, dépôt et lignes.
- Pour obtenir un **nombre de boutons affichés**, il faudra rendre chaque type/statut et
  profil utilisateur, parcourir les boîtes de dialogue et tester les clics et routes.
- Référence Sage : support officiel Sage 100 V12, découpage V12.10 ; un intitulé identique
  ne prouve pas qu'un dialogue ou un traitement est identique. Marquer « A_VERIFIER ».

## Procédure de vérification fonctionnelle conjointe Claude / GPT

Pour chaque ligne CSV, renseigner après essai le dialogue ouvert, la vue/route et sa
méthode HTTP, droits, état initial et final, test des statuts, effets sur stock/écritures,
preuve Sage (page + capture + édition V12), écarts et responsable de la correction.
Aucune écriture SQL de production ni aucun taux fiscal inventé.
