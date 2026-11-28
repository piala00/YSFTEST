param(
    [Parameter(Mandatory = $true)]
    [string]$Installateur,
    [Parameter(Mandatory = $true)]
    [ValidateSet("transport", "commerce")]
    [string]$Edition,
    [Parameter(Mandatory = $true)]
    [string]$Rapport
)

$ErrorActionPreference = "Stop"
$Installateur = (Resolve-Path -LiteralPath $Installateur).Path
$journal = Join-Path $env:RUNNER_TEMP "wizard-copie-code-$Edition.log"
$processus = $null
$wizard = [IntPtr]::Zero
$processusSnapshot = @()
$processIds = @()
$pidFenetre = 0
$preuve = [ordered]@{
    edition = $Edition
    resultat = "ECHEC"
    bouton = $null
    code_longueur = 0
    code_sha256 = $null
    presse_papiers_verifie = $false
    date_utc = [DateTime]::UtcNow.ToString("o")
}

Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;

public sealed class InnoWindowInfo
{
    public IntPtr Handle { get; set; }
    public string Text { get; set; }
    public string ClassName { get; set; }
    public bool Visible { get; set; }
    public bool Enabled { get; set; }
    public int ProcessId { get; set; }
    public int Left { get; set; }
    public int Top { get; set; }
    public int Right { get; set; }
    public int Bottom { get; set; }
}

public static class InnoUiNative
{
    [StructLayout(LayoutKind.Sequential)]
    private struct NativeRect
    {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    private static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);

