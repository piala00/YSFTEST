# Spécification proposée : échanges et vue regroupée

## Sommaire

1. Périmètre et architecture
2. Identités et propriétaires
3. Format de lot
4. Authentification et confidentialité
5. Import, rejouabilité et accusés
6. Correspondances et liaisons
7. Regroupement et transit
8. Reprise, déploiement et recette

## 1. Périmètre et architecture

Une société, plusieurs agences avec serveur local ; le logiciel doit continuer localement sans connexion centrale. Proposer un central recevant des lots et produisant une lecture regroupée. Ne pas exiger de VPN permanent ni ouvrir les serveurs des agences sur Internet. Préférer un transfert sortant HTTPS lorsque disponible ; exporter/importer le même format de lot via un canal manuel approuvé si nécessaire. La clé USB n’est pas imposée. Aucun transport n’est encore arbitré par l’utilisateur.

Commencer par collecte centrale et accusés de réception. Ajouter ensuite distribution de référentiels et des versements pour compte d’autres agences selon les droits. Ne pas présenter une collecte seule comme une synchronisation complète bidirectionnelle.

Le central conserve données d’origine en lecture, journal d’intégration et projections de reporting. Ne pas appeler Document.valider, Reglement.enregistrer ou les fonctions de stock locales pour chaque pièce importée au central : leurs effets créeraient encore mouvements et écritures. Soit les faits comptables/mouvements déjà produits sont reçus et projetés, soit un moteur central les produit selon un contrat exclusif ; ne jamais cumuler les deux stratégies. Proposition retenue ici : recevoir les faits locaux déjà produits, sans les reproduire.

## 2. Identités et propriétaires

Attribuer société_uuid identique à tous les sites de cette société ; site_uuid unique et stable ; objet_uuid global à chaque objet ; revision positive croissante par objet. Préserver aussi type, identifiant primaire local pour diagnostic et référence imprimable. Un id entier 12 ou une référence BL2026-00001 n’est pas globalement unique.

À la migration, créer les identifiants une seule fois, conserver une table de correspondance et inclure ces identifiants dans les sauvegardes. Les acteurs/auteurs doivent avoir une identité d’origine stable et un libellé affichable. Ne pas attribuer au compte technique central la création métier.

Le site d’origine est propriétaire d’écriture de ses pièces ; modifications permises en brouillon et événements de correction/contrepassation après validation selon le dossier. Le central ne réécrit pas une facture validée distante. Les référentiels peuvent avoir un propriétaire central et des demandes de création locales, à arbitrer.

## 3. Format de lot

Proposer une archive applicative de taille bornée contenant manifest.json, events.jsonl et auth.json ; pièces jointes optionnelles déclarées avec taille et empreinte dans une liste explicite. Refuser chemins absolus, traversée, liens symboliques, fichiers imprévus et décompression dépassant les limites. Ne jamais importer SQL, pickle ou sauvegarde brute via ce protocole.

manifest.json en UTF-8 : protocol=erp-ohada-agency-exchange, schema_version=1, package_uuid, societe_uuid, source_site_uuid, destination, created_at_utc, business_timezone, stream_uuid, sequence_from, sequence_to, event_count et liste des fichiers avec octets/SHA256. Les seuils de taille, nombre d’événements et conservation sont paramétrables et restent à fixer selon volume.

events.jsonl : un objet JSON complet par ligne UTF-8. Chaque événement porte event_uuid, objet_uuid, type, revision, sequence, opération, date métier, date de validation/émission, auteur/site d’origine, dépendances et payload versionné. Les décimaux sont des chaînes non exponentielles, dates au format ISO, horodatages avec fuseau/UTC, null distingué du vide et zéro. Refuser NaN/Infinity et les dates ou montants incohérents.

Les types portent des contrats distincts : client/compte local, article/présentation, document/lignes/liens, versement, affectation, liaison, mouvement stock, écriture/lignes, pointage, correction/contrepassation et photographie de clôture si livrée. Les données d’annulation sont de nouveaux événements traçables ; ne pas supprimer en cascade les faits historiques reçus.

