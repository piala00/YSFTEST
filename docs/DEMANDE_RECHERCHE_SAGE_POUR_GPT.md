# Cahier de demande de recherche — ERP OHADA (façon Sage 100 V12)

**Destinataire : l'assistant chargé des recherches (ChatGPT ou autre).**
**Rédigé par : l'assistant qui développe l'ERP (Claude), à transmettre par le propriétaire du projet.**
**Date : 21/10/2026 — version 2.**

Ce document a trois parties :
1. **Le projet** : ce qui est construit, ce qui fonctionne, ce qui est en cours ;
2. **Les recherches demandées**, classées par priorité, chacune avec son utilité concrète dans le logiciel ;
3. **Le format de livraison**, à respecter strictement : le résultat est intégré automatiquement.

---

## Partie 1 — Le projet

### Ce que nous construisons

Un ERP pour PME d'Afrique centrale (Cameroun d'abord), conforme **OHADA / SYSCOHADA révisé**, en FCFA (XAF),
qui reproduit l'ergonomie de **Sage 100 V12 SQL Server**, logiciel que nos utilisateurs connaissent déjà.

- **Trois logiciels**, chacun avec sa barre de menus Fichier · Édition · Structure · Traitement · Etat · Fenêtre · ? :
  **Gestion commerciale**, **Comptabilité**, **Reporting**.
- **Deux interfaces** sur le même serveur : web (Django, consultable en ligne) et bureau Windows (Python CustomTkinter).
- **Bases** : PostgreSQL ou SQL Server (SQLite en test).
- Code : dépôt GitHub `piala00/YSFTEST`. Version de test en ligne sur Render, reconstruite à chaque modification.

### Ce qui fonctionne aujourd'hui

**Gestion commerciale** (menus alignés sur le « Découpage détaillé Sage 100 Gescom V11/V12 » officiel)
- 9 types de documents de vente (devis → bon de commande → préparation → bon de livraison → facture ; bon de retour,
  bon d'avoir financier, facture de retour, facture d'avoir), 9 d'achat, 3 de stock (entrée, sortie, transfert).
- Transformations avec reliquats et livraisons partielles ; stock par dépôt ; coût moyen pondéré (CMUP) ;
  inventaire ; réapprovisionnement (stock mini / maxi) ; catégories tarifaires ; contrôle d'encours client
  (aucun / avertir / bloquer) ; règlements avec imputation ; 22 états statistiques.
- Régime de TVA de la société (assujettie / non assujettie), clients exonérés, fournisseurs non assujettis.

**Comptabilité**
- Plan SYSCOHADA (environ 200 comptes chargés), journaux, saisie par pièce, brouillard puis validation.
- Écritures automatiques des factures et règlements ; lettrage manuel et automatique ; rapprochement bancaire ;
  analytique par section ; clôture des journaux ; clôture d'exercice avec reports à nouveau.
- Balance, grand-livre, journaux, balance âgée, échéancier, bilan et compte de résultat SYSCOHADA (rubriques
  officielles AD…, TA…, XA…XI), récapitulatif de TVA.

**Commun**
- Espace de travail façon Sage : fenêtres au centre (réduire / agrandir / fermer), onglets de fenêtres, barre
  verticale activable.
- **Autorisations d'accès** par profil, sur l'arbre complet des menus (boutons + / −), quatre niveaux :
  Tout autoriser, Interdire la suppression, Interdire l'écriture, Tout interdire.
- Reprise des données d'un dossier Sage 100 (requêtes SQL en lecture seule → CSV → import contrôlé).

### Ce qui est en cours ou bloqué faute d'information