    [DllImport("user32.dll")]
    private static extern bool EnumChildWindows(IntPtr parent, EnumWindowsProc callback, IntPtr lParam);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool GetWindowRect(IntPtr hWnd, out NativeRect rect);

    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool IsWindowEnabled(IntPtr hWnd);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int GetWindowTextLength(IntPtr hWnd);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int maxCount);

    [DllImport("user32.dll", CharSet = CharSet.Unicode)]
    private static extern int GetClassName(IntPtr hWnd, StringBuilder className, int maxCount);

    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern IntPtr SetActiveWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern IntPtr SetFocus(IntPtr hWnd);

    [DllImport("user32.dll")]
    private static extern IntPtr SendMessage(IntPtr hWnd, uint message, IntPtr wParam, IntPtr lParam);

    private const uint BM_CLICK = 0x00F5;
    private const uint LB_GETCOUNT = 0x018B;
    private const uint LB_GETITEMHEIGHT = 0x01A1;
    private const uint LB_GETCURSEL = 0x0188;
    private const uint WM_LBUTTONDOWN = 0x0201;
    private const uint WM_LBUTTONUP = 0x0202;

    public static string Text(IntPtr hWnd)
    {
        int length = GetWindowTextLength(hWnd);
        StringBuilder value = new StringBuilder(Math.Max(length + 2, 256));
        GetWindowText(hWnd, value, value.Capacity);
        return value.ToString();
    }

    private static string ClassName(IntPtr hWnd)
    {
        StringBuilder value = new StringBuilder(256);
        GetClassName(hWnd, value, value.Capacity);
        return value.ToString();
    }

    public static int ProcessIdForWindow(IntPtr hWnd)
    {
        uint owner;
        GetWindowThreadProcessId(hWnd, out owner);
        return (int)owner;
    }

    public static InnoWindowInfo[] WindowsForProcesses(int[] processIds)
    {
        HashSet<int> owners = new HashSet<int>(processIds ?? new int[0]);
        List<InnoWindowInfo> result = new List<InnoWindowInfo>();
        EnumWindowsProc callback = delegate(IntPtr hWnd, IntPtr lParam)
        {
            uint owner;
            GetWindowThreadProcessId(hWnd, out owner);
            if (owners.Count == 0 || owners.Contains((int)owner))
            {
                NativeRect rect;
                GetWindowRect(hWnd, out rect);
                result.Add(new InnoWindowInfo {
                    Handle = hWnd,
                    ProcessId = (int)owner,
                    Text = Text(hWnd),
                    ClassName = ClassName(hWnd),
                    Visible = IsWindowVisible(hWnd),
                    Enabled = IsWindowEnabled(hWnd),
                    Left = rect.Left,
                    Top = rect.Top,
                    Right = rect.Right,
                    Bottom = rect.Bottom
                });
            }
            return true;
        };
        EnumWindows(callback, IntPtr.Zero);
        GC.KeepAlive(callback);
        return result.ToArray();
    }

    public static IntPtr FindMainWindow(int[] processIds)
    {
        // Ne jamais confondre le wizard avec une boîte modale, un dialogue UAC
        // ou une fenêtre auxiliaire appartenant au processus Setup.
        foreach (InnoWindowInfo window in WindowsForProcesses(processIds))
        {
            if (window.Visible && window.ClassName == "TWizardForm")
                return window.Handle;
        }

        // UseSetupLdr peut détacher le Setup extrait de TEMP du lanceur initial.
        // Le repli global reste strict : classe TWizardForm et titre de ce produit.
        foreach (InnoWindowInfo window in WindowsForProcesses(new int[0]))
        {
            if (window.Visible && window.ClassName == "TWizardForm" &&
                window.Text.IndexOf("ERP OHADA", StringComparison.OrdinalIgnoreCase) >= 0)
                return window.Handle;
        }
        return IntPtr.Zero;
    }

    public static InnoWindowInfo[] Children(IntPtr parent)
    {
        List<InnoWindowInfo> result = new List<InnoWindowInfo>();
        EnumWindowsProc callback = delegate(IntPtr hWnd, IntPtr lParam)
        {
            NativeRect rect;
            GetWindowRect(hWnd, out rect);
            result.Add(new InnoWindowInfo {
                Handle = hWnd,
                ProcessId = ProcessIdForWindow(hWnd),
                Text = Text(hWnd),
                ClassName = ClassName(hWnd),
                Visible = IsWindowVisible(hWnd),
                Enabled = IsWindowEnabled(hWnd),
                Left = rect.Left,
                Top = rect.Top,
                Right = rect.Right,
                Bottom = rect.Bottom
            });
            return true;
        };
        EnumChildWindows(parent, callback, IntPtr.Zero);
        GC.KeepAlive(callback);
        return result.ToArray();
    }

    public static void ClickButton(IntPtr parent, IntPtr button)
    {
        SetForegroundWindow(parent);
        SetActiveWindow(parent);
        SendMessage(button, BM_CLICK, IntPtr.Zero, IntPtr.Zero);
    }

    public static int ListCount(IntPtr listBox)
    {
        return (int)SendMessage(listBox, LB_GETCOUNT, IntPtr.Zero, IntPtr.Zero).ToInt64();
    }

    public static int ClickListItem(IntPtr parent, IntPtr listBox, int index)
    {
        int count = ListCount(listBox);
        if (index < 0 || index >= count)
            return -1;

        SetForegroundWindow(parent);
        SetActiveWindow(parent);
        SetFocus(listBox);

        int height = (int)SendMessage(
            listBox, LB_GETITEMHEIGHT, new IntPtr(index), IntPtr.Zero).ToInt64();
        if (height <= 0)
            height = 24;

        int x = 12;
        int y = index * height + Math.Max(2, height / 2);
        IntPtr coordinates = new IntPtr((y << 16) | (x & 0xFFFF));
        SendMessage(listBox, WM_LBUTTONDOWN, new IntPtr(1), coordinates);
        SendMessage(listBox, WM_LBUTTONUP, IntPtr.Zero, coordinates);
        return (int)SendMessage(listBox, LB_GETCURSEL, IntPtr.Zero, IntPtr.Zero).ToInt64();
    }
}
'@

function Get-VisibleControls {
    @([InnoUiNative]::Children($wizard) | Where-Object { $_.Visible })
}

function Find-Control([string]$Pattern) {
    Get-VisibleControls | Where-Object { $_.Text -match $Pattern } | Select-Object -First 1
}

