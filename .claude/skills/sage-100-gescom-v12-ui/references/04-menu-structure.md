# 04 — Menu Structure [DOC-V12]

**Source principale : S1, pages 6 à 10.** Les rubriques des fiches sont des regroupements de fonctionnalités ; le nombre et l'ordre des **onglets réels** nécessitent des captures.

## Arborescence de référence

```text
Structure
├── Familles [d'articles]
├── Articles
├── Nomenclatures
├── Comptabilité
│   ├── Plan comptable
│   ├── Plan analytique
│   ├── Taux de taxes
│   ├── Codes journaux
│   ├── Banques
│   ├── Modèles de règlement
│   └── Modèles de grille (selon édition)
├── Codes affaires
├── Clients
├── Fournisseurs
├── Barèmes
│   ├── Commissions représentants
│   ├── Rabais, remises, ristournes clients/fournisseurs
│   └── Soldes et promotions clients/fournisseurs
├── Glossaires
├── Modèles d'enregistrement (selon édition)
├── Ressources (option/édition)
├── Centres de charges (option/édition)
├── Collaborateurs
└── Dépôts de stockage
```

### Familles

- Identification et choix de suivi de stock (sans suivi, CMUP, FIFO/LIFO, série/lot si option).
- Paramètres de tarification : fournisseurs, catégories de tarifs, remises clients.
- Statistiques et paramètres de traitement : escompte, code-barres, remises, contremarque, poids, etc.
- Logistique et valorisation comptable selon édition.

### Articles

**Identification** : référence/désignation, nature de l'article, gammes/conditionnement, suivi de stock (aucun/CMUP/FIFO/LIFO/lot-série si option).

**Tarifs** : catégories tarifaires, tarifs clients, tarifs fournisseurs, nouveaux tarifs et conditions particulières.

**Descriptif** : catalogue, description complémentaire, glossaire.

**Champs libres** : informations libres, statistiques, documents attachés, photo.

**Paramètres** : escompte, affichage/vente au poids, publication, article en sommeil, contremarque, modes de facturation, exclusion statistiques, modèles d'enregistrement.

**Logistique** : poids, unité, code-barres, article de substitution, criticité, délais de livraison/fabrication/sécurité/péremption, frais fixes.

**Dépôt** : dépôt principal, min/max, emplacement principal et contrôle (si option).

**Comptabilité** : analytique, catégorie comptable de stock.

### Nomenclatures

Fabrication (option), commerciale composé, commerciale composant, article lié, saisie variable, gamme opératoire et prévisions (option fabrication).

### Clients

**Identification** : tiers et prospect, coordonnées, contacts.

**Tarifs** : centrale d'achat si édition, catégorie tarifaire, représentant, remises, escompte, relevés, RFA, remises par famille, tarifs d'exception.

**Adresses et banques** : adresses multiples et données bancaires.

**Champs libres** : informations libres, bloc-notes, statistiques, documents joints.

**Solvabilité** : encours, code risque, contrôle automatique.

**Agenda** : suivi des événements.

**Paramètres** : payeur, modes/conditions de règlement, dépôt de rattachement, devise, langue, périodicité et priorité des livraisons, délais de transport, options de BL et facturation, catégorie comptable et informations diverses.

### Fournisseurs

**Identification / contacts**, **tarifs** (acheteur, remises/escompte/relevés, RFA, tarifs par article), **banques**, **champs libres**, **solvabilité**, **agenda**, **paramètres** (tiers encaisseur, règlement, dépôt, affaire, devise, expédition, délai d'approvisionnement, catégorie comptable), factures électroniques selon services.

### Barèmes

Commissions des représentants ; rabais/remises/ristournes clients et fournisseurs ; soldes/promotions clients et fournisseurs.

### Dépôts de stockage

Identification, éventuelle catégorie comptable, contacts, emplacements selon édition, utilisateurs, règles de réapprovisionnement et souches de documents en saisie selon édition.

## Relevés visuels pour une fiche

Pour Articles/Clients/Fournisseurs/Dépôts, demander **une capture de la liste**, **une capture de la fiche**, **une capture par onglet visible**, puis relever les intitulés de champs et les boutons. Ne jamais convertir le regroupement « Solvabilité » en onglet certain sans l'avoir vu dans cette V12.