| Sujet | Blocage |
|---|---|
| Menus de la **Comptabilité** | Construits sans document officiel : l'arborescence exacte de Sage 100 Comptabilité manque. |
| **Autorisations d'accès** | Libellés exacts des niveaux et droits particuliers de Sage non confirmés. |
| **Fiches et écrans** | Nos fiches article, tiers, document… n'ont pas les mêmes onglets et champs que Sage. |
| **Fiscalité camerounaise** | Seule la TVA est gérée ; précompte, AIR, timbre, mentions de facture à confirmer. |
| **Plan comptable** | Environ 200 comptes seulement : il faut le plan SYSCOHADA révisé complet. |
| **États financiers** | Bilan et compte de résultat faits ; tableau des flux de trésorerie, notes annexes, DSF manquent. |
| **Reprise Sage** | Plusieurs noms de colonnes SQL Sage sont « à confirmer ». |

---

## Partie 2 — Les recherches demandées

### Règles impératives (valables pour toutes les recherches)

1. **Ne rien inventer.** Chaque information cite sa source (URL, document, page ou article de loi). Ce qui est
   introuvable va dans `INCONNUES.csv`, jamais deviné.
2. **Libellés exacts** de Sage (casse, accents, ponctuation ; « Etat » sans accent dans la barre de menus).
   Conserver l'**ordre** d'affichage et la place des **séparateurs**.
3. Préciser la **version** (V12 de préférence ; V11 si Sage dit que c'est identique) et l'**édition** (Standard,
   Premium…) quand elle change quelque chose.
4. Niveau de preuve de chaque ligne : `DOC-OFFICIEL` (Sage, DGI, OHADA, journal officiel), `DOC-TIERS`
   (partenaire, formation, forum : préciser lequel) ou `A-CONFIRMER`.
5. Pour la fiscalité : texte en vigueur au **1er janvier 2026** (loi de finances 2026 du Cameroun si disponible,
   sinon 2025 en le signalant), avec l'article du Code général des impôts.
6. Aucune donnée réelle d'entreprise, aucun identifiant ni mot de passe.

Sources Sage utiles :
- Découpage fonctionnel détaillé (un PDF par produit) :
  https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=240126081806063
- Structure des bases Sage 100 V12.20 (tables et champs) :
  https://fr-kb.sage.com/portal/app/portlets/results/viewdocument.jsp?solutionid=230113095648937
- Manuels techniques : https://fr-kb.sage.com/portal/app/portlets/results/viewsolution.jsp?solutionid=230113110234020
- Aides en ligne Sage, manuels de référence Sage 100 Comptabilité et Gestion commerciale.

---

### PRIORITÉ 1 — indispensable pour finir les menus et les droits

#### R1. Arborescence complète des menus de Sage 100 Comptabilité V12
**Pourquoi** : nos menus Comptabilité ne sont pas vérifiés ; les autorisations d'accès en dépendent directement.
**Quoi** : pour Fichier, Édition, Structure, Traitement, Etat, Fenêtre et ?, **toutes** les commandes et **tous
les niveaux** de sous-menus, dans l'ordre, avec séparateurs, raccourcis, édition requise et une phrase de
description. Ne rien oublier, en particulier :
- Etat › **Etats tiers** (grand-livre, balance, échéancier, balance âgée, relevés, justificatif de solde à date,
  statistiques tiers, historique des rappels…), Etats analytiques, états budgétaires, Analyse et contrôles,
  bilan / compte de résultat, déclarations de taxes, réimpressions, états de révision ;
- Traitement : saisie des journaux, saisie par pièce, saisie par lot, interrogation et lettrage, lettrage
  automatique, rapprochement bancaire, extraits, règlements tiers, rappels / relances, abonnements, réimputation,
  recherche d'écritures, révision, fin d'exercice (clôture, reports à nouveau, archivage)… ;
- Structure : plans (comptable, tiers, analytique, reporting), codes journaux, taxes, banques, modèles, postes
  budgétaires, devises… ; Fichier : paramètres de la société avec **tous** leurs onglets.
**Livrable** : `MENUS_COMPTABILITE.csv`.

#### R2. Menus Édition, Fenêtre et ? de Sage 100 Gestion commerciale V12
**Pourquoi** : le découpage officiel Gescom ne les détaille pas.
**Livrable** : `MENUS_GESCOM_COMPLEMENT.csv` (même format que R1).

#### R3. Autorisations d'accès (Comptabilité et Gestion commerciale)
**Pourquoi** : notre écran existe, mais ses libellés et règles doivent être ceux de Sage.
**Quoi** :
1. Profils et utilisateurs : fiche utilisateur, fiche profil, onglets, administrateur / superviseur, mots de passe.
2. Présentation de l'arbre des droits (+ / −, profondeur, droit global d'un menu).
3. **Libellés exacts des niveaux** et effet précis de chacun (consulter, créer, modifier, supprimer, imprimer ?).
   Nous avons retenu : « Tout autoriser », « Interdire la suppression », « Interdire l'écriture », « Tout interdire ».
