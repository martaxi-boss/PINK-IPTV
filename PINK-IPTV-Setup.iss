; Inno Setup 6 — gera PINK-IPTV-Setup-X.X.exe (instalador, não é app “portátil” de um ficheiro)
; Cor de rosa: fundo lateral do assistente + realce do texto "Seguinte".
;
; 1) Compila primeiro a pasta com PyInstaller (ver INSTALL-SETUP-WINDOWS.txt na pasta installer).
; 2) Instala Inno Setup: https://jrsoftware.org/isdl.php
; 3) Abre este .iss no Inno e Compila (F9).
;
; Imagem lateral opcional (164x314 px, 24-bit BMP): coloca wizard-side.bmp nesta pasta
; e descomenta a linha WizardImageFile.

#define MyAppName "PINK IPTV"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "PINK IPTV"
#define MyAppExeName "PINK-IPTV.exe"
#define BuildDir "..\dist\PINK-IPTV"

[Setup]
AppId={{E8B2F4A1-0C9D-4E5F-8A3B-1D2E3F4A5B6C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=..\dist-installer
OutputBaseFilename=PINK-IPTV-Setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=no
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#MyAppExeName}

; Rosa estilo app (#FF0080 em BGR para Inno: $008000FF)
WizardImageBackColor=$008000FF
WizardImageStretch=yes
; Descomenta se tiveres wizard-side.bmp (164x314):
;WizardImageFile=wizard-side.bmp

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
  { Realce rosa no botão Seguinte: texto branco + negrito (fundo segue tema Windows) }
  WizardForm.NextButton.Font.Style := [fsBold];
  WizardForm.NextButton.Font.Color := clWhite;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if CurPageID = wpWelcome then
    WizardForm.WelcomeLabel2.Font.Color := clWhite;
end;
