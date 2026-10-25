# Audit : comptabilité générale source unique, analytique Véhicules / Propriétaires, reporting

Skills appliqués (installés dans `.claude/skills/`, version cumulative du 25/10/2026) :
- `erp-transport-comptabilite-source-unique` (prioritaire) ;
- `erp-transport-comptabilite-generale-analytique` ;
- `erp-transport-reporting-analytique`.

Les skills précédents (plan analytique, caisses, rapport journalier) sont mis à jour dans le même envoi.

Légende : ✅ conforme · 🟡 partiel · ❌ absent · ⚠️ contraire à la règle (corrigé ci-dessous).

## 1. Constat avant modification

| Règle | État | Constat dans le code |
|---|---|---|
| Aucun montant analytique sans écriture générale validée | ✅ | Le véhicule est une **colonne de la ligne d'écriture générale** (`LigneEcriture.vehicule`). L'analytique n'est donc pas une seconde table de montants : une ligne analytique orpheline est impossible par construction. |
| Seules les écritures validées alimentent les états | ✅ | Balance et grand-livre des véhicules, décompte partenaire et rapport journalier filtrent `STATUT_VALIDEE`. |
| Ventilation = même montant, sans double charge | ✅ | La paie répartit le salaire sur les lignes de la même écriture (`Employe.repartition`). La part de chaque véhicule d'un billet en correspondance est une ligne de l'écriture de départ. |
| Rentabilité (Direction) | ⚠️ | Les montants venaient des billets, des colis et des dépenses (données d'exploitation), et non des écritures. Une retenue d'annulation était ajoutée au départ. |
| Non affecté visible, rapprochement GL | ❌ | Aucun état ne montrait les charges et produits sans véhicule. |
| Propriétaire selon le contrat daté | 🟡 | Le décompte suit le contrat ; aucun état « Propriétaires » (portefeuille, résultat, situation financière séparée). |
| Flottes Classique / VIP distinctes | ❌ | Aucune notion de gamme. |
| Menu : générale + analytique (Véhicules, Propriétaires) | 🟡 | États des véhicules dans la Comptabilité ; propriétaires seulement dans la Direction. |
| Correction par contrepassation | ✅ | Les annulations passent des écritures inverses (billets, colis) ; rien n'est effacé. |
| Hors connexion, provisoire | 🟡 | Rapport journalier : état et synchronisation affichés ; pas encore sur les états analytiques du siège. |

## 2. Modifications faites (migrations additives, aucune donnée supprimée)

**Flottes Classique / VIP.**
- `Vehicule.gamme` et `Ligne.gamme` (Classique par défaut) ; historique daté `ChangementGamme`, ouvert pour chaque véhicule existant.
- Un véhicule ne fait que les départs de sa flotte : contrôle à la programmation et au départ.
- Une ligne VIP a son propre tarif. **Défaut corrigé** : un billet VIP prenait le prix Classique.
- La gamme est transmise aux agences par les échanges.

**Comptabilité analytique — deux rubriques**, dans le menu Etat de la Comptabilité (la disposition Sage des onglets est conservée) :
- **Véhicules › Comptes d'exploitation** :
  - par véhicule : billetterie, bagages, colis, autres produits, total des charges ;
  - résultat d'exploitation, part du propriétaire (622), résultat pour la société ;
  - filtres : période, flotte, et agence au siège ;
  - **rapprochement avec la comptabilité générale** : produits et charges, affecté et non affecté.
- **Fiche d'un véhicule** :
  - compte d'exploitation par rubrique ;
  - chaque montant renvoie à l'écriture générale d'origine ;
  - historique daté du propriétaire et de la flotte ;
  - voyages et kilomètres présentés comme données d'exploitation, hors montants.
- **Propriétaires › Portefeuilles et résultats** :
  - résultats attribués selon le contrat **en vigueur à la date de chaque écriture** ; les véhicules propres restent à la société ;
  - situation financière séparée : droits calculés non approuvés (provisoire), dû comptabilisé, règlements, solde du compte en comptabilité générale.
- **Propriétaires › Relevés et règlements** : écran existant, accessible aussi depuis la Comptabilité.

**Rentabilité.**
- Montants tirés des écritures validées, rattachés au départ par leur pièce (départ, colis, dépense, plein, avance de mission) ; le reste est « hors voyage ».
- Voyageurs et remplissage restent des données d'exploitation.

## 3. Reste à faire (à valider)

| Point | Proposition |
|---|---|
| Bagages payants | Saisie rattachée au billet et au voyage, produit propre (compte à valider), rubrique déjà prévue. |
| Charges communes réparties | Clés de répartition validées, ventilation d'une ligne générale sur plusieurs véhicules (somme identique), journalisée. Aujourd'hui elles restent « non affectées ». |
| Affecter un véhicule à une ligne générale validée | Écran contrôlé et tracé (modifie la dimension, jamais le montant). |
| Reporting comparatif | Module Reporting : comparaisons agences, périodes, Classique/VIP, lignes, sur les mêmes écritures. |
| Statut provisoire au siège | Afficher sur les états analytiques la date du dernier fichier reçu de chaque agence. |
| Correspondance VIP | Placement d'un voyageur VIP en correspondance : imposer la même flotte ou un complément de prix (règle à fixer). |
| Comptes | 622 (part du propriétaire), 401, 41911 / 41912 / 41913 : **à valider par l'expert-comptable**. |
