# Hébergement Django et PostgreSQL — relevé du 21/10/2026

## Périmètre et choix proposé

Recommandation de conception : conserver Render pour l’application de test afin de limiter les changements, et privilégier pour un pilote métier un service web payant avec PostgreSQL persistant, sauvegardes gérées et copie indépendante. Le dimensionnement reste à mesurer. Aucun abonnement, déplacement de base ou déploiement n’a été effectué.

Comparer les offres dans OFFRES_HEBERGEMENT_2026.csv. Tous les prix sont en USD, avant taxes, frais de change et commissions de paiement. Aucun montant FCFA n’est calculé avec un taux de change présumé. La disponibilité et la latence depuis le Cameroun doivent être mesurées ; une région géographiquement proche n’est pas une preuve de bon routage. Garder application et base dans la même région quand possible.

## Comparaison utile à ce projet

| Solution | Ce qu’elle couvre | Limite déterminante |
|---|---|---|
| Render | Application Python et PostgreSQL distincts | Le gratuit ne sécurise pas un dossier métier durable |
| Railway | Application et service PostgreSQL sur consommation | Le crédit couvre l’usage total, pas une base illimitée |
| Neon | PostgreSQL et fonctions annexes | Prévoir séparément le processus serveur Django |
| Supabase | PostgreSQL/backend et stockage | Ne remplace pas un serveur Django généraliste |
| Fly.io | Machines et PostgreSQL géré | Le total application + base dépasse le prix de la seule machine |

### Render — R01 à R05

Web gratuit : veille après 15 minutes sans trafic entrant, 750 h/mois partagées par espace, fichiers locaux perdus aux redéploiements/redémarrages/veilles. PostgreSQL gratuit : 1 Go, expiration 30 jours, puis 14 jours de grâce avant suppression ; pas de sauvegarde gérée. SQLite et pièces jointes locales n’offrent donc pas une persistance durable sur ce service gratuit. Ces faits ne prouvent pas la configuration de notre site actuel, qui n’a pas été inspectée. [R01]

Web payant 0.5c-512mb (ancien Starter), PostgreSQL 0.1c-256mb (ancien Basic-256mb) : repère 7 + 6 USD/mois de calcul, avant stockage et autres postes. Les nouveaux noms sont vérifiés [R02] ; les montants figurent dans l’extrait de recherche officiel [R03] et le repère de juillet 2026 [R05]. Le corps dynamique de la page tarifaire n’a pas livré le tableau complet : confirmer le panier actuel. Ne pas annoncer « 13 USD tout compris ». Les plus petits plans ne sont pas une capacité ERP validée. PITR d’une base payante : 3 jours sur espace Hobby, 7 jours sur Pro ou supérieur [R04].

### Railway — W01 à W04

Essai : crédit 5 USD pour 30 jours ; puis Free : crédit mensuel 1 USD, par service au plus 0.5 Go RAM et 0.5 Go de volume. Hobby : minimum 5 USD/mois, crédit d’usage inclus 5 USD ; une consommation 7 donne une facture 7, pas 12. CPU, RAM, volumes et trafic s’additionnent entre application et base. Pro commence à 20 USD/mois avec son crédit correspondant. [W01,W02]

Serverless est optionnel : inactivité observée via trafic sortant, sommeil généralement après 5–10 min ; des connexions DB persistantes peuvent l’empêcher, et le premier réveil peut retourner 502. [W04] Les sauvegardes de volumes doivent être configurées ; calendrier quotidien conservé 6 jours, hebdomadaire 27 jours, mensuel 89 jours, facturation incrémentale. Ce n’est pas une promesse de PITR PostgreSQL activé par défaut. [W03]

### Neon — N01 et N02

Free : 1 Go/projet, 100 CU-h/projet/mois, 5 Go de transfert public/projet, calcul arrêté après 5 min ; pas d’échéance fixe de 30 jours annoncée. Historique gratuit jusqu’à 6 h, limité en volume de changements, un snapshot manuel ; calendriers automatiques réservés au payant. L’arrêt du calcul ne signifie pas suppression des données. [N01,N02]

Launch : 0.106 USD/CU-h, stockage 0.35 USD/Go-mois, historique 0.20 USD/Go-mois ; pas de minimum mensuel. Historique réglable jusqu’à 7 j, défaut payant 1 j. Le montant « typical spend 15 USD » est un scénario d’usage et non un forfait. Exemple de calcul proposé : 0.25 CU × 730 h × 0.106 = 19.345 USD de calcul seul en continu ; ajouter stockage, historique, autres services et serveur Django. Cette arithmétique n’est pas un devis ni une mesure de notre ERP. [N01,N02]

### Supabase — S01 et S02

Free : base 500 Mo, stockage fichiers 1 Go, 2 projets actifs ; pause après une semaine d’inactivité. Ne pas supposer une conservation illimitée après pause. Pro : à partir de 25 USD/mois, premier projet inclus, base 8 Go, sauvegardes quotidiennes conservées 7 j ; serveur Django à financer séparément. Le PITR est une option distincte des sauvegardes quotidiennes. Les sauvegardes DB n’incluent pas les objets Storage, uniquement leurs métadonnées. Exporter régulièrement hors site pour Free. [S01,S02]

### Fly.io — F01 et F02

Pas de gratuit permanent pour les nouvelles organisations ; essai limité à 2 h de calcul ou 7 j. Exemple officiel d’une application avec base gérée : environ 43.67 USD/mois, dont 38 pour Managed Postgres Basic ; l’exemple comprend machine, volume, stockage et trafic selon hypothèses. Ne pas comparer le seul prix de machine 2.19 USD à une offre complète application + base. Les ressources arrêtées et volumes peuvent rester facturés. [F01]

Managed Postgres inclut haute disponibilité, sauvegardes et pooling ; la rétention exacte n’a pas été certifiée dans ce dossier. La gestion autonome de PostgreSQL sur une Machine ajoute une responsabilité d’exploitation, elle ne doit pas être présentée comme le même service géré. [F02]

## Budget et vérification avant choix

Additionner application, base, stockage DB, fichiers, sauvegardes externes, tâches planifiées, worker éventuel, trafic, espace payant, domaine, taxes et change. Les impressions PDF volumineuses et imports peuvent dépasser la RAM d’un petit service ; mesurer au lieu de promettre une capacité d’après son prix.

Configurer un serveur WSGI/ASGI de production, les paramètres de production, HTTPS, hôtes autorisés et secrets hors dépôt ; exécuter `manage.py check --deploy` avec les vrais paramètres de production [D01]. Sauvegarder données et fichiers ; tester restauration et reprise des connexions après veille. Vérifier sur les réseaux utilisateurs camerounais les temps de connexion, saisie, recherche, édition et téléchargement. Aucun résultat de mesure ni approbation de mise en production n’est fourni ici.
