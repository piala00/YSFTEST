# Règlements, crédit et auteurs visibles — version 2

## Règle actuelle U5, prioritaire sur U4

Conserver les profils client comptant/crédit, le compte, le plafond, les délais et les auteurs définis dans U4. Pour la saisie, appliquer désormais : choisir le client, charger automatiquement ses factures non soldées, sélectionner une ou plusieurs factures, ou enregistrer un règlement en attente de rattachement lorsqu’aucune facture n’est disponible.

Ne plus refuser systématiquement tout règlement dépourvu de facture. La création d’un règlement en attente est une action d’enregistrement explicite, pas seulement un brouillon. Il constate l’argent reçu sans marquer artificiellement une facture soldée. Le contrôle du client, montant, mode, trésorerie, auteur et agence reste nécessaire.

## Écran et affectations proposés

Lire FENETRES_ET_REGLEMENTS_V2.md pour le parcours et les fenêtres. Champs minimaux proposés, à confirmer dans l’en-tête annoncé : client, date, mode et trésorerie, montant reçu et référence. Le client déclenche une liste des factures non soldées : numéro/date/échéance/montant initial/reste dû et montant affecté. Ces colonnes sont une proposition, pas le relevé de la feuille attendue.

Conserver une transaction monétaire unique. Une collection d’affectations relie ce règlement aux factures sélectionnées. Proposer des montants modifiables, sans affectation FIFO silencieuse. Contrôler que chaque facture appartient au client ou à un payeur explicitement autorisé, que le montant affecté ne dépasse pas son reste et que la somme des affectations ne dépasse pas le règlement. Réserver les mises à jour concurrentes et reprendre le solde disponible au moment de validation.

Montant non affecté = montant du règlement − somme des affectations actives. Si aucune facture n’est disponible, conserver le total en attente. Le traitement d’un reliquat volontaire lorsque des factures existent reste à préciser ; ne pas l’interdire ou le rendre automatique sans décision. Le règlement partiel d’une facture reste possible selon le circuit conservé.

L’affectation ultérieure, sa correction et son annulation doivent être historisées. Elles ne créent pas de nouvel encaissement physique. Un changement de client après sélection impose un contrôle : ne pas conserver les affectations d’un autre client ; prévenir avant de perdre une saisie.

## Soldes et échéances proposés


Reste dû d’une facture = montant exigible de la facture − avoirs affectés − règlements validés affectés, selon les signes et règles comptables du dossier. Conserver montant initial, chaque affectation et contre-opération. Les documents de brouillon n’affectent pas silencieusement le reste dû. Une annulation de règlement rouvre le solde par une opération tracée, sans supprimer le reçu original.

Exemple pédagogique : facture 150000, reçu 100000 rattaché → reste 50000. Second reçu 50000 rattaché → reste 0. Chaque reçu apparaît avec son auteur et son agence ; l’utilisateur peut remonter de la facture aux règlements et inversement. La disponibilité effective du solde dans une agence distante dépend de la synchronisation.

Définir sur le client des conditions proposées par défaut ; conserver sur la facture la condition effectivement appliquée, la date de départ et la date d’échéance. Un changement futur du délai client ne recalcule pas silencieusement les factures anciennes. Le calcul en jours calendaires/ouvrés, fin de mois, plusieurs échéances et les dérogations restent ouverts.

Proposer un suivi de créances par agence propriétaire, client et facture : montant initial, échéance, jours de retard, règlements, reste dû, commercial de suivi et dernier mouvement. Distinguer commercial responsable, utilisateur qui crée le reçu et personne qui encaisse physiquement si différente.


## Crédit et agences hors ligne


Le plafond est une exigence ; sa formule et le mode de blocage restent à définir. Distinguer créance facturée et engagements de commandes non encore facturés ; ne pas décider implicitement qu’ils consomment tous le même encours. Prévoir dépassement, alerte, blocage ou dérogation avec auteur/motif selon la politique validée. Un paiement ne doit pas être bloqué simplement parce que le client dépasse son plafond.

Si plusieurs agences déconnectées peuvent engager le même plafond global, elles ne connaissent pas simultanément les autres nouvelles ventes. Ne pas promettre un plafond global strict dans cette situation. Proposer agence propriétaire seule autorisée à vendre à crédit, ou quotas répartis, ou validation centrale pour certains dépassements, selon les besoins. Les autres agences peuvent rester autorisées à recevoir des versements pour compte de l’agence propriétaire.


Pour reçu interagences, conserver agence d’encaissement, agence propriétaire de la créance et identité du paiement source. Si la facture distante n’est pas disponible localement, enregistrer le règlement en attente de rattachement, comme U5 l’autorise ; ne pas créer une facture artificielle ni annoncer celle-ci soldée. À réception des références, affecter une seule fois et rapprocher la liaison sans nouvelle entrée d’espèces dans l’agence bénéficiaire. La dénomination comptable/légale du justificatif et les comptes restent à paramétrer.

## Avances avant facture

Conserver l’avance rattachée à une commande lorsqu’un BC est identifié. Un règlement en attente de facture n’exige pas d’inventer un BC pour satisfaire le modèle. Les deux situations conservent client, versement et éventuelles affectations futures. À facturation et rattachement, ne pas créer une deuxième recette. Vérifier séparément les obligations fiscales du dossier ; U5 ne définit pas le modèle légal d’un justificatif d’avance.

## Auteur et historique sur toutes les pièces


Proposer un bandeau sur chaque fiche : créé par, créé le, agence/site d’origine ; modifié par/le ; validé par/le ; annulé ou contrepassé par/le avec motif si applicable. Afficher les informations pertinentes sans afficher les secrets techniques du compte.

Couvrir BC, BL, factures, avoirs, reçus, avances, dépenses, liaisons, transferts, déclarations magasin, inventaires, écritures, ajustements, clôtures et opérations de synchronisation. Les pièces générées automatiquement indiquent automate et utilisateur ou événement initiateur si connu ; ne pas attribuer une action automatique à une personne fictive.

Conserver l’identifiant stable de l’auteur et une identité affichable selon la politique retenue. Désactiver un compte ne doit pas effacer son attribution historique. Pour une pièce reprise sans auteur connu, afficher auteur d’origine inconnu et provenance de reprise ; ne pas prendre l’importateur pour l’auteur métier historique.

En synchronisation, conserver auteur, site et horodatage d’origine ; ajouter séparément date de réception et compte technique d’intégration. Ne pas remplacer l’auteur par l’utilisateur qui consulte, imprime ou synchronise. Distinguer date métier saisie et horodatages techniques ; les horloges locales peuvent être décalées.

Conserver une piste des changements significatifs avec ancienne/nouvelle valeur pertinente, action, auteur, date et motif. Protéger sa consultation et sa modification par des droits spécifiques ; éviter d’enregistrer inutilement des secrets ou données sensibles dans les journaux. Ne pas promettre une inviolabilité absolue : prévoir droits, sauvegardes et contrôles. Afficher l’auteur dans le document comme demandé ; la présence systématique sur toutes les impressions reste à valider.
