# Sauvegarder et prouver la restauration

## Politique proposée pour le pilote

Décider avec l’entreprise la perte de données maximale acceptable (RPO) et la durée d’interruption maximale (RTO). Proposition initiale à ajuster : sauvegardes gérées/PITR selon le plan, copie logique hors fournisseur chaque jour et avant migration, conservation indépendante 7 quotidiennes, 4 hebdomadaires et 12 mensuelles, fichiers sauvegardés également. Ce calendrier est un choix de conception, pas une obligation OHADA ou une fonctionnalité incluse chez tous les hébergeurs.

Contrôler quotidiennement succès, date et taille cohérente ; chiffrer la copie indépendante et limiter les accès. Préserver la clé de déchiffrement séparément. Une copie sur le même disque ne couvre pas sa perte. Tester une restauration mensuelle et après toute évolution importante. Ne pas créer d’automatisation ou changer un service avec le seul présent document.

## PostgreSQL : modèle d’export et de restauration

Configurer localement deux services PostgreSQL distincts via le mécanisme de configuration protégé de libpq : `erp_source` et `erp_recette_vide`. Préparer la base de recette isolée et vide avant restauration. Ne pas placer une URI avec mot de passe dans une commande, un dépôt ou un journal partagé.

```bash
pg_dump --dbname='service=erp_source' --format=custom --file=erp_YYYYMMDD.dump
pg_restore --list erp_YYYYMMDD.dump
pg_restore --dbname='service=erp_recette_vide' --no-owner --no-privileges --exit-on-error erp_YYYYMMDD.dump
```

Remplacer la date à chaque sauvegarde pour conserver les versions. `pg_restore --list` vérifie seulement la lecture du catalogue d’archive, pas la restauration complète. Utiliser un client compatible avec la version du serveur ; vérifier extensions et privilèges. Le dump d’une base ne contient pas les rôles globaux de l’instance ; recréer les rôles et droits nécessaires dans l’environnement cible. Les commandes ci-dessus sont des modèles documentaires non exécutés dans cette recherche. [P01,P02]

Un dump logique fournit un export cohérent d’une base mais ne remplace pas une stratégie de sauvegarde physique/PITR de production. Il ne synchronise pas automatiquement les pièces jointes stockées hors base. Pour la copie indépendante, archiver aussi configuration nécessaire hors secrets, version du code, migrations et objets/fichiers ; gérer une coupe cohérente données-fichiers. [P01 et choix de conception]

## Contrôles après restauration

1. Démarrer la même version de l’ERP en recette sans envoyer de mails réels ni déclencher les tâches métier externes.
2. Vérifier accès, sociétés, profils, exercices et derniers documents attendus.
3. Comparer nombres de lignes, balances, débits/crédits, créances, quantités par dépôt et un échantillon de pièces jointes.
4. Mesurer la durée complète de reprise et le dernier point récupéré ; comparer aux objectifs RTO/RPO.
5. Consigner date de copie, version, empreinte, environnement restauré, écarts et décision de recette.

En cas d’écart, préserver la source et les sauvegardes antérieures ; ne pas basculer les utilisateurs sur la restauration incomplète. Supabase exclut les objets Storage des sauvegardes DB [S02]. Render gratuit n’a pas la récupération du payant [R01,R04]. Les sauvegardes Railway de volume sont configurables et facturées [W03]. Les instantanés/branches Neon ne suppriment pas le besoin de copie indépendante [N02 et choix de conception].
