@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

cd /d "%~dp0\.."
echo [PINK-IPTV] Pasta do projeto: %CD%

where py >nul 2>&1
if errorlevel 1 (
  echo ERRO: Python não está no PATH. Instala Python 3.12 e marca "Add python.exe to PATH".
  pause
  exit /b 1
)

echo [PINK-IPTV] pip + PyInstaller...
py -3.12 -m pip install --upgrade pip
if errorlevel 1 (
  echo Tentando "py -3"...
  py -3 -m pip install --upgrade pip
)
py -3.12 -m pip install -r requirements.txt pyinstaller 2>nul
if errorlevel 1 py -3 -m pip install -r requirements.txt pyinstaller

echo [PINK-IPTV] A compilar pasta da app...
py -3.12 -m PyInstaller --noconfirm installer\PINK-IPTV-onedir.spec
if errorlevel 1 (
  py -3 -m PyInstaller --noconfirm installer\PINK-IPTV-onedir.spec
)
if errorlevel 1 (
  echo ERRO: PyInstaller falhou.
  pause
  exit /b 1
)

set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  echo ERRO: Inno Setup 6 não encontrado. Instala a partir de https://jrsoftware.org/isdl.php
  echo A pasta da app já está em: dist\PINK-IPTV\
  pause
  exit /b 1
)

echo [PINK-IPTV] A compilar instalador...
"%ISCC%" installer\PINK-IPTV-Setup.iss
if errorlevel 1 (
  echo ERRO: Compilação do Setup falhou.
  pause
  exit /b 1
)

echo.
echo Pronto. Instalador em: %CD%\dist-installer\
explorer "dist-installer"
pause
