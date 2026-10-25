# 02 — Source de vérité, regroupements, équations et règles métier

## Deux ensembles de faits distincts

**Exploitation (date de départ)** : voyage réellement parti depuis l'agence demandée ; manifeste des billets qualifiés ; tarif réellement appliqué ; bagages transportés et facturés associés à une date/étape de voyage. Cela renseigne l'activité du véhicule, même si le paiement a été effectué avant le jour ou ailleurs.

**Trésorerie (date effective du paiement)** : mouvements financiers datés et rattachés à une caisse et à une agence d'encaissement. C'est la source des lignes « encaissé », « sorties » et « reversé » du tableau de caisse. Ne jamais convertir automatiquement un billet embarqué en encaissement.

Choix produit : l'intitulé en tête du premier tableau est « Billetterie — Départs de la journée », et la ligne de trésorerie est « Billets encaissés dans l'agence ce jour ». Si l'utilisateur souhaite uniquement une vue d'encaissement par véhicule, proposer un filtre distinct, sans remplacer la règle du départ.

## Billetterie

- Filtrer les voyages par `actual_departure_at` local dans la fenêtre journalière, et agence *physique de départ*. Exclure les départs annulés/non réalisés ; gérer les tronçons/arrêts intermédiaires sans compte double des places si plusieurs trajets sont reportés.
- Grouper `(trip_id, vehicle_id, origin, destination, fare_class, realized_unit_price)` ; garder `trip_id` même si l'affichage montre le nom du bus.
- `nb_places = count(distinct ticket/trip/seat/segment)` selon configuration métier de places « vendues », « transportées » ou « embarquées » ; éviter cumul d'un même voyageur à plusieurs escales, de réimpression, de corrections, d'avoirs.
- `total_ligne = sum(amount_eligible_of_ticket_lines)` ; si tarifs hétérogènes, ne pas faire `prix_moyen * nb_places` sans méthode précise : une ligne par prix réellement facturé ; remises/redevances doivent apparaître correctement dans la valeur nette.
- Gamme CLASSIQUE / VIP déterminée par affectation datée de véhicule et voyage, flottes distinctes.

## Bagages

- Le service bagages désigne les **suppléments payants transportés pour des passagers** ; document et paiement spécifiques si nécessaire ; franchise poids et barème paramétrables.
- Grouper par véhicule/trip/destination/designation ou détailler par pièce ; calculer total avec montants **enregistrés**, sans déduire un tarif fixe fictif.
- Attention : une recette de bagage peut être encaissée avant le départ ; le tableau exploitation et la caisse peuvent diverger légitimement.

## Colis / messagerie

- Conserver l'activité `messagerie`, indépendante des suppléments de bagages. Le véhicule peut transporter les deux ; ne pas enregistrer deux fois la même charge ou encaissement.
- Le rapport de **caisse** reprend l'encaissement dans l'agence, y compris pour un colis dont le départ est futur. Les coûts/résultats véhicule se fondent sur le transport réel.

## Sorties

- Ne prendre que les `payment/disbursement` validés et effectués depuis les caisses de cette agence ; écarter les factures sans paiement et les demandes de dépenses non autorisées.
- Empêcher doublons lorsqu'une dépense apparaît dans Garage et Comptabilité (un événement financier unique). Les sorties par banque/Mobile Money sont affichées séparément des sorties en espèces.
- Remboursements de billets : identifier clairement soit comme `remboursements` (ligne séparée de sorties) soit comme sorties de caisse, **sans double déduction** ; choix constant et configurable avec rapprochement.
- Transferts entre caisses : pas un produit/charge d'exploitation ; mouvement de trésorerie traçable, avec contrepartie et pas de duplication dans total siège.

## Équations / rapprochement

```
ENCAISSEMENTS_TOT = somme(receipts_money, agence, date de caisse, état validé)
ENCAISSEMENTS_ESPECES = somme(receipts_money where moyen=ESPECES)
ENCAISSEMENTS_ELECTRONIQUES = somme(receipts_money where moyen in compte_ou_portefeuille)
SORTIES_ESPECES = somme(disbursements_cash, validés et payés) [incl. remboursements si règles choisies]
DISPONIBLE_ESPECES = OUVERTURE_ESPECES + ENCAISSEMENTS_ESPECES - SORTIES_ESPECES - TRANSFERTS_ESPECES_SORTANTS + TRANSFERTS_ESPECES_ENTRANTS
SOLDE_THEORIQUE_FIN = DISPONIBLE_ESPECES - REMISES_ESPECES_EFFECTUEES
ECART = SOLDE_PHYSIQUE_COMPTE - SOLDE_THEORIQUE_FIN
RECETTE_NETTE_JOUR_TOUS_MOYENS = ENCAISSEMENTS_TOT - DECAISSEMENTS_REELS_JOUR (sans compter deux fois remboursement ou transfert)
```

`RECETTE_NETTE_JOUR_TOUS_MOYENS` est **un indicateur de flux net journalier**, pas résultat comptable, bénéfice, résultat du véhicule ni somme à remettre physiquement. Distinguer charges payées mais financées par autre compte, transferts internes, frais Mobile Money et régularisations.

**Règle :** lorsque les chiffres dans le tableau A ou B ne correspondent pas aux encaissements du tableau E, c'est une **différence de périmètre de dates et d'agences** potentiellement normale : afficher la raison vérifiable, pas forcer l'égalité.

## Résultats de flotte et partenaires

- La vente de billet ne crée pas deux revenus parce qu'elle apparaît dans « Jour agence » et « Résultat véhicule ».
- Les axes analytiques véhicule, voyage, ligne, gamme et partenaire sont des vues sur le **même fait métier**.
- Le reversement de l'agence n'est pas le règlement au propriétaire du véhicule. Les comptes partenaires sont déterminés par contrat, droits, avances et paiements.

## Complément multi-caisses

Chaque mouvement espèces est rattaché à `cashbox_id` et à sa source service ; les tableaux d'agence agrègent **toutes les caisses autorisées**. Les transferts source/destination entre caisses de la même entreprise sont exclus de `RECETTES_EXTERNES` et `DECAISSEMENTS_EXTERNES`. Un transfert en transit doit être isolé. `SOLDE_AGENCE_PHYSIQUE = somme(soldes des caisses physiques)` ; `TRÉSORERIE_ESPECES_GLOBALE` peut ajouter les transferts encore en transit, affichés distinctement. Le **net flux externe** exclut fonds d'ouverture et transferts internes, contrairement au **solde de caisse**. Pour les formules et exemples lire `/erp-transport-caisses-multi-agences`.

