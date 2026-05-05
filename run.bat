@echo off
REM Corre sempre na pasta deste .bat (duplo-clique ou atalho noutro sitio).
cd /d "%~dp0"

title PINK IPTV
color 0D
cls
echo.
echo  ================================================
echo                  P I N K   I P T V
echo  ================================================
echo.

REM ---- Verificar Python ----
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERRO] Python nao encontrado.
    echo         Descarrega em: https://www.python.org/downloads/
    echo         Marca "Add Python to PATH" na instalacao.
    pause
    exit /b 1
)

REM ---- Instalar dependencias so na primeira vez ----
if not exist "%USERPROFILE%\Documents\PINK-IPTV\.installed" (
    echo  A instalar dependencias pela primeira vez...
    python -m pip install --upgrade pip --quiet
    python -m pip install --quiet -r "%~dp0requirements.txt"
    mkdir "%USERPROFILE%\Documents\PINK-IPTV" >nul 2>&1
    echo. > "%USERPROFILE%\Documents\PINK-IPTV\.installed"
    echo  Instalacao concluida!
)

echo  A iniciar PINK IPTV...
echo.
python "%~dp0app.py"

if errorlevel 1 (
    echo.
    echo  [ERRO] A app fechou com erro. Detalhes acima.
    pause
)
