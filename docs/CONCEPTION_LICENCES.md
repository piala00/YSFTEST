# Licences de l'ERP OHADA — note de conception (à valider par le propriétaire)

**Statut : validé par le propriétaire le 27/10/2026 (« choisir les meilleures options et appliquer ») ; implémenté.**

Choix appliqués : postes = **comptes utilisateurs actifs** ; licence **annuelle ou définitive** au choix à
l'émission (annuelle par défaut) ; **essai 30 jours, 3 postes** ; rappel 30 jours avant, **15 jours de grâce puis
lecture seule** ; **une licence par serveur** (direction, chaque agence, site unique), regroupées par client.
Code : `apps/licences/` (contrôle), `deploy/licences/licences.py` (outil du propriétaire).

## Mise en route pour le propriétaire (une seule fois)

1. Télécharger **ERP-OHADA-Licences.exe** (artefact « ERP-OHADA-Licences-PROPRIETAIRE » de la CI) sur VOTRE ordinateur.
2. Double-clic → **1. Créer la paire de clés** → choisir un mot de passe solide (10 caractères ou plus).
   Sauvegarder le dossier `ERP-OHADA-Licences` (clé privée + registre) sur une clé USB gardée au coffre.
3. Envoyer à Claude le contenu de **cle-publique.txt** (une ligne, sans danger) : il est ajouté dans
   `apps/licences/cle_publique.txt` et les programmes suivants savent vérifier vos licences.
4. Pour chaque client : il vous envoie le **code d'activation** (écran *Licence*) → double-clic sur l'outil →
   **2. Émettre une licence** → envoyez-lui le fichier `.erplic` produit.

Les sections suivantes gardent la proposition d'origine ; les **[À DÉCIDER]** sont tranchés comme ci-dessus.

## 1. Principes

- **Vérifiable hors ligne** : le serveur n'a jamais besoin d'Internet pour vérifier sa licence (agences sans connexion).
- **Fichier signé** : la licence est un petit fichier (`.erplic`) signé par le propriétaire. Le logiciel contient
  seulement la **clé publique** : il peut vérifier une licence, jamais en fabriquer une.
- **La clé privée reste chez le propriétaire**, sur son ordinateur (et une copie de secours hors ligne). Elle n'est
  **jamais** dans le dépôt GitHub, ni dans l'exécutable, ni dans l'installateur.
- **Jamais de perte de données** : une licence absente ou expirée ne bloque jamais l'accès en lecture, les exports
  ni les sauvegardes (obligations comptables du client).
- **Honnêteté** : une protection hors ligne peut être contournée par un spécialiste déterminé ; le but est d'empêcher
  la copie facile et l'usage non payé ordinaire, pas d'être inviolable.

## 2. Contenu d'une licence

| Champ | Exemple | Rôle |
|---|---|---|
| numéro | LIC-2026-0042 | référence commerciale |
| client | raison sociale, NIU | affichés dans le logiciel et sur les états |
| édition | Transport ou Commerce (ou les deux) | une édition non achetée ne démarre pas |
| rôle du site | Direction, Agence DLA, site unique | une licence par serveur |
| postes | 10 | nombre maximal **[À DÉCIDER : comptes actifs ou connexions simultanées]** |
| machine | empreinte du serveur | la licence ne marche que sur ce serveur |
| émise le / valable jusqu'au | 01/11/2026 → 31/10/2027 | **[À DÉCIDER : abonnement annuel ou licence définitive + maintenance]** |
| mises à jour jusqu'au | 31/10/2027 | versions du logiciel couvertes |
| signature | Ed25519 | rend toute modification du fichier détectable |

