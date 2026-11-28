# 06 — Offline-first, synchronisation, séparation des tâches et audit

## Décentralisation

- Chaque agence possède le stockage local et l'autorité de ses caisses ; un serveur central ne doit pas être requis pour encaisser en espèces dans l'agence autorisée.
- Le siège reçoit les mouvements par **outbox/inbox**, avec IDs originaux et accusés de réception, sans re-création des encaissements.
- Rapports siège affichent dernière synchronisation de chaque agence, états « complet / provisoire / manquant » et liste des caisses en retard ; une somme partielle ne doit pas être affichée comme résultat définitif.
- Cashbox créée au siège pour une agence distante : l'agence ne peut la rendre opérationnelle qu'après réception et validation de la configuration ; versions datées avec résolution des changements en conflit.
- Deux caissiers sur une même caisse locale utilisent un contrôleur transactionnel local unique. Si le réseau local lui-même est inaccessible, **ne pas accepter des mouvements concurrents non coordonnés sur la même caisse** ; prévoir procédure de secours manuelle ou caisses indépendantes.

## Cas du transfert agence ↔ siège quand hors ligne

L'agence source peut enregistrer une remise sortante en transit sous son autorité. Le siège ne crédite sa caisse à destination que lorsqu'un agent habilité reconnaît la réception, en conservant la référence du transfert. L'état consolidé présente la valeur en transit, et rapproche après synchronisation. Si les preuves de livraison sont contestées, état d'anomalie et validation manuelle.

## Gestion des droits

- Rôles limités par `tenant_id`, `legal_entity_id`, `agency_id`, `cashbox_id`, `operation`, `amount_ceiling` et plage de validité.
- Séparation des tâches configurable : enregistrement d'un paiement, annulation, remboursement, correction, approbation des écarts et clôture ne doivent pas reposer sur un utilisateur tout-puissant par défaut.
- Le siège peut superviser sans nécessairement pouvoir éditer/effacer les transactions locales. Correction = événement daté avec motif, auteur, approbateur et écriture compensatoire si nécessaire.
- Historiser changement de responsabilité, ouverture forcée, montant initial, écart de caisse, dépôts, transferts refusés et clôtures remplacées.

## Protéger les identifiants et données

Authentification forte pour fonctions financières sensibles ; ne pas mettre de secrets d'API ou de mots de passe en clair dans dépôt, QR ou logs. TLS et certificats sur échanges inter-agences. Horloges locales et dates d'activité en heure locale agence ; stocker timestamps UTC plus timezone. Numérotation documentaire globale ou préfixes/identifiants uniques par agence pour continuer hors ligne.

## Dégradations électriques

Panne Internet ≠ panne électrique. Sauvegarde locale régulière, onduleur pour serveur/switch/guichet critique, alimentation de secours selon site, procédures de reprise et tests de restauration. Ne pas promettre disponibilité totale avec équipements éteints.
