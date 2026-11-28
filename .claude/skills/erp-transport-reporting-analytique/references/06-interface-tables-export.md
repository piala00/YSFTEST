# 06 — Design des écrans, tableaux comparatifs et rapports

## Comptabilité analytique

Navigation principale reste : `Véhicules` et `Propriétaires`. Dans chaque rubrique : liste + filtres + compte d'exploitation + historique des mouvements + documents sources + export PDF/Excel. Ne pas ajouter 10 onglets de restitution obligatoires.

## Reporting transversal

Écran comportant :
- barre de filtres cohérente (période A, période B, agences, service Classique/VIP, véhicules, ligne, partenaire si autorisé, statut) ;
- tableau de synthèse **prioritaire**, avec colonnes `indicateur | A | B | écart montant | variation % | unité` ;
- tableaux croisés par véhicule/agence, puis graphiques **facultatifs**, si réellement informatifs ;
- classement top/bottom explicite, sans comparer des dénominateurs incompatibles ;
- clic sur cellule → sous-total analytique → ventilation → écriture comptable → document du service (billet, colis, garage, justificatif de paie, etc.) ;
- bouton imprimer/exporter lorsque l'application dispose de cet export.

## Rapport quotidien d'agence

**Toujours simple**, tables successives : en-tête (agence, date, statut, auteur), lignes de billetterie `véhicule/code, trajet, places ou quantités, prix unitaire, montant`, bagages, colis, sorties, détail des caisses mono/multi, recettes nettes, remises, écarts, signatures. Les soldes de caisse tiennent compte du solde d'ouverture, modes de paiement et transferts internes ; la recette du jour ne s'identifie pas nécessairement au solde à reverser.

## États spécifiques de performance

- Agences A/B entre deux périodes, produit et résultat, avec ventilation Classique/VIP.
- Véhicules par période, résultats, coût/km et disponibilité, avec indication si les kilomètres manquent.
- Propriétaire : synthèse portefeuille, comparaison des véhicules et compte financier **séparé**.
- Société : vue agrégée activités passagers/bagages/courrier ; statut des remontées d'agences.

## Impression / export

- Impression A4 portrait ou paysage selon largeur ; en-tête/période/périmètre sur chaque page ; sous-totaux, total général, numéros de page, date et heure d'édition, horodatage de fraîcheur et statut provisoire/définitif.
- CSV UTF-8/BOM selon besoin, Excel `.xlsx` avec nombres stockés en numérique et métadonnées, PDF paginé et lisible, sans colonnes coupées.
- Préférer des tableaux sobres à une interface saturée d'éléments graphiques ; libellés compréhensibles pour responsables non comptables.
