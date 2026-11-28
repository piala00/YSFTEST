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

## Complément — PID réel de la fenêtre

Après la recherche du wizard, le script récupère aussi le PID propriétaire du HWND via `GetWindowThreadProcessId`. Ce PID est ajouté à la liste de nettoyage, y compris lorsque la fenêtre a été trouvée par le repli global sur la classe `TWizardForm` et le titre `ERP OHADA`. Le repli global est limité au runner CI isolé, qui ne lance qu'un seul installateur à la fois.

Le retour de `Get-InstallerProcessIds` est un tableau d'entiers directement énuméré par PowerShell ; le script évite un tableau imbriqué. Le nettoyage couvre l'arbre du lanceur et le PID propriétaire du wizard.

Référence Microsoft : https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getwindowthreadprocessid


## Échec #863 après copie réellement vérifiée

Dans les deux jobs Windows du run #863, le script a atteint la page d'autorisation, cliqué « Copier le code », lu le presse-papiers et comparé exactement sa valeur au code affiché. Les journaux contiennent chacun la ligne « Copie interactive vérifiée ... », puis GitHub marque immédiatement le step en échec avec le code 1.

Le script terminait son bloc `finally` par l'appel natif `taskkill.exe /F /T`. Une course est possible entre l'instantané des processus et leur arrêt : si Setup s'est déjà fermé, `taskkill.exe` peut retourner un code non nul. GitHub documente que son shell intégré `pwsh` ajoute en fin de step `exit $LASTEXITCODE`; Microsoft documente que cette variable conserve le code de sortie du dernier programme natif. Cela explique l'échec après la preuve fonctionnelle, sans invalider la comparaison du presse-papiers.

Correctif : remplacement de `taskkill.exe` par le cmdlet `Stop-Process`, gestion de la disparition concurrente des processus, exclusion du PID du shell courant, et remise à zéro explicite de `$global:LASTEXITCODE` en fin de nettoyage. Une erreur d'arrêt reste propagée si le processus est toujours vivant.

Références officielles :
- GitHub Actions — shells intégrés et propagation de `LASTEXITCODE` : https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idstepsshell
- Microsoft Learn — `$LASTEXITCODE` : https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_automatic_variables
- Microsoft Learn — erreurs des programmes natifs : https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_error_handling

La preuve interactive #863 est positive pour le clic et l'égalité du presse-papiers dans les deux éditions ; le statut du job restait négatif à cause du code de sortie final. La nouvelle CI doit confirmer le correctif du nettoyage.
