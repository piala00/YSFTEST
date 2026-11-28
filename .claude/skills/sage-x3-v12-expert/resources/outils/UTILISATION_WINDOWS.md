# Exécuter les collecteurs Sage sur Windows sans modifier les données

## Prérequis
- Machine Windows où sont installés Sage et/ou les pilotes ODBC SQL.
- Python 3.10+ de préférence.
- `pip install pyodbc pywinauto` (sur une machine autorisée ; pyodbc nécessite pilote ODBC MS SQL Server).
- Un compte SQL dédié lecture seule pour consulter uniquement des **métadonnées** (ou Windows Auth avec droits minimaux) ; ne pas utiliser `sa`.
- Société de test sans données personnelles pour observer les écrans. Vérifier les autorisations de l'entreprise.

## 1. Inventorier une base SQL
Sous PowerShell :

```powershell
python .\export_sql_metadata.py --server 'SERVEUR\INSTANCE' --database 'DOSSIER_TEST' --out 'captures\gescom_v12'
```

Si le serveur requiert identifiants SQL, définir temporairement `SAGE_SQL_USER` et `SAGE_SQL_PASSWORD` dans le processus PowerShell (ne pas les inclure dans un script commité). Supprimer ensuite les variables ou fermer la session.

Produits : `tables.csv`, `columns.csv`, `indexes.csv`, `foreign_keys.csv`, `manifest.json`. **Aucune ligne client/facture** exportée.

## 2. Comparer V5 et V12

```powershell
python .\diff_sql_schemas.py --old '.\captures\gescom_v5' --new '.\captures\gescom_v12' --out '.\captures\difference_gescom_v5_v12.csv'
```

La comparaison ne prouve pas que le comportement fonctionnel a changé. Croiser avec menus, versions et cas.

## 3. Inventorier les fenêtres déjà ouvertes

```powershell
python .\capture_ui_windows.py --title 'Sage' --product 'Gestion Commerciale' --version 'V12' --output '.\captures\sage_interface.json'
```

L'outil n'ouvre ni ne clique un menu. Ouvrir les fenêtres manuellement dans la société de test (une par une). L'UI Automation ne capture pas toujours les contrôles Win32 historiques. Les valeurs de Text, Edit, ListItem et DataItem sont masquées, et aucun texte métier n'est exporté.

## 4. Objets métiers : registre COM

```powershell
python .\inventaire_com_windows.py --out '.\captures\com_version_sage.json'
```

Les entrées représentent des ProgIDs candidats. Compléter par les interfaces vérifiées du manuel de la version installée.

## 5. Mettre à jour la matrice
Pour chaque menu/fenêtre/champ, joindre preuve visuelle expurgée de société fictive, droits et édition ; réaliser des tests pour chaque bouton ; dater et certifier les lignes du catalogue.

**À ne pas faire** : pointer ces outils sur une installation sans autorisation ou recopier des exports contenant des secrets/coordonnées clients dans une conversation publique.
