@echo off
REM Build script para Windows
REM Compila o OptiScaler Center usando PyInstaller

echo ========================================
echo OptiScaler Center - Build Script
echo ========================================
echo.

REM Verificar se está no diretório correto
if not exist "optiscaler-center.spec" (
    echo [ERROR] Execute este script no diretorio raiz do projeto
    exit /b 1
)

REM Verificar Python
echo [INFO] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python nao encontrado. Instale Python 3.10+
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] Python %PYTHON_VERSION% encontrado
echo.

REM Verificar/criar ambiente virtual
if not exist ".venv" (
    echo [INFO] Criando ambiente virtual...
    python -m venv .venv
    echo [OK] Ambiente virtual criado
) else (
    echo [OK] Ambiente virtual ja existe
)

REM Ativar ambiente virtual
echo [INFO] Ativando ambiente virtual...
call .venv\Scripts\activate.bat

REM Instalar dependências
echo.
echo [INFO] Instalando dependencias...
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q pyinstaller

echo [OK] Dependencias instaladas
echo.

REM Limpar builds anteriores
if exist "build" (
    echo [INFO] Limpando builds anteriores...
    rmdir /s /q build
)
if exist "dist" (
    rmdir /s /q dist
)
if exist "build" echo [OK] Limpeza concluida
echo.

REM Build com PyInstaller
echo [INFO] Compilando com PyInstaller...
echo Isso pode levar alguns minutos...
echo.

pyinstaller optiscaler-center.spec

REM Verificar resultado
if exist "dist\OptiScalerCenter" (
    echo.
    echo [OK] Build concluido com sucesso!
    echo.
    echo [INFO] Executavel criado em: dist\OptiScalerCenter\
    echo.
    echo Para executar: dist\OptiScalerCenter\OptiScalerCenter.exe
    echo.
    
    REM Criar arquivo ZIP
    echo [INFO] Criando arquivo ZIP...
    cd dist
    for /f "tokens=2 delims==" %%i in ('findstr "APP_VERSION" ..\src\utils\constants.py') do set VERSION=%%i
    set VERSION=%VERSION:"=%
    set VERSION=%VERSION: =%
    powershell -command "Compress-Archive -Path OptiScalerCenter -DestinationPath OptiScalerCenter-Windows-v%VERSION%.zip -Force"
    echo [OK] Arquivo criado: dist\OptiScalerCenter-Windows-v%VERSION%.zip
    cd ..
    echo.
    echo [SUCCESS] Build completo!
) else (
    echo.
    echo [ERROR] Erro durante o build. Verifique os logs acima.
    exit /b 1
)

pause