function Find-NextButtonByPosition {
    # Les libellés proviennent des fichiers de langue Inno Setup. Si GetWindowText
    # ne les restitue pas (contrôle VCL owner-drawn), le bouton Suivant reste le
    # deuxième bouton actif en partant de la droite sur la rangée inférieure :
    # Annuler est à droite, Retour à gauche. On ne clique jamais sur une position
    # arbitraire sans avoir identifié cette rangée et au moins deux boutons.
    $boutons = @(Get-VisibleControls | Where-Object {
        $_.Enabled -and $_.ClassName -match 'Button'
    })
    if ($boutons.Count -lt 2) { return $null }

    $bas = ($boutons | Measure-Object -Property Bottom -Maximum).Maximum
    $ligne = @($boutons | Where-Object { $_.Bottom -ge ($bas - 32) })
    $ordonnes = @($ligne | Sort-Object -Property Right -Descending)
    if ($ordonnes.Count -lt 2) { return $null }
    return $ordonnes[1]
}

function Get-ControlSnapshot {
    @([InnoUiNative]::Children($wizard) | ForEach-Object {
        $texte = $_.Text
        if ($_.ClassName -match 'Edit' -and $texte) { $texte = '[champ texte masqué]' }
        [pscustomobject]@{
            classe = $_.ClassName
            texte = $texte
            visible = $_.Visible
            actif = $_.Enabled
            gauche = $_.Left
            haut = $_.Top
            droite = $_.Right
            bas = $_.Bottom
            pid = $_.ProcessId
        }
    })
}

function Get-InstallerProcessSnapshot {
    try {
        return @(Get-CimInstance -ClassName Win32_Process -ErrorAction Stop |
            Select-Object ProcessId, ParentProcessId, Name, ExecutablePath)
    }
    catch {
        # Le PID initial reste exploitable si CIM/WMI est restreint. Le repli
        # global TWizardForm/ERP OHADA est alors utilisé par FindMainWindow.
        return @()
    }
}

function Get-InstallerProcessIds([int]$RootProcessId, [object[]]$Snapshot) {
    $ids = [System.Collections.Generic.HashSet[int]]::new()
    [void]$ids.Add($RootProcessId)
    $changed = $true
    while ($changed) {
        $changed = $false
        foreach ($item in $Snapshot) {
            $pidEnfant = [int]$item.ProcessId
            $pidParent = [int]$item.ParentProcessId
            if ($ids.Contains($pidParent) -and $ids.Add($pidEnfant)) {
                $changed = $true
            }
        }
    }
    return [int[]]@($ids)
}

function Wait-Control([string]$Pattern, [int]$TimeoutSeconds = 12) {
    $limite = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    do {
        $controle = Find-Control $Pattern
        if ($null -ne $controle) { return $controle }
        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $limite)
    return $null
}

