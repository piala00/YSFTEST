# Règlements, crédit et auteurs visibles

## Exigences confirmées U4

Distinguer clients comptant et clients à crédit. Pour ces derniers, conserver compte client, plafond accordé et délai de paiement de chaque facture. Lors de la création d’un reçu de règlement de créance, imposer le rattachement à une facture pour savoir quelle dette est réglée.

Afficher l’identité de la personne ayant généré chaque document lorsque l’on l’ouvre : reçu, facture, commande et tous les autres documents. Conserver également les traces pour écritures et opérations. Cette exigence est transversale, pas limitée à la caisse.

## Écran de règlement proposé

Demander client, agence propriétaire de la créance, agence d’encaissement, facture cible, date du versement, mode, caisse ou compte de réception, montant et référence du moyen de paiement. Afficher les informations nécessaires de la facture : numéro, date, échéance, montant initial, avoirs applicables, règlements déjà affectés et reste dû. Enregistrer l’auteur réel automatiquement, pas via une liste modifiable choisie par le saisissant.

Contrôler cohérence société/client/facture, devise ou conversion autorisée, statut et version de la facture, montant positif et affectation disponible. Ne pas permettre de valider un reçu de créance sans facture cible. Un brouillon incomplet n’est pas un reçu validé. Un client déjà soldé ne doit pas devenir débiteur ou avoir une affectation doublée à cause d’un rejeu.

Par défaut proposé : un reçu de créance → une facture. Une facture peut être soldée progressivement par plusieurs reçus si le règlement partiel est autorisé. Ne pas interpréter « solder cette facture » comme une preuve que seuls les paiements intégraux sont possibles ; faire valider ce point si le circuit en dépend.

Si un seul versement couvre plusieurs factures, conserver une transaction monétaire source unique et proposer des reçus de créance distincts par facture, chacun rattaché à cette transaction. Ne compter le versement qu’une fois dans le rapport de caisse ; contrôler somme des reçus = montant affecté du versement. Ce circuit et l’éventuel reçu multi-factures sont à arbitrer, pas des exigences déjà validées. Ne pas créer plusieurs mouvements d’espèces pour un seul billet remis par le client.

## Soldes et échéances proposés

Reste dû d’une facture = montant exigible de la facture − avoirs affectés − règlements validés affectés, selon les signes et règles comptables du dossier. Conserver montant initial, chaque affectation et contre-opération. Les documents de brouillon n’affectent pas silencieusement le reste dû. Une annulation de règlement rouvre le solde par une opération tracée, sans supprimer le reçu original.

Exemple pédagogique : facture 150000, reçu 100000 rattaché → reste 50000. Second reçu 50000 rattaché → reste 0. Chaque reçu apparaît avec son auteur et son agence ; l’utilisateur peut remonter de la facture aux règlements et inversement. La disponibilité effective du solde dans une agence distante dépend de la synchronisation.

Définir sur le client des conditions proposées par défaut ; conserver sur la facture la condition effectivement appliquée, la date de départ et la date d’échéance. Un changement futur du délai client ne recalcule pas silencieusement les factures anciennes. Le calcul en jours calendaires/ouvrés, fin de mois, plusieurs échéances et les dérogations restent ouverts.

Proposer un suivi de créances par agence propriétaire, client et facture : montant initial, échéance, jours de retard, règlements, reste dû, commercial de suivi et dernier mouvement. Distinguer commercial responsable, utilisateur qui crée le reçu et personne qui encaisse physiquement si différente.

## Crédit et agences hors ligne

Le plafond est une exigence ; sa formule et le mode de blocage restent à définir. Distinguer créance facturée et engagements de commandes non encore facturés ; ne pas décider implicitement qu’ils consomment tous le même encours. Prévoir dépassement, alerte, blocage ou dérogation avec auteur/motif selon la politique validée. Un paiement ne doit pas être bloqué simplement parce que le client dépasse son plafond.

Si plusieurs agences déconnectées peuvent engager le même plafond global, elles ne connaissent pas simultanément les autres nouvelles ventes. Ne pas promettre un plafond global strict dans cette situation. Proposer agence propriétaire seule autorisée à vendre à crédit, ou quotas répartis, ou validation centrale pour certains dépassements, selon les besoins. Les autres agences peuvent rester autorisées à recevoir des versements pour compte de l’agence propriétaire.

Pour reçu interagences : conserver la facture cible de l’agence propriétaire et la pièce d’origine ; ne pas créer de facture artificielle dans l’agence d’encaissement. Utiliser les données répliquées avec indication de fraîcheur et contrôle d’affectation au retour réseau. Si la facture n’est pas connue localement, l’exigence de rattachement empêche la validation d’un reçu de créance définitif dépourvu de facture. Proposer un enregistrement de versement et justificatif provisoire en attente de vérification, à faire arbitrer ; tracer l’argent réellement reçu sans prétendre que la facture est déjà soldée.

## Avances avant facture

Conserver l’exigence antérieure : une commande peut être payée avant livraison et facture. Séparer explicitement les types « avance sur commande » et « règlement de facture ». L’avance est rattachée au BC et au client ; elle ne contourne pas la règle sur les reçus de créance et ne crée pas une facture finale fictive. À facturation, affecter l’avance sans nouvel encaissement.

L’utilisateur n’a pas fixé le libellé légal des justificatifs d’avance ni le traitement fiscal ; les vérifier selon le régime applicable. Exposer ce point de conciliation dans les décisions ouvertes au lieu de supprimer les avances ou d’autoriser tous les reçus sans facture.

## Auteur et historique sur toutes les pièces

Proposer un bandeau sur chaque fiche : créé par, créé le, agence/site d’origine ; modifié par/le ; validé par/le ; annulé ou contrepassé par/le avec motif si applicable. Afficher les informations pertinentes sans afficher les secrets techniques du compte.

Couvrir BC, BL, factures, avoirs, reçus, avances, dépenses, liaisons, transferts, déclarations magasin, inventaires, écritures, ajustements, clôtures et opérations de synchronisation. Les pièces générées automatiquement indiquent automate et utilisateur ou événement initiateur si connu ; ne pas attribuer une action automatique à une personne fictive.

Conserver l’identifiant stable de l’auteur et une identité affichable selon la politique retenue. Désactiver un compte ne doit pas effacer son attribution historique. Pour une pièce reprise sans auteur connu, afficher auteur d’origine inconnu et provenance de reprise ; ne pas prendre l’importateur pour l’auteur métier historique.

En synchronisation, conserver auteur, site et horodatage d’origine ; ajouter séparément date de réception et compte technique d’intégration. Ne pas remplacer l’auteur par l’utilisateur qui consulte, imprime ou synchronise. Distinguer date métier saisie et horodatages techniques ; les horloges locales peuvent être décalées.

Conserver une piste des changements significatifs avec ancienne/nouvelle valeur pertinente, action, auteur, date et motif. Protéger sa consultation et sa modification par des droits spécifiques ; éviter d’enregistrer inutilement des secrets ou données sensibles dans les journaux. Ne pas promettre une inviolabilité absolue : prévoir droits, sauvegardes et contrôles. Afficher l’auteur dans le document comme demandé ; la présence systématique sur toutes les impressions reste à valider.
