# Module ACHATS ET APPROVISIONNEMENTS — cahier des charges

## Menus
- `Tableau de bord achats` ; `Demandes internes / Approbation` ; `Consultations / Devis fournisseurs` ; `Comparatif des offres` ; `Bons de commande` ; `Réceptions` ; `Factures fournisseurs et avoirs` ; `Règlements fournisseurs` ; `Articles / Catalogues` ; `Dépôts / Stocks` ; `Transferts inter-dépôts` ; `Sorties / Consommations` ; `Inventaires / Écarts` ; `Reporting achats` ; `Fournisseurs / Contrats`.
- Autoriser deux politiques par agence / catégorie / seuil : **achat local** ou **achat centralisé au siège**, avec possibilité d'achat siège pour le compte d'une agence et livraison directe dans son dépôt.
- Catégories : pièces automobiles (filtres, pneus, freins, huiles...), emballage courrier (scotch/ruban adhésif, cartons, sacs, étiquettes), fournitures de bureau, consommables informatiques, matériels durables (imprimantes, terminaux de scan, équipements garage) et services externes (réparations sous-traitées).

## Workflow opérationnel obligatoire
`Demande d'achat` → `Validation hiérarchique` → `Devis et comparaison fournisseurs` → `Bon de commande` → `Livraison / Réception / Contrôle qualité` → `Facture + rapprochement 3 pièces (BC/BR/Facture)` → `Comptabilisation GA` → `Dette fournisseur / règlement` → `Entrée stock ou immobilisation` → `Sortie stock sur ordre du service` → `Charge GA de consommation et imputation analytique`.

À différencier : devis client / devis fournisseur ; une demande interne peut comporter plusieurs devis, achats fractionnés, validations partielles, livraisons en plusieurs fois, retours, ristournes, avoirs, achats urgents sans BC sous politique autorisée, immobilisations et prestations qui ne passent pas en stock. Un bon de commande **n'est pas** une facture et **ne déclenche pas** à lui seul un produit/une charge.

## Écritures et stocks (schémas À VALIDER)
- **À réception / facture** : provisionner les stocks ou immobilisations contre compte fournisseur selon séquence facturation/réception et réglementation ; ne pas passer automatiquement les stocks en charge.
- **À la consommation** : débit compte charge de pièces ou de consommables approprié ; crédit du stock selon méthode de valorisation validée (FIFO/CUMP selon paramétrage autorisé) ; **ventilation analytique seulement APRÈS comptabilisation GA**.
- **Facture fournisseur réglée** : débit compte fournisseur / crédit banque/caisse, aucun deuxième achat.
- **Transfert inter-dépôt d'une même société** : mouvement quantitatif et valeur stock par site ; ne constitue pas une vente, ni une nouvelle charge.
- **Matériel immobilisable** : immobilisation en classe 2, pas charge totale d'achat ; amortissements ultérieurs selon règles validées par la comptabilité.
- **Répartition analytique** : pièce utilisée au garage → véhicule réparé ; ruban/carton → activité courrier (ou véhicule seulement si attribuable/ventilation documentée) ; papier → agence/service administratif ; dépenses communes → pool « NON_AFFECTE » avant répartition approuvée ; coût véhicule propriétaire et quote-part de contrat distincts.

## Dépôts et responsabilités
- Un dépôt principal au siège et des dépôts d'agence configurables : entrepôt pièces, fournitures, emballages, consommables ; emplacements, lots/numéro de série si applicable, seuil mini, transfert siège→agence, inventaires tournants.
- Gestion de stock en hors connexion : un dépôt ne peut sortir qu'un article selon sa disponibilité locale réservée ; références uniques, anti-doublon et rapprochement à synchronisation.
- À la sortie de garage : ordre de réparation, véhicule, bon de sortie stock, technicien, quantité, coût comptable, source ligne GL ; interdit de facturer deux fois même pièce.

## Cas de recette démonstratifs
1. Direction Douala achète du ruban pour Bertoua, fournisseur livre directement à Bertoua : dépôt Bertoua crédité en quantité, dette fournisseur au GL, AUCUNE charge courrier avant sortie consommée.
2. Garage Bertoua reçoit six filtres, en consomme un pour BUS-005 : six entrées stock, une sortie, un coût GA à la date de consommation, une ventilation analytique du BUS-005, cinq restant en stock.
3. Bureau achète une imprimante destinée à durer plusieurs exercices : facture immobilisée et non consommable courant.
4. Livraison partielle / facture avec prix divergent : blocage `3-way match`, demande d'approbation, audit.
5. Double réception du même événement offline : aucune double entrée stock ou dette.
