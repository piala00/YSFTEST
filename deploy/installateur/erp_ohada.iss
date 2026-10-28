; Installateur Windows de l'ERP OHADA (Inno Setup 6), une édition par installateur :
;   ISCC /DEdition=Transport /DPort=8100 /DVersion=1.0.0 /DSource=..\..\dist\ERP-OHADA-Transport erp_ohada.iss
; Installation silencieuse (déploiement sur plusieurs postes) :
;   ERP-OHADA-Transport-Installation.exe /VERYSILENT /ROLE=seul|siege|agence|poste [/FICHIER=agence.erpx] [/SERVEUR=http://SERVEUR:8100]
;       [/CLE=clé d'installation remise par l'éditeur]
;       [/BASE=sqlite|sqlserver|les-deux /SQL_SERVEUR=SRV\SQLEXPRESS /SQL_BASE=ERP /SQL_UTILISATEUR=… /SQL_MDP=…]
;       [/TASKS="service,parefeu"]   (service Windows : serveur en arrière-plan, recommandé)
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
#define Service "ERP-OHADA-" + Edition + "-service.exe"

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
LicenseFile=CLUF.txt

[Languages]
Name: "fr"; MessagesFile: "compiler:Languages\French.isl"

[Tasks]
Name: "bureau"; Description: "Icône sur le bureau"; GroupDescription: "Raccourcis :"
Name: "service"; Description: "En arrière-plan : service Windows (recommandé) — démarre avec l'ordinateur, se relance tout seul, aucune fenêtre à garder ouverte"; GroupDescription: "Fonctionnement du serveur :"; Flags: exclusive; Check: EstServeur
Name: "fenetre"; Description: "Dans une fenêtre, ouverte à l'ouverture de session (la fermer arrête le logiciel)"; GroupDescription: "Fonctionnement du serveur :"; Flags: exclusive unchecked; Check: EstServeur
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
Name: "{commonstartup}\{#Nom}"; Filename: "{app}\{#Programme}"; Parameters: "sans-navigateur"; WorkingDir: "{app}"; Flags: runminimized; Tasks: fenetre; Check: EstServeur

[Run]
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""ERP OHADA (port {#Port})"""; Flags: runhidden; Tasks: parefeu
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall add rule name=""ERP OHADA (port {#Port})"" dir=in action=allow protocol=TCP localport={#Port} profile=private,domain"; Flags: runhidden; Tasks: parefeu
Filename: "{app}\{#Service}"; Parameters: "install"; StatusMsg: "Installation du service Windows…"; Flags: runhidden waituntilterminated; Tasks: service
Filename: "{app}\{#Service}"; Parameters: "start"; StatusMsg: "Démarrage du service…"; Flags: runhidden waituntilterminated; Tasks: service
Filename: "{app}\{#Programme}"; Parameters: "ouvrir"; Description: "Ouvrir {#Nom} dans le navigateur"; Flags: postinstall nowait skipifsilent; Tasks: service
Filename: "{app}\{#Programme}"; Description: "Démarrer {#Nom} maintenant"; Flags: postinstall nowait skipifsilent; Tasks: fenetre
Filename: "{code:AdresseServeur}"; Description: "Ouvrir {#Nom}"; Flags: postinstall shellexec nowait skipifsilent; Check: EstPoste

[UninstallRun]
Filename: "{app}\{#Service}"; Parameters: "stop"; Flags: runhidden waituntilterminated; RunOnceId: "ServiceArret"
Filename: "{app}\{#Service}"; Parameters: "uninstall"; Flags: runhidden waituntilterminated; RunOnceId: "ServiceRetrait"
Filename: "{sys}\taskkill.exe"; Parameters: "/F /T /IM ""{#Programme}"""; Flags: runhidden; RunOnceId: "Arreter"
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""ERP OHADA (port {#Port})"""; Flags: runhidden; RunOnceId: "PareFeu"

[Messages]
fr.FinishedLabel=L'installation est terminée.%n%nLe serveur tourne en arrière-plan (service Windows « {#Nom} ») si vous l'avez choisi. Au premier démarrage, le navigateur ouvre l'assistant : compte administrateur, clé d'installation, société, rôle du serveur, base de données. Les données sont dans C:\ProgramData\ERP-OHADA ; elles sont conservées si vous désinstallez le logiciel.

[Code]
var
  PageCle: TInputQueryWizardPage;
  PageBase: TInputOptionWizardPage;
  PageSQL: TInputQueryWizardPage;
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

function Donnees(): String;
begin
  Result := ExpandConstant('{commonappdata}\ERP-OHADA\{#Edition}');
end;

function DejaConfigure(): Boolean;
begin
  { Mise à jour : la base en place n'est jamais changée par l'installateur (écran Base de données) }
  Result := FileExists(Donnees() + '\configuration.env');
end;

function Base(): String;
begin
  Result := Lowercase(ExpandConstant('{param:BASE|}'));
  if Result = '' then
    if PageBase.SelectedValueIndex = 1 then
      Result := 'sqlserver'
    else if PageBase.SelectedValueIndex = 2 then
      Result := 'les-deux'
    else
      Result := 'sqlite';
end;

function ValeurSQL(Parametre: String; Indice: Integer): String;
begin
  Result := ExpandConstant('{param:' + Parametre + '|}');
  if Result = '' then
    Result := Trim(PageSQL.Values[Indice]);
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

function CleInstallation(): String;
begin
  Result := Trim(ExpandConstant('{param:CLE|}'));
  if Result = '' then
    Result := Trim(PageCle.Values[0]);
end;

procedure InitializeWizard();
begin
  PageCle := CreateInputQueryPage(wpWelcome, 'Clé d''installation',
    'Saisissez la clé d''installation remise par l''éditeur',
    'Elle indique votre société et l''édition achetée ; collez-la telle quelle (groupes de 5 caractères). ' +
    'Sans clé, l''assistant du premier démarrage la demandera.');
  PageCle.Add('Clé d''installation :', False);

  PageRole := CreateInputOptionPage(PageCle.ID, 'Rôle de cet ordinateur',
    'Comment cet ordinateur sera-t-il utilisé ?',
    'Le serveur garde les données ; les autres postes du réseau l''ouvrent simplement dans leur navigateur.',
    True, False);
  PageRole.Add('Serveur de la société (un seul site)');
  PageRole.Add('Serveur de la direction (siège) : reçoit les données des agences');
  PageRole.Add('Serveur d''agence : avec le fichier d''installation remis par la direction');
  PageRole.Add('Poste de travail : accès au serveur par le navigateur (rien d''autre n''est installé)');
  PageRole.SelectedValueIndex := 0;

  PageBase := CreateInputOptionPage(PageRole.ID, 'Base de données',
    'Où le logiciel garde-t-il ses données ?',
    'Vous pourrez changer plus tard (Administration du poste › Base de données) : les données sont alors recopiées et contrôlées.',
    True, False);
  PageBase.Add('SQLite (recommandé) : un fichier sur ce serveur, rien à installer');
  PageBase.Add('SQL Server : une base dédiée sur votre serveur SQL (créée si elle n''existe pas)');
  PageBase.Add('Les deux : SQLite, avec une copie automatique dans SQL Server');
  PageBase.SelectedValueIndex := 0;

  PageSQL := CreateInputQueryPage(PageBase.ID, 'SQL Server',
    'Informations de connexion au serveur SQL',
    'Une base qui contient les tables d''un autre logiciel (ex. Sage) est refusée. Avec le service Windows, préférez un compte SQL : ' +
    'le compte Windows du service est celui de l''ordinateur. Si la connexion échoue, le logiciel démarre sur SQLite et l''assistant le signale.');
  PageSQL.Add('Serveur (\instance) :', False);
  PageSQL.Add('Nom de la base :', False);
  PageSQL.Add('Utilisateur SQL (vide : compte Windows) :', False);
  PageSQL.Add('Mot de passe :', True);
  PageSQL.Values[0] := 'localhost\SQLEXPRESS';
  PageSQL.Values[1] := 'ERP_{#Edition}';

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
  if PageID = PageCle.ID then
    Result := (Role() = 'poste') or DejaConfigure() or (ExpandConstant('{param:CLE|}') <> '');
  if PageID = PageAgence.ID then
    Result := Role() <> 'agence';
  if PageID = PageServeur.ID then
    Result := Role() <> 'poste';
  if PageID = wpSelectDir then
    Result := Role() = 'poste';
  if PageID = PageBase.ID then
    Result := (Role() = 'poste') or DejaConfigure();
  if PageID = PageSQL.ID then
    Result := (Role() = 'poste') or DejaConfigure() or (Base() = 'sqlite');
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

function LignesSQL(Prefixe: String): String;
var
  Utilisateur, MotDePasse: String;
begin
  Utilisateur := ValeurSQL('SQL_UTILISATEUR', 2);
  MotDePasse := ValeurSQL('SQL_MDP', 3);
  Result := Prefixe + 'DB_ENGINE=mssql' + #13#10 +
            Prefixe + 'DB_HOST=' + ValeurSQL('SQL_SERVEUR', 0) + #13#10 +
            Prefixe + 'DB_NAME=' + ValeurSQL('SQL_BASE', 1) + #13#10 +
            Prefixe + 'DB_PYTHON_DRIVER=mssql_python' + #13#10;
  if Utilisateur <> '' then
    Result := Result + Prefixe + 'DB_USER=' + Utilisateur + #13#10 + Prefixe + 'DB_PASSWORD=' + MotDePasse + #13#10;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssInstall) and EstServeur() and not DejaConfigure() then
  begin
    { Choix de la base, appliqué par le programme à son premier démarrage (avant le service) }
    ForceDirectories(Donnees());
    if Base() = 'sqlserver' then
      SaveStringToFile(Donnees() + '\installation-base.env', LignesSQL('') + 'DB_EXTRA_PARAMS=TrustServerCertificate=yes' + #13#10, False)
    else if Base() = 'les-deux' then
      SaveStringToFile(Donnees() + '\installation-base.env', LignesSQL('MIROIR_') + 'MIROIR_INTERVALLE_MINUTES=60' + #13#10, False);
  end;
  if (CurStep = ssPostInstall) and EstServeur() then
  begin
    { L'assistant du premier démarrage proposera ce rôle (et installera l'agence avec ce fichier) }
    ForceDirectories(Donnees());
    SaveStringToFile(Donnees() + '\role-installation.txt', Role(), False);
    if CleInstallation() <> '' then
      SaveStringToFile(Donnees() + '\cle-installation.txt', CleInstallation(), False);
    if (Role() = 'agence') and (FichierAgence() <> '') and FileExists(FichierAgence()) then
      FileCopy(FichierAgence(), Donnees() + '\installation-agence.erpx', False);
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Code: Integer;
begin
  { Mise à jour : le service et le programme en marche sont arrêtés (les données ne bougent pas) }
  if FileExists(ExpandConstant('{app}\{#Service}')) then
  begin
    Exec(ExpandConstant('{app}\{#Service}'), 'stop', '', SW_HIDE, ewWaitUntilTerminated, Code);
    Exec(ExpandConstant('{app}\{#Service}'), 'uninstall', '', SW_HIDE, ewWaitUntilTerminated, Code);
  end;
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /T /IM "{#Programme}"', '', SW_HIDE, ewWaitUntilTerminated, Code);
  Result := '';
end;
