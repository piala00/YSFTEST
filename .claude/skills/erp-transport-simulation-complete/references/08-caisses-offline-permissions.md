# Caisses, responsabilité des services et synchronisation

## Caisse par agence
- AG01 Douala / AG02 Yaoundé / AG03 Bafoussam : démonstration de caisses multiples (`BILLET`, `COURRIER`, `GARAGE`, `CENTRALE`). Autres agences : `CAISSE_UNIQUE`, mais administrateur peut modifier selon organisation réelle.
- La simulation comptable présente un compte espèces GA symbolique agrégé `5711-DEMO`, **pas une comptabilité par caisse certifiée** : Claude doit ajouter/s'assurer des sous-comptes et journaux locaux selon le plan comptable réel, et refuser tout rapprochement par caisse absent de mouvements identifiés.
- Les services n'ont pas nécessairement de caisse : dépense garage peut être autorisée par garage et réglée par caisse centrale. Chaque paiement a `caisse_id`, `payment_method`, auteur, responsable, origine et référence.
- Les transferts entre caisses ne produisent pas de recettes ni charges. Conserver l'équilibre débit-crédit des virements internes et l'horodatage des réceptions en transit.

## Offline-first
- Base locale agence, journal outbox transactionnel, reçus idempotents, snapshots d'ouverture/clôture, sync bidirectionnelle avec contrôles d'autorité, statut `LOCAL_COMPTABILISE_NON_SYNC` vs `CENTRAL_RECONCILIE` ; report siège incomplet tant qu'une agence n'a pas synchronisé.
- Billets/sièges en offline : attribution exclusive des quotas ou autorité centralisée locale par départ, pas de vente concurrente libre du même siège ; scanner maître par voyage contre double validation.
- Achats et stock : contrôle quantités par dépôt, réservation locale et verrouillage, transfert inter-agence avec expéditeur et destinataire ; différends mis en quarantaine.

## RBAC (séparation des tâches)
- Guichetier vend, ne change pas le plan comptable ; responsable de caisse clôture, ne peut supprimer un journal ; achats saisit demande/BC, un autre valide selon seuil ; magasinier réceptionne, garage demande sortie ; comptable poste/réconcilie ; administrateur technique ne valide pas lui-même les paiements financiers ; propriétaire voit ses seuls véhicules et compte.
- Pistes d'audit immuables, pas de suppression des postes synchronisés ; données de démonstration totalement fictives.
