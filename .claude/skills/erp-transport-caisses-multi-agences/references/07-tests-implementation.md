# 07 — Tests d'acceptation et séquencement de réalisation

## Tests minimum indispensables

| ID | Situation | Attendu |
|---|---|---|
| C01 | Petite agence unique caisse, ventes billets + colis | Deux services sur la même caisse ; recettes par service et total caisse sans doublon |
| C02 | Grande agence billetterie + courrier + garage + centrale | Caisses indépendantes, utilisateurs et rapports séparés ; total consolidé exact |
| C03 | Garage enregistre une facture puis caisse centrale paye | Dépense réelle dans le garage ; sortie d'espèces uniquement à la date de paiement et dans la caisse centrale |
| C04 | 300 000 XAF transférés billetterie → centrale | Solde source -300 000, solde destination +300 000 après réception ; total agence inchangé ; pas de produit ni charge |
| C05 | Transfert sortie sans réception | Montant visible en transit, pas en caisse destinataire ; pas de disparition du patrimoine |
| C06 | Dépôt caisse d'agence → siège | Encaissement initial conservé dans l'agence ; au siège simple transfert reçu, pas recette nouvelle |
| C07 | Vente Mobile Money 40 000 | Produit/billet exact, entrée paiement électronique, **0 ajout espèces** |
| C08 | Billet encaissé la veille, départ aujourd'hui | Report activité aujourd'hui ; aucun nouvel encaissement aujourd'hui |
| C09 | Plusieurs rotations du même BUS avec tarifs | Lignes distinctes par voyage/tarif, sans gonflement des places |
| C10 | Remboursement espèce / Mobile Money | Sortie dans le bon compte, correction pièce traçable, pas doublon |
| C11 | Deux caissiers opèrent même caisse locale | Mouvements concurrents sécurisés, pas de double débit ni solde incohérent |
| C12 | Synchronisation rejoue deux fois même paiement | Un seul mouvement, une seule écriture comptable |
| C13 | Perte d'Internet pendant clôture | Rapport agence provisoire conservé ; siège reconnaît statut et se met à jour après sync |
| C14 | Caissier d'agence A lit agence B | Refus explicite, aucune fuite API/SQL |
| C15 | Caisse fermée, nouvelle tentative de paiement | Refus ou procédure exceptionnelle contrôlée |
| C16 | Changement de caisse par défaut | Historique anciennes opérations inchangé |
| C17 | Impression mono-caisse | Rapport compact sans tableau multi-caisses inutile |
| C18 | Impression multi-caisses | Récap de toutes les caisses + détail individuel, sommes égales aux mouvements source |
| C19 | Solde d'ouverture et sorties | Solde fin juste ; net du jour distinct des fonds présents |
| C20 | Partenaire/VIP/Classique | Résultat véhicule/contrat/gamme non modifié selon la caisse qui encaisse |

## Séquence recommandée après audit

1. Cartographier les rôles, modèles et cas de caisses actuels ; conserver les flux qui fonctionnent.
2. Ajouter configuration des caisses et permissions minimales ; créer la caisse historique par défaut sans pertes.
3. Introduire les transactions financières indépendantes du service, l'idempotence et les sessions.
4. Développer virements/transferts internes, caisse en transit et rapprochement.
5. Intégrer les services billet, courrier, garage, carburant, RH, partenaires et remboursements.
6. Étendre rapport simple (mono/multi) et rapports caisse/siège ; préserver export et impression existants.
7. Scénarios concurrency/offline/sync, contrôles de sommes et non-régression analytique.
8. Fournir le listing fichiers changés, scripts migrations, tests, limites et démonstration avec données anonymisées.

## Règle finale

Aucune fusion de caisses par concaténation de colonnes, aucune consolidation de paiements à partir de simples montants de ventes. Le moteur de trésorerie doit garder une trace vérifiable **mouvement → caisse → agence → service/source → justificatif**, et des mouvements internes sans gonfler les recettes.
