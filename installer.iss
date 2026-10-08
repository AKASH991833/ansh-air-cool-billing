#define MyAppName "Ansh Air Cool Billing"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Ansh Air Cool"
#define MyAppExeName "AC_Billing_System.exe"

[Setup]
AppId={{A7E8F3D4-7A1D-4C18-9C52-ACBILLING2024}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=assets\app_icon.ico
OutputDir=installer-output
OutputBaseFilename=AnshAirCoolBilling-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "dist\AC_Billing_System\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Check: DirExists(ExpandConstant('{src}\dist\AC_Billing_System'))
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion; Check: not DirExists(ExpandConstant('{src}\dist\AC_Billing_System'))

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
