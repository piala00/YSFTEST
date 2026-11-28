---
name: sage-x3-v12-expert
description: "Expert Sage X3 V12 : dictionnaires écrans, fenêtres, champs, actions, permissions, tables SQL, Sage X3 4GL, REST/SOAP/GraphQL et intégration ERP."
---

# Sage X3 V12 — expertise fonctionnelle et technique

## Ne pas confondre Sage X3 et Sage 100
Sage X3 est un ERP distinct, avec dossiers, sites, sociétés, législations, superviseur, transactions de saisie, menus métiers, dictionnaires, 4GL, API. Sources officielles : https://online-help.sagex3.com/erp/12/fr-fr/Content/Tech%20Help/TH_LP.htm, https://developer.sage.com/x3.

## Cartographie des domaines
Ventes : prospects/clients, tarifs, devis, commandes, expéditions, factures, retours.
Achats : fournisseurs, demandes, commandes, réceptions, factures et retours.
Stocks : articles/sites/emplacements, lots/séries, mouvements, inventaires, valorisation.
Finance : comptabilité, tiers, analytique, immobilisations et contrôle selon modules.
Production : nomenclatures, gammes, ordres de fabrication, besoins, planification.
Administration/Setup : sociétés, sites, unités, codes activité, profils, workflow, transactions.
**Ces familles ne sont pas des chemins de menus validés pour un dossier précis.**

## Moyens officiels de collecter les écrans réels
- Dictionnaire des écrans : `GESAMK` (https://online-help.sagex3.com/erp/12/fr-fr/Content/FCT/GESAMK.htm). Un écran comporte des blocs et des champs ; onglets `Général` et `Champs`. Code écran `CODMSK`, abréviation `ABRMSK`, champ `CODZON`, bloc `NUMBLOC`, position `NOZONE`, conditions `CODACT`, obligations `OBLIG`, actions par champ.
- Dictionnaire des fenêtres : `GESAWI` (https://online-help.sagex3.com/erp/12/fr-fr/Content/FCT/GESAWI.htm). Fenêtre composée d'écrans, menus, boutons, navigateur ; onglets `Écrans`, `Boutons/menus`, `Boutons prédéfinis`, `Browser`.
- Tables superviseur à découvrir et valider localement : `AMSK`, `AMSKZON`, `AWINDOW`, `AWINBOUT`, `AWINBRO`, `AWINPAR`, `ATABLE`, `ATABZON`, `ACTION`, `AOBJET`, `ACTIV`. Source prérequis : https://online-help.sagex3.com/erp/12/fr-fr/Content/FCT/PRQ_AFC_GESAWI.htm.
- Code activité / transaction de saisie / droits / langue peuvent masquer ou changer des éléments : l'écran dictionnaire n'est pas toujours l'écran réellement rendu.

## Architecture technique et APIs
- Platform/dev/Workbench : https://developer.sage.com/x3/docs/latest/guides/x3-development-platform/platform-reference
- API REST et SOAP selon plateforme : https://developer.sage.com/x3/docs/latest/guides/x3-development-platform/platform-reference/api-guide
- Classes/représentations, modèles 4GL, fonctions et intégrations : https://developer.sage.com/x3/docs/latest/guides/x3-development-platform/templates
- API GraphQL/Builder selon environnement et configuration X3 (ne pas la supposer installée).
- SQL X3 : lecture seule pour analytics ; pour mise à jour passer par API/flux métier public adéquat, import conforme ou services X3 ; jamais SQL brut sur tables transactionnelles.

## Extraction exhaustive d'une fonction X3
1. Capturer le code fonction et le code fenêtre, l'objet et les transactions de saisie.
2. Extraire liste des écrans (code et ordre), chacun des blocs, chaque champ, attributs, contrôles, référence de table, événements/actions et conditions de code activité.
3. Capturer boutons et menus (action associée, paramètres), autorisations de rôles, traduction et état visible/désactivé.
4. Documenter le traitement métier réellement produit sur dossier test avant/après, états, SQL et logs.
5. Consolider la fiche et lier référence officielle + base/dossier/build.

## Exigence
Ne jamais extrapoler une action X3 V12 à partir de Sage 100 V12. Vérifier la législation, le site, les modules activés et le dossier de test.

