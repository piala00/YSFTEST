# Tests exécutés et portée des preuves

## Environnement réel

Archive locale transmission-gpt-2026-10-24.zip, extraite dans un dossier de revue séparé. Python 3.12, environnement virtuel neuf, paquets fournis dans le ZIP installés sans index réseau : Django 5.2.18, Django REST Framework 3.18.3, WhiteNoise 6.12.0, asgiref 3.13.0, sqlparse 0.6.0. Base de test SQLite en mémoire créée puis détruite par Django.

Les versions proviennent des paquets joints ; ce contrôle ne certifie pas leur provenance PyPI ni une autre version de Django. Aucun accès SQL Sage, au serveur de la société ou à une base de production n’a été utilisé. Le ZIP source reste intact et les sources applicatives n’ont pas été modifiées. Les empreintes identifient les fichiers examinés.

## Exécutions

1. `python manage.py test --noinput --verbosity 1` : 155 tests, 41,642 s, OK. Journal dans PREUVES_TESTS_BASE.md.
2. Contrôles complémentaires `python manage.py test review_probes --noinput --verbosity 2` : 8 tests, 1,220 s, 7 échecs et 1 succès. Ces échecs sont des assertions métier souhaitées confrontées au comportement actuel, détaillé dans ANOMALIES.csv. Journal dans PREUVES_TESTS_COMPLEMENTAIRES.md.
3. Livraison partielle isolée : 1 test, 0,692 s, OK ; le même scénario réussi fait aussi partie des 8 tests. Ne pas compter cette répétition comme un scénario indépendant supplémentaire.

Le contrôle système Django ne remonte pas de problème. Un avertissement signale l’absence de répertoire staticfiles collecté dans cette copie ; il n’empêche pas les tests Django. Il ne prouve pas un incident sur le site hébergé.

## Scénarios complémentaires

- R14 : profil restreint, URL API filtrée refusée mais liste générale révélant la quantité attendue.
- R17 : champ absent transformé en zéro et quantité négative acceptée.
- Traçabilité : correction par une deuxième personne attribuant l’ancienne déclaration au correcteur.
- Rapport passé : facture 3000 à J-1 puis règlement à J modifiant le reste dû du rapport J-1.
- Fiche indépendante : sortie non pointée incluse dans son solde théorique.
- R09 : Mobile Money accepté sur le journal CA et augmentant sa caisse ; cohérence modes/journaux à contrôler.
- R13 : livraison partielle 4 sur 10, facture de 4 et reliquat 6, sans seconde sortie.

## Reproduire chez Claude

Utiliser une copie locale du code correspondant à l’archive. Installer les dépendances adaptées dans un environnement isolé. Placer le dossier `scripts` de ce Skill dans PYTHONPATH puis lancer depuis le dossier source :

```bash
python manage.py test review_probes --noinput --verbosity 2
```

Exemple : définir PYTHONPATH sur le chemin absolu du dossier scripts avant la commande, selon le système. Ne pas ajouter ces tests à une branche de production sans revue. Les classes utilisent les données synthétiques de tests du ZIP ; si Claude change ces fixtures, adapter la préparation sans affaiblir les assertions.

## Ce qui n’est pas prouvé

Pas de test visuel navigateur ou du client Windows, pas d’installation Windows, pas de charge ni de concurrence multi-postes, pas de validation PostgreSQL/SQL Server, pas de test du site PythonAnywhere, pas de lecture d’une installation Sage V12, pas d’essai de synchronisation interserveurs. Les fonctionnalités non livrées ne deviennent pas des bugs reproduits : elles restent dans la feuille de route. R18 n’a pas de test d’attente temporelle ; l’absence d’alerte de délai est annoncée dans la transmission, pas reproduite par une horloge simulée ici.
