# Guide d'utilisation des outils SQL — lecture seule

## Conditions avant la première connexion
- Un dossier Sage **de démonstration** ou sa copie autorisée ; ne pas se connecter sur une base de production pour le premier essai.
- Un compte SQL dédié limité à la **lecture des catalogues SQL**, sans `INSERT`, `UPDATE`, `DELETE`, `ALTER`, etc. SQL Server expose seulement les métadonnées que l'utilisateur est autorisé à voir.
- **Ne pas envoyer de mot de passe, de chaîne de connexion ou de véritables données clients à Claude**.
- Noter le produit (Compta / Gescom), la version V5…V12, le build exact, l'édition et les options.

## Mode 1 — Exécution dans SQL Server Management Studio
1. Ouvrir SSMS, choisir la base Sage de **test** (une base à la fois).
2. Se connecter avec un compte de lecture seule. Ouvrir `sql/01_INVENTAIRE_SYSTEME_LECTURE_SEULE.sql`.
3. Inspecter les six résultats et les exporter séparément en CSV si nécessaire.
4. Vérifier que l'export contient **uniquement des métadonnées**. Si des informations personnelles figurent dans les noms d'objets, anonymiser avant tout partage.
5. Recommencer sur chaque version d'une même famille ; comparer avec les fichiers CSV et l'outil ci-dessous.

## Mode 2 — Export Python (optionnel, Windows)
Prérequis : `python`, `pyodbc` et un pilote Microsoft ODBC Driver for SQL Server compatible avec le serveur.

```powershell
$env:SAGE_SQL_CONN_RO = "DRIVER={ODBC Driver 18 for SQL Server};SERVER=SERVEUR_TEST;DATABASE=SOCIETE_TEST;Trusted_Connection=Yes;Encrypt=Yes;TrustServerCertificate=No"
python .\outils\exporter_metadonnees.py --dossier .\sorties\v12_gescom --alias GESCOM_V12_TEST
Remove-Item Env:SAGE_SQL_CONN_RO
```

Ne pas copier cet exemple avec une base réelle sans contrôle des permissions. La variable d'environnement peut contenir des informations sensibles : éviter les journaux de commandes et effacer la variable après utilisation.

## Comparaison de colonnes, hors connexion SQL
```powershell
python .\outils\comparer_catalogues.py --avant .\sorties\v10_gescom\colonnes.csv --apres .\sorties\v12_gescom\colonnes.csv --sortie .\sorties\diff_v10_v12.csv
```

Ce comparateur identifie **ajouts, suppressions et changements de propriétés de colonnes** uniquement. Les inventaires d'index, vues, contraintes, triggers et dépendances sont fournis, mais leur comparaison structurée reste un développement ultérieur.

## Sécurité et confidentialité
Aucune création de procédures, aucune réparation automatique et aucun script de mise à jour n'est fourni. En cas de problème, **arrêter le test**, sauvegarder les fichiers de diagnostic expurgés et ne pas lancer de réparation sur une base commerciale.
