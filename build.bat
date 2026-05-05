@echo off
cd /d "%~dp0"

title PINK IPTV - Construtor do Executavel
color 0D
cls
echo.
echo  ================================================
echo        P I N K   I P T V  -  B U I L D
echo  ================================================
echo.

REM ---- Verificar Python ----
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERRO] Python nao encontrado.
    echo         Descarrega em: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM ---- Atualizar pip ----
echo  [1/5] A atualizar pip...
python -m pip install --upgrade pip --quiet

REM ---- Instalar dependencias (sem --quiet para vermos o progresso) ----
echo  [2/5] A instalar dependencias (pode demorar 1-2 minutos)...
python -m pip install --upgrade -r "%~dp0requirements.txt" pyinstaller
if errorlevel 1 (
    echo.
    echo  [ERRO] Falha na instalacao das dependencias.
    pause
    exit /b 1
)

REM ---- Limpar builds anteriores ----
echo  [3/5] A limpar builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM ---- Construir o executavel via 'python -m PyInstaller' (resolve problema de PATH) ----
echo  [4/5] A construir PINK-IPTV.exe (pode demorar 2-5 minutos)...
echo.
python -m PyInstaller --clean --noconfirm "%~dp0PINK-IPTV.spec"
if errorlevel 1 (
    echo.
    echo  [ERRO] Falhou a construcao do executavel.
    pause
    exit /b 1
)

REM ---- Limpar pasta build ----
echo  [5/5] A limpar ficheiros temporarios...
if exist build rmdir /s /q build

echo.
echo  ================================================
echo            CONSTRUCAO CONCLUIDA!
echo  ================================================
echo.
echo  Executavel disponivel em:
echo    dist\PINK-IPTV.exe
echo.
echo  Tamanho aproximado: 80-120 MB
echo.
pause
