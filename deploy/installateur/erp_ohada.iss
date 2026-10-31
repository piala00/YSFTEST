; Installateur Windows de l'ERP OHADA (Inno Setup 6), une édition par installateur :
;   ISCC /DEdition=Transport /DPort=8100 /DVersion=1.0.0 /DSource=..\..\dist\ERP-OHADA-Transport erp_ohada.iss
; Installation silencieuse (déploiement sur plusieurs postes) :
;   ERP-OHADA-Transport-Installation.exe /VERYSILENT /ROLE=seul|siege|agence|poste [/FICHIER=agence.erpx] [/SERVEUR=http://SERVEUR:8100]
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
#define Outils "..\..\dist-outils"

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
Source: "{#Outils}\ERP-Controle-Installation.exe"; Flags: dontcopy
Source: "{#Outils}\ERP-Nettoyage.exe"; DestDir: "{app}"; Flags: ignoreversion; Check: EstServeur

[InstallDelete]
Type: files; Name: "{app}\documentation\AUDIT_COMPTABILITE_SOURCE_UNIQUE_2026-10-26.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\AUDIT_REPORTING_ETATS.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\AUDIT_SAGE_COMPTABILITE.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\AUDIT_SAGE_V12_GESCOM.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\AUDIT_SKILL_TRANSPORT_2026-10-26.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\BENCHMARK_TRANSPORT_COMMERCE.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\COMPTABILITE_ANALYTIQUE_ETATS.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\CONCEPTION_BAREMES_REMISES.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\CONCEPTION_DEPART_COMPTABILISATION.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\CONCEPTION_LICENCES.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\DEMANDE_GPT_PROCHAINE.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\DEMANDE_RECHERCHE_SAGE_POUR_GPT.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\ECHANGES_AGENCES.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\FEUILLE_DE_ROUTE.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\HEBERGEMENT_PYTHONANYWHERE.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\IMPREVUS_VOYAGE.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\LIAISON_COMPTABILITE.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\LICENCES_SIMPLIFIEES.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\MATRICE_AGENCES_CAISSE_STOCK.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\RECETTE_SAHEL_DISTRIBUTION.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\REPONSE_GPT_2026-10-24.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\REPRISE_SAGE100.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\SAGE_V12_POINTS_A_VERIFIER.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\TRANSMISSION_GPT.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\V2_TRANSPORT_VOYAGEURS.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\VERSION_EN_LIGNE.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\erp-simulateur-bureau.html"; Check: EstServeur
Type: files; Name: "{app}\documentation\erp-simulateur-web.html"; Check: EstServeur
Type: files; Name: "{app}\documentation\explorateur-menus-autonome.html"; Check: EstServeur
Type: files; Name: "{app}\documentation\explorateur-menus.html"; Check: EstServeur
Type: files; Name: "{app}\documentation\recherche\reponses-gpt-2026-10-22\LIRE_D_ABORD.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\recherche\reponses-gpt-2026-10-22\MANIFESTE.csv"; Check: EstServeur
Type: files; Name: "{app}\documentation\recherche\reponses-gpt-2026-10-22\REPONSES_PAR_QUESTION.csv"; Check: EstServeur
Type: files; Name: "{app}\documentation\recherche\sage-liaisons-comptabilite-claude\CONTRAT_ERP_PROPOSE.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\recherche\sage-liaisons-comptabilite-claude\CYCLE_TIERS.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\recherche\sage-liaisons-comptabilite-claude\MANIFEST_SHA256.json"; Check: EstServeur
Type: files; Name: "{app}\documentation\recherche\sage-liaisons-comptabilite-claude\PROMPT_CLAUDE.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\recherche\sage-liaisons-comptabilite-claude\PROTOCOLE_VERIFICATION.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\recherche\sage-liaisons-comptabilite-claude\RAPPORT.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\recherche\sage-liaisons-comptabilite-claude\README.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\recherche\sage-liaisons-comptabilite-claude\VALIDATION.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\recherche\sage-liaisons-comptabilite-claude\references\CARTOGRAPHIE_LIAISONS.csv"; Check: EstServeur
Type: files; Name: "{app}\documentation\recherche\sage-liaisons-comptabilite-claude\references\DROITS_ET_AUTORISATIONS.csv"; Check: EstServeur
Type: files; Name: "{app}\documentation\recherche\sage-liaisons-comptabilite-claude\references\FAITS_DOCUMENTES.csv"; Check: EstServeur
Type: files; Name: "{app}\documentation\recherche\sage-liaisons-comptabilite-claude\references\IMPACTS_PARAMETRAGE.csv"; Check: EstServeur
Type: files; Name: "{app}\documentation\recherche\sage-liaisons-comptabilite-claude\references\INCONNUES.csv"; Check: EstServeur
Type: files; Name: "{app}\documentation\recherche\sage-liaisons-comptabilite-claude\references\SCENARIOS_RECETTE.csv"; Check: EstServeur
Type: files; Name: "{app}\documentation\recherche\sage-liaisons-comptabilite-claude\references\SOURCES.csv"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\2026-10-30-GPT-SAISIE-RAPIDE.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\AUDIT_ECARTS.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\BILAN_SIMULATION_RESULTATS.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\BILAN_SIMULATION_SEPTEMBRE_2026.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\CAHIER_AUDIT_EXHAUSTIF_BOUTONS_ERP_SAGE.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\CLAUDE_RECETTE_BOUTONS_DOCUMENTS.csv"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\CLAUDE_RECETTE_BOUTONS_DOCUMENTS.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\COMPARAISON_SAGE_V12_BOUTONS_COMMERCIAL.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\GPT_AUDIT_ACTIONS_DOCUMENTS_LOT04.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\GPT_AUDIT_BOUTONS_SAGE_V12_LOT01.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\GPT_AUDIT_BOUTONS_SAGE_V12_LOT02.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\GPT_AUDIT_SAISIE_DOCUMENTS_LOT05.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\GPT_AUDIT_SECURITE_SYNCHRONISATION_LOT01.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\LISTE_DES_ROUTES.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\MAPPING_JOURNAUX_ET_ANALYTIQUE.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\MATRICE_ACTIONS_DOCUMENTS_COMMERCIAL.csv"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\MATRICE_AUDIT_GLOBAL_ERP_SAGE.csv"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\MODELE_RETOUR_POUR_CHATGPT.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\RECENSEMENT_BOUTONS_COMMERCIAL.csv"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\RECENSEMENT_BOUTONS_COMMERCIAL.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\RETOUR_POUR_CHATGPT.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\SCHEMA_BASE.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\SECURITE_ET_EXPORT.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\TESTS_EXECUTES.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\analytique\AUDIT_ANALYTIQUE.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\analytique\ECARTS_A_CORRIGER.md"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\analytique\MATRICE_ETATS_PLAN.csv"; Check: EstServeur
Type: files; Name: "{app}\documentation\retour\analytique\RESULTATS_TESTS.md"; Check: EstServeur

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
  PageBase: TInputOptionWizardPage;
  PageSQL: TInputQueryWizardPage;
  PageRole: TInputOptionWizardPage;
  PageAgence: TInputFileWizardPage;
  PageServeur: TInputQueryWizardPage;
  PageAutorisation: TInputFileWizardPage;
  NettoyageVoulu: Boolean;
  OutilNettoyageTemp: String;

function FichierAutorisation(): String;
begin
  Result := ExpandConstant('{param:AUTORISATION|}');
  if (Result = '') and (PageAutorisation <> nil) then
    Result := PageAutorisation.Values[0];
end;

function Controle(Arguments: String; var MessageControle: String): Boolean;
var
  Code: Integer;
  Brut: AnsiString;
  Rapport: String;
begin
  Rapport := ExpandConstant('{tmp}\controle-autorisation.txt');
  DeleteFile(Rapport);
  Result := Exec(ExpandConstant('{tmp}\ERP-Controle-Installation.exe'),
    '--edition {#LowerCase(Edition)} --rapport "' + Rapport + '" ' + Arguments,
    '', SW_HIDE, ewWaitUntilTerminated, Code) and (Code = 0);
  if LoadStringFromFile(Rapport, Brut) then
    MessageControle := UTF8Decode(Brut)
  else
    MessageControle := 'Le contrôle embarqué n''a pas pu produire de résultat. Aucune installation autorisée.';
end;

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

procedure InitializeWizard();
var
  Identifiant: String;
begin
  ExtractTemporaryFile('ERP-Controle-Installation.exe');
  Controle('', Identifiant);
  PageRole := CreateInputOptionPage(wpWelcome, 'Rôle de cet ordinateur',
    'Comment cet ordinateur sera-t-il utilisé ?',
    'Le serveur garde les données ; les autres postes du réseau l''ouvrent simplement dans leur navigateur.',
    True, False);
  PageRole.Add('Serveur de la société (un seul site)');
  PageRole.Add('Serveur de la direction (siège) : reçoit les données des agences');
  PageRole.Add('Serveur d''agence : avec le fichier d''installation remis par la direction');
  PageRole.Add('Poste de travail : accès au serveur par le navigateur (rien d''autre n''est installé)');
  PageRole.SelectedValueIndex := 0;

  PageAutorisation := CreateInputFilePage(PageRole.ID, 'Autorisation de cette installation',
    'Choisissez l’autorisation .erpinst signée remise pour ce serveur et cette édition.',
    'Code à communiquer à l''éditeur avant une première installation : ' + Identifiant + #13#10 +
    'Chaque installation, réinstallation, mise à jour et réparation vérifie cette autorisation hors ligne. ' +
    'Un code court ou une ancienne configuration ne suffit pas. Cette autorisation ne remplace pas la licence d''exploitation.');
  PageAutorisation.Add('Autorisation signée (.erpinst) :', 'Autorisation ERP (*.erpinst)|*.erpinst', '.erpinst');

  PageBase := CreateInputOptionPage(PageAutorisation.ID, 'Base de données',
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
  if PageID = PageAutorisation.ID then
    Result := Role() = 'poste';
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
var
  MessageControle: String;
begin
  Result := True;
  { Le mode silencieux valide toujours dans PrepareToInstall, sans ouvrir de dialogue bloquant. }
  if not WizardSilent and (CurPageID = PageAutorisation.ID) and not Controle('--verifier "' + FichierAutorisation() + '"', MessageControle) then
  begin
    MsgBox(MessageControle, mbError, MB_OK);
    Result := False;
  end;
  if (CurPageID = PageServeur.ID) and (Pos('SERVEUR:', Uppercase(PageServeur.Values[0])) > 0) then
  begin
    SuppressibleMsgBox('Remplacez SERVEUR par le nom ou l''adresse IP du serveur (ex. http://192.168.1.10:{#Port}).', mbError, MB_OK, IDOK);
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
var
  MessageControle: String;
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
    if not Controle('--marquer-programme "' + ExpandConstant('{app}') + '" --marquer-donnees "' + Donnees() + '"', MessageControle) then
      RaiseException(MessageControle + #13#10 + 'Les données restent conservées ; les dossiers doivent être identifiés avant installation.');
    { L'assistant du premier démarrage proposera ce rôle (et installera l'agence avec ce fichier) }
    ForceDirectories(Donnees());
    SaveStringToFile(Donnees() + '\role-installation.txt', Role(), False);
    if (Role() = 'agence') and (FichierAgence() <> '') and FileExists(FichierAgence()) then
      FileCopy(FichierAgence(), Donnees() + '\installation-agence.erpx', False);
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Code: Integer;
  MessageControle: String;
begin
  Result := '';
  if EstServeur() and ((FichierAutorisation() = '') or (Pos('"', FichierAutorisation()) > 0) or
    (Pos(#13, FichierAutorisation()) > 0) or (Pos(#10, FichierAutorisation()) > 0)) then
  begin
    Result := 'Choisissez une autorisation .erpinst valide (/AUTORISATION=chemin pour une installation silencieuse).';
    exit;
  end;
  { Toujours vérifié, même en mode silencieux et avec une base/clé résiduelle. Aucun service arrêté avant ce contrôle. }
  if EstServeur() and (not Controle('--verifier "' + FichierAutorisation() + '" --dossier-cible "' + ExpandConstant('{app}') + '"', MessageControle)) then
  begin
    Result := MessageControle;
    exit;
  end;
  { Mise à jour : le service et le programme en marche sont arrêtés (les données ne bougent pas) }
  if FileExists(ExpandConstant('{app}\{#Service}')) then
  begin
    Exec(ExpandConstant('{app}\{#Service}'), 'stop', '', SW_HIDE, ewWaitUntilTerminated, Code);
    Exec(ExpandConstant('{app}\{#Service}'), 'uninstall', '', SW_HIDE, ewWaitUntilTerminated, Code);
  end;
  Exec(ExpandConstant('{sys}\taskkill.exe'), '/F /T /IM "{#Programme}"', '', SW_HIDE, ewWaitUntilTerminated, Code);
  Result := '';
end;

function InitializeUninstall(): Boolean;
begin
  Result := True;
  NettoyageVoulu := False;
  { Une désinstallation silencieuse conserve toujours les données. Pas de commutateur d'effacement automatique. }
  if UninstallSilent then
    exit;
  NettoyageVoulu := MsgBox('Les données sont conservées par défaut. Après le retrait du programme et de son service, voulez-vous ouvrir le nettoyage contrôlé ?' + #13#10 +
    'Il présentera les fichiers, demandera une sauvegarde vérifiée et une confirmation avant tout effacement. Les bases SQL Server, dossiers partagés et autres éditions seront préservés.',
    mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES;
  if NettoyageVoulu then
  begin
    OutilNettoyageTemp := ExpandConstant('{tmp}\ERP-Nettoyage.exe');
    if not FileCopy(ExpandConstant('{app}\ERP-Nettoyage.exe'), OutilNettoyageTemp, False) then
    begin
      MsgBox('Impossible de préparer le nettoyage. Désinstallation arrêtée ; toutes les données sont conservées.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Code: Integer;
begin
  if (CurUninstallStep = usPostUninstall) and NettoyageVoulu then
    if not Exec(OutilNettoyageTemp, '--edition {#LowerCase(Edition)} --programme "' + ExpandConstant('{app}') +
      '" --donnees "' + Donnees() + '"', '', SW_SHOW, ewWaitUntilTerminated, Code) or (Code <> 0) then
      MsgBox('Le nettoyage n''a pas abouti. Les données non traitées sont conservées ; consultez le rapport ou relancez le diagnostic.', mbError, MB_OK);
end;
