# Paramétrage et fonctionnement hors ligne

## Portée

Exigences E01–E12 ; propositions P01–P09 et P20–P21. Aucun moteur de base ni outil de synchronisation n’est imposé par l’utilisateur. Auditer l’ERP Django existant avant de sélectionner les composants. Ne pas remplacer une application complète par un prototype isolé.

## Société et organisation

Prévoir plusieurs sociétés clientes isolées. Pour le cas détaillé, créer une société avec plusieurs agences autonomes ; conserver agence d’origine de la créance et agence d’exécution de chaque mouvement. Ne pas déduire une identité juridique du seul nom d’agence.

Proposer la hiérarchie société → agences → dépôts/boutiques → caisses, avec rattachements configurables. Une boutique peut être un point de vente d’une agence, pas nécessairement une nouvelle agence comptable. Préserver la possibilité d’une structure monoposte simple.

Prévoir un assistant : identité/pays/devise/exercice ; activités ; agences et lieux ; gros/détail ; unités/conditionnements ; facturation/crédit/avances ; comptabilité et reporting ; utilisateurs ; mode local/synchronisation. Les profils boutique, grossiste ou multisite préremplissent des options, sans créer trois logiciels incompatibles ni déterminer à eux seuls le régime fiscal.

Conserver les options après démarrage, avec procédures contrôlées pour changements structurels : unité de référence déjà mouvementée, exercice, numérotation, agence de rattachement ou schéma comptable. Ajouter un établissement ne doit pas réécrire l’historique.

## Gros, détail, conditionnements et tarifs

Configurer par article l’unité de stock de référence, les unités d’achat/vente, leurs facteurs de conversion exacts, précision et règles d’arrondi. Conserver unité et facteur effectivement appliqués sur chaque ligne. Séparer coût, prix de vente et conversion physique.

Exemple proposé, avec hypothèse de portion de 500 ml à confirmer : huile référencée en litres ; carton =15 L ; bidon =5 L ; portion =0,5 L. Deux cartons donnent 30 L. Sortie de 1 carton, 3 L et deux portions de 0,5 L : 19 L sortis, 11 L restants. Permettre une lecture équivalente en unité de référence et en présentations lorsque la décomposition est pertinente.

Ne pas convertir kg et litres sans règle propre au produit, documentée. Ne pas multiplier aveuglément le prix du litre pour déterminer le prix d’un carton : les tarifs gros, demi-gros, détail, client et quantités peuvent être différents.

Distinguer vente en vrac d’un même produit et références emballées/scellées distinctes. Si une bouteille scellée et un bidon ont leurs propres stocks, codes-barres, lots ou emballages, utiliser des articles ou variantes liés et un déconditionnement/reconditionnement explicite. Ne pas créer des bouteilles disponibles simplement parce qu’un bidon existe. Suivre les pertes autorisées et leur justification. L’arbitrage vrac/emballé est ouvert par article.

## Installation et synchronisation proposées

- Monoposte : service applicatif et données locaux, utilisables sans Internet.
- Plusieurs postes dans une agence : serveur local et réseau local ; une coupure d’Internet n’empêche pas le travail tant que le serveur et le réseau local fonctionnent.
- Plusieurs agences : installations locales autonomes et serveur central de collecte/synchronisation, quand une liaison est disponible.
- Mode en ligne seul : option possible pour une société qui le choisit, sans supprimer le mode autonome du produit.

Une application Django distante sur Render n’est pas rendue autonome par le simple cache du navigateur. La synchronisation exige une conception explicite ; une réplication brute des bases et une fusion de sauvegardes ne sont pas un protocole métier.

Proposer un journal d’événements avec identifiant global stable, société, site d’origine, type de pièce, version, date métier et horodatage de réception. Préserver les références imprimables par agence. Transmettre par lots, vérifier l’identité de la société et l’autorisation du site, enregistrer l’intégration et acquitter durablement. Reprendre après interruption sans doublon ; l’identifiant imprimé seul ne garantit pas l’unicité mondiale.

La même opération a un seul propriétaire d’écriture à un instant donné. Refuser le remplacement silencieux d’une facture validée ou d’un règlement par une version concurrente. Détecter les divergences, placer l’opération en anomalie et conserver un historique. Les référentiels communs peuvent avoir un propriétaire central et des demandes de création locales ; ce partage est à arbitrer.

Sans connectivité, la direction ne peut pas connaître les opérations encore non transmises. Afficher pour chaque agence la date métier couverte, la dernière réception et les éventuelles anomalies. Un rapport global incomplet reste consultable comme provisoire, avec son périmètre visible.

En l’absence totale et durable de connexion, un échange de lots de données par un canal autorisé pourrait être ajouté, mais n’est pas validé comme mode de transport dans ce besoin. Ne pas imposer une procédure USB. Ne pas promettre une consultation à distance sans aucun moyen de transmission.

## Droits et exploitation

Distinguer accès société, agence, dépôt, caisse, fonction et action. Un responsable régional peut consulter plusieurs agences sans modifier leurs écritures ; un utilisateur local n’a pas accès par défaut aux autres sociétés.

Prévoir contrôle du serveur sur listes, exports et API. Documenter les droits disponibles en mode déconnecté : une révocation centrale ne peut pas être connue instantanément par un site coupé. Définir durée d’autorisation locale, actions sensibles et reprise au retour réseau sans bloquer arbitrairement le fonctionnement hors ligne promis.

Sauvegarder chaque site et le central, chiffrer les échanges et contrôler l’identité des sites. Après restauration, réconcilier les accusés de réception et les événements pour éviter le rejeu de règlements ou de mouvements déjà intégrés. Ne pas demander ni intégrer les mots de passe de test dans le Skill.

## Analyses par agence et globales

Stocks : conserver unité commune, dépôt, agence et transit. Une expédition interne diminue l’origine et augmente le transit ; la réception diminue le transit et augmente la destination. Gérer les transmissions partielles sans compter deux fois le même mouvement.

Créances : distinguer propriétaire de la créance et lieu du règlement ; suivre les paiements non encore reçus/rapprochés. Les correspondances client ne se fondent pas uniquement sur le nom.

Comptabilité : préserver les analyses locales demandées. Pour un bilan d’agence, définir aussi banques, immobilisations, dettes, charges communes et liaisons. Ne pas présenter l’addition des ventes comme un bilan équilibré. Le regroupement de sites d’une même société et la consolidation légale de sociétés indépendantes sont des périmètres différents. Les règles fiscales et numéros de comptes restent soumis au dossier OHADA applicable.