4. Droits particuliers hors menus : journaux protégés, types de journaux, prix d'achat, marges, remises, dépôts,
   souches, collaborateurs, etc.
5. Comportement d'une commande interdite à l'écran (grisée, masquée, message).
**Livrables** : `AUTORISATIONS.md`, `NIVEAUX_DROITS.csv`, `DROITS_PARTICULIERS.csv`.

#### R4. Espace de travail Sage 100 V12
**Pourquoi** : nous imitons la zone centrale et la barre verticale.
**Quoi** : fenêtres (réduire, agrandir, fermer, plusieurs fenêtres, cascade / mosaïque, liste dans le menu
Fenêtre), barre verticale (activer / désactiver, contenu, personnalisation), page d'accueil V12 (widgets, indicateurs,
raccourcis), barre d'outils (boutons et ordre).
**Livrable** : `ESPACE_DE_TRAVAIL.md`.

---

### PRIORITÉ 2 — conformité légale (Cameroun / OHADA)

#### R5. Fiscalité camerounaise de la facturation et des achats
**Pourquoi** : la TVA seule ne suffit pas ; des sociétés utilisent déjà le logiciel.
**Quoi** :
- TVA : taux (y compris centimes additionnels communaux), base, exonérations, régime des **non-assujettis** et
  mention obligatoire sur leurs factures ;
- **précompte** sur achats et **acompte d'impôt sur le revenu (AIR)** : taux selon le régime du fournisseur,
  qui retient, comment l'écrire sur la facture et en comptabilité ;
- **droit de timbre** (sur factures, quittances, reçus) ;
- régimes d'imposition (réel, simplifié, impôt libératoire) : seuils et obligations de facturation ;
- **mentions obligatoires** d'une facture au Cameroun (NIU, RCCM, numérotation…) ;
- **facture électronique / facture normalisée** au Cameroun : obligations et calendrier en vigueur en 2026.
**Livrable** : `FISCALITE_CAMEROUN.md` + `TAUX_ET_REGLES.csv`
(`impot;regime_ou_cas;taux;base;qui_retient;compte_syscohada;mention_facture;article_CGI;source;preuve`).

#### R6. Plan comptable SYSCOHADA révisé (2017) complet
**Pourquoi** : nous n'avons qu'environ 200 comptes.
**Quoi** : tous les comptes (classes 1 à 9) jusqu'au niveau le plus fin publié, avec leur intitulé exact.
**Livrable** : `PLAN_SYSCOHADA.csv` (`numero;intitule;classe;niveau;compte_parent;source`).

#### R7. États financiers SYSCOHADA révisé
**Pourquoi** : il manque le tableau des flux de trésorerie, les notes annexes et le système minimal de trésorerie.
**Quoi** : pour le **système normal** et le **système minimal de trésorerie (SMT)** : bilan, compte de résultat,
**tableau des flux de trésorerie** (rubriques ZA…), liste des **notes annexes**. Pour chaque rubrique : référence
officielle, libellé, comptes rattachés, formule de calcul.
**Livrable** : `ETATS_FINANCIERS_SYSCOHADA.csv`
(`etat;systeme;reference;libelle;comptes_debit;comptes_credit;formule;source`).

