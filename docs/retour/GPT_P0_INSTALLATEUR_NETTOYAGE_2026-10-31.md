# Codex — installation et nettoyage contrôlés — 31 octobre 2026

Demandes : issue #1, commentaires 6536201349 et 6536570880 (architecture précisée). Dépend de #23 (identité vérifiée avant compilation).
Réutilisation de #13/#21, Inno Setup et WinSW existants. Aucune installation ni suppression sur le PC
du propriétaire ou dans une société réelle. Aucune connexion SQL Server dans les nouveaux outils.

## Causes vérifiées et changement de politique

L'ancien script conservait volontairement toutes les données. `DejaConfigure()` vérifie la présence de
`configuration.env` pour sauter le choix de base ; `Societe.assistant_termine` conserve la fin de l'assistant.
La mémoire d'essai existe aussi en base, dans `.erp-essai` et dans le registre utilisateur. Ces états persistants
ne sont pas une autorisation signée de copier le logiciel. Le service écrit des journaux non suivis par Inno
dans `{app}/journaux-service`, et Python peut créer des caches de migrations sous `_internal`.

Politique proposée et implémentée :

| Situation | Autorisation | Données |
|---|---|---|
| Première installation serveur | Autorisation `.erpinst` distincte, signée : machine/édition/dates/key_id vérifiés hors ligne | Créées ensuite par l'ERP |
| Réinstallation, même PC ou après retrait | Même vérification et fichier à sélectionner de nouveau | Ancienne configuration ne dispense jamais du contrôle |
| Mise à jour / réparation | Autorisation signée valide également vérifiée | Configuration et données conservées |
| Nouveau PC | Licence de ce PC requise ; celle d'un autre PC est refusée | Aucun transfert implicite d'autorité |
| Poste navigateur | Aucun binaire métier n'est installé ; accès au serveur par son URL | Aucune base locale créée |
| Désinstallation normale ou silencieuse | Retire programme/service/raccourcis suivis par Inno et règle de pare-feu | Conservation par défaut |
| Nettoyage demandé dans la désinstallation interactive | Inventaire, choix d'une sauvegarde hors périmètre, relecture par empreintes et confirmation finale | Seulement fichiers attribués ; éléments inconnus ou partagés préservés et signalés |

L’autorisation `.erpinst` permet la copie du programme. Elle utilise un domaine de signature séparé, une référence 4×6, le matériel du serveur, l’édition, une échéance et le `key_id` SHA-256 de l’identité publique intégrée. Une licence d’exploitation `.erplic` est refusée à cette étape. L’activation de l’exploitation reste indépendante, par fichier ou clé texte, avec ses contrôles de société, référence d’installation, rôle/site et durée. Les anciens fichiers de licence ne sont pas convertis ni invalidés.
Le code court autonome 4×6 reste une référence ; sa seule forme n'autorise rien. Il n'est pas remplacé par
un secret partagé dans le client. Aucun nouveau format de licence ni nouvelle paire réelle n'est imposé.

## Contrôle avant la copie

L'outil onefile embarqué `ERP-Controle-Installation.exe` utilise la même autorité publique native que l'ERP.
L'installateur affiche le code matériel pour l'émission avant la première installation. `PrepareToInstall`
vérifie le fichier même en mode silencieux, avant d'arrêter un service existant. Aucun booléen de configuration,
registre ou ancienne clé stockée ne remplace la signature. Les chemins cités sont contrôlés et le marquage de
dossiers est distinct de la vérification, pour éviter qu'un argument ajouté ne contourne celle-ci.

Installation silencieuse serveur : ajouter `/AUTORISATION="C:\Reception\autorisation.erpinst"` aux paramètres existants.
Le dossier cible doit être vide, déjà celui de cette édition ou marqué pour elle ; un autre produit est refusé.
Les fichiers de preuve sont sélectionnés, pas recopiés au hasard dans les dossiers système. Une copie directe
des exécutables hors installateur reste techniquement possible ; c'est la licence signée et liée à la machine
qui protège leur usage commercial, pas la seule présence de cet écran.

## Inventaire des ressources et propriétaires

