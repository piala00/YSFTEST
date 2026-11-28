---
name: sage100-fenetres-selection-v12
description: "Documenter et concevoir les fenêtres de sélection de Sage 100 Gestion commerciale et Comptabilité pour un ERP : appels de tiers, articles et comptes, filtres de listes, recherches multicritères, sélections avant états ou traitements et choix de modèles. Utiliser pour inventorier les dialogues, leurs critères, boutons, retours et règles en distinguant les preuves de version et les compléments à observer."
---

# Fenêtres de sélection Sage 100

Version 0.1, recherche du 21 octobre 2026. Catalogue étendu et traçable ; exhaustivité sur V12 non certifiée. Ne pas assimiler « toutes les fenêtres à couvrir » à « toutes les fenêtres V12 déjà observées ».

## Utilisation

1. Lire [PERIMETRE_ET_COUVERTURE.md](references/PERIMETRE_ET_COUVERTURE.md), puis [FAMILLES_ET_PARCOURS.md](references/FAMILLES_ET_PARCOURS.md).
2. Rechercher le contexte dans [FENETRES_SELECTION.csv](references/FENETRES_SELECTION.csv). Une sélection simplifiée, un format avancé et la liste de résultats sont trois contextes distincts.
3. Charger [CHAMPS_ET_CRITERES.csv](references/CHAMPS_ET_CRITERES.csv) et [BOUTONS_ACTIONS.csv](references/BOUTONS_ACTIONS.csv) par identifiant stable `fenetre_id`. Un champ d’appel dans le parent n’est pas une colonne du sélecteur.
4. Lire [COMPORTEMENTS.csv](references/COMPORTEMENTS.csv) et [REGLES_DE_SELECTION.md](references/REGLES_DE_SELECTION.md) avant de coder le moteur ou les retours.
5. Pour la maquette ERP, utiliser [CONTRAT_ERP.md](references/CONTRAT_ERP.md) comme proposition de conception. Ne pas présenter ses choix comme des fonctions Sage attestées.
6. Compléter [COUVERTURE_A_COMPLETER.csv](references/COUVERTURE_A_COMPLETER.csv) avec le protocole dans [RECETTE_ET_RELEVE.md](references/RECETTE_ET_RELEVE.md) et [CAS_DE_RECETTE.csv](references/CAS_DE_RECETTE.csv). Aucun de ces cas n’a été exécuté sur Sage pendant la recherche.
7. Consulter [SOURCES.csv](references/SOURCES.csv), [INCONNUES.csv](references/INCONNUES.csv) et [EMPREINTES.csv](references/EMPREINTES.csv). Utiliser [REPERES_TYPOGRAPHIQUES.csv](references/REPERES_TYPOGRAPHIQUES.csv) uniquement pour orienter une lecture manuelle, jamais comme un schéma d’écran validé.

## Appliquer les limites

- Conserver toutes les colonnes, UTF-8, séparateur `;` et cellules citées. Les identifiants ne dépendent pas du numéro de ligne.
- Garder les défauts et conditions non établis ouverts. Un ordre UI vide ne constitue pas un rang connu.
- Séparer les sources 8.50, celles V10.00 et sup. et les aides sans build. L’origine officielle ne certifie pas une disposition V12.
- Ne pas généraliser F4, double-clic, sélection multiple, extension de fichier ou existence de Plus à toutes les fenêtres.
- Ne pas utiliser le schéma SQL ou les colonnes d’une fiche pour inventer celles d’une liste d’appel.
- Distinguer Enregistrer une ligne de critère et Sauvegarder le format ; distinguer format de sélection et modèle de mise en page.
- Faire respecter les droits et le contexte métier aux résultats comme aux actions ; ne pas autoriser une création par simple retour de sélection.
- Distinguer sélection, validation d’une fiche, lancement d’un traitement et remplacement en masse. Une recherche ne doit pas être utilisée comme autorisation de modification.
- Limiter ce corpus à Gescom/Comptabilité et leurs fonctions communes. Les écrans BI Reporting, X3, Paie et autres produits demandent un relevé propre.
