@echo off
REM Script para executar OptiScaler Center no Windows

cd /d "%~dp0"

REM Verificar se venv existe
if not exist ".venv" (
    echo 🔧 Criando ambiente virtual...
    python -m venv .venv
)

REM Verificar se dependências estão instaladas
if not exist ".venv\.dependencies_installed" (
    echo 📦 Instalando dependências...
    .venv\Scripts\pip.exe install -r requirements.txt
    echo. > .venv\.dependencies_installed
)

REM Executar aplicação
echo 🚀 Iniciando OptiScaler Center...
.venv\Scripts\python.exe src\main.py
