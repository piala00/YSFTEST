# Licences simplifiées 2.0 — 30 octobre 2026

## Pour le propriétaire

1. Ouvrir ERP-OHADA-Licences : la fenêtre indique « Licences simplifiées 2.0 ».
2. Choisir le dossier du coffre existant. Ne pas recréer la paire de clés : les anciennes licences en dépendent.
   Les anciens fichiers sont reconnus. Une nouvelle identité utilise `coffre.dat` (privé, chiffré) et
   `parametres.dat` (identité publique binaire).
3. Déverrouiller au premier besoin : le même mot de passe sert pendant toute la session. Verrouiller ou fermer
   l'outil retire la référence de la clé en mémoire ; aucun mot de passe n'est sauvegardé dans les préférences.
4. Choisir société/édition et le dossier de livraison, distinct du coffre. « Clé d'installation » génère
   quatre groupes de six caractères. Ce code identifie l'installation ; ce n'est pas une licence payante.
5. Le client utilise le logiciel **mis à jour avec cette version** : ancien Transport incompatible avec le code court.
   Il saisit sa société, son code court, puis télécharge sa demande dans Licence.
6. Ouvrir sa demande dans l'outil, choisir durée et postes, puis « Générer le dossier client ».
   La licence `.erplic`, la notice `…-LIRE-MOI.txt`, le code alternatif et `parametres.dat` sont dans le dossier choisi.
   Transmettre ces fichiers publics uniquement ; jamais le coffre ou son mot de passe.

## Pour le serveur du client

Si l'identité de l'éditeur est déjà intégrée au programme officiel, elle reste prioritaire et aucun fichier
ne peut la remplacer. Sinon, cette distribution de transition reconnaît `parametres.dat` à côté de l'exécutable
du serveur : copier ce seul fichier public reçu de l'éditeur, puis redémarrer le serveur/service.
Ne pas le copier dans les dossiers de données de ProgramData ; ne jamais y installer le coffre.

Dans Licence : **Installer le fichier de licence** puis choisir le `.erplic` reçu. Cela suffit.
Le code d'activation reste une méthode alternative facultative, dans « Autre méthode ».

## Compatibilité et limites

- Les anciennes licences, demandes, clés signées et coffres PEM restent reconnus.
- Le CLI conserve les formats historiques par défaut : `cles --noms-neutres`, `installation --courte` activent
  les nouveaux formats ; l'interface graphique les utilise pour les nouvelles installations.
- Les licences du nouveau parcours sont signées et liées au serveur, au code, à la société, à l'édition,
  au rôle et au site. Modifier les droits invalide leur signature. Un code court seul ne donne pas de licence.
- Le code court est une référence aléatoire de 120 bits, pas une signature Ed25519 tronquée.
- `parametres.dat` est binaire, **pas secret**. Il n'apporte pas la protection cryptographique du coffre : la
  protection de cette identité dépend des droits du dossier d'installation tant qu'elle n'est pas intégrée.
  L'intégration au programme officiel reste préférable. Ne pas accepter une identité reçue d'une source inconnue.
- L'identité publique placée dans un dossier client ne remplace jamais celle d'un autre éditeur silencieusement.
- La licence ne peut pas être testée sur le PC du propriétaire sans son message d'erreur et sa version installée.

Aucune fusion ni modification de production automatique. La mise à jour du serveur est un choix du propriétaire.
