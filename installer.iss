; UniBoard installer script (Inno Setup 6)
; Build with:  ISCC.exe installer.iss
; Output goes to: installer_output\UniBoard_Setup.exe

#define MyAppName "UniBoard"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "UniBoard"
#define MyAppExeName "UniBoard.exe"

[Setup]
AppId={{8E4F7C2A-9B1D-4A6E-BC3F-D5A2E8F10C77}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
; LZMA2/max + solid = smallest download size (~50-60% of raw payload)
Compression=lzma2/max
SolidCompression=yes
LZMANumBlockThreads=4
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=installer_output
OutputBaseFilename=UniBoard_Setup
; Uncomment once an icon asset exists:
; SetupIconFile=assets\app.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\UniBoard\*"; DestDir: "{app}"; \
    Flags: recursesubdirs ignoreversion createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; \
    Flags: nowait postinstall skipifsilent

[Messages]
; Remind users about the LibreOffice requirement for PPTX rendering.
WelcomeLabel2=This will install [name/ver] on your computer.%n%nNote: PPTX slide rendering requires LibreOffice to be installed on this machine (free at libreoffice.org).
