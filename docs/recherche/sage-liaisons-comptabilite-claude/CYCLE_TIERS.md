# Cycle du tiers à concevoir et à vérifier

Les étapes ci-dessous sont un protocole proposé pour l’ERP, pas la reproduction garantie d’un assistant Sage V12. Les repères documentaires sont F22, F29, F33 et F44–F45 ; les tests natifs manquants sont U04–U07 et U16.

## Création

1. Identifier la société juridique et le dossier technique avant d’afficher les défauts. Une agence, un dépôt et une société sont des dimensions distinctes.
2. Déterminer le rôle : client, fournisseur, salarié ou autre selon le modèle effectivement retenu. Un prospect requiert un cycle dédié, pas une écriture de créance immédiate.
3. Chercher un doublon par code dans le bon périmètre. Une ressemblance de nom doit seulement proposer une revue manuelle. Deux sociétés peuvent employer le même code pour des tiers différents.
4. Appliquer une codification explicite. Si deux canaux réservent le même code simultanément, un seul doit réussir dans l’ERP et le second doit recevoir un résultat explicable.
5. Choisir et valider le collectif, le payeur, la devise, les échéances, la catégorie comptable et les coordonnées nécessaires au flux. Distinguer les champs réellement obligatoires et les défauts d’interface.
6. Vérifier le droit de créer, puis enregistrer de manière atomique dans l’ERP. Une intégration distante peut rester en attente même après création locale : conserver deux états distincts.
7. Contrôler la visibilité et la cohérence depuis le module suivant. Ne pas créer un second tiers en réponse automatique à une simple absence dans une liste filtrée.

## Première facture

Copier dans la pièce ERP les choix métier nécessaires au calcul et à l’affectation comptable ; conserver leur version. Valider le document selon son cycle propre, puis préparer un lot d’écritures avec référence au tiers, à la société et à la source. Après transfert, vérifier le montant, le sens, le journal, la date, la devise et les échéances dans la cible.

## Modification

Un changement d’adresse ou de nom appelle une politique distincte d’un changement de code, de rôle, de collectif ou de payeur. Ne pas attribuer à Sage une permission de renommer ou changer de type par SQL : appliquer les opérations métier réellement supportées. Dans l’ERP, une réaffectation doit être une opération dédiée avec analyse d’impact, journal et traitement explicite des pièces ouvertes.

Changer les paramètres d’un tiers ne doit pas réécrire silencieusement les écritures déjà produites par l’ERP. Conserver les anciennes correspondances et les références de pièces. Si une correction comptable est nécessaire, utiliser un flux de correction traçable selon les règles validées du projet.

## Blocage et suppression

Un tiers en sommeil, interdit de vente, en dépassement d’encours ou inaccessible à un utilisateur représente plusieurs situations différentes. Tester chaque opération : recherche, nouvelle facture, validation, transfert, encaissement, consultation historique et export.

Avant toute suppression ERP, rechercher les références dans les documents, écritures, échéances, adresses, banques et connecteurs. Privilégier une désactivation lorsque l’historique impose la conservation. Ne jamais effacer automatiquement un tiers de Comptabilité parce qu’il a été retiré d’une liste commerciale.

## Fiche minimale de correspondance proposée

| Élément ERP | Rôle |
|---|---|
| company_id | Société juridique propriétaire |
| party_id | Identité interne stable |
| role | Rôle métier dans cette société |
| source_system + source_company + source_party_key | Identité externe et provenance |
| accounting_account_id | Collectif choisi et validé |
| payer_party_id | Tiers payeur distinct du destinataire |
| configuration_version | Paramètres appliqués au document |
| sync_status + last_error + last_success | État d’échange distinct de l’état métier |

Ces noms sont proposés pour l’ERP ; ils ne sont pas des colonnes Sage.
