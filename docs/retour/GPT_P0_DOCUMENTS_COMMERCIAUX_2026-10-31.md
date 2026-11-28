# Codex — P0 Documents commerciaux — 31 octobre 2026

Suivi : issue #27, registre #24 (D-002/D-004/Q-001), prise en charge dans l'issue #1 commentaire6543240485.
Base : produit dea6c9161872b46d08c9756baad8bd2ad036e301 de #25, arbre0420693ff6d0bb21b741fc5a3e8d11bbd4b4eba2.
La copie locale de travail a exactement cet arbre ; le commit local de base diffère car les publications précédentes
ont été faites par API GitHub. L'audit #22 et les moteurs métier, comptables et d'échanges sont réutilisés.

## Reproductions et correction

Les scénarios utilisent une agence, des tiers, un article et des montants fictifs. Aucun taux fiscal ni contrat nouveau.

| Référence | Priorité | Fait reproduit avant correction | Correction |
|---|---|---|---|
| DOC-01 | P0 | Deux objets d'une même facture en brouillon, chargés avant la première validation, produisent deux écritures et deux mouvements ; vente de10 sur100 : stock80 au lieu de90. Le numéro et le lien à l'écriture sont aussi remplacés. Cas achat reproduit. | Verrouiller et relire la pièce avant le contrôle du statut ; la seconde validation est refusée, comme un appel répété sur le même objet. |
| DOC-02 | P0 | Un ancien brouillon annule une facture devenue validée ; une livraison est marquée annulée sans restituer le stock. Un ancien brouillon revalide une pièce déjà annulée. | Décider d'après le statut réellement stocké ; conserver les règles existantes d'avoir et d'annulation des livraisons. |
| DOC-03 | P1 | L'ancien objet écrase tiers/référence corrigés en base et ignore un blocage du tiers présent dans son cache. | Rechargement complet, y compris invalidation des relations et données préchargées. |
| DOC-04 | P1 | Le rollback retire bien stock, pièce et outbox, mais laisse le cache Python à VALIDE : reprendre le même objet est refusé. | Chaque nouvelle action relit la pièce stockée avant ses préconditions ; la reprise ne double aucun effet. |
| DOC-05 | P1 | Une seconde annulation depuis une ancienne instance réécrit la date initiale de l'annulation. | Retour sans mutation lorsque la pièce stockée est déjà annulée. |

`Document.valider` et `annuler` gardent leur transaction globale. `_verrouiller_et_relire` utilise une lecture avec
verrou de ligne dans cette transaction, puis les services existants. Aucun nouveau schéma de comptes, migration ou
moteur comptable. Le programme commercial traite la base active `default` : une instance provenant directement d'une
autre copie/alias, notamment `miroir`, est refusée avant toute mutation de la base active. Ce lot ne transforme pas
les services commerciaux en moteur d'écriture multi-base. Un document supprimé entre le chargement et l'action est
signalé par une ValidationError exploitable dans le parcours existant.

## Tests réellement exécutés

- Avant correction : 14 tests découverts, dont2 ignorés sur SQLite ; 14 échecs d'assertions/sous-cas et1 erreur
  de reprise, répartis entre8 méthodes en échec et1 méthode en erreur. Ce n'est pas14 anomalies indépendantes.
  Journal local `DOCUMENTS_P0_AVANT.log`.
- Après correction : 16 tests, OK en1,737s, dont2 ignorés sur SQLite (`DOCUMENTS_P0_APRES.log`).
- Régressions Commercial + P0 comptable #22 : 111 tests, OK en18,418s, dont4 ignorés sur SQLite
  (`DOCUMENTS_P0_REGRESSIONS.log`). GET405, profil lecture403, POST sans CSRF403 effectivement vérifiés.
- Les deux nouvelles recettes concurrentes utilisent chacune deux connexions et une barrière après chargement des
  objets. Elles sont ignorées lorsque le moteur n'a pas de verrou de ligne, notamment SQLite ; leur succès SQL Server
  doit être constaté dans la CI, pas déduit des essais séquentiels locaux.

Commande ciblée : `python manage.py test apps.commercial.tests_p0_documents --noinput -v1`.
Régression : `python manage.py test apps.commercial apps.comptabilite.tests_p0_validation --noinput -v1`.
Variables locales : DB_ENGINE=sqlite, DATABASE_URL et MIROIR_DB_ENGINE vides, ERP_ASSISTANT/ERP_LICENCE/RELAIS_ACTIF=0.
Le bac à sable local interdit les sockets nécessaires à certains essais de la suite globale ; ne pas redemander
de permissions en boucle ni présenter ces restrictions comme défauts ERP. Les suites complètes et les compilations
Windows du nouveau SHA sont donc à vérifier en CI externe avant de conclure. Aucun succès complet anticipé.

## Périmètre restant

La transaction existante stock/pièce/publication reste unique ; le test injecte une panne après une vraie écriture
d'outbox pour le vérifier. Les tests concurrents de ce lot portent sur deux validations de la même facture et deux
annulations de la même livraison. Ils ne certifient pas toutes les combinaisons édition simultanée de lignes,
transformation, règlements, caisses, multi-agences ou erreurs transitoires SQLite. Ces écarts restent au programme.
Les services déjà audités et le reporting fondé sur les écritures générales validées ne sont pas réanalysés ici.

Aucune fusion, aucun déploiement ni donnée de production modifiée. PR en brouillon et revue croisée attendue.
