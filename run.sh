#!/bin/bash
# Script para executar OptiScaler Center

# Diretório do projeto
cd "$(dirname "$0")"

# Verificar se venv existe
if [ ! -d ".venv" ]; then
    echo "🔧 Criando ambiente virtual..."
    python3 -m venv .venv
fi

# Verificar se dependências estão instaladas
if [ ! -f ".venv/.dependencies_installed" ]; then
    echo "📦 Instalando dependências..."
    .venv/bin/pip install -r requirements.txt
    touch .venv/.dependencies_installed
fi

# Executar aplicação
echo "🚀 Iniciando OptiScaler Center..."
.venv/bin/python3 src/main.py
