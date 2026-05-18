@echo off
cd /d "%~dp0"

echo ==========================================
echo Atualizando repositorio Git...
echo Pasta atual:
cd
echo ==========================================
echo.

git status
echo.

set /p MSG=Digite a mensagem do commit: 
if "%MSG%"=="" set MSG=Atualizacao

echo.
echo Adicionando arquivos...
git add .
if errorlevel 1 (
    echo.
    echo ERRO ao adicionar arquivos com git add .
    pause
    exit /b 1
)

echo.
echo Criando commit...
git commit -m "%MSG%"
if errorlevel 1 (
    echo.
    echo Aviso: talvez nao haja alteracoes para commit.
)

echo.
echo Enviando para o GitHub...
git push origin main
if errorlevel 1 (
    echo.
    echo ERRO ao enviar para o GitHub.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Finalizado com sucesso.
echo ==========================================
pause