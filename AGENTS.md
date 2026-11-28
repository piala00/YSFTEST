# Règles communes aux assistants (Claude, GPT/Codex…) qui travaillent sur ce dépôt

Le propriétaire du dépôt fait travailler plusieurs assistants sur le même logiciel. Ces règles valent pour tous.

## Le logiciel
- ERP OHADA (Cameroun), Django + Python, deux éditions : **Commerce** (port 8000) et **Transport** (port 8100).
- Plan comptable à 7 chiffres. Deux modules : Comptabilité générale et Comptabilité analytique (10 plans Transport).
- Reporting construit sur les états (`apps/reporting`).
- Base de travail SQLite, avec copie miroir automatique vers SQL Server (commande `miroir`).
- Programme compilé : `deploy/executable`. Paquets Windows : `deploy/windows`.
- Documentation : `docs/`. Retours entre assistants : `docs/retour/`. Audit du reporting : `docs/AUDIT_REPORTING_ETATS.md`.

## Où travailler
- Le travail courant est sur la branche **`ccr-5592a371-fusjt2`**, et non sur `main` (qui ne contient que le premier fichier).
- Chaque assistant travaille sur **sa propre branche**, créée à partir de la branche de travail courante.
  Exemple : `gpt/<sujet>` pour GPT, `ccr-…` pour Claude.
- Ses changements arrivent par une pull request vers la branche de travail.
- Pas de réécriture d'historique (rebase, force-push) sur la branche d'un autre assistant.
- Avant de commencer : lire les derniers commits et `docs/retour/` pour ne pas refaire ou défaire le travail de l'autre.
- Pour une remarque sur le travail de l'autre : un commentaire sur la pull request, ou un fichier dans `docs/retour/` daté et signé (Claude / GPT).

## Règles qui ne se discutent pas
- **Aucune écriture dans les bases d'un autre logiciel.** L'accès aux bases SQL Server de l'ancien logiciel (reprise, synchronisation) est en lecture seule. Ne jamais modifier le serveur de production.
- **Aucune donnée réelle** de la société dans le dépôt : uniquement des données fictives (simulation).
- **Rien d'inventé en fiscalité ou en paie.** Aucun taux de TVA, d'impôt ou de cotisation n'est imposé. Les comptes et formules non confirmés sont marqués « à valider par l'expert-comptable ».
- Le nom de l'ancien logiciel n'apparaît pas dans les écrans du logiciel.
- Pour l'argent, jamais de « la dernière écriture gagne ». Toute écriture analytique provient d'une écriture générale validée.
- Les migrations sont additives. Les migrations de données écrivent avec `schema_editor.connection.alias`.
- Pas de filtre `__regex` : non pris en charge par SQL Server. Utiliser des préfixes (`startswith`).
- Les textes du logiciel et les messages de commit sont en français.

## Avant de pousser
```
python manage.py test --parallel 4          # toute la suite doit passer (307 tests au 27/10/2026)
```
- Dire quels tests ont été réellement lancés, et ne jamais annoncer comme testé ce qui ne l'a pas été.
- En particulier, ne pas prétendre qu'un .exe Windows fonctionne sans l'avoir compilé sous Windows.
- Les paquets `docs/ERP-OHADA-*-Windows.zip` se reconstruisent avec `deploy/windows/construire_paquet.sh`. Les fichiers `.bat` restent en fins de ligne CRLF.
