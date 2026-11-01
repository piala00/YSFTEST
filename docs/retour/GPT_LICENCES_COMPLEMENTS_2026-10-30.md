# Codex — compléments licences 3.1 — 30 octobre 2026

Reprise demandée explicitement par le propriétaire dans la conversation (« il faut commencer »),
après les commentaires #6531167365 et #6531246203 de la PR #21. Complément de la branche gpt/
existante, sans perdre #11 à #20. Le programme global est conservé dans le document de suivi local.

## Interface propriétaire

Fenêtre 760×640 au lieu de 960×790, minimum 600×440, redimensionnable. Deux modules conservés.
Le contenu du module Licence défile ; Générer, Exporter et Supprimer restent en bas de la fenêtre.
L'historique dispose de son propre ascenseur. Les raccourcis de durée restent disponibles dans une liste compacte.
Créer/regrouper/verrouiller l'identité, options avancées et ancien identifiant serveur restent accessibles.

## Suppression ciblée et journal

Le bouton exige une sélection unique, affiche numéro, société, édition, postes, machine et fichier, puis demande
confirmation. Le registre et la signature sont vérifiés ; chemins externes, liens, doublons, public différent et
sélection devenue périmée sont refusés. Le fichier .erplic seul est déplacé dans corbeille-licences/<identifiant>/.
Les clés, autres licences, données, demandes, notices et ZIP déjà exportés restent inchangés.

Journal propriétaire journal-suppressions.json : intention durable avant déplacement, puis état final, date UTC,
compte local, numéro, société, emplacement et SHA-256. Écriture du journal par fichier temporaire synchronisé et
remplacement atomique. En cas d'échec de finalisation, le fichier est remis à sa place et l'annulation journalisée.
Une opération interrompue est signalée et bloque une nouvelle suppression jusqu'au contrôle du journal/corbeille.
Ce n'est pas une transaction matérielle multi-fichiers ni une garantie contre toute panne : les fichiers restent
récupérables en corbeille ; un verrou d'une exécution interrompue nécessite diagnostic.

Le CSV conserve les numéros émis : pas de réattribution d'un numéro supprimé. La liste active masque ces entrées.
Le regroupement d'identité transmet l'état supprimé sans recopier la licence. Un réexport d'une licence restaurée
manuellement est refusé tant que cet état subsiste. Ce retrait local ne révoque pas une licence déjà remise au client.

## Guide et installation cliente

INSTALLATION_CLE_PUBLIQUE.md est généré dans le dossier propriétaire à la création, au regroupement et à l'ouverture
de l'identité. Le bouton Guide permet de le générer/consulter pour un dossier existant. Il contient : fichiers,
empreinte publique brute SHA-256, chemins par défaut des deux éditions, procédure exacte d'import, vérifications,
messages de refus et solutions, Windows 10/11/Server, conservation et limites de suppression.

Le formulaire client existant est conservé : fichier .erplic + parametres.dat → Installer la licence.
Le public facultatif s'il est déjà intégré est vérifié contre l'autorité autorisée ; il ne devient jamais une
nouvelle autorité par simple import. Le client affiche l'empreinte des identités autorisées et confirme le public
reconnu après une installation réussie. La licence validée est dans la base, aucun collage de clés dans les dossiers
Windows n'est requis. Le coffre privé DER/PEM reste refusé et n'est jamais distribué.

## Validation

35 tests unitaires de l'outil effectivement exécutés localement : anciens parcours, guide et empreinte,
annulation, suppression exacte, numérotation, sélection périmée, fichier d'une autre licence, doublons,
chemins externes, liens durs/symboliques, public altéré, journal invalide/interruption, échecs d'écriture/déplacement,
reprise après échec, regroupement et réexport refusé. Compilation syntaxique Python exécutée.

Deux scénarios Django supplémentaires couvrent l'absence d'autorité intégrée et le refus d'un coffre privé DER
ou d'un fichier public trop volumineux. Le scénario existant d'import contrôle aussi l'empreinte affichée et le
message « Clé publique reconnue ». Django local indisponible : aucun succès Django local n'est revendiqué.

Le parcours interface-essai ouvre les deux modules, émet deux licences fictives, annule puis confirme la suppression
de la première, vérifie l'autre et les clés, le guide, le journal et l'accessibilité des boutons à 760×640 et 600×440.
Ce parcours doit s'exécuter sous écran virtuel puis dans l'exécutable Windows construit par la CI avant livraison.
Les journaux finaux seront cités dans la PR ; ce fichier ne prétend pas anticiper leurs résultats.

Les essais de runner Windows ne valent pas essais séparés de Windows 10, Windows 11 et Windows Server :
l'OS réellement essayé sera identifié dans les résultats. Aucun nouvel essai sur le PC du propriétaire ni imprimante réelle.

## Limites conservées

Le code court 4×6 n'authentifie pas son émetteur à lui seul. Le public binaire n'est pas secret ; le privé est chiffré.
L'identité publique commerciale du propriétaire reste à intégrer aux exécutables clients : aucune identité privée
réelle demandée ou créée à sa place. Aucune fusion, aucun déploiement ni modification de production.
