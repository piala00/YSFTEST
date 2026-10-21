# Étape 06 — Sage 100 SQL Server : structures et règles de lecture
**Date :** 21 octobre 2026  
**Statut :** livrables documentaires produits ; en attente de validation utilisateur.  
**Périmètre :** Sage 100 Gestion Commerciale (.GCM) + Sage 100 Comptabilité (.MAE), V12.20 comme référence certifiée documentaire, V5–V12 comme périmètre cible **non vérifié physiquement**.

## 1. Résultat précis
Ce dossier contient :
- **40 entrées table/produit** : un catalogue raisonné des principaux objets Sage ; certaines tables communes sont recensées séparément selon leur périmètre documentaire. **Ce n'est pas la liste exhaustive des tables**.
- **100 couples table/champ repères**, avec description, version et localisation documentaire. **Ce n'est pas l'ensemble des colonnes physiques**.
- **30 relations explicites** dans les annexes Sage. Une relation documentée n'est **pas automatiquement une contrainte `FOREIGN KEY`** en SQL Server.
- **35 codes de type de document** issus de `F_DOCENTETE.DO_Type` et leur domaine.
- **19 valeurs d'énumérations** sur six champs de comportement, avec réserves spécifiques.
- **10 limites/tests ouverts** au stade documentaire.
- Scripts et tests techniques sans requête d'écriture ; aucun accès aux serveurs Sage n'a été effectué.

## 2. Sources et classement
**S06-01 — source principale examinée :** Sage 100 V12.20, *Structure des bases Sage 100*, PDF 447 pages, mise à jour juillet 2026. Texte et pages sélectionnées étudiés : p. 103–107 (écritures), p. 215–219 (tarifs), p. 241–261 (documents), p. 277+ (règlements), p. 409–418 (jointures), p. 439–442 (inaltérabilité en contexte législatif français).  
https://fr-kb.sage.com/portal/app/portlets/results/viewdocument.jsp?solutionid=230113095648937

**S06-02 — fiche identifiée, PDF non analysé :** *Structure des fichiers V12.25* ; ne pas extrapoler des différences V12.25.  
https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=230113095807277

**S06-03 — index historique :** formats d'import Sage (#VER), distincts des schémas physiques.  
https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=211010160114075

**S06-04 — communauté Sage :** recommandation de ne pas transformer les documents directement par SQL.  
https://communityhub.sage.com/fr/sage-100/f/partenaire-sage-100-la-communaute-des-developpeurs/217377/pb-transformation-pl-en-bl

> La documentation Sage est protégée : le pack propose une synthèse originale, des références factuelles et des pointeurs de pages, sans redistribuer le manuel.

## 3. Modèle relationnel minimal
- `F_DOCENTETE` (document) → `F_DOCLIGNE` (lignes) : (`DO_Type`, `DO_Piece`) ; l'attribut `DO_Domaine` reste important pour la cohérence métier.
- `F_DOCENTETE.DO_Tiers` → `F_COMPTET.CT_Num` pour les documents dont le domaine est vente/achat. Ne pas appliquer ce lien aveuglément aux documents de stock.
- `F_DOCLIGNE.AR_Ref` → `F_ARTICLE.AR_Ref` ; `F_DOCLIGNE.DE_No` → `F_DEPOT.DE_No`.
- `F_ARTSTOCK.AR_Ref` → `F_ARTICLE.AR_Ref` et `F_ARTSTOCK.DE_No` → `F_DEPOT.DE_No`.
- `F_CREGLEMENT` → `F_REGLECH` → `F_DOCREGL` : règlement, imputation, échéance. Ne **pas** assimiler le total encaissé au total imputé.
- `F_ECRITUREC.EC_No` → `F_ECDOCDN.EC_No` ; `F_ECDOCDN` référence des documents par type et pièce, à vérifier sur chaque base.

## 4. Points métier déterminants
**Ventes** : `DO_Type` distingue devis, commande, livraison, facture ; `DO_Provenance` permet de distinguer facture normale, facture de retour et facture d'avoir. Un chiffre d'affaires fiable doit réconcilier les factures et les retours/avoirs, sans additionner commandes et livraisons à nouveau. L'état validé/comptabilisé est également à prendre en compte. 

