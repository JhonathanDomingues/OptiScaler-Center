#!/bin/bash
# Script para gerar AppImage local do OptiScaler Center
# Requer: appimagetool, imagemagick (opcional para ícone)

set -e

echo "📦 OptiScaler Center - AppImage Builder"
echo "========================================"
echo ""

# Verificar se dist existe
if [ ! -d "dist/OptiScalerCenter" ]; then
    echo "❌ Erro: Diretório dist/OptiScalerCenter não encontrado"
    echo "Execute primeiro: ./build.sh"
    exit 1
fi

# Verificar appimagetool
if ! command -v appimagetool &> /dev/null; then
    echo "📥 Baixando appimagetool..."
    wget -O appimagetool https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage
    chmod +x appimagetool
    sudo mv appimagetool /usr/local/bin/ 2>/dev/null || {
        mkdir -p ~/.local/bin
        mv appimagetool ~/.local/bin/
        export PATH="$HOME/.local/bin:$PATH"
    }
    echo "✅ appimagetool instalado"
fi

# Limpar AppDir anterior
rm -rf AppDir

echo "🏗️  Criando estrutura AppDir..."
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons/hicolor/256x256/apps

# Copiar executável
echo "📋 Copiando executável..."
cp -r dist/OptiScalerCenter/* AppDir/usr/bin/

# Copiar arquivo desktop
echo "📋 Copiando arquivo desktop..."
cp optiscaler-center.desktop AppDir/usr/share/applications/
cp optiscaler-center.desktop AppDir/

# Criar ícone
echo "🎨 Criando ícone..."
if command -v convert &> /dev/null; then
    convert -size 256x256 xc:transparent \
        -fill '#1b2838' -draw 'roundrectangle 20,20 236,236 20,20' \
        -fill '#5c7e10' -draw 'circle 128,128 128,88' \
        AppDir/usr/share/icons/hicolor/256x256/apps/optiscaler-center.png
    echo "✅ Ícone criado com ImageMagick"
elif command -v python3 &> /dev/null; then
    echo "🐍 Usando Python/Pillow para criar ícone..."
    python3 << 'PYTHON_SCRIPT'
try:
    from PIL import Image, ImageDraw
    
    # Criar imagem 256x256
    img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Fundo escuro arredondado
    draw.rounded_rectangle([(20, 20), (236, 236)], radius=20, fill='#1b2838')
    
    # Círculo verde (ícone simples)
    draw.ellipse([(88, 88), (168, 168)], fill='#5c7e10')
    
    # Salvar ícone
    img.save('AppDir/usr/share/icons/hicolor/256x256/apps/optiscaler-center.png')
    print("✅ Ícone criado com Pillow")
except ImportError:
    print("⚠️  Pillow não instalado, criando ícone simples...")
    # Criar PNG mínimo válido (ícone verde simples 256x256)
    import base64
    png_data = "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAACXBIWXMAAAsTAAALEwEAmpwYAAADIklEQVR4nO3BMQEAAADCoPVPbQhfoAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOA3gVkAAZ7eNEwAAAAASUVORK5CYII="
    with open('AppDir/usr/share/icons/hicolor/256x256/apps/optiscaler-center.png', 'wb') as f:
        f.write(base64.b64decode(png_data))
PYTHON_SCRIPT
else
    echo "⚠️  Nenhuma ferramenta de imagem disponível, criando ícone mínimo..."
    # PNG mínimo válido codificado em base64
    echo "iVBORw0KGgoAAAANSUhEUgAAAQAAAAEACAYAAABccqhmAAAACXBIWXMAAAsTAAALEwEAmpwYAAADIklEQVR4nO3BMQEAAADCoPVPbQhfoAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAOA3gVkAAZ7eNEwAAAAASUVORK5CYII=" | base64 -d > AppDir/usr/share/icons/hicolor/256x256/apps/optiscaler-center.png
fi

# Link simbólico para o ícone
ln -sf usr/share/icons/hicolor/256x256/apps/optiscaler-center.png AppDir/optiscaler-center.png 2>/dev/null || true

# Criar AppRun script
echo "📝 Criando AppRun..."
cat > AppDir/AppRun << 'EOF'
#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
cd "${HERE}/usr/bin"
exec "${HERE}/usr/bin/OptiScalerCenter" "$@"
EOF

chmod +x AppDir/AppRun

# Obter versão
VERSION=$(grep "APP_VERSION" src/utils/constants.py | cut -d'"' -f2)

# Criar AppImage
echo ""
echo "🔨 Construindo AppImage..."
ARCH=x86_64 appimagetool AppDir "OptiScalerCenter-Linux-v${VERSION}.AppImage"

if [ -f "OptiScalerCenter-Linux-v${VERSION}.AppImage" ]; then
    chmod +x "OptiScalerCenter-Linux-v${VERSION}.AppImage"
    mv "OptiScalerCenter-Linux-v${VERSION}.AppImage" dist/
    echo ""
    echo "✅ AppImage criado com sucesso!"
    echo ""
    echo "📁 Arquivo: dist/OptiScalerCenter-Linux-v${VERSION}.AppImage"
    echo ""
    echo "Para executar:"
    echo "  chmod +x dist/OptiScalerCenter-Linux-v${VERSION}.AppImage"
    echo "  ./dist/OptiScalerCenter-Linux-v${VERSION}.AppImage"
    echo ""
    echo "🎉 Pronto!"
else
    echo ""
    echo "❌ Erro ao criar AppImage"
    exit 1
fi

# Limpar
rm -rf AppDir