Utiliser un journal d’envoi transactionnel local : la création/validation métier et l’événement sortant sont engagés ensemble. Si l’exportation est d’abord réalisée par extraction périodique, utiliser un curseur fiable et un journal des révisions/suppressions ; une simple comparaison de dates de modification ne garantit pas l’exhaustivité.

## 4. Authentification et confidentialité

Un SHA256 protège une comparaison d’intégrité ; il n’authentifie pas l’émetteur. Proposition de démarrage : clé secrète distincte par site et identifiant de clé, HMAC-SHA256 sur les octets exacts de manifest.json avec préfixe de domaine constant ; manifest inclut les empreintes de tous les fichiers de données. auth.json porte algorithme, key_id et MAC détaché. Exemple de préfixe versionné : ERP-OHADA-EXCHANGE-V1 suivi d’un octet nul. Conserver exactement les octets signés, pas une réécriture JSON à l’arrivée.

Vérifier la correspondance clé/site/société/destination, comparer les MAC avec une primitive adaptée, prévoir rotation/révocation et journaliser le résultat. Ne mettre aucune clé réelle dans le Skill, les fichiers de démonstration ou le dépôt. HMAC est un MAC symétrique : il ne fournit ni signature publique ni chiffrement. Si le besoin exige des signatures asymétriques, définir un contrat de clés publiques séparé.

HTTPS protège le transport connecté ; pour dépôt manuel ou conservation de lots contenant des données sensibles, utiliser un conteneur chiffré approuvé avec gestion des clés. Ne pas appeler « chiffré » un ZIP simplement compressé ou authentifié. Limiter les destinataires et les données reçues par chaque agence.

## 5. Import, rejouabilité et accusés

1. Déposer le lot en zone de réception, sans effet métier immédiat.
2. Vérifier bornes, format, schéma accepté, clé/site/société/destination, MAC, empreintes et nombres d’événements.
3. Détecter package_uuid déjà reçu : même empreinte → retourner l’accusé précédent ; empreinte différente → conflit, sans écrasement.
4. Enregistrer les événements dans une inbox. Unicité durable (société, site d’origine, event_uuid) et (société, origine, type, objet_uuid, revision). Même identité et contenu différent → conflit ; ne pas appliquer la dernière arrivée.
5. Vérifier ordre, dépendances, unités, comptes, devise, auteurs et correspondances. Mettre en attente ce qui dépend d’une facture/client non reçu. Ne pas créer un client approximatif ni affecter arbitrairement un reçu.
6. Dans une transaction bornée, intégrer l’agrégat et ses effets de projection une seule fois, puis enregistrer le statut et la version intégrée. Les contraintes d’unicité doivent aussi résister à deux imports concurrents. Les échecs ne laissent pas une moitié d’écriture ou de règlement.
7. Produire un accusé durable avec état reçu, validé-format, intégré, doublon, attente-dépendance ou rejet/conflit par événement. Reprendre la même procédure après interruption. Ne jamais acquitter comme intégré avant le commit durable.

L’acquittement technique n’est pas le rapprochement comptable de liaison ni l’affectation client. Conserver les deux statuts. Une séquence reçue avec trou ne fait pas progresser le curseur contigu au-delà du manque ; les autres événements peuvent rester en attente. Définir le lot complet comme une plage de flux sans filtre arbitraire afin de distinguer manque et événement volontairement absent.

Les notifications/retransmissions sont déclenchées après commit. Un crash après commit mais avant réception de l’accusé doit produire au rejeu un doublon reconnu, pas une seconde opération. La documentation Django T01 décrit atomic ; l’idempotence métier dépend aussi des identifiants, contraintes et statuts décrits ici.

## 6. Correspondances clients, comptes et liaisons

Conserver identité globale d’une personne/entreprise et compte client local par agence : agence propriétaire, code local, éventuel payeur et comptes comptables. Une personne peut avoir plusieurs comptes d’agence sans créer une créance unique indistincte. Valider les rapprochements de référentiel ; ne pas fusionner sur le seul nom.

