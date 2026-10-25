# 06 — Cohérence Offline-First et clôtures

- Chaque agence autonome reçoit un schéma GL local si la comptabilité locale est autorisée, sinon les opérations sont enregistrées dans l'attente de validation comptable au siège. **Dans ce second cas, ne pas produire des écritures analytiques financières définitives tant que GL n'a pas posté l'opération**.
- Si comptabilisation validée localement : marquer `POSTED_LOCAL_PENDING_SYNC`, répercuter analytique localement depuis ces lignes GL ; le siège affiche ces chiffres comme **non inclus / provisoires** jusqu'à intégration centrale reconnue, sans créer de nouvelle écriture GL.
- Clés d'événement globalement uniques (UUID/ULID) pour opérations, écritures, lignes et synchronisations ; ne jamais recycler les codes humains comme clés d'idempotence.
- Transaction DB atomique : insertion GL + outbox de publication ; réessayer à la réception sans dupliquer la ligne GL, l'analytique, ni les règlements.
- États multi-agences affichent l'heure de dernière synchro, les agences manquantes, les montants non comptabilisés et le statut de fiabilité.
- Clôture journalière d'une agence : rapports d'activité simples, solde d'ouverture + entrées − sorties = solde théorique, remises physiques, écarts ; total caisses consolidé hors transferts internes.
- La **clôture comptable et analytique** doit être ordonnée : validation GL → ventilation → rapprochement → validation rapport → clôture selon politiques. Correction ultérieure : avoir/contrepassation ou écriture d'ajustement comptable, puis nouvelle projection analytique.
- Sauvegardes testées, restauration cohérente GL/outbox/analytique, repérage des événements non publiés, journaux de réparation ; ne jamais accepter une "réparation" qui insère en analytique des montants sans source.
