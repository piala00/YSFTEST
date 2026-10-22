# Contrat de liaison proposé pour l’ERP OHADA

Ce document est une conception indépendante. Il ne décrit pas un SDK Sage certifié et ne donne aucune autorisation de modifier les bases Sage. Les identifiants et états ci-dessous sont des propositions à adapter au code existant en préservant ses fonctionnalités.

## Identité et configuration

Séparer `company_id` (entité juridique), `site_id` (agence), `connector_id` (liaison), `source_company_key` (dossier distant), `database_locator` (adresse technique), `legal_name` (raison sociale) et `display_name` (nom affiché). Un renommage de libellé ne doit pas modifier automatiquement le destinataire des écritures.

Une liaison comporte : produit et version source/cible, canal, sens, objets autorisés, déclencheur, compte d’exécution, référence vers le secret, correspondances de codes, période permise, date de dernière vérification et état d’activation. La configuration peut être BROUILLON, VERIFIEE, ACTIVE, SUSPENDUE ou EN_ERREUR. Ces états ne sont pas des états Sage.

Avant activation, afficher la société réellement résolue à chaque extrémité. Après modification de cible ou de correspondance, suspendre les nouveaux transferts jusqu’à un nouveau contrôle ; ne pas rejouer les anciens lots vers le nouveau dossier.

## Droits et responsabilités

Proposer des permissions séparées : voir la liaison, modifier la configuration, tester la connexion, créer un tiers, modifier un tiers, transformer un prospect, valider un document, préparer un lot, comptabiliser, exporter, approuver un paiement, transmettre à la banque et consulter les journaux.

Chaque permission a un périmètre société et éventuellement agence/journal. Vérifier l’autorisation dans le service serveur, y compris lors d’un appel direct ou d’une tâche différée. Tracer l’utilisateur demandeur, l’approbateur si nécessaire et l’identité technique exécutante. Ne pas exposer les salaires dans un flux commercial par simple partage de référentiel.

## Référentiels

Définir un propriétaire et un sens de mise à jour par champ lorsque deux systèmes possèdent chacun leur copie. Distinguer valeurs par défaut, valeurs appliquées au document et données historiques. Si les modules de l’ERP utilisent une même fiche, leur donner une vue commune contrôlée plutôt que simuler une synchronisation entre copies inutiles.

Toute correspondance externe est bornée par système et société. Une collision reçoit un conflit explicite ; le dernier horodatage ne suffit pas à décider qu’un nom ou une banque doit être écrasé. Un changement de coordonnées bancaires peut nécessiter une validation dédiée selon les choix de gouvernance du projet.

## Production comptable

Proposition de chaîne : document brouillon → document validé → lot préparé → contrôles → comptabilisation confirmée. L’état d’export et l’état d’intégration distante sont distincts. Les paiements et le lettrage ont leurs propres événements ; une facture « réglée » commercialement n’est pas une preuve suffisante de banque comptabilisée.

Le lot conserve : société, identifiant source stable, nature d’événement, version du document, période, devise, lignes débit/crédit, références de tiers et d’échéances, paramètres appliqués, hash du contenu et trace de traitement. Les montants utilisent un type décimal, jamais des nombres flottants binaires pour la comptabilité.

Avant émission, vérifier l’équilibre, les comptes et tiers cibles, la période, le journal, les règles de taxes/arrondis, la devise et les autorisations. Un compte absent entraîne une anomalie à résoudre, pas la création automatique d’un compte arbitraire.

## Doublons, reprise et erreurs

Construire une clé d’idempotence à partir de la société, du système source, de l’identifiant de document, de la nature d’événement et de sa version. Enregistrer la réservation de cette clé de façon transactionnelle dans l’ERP. Si le contenu change sous une même clé, retourner un conflit ; ne pas l’accepter comme un rejeu identique.

Pour un transfert distant, prévoir une boîte d’envoi durable. Une interruption entre acceptation distante et confirmation locale impose une vérification de réception avant relance. L’idempotence de la cible Sage n’étant pas établie par ce dossier, ne pas promettre « exactement une fois » à partir d’un simple retry HTTP ou d’une réimportation de fichier.

Journaliser par ligne et par lot : contrôlé, rejeté, accepté, inconnu après interruption. Une réussite partielle n’autorise pas à marquer toute la facture comme transférée sans rapprochement. Conserver le fichier ou la référence de lot, les totaux et les messages sans secret.

## Corrections et fermeture de période

Ne pas effacer une écriture comptabilisée afin de refaire une liaison. Prévoir les opérations métier de correction autorisées, une référence à l’événement corrigé et une piste d’audit. Avant clôture, rapprocher chaque flux attendu avec les lots acceptés et traiter les éléments en attente ou d’état inconnu.

Dans l’ERP, le contrôle des flux doit comparer : nombre de documents, HT, taxes, TTC, débits/crédits, soldes tiers, échéances, règlements et résidu. Une balance équilibrée seule ne garantit pas l’absence de facture oubliée ou doublonnée.

## Écrans utiles

Prévoir un écran Société, un écran Liaisons, une fiche Tiers, un paramétrage Comptabilisation, une matrice d’autorisations et un Journal des échanges. Dans le parcours métier, montrer le nom de la société cible et le statut compréhensible de l’opération ; réserver noms de tables, numéros de versions et diagnostics détaillés aux écrans d’administration.

Ne supprimer aucun menu ou calcul existant pour installer ce modèle. Claude doit d’abord dresser la correspondance avec les composants déjà présents, puis proposer des modifications limitées et vérifiables.