**Stocks** : le champ `DL_MvtStock` distingue absence de mouvement, entrée/sortie **quantité** et entrée/sortie **valeur**. Compter chaque ligne comme entrée/sortie de quantité serait faux. Les lots, gammes, transferts inter-dépôts et emplacements ont des structures spécifiques ; les stocks réels/disponibles/commandés/réservés ne sont pas interchangeables.

**Comptabilité** : `EC_Sens=0` correspond au débit et `EC_Sens=1` au crédit ; pour une revue simplifiée, ventiler `EC_Montant` en conséquence, puis rapprocher des états du logiciel. Vérifier exercices, à-nouveaux, journaux, écritures clôturées, lettrages et contextes analytiques.

**Sécurité** : la documentation expose la sécurisation de certaines factures validées, règlements et écritures clôturées dans un **contexte légal français** ; ne pas transposer automatiquement les obligations juridiques au Cameroun. L'exigence d'intégrité et de non-altération reste importante pour notre ERP.

## 5. Architecture cible pour l'ERP de Claude
**Lecture Sage** : une connexion spécifique **lecture seule** par source (Gestion Commerciale ou Comptabilité, par agence et par version).  
**Zone d'atterrissage** : journal immuable de l'extraction, identifiants stables `(source_system, source_agence, base_alias, table, clé logique)` ; origine et horodatage des extractions.  
**Normalisation** : vues / tables propres à l'ERP pour documents, lignes, mouvements, règlements et écritures ; aucune écriture dans Sage.  
**Réconciliation** : regroupements de la même période/entité avec les états natifs Sage ; détection des doubles comptages et des corrections.  
**Compatibilité** : chaque extraction doit lire le manifeste de schéma du build réel avant d'utiliser des colonnes facultatives.

## 6. Méthode d'inventaire sans écrire dans Sage
1. Sur **copie de test** de chaque dossier V5 à V12, identifier la version précise et le produit (`.GCM` / `.MAE`) et créer un compte SQL en lecture seule.
2. Lancer dans SSMS `sql/01_INVENTAIRE_SYSTEME_LECTURE_SEULE.sql` ou, facultativement, `outils/exporter_metadonnees.py` avec chaîne de connexion transmise par variable d'environnement.
3. Exporter les **six jeux de métadonnées** : objets, colonnes, index, clés étrangères, contraintes, dépendances. Ne jamais inclure les définitions de procédures ni des données commerciales dans le lot documentaire.
4. Utiliser `outils/comparer_catalogues.py` pour comparer les colonnes de deux versions (sorties `colonnes.csv`) ; poursuivre l'analyse de tous les autres objets avec les exports bruts.
5. Contrôler visuellement dans Sage les conséquences métiers ; reporter précisément édition/build/module/options.
6. Réviser les Skills uniquement pour les affirmations confirmées.

## 7. État de validation
| Contrôle | État |
|---|---|
| Ouverture du manuel V12.20 | Document consulté, sections pertinentes examinées |
| Référence V12.25 | Fiche vérifiée, PDF non examiné |
| Présence réelle des colonnes en V12 de l'utilisateur | Non vérifiée |
| Présence et changements V5–V11 | Non vérifiés |
| Compilation Python scripts | Vérifiée localement (3 scripts) |
| Comparaison fictive de schémas | Réussie : 1 ajout, 1 retrait, 1 modification |
| Requêtes SQL Server sur serveur Sage | Non exécutées |
| Réconciliation avec états Sage | Non exécutée |

**Décision proposée** : valider **l'étape 06 comme étude documentaire et outillage en lecture seule**. Ne pas présenter une couverture comme physiquement exhaustive. L'étape 07 (interface Sage Comptabilité) doit attendre une validation explicite.

## 8. Vérification complémentaire du 21 octobre 2026

Les 35 types de pièces ont été rapprochés de la page imprimée 241–242 du manuel. Une variation terminologique `DO_Type=12` est décrite dans `NOTE_VARIATIONS_ET_PRUDENCE.md`. Le catalogue ne contient aucune donnée de client réel.