Algorithme : **Ed25519** (bibliothèque `cryptography`, déjà incluse dans l'exécutable pour les échanges).

## 3. Lien avec la machine (empreinte du serveur)

- Empreinte = identifiant Windows de la machine (`MachineGuid`) + nom de l'édition, passés dans une fonction de hachage.
  Rien de personnel n'est transmis.
- **Code d'activation** affiché dans *Fichier › Administration du poste › Licence* : le client l'envoie au
  propriétaire (WhatsApp, e-mail) ; le propriétaire renvoie le fichier `.erplic`, que le client dépose sur le même écran.
- **Changement de serveur** (panne, nouveau PC, Windows réinstallé) : nouveau code → nouvelle licence émise par le
  propriétaire. Les données, elles, se déplacent par la sauvegarde habituelle.

## 4. Période d'essai

- À la première installation : **essai de 30 jours [À DÉCIDER]**, toutes fonctions, avec le bandeau
  « Version d'essai — reste N jours » et la mention « Essai » sur les états imprimés.
- La date de début d'essai est gardée en plusieurs endroits (base, dossier des données, registre Windows), signée avec
  l'empreinte de la machine : réinstaller le logiciel ne relance pas l'essai.
- Recul de l'horloge détecté (date du jour antérieure à la dernière date vue) : avertissement, l'essai ne s'allonge pas.

## 5. Ce qui se passe à l'expiration

1. **30 jours avant** : rappel à l'administrateur sur l'accueil.
2. **Échéance** : délai de grâce de **15 jours [À DÉCIDER]** avec avertissement sur chaque page.
3. **Après la grâce** : **lecture seule** [À DÉCIDER] — consultation, états, impressions, exports, sauvegardes et
   restauration restent possibles ; les saisies sont refusées avec un message clair.
   Déposer une nouvelle licence rétablit tout immédiatement, sans redémarrage.

Le contrôle se fait au démarrage et une fois par jour ; il ne ralentit pas les écrans.

## 6. Postes

Deux façons de compter, au choix du propriétaire **[À DÉCIDER]** :
- **comptes utilisateurs actifs** : simple et prévisible (« 10 utilisateurs ») ; un 11e compte ne peut pas être activé ;
- **connexions simultanées** : plus souple pour les équipes qui se relaient ; la 11e connexion attend qu'une se libère.

Le serveur lui-même et la **simulation** (données fictives) ne comptent pas.

## 7. Direction et agences

- **Une licence par serveur** (direction, chaque agence), chacune liée à sa machine et à son rôle.
- Un même numéro de contrat client regroupe toutes les licences de la société ; le contrat indique le nombre d'agences.
- Une agence sans licence valide continue d'**envoyer** ses lots à la direction (pour que la comptabilité consolidée
  reste complète), même en lecture seule.

## 8. Outil du propriétaire (émission des licences)

- Petit programme séparé, **jamais livré aux clients** : *ERP-OHADA-Licences.exe* (ou commande sur le PC du propriétaire).
- Il lit la clé privée sur le disque du propriétaire (protégée par un mot de passe), demande client / édition / rôle /
  postes / dates / code d'activation, et produit le fichier `.erplic`.
- Il tient un **registre des licences émises** (fichier CSV local) : numéro, client, machine, dates.
- Génération initiale de la paire de clés : une seule fois, sur le PC du propriétaire ; la clé publique est ensuite
  copiée dans le code du logiciel (elle peut être publique sans risque).

## 9. Écran client : *Fichier › Administration du poste › Licence*

- État : essai (jours restants), licence valide (client, édition, postes, échéance), en grâce, expirée.
- Code d'activation à copier ; bouton « Déposer le fichier de licence ».
- Historique des licences déposées (journal des événements).

## 10. Tests prévus (après validation)

Licence valide / signature altérée / autre machine / autre édition / expirée → grâce → lecture seule / postes dépassés /
recul d'horloge / essai non relancé par une réinstallation / lecture, exports et sauvegardes toujours possibles /
simulation sans licence. Contrôle sur le PC Windows de GitHub avec l'installateur.

## Questions au propriétaire

1. **Postes** : compter les **comptes utilisateurs actifs** ou les **connexions simultanées** ?
2. **Durée de la licence** : **abonnement annuel** (renouvelé chaque année) ou **licence définitive** avec un an de
   mises à jour (renouvelable à part) ?
3. **Essai** : 30 jours conviennent-ils ? Avec combien de postes ?
4. **Après expiration** : 15 jours de grâce puis **lecture seule** vous conviennent-ils ?
5. **Agences** : une licence par serveur d'agence (proposé), ou une licence de la direction qui couvre N agences ?