function Click-Next {
    $suivant = Wait-Control '^\s*&?(Suivant|Next)\s*>?\s*

try {
    if (-not (Test-Path -LiteralPath $env:RUNNER_TEMP)) {
        throw "RUNNER_TEMP indisponible."
    }

    $processus = Start-Process -FilePath $Installateur -ArgumentList @("/LOG=$journal") -PassThru
    $limiteFenetre = [DateTime]::UtcNow.AddSeconds(60)
    do {
        # Avec le Setup Loader, l'interface peut appartenir à la copie temporaire
        # lancée depuis TEMP, et non au PID du lanceur retourné par Start-Process.
        # On suit donc l'arbre des processus à chaque sondage, même si le lanceur
        # initial s'est déjà terminé.
        $processusSnapshot = @(Get-InstallerProcessSnapshot)
        $processIds = @(Get-InstallerProcessIds -RootProcessId $processus.Id -Snapshot $processusSnapshot)
        $wizard = [InnoUiNative]::FindMainWindow([int[]]$processIds)
        if ($wizard -ne [IntPtr]::Zero) { break }
        Start-Sleep -Milliseconds 300
    } while ([DateTime]::UtcNow -lt $limiteFenetre)

    if ($wizard -eq [IntPtr]::Zero) {
        $fenetres = @([InnoUiNative]::WindowsForProcesses([int[]]$processIds) |
            Where-Object { $_.Visible } |
            ForEach-Object {
                [pscustomobject]@{
                    pid = $_.ProcessId
                    classe = $_.ClassName
                    titre = $_.Text
                    actif = $_.Enabled
                }
            })
        $preuve.processus = @($processusSnapshot |
            Where-Object { $processIds -contains [int]$_.ProcessId } |
            Select-Object ProcessId, ParentProcessId, Name, ExecutablePath)
        $preuve.fenetres = $fenetres
        $preuve.journal_setup = $journal
        throw "Fenêtre principale Inno Setup introuvable après suivi du lanceur et de ses descendants (PID suivis : $($processIds -join ', '))."
    }

    $pidFenetre = [InnoUiNative]::ProcessIdForWindow($wizard)
    if ($pidFenetre -gt 0 -and $processIds -notcontains $pidFenetre) {
        $processIds += $pidFenetre
    }

    [InnoUiNative]::SetForegroundWindow($wizard) | Out-Null
    [InnoUiNative]::SetActiveWindow($wizard) | Out-Null

    $pageAutorisationAtteinte = $false
    for ($page = 0; $page -lt 12; $page++) {
        $copier = Find-Control '^\s*Copier le code\s*$'
        if ($null -ne $copier) {
            $pageAutorisationAtteinte = $true
            break
        }

        # Page « Méthode d'installation » : le premier choix est le .erpinst.
        # TInputOptionWizardPage est un TNewCheckListBox owner-drawn ; ses lignes
        # ne sont pas des HWND séparés. On clique donc réellement la première ligne.
        $listes = @(Get-VisibleControls | Where-Object {
            $_.ClassName -match 'CheckListBox|ListBox' -and
            [InnoUiNative]::ListCount($_.Handle) -eq 3
        })
        if ($listes.Count -gt 0) {
            $selection = [InnoUiNative]::ClickListItem($wizard, $listes[0].Handle, 0)
            Start-Sleep -Milliseconds 250
        }

        # Accepter le CLUF si cette page intégrée apparaît avant la page personnalisée.
        $acceptation = Find-Control '^(?i).*J''accepte.*'
        if ($null -ne $acceptation -and $acceptation.Enabled) {
            [InnoUiNative]::ClickButton($wizard, $acceptation.Handle)
            Start-Sleep -Milliseconds 200
        }

        Click-Next
    }

    if (-not $pageAutorisationAtteinte) {
        $diagnostic = Get-VisibleControls | ForEach-Object {
            $texte = $_.Text
            if ($_.ClassName -match 'Edit' -and $texte) { $texte = '[champ texte masqué]' }
            [pscustomobject]@{ classe = $_.ClassName; texte = $texte; actif = $_.Enabled }
        }
        throw ("Page d'autorisation non atteinte. Contrôles visibles : " +
            ($diagnostic | ConvertTo-Json -Compress -Depth 3))
    }

    $champ = Get-VisibleControls | Where-Object {
        $_.ClassName -match 'Edit' -and -not [string]::IsNullOrWhiteSpace($_.Text)
    } | Select-Object -First 1
    if ($null -eq $champ) {
        throw "Le champ en lecture seule du code d'installation est vide ou introuvable."
    }

    $code = $champ.Text.Trim()
    if ($code.Length -lt 8 -or $code.Length -gt 64) {
        throw "Longueur inattendue du code d'installation ($($code.Length))."
    }

    $copier = Wait-Control '^\s*Copier le code\s*$' 5
    if ($null -eq $copier -or -not $copier.Enabled) {
        throw "Bouton Copier le code absent ou désactivé."
    }

    [InnoUiNative]::ClickButton($wizard, $copier.Handle)
    Start-Sleep -Milliseconds 500
    $copierApres = Find-Control '^\s*Code copié\s*!\s*$'
    $pressePapiers = [string](Get-Clipboard -Raw -ErrorAction Stop)
    $pressePapiers = $pressePapiers.Trim()

    if ($null -eq $copierApres) {
        throw "Le bouton n'a pas affiché la confirmation « Code copié ! »."
    }
    if ($pressePapiers -cne $code) {
        throw "Le contenu du presse-papiers ne correspond pas exactement au code affiché."
    }

    $empreinte = [BitConverter]::ToString(
        [Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($code))
    ).Replace("-", "")

    $preuve.resultat = "OK"
    $preuve.bouton = $copierApres.Text
    $preuve.code_longueur = $code.Length
    $preuve.code_sha256 = $empreinte
    $preuve.presse_papiers_verifie = $true
    $preuve | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $Rapport -Encoding utf8
    Write-Output "Copie interactive vérifiée pour $Edition : longueur $($code.Length), empreinte SHA-256 $empreinte. Le code lui-même n'est pas journalisé."
}
catch {
    $preuve.erreur = $_.Exception.Message
    $preuve | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $Rapport -Encoding utf8
    Write-Error $_
    throw
}
finally {
    if ($null -ne $processus) {
        $nettoyageSnapshot = @(Get-InstallerProcessSnapshot)
        $idsArbre = @(Get-InstallerProcessIds -RootProcessId $processus.Id -Snapshot $nettoyageSnapshot)
        $nettoyageIds = @($processIds + $idsArbre) | Sort-Object -Unique
        foreach ($pidActuel in $nettoyageIds) {
            if (Get-Process -Id $pidActuel -ErrorAction SilentlyContinue) {
                & taskkill.exe /F /T /PID $pidActuel 2>$null | Out-Null
            }
        }
    }
}
 5
    $methode = "libelle"
    if ($null -eq $suivant) {
        $suivant = Find-NextButtonByPosition
        $methode = "rangée inférieure, deuxième bouton depuis la droite"
    }
    if ($null -eq $suivant -or -not $suivant.Enabled) {
        $preuve.fenetre = @{
            titre = [InnoUiNative]::Text($wizard)
            pid = [InnoUiNative]::ProcessIdForWindow($wizard)
            classe_attendue = "TWizardForm"
        }
        $preuve.controles_suivant = @(Get-ControlSnapshot)
        $preuve.journal_setup = $journal
        throw "Bouton Suivant introuvable ou désactivé. Contrôles visibles et géométrie ajoutés au rapport."
    }
    $preuve.navigation_suivant = $methode
    [InnoUiNative]::ClickButton($wizard, $suivant.Handle)
    Start-Sleep -Milliseconds 650
}

