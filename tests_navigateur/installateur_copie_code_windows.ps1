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
}

public static class InnoUiNative
{
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

    [DllImport("user32.dll")]
    private static extern bool EnumWindows(EnumWindowsProc callback, IntPtr lParam);

    [DllImport("user32.dll")]
    private static extern bool EnumChildWindows(IntPtr parent, EnumWindowsProc callback, IntPtr lParam);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

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
                result.Add(new InnoWindowInfo {
                    Handle = hWnd,
                    ProcessId = (int)owner,
                    Text = Text(hWnd),
                    ClassName = ClassName(hWnd),
                    Visible = IsWindowVisible(hWnd),
                    Enabled = IsWindowEnabled(hWnd)
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
        InnoWindowInfo[] windows = WindowsForProcesses(processIds);
        IntPtr fallback = IntPtr.Zero;
        foreach (InnoWindowInfo window in windows)
        {
            if (!window.Visible)
                continue;
            if (window.ClassName == "TWizardForm")
                return window.Handle;
            if (fallback == IntPtr.Zero && !String.IsNullOrWhiteSpace(window.Text))
                fallback = window.Handle;
        }

        // UseSetupLdr may run the extracted setup copy from TEMP. If Windows
        // detached that process from the original launcher PID, identify only
        // the unique Inno wizard for this product (the CI job runs one setup).
        foreach (InnoWindowInfo window in WindowsForProcesses(new int[0]))
        {
            if (window.Visible && window.ClassName == "TWizardForm" &&
                window.Text.IndexOf("ERP OHADA", StringComparison.OrdinalIgnoreCase) >= 0)
                return window.Handle;
        }
        return fallback;
    }

    public static InnoWindowInfo[] Children(IntPtr parent)
    {
        List<InnoWindowInfo> result = new List<InnoWindowInfo>();
        EnumWindowsProc callback = delegate(IntPtr hWnd, IntPtr lParam)
        {
            result.Add(new InnoWindowInfo {
                Handle = hWnd,
                Text = Text(hWnd),
                ClassName = ClassName(hWnd),
                Visible = IsWindowVisible(hWnd),
                Enabled = IsWindowEnabled(hWnd)
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
    return ,([int[]]@($ids))
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
    $suivant = Wait-Control '^\s*&?Suivant\s*>?\s*$' 12
    if ($null -eq $suivant -or -not $suivant.Enabled) {
        throw "Bouton Suivant introuvable ou désactivé dans le wizard."
    }
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
        $nettoyageIds = @(Get-InstallerProcessIds -RootProcessId $processus.Id -Snapshot $nettoyageSnapshot)
        foreach ($pidActuel in $nettoyageIds) {
            if (Get-Process -Id $pidActuel -ErrorAction SilentlyContinue) {
                & taskkill.exe /F /T /PID $pidActuel 2>$null | Out-Null
            }
        }
    }
}