| Ressource | Création / propriétaire | Traitement |
|---|---|---|
| `Program Files/ERP-OHADA/<Édition>` ou dossier choisi | Fichiers du paquet, suivis par Inno | Retrait standard Inno ; dossier d'une autre édition refusé |
| `.erp-produit` | Marqueur de l'édition, non assimilé à une autorisation | Nettoyage ciblé ; ne rend pas propriétaires les fichiers inconnus |
| `journaux-service/ERP-OHADA-<Édition>*` | WinSW de cette édition | Inventoriés et sauvegardés avant retrait confirmé |
| `_internal/{apps,erp,django}/**/__pycache__/*.pyc` | Caches générés du programme | Même nettoyage ciblé ; aucun effacement récursif générique |
| `ProgramData/ERP-OHADA/<Édition>` | Base SQLite, configuration, mémoire d'essai, journaux | Liste explicite de noms connus, archive vérifiée, confirmation |
| `sauvegardes/erp-*` | Sauvegardes de l'ERP | Inventoriées avant effacement ; une archive extérieure reste conservée |
| `dossiers-simulation/` | Dossiers fictifs gérés par l'ERP | Extensions gérées seulement ; autres fichiers conservés |
| Base SQL Server, `.mdf/.ldf`, chemins SQLite externes | Ressources potentiellement partagées ou hébergées ailleurs | Jamais supprimés par cet outil ; aucune instruction SQL |
| Dossier partagé des agences / copie externe de sauvegarde | Hors des deux racines | Jamais parcouru ni effacé |
| Autre édition, parents `ERP-OHADA`, `ProgramData`, `Program Files` | Partagés | Jamais supprimés comme un ensemble |
| Service `ERP-OHADA-<Édition>` et règle au port de l'édition | WinSW / Inno | Arrêt et retrait standard ; processus encore actif bloque le nettoyage |
| Raccourcis Inno (menu, bureau, démarrage commun) | Inno pour cette édition | Retirés par Inno |
| Ancien `.bat` de démarrage dans un profil AppData | Créé à la demande par le programme | Profils non parcourus ; contrôle manuel à prévoir, ne pas annoncer leur nettoyage |
| Clé de désinstallation Inno | Inno, AppId par édition | Gérée par le désinstallateur |
| `HKCU/Software/ERP-OHADA`, valeur `Essai` | Mémoire historique commune aux éditions | Conservée et signalée, pour ne pas effacer celle d'une autre édition |
| Tâches planifiées | Aucune création trouvée dans les scripts relus | Pas de suppression générique de tâches Windows |
| Fichiers utilisateurs inconnus / liens / jonctions / liens durs | Attribution non sûre | Préservés, chemin et raison affichés |

Les anciennes données sans marqueur ne sont candidates que sous le chemin standard explicitement nommé
`ERP-OHADA/<Édition>` ; la liste blanche reste requise. Un marqueur d'une autre édition empêche cette reprise.
Une base SQLite est contrôlée en lecture seule avant sauvegarde ; l'outil refuse une archive dans les dossiers
à supprimer, une archive différente/altérée, un inventaire modifié ou une collision du journal de suppression.
La suppression n'est jamais déclenchée en silence. Un défaut sur un fichier produit un rapport à côté de
la sauvegarde, avec chemins et raisons. Des inconnus conservés peuvent laisser un dossier non vide : cela
doit être annoncé, sans prétendre à une absence de résidus universelle.

## Essais

12 scénarios ciblés exécutés après séparation explicite des autorisations sur dossiers fictifs : autorisation/refus des éditions, machines, dates et codes seuls,
contrôle embarqué, sauvegarde relue, absence de confirmation, liens, collisions, modification après inventaire,
fichiers inconnus, autre édition et parents partagés préservés. Journaux locaux dans `/workspace/INSTALLATION_P0_CIBLE.log`.
Les dates et durées finales de la suite complète sont ajoutées après exécution, pas anticipées.
Première version locale : 555 tests en 427,678 s, OK (4 ignorés). Après la consigne6536570880, autorisation distincte .erpinst et émission propriétaire ajoutées : 12 ciblés OK en 0,200 s (émission CLI depuis coffre chiffré comprise) ; nouvelle suite complète : **556 tests en 352,712 s, OK (4 ignorés SQLite)**. Ne pas attribuer le résultat de l’ancienne version à ces nouveaux ajouts.