Comptes : garder numéros locaux historiques et table de correspondance vers comptes de regroupement validés. Ne pas renuméroter les écritures validées pour satisfaire l’import. Le compte 185NN créé dans le code de Claude est un fait d’implémentation, pas une certification ici de son adéquation à chaque dossier SYSCOHADA. Paramétrer les paires de liaison réciproques et la nature des contreparties.

Versement hors-recettes : émettre un identifiant de paiement physique stable côté encaisseur, avec agence bénéficiaire, client/compte distant, facture si connue et référence du reçu. Le traitement bénéficiaire porte le même identifiant d’opération source et crée la réduction de créance sans seconde entrée d’espèces. Le central conserve une seule transaction externe et rapproche les deux représentations locales.

Le logiciel actuel prévoit une saisie manuelle du reçu côté bénéficiaire avec agence+n° reçu unique. Lors du premier import automatique, chercher ces correspondances de reprise et les faire confirmer pour les cas ambigus avant de créer quoi que ce soit. Ne pas déclarer idempotent un import qui double les opérations déjà saisies manuellement.

Si facture distante inconnue : tracer le paiement reçu mais conserver l’affectation en attente et la preuve provisoire selon arbitrage D19. Ne pas inventer une facture. Pour dépenses pour autre agence, même distinction payeur physique/bénéficiaire ; pas de second décaissement au destinataire.

## 7. Ce qui reste local et ce qui se regroupe

Local : saisie/validation, documents originaux, caisse réelle, créances locales, stock physique, déclarations du fichiste et droits d’exécution. Central : copies d’origine, correspondances, fraicheur, contrôles de liaison, projections de stock/créances/analyses et états de regroupement selon périmètre validé. Diffuser aux autres agences seulement référentiels et pièces nécessaires à leurs droits.

Séparer faits de détail et photographies. Les stocks se calculent à partir d’une ouverture et des mouvements reçus ; un instantané de stock sert à contrôler ou à initialiser une reprise, jamais à s’ajouter aux mêmes mouvements. Même règle pour créances, soldes comptables et rapports de caisse. Les lignes de facture, règlement et écritures représentent des aspects d’une opération ; ne pas les sommer comme trois encaissements.

Transfert physique : identifiant de transfert stable et événements expédition/réception avec quantités partielles ; tenir l’état origine/transit/destination. Exemple de contrôle proposé : 10 expédiés, 4 reçus →6 en transit, non 10 encore à l’origine plus 4 à destination. Les mouvements locaux qui composent ce transfert sont liés à l’opération et ne sont pas comptés une deuxième fois par un moteur central de transfert. Cas d’une réception reçue avant l’expédition : attendre/réconcilier, pas inventer une ouverture de stock.

Rapports globaux : afficher sites inclus, date métier de couverture, dernière réception, trous de séquence et liaisons non rapprochées. Distinguer une photographie à date, la situation actuelle et la date de réception. Pour une seule société, définir regroupement et neutralisations des liaisons internes sans effacer les encaissements externes. Les bilans d’agence nécessitent aussi affectation des charges, banques, immobilisations et dettes ; l’addition des ventes n’est pas un bilan consolidé.

## 8. Reprise, déploiement et recette

Première reprise : inventaire des agences et versions, attribution des identités, correspondances validées, photographie d’ouverture datée avec frontière claire, puis événements postérieurs. Comparer stocks, soldes clients, trésoreries et liaisons entre local et central avant activation. Les objets historiques repris ne doivent pas déclencher de nouveaux mouvements.

Sauvegarder données, identités, outbox/inbox, curseurs et décisions ensemble. Une restauration ne doit pas créer un nouveau site pour échapper aux doublons : réconcilier la séquence centrale et les objets, retrouver événements manquants depuis les sauvegardes et signaler la perte éventuelle. Tester restauration après acquittement et restauration avant acquittement. Un réimport ne recrée pas des règlements.

Piloter d’abord deux copies d’agence fictives : collecte, rejeu, rupture d’ordre, coupure, rapprochement de liaison et paiements. Ajouter ensuite les agences restantes. La recette proposée est dans RECETTE_ECHANGES.csv ; elle n’a pas été exécutée ici car le moteur n’existe pas dans le ZIP examiné.
