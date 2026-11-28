# Diagnostic et correction Inno Setup — 28/11/2026

## Échec observé dans GitHub Actions #818

Run : https://github.com/piala00/YSFTEST/actions/runs/46115965026

Les deux matrices Windows ont échoué au même step « Fabriquer l'installateur (Inno Setup) » :
- Commerce, job 140889760640 ;
- Transport, job 140889760717.

Erreur exacte du compilateur ISCC, ligne 361 de `deploy/installateur/erp_ohada.iss` :

```text
Unknown identifier 'SETFOCUS'
Compile aborted.
```

Les étapes précédentes de compilation native et de démarrage des exécutables avaient réussi. Les jobs Linux, SQL Server shard 0/1, guichet, licences et activation compilée ont réussi. Les recettes d'installation Inno Setup ont été ignorées à la suite de l'échec de compilation.

## Cause racine

Le script appelait `ChampCodeInstallation.SetFocus`. Or la référence officielle des classes Pascal Script Inno Setup décrit `TWinControl` avec `Handle`, `CanFocus`, `Focused`, etc., mais ne fournit pas de méthode `SetFocus`.

La fonction `SetFocus(HWND)` est une API Win32 exportée par `user32.dll`. Inno Setup permet d'appeler des fonctions DLL avec une déclaration `external 'Nom@DLL stdcall'`.

Sources consultées :
- Inno Setup, Pascal Scripting — Support Classes Reference : https://jrsoftware.org/inno-setup/documentation/topic_scriptclasses.htm
- Inno Setup, Pascal Scripting — Using DLLs : https://documentation.help/Inno-Setup/topic_scriptdll.htm
- Microsoft Learn, SetFocus : https://learn.microsoft.com/fr-fr/windows/win32/api/winuser/nf-winuser-setfocus
- Microsoft Learn, GetFocus : https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getfocus

## Correction publiée

Le script déclare désormais des alias Pascal Script vers les API Win32 :

```pascal
function DefinirFocus(Fenetre: HWND): HWND;
  external 'SetFocus@user32.dll stdcall';
function ObtenirFocus: HWND;
  external 'GetFocus@user32.dll stdcall';
```

Le bouton appelle `DefinirFocus(ChampCodeInstallation.Handle)`, puis vérifie que `ObtenirFocus()` renvoie bien le handle du champ avant d'envoyer `EM_SETSEL` et `WM_COPY`. Le chemin d'échec utilise également l'API Win32. Aucun appel de méthode `.SetFocus` ne reste dans le script.

La fonction Win32 retourne le handle qui avait précédemment le focus, pas un booléen de succès ; la vérification du focus courant via `GetFocus` évite donc d'interpréter incorrectement cette valeur de retour.

## Tests et validation

Le test `tests/test_installateur_copie_code.py` vérifie :
- la déclaration des fonctions externes `SetFocus` et `GetFocus` ;
- leur appel avec le handle du champ ;
- l'absence de `ChampCodeInstallation.SetFocus` ;
- le maintien du contrat de copie vérifiée et du repli Ctrl+C.

Le commit de correction du script est `cd8413ab4af2a5a8090cf2030b138660b5dacc0b` et celui du test est `78e6da88896ccecdd84819538e126c0b966692bf`.

Le workflow de contrôle #824 a été déclenché pour ces changements. La compilation Inno Setup des deux éditions et le parcours d'installation doivent être confirmés par ses journaux avant de déclarer le correctif validé.

Aucune fusion, aucun déploiement, aucune identité réelle ni donnée réelle.
