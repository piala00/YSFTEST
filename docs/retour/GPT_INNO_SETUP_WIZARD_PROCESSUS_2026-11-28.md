# Recette interactive du wizard Inno Setup — 28/11/2026

## Échec observé dans le run #844

Run : https://github.com/piala00/YSFTEST/actions/runs/46123070854

Les deux jobs Windows (Commerce et Transport) ont compilé l'installateur Inno Setup, puis échoué uniquement dans le nouveau parcours interactif :

`Fenêtre principale Inno Setup introuvable pour le processus 8988` (Commerce) et `...` pour le PID 6644 (Transport).

Les étapes de compilation native, démarrage de l'ERP, clôture native Transport, outil de nettoyage, SQL Server (deux shards), Linux, licences, guichet et simulation ont réussi dans ce run. L'échec n'est donc pas un échec de compilation ISCC ni du bouton lui-même : le test n'a pas atteint l'interface.

Les artefacts de diagnostic initiaux contenaient uniquement le PID du lanceur et l'erreur. Ils ne conservaient ni l'arbre des processus ni le journal Inno Setup, ce qui limitait l'analyse.

## Analyse de cause

Le script précédent cherchait une fenêtre visible appartenant strictement au PID retourné par `Start-Process`. Inno Setup documente que, lorsque `UseSetupLdr=yes` (valeur par défaut), le programme Setup est copié dans le répertoire TEMP et exécuté depuis ce répertoire : https://jrsoftware.org/inno-setup/documentation/topic_setup_usesetupldr.htm

Cela rend plausible une séparation entre le lanceur initial et le processus qui porte la fenêtre du wizard. Les journaux #844 confirment que la fenêtre n'est pas rattachée au PID initial, mais ne contiennent pas encore l'arbre de processus permettant d'affirmer quel PID héberge le wizard. Cette distinction reste explicitement une hypothèse à confirmer par la prochaine recette.

Références Win32 :
- `EnumWindows` énumère les fenêtres de premier niveau : https://learn.microsoft.com/en-us/windows/desktop/api/winuser/nf-winuser-enumwindows
- `GetWindowThreadProcessId` renvoie le PID qui a créé une fenêtre : https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindowthreadprocessid

## Correctif publié

Le script de recette suit maintenant l'arbre Win32 des processus à partir du lanceur :
- capture de `Win32_Process.ProcessId` et `ParentProcessId` via CIM ;
- calcul transitif des descendants, y compris après la sortie du lanceur initial ;
- recherche de la fenêtre parmi tous les PID suivis ;
- priorité à la classe de fenêtre Inno Setup `TWizardForm` ;
- repli limité à une fenêtre `TWizardForm` visible dont le titre contient `ERP OHADA`, dans le runner isolé qui ne lance qu'un installateur ;
- en cas d'échec, conservation des PID, noms, chemins exécutables, fenêtres visibles et chemin du journal Setup.

Le nettoyage final tue l'arbre de processus suivi, pas seulement le lanceur. Le workflow archive désormais aussi `wizard-copie-code-*.log`.

Le test ne désactive ni l'UAC, ni la signature, ni les contrôles de licence. Il n'installe rien : il vérifie uniquement le wizard et le presse-papiers avec l'identité fictive CI.

## Validation attendue

- Les tests unitaires de contrat vérifient le suivi des processus et l'archivage du journal.
- La prochaine CI Windows doit confirmer que le wizard est trouvé dans l'arbre du lanceur ou via sa classe/titre produit.
- Après découverte de la page d'autorisation, le test doit cliquer le bouton, vérifier `Code copié !`, lire le presse-papiers et comparer exactement le texte au code affiché.
- Les deux éditions doivent produire chacune un rapport JSON `resultat=OK`.

Aucune fusion, aucun déploiement, aucune donnée réelle, aucune clé privée publiée.
