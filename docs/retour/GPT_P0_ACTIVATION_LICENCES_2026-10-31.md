# Codex — activation des licences — 31 octobre 2026

Demandes : issue #1, commentaires 6536186700 et 6536201349. Parent : fdb57a3 (#22).
Réutilisation des formats, coffre propriétaire et distribution protégée de #13/#21. Aucune nouvelle paire réelle,
aucune conversion des licences existantes, aucune fusion ou modification de production.

## Cause vérifiée

`apps/licences/cle_editeur.py:CLES` est vide. Dans le programme compilé, `cles_publiques()` renvoie alors une liste
vide, sans lire une autorité remplaçable à côté de l'exécutable. `verifier_fichier_public()` refuse donc le dépôt avec
le message rapporté. `parametres.dat` est un conteneur PUBLIC : six octets `ERPID\x01` et 32 octets Ed25519.
Son import ne constitue pas une autorisation de faire confiance à un nouvel éditeur. La signature existante
et les contrôles de machine, édition, société, rôle/site et référence d'installation restent actifs.

L'incident n'est pas corrigé en recréant des clés ni en acceptant arbitrairement le fichier fourni. Une licence
signée par l'identité du propriétaire exige cette identité publique dans le programme personnalisé.

## Correctif

- `personnaliser_identite.py` intègre le public existant avant Cython. Empreinte SHA-256 obligatoire et comparée
  à celle autorisée du guide propriétaire ; ancien public texte et nouveau conteneur binaire acceptés.
  Coffre privé, fichier invalide, empreinte différente et remplacement implicite d'une identité refusés.
  Écriture atomique ; pas de génération de clé et pas d'altération des fichiers de licences émis.
- Une compilation commerciale sans identité échoue désormais avant Cython et avant PyInstaller.
  Une version sans éditeur n'est possible que par choix explicite `--version-essai` puis `ERP_VERSION_ESSAI=1`.
  La documentation du paquet contient `IDENTITE-DISTRIBUTION.json` avec son mode et ses empreintes publiques.
- Le workflow manuel peut recevoir le public base64 et l'empreinte autorisée. Ces valeurs publiques ne sont
  jamais une clé privée. Sans ces valeurs, les contrôles ordinaires construisent explicitement une version d'essai.
- L'écran explique le refus avant le dépôt, et présente le fichier public comme une vérification facultative.
  Dans un programme personnalisé, le `.erplic` seul suffit déjà ; ce parcours est réutilisé et éprouvé.
- Un nouveau dépôt depuis l'écran ou le code d'activation refuse une licence déjà échue. L'historique existant
  et la lecture des anciennes licences ne sont pas effacés : leurs règles de grâce/consultation sont conservées.

## Procédure de personnalisation dans une copie de compilation

Avec le `parametres.dat` existant et l'empreinte autorisée obtenue dans le guide propriétaire :

```powershell
python deploy/executable/personnaliser_identite.py --publique "D:\Emission\parametres.dat" --empreinte "<SHA256 autorisé>"
python deploy/executable/compiler_natif.py . --supprimer-sources
python -m PyInstaller deploy/executable/erp_ohada.spec --noconfirm --workpath build --distpath dist
```

Ne jamais passer `coffre.dat`, changer l'autorité pour masquer une erreur ou personnaliser après compilation.
Une vraie rotation future doit conserver les anciennes identités autorisées selon une procédure distincte.

## Essais et limites

18 tests ciblés exécutés localement le 31 octobre : OK, 1,981 s. Ils couvrent la personnalisation, les refus,
les deux éditions, le dépôt sans fichier public, la relecture en base et la conservation de l'historique.
Le premier lancement des nouveaux tests comportait deux erreurs de nom de paramètre dans le test ; corrigées
avant ce résultat. Aucun résultat de ce premier lancement n'est présenté comme une régression de l'ERP.
Le refus réel du compilateur sans identité a aussi été exécuté (code de sortie 1, message explicite).
Suite complète locale ensuite exécutée : **544 tests en 463,364 s, OK (4 ignorés sous SQLite)**.
Journal : `/workspace/ACTIVATION_P0_COMPLET.log`. Les tests SQL Server et Windows restent distincts.

Une recette CI distincte prépare une identité FICTIVE dans le répertoire temporaire du runner Windows, compile
les deux ERP, les lance réellement, essaie de faux signataires, mauvaise édition/machine/installation et échéance,
puis active un fichier valide sans public supplémentaire et relance un nouveau processus pour vérifier la
persistance. Seuls résultats JSON et journaux sont publiés ; ni le privé fictif ni ces exécutables ne sont distribués.
Les résultats Windows ne sont acquis qu'après le succès effectif de ce travail.

La clé publique réelle n'a pas été fournie (le propriétaire a demandé de poursuivre sans). Cela ne bloque pas
ces correctifs et tests, mais empêche d'annoncer une distribution commerciale personnalisée ou l'activation
de `LIC-2026-0002-OTL.erplic` sur son installation. Aucun succès sur son PC n'est revendiqué.
Un runner Windows Server ne prouve pas des essais Windows 10 et Windows 11 séparés.

Le contrôle de chaque nouvelle installation et le nettoyage complet relèvent du lot installateur suivant ;
le code court autonome 4×6 reste une référence, pas une preuve d'autorisation de l'éditeur.
