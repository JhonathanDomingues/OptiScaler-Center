# Changelog

Todas as mudanças notáveis do projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Não Lançado]

### Planejado
- Scanner de jogos Steam (Windows/Linux)
- Análise de DLLs (DLSS, FSR, XeSS)
- Download de versões do OptiScaler
- Instalação/desinstalação do OptiScaler
- Sistema de backup de DLLs
- Configurações por jogo
- Gerenciador de downloads visual

## [0.1.0] - 2026-03-18

### Adicionado - Estrutura Inicial
- 📚 Documentação completa do projeto
  - DOCUMENTATION.md - Documentação técnica completa
  - README.md - Apresentação do projeto
  - TECHNICAL_SPECS.md - Especificações técnicas detalhadas
  - CONTRIBUTING.md - Guia de contribuição
  - PROJECT_SUMMARY.md - Resumo do projeto
  - SETUP.md - Guia de instalação e setup
  - LICENSE - Licença MIT

- 🏗️ Arquitetura Clean Architecture
  - Camada de Apresentação (UI)
  - Camada de Aplicação (Use Cases)
  - Camada de Domínio (Entities, Enums)
  - Camada de Infraestrutura (Services)

- 📁 Estrutura de pastas completa
  - src/ - Código fonte organizado por camadas
  - tests/ - Estrutura para testes (unit, integration)
  - docs/ - Documentação adicional
  - data/ - Banco de dados e backups
  - resources/ - Recursos (FSR4 SDK, cache)
  - logs/ - Sistema de logs

- 💻 Código base implementado
  - src/main.py - Entry point da aplicação
  - src/utils/constants.py - Constantes globais
  - src/utils/logger.py - Sistema de logging com rotação
  - src/presentation/main_window.py - Janela principal PyQt6
  - src/infrastructure/config/config_service.py - Gerenciamento de configurações YAML
  - src/infrastructure/database/db_service.py - Gerenciamento de SQLite

- 🎯 Entidades do Domínio
  - Game - Representação de jogo
  - DLLInfo - Informações de DLL detectada
  - Installation - Registro de instalação
  - OptiScalerVersion - Versão do OptiScaler
  - Backup - Registro de backup

- 📊 Enums
  - DLLType - Tipos de DLL (DLSS, FSR, XeSS)
  - APIType - APIs gráficas (DX11, DX12, Vulkan)
  - InstallationStatus - Status de instalação
  - OperationStatus - Status de operações
  - Platform - Plataformas de jogos
  - OperatingSystem - Sistemas operacionais

- 🗄️ Schema de Banco de Dados
  - Tabela games - Jogos gerenciados
  - Tabela game_dlls - DLLs detectadas
  - Tabela installations - Instalações do OptiScaler
  - Tabela optiscaler_versions - Versões em cache
  - Tabela backups - Backups realizados
  - Tabela app_settings - Configurações
  - Tabela operation_logs - Logs de operações
  - Índices para performance

- 📦 Dependências
  - PyQt6 - Framework de UI
  - requests - Cliente HTTP
  - aiohttp - Cliente HTTP assíncrono
  - vdf - Parser de arquivos Steam
  - psutil - Utilitários de sistema
  - PyYAML - Parser YAML
  - colorlog - Logs coloridos

- 🎨 Interface Base
  - Janela principal com abas
  - Layout responsivo
  - Tema escuro implementado
  - Placeholders para desenvolvimento futuro

- 📦 FSR4 SDK
  - DLLs FSR4 organizadas (standard e int8)
  - 4 arquivos copiados para estrutura do projeto

- 🔧 Configuração
  - requirements.txt - Dependências de produção
  - requirements-dev.txt - Dependências de desenvolvimento
  - .gitignore - Arquivos ignorados pelo Git
  - Configuração padrão completa em YAML

### Decidido - Decisões de Design
- Python 3.10+ como linguagem base
- PyQt6 para interface gráfica
- SQLite para banco de dados
- YAML para configuração
- Clean Architecture para organização
- MIT License para máxima liberdade

### Documentado
- Roadmap de 4 fases detalhado
- 10+ melhorias sugeridas
- Fluxos de trabalho ilustrados
- Especificações técnicas completas
- Guias de contribuição e setup
- Código de conduta

---

## Legenda de Tipos de Mudança

- **Adicionado** - para novas funcionalidades
- **Modificado** - para mudanças em funcionalidades existentes
- **Descontinuado** - para funcionalidades que serão removidas
- **Removido** - para funcionalidades removidas
- **Corrigido** - para correção de bugs
- **Segurança** - para vulnerabilidades corrigidas

---

[Não Lançado]: https://github.com/seu-usuario/optiscaler-center/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/seu-usuario/optiscaler-center/releases/tag/v0.1.0
