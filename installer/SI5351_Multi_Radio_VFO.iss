#define MyAppName "SI5351 Multi-Radio VFO"
#define MyAppVersion "6.0"
#define MyAppPublisher "John Bielefeld"
#define MyAppExeName "SI5351_Multi_Radio_VFO.exe"

[Setup]
AppId={{5F0B8F8C-5351-4D6E-9B11-SI5351VFO0001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\SI5351 Multi-Radio VFO
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\installer_output
OutputBaseFilename=SI5351_Multi_Radio_VFO_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}

CloseApplications=yes
CloseApplicationsFilter=SI5351_Multi_Radio_VFO.exe
RestartApplications=no
AlwaysRestart=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "..\pc_software\dist\SI5351_Multi_Radio_VFO\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
Type: filesandordirs; Name: "{app}"
Type: files; Name: "{commondesktop}\SI5351 Multi-Radio VFO.lnk"

[Icons]
Name: "{group}\SI5351 Multi-Radio VFO"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall SI5351 Multi-Radio VFO"; Filename: "{uninstallexe}"
Name: "{commondesktop}\SI5351 Multi-Radio VFO"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch SI5351 Multi-Radio VFO"; Flags: nowait postinstall skipifsilent