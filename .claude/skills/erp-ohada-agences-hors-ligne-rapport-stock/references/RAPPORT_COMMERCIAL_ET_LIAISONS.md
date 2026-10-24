# Rapport commercial, commandes et liaisons

## Présentation obligatoire et compléments proposés

Préserver les quatre parties demandées : ventes du jour ; encaissements ; sorties/dépenses ; solde de caisse. Proposer un filtre date/agence/caisse et des sous-totaux par mode de règlement. La vue globale ne mélange pas plusieurs sociétés indépendantes.

### Ventes du jour

Présenter factures, retours et avoirs avec leurs dates métier et leurs montants, et distinguer comptant/en compte selon le vocabulaire retenu. Montrer séparément l’état de paiement non payé/partiel/payé. « En compte » et « à crédit » ne sont pas deux catégories disjointes tant que leur sens n’est pas confirmé.

Afficher le suivi des BC dans une sous-rubrique dédiée : BC créés, payés non livrés, partiellement livrés, restant à livrer et transformés. Ne pas additionner la valeur d’un BC et sa facture comme deux ventes. Conserver les liens pour passer de chaque total aux documents sources.

La base de présentation HT/TTC, la gestion des dates d’annulation et les détails de caisse sont ouverts. Définir clairement l’intitulé de chaque total avant de coder une formule.

### Encaissements

Séparer règlements des ventes du jour, règlements d’anciennes créances, avances sur BC et versements hors-recettes pour d’autres agences. Ventiler espèces, banque, Mobile Money et autres moyens réellement configurés. Chaque reçu a une référence unique et un lien vers son bénéficiaire.

Complément U4 : un reçu de règlement de créance doit être rattaché à une facture. Par défaut, limiter chaque reçu de créance à une facture ; une facture peut recevoir plusieurs reçus partiels dans la proposition de gestion. Un versement couvrant plusieurs factures nécessite un arbitrage décrit dans REGLEMENTS_CREDIT_ET_TRACABILITE.md ; ne pas imposer silencieusement un reçu multi-factures. Une facture payée n’est pas un second reçu. Le passage d’une avance à une facture modifie l’affectation, pas le montant encaissé à nouveau.

### Sorties et dépenses

Séparer dépenses propres, sorties pour compte d’autres agences, remboursements clients, décaissements fournisseurs, transferts de caisse et versements en banque. Une sortie monétaire n’est pas automatiquement une charge de l’agence qui paie. Conserver justificatif, nature, agence bénéficiaire et personne ayant validé.

### Caisse

Solde théorique espèces = solde initial + entrées espèces propres + avances espèces + hors-recettes espèces + autres entrées espèces − toutes sorties espèces. Ne pas omettre les dépenses pour autres agences, remboursements, remises en banque ou transferts sortants.

Conserver le solde physique compté et calculer écart = espèces comptées − solde théorique. Un écart ne crée pas une écriture d’ajustement sans procédure et autorisation. Définir clôture par caisse, heure limite, date métier et réouverture auditée.

Exemple pédagogique FCFA : initial 50 000 ; encaissements propres 200 000 ; avances 50 000 ; hors-recettes 100 000 ; dépenses propres 30 000 ; dépenses pour autre agence 20 000 ; remise banque 150 000. Solde espèces théorique =200 000. Un paiement Mobile Money distinct de 40 000 apparaît dans son total, pas en espèces.

## Versement pour une autre agence

Exemple demandé : client de Bertoua, versement de 100 000 FCFA à Garoua-Boulaï.

1. Créer un reçu dans l’agence d’encaissement, avec caisse/mode de paiement réel, client identifié et agence propriétaire de la créance.
2. Présenter les 100 000 dans les encaissements hors-recettes de Garoua-Boulaï ; augmenter ses espèces si le paiement est en espèces ; ne créer aucune vente propre.
3. Créer l’opération de liaison avec identifiant stable partagé et pièces de chaque côté. Paramétrer les comptes sur le plan validé, sans imposer un numéro.
4. Transmettre à Bertoua dès qu’un canal est disponible ; afficher en attente tant que l’opération n’est pas intégrée/affectée.
5. Affecter une seule fois les 100 000 au compte client de Bertoua ; conserver reçu d’origine, rapprochement et écritures locales éventuelles sans nouvel encaissement physique à Bertoua.
6. Au niveau société, conserver un encaissement externe de 100 000 et sa réduction de créance, pas deux encaissements. Neutraliser les doubles représentations internes appropriées lors du regroupement, pas le paiement externe réel.

Ne pas considérer cette description fonctionnelle comme un schéma d’écritures complet. Définir comptes de liaison réciproques, dates et comptes d’attente éventuels avec le paramétrage comptable applicable. Préserver les états locaux et la traçabilité des écritures déjà validées.

Pour un paiement reçu hors ligne sans client ou facture connus dans le référentiel local, conserver code et éléments de correspondance contrôlés. Le complément U4 impose une facture au reçu de créance définitif : proposer un enregistrement du versement et un justificatif provisoire en attente de vérification, à arbitrer. Ne pas prétendre la créance déjà soldée, créer automatiquement un doublon client à partir d’un nom ressemblant ni lettrer arbitrairement une facture.

Pour une dépense pour une autre agence, appliquer la même séparation exécution/bénéficiaire : baisse de la caisse qui paie, hors des dépenses propres selon classement, liaison et pièce à recevoir côté bénéficiaire. Ne pas créer une seconde sortie physique au destinataire.

Prévoir annulation motivée, correction, justificatifs et rapprochement des deux sens. Distinguer états de transmission et états de rapprochement métier ; un accusé technique ne prouve pas le lettrage du client.

## Commande, avance, livraison et facture

Exigence : commande créée et livrée le même jour → transformation automatique en facture le même jour ; sans livraison, transformation ultérieure. Le détail de validation reste à préciser. Ne pas transformer toutes les commandes à la clôture simplement parce qu’elles sont datées du jour.

Proposition : déclencher après confirmation d’une livraison effective ; conserver BC et BL et générer la facture liée, avec le statut de validation autorisé par les règles du dossier. L’impression du BL ne prouve pas à elle seule la livraison physique. Le paiement est indépendant du déclenchement de la sortie physique.

Exemple pédagogique : J1 BC de 100 000 et paiement de 100 000, sans retrait. Rapport J1 : BC payé non livré 100 000, encaissement 100 000, pas de facture de vente finale de marchandises dans ce scénario. J2 livraison et facture 100 000, avance affectée : vente facturée 100 000, nouvel encaissement 0, solde client final 0. Les éventuelles obligations de document fiscal d’acompte sont à vérifier séparément ; ce scénario ne les écarte pas.

Proposition pour livraison partielle : BC 10 cartons, sortie 4, facture des 4 si la politique de facturation suit le livré, reste 6 à livrer. Ne pas clôturer le BC ou facturer les 10 sans motif. La règle partielle, l’affectation des avances, les frais, les retours et remboursements sont à arbitrer.

## Clôtures et rapports globaux

Un rapport local doit fonctionner sans Internet. Indiquer la version de calcul et les pièces incluses. Préserver un historique des clôtures et des réouvertures ; une synchronisation tardive ne doit pas modifier silencieusement un rapport clos.

Au siège, distinguer date métier de la pièce et date de réception. Signaler les agences manquantes, les événements rejetés et les liaisons non rapprochées. Ne pas déclarer un bilan global définitif tant que les données nécessaires et contrôles de liaisons ne sont pas complets.
