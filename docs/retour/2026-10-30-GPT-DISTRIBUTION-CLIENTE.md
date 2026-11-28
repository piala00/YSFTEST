# Distribution cliente et activation — Codex, 30 octobre 2026

Lot demandé après l'installation de la version de saisie rapide (#12). Les deux répertoires Program Files et ProgramData séparent normalement programme et données persistantes ; leur existence n'est pas une faille en elle-même.

## Constats vérifiés

- La spécification PyInstaller copiait tout `docs/` dans `documentation/`, avec les documents techniques et les procédures de l'éditeur. Le nouveau paquet ne livre que le guide client explicitement autorisé.
- L'installateur Inno écrivait la référence d'installation dans `cle-installation.txt`. Cette saisie est désormais faite dans l'assistant du logiciel ; le nouvel installateur ne crée plus ce fichier. Les fichiers des anciens installateurs sont convertis au démarrage en stockage protégé, sans suppression avant réussite de l'écriture.
- Le code court 4×6 est une référence d'essai, pas une licence payante. Les licences signées sont déjà liées à l'empreinte de la machine et à l'édition ; copier un code court ou une licence ne doit pas donner des droits sur une autre machine. Le stockage du code en base est désormais authentifié, chiffré et lié à l'installation et à la machine ; Windows utilise en complément DPAPI avec portée machine (service et mode fenêtre). Hors Windows, le chiffrement utilise la clé secrète locale et l'identité machine.
- `ERP_MACHINE_ID`, utile aux tests, ne doit plus modifier l'identité matérielle d'un binaire compilé.
- Le binaire avait une liste `cle_editeur.CLES` vide et acceptait un fichier public remplaçable comme autorité. Un programme client compilé n'accepte désormais que l'identité intégrée. Sans identité intégrée, il reste en essai ; une clé publique fournie librement ne peut pas établir sa propre autorité.

La clé publique d'éditeur nécessaire à une version commerciale personnalisée a été demandée au propriétaire. La clé privée ne doit jamais être envoyée à Codex ni livrée dans le programme client. Son absence n'empêche pas le développement des autres lots. Une installation maîtrisée par un administrateur malveillant peut toujours être altérée ; aucun simple renommage ou chiffrement de fichier ne garantit une protection absolue contre la copie du logiciel.

## Activation

L'administrateur sélectionne le fichier `.erplic`, et facultativement le fichier public reçu dans le même dossier. Le logiciel vérifie qu'il correspond à l'éditeur intégré avant de contrôler la licence. Il ne copie pas de coffre privé et ne remplace pas l'autorité de signature. Aucune manipulation de ProgramData/Program Files n'est requise. Les écrans et nouveaux événements ne répètent plus le code court en clair ; le téléchargement explicite de la demande de licence reste disponible pour l'éditeur.

## Validation

Trois tests purs exécutés localement (aller-retour, autre machine/installation, altération). Tests HTTP, licence copiée, rejet de clé étrangère/coffre privé, conversion des anciens fichiers et distribution ajoutés pour la CI complète. Un contrôle DPAPI réel est ajouté à la compilation Windows. Django indisponible localement : résultats complets à citer depuis la CI, sans prétendre à leur exécution locale. Pas de fusion ni accès à la production.
