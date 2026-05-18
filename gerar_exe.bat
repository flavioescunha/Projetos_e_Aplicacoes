@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ==========================================
echo Gerador de Executavel com versao automatica
echo Pasta atual:
cd
echo ==========================================
echo.

REM ==========================================
REM CONFIGURE AQUI
REM ==========================================
set "PYFILE=ProjetosAplicacoes.py"
set "EXE_BASE=Gerenciador_Investimentos"
set "ICON_FILE=icone.ico"
set "DIST_DIR=dist"
set "RELEASE_DIR=release"
REM ==========================================

if not exist "%PYFILE%" (
    echo ERRO: arquivo "%PYFILE%" nao encontrado.
    pause
    exit /b 1
)

echo Lendo versao em %PYFILE%...
set "VERSAO="

for /f tokens^=2delims^=^" %%v in ('findstr /R /C:"^VERSAO_ATUAL[ ]*=" "%PYFILE%"') do (
    set "VERSAO=%%v"
)

if "%VERSAO%"=="" (
    echo ERRO: nao foi possivel ler VERSAO_ATUAL dentro de "%PYFILE%".
    echo Certifique-se de que existe uma linha como:
    echo VERSAO_ATUAL = "v1.0.9"
    pause
    exit /b 1
)

set "EXE_NAME=%EXE_BASE%_%VERSAO%"

echo.
echo Versao encontrada: %VERSAO%
echo Nome do executavel: %EXE_NAME%.exe
echo.

REM ==========================================
REM DESCOBRIR QUAL COMANDO PYTHON FUNCIONA
REM ==========================================
set "PY_CMD="

py -V >nul 2>nul
if not errorlevel 1 set "PY_CMD=py"

if "%PY_CMD%"=="" (
    python --version >nul 2>nul
    if not errorlevel 1 set "PY_CMD=python"
)

if "%PY_CMD%"=="" (
    echo ERRO: nao foi encontrado "py" nem "python" no sistema.
    pause
    exit /b 1
)

echo Interpretador encontrado: %PY_CMD%

REM ==========================================
REM TESTAR SE O PYINSTALLER ESTA INSTALADO
REM ==========================================
%PY_CMD% -m PyInstaller --version >nul 2>nul
if errorlevel 1 (
    echo.
    echo PyInstaller nao encontrado neste interpretador.
    echo Tentando instalar automaticamente...
    %PY_CMD% -m pip install pyinstaller
    if errorlevel 1 (
        echo.
        echo ERRO: nao foi possivel instalar o PyInstaller automaticamente.
        echo Tente manualmente com:
        echo %PY_CMD% -m pip install pyinstaller
        pause
        exit /b 1
    )
)

echo.
echo Limpando compilacoes antigas...
if exist build rmdir /s /q build
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"
if exist "%EXE_NAME%.spec" del /q "%EXE_NAME%.spec"

if not exist "%RELEASE_DIR%" mkdir "%RELEASE_DIR%"

echo.
echo Gerando executavel...
if exist "%ICON_FILE%" (
    %PY_CMD% -m PyInstaller --noconfirm --onefile --windowed ^
        --name "%EXE_NAME%" ^
        --icon "%ICON_FILE%" ^
        --collect-all customtkinter ^
        --collect-all tkcalendar ^
        "%PYFILE%"
) else (
    %PY_CMD% -m PyInstaller --noconfirm --onefile --windowed ^
        --name "%EXE_NAME%" ^
        --collect-all customtkinter ^
        --collect-all tkcalendar ^
        "%PYFILE%"
)

if errorlevel 1 (
    echo.
    echo ERRO: falha ao gerar o executavel.
    pause
    exit /b 1
)

echo.
echo Copiando executavel para a pasta "%RELEASE_DIR%"...
copy /Y "%DIST_DIR%\%EXE_NAME%.exe" "%RELEASE_DIR%\%EXE_NAME%.exe" >nul

if errorlevel 1 (
    echo ERRO: nao foi possivel copiar o executavel para "%RELEASE_DIR%".
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Executavel gerado com sucesso!
echo Arquivo final:
echo %RELEASE_DIR%\%EXE_NAME%.exe
echo ==========================================
pause