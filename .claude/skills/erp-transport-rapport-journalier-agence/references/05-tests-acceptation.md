# 05 — Plan de travail pour Claude Code et tests de validation

## Ordre de réalisation

1. Cartographier les modèles actuels : agence, caisse, véhicule, voyage, ticket, bagage, colis, frais, droits et clôture.
2. Montrer modèle actuel vs champs requis pour chaque tableau ; établir source unique des événements monétaires.
3. Implémenter une projection `daily_agency_report` et l'API adaptée à l'existant ; pas de nouvelle écriture de vente déclenchée lors de la génération du rapport.
4. Créer vue HTML/tableau simple + impression ; réutiliser exactement la même projection pour PDF et CSV si nécessaires.
5. Ajouter traitement des périodes closes, écarts, statut offline et version rectificative.
6. Écrire/exécuter les tests. Fournir preuves et limites. Pas de migration destructive.

## Tests minimum

1. Trois départs, dont au moins un Classique et un VIP, chacun avec véhicule différent : montants + nombre places exacts.
2. Même véhicule effectue deux départs dans la même journée : **deux lignes** de voyage, pas une somme qui efface les trajets.
3. Un départ comporte billets de tarifs différents : deux lignes ou détail de prix, total exact sans moyenne artificielle.
4. Billet vendu la veille pour voyage aujourd'hui : dans exploitation aujourd'hui, encaissé en caisse hier uniquement.
5. Billet vendu aujourd'hui pour voyage demain : caisse aujourd'hui, exploitation demain.
6. Billet vendu à agence A pour départ à agence B : caisse de A, départ de B, et une seule recette consolidée.
7. Bagage payant du passager : bonne destination et bon véhicule; colis de messagerie indépendant.
8. Bagage annulé/remboursé : ajustement documenté, pas double compte.
9. Facture de garage non réglée : coût analytique possible, **pas de sortie caisse** dans le journalier.
10. Sortie caisse réellement payée : déduit une seule fois, y compris si elle provient du module garage.
11. Encaissement Mixte espèces + Mobile Money : montants distincts ; espèces remises différentes du net tous moyens.
12. Caisse avec solde d'ouverture non nul, transfert entrant, remboursement et remise partielle : formule exacte.
13. Coupure Internet puis reprise, événements retransmis deux fois : mêmes totaux et version centralisée sans duplication.
14. Client utilisateur agence X tente accès URL agence Y : refus par serveur.
15. Rapport provisoire avec service non synchronisé : afficher statut et horodatage, pas chiffre faussement définitif.
16. Rapport clôturé puis correction : conserver la version initiale et émettre rectificatif, traces et approbation.
17. Impression A4 paysage 10+ lignes et page supplémentaire : entête, totaux, signatures, aucune coupure de montant.
18. Rapports de deux agences au siège : centralisation sans double imputation d'un même paiement.

## Livrable de Claude Code

- Fichiers applicatifs réellement modifiés et lien vers la vue/route de rapport.
- Modèles/API, calculs et conventions de comptabilisation documentés.
- Tests réellement exécutés et leurs résultats, captures ou PDF si possible.
- Points bloquants (données historiques manquantes, règles de caisse non confirmées, modules pas encore développés).
- Aucune affirmation « prêt » si ni code, ni tests, ni migration ont été exécutés.
