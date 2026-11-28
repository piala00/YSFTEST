# Complément U5 — fenêtres et règlements, version 2

## Besoin confirmé et priorité

Cette clarification utilisateur du 24 octobre 2026 prévaut sur les anciennes règles E40/P22, D16/D19 et les attentes R29/R31. Elle ajoute deux comportements indépendants : fenêtres de documents persistantes et saisie de règlement guidée par le client. L’ERP n’a pas encore été modifié dans cette livraison documentaire.

## Fenêtres indépendantes

Depuis une facture, « ajouter/saisir un règlement » ouvre un autre formulaire dans une nouvelle fenêtre interne. La facture reste ouverte ; l’utilisateur peut la laisser derrière, la remettre devant ou la fermer volontairement. Ce comportement s’applique aux autres documents ouverts depuis un document, pas seulement au règlement.

Permettre plusieurs documents et formulaires simultanément. Proposer fenêtres déplaçables/redimensionnables/réductibles si le gestionnaire existant le prévoit ; conserver l’ordre de superposition et un accès aux fenêtres ouvertes. Ne pas remplacer ce besoin par un historique retour arrière, un accordéon qui détruit le formulaire précédent ou une boîte modale bloquant toute navigation vers la facture.

L’indépendance des fenêtres n’autorise pas à dépasser les droits métier ni à valider une facture contradictoire. Aucun nombre illimité de fenêtres n’est garanti indépendamment des ressources ; ne pas imposer une fermeture automatique des autres documents pour ouvrir le suivant.

Propositions techniques : une identité par fenêtre et contexte, état de formulaire isolé, requêtes associées au bon document, fermeture individuelle, protection de la saisie non enregistrée. Après validation d’un règlement, notifier les autres vues de la facture et actualiser les soldes sans écraser un brouillon. Ces mécanismes sont à adapter au gestionnaire existant, pas une demande de réécriture du bureau.

Dans la transmission précédente, examiner notamment static/js/fenetres.js, les liens et actions du détail facture, les redirections après saisie et les formulaires intégrés. Le symptôme peut venir d’une navigation dans la fenêtre source ; cette cause est une hypothèse à vérifier, pas un diagnostic reproduit ici. Tester le vrai bureau web et le client bureau concerné, pas uniquement le simulateur.

## Parcours de saisie confirmé

1. Ouvrir Traitement → gestion de règlement → saisie de règlement client. Ce sont les mots de l’utilisateur ; adapter les libellés de navigation à l’ERP après validation, sans prétendre qu’ils reproduisent exactement Sage.
2. Choisir le client.
3. Charger automatiquement ses factures non soldées.
4. Choisir une ou plusieurs factures et les montants d’affectation proposés par la conception.
5. Enregistrer le règlement. Si aucune facture n’est disponible, permettre un règlement en attente de facture pour un rattachement ultérieur.

Depuis une facture, proposer le client et la facture d’origine comme contexte initial sans supprimer le parcours ni fermer la facture. Ce préremplissage est une proposition ergonomique, pas une interdiction de choisir une autre facture autorisée.

Le règlement en attente est enregistré et traçable. Il ne doit pas être refusé au seul motif facture absente, ni être réduit à un formulaire brouillon impossible à enregistrer. Il conserve un montant non affecté ; le statut « en attente de rattachement » ne signifie pas que l’argent n’a pas été reçu.

## Modèle et contrôles proposés

Un règlement décrit le versement réel. Des affectations distinctes relient ce règlement à zéro, une ou plusieurs factures. Montant reçu = somme affectée + non affecté. Ne pas créer une entrée de caisse par facture sélectionnée. Ne pas affecter automatiquement par FIFO sans choix explicite alors que l’utilisateur souhaite sélectionner les factures.

Exemple : versement 100000, factures sélectionnées 60000 et 40000 →un règlement, deux affectations et un seul encaissement. Sans facture : 100000 en attente ; après création et rattachement d’une facture, nouvel encaissement 0. Le traitement d’un reliquat volontaire alors que des factures existent reste à préciser.

Conserver avance sur BC lorsqu’une commande est identifiée ; ne pas imposer un BC fictif à tout règlement en attente. Préserver client/payeur autorisé, agence d’encaissement et bénéficiaire, mode/trésorerie, preuve et auteur ; vérifier les montants disponibles à la validation et les conflits hors ligne.

## En-tête et présentation à compléter

U6 apporte deux captures de la fenêtre Sage des règlements : lire FONCTIONNEMENT_FENETRES_U6.md. Elles documentent le modèle visuel, sans fixer les adaptations de l’en-tête ERP ni montrer l’écran d’affectation des factures. Conserver les champs ERP, leur ordre et la présentation imprimée à préciser. Les colonnes et contrôles suggérés dans les autres références restent des propositions. Ne pas transformer la feuille à venir en obligation d’utiliser une interface Sage identique.

## Transmission à Claude

Faire remplacer la logique facture obligatoire et le lien unique Reglement.facture par le modèle d’affectations adapté, en conservant les données historiques et les références existantes. Prévoir une migration explicite des anciens reçus liés à une seule facture ; ne pas les dupliquer. Actualiser les tests de refus sans facture pour couvrir l’enregistrement en attente, puis les affectations ultérieures. Conserver les contrôles de mauvais client, suraffectation, double encaissement, droits et auteurs.

Le retour de revue précédent prouve le comportement de l’ancienne copie ; il ne constitue plus une cible métier valide pour les tests qui interdisaient tous les règlements sans facture. Les sept anomalies reproduites restent séparées de cette nouvelle demande d’évolution.
