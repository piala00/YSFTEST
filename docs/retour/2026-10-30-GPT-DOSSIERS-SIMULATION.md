# Dossiers de simulation dans le même logiciel — Codex, 30 octobre 2026

Lot dépendant des onglets d'administration (#14), conservant sécurité, licences simplifiées et saisie rapide. Aucun nouveau taux fiscal/de paie ni moteur de simulation : réutilisation de la commande Transport existante.

## Parcours

- Administration du poste > Simulation : création en arrière-plan d'un répertoire `dossiers-simulation/<identifiant>/` contenant sa propre base SQLite, son descripteur et son journal. Le sous-processus fabrique les données et s'arrête ; il ne lance pas de serveur secondaire et n'ouvre pas de navigateur. La progression est consultable dans l'onglet.
- Télécharger ce dossier produit une archive `.erpsim`. L'importation l'ajoute comme dossier séparé et crée son administrateur avec les identifiants de l'administrateur qui importe ; elle ne remplace ni ne fusionne les données de la société.
- Sur le serveur, après fin des saisies et confirmation OUVRIR : sauvegarde du dossier courant, sélection du dossier fictif et redémarrage du programme. Même édition, même adresse et même port ; session distincte et nouvelle connexion. Tous les postes connectés changent de dossier : l'écran le dit avant confirmation.
- Le bandeau SIMULATION reste visible. Revenir au dossier de la société utilise le même parcours confirmé, avec sauvegarde de la simulation. Le programme et sa configuration d'origine sont conservés. Le dossier actif ne peut pas être supprimé.
- Une ancienne `simulation.sqlite3` peut être reprise dans le catalogue sans nouvelle génération, par une copie nettoyée ; le fichier original est conservé.

## Isolation et fichiers

Le choix est effectué avant le chargement de Django, au redémarrage. Aucune connexion globale n'est remplacée au milieu d'une requête. Les accès SQL, miroir, échanges automatiques, programmation et destination de sauvegarde de la société ne sont pas transmis au dossier fictif. Les sauvegardes de la simulation sont dans son propre dossier. Son secret local est distinct, et il n'est pas exporté.

La copie exportée retire les sessions, jetons d'API, mots de passe et autorisations de licence. Les anciens noms des comptes et coordonnées d'authentification sont remplacés dans la copie. `secure_delete` et VACUUM retirent aussi les anciennes valeurs des pages libres. La base source n'est pas nettoyée ou modifiée par cet export. Les données métier saisies manuellement en simulation restent dans le dossier : ne partager que des données fictives.

L'archive a une liste fermée de fichiers admis, une empreinte SHA-256 du contenu et des limites de taille (512 Mo compressés, 2 Go pour la base). Aucune extraction de chemin fourni par l'archive. Édition, état fictif, intégrité SQLite, tables attendues, migrations connues et absence de vues/déclencheurs sont vérifiés. L'empreinte détecte une altération de transfert ; ce n'est pas une signature d'origine. La sélection et les imports sont réservés à l'administrateur ; un dossier de simulation n'établit aucune confiance d'échange avec une agence réelle.

Si le dossier sélectionné est défectueux au redémarrage, le programme conserve ce dossier, écarte son marqueur et revient à la société avec un message. Les générations possèdent un verrou de fichier pour éviter leur suppression en cours ; une génération interrompue est signalée.

Comme l'ancien serveur séparé de démonstration, le dossier fictif s'ouvre en démonstration pour les essais. Cela ne constitue pas une licence commerciale du dossier de la société : le contrôle normal y est rétabli au retour. La racine de confiance de l'éditeur reste celle du lot #13 ; la clé publique manquante du propriétaire reste à intégrer pour un binaire commercial personnalisé.

## Validation

Dix tests portables SQLite exécutés localement : aller-retour complet, conservation de la base source et du témoin société, retrait des anciens secrets dans les octets exportés, refus de chemins arbitraires, archive altérée/non fictive/version inconnue, vues SQL, sauvegarde en échec, dossier actif non supprimable et verrou de génération. Ces tests sont aussi exécutés sous Windows avant compilation.

La CI exécute en plus les tests HTTP de confirmation/droits et un essai réel : une journée de simulation réduite avec la vraie commande, export/import, démarrage du logiciel à la même adresse, connexion au dossier fictif et retour confirmé avec redémarrage. Les assertions s'exécutent uniquement dans des répertoires temporaires et processus d'essai. Django local indisponible ; ne citer les résultats complets qu'après la CI. Aucun déploiement, aucune fusion, aucune donnée de production manipulée.