try {
    if (-not (Test-Path -LiteralPath $env:RUNNER_TEMP)) {
        throw "RUNNER_TEMP indisponible."
    }

    $processus = Start-Process -FilePath $Installateur -ArgumentList @("/LOG=$journal") -PassThru
    $limiteFenetre = [DateTime]::UtcNow.AddSeconds(60)
    do {
        # Avec le Setup Loader, l'interface peut appartenir à la copie temporaire
        # lancée depuis TEMP, et non au PID du lanceur retourné par Start-Process.
        # On suit donc l'arbre des processus à chaque sondage, même si le lanceur
        # initial s'est déjà terminé.
        $processusSnapshot = @(Get-InstallerProcessSnapshot)
        $processIds = @(Get-InstallerProcessIds -RootProcessId $processus.Id -Snapshot $processusSnapshot)
        $wizard = [InnoUiNative]::FindMainWindow([int[]]$processIds)
        if ($wizard -ne [IntPtr]::Zero) { break }
        Start-Sleep -Milliseconds 300
    } while ([DateTime]::UtcNow -lt $limiteFenetre)

    if ($wizard -eq [IntPtr]::Zero) {
        $fenetres = @([InnoUiNative]::WindowsForProcesses([int[]]$processIds) |
            Where-Object { $_.Visible } |
            ForEach-Object {
                [pscustomobject]@{
                    pid = $_.ProcessId
                    classe = $_.ClassName
                    titre = $_.Text
                    actif = $_.Enabled
                }
            })
        $preuve.processus = @($processusSnapshot |
            Where-Object { $processIds -contains [int]$_.ProcessId } |
            Select-Object ProcessId, ParentProcessId, Name, ExecutablePath)
        $preuve.fenetres = $fenetres
        $preuve.journal_setup = $journal
        throw "Fenêtre principale Inno Setup introuvable après suivi du lanceur et de ses descendants (PID suivis : $($processIds -join ', '))."
    }

    $pidFenetre = [InnoUiNative]::ProcessIdForWindow($wizard)
    if ($pidFenetre -gt 0 -and $processIds -notcontains $pidFenetre) {
        $processIds += $pidFenetre
    }

    [InnoUiNative]::SetForegroundWindow($wizard) | Out-Null
    [InnoUiNative]::SetActiveWindow($wizard) | Out-Null

    $pageAutorisationAtteinte = $false
    for ($page = 0; $page -lt 12; $page++) {
        $copier = Find-Control '^\s*Copier le code\s*$'
        if ($null -ne $copier) {
            $pageAutorisationAtteinte = $true
            break
        }

        # Page « Méthode d'installation » : le premier choix est le .erpinst.
        # TInputOptionWizardPage est un TNewCheckListBox owner-drawn ; ses lignes
        # ne sont pas des HWND séparés. On clique donc réellement la première ligne.
        $listes = @(Get-VisibleControls | Where-Object {
            $_.ClassName -match 'CheckListBox|ListBox' -and
            [InnoUiNative]::ListCount($_.Handle) -eq 3
        })
        if ($listes.Count -gt 0) {
            $selection = [InnoUiNative]::ClickListItem($wizard, $listes[0].Handle, 0)
            Start-Sleep -Milliseconds 250
        }

        # Accepter le CLUF si cette page intégrée apparaît avant la page personnalisée.
        $acceptation = Find-Control '^(?i).*J''accepte.*'
        if ($null -ne $acceptation -and $acceptation.Enabled) {
            [InnoUiNative]::ClickButton($wizard, $acceptation.Handle)
            Start-Sleep -Milliseconds 200
        }

        Click-Next
    }

    if (-not $pageAutorisationAtteinte) {
        $diagnostic = Get-VisibleControls | ForEach-Object {
            $texte = $_.Text
            if ($_.ClassName -match 'Edit' -and $texte) { $texte = '[champ texte masqué]' }
            [pscustomobject]@{ classe = $_.ClassName; texte = $texte; actif = $_.Enabled }
        }
        throw ("Page d'autorisation non atteinte. Contrôles visibles : " +
            ($diagnostic | ConvertTo-Json -Compress -Depth 3))
    }

    $champ = Get-VisibleControls | Where-Object {
        $_.ClassName -match 'Edit' -and -not [string]::IsNullOrWhiteSpace($_.Text)
    } | Select-Object -First 1
    if ($null -eq $champ) {
        throw "Le champ en lecture seule du code d'installation est vide ou introuvable."
    }

    $code = $champ.Text.Trim()
    if ($code.Length -lt 8 -or $code.Length -gt 64) {
        throw "Longueur inattendue du code d'installation ($($code.Length))."
    }

    $copier = Wait-Control '^\s*Copier le code\s*$' 5
    if ($null -eq $copier -or -not $copier.Enabled) {
        throw "Bouton Copier le code absent ou désactivé."
    }

    [InnoUiNative]::ClickButton($wizard, $copier.Handle)
    Start-Sleep -Milliseconds 500
    $copierApres = Find-Control '^\s*Code copié\s*!\s*$'
    $pressePapiers = [string](Get-Clipboard -Raw -ErrorAction Stop)
    $pressePapiers = $pressePapiers.Trim()

    if ($null -eq $copierApres) {
        throw "Le bouton n'a pas affiché la confirmation « Code copié ! »."
    }
    if ($pressePapiers -cne $code) {
        throw "Le contenu du presse-papiers ne correspond pas exactement au code affiché."
    }

    $empreinte = [BitConverter]::ToString(
        [Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($code))
    ).Replace("-", "")

    $preuve.resultat = "OK"
    $preuve.bouton = $copierApres.Text
    $preuve.code_longueur = $code.Length
    $preuve.code_sha256 = $empreinte
    $preuve.presse_papiers_verifie = $true
    $preuve | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $Rapport -Encoding utf8
    Write-Output "Copie interactive vérifiée pour $Edition : longueur $($code.Length), empreinte SHA-256 $empreinte. Le code lui-même n'est pas journalisé."
}
catch {
    $preuve.erreur = $_.Exception.Message
    $preuve | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $Rapport -Encoding utf8
    Write-Error $_
    throw
}
finally {
    if ($null -ne $processus) {
        $nettoyageSnapshot = @(Get-InstallerProcessSnapshot)
        $idsArbre = @(Get-InstallerProcessIds -RootProcessId $processus.Id -Snapshot $nettoyageSnapshot)
        $nettoyageIds = @($processIds + $idsArbre) | Sort-Object -Unique
        foreach ($pidActuel in $nettoyageIds) {
            if (Get-Process -Id $pidActuel -ErrorAction SilentlyContinue) {
                & taskkill.exe /F /T /PID $pidActuel 2>$null | Out-Null
            }
        }
    }
}
