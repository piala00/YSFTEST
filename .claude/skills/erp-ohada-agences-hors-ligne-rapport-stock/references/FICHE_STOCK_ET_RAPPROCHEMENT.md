# Fiche de stock magasin et rapprochement

## Besoin confirmé

Le fichiste tient aujourd’hui des fiches papier à partir des BL remis par le magasin. L’utilisateur demande un espace numérique intégré : saisie du numéro du BL, chargement des articles, quantités attendues invisibles, quantités saisies manuellement par le fichiste, comparaison immédiate après validation.

Ne pas préremplir les quantités ni proposer une action « reprendre les quantités du BL » à ce rôle. Ne pas présenter une case initialisée à zéro comme une quantité effectivement déclarée.

## Circuit proposé

1. Identifier agence, dépôt, fiche et utilisateur autorisé.
2. Rechercher ou scanner le BL local validé. Contrôler document annulé, dépôt, société et éventuelle saisie antérieure.
3. Charger référence, date, articles, unités et, si pertinent, lot/conditionnement. Ne transmettre ni attendu, ni prix, ni total, ni stock théorique permettant de déduire les quantités. Auditer API, impressions, exports et autres écrans du rôle.
4. Laisser le fichiste saisir les quantités constatées sur son document physique. Distinguer non saisi et zéro confirmé. Autoriser la sauvegarde en brouillon sans marquer le BL rapproché.
5. Demander sa validation et figer une version de la déclaration avec date et auteur.
6. Comparer côté serveur les lignes, unités et quantités converties au même référentiel. Calculer écart = déclaré − attendu. La référence visée est la livraison/sortie effective, pas la quantité totale commandée.
7. Présenter les écarts au contrôleur autorisé et créer une anomalie documentée. Ne pas modifier automatiquement le BL, le stock ou la facture.
8. Conserver la décision, les pièces, le motif et les corrections. Une correction ne supprime pas la déclaration originale.

Définir qui voit le résultat après soumission. Par défaut proposé, le fichiste reçoit un accusé d’enregistrement ; le contrôleur voit attendu/déclaré/écart. Ne pas permettre des essais successifs « plus/moins » pour découvrir l’attendu sans trace. Le droit de corriger et l’éventuelle visibilité après validation restent à arbitrer.

## Deux registres et un stock opérationnel

Registre de gestion : sorties issues des documents validés et autres mouvements métier. Registre indépendant magasin : déclarations du fichiste. Le second n’est pas une copie automatique du premier.

Ne pas déduire à nouveau le stock opérationnel lors de la saisie du fichiste. Si le BL a déjà sorti 20 cartons, la déclaration de 20 cartons constate une concordance ; elle ne sort pas 20 cartons supplémentaires. Si le fichiste déclare 19, créer un écart −1 à instruire, pas un ajustement silencieux.

Une fiche indépendante complète calcule son solde à partir d’une ouverture contrôlée et de ses entrées/sorties déclarées. Définir le stock de départ par un inventaire ou une reprise validée ; ne pas inventer un historique manquant. Ne pas comparer deux soldes construits sur des dates de départ différentes.

Pour parler de rapprochement de stock complet, couvrir réceptions fournisseurs, retours clients/fournisseurs, transferts, pertes, régularisations autorisées et tous dépôts concernés. Sinon nommer le périmètre « rapprochement des sorties BL ».

## Cas et alertes

- BL sans déclaration après le délai choisi : alerte à saisir, pas écart zéro.
- Déclaration sans pièce connue : attente ou exception autorisée, sans création arbitraire de BL.
- Écart par article ou unité : conserver brut et conversion ; distinguer 1 carton de 1 litre.
- BL partiel : rattacher chaque déclaration à l’événement de sortie et à son solde pertinent ; ne pas bloquer une seconde livraison légitime comme doublon.
- Article supplémentaire réellement livré : permettre un signalement distinct contrôlé ; ne pas obliger à le cacher ou modifier automatiquement le document commercial.
- Modification ou annulation du BL après déclaration : conserver la version rapprochée, invalider le résultat courant si nécessaire et déclencher un contrôle.
- Retour : créer le mouvement inverse lié selon son circuit, sans changer la déclaration de sortie originale.
- Livraison réelle à une autre date que le BL : préserver les deux dates et instruire le décalage.

Proposer les états attendue, brouillon, déclarée conforme, déclarée en écart, en investigation, résolue, annulée, avec audit. Les libellés précis ne sont pas imposés par l’utilisateur.

## Ce que le rapprochement prouve

Une concordance compare les quantités de gestion et celles saisies depuis les justificatifs du magasin. Elle ne prouve pas automatiquement ce qui est physiquement présent sur les rayons. Préserver inventaires réels et contrôles sur marchandises non documentées, casse ou pertes. Le système accélère le contrôle ; il ne permet pas de détecter toute fraude par la seule concordance des BL.

## Fonctionnement local et droits

Exécuter saisie et comparaison sur le serveur local de l’agence, sans Internet. La direction reçoit les déclarations, anomalies et décisions quand elles sont synchronisées. Ne pas rendre le résultat local dépendant de l’accusé central.

Séparer les rôles commercial, magasinier, fichiste, contrôleur, comptable et administrateur. Un rôle cumulant d’autres autorisations peut connaître l’attendu ailleurs ; vérifier le périmètre effectif plutôt que prétendre garantir l’aveugle en masquant une colonne. L’accès aux quantités et aux pièces financières est explicite et audité.
