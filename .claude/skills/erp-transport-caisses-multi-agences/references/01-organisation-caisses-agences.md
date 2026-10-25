# 01 — Organisation des caisses par agence et droits

## Règle maîtresse : configuration libre par agence

L'agence est une **unité d'exploitation**. À sa création, choisir les caisses autorisées : une seule, plusieurs, ou temporairement une caisse inactive sans gestion espèces (opérations sans paiement possibles sous droits). La petite/grande taille ou le fait d'être au siège n'est qu'un profil d'assistance, **jamais un verrou métier**.

### Profils recommandés (modifiable)

| Profil | Configuration initiale facultative | Rapport standard |
|---|---|---|
| Agence de proximité | CAISSE PRINCIPALE mutualisée | 1 tableau synthèse caisse |
| Grande agence | BILLETTERIE ; COURRIER ; CAISSE GÉNÉRALE (option GARAGE) | détail par caisse et total agence |
| Agence du siège | BILLETTERIE ; COURRIER ; GARAGE si règlement autonome ; CENTRALE | détail multi-caisses et total agence |
| Direction/siège administratif | accès de supervision / éventuellement caisse propre | états de supervision, aucun encaissement inventé |

Les caisses sont des **unités de détention et de responsabilité des fonds physiques**. Le service garage n'a une caisse propre **que s'il tient effectivement des fonds**. Une caisse technique de paiement ne doit pas être créée artificiellement pour représenter une dépense comptable.

### Fiche caisse

- Tenant/société, agence, code unique dans l'agence, nom explicite, nature (guichet/service/générale/coffre/petite caisse), statut active/suspendue/fermée, devise, date d'effet, restrictions facultatives de paiements, seuils/plafonds configurables.
- Caissiers autorisés, responsable, suppléant, responsables d'approbation, sessions d'ouverture/fermeture ; journaux d'affectation historisés.
- Une caisse « par défaut » peut être prévue pour simplifier la petite agence ; changer cette affectation ne réécrit pas les opérations historiques.
- Si l'agence opère plusieurs caisses, choix automatique par droits du poste/service ou sélection contrôlée, jamais caisse « invisible » choisie silencieusement.

### Ce que chaque acteur peut faire

| Profil | Règle d'accès minimale |
|---|---|
| Vendeur billets | vendre/encaisser via sa caisse attribuée ; lire ses opérations |
| Agent courrier | gérer colis et encaisser via caisse autorisée (même commune si besoin) |
| Garage / maintenance | enregistrer réparation et demande de paiement ; accès caisse uniquement si rôle cumulatif explicitement accordé |
| Caissier | ouvrir session, enregistrer paiement/décaissement validé, remises, clôture et décompte de **sa** caisse |
| Chef d'agence | voir caisses de son agence, approuver dans ses limites, valider rapprochements ; ne voit pas les autres agences par défaut |
| Comptable | consulter et comptabiliser flux autorisés, rapprocher et corriger via pièces de régularisation |
| Direction | consulter états consolidés des agences et autoriser les exceptions selon délégation |
| Administrateur technique | paramétrer selon habilitation ; **aucun droit d'encaissement implicite** |

Interdire partage de session ou identifiant utilisateur. Autoriser plusieurs sessions ou caissiers selon workflow explicite et contrôle de concurrence ; demander un responsable de caisse pour chaque période de clôture.

## Distinctions à préserver

- `service_origin`: billetterie/courrier/garage/etc. (qui produit le fait métier).
- `cashbox`: lieu responsable des espèces (qui prend/remet les fonds).
- `payment_method`: espèces, carte, Mobile Money, virement (comment le règlement a été fait).
- `payment_account`: caisse espèces, compte bancaire ou portefeuille électronique (où l'argent existe).
- `agency_operational`: où le voyage ou le véhicule produit l'activité.
- `agency_cash`: où le paiement a eu lieu.
- `cashier_id`: qui a reçu/payant physiquement (selon opérations).

Cette séparation garantit que : 1) une petite agence peut vendre des billets et des colis dans une même caisse ; 2) une grande agence peut avoir plusieurs caisses par service ; 3) une réparation saisie au garage peut être payée par caisse centrale ou banque ; 4) la comptabilité retrouve le bon véhicule sans confondre son coût et l'emplacement des fonds.