#### R8. DSF Cameroun (déclaration statistique et fiscale)
**Pourquoi** : la commande « DSF » est grisée dans nos menus.
**Quoi** : structure de la DSF en vigueur (tableaux, codes, correspondance avec les états SYSCOHADA), format de dépôt
(papier, électronique, fichier), échéance.
**Livrable** : `DSF_CAMEROUN.md`.

---

### PRIORITÉ 3 — fidélité des écrans à Sage

#### R9. Fiches et écrans de Sage 100 Gestion commerciale V12
**Pourquoi** : nos fiches ont moins d'onglets et de champs que Sage.
**Quoi** : pour chaque écran, les **onglets** et les **champs** (libellé exact, type, obligatoire, valeurs possibles,
valeur par défaut) :
- fiche article (Identification, Descriptif, Paramètres, Champs libres…) ;
- fiche client et fiche fournisseur (Identification, Complément, Paramètres, Contacts, Banques…) ;
- document de vente / d'achat / de stock : en-tête, lignes (colonnes), pied, onglets ;
- famille, dépôt, catégorie tarifaire, règlement ;
- Fichier › Paramètres société (tous les onglets).
Et la **matrice exacte des transformations** autorisées entre types de documents (V12).
**Livrable** : `ECRANS_GESCOM.csv`
(`ecran;onglet;ordre;champ;type;longueur;obligatoire;valeurs;defaut;description;source;preuve`)
+ `TRANSFORMATIONS.csv` (`domaine;type_origine;type_cible;autorise;remarque;source`).

#### R10. Fiches et écrans de Sage 100 Comptabilité V12
**Quoi** : même relevé pour la fiche compte général, la fiche tiers (côté comptable), le code journal, la saisie des
journaux (colonnes du bandeau et de la grille), la saisie par pièce, l'interrogation et lettrage, le rapprochement,
la fiche banque, la fiche taxe, le paramétrage des exercices.
**Livrable** : `ECRANS_COMPTABILITE.csv` (mêmes colonnes que R9).

#### R11. États standard de Sage 100 (colonnes et options)
**Quoi** : pour les états principaux (Gescom : statistiques ventes / achats, état du stock, inventaire,
échéancier ; Comptabilité : brouillard, journal, grand-livre, balance, balance âgée, échéancier, états tiers), les
**options de sélection** proposées avant impression et les **colonnes** imprimées.
**Livrable** : `ETATS_STANDARDS.csv`
(`produit;etat;type;option_ou_colonne;libelle;valeurs;source;preuve`).

---

### PRIORITÉ 4 — reprise des données Sage et technique

#### R12. Colonnes SQL de Sage 100 V12 à confirmer
**Pourquoi** : notre outil de reprise (lecture seule) utilise des colonnes absentes de notre catalogue.
**Quoi** : confirmer dans « Structure des bases Sage 100 V12.20 » l'existence, le type et la signification de :
`F_COMPTET.CT_Intitule`, `CT_Type` (valeurs : 0 client, 1 fournisseur, 2 salarié, 3 autre ?), `CG_NumPrinc`,
`CT_Ville`, `CT_Telephone`, `CT_EMail`, `CT_Sommeil`, `CT_Encours`, `CT_Assurance`, `N_CatTarif` ;
`F_COMPTEG.CG_Intitule`, `CG_Type`, `CG_Lettrage` ; `F_ARTICLE.AR_PrixAch`, `AR_PrixVen`, `AR_UniteVen`
(code ou libellé ?), valeurs de `AR_SuiviStock` ; `F_ECRITUREC` : filtres pour exclure les écritures de
simulation / d'une autre norme (`EC_Norme` ?) ; `F_JOURNAUX.JO_Intitule`, `JO_Type`.
**Livrable** : `COLONNES_SQL_SAGE.csv` (`table;colonne;type;longueur;signification;valeurs;page;preuve`).

#### R13. Hébergement et sauvegarde (2026)
**Quoi** : offres gratuites ou peu coûteuses **actuelles** pour héberger une application Django + PostgreSQL
accessible depuis le Cameroun (Render, Railway, Fly.io, Neon, Supabase…) : limites, mise en veille, durée de
conservation des bases gratuites, sauvegardes automatiques, prix d'entrée de gamme.
**Livrable** : `HEBERGEMENT_2026.md`.