La CI compile les outils avec la même identité, teste leurs refus, puis installe/démarre/met à jour/désinstalle
les deux éditions. Elle vérifie réellement le refus sans autorisation avant et après désinstallation et inspecte
les répertoires après nettoyage de données fictives. Les paquets ordinaires de ce lot sont nommés
`ESSAI-IDENTITE-FICTIVE` ; ils ne sont pas personnalisés avec l'identité du propriétaire et ne doivent pas être
livrés comme tels. Avec un public réel fourni au workflow, les essais qui nécessitent sa signature privée sont
explicitement ignorés plutôt que fabriqués ; la vraie personnalisation reste à finaliser séparément.

La recette de l'écran compilé ouvre une vraie fenêtre Tk, invoque son bouton et exécute la sauvegarde/relecture/
suppression sur ses propres fichiers temporaires. Les réponses aux dialogues sont simulées. Elle n'autorise
jamais un chemin de société en mode recette. Les résultats ne sont acquis qu'après succès effectif Windows.
Coexistence des deux services sur un même PC, permissions de plusieurs profils, Windows 10/11 distincts et
réseau physiquement déconnecté restent des recettes à nommer séparément ; aucune certification générale.

### Correction issue de la première recette Windows

Run41182218496 : Linux/SQL et activation compilée réussis, mais la vraie fenêtre de nettoyage échoue sur
les deux éditions avec WinError32 (fichier SQLite encore ouvert). Le contexte transactionnel d'une connexion
SQLite ne ferme pas le fichier. Le contrôle de sauvegarde et la fixture GUI utilisent maintenant
`contextlib.closing` ; la recette vérifie aussi explicitement la fermeture avant effacement.
12 tests ciblés locaux du correctif : OK, 0,075 s. La nouvelle suite complète locale n'a pas démarré : les
sockets de boucle locale sont interdites par le bac à sable ; le résultat de 556 tests précédent ne lui est
pas réattribué. La CI du nouveau commit doit revalider la suite et les deux outils Windows avant succès.

La CI41189566461 a ensuite réussi les suites Linux et SQL Server et les deux vraies fenêtres de nettoyage.
La recette d'installation reste toutefois en attente depuis plus de dix minutes sur les deux éditions. Une
validation d'assistant pouvait ouvrir un MsgBox lors d'un appel silencieux : le mode silencieux passe maintenant
directement au contrôle obligatoire de PrepareToInstall, sans dialogue ; le contrôle n'est jamais désactivé.
Un échec de marquage devient fatal au lieu d'ouvrir une boîte de dialogue. Les processus de recette ont une
limite de quatre minutes avec journaux distincts ; le job Windows est borné à 35 minutes et conserve ses
diagnostics même en échec. Une réinstallation autorisée est maintenant éprouvée après le refus sans autorisation.
Ce nouveau parcours doit encore réussir en CI avant d'être présenté comme validé.


## Émission propriétaire et activation unifiée

Le générateur garde ses deux modules. Le code autonome reste disponible sans société ni mot de passe. Le bouton « Autoriser une installation (.erpinst)… » utilise le coffre existant déverrouillé une seule fois, le code matériel affiché par l’installateur et une échéance explicitement choisie. Il ne génère pas de nouvelle paire. Console :

```powershell
ERP-OHADA-Licences.exe autoriser-installation --cle D:\Emission\coffre.dat --code T-AAAA-AAAA-AAAA-AAAA --jusqu-au 2026-12-31 --sortie D:\Emission
```

Le client ne propose plus de sélection de parametres.dat. Le fichier de licence ou la clé texte passent toujours par le moteur existant. Le Hardware ID affiché est celui du serveur, avec bouton copier. Les contrôles actuels et l’identifiant historique sont conservés.

L’agrégation de plusieurs identifiants, la preuve TPM, les procédures de transfert/réactivation et le key_id dans les **anciens formats de licence** ne sont pas annoncés comme livrés. Leur introduction demande une migration explicite et des tests d’anciennes licences. Le key_id des nouvelles autorisations est déjà vérifié contre la clé publique qui a réellement signé ; aucune rotation de l’identité du propriétaire n’est effectuée. La recette d’activation .erplic seul des deux vrais EXE est acquise dans #23 ; la recette est maintenant étendue à la clé texte dans ce lot (succès à confirmer en CI). Le serveur multi-postes et la coexistence réelle de deux services restent dans la suite du programme.
