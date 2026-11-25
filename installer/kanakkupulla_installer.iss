; Inno Setup Script for Kanakkupulla Windows Desktop Application
; Generates standard Windows installer with desktop and start menu shortcuts

#define MyAppName "Kanakkupulla"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Google Antigravity Team"
#define MyAppURL "https://github.com/Kanakkupulla"
#define MyAppExeName "Kanakkupulla.exe"

[Setup]
AppId={{E58C361F-9C3E-4B02-86A9-27A7B9B497D2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist_installer
OutputBaseFilename=Kanakkupulla_Setup_v1.0.0
SetupIconFile=..\assets\icons\app_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\Kanakkupulla\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\Kanakkupulla\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icons\app_icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icons\app_icon.ico"; Tasks: desktopicon

[Registry]
; Register .kpk file association for Kanakkupulla Backup Packages
Root: HKA; Subkey: "Software\Classes\.kpk"; ValueType: string; ValueName: ""; ValueData: "KanakkupullaBackupPackage"; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\KanakkupullaBackupPackage"; ValueType: string; ValueName: ""; ValueData: "Kanakkupulla Backup Archive"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\KanakkupullaBackupPackage\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKA; Subkey: "Software\Classes\KanakkupullaBackupPackage\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
