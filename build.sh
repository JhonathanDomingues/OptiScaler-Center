#!/bin/bash
# Build script para Linux/MacOS
# Compila o OptiScaler Center usando PyInstaller

set -e

echo "🚀 OptiScaler Center - Build Script"
echo "===================================="
echo ""

# Verificar se está no diretório correto
if [ ! -f "optiscaler-center.spec" ]; then
    echo "❌ Erro: Execute este script no diretório raiz do projeto"
    exit 1
fi

# Verificar Python
echo "📦 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Instale Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION encontrado"
echo ""

# Verificar/criar ambiente virtual
if [ ! -d ".venv" ]; then
    echo "📦 Criando ambiente virtual..."
    python3 -m venv .venv
    echo "✅ Ambiente virtual criado"
else
    echo "✅ Ambiente virtual já existe"
fi

# Ativar ambiente virtual
echo "📦 Ativando ambiente virtual..."
source .venv/bin/activate

# Instalar dependências
echo ""
echo "📦 Instalando dependências..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q pyinstaller

echo "✅ Dependências instaladas"
echo ""

# Limpar builds anteriores
if [ -d "build" ] || [ -d "dist" ]; then
    echo "🧹 Limpando builds anteriores..."
    rm -rf build dist
    echo "✅ Limpeza concluída"
    echo ""
fi

# Build com PyInstaller
echo "🔨 Compilando com PyInstaller..."
echo "Isso pode levar alguns minutos..."
echo ""

pyinstaller optiscaler-center.spec

# Verificar resultado
if [ -d "dist/OptiScalerCenter" ]; then
    echo ""
    echo "✅ Build concluído com sucesso!"
    echo ""
    echo "📁 Executável criado em: dist/OptiScalerCenter/"
    echo ""
    echo "Para executar: ./dist/OptiScalerCenter/OptiScalerCenter"
    echo ""
    
    # Criar arquivo tarball
    echo "📦 Criando arquivo tar.gz..."
    cd dist
    VERSION=$(grep "APP_VERSION" ../src/utils/constants.py | cut -d'"' -f2)
    tar -czf "OptiScalerCenter-Linux-v${VERSION}.tar.gz" OptiScalerCenter/
    echo "✅ Arquivo criado: dist/OptiScalerCenter-Linux-v${VERSION}.tar.gz"
    cd ..
    echo ""
    echo "🎉 Build completo!"
else
    echo ""
    echo "❌ Erro durante o build. Verifique os logs acima."
    exit 1
fi
