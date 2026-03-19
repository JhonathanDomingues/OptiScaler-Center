# Guia de Solução de Problemas - Build

## Problema: DLL load failed while importing QtWidgets

### Sintomas
```
ImportError: DLL load failed while importing QtWidgets: Módulo não encontrado.
```

### Causa
PyInstaller não incluiu corretamente as DLLs do PyQt6 ou o UPX corrompeu as DLLs.

### Soluções

#### Solução 1: Usar spec atualizado (Recomendado)
O arquivo `optiscaler-center.spec` já foi atualizado com:
- Hidden imports completos do PyQt6
- Exclusão de DLLs Qt do UPX
- Bindings corretos

Rebuild com:
```bash
# Linux
./build.sh

# Windows
build.bat
```

#### Solução 2: Usar versão onefile
Se o problema persistir, tente a versão onefile:

```bash
# Windows
pyinstaller optiscaler-center-onefile.spec

# Linux
pyinstaller optiscaler-center-onefile.spec
```

A versão onefile:
- Cria um único executável
- Desabilita UPX (mais compatível)
- Pode ser mais lenta ao iniciar, mas mais confiável

#### Solução 3: Verificar instalação do PyQt6
Certifique-se que o PyQt6 está instalado corretamente:

```bash
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
pip install PyQt6>=6.6.0
```

#### Solução 4: Limpar cache e rebuild
```bash
# Limpar cache do PyInstaller
rm -rf build/ dist/ __pycache__/
rm -rf src/__pycache__/ src/*/__pycache__/

# Rebuild
pyinstaller --clean optiscaler-center.spec
```

---

## Problema: ModuleNotFoundError para outros módulos

### Sintomas
```
ModuleNotFoundError: No module named 'xxxxx'
```

### Solução
Adicione o módulo à lista `hiddenimports` no arquivo `.spec`:

```python
hiddenimports = [
    # ... módulos existentes ...
    'seu_modulo_aqui',
]
```

---

## Problema: Arquivo não encontrado ao criar release

### Sintomas
```
ERROR: Unable to find 'data/config.yaml' when adding binary and data files
```

### Solução
O arquivo está no `.gitignore` e não deve ser incluído. Já corrigido no spec para verificar existência antes de incluir.

Se precisar incluir outros arquivos, adicione em `optional_files` ou `optional_dirs` no `.spec`:

```python
optional_files = [
    ('README.md', '.'),
    ('seu_arquivo.txt', 'destino'),
]
```

---

## Problema: AppImage não executa no Linux

### Sintomas
```
cannot execute: required file not found
```

### Solução 1: Verificar permissões
```bash
chmod +x OptiScalerCenter-Linux-*.AppImage
./OptiScalerCenter-Linux-*.AppImage
```

### Solução 2: Habilitar FUSE
Algumas distribuições precisam do FUSE:

```bash
# Ubuntu/Debian
sudo apt install fuse libfuse2

# Fedora
sudo dnf install fuse fuse-libs

# Arch
sudo pacman -S fuse2
```

### Solução 3: Extrair e executar
Se FUSE não estiver disponível:

```bash
./OptiScalerCenter-Linux-*.AppImage --appimage-extract
cd squashfs-root
./AppRun
```

---

## Problema: Build falha no GitHub Actions

### Verificar logs
1. Acesse: `https://github.com/SEU-USUARIO/OptiScaler-Center/actions`
2. Clique no workflow que falhou
3. Expanda os logs para ver o erro

### Problemas comuns

#### Dependência faltando
Adicione ao `requirements.txt`:
```
nome-da-dependencia>=versao
```

#### Timeout no build
Aumente o timeout no workflow (já configurado para 30min por padrão).

#### Permissões do GitHub Token
Configure em: Settings → Actions → General → Workflow permissions
- Marque: "Read and write permissions"

---

## Problema: Executável muito grande

### Causas
- Muitas dependências incluídas
- UPX desabilitado
- Debugging symbols incluídos

### Soluções

#### Reduzir tamanho
1. **Habilitar UPX** (em `.spec`):
```python
upx=True,
```

2. **Excluir mais módulos** (em `.spec`):
```python
excludes=[
    'matplotlib',
    'numpy',
    'pandas',
    # adicione mais aqui
],
```

3. **Usar onefile** em vez de onedir:
```bash
pyinstaller optiscaler-center-onefile.spec
```

---

## Problema: Executável lento para iniciar

### Causa
- Versão onefile extrai arquivos temporários toda vez
- Muitos módulos para carregar

### Solução
Use a versão onedir (padrão):
```bash
pyinstaller optiscaler-center.spec
```

A versão onedir:
- Inicia mais rápido
- Usa mais espaço em disco
- Melhor para uso frequente

---

## Testar Build Localmente

Sempre teste localmente antes de fazer release:

### Windows
```cmd
# Compilar
build.bat

# Testar
cd dist\OptiScalerCenter
OptiScalerCenter.exe

# Se funcionar, pode fazer release
```

### Linux
```bash
# Compilar
./build.sh

# Testar
./dist/OptiScalerCenter/OptiScalerCenter

# Criar AppImage
./build-appimage.sh

# Testar AppImage
./dist/OptiScalerCenter-Linux-*.AppImage
```

---

## Obter Ajuda

Se o problema persistir:

1. **Ative modo debug** no `.spec`:
```python
exe = EXE(
    ...
    debug=True,
    console=True,  # Mostrar console para ver erros
    ...
)
```

2. **Verifique dependências**:
```bash
pipdeptree
```

3. **Teste em ambiente limpo**:
```bash
# Criar novo venv
python -m venv test_venv
source test_venv/bin/activate  # Linux
# ou
test_venv\Scripts\activate  # Windows

pip install -r requirements.txt
pyinstaller optiscaler-center.spec
```

4. **Abra uma issue** com:
   - Sistema operacional e versão
   - Versão do Python
   - Logs completos do erro
   - Passos para reproduzir
