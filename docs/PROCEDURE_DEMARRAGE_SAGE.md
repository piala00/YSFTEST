# Procédure de démarrage et de création des sociétés (façon Sage)

Spécification donnée par le propriétaire le 2026-11-03. À implémenter dans l'édition
Transport (puis Commerce). Ce document fait foi ; toute implémentation s'y réfère.

## 1. Installation
- On installe à partir de l'**autorisation** ou de la **clé d'installation**, mais
  **cette clé / autorisation n'est plus demandée** au moment de l'installation.
- Après l'installation, le **menu du logiciel s'ouvre**, mais le logiciel est **vide**
  (aucune société).

## 2. Au premier démarrage (logiciel vide)
- Tous les menus sont présents (comme Sage), mais vides.
- Dans **Administration du poste**, deux possibilités :
  - **Restaurer une société** (depuis une sauvegarde), ou
  - **Créer une nouvelle société**.

## 3. Création d'une nouvelle société — Fichier › Nouvelle société
- On suit le **processus de création** de la société (identité, rôle, base…).
- **À LA FIN** du processus, on saisit les **informations du compte administrateur**
  (nom d'utilisateur + mot de passe) de la personne qui vient de créer la société.
- **C'est à ce moment** (saisie de l'identifiant administrateur, à la fin) que la
  **base de données de la société est créée** (dans SQL Server le cas échéant).
- Donc : **l'identifiant est à la FIN, pas au début.** (Aujourd'hui il est au début.)

## 4. Licence et version d'essai
- L'activation de la licence **ne bloque pas** : sans licence, on peut ouvrir le
  logiciel **29 fois** (essai) pour tester.
- Sans licence, on peut **créer une nouvelle société et l'utiliser** (essai), mais on
  **ne peut pas** utiliser **Sauvegarder** ni **Restaurer**.
- Sans achat de licence, on est obligé d'**effacer** cette société d'essai.
- Avec licence **activée** : accès à la **Sauvegarde** et à la **Restauration**.

## 5. Restauration d'une société existante (client qui avait déjà une licence)
- **De préférence : la personne active d'abord le logiciel avec sa licence, puis
  restaure sa société** — sans avoir besoin de créer une nouvelle société si elle en
  a déjà une.

## 6. Multi-agences (sociétés à plusieurs structures)
- Le **siège (serveur principal)** crée **chaque agence** dans Fichier ; cette création
  **crée automatiquement la base de données de l'agence** côté siège.
- Le siège **exporte** le fichier de cette agence.
- Sur le **serveur secondaire de l'agence** : on installe seulement le logiciel, puis on
  **importe le fichier d'agence** fourni par le siège.
- **Règle : le fichier d'agence sort TOUJOURS du siège.** On ne crée pas un fichier au
  siège puis un autre, différent, à l'agence. Le fichier importé à l'agence doit être
  **synchronisable** avec le serveur central (direction).

## Décisions de conception (confirmées par le propriétaire le 2026-11-03)
1. **Ouverture sans connexion jusqu'au 1er admin** : sur le poste serveur, le logiciel
   s'ouvre directement (sans login) tant qu'aucun administrateur n'existe. On crée ou
   restaure la société ; l'admin est créé **à la fin**. Ensuite, l'usage normal redemande
   la **connexion** (app réseau multi-utilisateurs avec droits).
2. **Base de données** : trois propositions, comme aujourd'hui, mais **à la fin** de la
   création de société : **SQLite**, **SQL Server**, ou **les deux (SQLite + miroir
   SQL Server)**. La base est créée à ce moment-là.
3. **Clé d'installation** : retirée de l'installation. Le contrôle se fait **uniquement
   par la licence** (29 ouvertures d'essai, puis blocage de Sauvegarde/Restauration).

## Ordre d'implémentation prévu (étapes vérifiables)
1. Premier démarrage Django : page d'accueil « vide » accessible sans connexion tant
   qu'aucun admin n'existe, avec « Créer une société » / « Restaurer une société ».
2. Création de société réordonnée : identité → rôle → base → **compte administrateur
   (fin)** → création de la base + de l'admin + marquage « configuré ».
3. Blocage d'essai : sans licence, création/utilisation possibles (29 ouvertures), mais
   Sauvegarde/Restauration verrouillées ; message « activez la licence ».
4. Restauration : activer la licence d'abord, puis restaurer (sans créer de société).
5. Multi-agences : le siège crée l'agence (crée sa base) et exporte son fichier ;
   l'agence installe + importe ce fichier (synchronisable avec le central).
6. Clé d'installation retirée de l'installateur + du lanceur compilé.
7. Tests réécrits + recompilation → validation Windows par le propriétaire.

## Suivi de l'implémentation
- D1 ✅ Premier démarrage vide, sans connexion (accueil Créer / Restaurer).
- D2 ✅ Création réordonnée : identité → rôle → base → compte administrateur à la fin.
- D3 ✅ Essai : sauvegarde/restauration verrouillées sans licence + « Repartir à zéro ».
- D4 ✅ Restaurer une société au premier démarrage (activer la licence, puis restaurer).
- D5 ✅ Multi-agences : déjà couvert par le module Échanges — le siège `ajouter_agence`
  (crée le rang/compte de liaison 185NN et la clé d'échange de l'agence) puis
  `fichier_installation` (exporte le fichier) ; l'agence l'importe au rôle « agence »
  de l'assistant. Le fichier sort toujours du siège et est synchronisable avec le central.
- D6 ⏳ Retrait de la clé d'installation + recompilation (validation Windows par le propriétaire).
