; Inno Setup — na RAIZ do repositório (BuildDir sem ..)
; Se moveres este ficheiro para installer\, usa as versões com ..\ no BuildDir.
;
; PyInstaller onedir: dist\PINK-IPTV\ com _internal (flet, flet_desktop, etc.). BuildDir mantém-se.

#define MyAppName "PINK IPTV"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "PINK IPTV"
#define MyAppExeName "PINK-IPTV.exe"
#define BuildDir "dist\PINK-IPTV"

[Setup]
AppId={{E8B2F4A1-0C9D-4E5F-8A3B-1D2E3F4A5B6C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=dist-installer
OutputBaseFilename=PINK-IPTV-Setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=no
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#MyAppExeName}
WizardImageBackColor=$008000FF
WizardImageStretch=yes

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\Portuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho no ambiente de trabalho"; GroupDescription: "Opcional:"; Flags: unchecked

[Files]
Source: "{#BuildDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Executar {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
procedure InitializeWizard;
begin
  WizardForm.NextButton.Font.Style := [fsBold];
  WizardForm.NextButton.Font.Color := clWhite;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpWelcome then
    WizardForm.WelcomeLabel2.Font.Color := clWhite;
end;
