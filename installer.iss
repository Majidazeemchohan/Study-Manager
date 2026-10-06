; StudyManager - Inno Setup installer script
; Steps:
;   1. Pehle build.bat chalao taake dist\StudyManager.exe ban jaye
;   2. Inno Setup install karo (jrsoftware.org/isinfo.php)
;   3. Ye file Inno Setup me kholo aur Compile dabao (F9)
;   4. Output folder me StudyManagerSetup.exe mil jayegi

#define MyAppName "StudyManager"
#define MyAppVersion "1.0"
#define MyAppExeName "StudyManager.exe"

[Setup]
AppId={{4502415D-4D1B-4498-A9BD-5B94A68F2316}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=StudyManager
DefaultDirName={autopf}\StudyManager
DefaultGroupName=StudyManager
PrivilegesRequired=lowest
OutputDir=Output
OutputBaseFilename=StudyManagerSetup
Compression=lzma
SolidCompression=yes
DisableProgramGroupPage=yes
UninstallDisplayName=StudyManager
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Desktop shortcut:
Name: "{autodesktop}\StudyManager"; Filename: "{app}\{#MyAppExeName}"
; Start Menu entry:
Name: "{group}\StudyManager"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall StudyManager"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch StudyManager"; Flags: nowait postinstall skipifsilent
