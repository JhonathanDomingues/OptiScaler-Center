# 🎮 OptiScaler Center

<div align="center">

![Version](https://img.shields.io/badge/version-0.1.3-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg)

**Gerenciador visual para instalação e configuração do OptiScaler em jogos**

[Documentação Completa](DOCUMENTATION.md) • [Reportar Bug](https://github.com/seu-usuario/optiscaler-center/issues) • [Solicitar Feature](https://github.com/seu-usuario/optiscaler-center/issues)

</div>

---

## 📖 Sobre

**OptiScaler Center** é uma aplicação desktop multiplataforma que facilita o gerenciamento do [OptiScaler](https://github.com/optiscaler/OptiScaler) em seus jogos. Com uma interface moderna e intuitiva, você pode:

- 🔍 **Detectar automaticamente** jogos instalados no Steam
- 🎯 **Identificar DLLs suportadas** (DLSS, FSR, XeSS)
- 📥 **Baixar e instalar** diferentes versões do OptiScaler
- 🔄 **Atualizar em lote** múltiplos jogos
- 💾 **Backup automático** de arquivos originais
- ⚙️ **Configurar** parâmetros por jogo
- 🚀 **Suporte FSR4** via SDK DLLs

## ✨ Features Principais

### 🎮 Gerenciamento de Jogos
- Detecção automática de bibliotecas Steam (Windows e Linux)
- Adição manual de jogos de qualquer plataforma
- Análise inteligente de DLLs compatíveis
- Filtros e busca rápida

### 📦 OptiScaler
- Integração com GitHub para download de releases
- Instalação com backup automático
- Desinstalação com restauração completa
- Gerenciamento de múltiplas versões

### 🎨 Interface Moderna
- Design estilo Steam com cards visuais
- Sistema de grid responsivo
- Tema dark moderno (#1b2838)
- Badges de tecnologia (DLSS/FSR/XeSS)
- Carregamento automático de imagens Steam
- Feedback visual em tempo real
- Logs e diagnóstico integrados

### 🛠️ FSR4 SDK
- Instalação de DLLs FSR4 da AMD
- Suporte para versões padrão e INT8
- Configuração por jogo

## 🚀 Início Rápido

### Pré-requisitos

- Python 3.10 ou superior
- Sistema operacional Windows 10/11 ou Linux

### 📦 Download (Binários Prontos)

Baixe a versão mais recente na [página de releases](https://github.com/JhonathanDomingues/OptiScaler-Center/releases):

#### Windows
1. Baixe `OptiScalerCenter-Windows-vX.X.X.zip`
2. Extraia para uma pasta
3. Execute `OptiScalerCenter.exe`

#### Linux (AppImage) - Recomendado 🚀
1. Baixe `OptiScalerCenter-Linux-vX.X.X.AppImage`
2. Torne executável: `chmod +x OptiScalerCenter-Linux-*.AppImage`
3. Execute: `./OptiScalerCenter-Linux-*.AppImage`

Não requer instalação! Funciona em qualquer distribuição Linux.

#### Linux (TAR.GZ)
1. Baixe `OptiScalerCenter-Linux-vX.X.X.tar.gz`
2. Extraia: `tar -xzf OptiScalerCenter-Linux-*.tar.gz`
3. Execute: `./OptiScalerCenter/OptiScalerCenter`

### 🔧 Instalação para Desenvolvimento

```bash
# Clone o repositório
git clone https://github.com/JhonathanDomingues/OptiScaler-Center.git
cd optiscaler-center

# Instale as dependências
pip install -r requirements.txt

# Execute a aplicação
python src/main.py
```

### 🏗️ Compilar Executáveis

#### Linux
```bash
# Compilar com PyInstaller
./build.sh

# Criar AppImage (requer build.sh primeiro)
./build-appimage.sh
```

#### Windows
```cmd
build.bat
```

### Instalação

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/optiscaler-center.git
cd optiscaler-center

# Instale as dependências
pip install -r requirements.txt

# Execute a aplicação
python src/main.py
```

### Uso Básico

1. **Abra o OptiScaler Center**
2. **Clique em "Scanner"** para detectar jogos automaticamente
3. **Selecione um jogo** da lista
4. **Escolha a versão do OptiScaler** e clique em "Instalar"
5. **Pronto!** O jogo está configurado

## 📸 Screenshots

> Em desenvolvimento - screenshots serão adicionados em breve

## 🏗️ Arquitetura

O projeto segue os princípios de **Clean Architecture** com separação clara de responsabilidades:

```
┌─────────────────────┐
│  Presentation UI    │  ← PyQt6 Interface
├─────────────────────┤
│  Application Layer  │  ← Use Cases & Services
├─────────────────────┤
│  Domain Layer       │  ← Entities & Business Logic
├─────────────────────┤
│  Infrastructure     │  ← External Services (Steam, GitHub, FS)
└─────────────────────┘
```

Para detalhes completos, veja a [documentação de arquitetura](DOCUMENTATION.md#arquitetura-do-sistema).

## 🛠️ Tecnologias

- **Python 3.10+** - Linguagem principal
- **PyQt6** - Framework de interface gráfica
- **SQLite** - Banco de dados local
- **aiohttp** - Downloads assíncronos
- **vdf** - Parser de arquivos Steam
- **requests** - Integração com GitHub API

## 📁 Estrutura do Projeto

```
OptiScaler-Center/
├── src/
│   ├── presentation/      # Interface PyQt6
│   ├── application/       # Casos de uso
│   ├── domain/           # Entidades e lógica
│   ├── infrastructure/   # Serviços externos
│   └── utils/           # Utilitários
├── resources/           # Recursos (FSR4 SDK, cache)
├── data/               # Dados (DB, configs, backups)
├── tests/              # Testes automatizados
└── docs/               # Documentação adicional
```

## 🗺️ Roadmap

### ✅ Fase 1: MVP (Concluído)
- [x] Estrutura do projeto
- [x] Documentação completa
- [x] Scanner de jogos Steam (Windows e Linux)
- [x] Detecção de DLLs (DLSS, FSR, XeSS)
- [x] Download de versões do GitHub
- [x] Instalação/desinstalação básica
- [x] Interface UI moderna com cards estilo Steam
- [x] Banco de dados SQLite
- [x] Sistema de backup automático
- [x] Logs e diagnóstico

### 🔄 Fase 2: Recursos Essenciais (Em Desenvolvimento)
- [x] Adição manual de jogos
- [x] Suporte FSR4 SDK (DLLs padrão e INT8)
- [x] Interface moderna com tema dark
- [ ] Perfis de configuração por jogo
- [ ] Atualização em lote
- [ ] Sistema de busca e filtros avançados
- [ ] Tema claro (alternativo)

### 🔮 Fase 3: Extras (Planejado)
- [ ] Integração Epic/GOG/EA/Ubisoft
- [ ] Download automático de imagens (SteamGridDB)
- [ ] Benchmark integrado
- [ ] Multi-idioma (EN, PT-BR, ES)
- [ ] Cloud sync de configurações
- [ ] Auto-update da aplicação
- [ ] Estatísticas de uso
- [ ] Modo portátil

Veja o [roadmap completo](DOCUMENTATION.md#roadmap-de-desenvolvimento).

## 📚 Documentação

- **[Documentação Completa](DOCUMENTATION.md)** - Guia detalhado do projeto
- **[Como Contribuir](CONTRIBUTING.md)** - Guia de contribuição (em breve)
- **[Manual do Usuário](docs/USER_GUIDE.md)** - Guia de uso (em breve)
- **[API Reference](docs/API.md)** - Documentação da API (em breve)

## 🤝 Contribuindo

Contribuições são bem-vindas! Veja como você pode ajudar:

1. 🍴 Fork o projeto
2. 🔨 Crie uma branch (`git checkout -b feature/AmazingFeature`)
3. ✅ Commit suas mudanças (`git commit -m 'Add: Amazing Feature'`)
4. 📤 Push para a branch (`git push origin feature/AmazingFeature`)
5. 🎉 Abra um Pull Request

Por favor, siga as [diretrizes de contribuição](CONTRIBUTING.md) e o [código de conduta](CODE_OF_CONDUCT.md).

## 🐛 Reportar Bugs

Encontrou um bug? Por favor, [abra uma issue](https://github.com/seu-usuario/optiscaler-center/issues) com:

- Descrição clara do problema
- Passos para reproduzir
- Comportamento esperado vs atual
- Screenshots (se aplicável)
- Informações do sistema (OS, Python version)

## 💡 Sugestões

Tem uma ideia para melhorar o projeto? [Abra uma issue](https://github.com/seu-usuario/optiscaler-center/issues) com a tag `enhancement`!

## 📜 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🙏 Agradecimentos

- [OptiScaler](https://github.com/optiscaler/OptiScaler) - Pelo projeto incrível
- [AMD FidelityFX](https://gpuopen.com/fidelityfx/) - Pelo FSR SDK
- Comunidade de modding de jogos

## 📧 Contato

- **GitHub Issues**: [Reportar problemas](https://github.com/seu-usuario/optiscaler-center/issues)
- **Discussions**: [Fazer perguntas](https://github.com/seu-usuario/optiscaler-center/discussions)

---

<div align="center">

**Feito para a comunidade de gamers**

[⬆ Voltar ao topo](#-optiscaler-center)

</div>
