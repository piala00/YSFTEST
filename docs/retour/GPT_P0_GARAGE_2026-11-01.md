# P004.3 — validation unique des pièces du garage

Codex, 1er novembre 2026. D-002 / C-007 / Q-001 ; suite des correctifs Documents,
Règlements et Frais déjà proposés en PR, sans réaudit général. Base : Reporting03.2 #35,
commit770afea86146b5e354894e5917ad4abf24292760 (précision Excel héritée).

## Défauts effectivement reproduits

Trois recettes prennent deux instances de la même pièce persistée, avant sa validation.
La première est enregistrée, puis l'ancienne est réutilisée :

- même plein de carburant : deux écritures au lieu d'une ;
- même achat magasin : deux écritures au lieu d'une ;
- même ordre de réparation utilisant une pièce du magasin : deux écritures au lieu d'une.

Le plein déjà comptabilisé pouvait aussi accepter un montant modifié en mémoire. Une pièce
supprimée pouvait être réinsérée ; les copies attachées à un alias miroir n'étaient pas
refusées explicitement avant traitement. Un plein d'origine distante pouvait être comptabilisé.

Relevé avant correction, après correction de la fixture :10 tests, huit assertions échouées,
trois erreurs de sous-cas alias miroir non configuré et trois ignorés SQLite. Ce ne sont pas
huit anomalies distinctes. Une erreur initiale de fixture (plusieurs pleins avec numéro vide
unique) a été corrigée avant ce relevé ; elle n'est pas classée comme défaut du produit.
Les trois doublons comptables `2 != 1` sont conservés dans les journaux de reproduction.

## Correctif

Les trois services conservent leur transaction atomique et leurs calculs. Un helper de garage
refuse un objet provenant d'une autre connexion, applique le mode de saisie, relit la pièce
sous verrou et refuse une pièce supprimée ou une copie d'agence. La décision porte sur les
champs persistés, après invalidation des caches de relations.

Le plein refuse un second passage lorsqu'il est déjà comptabilisé. L'achat et la réparation
refusent un état déjà validé/clôturé ou déjà lié à une écriture. Le statut de clôture protège
aussi les réparations dont les seules pièces viennent du stock, sans écriture principale.

Aucune formule de coût moyen, quantité, imputation véhicule, pièce, carburant, fournisseur,
main-d'œuvre ou commission n'est modifiée. Aucun mouvement historique n'est réécrit.
Le verrou et les garde-fous interviennent avant les effets financiers et de stock.

## Tests exécutés

- Garage :18 tests OK en2,284s, dont trois ignorés sous SQLite (concurrence).
- Contrôle combiné Garage + Excel après héritage du parent final :27 tests OK en20,059s,
  trois ignorés SQLite.
- Dix nouveaux tests, dont trois recettes à deux connexions réservées au moteur disposant
  de `select_for_update` : même plein, même achat et même ordre de réparation.
- Après correction : une seule écriture ; achat de10 pièces conservé à10 ; réparation de2
  pièces conservée à8 ; pas de second mouvement, de modification du montant déjà posté,
  de résurrection ni d'accès à la connexion miroir.
- Panne fictive après publication réelle : rollback stock/écriture/outbox, puis reprise
  avec une seule entrée et une seule dette. Les anciennes régressions garage restent exécutées.
- Suite locale complète avant la correction héritée de précision Excel :639 tests en626,013s,
  quinze ignorés et les trois erreurs connues de sockets interdites. Elle n’est pas annoncée réussie.
  Après héritage de la correction de précision du parent :640 tests en581,553s, quinze ignorés
  et les trois mêmes erreurs de sockets interdites. Aucune autre erreur ni assertion en échec.
  La suite locale n’est pas annoncée réussie ; la CI complète doit réellement passer.
  Aucun changement des trois services Garage n’est effectué entre ces versions.
- La CI Transport Windows est étendue pour exécuter Garage et Excel après compilation native,
  avec vérification préalable du chargement des quatre modules .pyd, sans repli sur leurs sources.
  Cette recette de27 tests doit réellement passer avant d'être annoncée acquise ; les trois
  concurrents restent réservés à SQL Server. Elle ne prétend pas remplacer toute la recette GUI.
- Aucune migration ; `git diff --check` vérifié.

## Portée

Ces contrôles concernent une même pièce persistée. Deux nouveaux formulaires distincts, les
éditions/suppressions simultanées de lignes et les achats différents portant plusieurs articles
ne sont pas certifiés par ce lot. Les échanges garage/décomptes restent ouverts dans ANO-F-001.
La recette concurrente SQL et les compilations doivent réellement terminer en CI avant d'être
annoncées acquises. Les frais/propriétaires, les référentiels SN/SMT et les comptes ne sont pas réinventés.

Données entièrement fictives, PR en brouillon, aucune fusion, aucun déploiement ni modification de production.
