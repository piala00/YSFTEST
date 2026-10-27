# Audit sécurité synchronisation Direction ↔ Agences — Lot 01

Branche de référence : `ccr-5592a371-fusjt2`. Revue statique de `apps/relais/views.py`, `apps/relais/models.py`, `apps/echanges/synchro.py`, `apps/echanges/lots.py`. Aucun test d'exploitation exécuté. Les constats sont des risques à confirmer par tests.

## P0 — Risque de non-réémission après échec de dépôt

`lots.exporter()` crée un `LotEmis` et les `Relais` avant que `_envoyer()` appelle `boite.deposer()`. `a_envoyer()` détermine ensuite les faits nouveaux à partir du maximum `LotEmis.sequence_a`. Si le dépôt échoue, les faits peuvent être considérés comme déjà émis et ne plus être envoyés. Un dépôt HTTP réussi suivi d'une réponse perdue peut aussi créer une ambiguïté.

**Correction proposée :** séparer préparation, mise en attente persistante, transfert et accusé de dépôt ; conserver les octets/identifiant du lot jusqu'à confirmation ; réessayer avec le même identifiant et le même contenu ; ne faire avancer le curseur de livraison qu'après confirmation fiable. Le destinataire conserve sa déduplication `package_uuid`.

**Test :** simuler `ConnectionError` après création du lot ; relancer et prouver que le même événement atteint le destinataire exactement une fois.

## P1 — Écrasement de lots existants

`views.boite` écrit `provisoire.replace(dossier / nom)` et `LotDepose.objects.update_or_create(...)`. Le nom contient une minute et une plage de séquences, pas d'identifiant aléatoire. Deux dépôts de même nom peuvent remplacer des octets différents. `DossierPartage.deposer` présente le même problème.

**Correction :** identifiant unique dans le nom, refus HTTP 409 si même nom et empreinte différente, dépôt idempotent si empreinte identique ; création atomique sans écrasement et protection des écritures concurrentes. Adapter la validation du nom côté relais et client.

**Tests :** même nom/mêmes octets ; même nom/octets différents ; deux dépôts concurrents ; panne entre écriture et insertion DB.

## P1 — Transport HTTP non sécurisé

`RelaisHTTP.__init__` accepte une URL arbitraire, puis envoie `Authorization: Bearer ...`. Un relais `http://` exposerait le jeton et permettrait l'interception ou la modification du trafic.

**Correction :** exiger HTTPS en production, vérifier les certificats, interdire les redirections inter-origines pour les requêtes authentifiées, prévoir une exception locale de développement strictement explicite. Ne jamais journaliser les jetons.

**Tests :** rejet HTTP, certificat invalide, redirection vers un autre hôte, HTTPS valide.

## P1 — Limite de taille appliquée après lecture

`views.boite` accède à `request.body` avant de comparer `len(corps)` à `TAILLE_MAX`. Le serveur peut consommer beaucoup de mémoire pour un corps surdimensionné.

**Correction :** limite de requête au reverse proxy et côté Django ; lecture bornée en flux avec limite stricte, suppression du temporaire si dépassement ; quotas par site et limitation de débit.

**Tests :** requête > 60 Mio, Content-Length absent ou falsifié, dépôts simultanés.

## P1 — Cohérence disque / base

Écriture du fichier puis `update_or_create` sans transaction couvrant le stockage. En cas d'échec, un fichier orphelin ou une métadonnée incohérente peut subsister. Le `DELETE` supprime d'abord le fichier puis la ligne DB.

**Correction :** protocole de publication avec état « en cours » puis « disponible », nom temporaire unique, écriture durable, transaction DB, procédure de réconciliation et nettoyage des orphelins ; suppression idempotente.

## P2 — Dossier partagé et contrôle des accès

`DossierPartage` dépend des permissions du système de fichiers. Sans ACL propres à chaque site, un client ayant accès à la racine pourrait lire/supprimer les lots d'autres sites. Le chiffrement protège leur confidentialité mais pas leur disponibilité.

**Correction :** permissions OS par site, stockage dédié, vérification des chemins et noms, quotas, sauvegarde et supervision. Ne pas présenter ce mode comme équivalent au relais authentifié.

## Contrôles existants à préserver

- AES-256-GCM avec nonce aléatoire et AAD `source>destination`.
- HMAC-SHA256 du manifeste, contrôle de destination et société.
- `LotRecu.package_uuid` et `EvenementRecu` limitent les réintégrations.
- Relais inactif par défaut (`RELAIS_ACTIF`).
- Lecture/suppression d'une boîte limitées au jeton du destinataire.

## Ordre recommandé

1. Corriger la reprise après échec d'envoi et la persistance des lots en attente.
2. Interdire l'écrasement des lots et rendre le dépôt idempotent.
3. Exiger HTTPS et limiter strictement la taille des requêtes.
4. Réconcilier stockage et base, ajouter quotas et tests de concurrence.
5. Valider les ACL du mode dossier partagé.

**Statut :** revue de code uniquement. Aucune exécution de tests, aucun correctif applicatif, aucune fusion, aucun déploiement. Demande de revue à Claude avant toute modification de ses fichiers.
