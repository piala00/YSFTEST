# 02 — Réservation (booking), billetterie, contrôle et embarquement

## Utilisateurs

Agents de vente, chefs de guichet, contrôleurs, chef de gare, exploitants, caisse, direction ; séparations de droits entre vente, remboursements, modification de tarif, scan, clôture et réouverture.

## Référentiels

- Ligne composée d'arrêts ordonnés et de tronçons. Départ planifié `trip_id` distinct de la ligne permanente.
- Véhicule, plan des sièges numérotés, configuration temporaire, sièges condamnés, affectation à un voyage.
- Tarifs par origine/destination, classe, bagage, catégorie, clientèle, date d'effet ; taxes/surcharges paramétrées.
- Inventaire des sièges **par tronçon**. Des réservations A→B et B→C peuvent occuper un même siège ; des réservations A→C et B→C ne peuvent pas l'occuper simultanément.

## Parcours nominal

1. L'agent choisit agence, ligne, date, voyage, montée, descente et disponibilité.
2. La réservation temporaire bloque une place pour une durée configurable au sein de son domaine d'autorité ; expiration sans vente = libération tracée.
3. Le paiement génère un ou plusieurs paiements et rattache la pièce de vente. Le billet n'est émis que selon statut financier autorisé (paiement immédiat, crédit approuvé, gratuité autorisée).
4. Émettre billet au format imprimable + QR cryptographiquement signé, identifiant UUID et numéro métier, départ/tronçon, statut, émission et audit.
5. Au départ, le contrôleur valide le billet pour le **voyage/tronçon approprié**, à travers une autorité d'embarquement capable de faire une transition atomique de `valide` vers `embarqué`.
6. Le départ produit un manifeste, nombre vendus/embarqué/no-show, clôture de voyage et calcul de recettes (dont éventuelles ventes de dernière minute).

## Cycle de vie typique

`BROUILLON → RÉSERVÉ → ÉMIS → CHECKED_IN (optionnel) → EMBARQUÉ → UTILISÉ`, avec branches `EXPIRÉ`, `ANNULÉ`, `REMBOURSÉ`, `REPORTÉ`, `ÉCHANGÉ`, `REFUSÉ`. Ne pas permettre des transitions illégales. Un report doit laisser un lien de parenté entre billet initial et nouveau billet. Un remboursement ne supprime pas la vente historique : il ajoute un avoir et, si effectivement remboursé, une sortie de trésorerie autorisée.

## Anti-fraude

- QR = référence opaque ou données minimales + signature forte, clé privée protégée, rotation/version de clé.
- À la lecture : vérification de signature, validité du voyage/tronçon, état de remboursement/annulation et de scan précédent.
- En réseau local : autorité de contrôle unique par voyage, contrainte sur consommation. Le premier scan gagnant prend le siège/billet dans une transaction unique ; autres scans refusés ou marqués comme relecture de supervision.
- Sans liaison entre scanners : ne pas promettre l'anti-double-utilisation en temps réel. Affecter un scanner maître ou déployer une seule autorité locale synchronisée en LAN. Réconciliation a posteriori si mode dégradé approuvé.
- Journaliser terminal, contrôleur, timestamp serveur, billet, véhicule, voyage, décision, raison ; protéger le manifeste et les données voyageurs.

## Ventes inter-agences et offline

Répartition par agence de *quotas exclusifs de sièges/tronçons*, préparés avant les déconnexions. Une agence peut vendre son quota local sans Internet. Aucune duplication de quota. Transfert de quota seulement via protocole confirmé par les deux propriétaires/serveur coordonnateur ; sinon garder le quota verrouillé. Les sièges sans quota restent invendables hors ligne et l'interface explique pourquoi. Prévoir waitlist, gestion des départs annulés et changement de véhicule.

## Effets métiers en chaîne

- Vente validée → billet/reçu → livre des ventes → paiement caisse si réellement encaissé → résultat voyage/ligne/véhicule selon règle de rattachement → moteur comptable pour reconnaissance de produit appropriée (attention billets vendus avant date de transport).
- Annulation → libération ou neutralisation de disponibilité + avoir éventuel ; remboursement = opération financière distincte.
- Embarquement → manifeste + statistiques de présence ; **pas de deuxième recette**.
- Clôture voyage → rapprocher billets vendus, embarqués, exception, chèques/mobile money/espèces et affectations ; anomalies à justifier.

## Rapports et tests

Tableaux vente par agence, guichetier, départ, ligne, date, moyen de paiement ; billets non utilisés, annulés, remboursés, scannés ; écarts et anomalies. Tests : concurrence sur siège, segments compatibles, expiration, remboursement partiel, tarifs historiques, copie QR, scan doublé, vente offline sur quota, modification de véhicule, conflit hors connexion, contrôleur sans autorisation.
