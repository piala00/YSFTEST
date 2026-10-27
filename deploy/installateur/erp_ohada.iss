; Installateur Windows de l'ERP OHADA (Inno Setup 6), une édition par installateur :
;   ISCC /DEdition=Transport /DPort=8100 /DVersion=1.0.0 /DSource=..\..\dist\ERP-OHADA-Transport erp_ohada.iss
; Installation silencieuse (déploiement sur plusieurs postes) :
;   ERP-OHADA-Transport-Installation.exe /VERYSILENT /ROLE=seul|siege|agence|poste [/FICHIER=agence.erpx] [/SERVEUR=http://SERVEUR:8100]
; Les données (C:\ProgramData\ERP-OHADA\<Édition>) ne sont jamais effacées, ni à la mise à jour ni à la désinstallation.

#ifndef Edition
  #define Edition "Transport"
#endif
#ifndef Port
  #define Port "8100"
#endif
#ifndef Version
  #define Version "1.0.0"
#endif
#ifndef Source
  #define Source "..\..\dist\ERP-OHADA-" + Edition
#endif
#define Programme "ERP-OHADA-" + Edition + ".exe"
#define Nom "ERP OHADA " + Edition

[Setup]
AppId=ERP-OHADA-{#Edition}
AppName={#Nom}
AppVersion={#Version}
AppPublisher=ERP OHADA
DefaultDirName={autopf}\ERP-OHADA\{#Edition}
DefaultGroupName={#Nom}
DisableProgramGroupPage=yes
PrivilegesRequired=admin
OutputDir=..\..\dist
OutputBaseFilename=ERP-OHADA-{#Edition}-Installation
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=force
UninstallDisplayName={#Nom}
UninstallDisplayIcon={app}\{#Programme}
SetupLogging=yes

[Languages]
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "bureau"; Description: "Icône sur le bureau"; GroupDescription: "Raccourcis :"
Name: "demarrage"; Description: "Démarrer le logiciel à l'ouverture de session Windows (serveur)"; GroupDescription: "Serveur :"; Check: EstServeur
Name: "parefeu"; Description: "Autoriser les autres postes du réseau local (pare-feu Windows, port {#Port})"; GroupDescription: "Serveur :"; Check: EstServeur

[Files]
Source: "{#Source}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: EstServeur

[Icons]
Name: "{group}\{#Nom}"; Filename: "{app}\{#Programme}"; Check: EstServeur
Name: "{group}\Lisez-moi"; Filename: "{app}\LISEZ-MOI.txt"; Check: EstServeur
Name: "{group}\Dossier des données"; Filename: "{commonappdata}\ERP-OHADA\{#Edition}"; Check: EstServeur
Name: "{group}\Désinstaller {#Nom}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#Nom}"; Filename: "{app}\{#Programme}"; Tasks: bureau; Check: EstServeur
Name: "{group}\{#Nom} (serveur)"; Filename: "{code:AdresseServeur}"; Check: EstPoste
Name: "{autodesktop}\{#Nom} (serveur)"; Filename: "{code:AdresseServeur}"; Tasks: bureau; Check: EstPoste
Name: "{commonstartup}\{#Nom}"; Filename: "{app}\{#Programme}"; Parameters: "sans-navigateur"; WorkingDir: "{app}"; Flags: runminimized; Tasks: demarrage; Check: EstServeur

[Run]
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""ERP OHADA (port {#Port})"""; Flags: runhidden; Tasks: parefeu
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall add rule name=""ERP OHADA (port {#Port})"" dir=in action=allow protocol=TCP localport={#Port} profile=private,domain"; Flags: runhidden; Tasks: parefeu
Filename: "{app}\{#Programme}"; Description: "Démarrer {#Nom} maintenant"; Flags: postinstall nowait skipifsilent; Check: EstServeur
Filename: "{code:AdresseServeur}"; Description: "Ouvrir {#Nom}"; Flags: postinstall shellexec nowait skipifsilent; Check: EstPoste

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /T /IM ""{#Programme}"""; Flags: runhidden; RunOnceId: "Arreter"
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""ERP OHADA (port {#Port})"""; Flags: runhidden; RunOnceId: "PareFeu"

[Messages]
fr.FinishedLabel=L'installation est terminée.%n%nAu premier démarrage, le navigateur ouvre l'assistant : compte administrateur, société, puis rôle du serveur. Les données sont dans C:\ProgramData\ERP-OHADA ; elles sont conservées si vous désinstallez le logiciel.

[Code]
var
  PageRole: TInputOptionWizardPage;
  PageAgence: TInputFileWizardPage;
  PageServeur: TInputQueryWizardPage;

function RoleParametre(): String;
begin
  Result := Lowercase(ExpandConstant('{param:ROLE|}'));
end;

function Role(): String;
begin
  if RoleParametre() <> '' then
    Result := RoleParametre()
  else if PageRole.SelectedValueIndex = 1 then
    Result := 'siege'
  else if PageRole.SelectedValueIndex = 2 then
    Result := 'agence'
  else if PageRole.SelectedValueIndex = 3 then
    Result := 'poste'
  else
    Result := 'seul';
end;

function EstServeur(): Boolean;
begin
  Result := Role() <> 'poste';
end;

function EstPoste(): Boolean;
begin
  Result := Role() = 'poste';
end;

function FichierAgence(): String;
begin
  Result := ExpandConstant('{param:FICHIER|}');
  if (Result = '') and (PageAgence <> nil) then
    Result := PageAgence.Values[0];
end;

function AdresseServeur(Param: String): String;
begin
  Result := ExpandConstant('{param:SERVEUR|}');
  if Result = '' then
    Result := Trim(PageServeur.Values[0]);
  if (Pos('://', Result) = 0) and (Result <> '') then
    Result := 'http://' + Result;
end;

procedure InitializeWizard();
begin
  PageRole := CreateInputOptionPage(wpWelcome, 'Rôle de cet ordinateur',
    'Comment cet ordinateur sera-t-il utilisé ?',
    'Le serveur garde les données ; les autres postes du réseau l''ouvrent simplement dans leur navigateur.',
    True, False);
  PageRole.Add('Serveur de la société (un seul site)');
  PageRole.Add('Serveur de la direction (siège) : reçoit les données des agences');
  PageRole.Add('Serveur d''agence : avec le fichier d''installation remis par la direction');
  PageRole.Add('Poste de travail : accès au serveur par le navigateur (rien d''autre n''est installé)');
  PageRole.SelectedValueIndex := 0;

  PageAgence := CreateInputFilePage(PageRole.ID, 'Fichier d''installation de l''agence',
    'Choisissez le fichier remis par la direction (ERP-INSTALLATION-….erpx).',
    'Vous pourrez aussi le donner plus tard, dans l''assistant qui s''ouvre au premier démarrage.');
  PageAgence.Add('Fichier :', 'Fichier d''installation (*.erpx)|*.erpx', '.erpx');

  PageServeur := CreateInputQueryPage(PageRole.ID, 'Adresse du serveur',
    'Quelle est l''adresse du serveur de l''ERP ?',
    'Elle est affichée dans la fenêtre du logiciel sur le serveur (« Autres postes du réseau »).');
  PageServeur.Add('Adresse :', False);
  PageServeur.Values[0] := 'http://SERVEUR:{#Port}';
end;

function ShouldSkipPage(PageID: Integer): Boolean;
begin
  Result := False;
  if PageID = PageAgence.ID then
    Result := Role() <> 'agence';
  if PageID = PageServeur.ID then
    Result := Role() <> 'poste';
  if PageID = wpSelectDir then
    Result := Role() = 'poste';
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if (CurPageID = PageServeur.ID) and (Pos('SERVEUR:', Uppercase(PageServeur.Values[0])) > 0) then
  begin
    MsgBox('Remplacez SERVEUR par le nom ou l''adresse IP du serveur (ex. http://192.168.1.10:{#Port}).', mbError, MB_OK);
    Result := False;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Donnees: String;
begin
  if (CurStep = ssPostInstall) and EstServeur() then
  begin
    { L'assistant du premier démarrage proposera ce rôle (et installera l'agence avec ce fichier) }
    Donnees := ExpandConstant('{commonappdata}\ERP-OHADA\{#Edition}');
    ForceDirectories(Donnees);
    SaveStringToFile(Donnees + '\role-installation.txt', Role(), False);
    if (Role() = 'agence') and (FichierAgence() <> '') and FileExists(FichierAgence()) then
      FileCopy(FichierAgence(), Donnees + '\installation-agence.erpx', False);
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Code: Integer;
begin
  { Mise à jour : le programme en marche est arrêté (les données ne bougent pas) }
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /T /IM "{#Programme}"', '', SW_HIDE, ewWaitUntilTerminated, Code);
  Result := '';
end;
