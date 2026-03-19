# 🚀 Guia de Setup - OptiScaler Center

## Pré-requisitos

- **Python 3.10 ou superior**
- **pip** (gerenciador de pacotes Python)
- **Sistema Operacional**: Windows 10/11 ou Linux

### Verificar Python

```bash
python --version
# ou
python3 --version
```

Se não tiver Python instalado:
- **Windows**: https://www.python.org/downloads/
- **Linux (Ubuntu/Debian)**: `sudo apt install python3 python3-pip python3-venv`
- **Linux (Arch)**: `sudo pacman -S python python-pip`

---

## 🔧 Instalação

### 1. Clone ou Navegue para o Projeto

```bash
cd /home/jhonathan/Desenvolvimento/OptiScaler-Center
```

### 2. Criar Ambiente Virtual

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

Quando ativado, você verá `(venv)` no início do prompt.

### 3. Atualizar pip

```bash
pip install --upgrade pip
```

### 4. Instalar Dependências

**Para Desenvolvimento:**
```bash
pip install -r requirements-dev.txt
```

**Para Uso Normal:**
```bash
pip install -r requirements.txt
```

### 5. Verificar Instalação

```bash
python -c "import PyQt6; print('PyQt6:', PyQt6.QtCore.PYQT_VERSION_STR)"
```

Deve exibir a versão do PyQt6 instalada.

---

## ▶️ Executar a Aplicação

### Modo de Desenvolvimento

```bash
# Ativar ambiente virtual (se não estiver ativo)
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Executar
python src/main.py
```

### Primeira Execução

Na primeira execução, a aplicação irá:
1. Criar o banco de dados SQLite em `data/games.db`
2. Criar arquivo de configuração em `data/config.yaml`
3. Criar diretório de logs `logs/`
4. Abrir a janela principal

---

## 🧪 Executar Testes

```bash
# Instalar dependências de desenvolvimento (se ainda não instalou)
pip install -r requirements-dev.txt

# Executar todos os testes
pytest tests/

# Com cobertura
pytest tests/ --cov=src --cov-report=html

# Visualizar relatório de cobertura
# O relatório estará em htmlcov/index.html
```

---

## 🎨 Verificar Qualidade do Código

### Formatação (Black)

```bash
# Verificar formatação
black --check src/

# Formatar automaticamente
black src/
```

### Linting (Flake8)

```bash
flake8 src/
```

### Linting (Pylint)

```bash
pylint src/
```

### Type Checking (MyPy)

```bash
mypy src/
```

---

## 📦 Estrutura de Dados

Após primeira execução, sua estrutura será:

```
OptiScaler-Center/
├── data/
│   ├── config.yaml          # Configurações
│   ├── games.db             # Banco de dados
│   └── backups/             # Backups de DLLs
├── logs/
│   └── optiscaler_center.log
└── resources/
    ├── fsr4_sdk/            # DLLs FSR4
    └── optiscaler_cache/    # Versões do OptiScaler
```

---

## 🐛 Solução de Problemas

### Erro: ModuleNotFoundError: No module named 'PyQt6'

**Solução:**
```bash
pip install PyQt6
```

### Erro: Permission denied (Linux)

**Solução:** Certifique-se de ter permissão de escrita nas pastas `data/` e `logs/`
```bash
chmod -R u+w data/ logs/
```

### Erro: DLL load failed (Windows)

**Solução:** Instale o Visual C++ Redistributable:
https://aka.ms/vs/17/release/vc_redist.x64.exe

### Interface não aparece

**Solução:** Verifique se há erros no terminal. Veja o log:
```bash
cat logs/optiscaler_center.log
```

### Banco de dados corrompido

**Solução:** Deletar e recriar:
```bash
rm data/games.db
python src/main.py
```

---

## 🔄 Atualizar Dependências

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Atualizar todas as dependências
pip install --upgrade -r requirements.txt
```

---

## 📚 Desenvolvimento

### Estrutura do Código

```
src/
├── main.py                    # Entry point
├── presentation/              # UI (PyQt6)
├── application/               # Casos de uso e serviços
├── domain/                    # Entidades e lógica de negócio
├── infrastructure/            # Serviços externos (DB, API, etc)
└── utils/                     # Utilitários
```

### Adicionar Nova Funcionalidade

1. **Criar entidade** em `domain/entities/` (se necessário)
2. **Criar caso de uso** em `application/use_cases/`
3. **Implementar UI** em `presentation/widgets/`
4. **Escrever testes** em `tests/`
5. **Documentar** no código e README

### Debugging

**VS Code:**
Crie `.vscode/launch.json`:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "OptiScaler Center",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/src/main.py",
            "console": "integratedTerminal"
        }
    ]
}
```

**PyCharm:**
- Run → Edit Configurations
- Adicionar Python
- Script path: `src/main.py`
- Working directory: raiz do projeto

---

## 📦 Build (Futuro)

Para criar executável standalone:

```bash
pip install pyinstaller

# Windows
pyinstaller --onefile --windowed --name="OptiScaler Center" src/main.py

# Linux
pyinstaller --onefile --windowed --name="optiscaler-center" src/main.py
```

O executável estará em `dist/`

---

## 🌐 Variáveis de Ambiente (Opcional)

Você pode definir:

```bash
# Linux/Mac
export OPTISCALER_DEBUG=1
export OPTISCALER_LOG_LEVEL=DEBUG

# Windows
set OPTISCALER_DEBUG=1
set OPTISCALER_LOG_LEVEL=DEBUG
```

---

## 📖 Documentação

- **Documentação Completa**: [DOCUMENTATION.md](DOCUMENTATION.md)
- **Especificações Técnicas**: [TECHNICAL_SPECS.md](TECHNICAL_SPECS.md)
- **Guia de Contribuição**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **Resumo do Projeto**: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

---

## ❓ Ajuda

Se encontrar problemas:

1. Verifique os logs em `logs/optiscaler_center.log`
2. Leia a documentação completa
3. Abra uma issue no GitHub
4. Veja [CONTRIBUTING.md](CONTRIBUTING.md) para mais informações

---

## ✅ Checklist de Setup

- [ ] Python 3.10+ instalado
- [ ] Ambiente virtual criado
- [ ] Dependências instaladas
- [ ] Aplicação executa sem erros
- [ ] Banco de dados criado
- [ ] Logs sendo gerados
- [ ] Interface abre corretamente

Se todos os itens estão marcados, você está pronto para desenvolver! 🎉

---

**Próximo Passo**: Leia [DOCUMENTATION.md](DOCUMENTATION.md) para entender a arquitetura e começar a implementar funcionalidades.