---

## Partie 3 — Format de livraison

Un **zip** contenant un dossier par thème, chacun étant un skill autonome :

```
livraison/
  sage100-menus-droits-v12/      # R1, R2, R3, R4
    SKILL.md
    references/ MENUS_COMPTABILITE.csv, MENUS_GESCOM_COMPLEMENT.csv, AUTORISATIONS.md,
                NIVEAUX_DROITS.csv, DROITS_PARTICULIERS.csv, ESPACE_DE_TRAVAIL.md, SOURCES.csv, INCONNUES.csv
  ohada-cameroun-fiscalite-comptable/   # R5, R6, R7, R8
    SKILL.md
    references/ FISCALITE_CAMEROUN.md, TAUX_ET_REGLES.csv, PLAN_SYSCOHADA.csv,
                ETATS_FINANCIERS_SYSCOHADA.csv, DSF_CAMEROUN.md, SOURCES.csv, INCONNUES.csv
  sage100-ecrans-etats-v12/      # R9, R10, R11
    SKILL.md
    references/ ECRANS_GESCOM.csv, TRANSFORMATIONS.csv, ECRANS_COMPTABILITE.csv, ETATS_STANDARDS.csv,
                SOURCES.csv, INCONNUES.csv
  sage100-sql-hebergement/       # R12, R13
    SKILL.md
    references/ COLONNES_SQL_SAGE.csv, HEBERGEMENT_2026.md, SOURCES.csv, INCONNUES.csv
```

On peut livrer **par étapes** : d'abord la priorité 1, puis les suivantes.

### `SKILL.md`
En-tête YAML obligatoire :
```
---
name: sage100-menus-droits-v12
description: Une phrase qui dit quand utiliser ce skill.
---
```
Puis : résumé, mode d'emploi des fichiers, limites et version des sources.

### Fichiers CSV
Séparateur `;`, encodage UTF-8, une ligne d'en-tête, pas de cellule fusionnée.

**`MENUS_COMPTABILITE.csv` et `MENUS_GESCOM_COMPLEMENT.csv`** : une ligne par commande **ou séparateur**,
dans l'ordre d'affichage.

| Colonne | Contenu | Exemple |
|---|---|---|
| `produit` | COMPTABILITE ou GESCOM | COMPTABILITE |
| `version` | V12, V11… | V12 |
| `menu` | Fichier, Édition, Structure, Traitement, Etat, Fenêtre, ? | Etat |
| `ordre` | rang dans son parent (1, 2, 3…) | 5 |
| `niveau` | 1 = commande du menu, 2 = sous-commande… | 2 |
| `chemin` | chemin complet, niveaux séparés par ` > ` | Etat > Etats tiers > Balance âgée |
| `libelle` | libellé exact | Balance âgée |
| `type` | COMMANDE, SOUS_MENU ou SEPARATEUR | COMMANDE |
| `raccourci` | raccourci clavier, vide sinon | |
| `edition` | édition ou option requise, vide si toutes | |
| `description` | une phrase | Créances échues par tranches d'ancienneté |
| `preuve` | DOC-OFFICIEL, DOC-TIERS ou A-CONFIRMER | DOC-OFFICIEL |
| `source` | URL ou document + page | KB 240126081806063, PDF Comptabilité p. 12 |

**`NIVEAUX_DROITS.csv`** :
`produit;libelle_exact;effet_consultation;effet_creation_modification;effet_suppression;preuve;source`

**`DROITS_PARTICULIERS.csv`** : `produit;libelle_exact;emplacement_dans_l_ecran;effet;preuve;source`

**`SOURCES.csv`** : `id;titre;editeur;url;version_ou_date;consulte_le`

**`INCONNUES.csv`** : `sujet;question;pistes;impact`

Les autres colonnes sont indiquées dans chaque recherche ci-dessus.

Merci !
