# Sécurité et export

## Contenu de l'export `RETOUR_CLAUDE_CODE_ERP_TRANSPORT.zip`
- Code source complet suivi par Git (applications, gabarits, migrations, tests, scripts de déploiement, skills, documentation).
- Exclus : archives `*.zip` du dépôt (paquet Windows, anciens envois), `.git`, bases de données, caches.
- Aucune base de données n'est incluse ; aucune donnée réelle de client, de salarié ou de comptabilité.

## Revue des secrets (faite avant l'export)
- Aucun fichier `.env`, clé privée, jeton ou mot de passe réel dans le dépôt.
- `erp/settings.py` lit la clé secrète et les accès base dans l'environnement (valeur par défaut de développement seulement).
- `.env.example` ne contient que des valeurs d'exemple (« motdepasse », domaine d'exemple).
- Dans la copie exportée, le nom de la société de démonstration est remplacé par « Société Démo ».
- Les clés d'échange entre agences sont générées dans chaque base, jamais dans le code.

## Données d'exemple
- Les seules données jointes sont fictives : CSV `demo_2026_09`, exemple propriétaire, PDF `rj-1.pdf` (rapport d'essai produit
  par le logiciel avec des véhicules « fictifs »).

## Diffusion
L'export est un fichier à remettre par vous-même à ChatGPT ; il n'est envoyé nulle part automatiquement.
