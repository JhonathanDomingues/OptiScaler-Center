# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [Unreleased]

## [0.1.6] - 2026-04-13

### Adicionado
- Validação pré-instalação: quando nenhum `.exe` é encontrado no diretório determinado, o instalador busca automaticamente por DLLs conhecidas (`amd_fidelityfx_upscaler_dx12.dll`, `nvngx_dlss.dll`, `libxess.dll`, etc.) para localizar o diretório correto
- Suporte a jogos adicionados manualmente (não detectados pela Steam) via botão **"➕ Adicionar Jogo"** na barra de ferramentas
- Diálogo `AddManualGameDialog` com campo de nome, seletor de pasta e auto-preenchimento do nome pelo diretório escolhido
- Jogos manuais são analisados automaticamente para detectar DLLs de upscaling e persistidos com `platform=MANUAL`
- Jogos adicionados manualmente são preservados após novas varreduras Steam

### Corrigido
- Após varredura Steam, a lista de jogos agora recarrega todos os jogos do banco (incluindo os manuais), evitando que sumissem da exibição
- Conteúdo duplicado removido do README.md

### Manutenção
- `.gitignore` atualizado para excluir ferramentas de desenvolvimento local

## [0.1.5] - 2026-03-30

### Adicionado
- Diálogo de Configurações completo (aba Geral, GitHub e FSR4 SDK)
- Configuração de token GitHub PAT para downloads de builds beta via GitHub Actions
- Suporte a downloads de builds beta com opção de ativar/desativar
- DLLs AMD FidelityFX Upscaler versões INT8: **4.0.1** e **4.0.2c**
- Opção de substituir DLLs FSR4 padrão por versão externa sem modificar código
- Opção de adicionar e remover versões INT8 customizadas
- Internacionalização (i18n) completa com suporte a **Português (PT-BR)** e **English**
- Troca de idioma em tempo real sem reiniciar o aplicativo
- Detecção de pastas UE4/UE5 para seleção correta da DLL loader (`winmm.dll`)
- Subpasta versionada para DLLs INT8 (estrutura `int8/<versão>/`)

### Melhorado
- Refatoração geral da estrutura de código para maior legibilidade e manutenibilidade
- i18n funcionando corretamente no AppImage (caminhos resolvidos em modo frozen)
- Detecção da subpasta correta ao instalar versões INT8

### Corrigido
- Caminhos de i18n no AppImage em modo Read-only filesystem
- Ordem de subpasta para DLLs INT8 versionadas

## [0.1.3] - 2026-03-19

### Adicionado
- Sistema de build automatizado com **GitHub Actions** (Windows e Linux)
- Suporte à geração de **AppImage** para Linux (sem dependências de instalação)
- Script `build-appimage.sh` para criação do AppImage com Pillow
- Script `build.sh` e `build.bat` para compilação via PyInstaller
- Arquivo `config.example.yaml` incluído no bundle para builds automatizados
- Spec PyInstaller com `hidden imports` completos do PyQt6 e versão onefile
- **Ícone profissional** do aplicativo gerado via script Python com Pillow
- Guia de troubleshooting para builds (`TROUBLESHOOTING.md`)
- Suporte a `libarchive` para extração de arquivos e salvamento de manifesto de instalação
- Detecção automática de arquivos do OptiScaler na desinstalação
- Gerenciamento avançado de versões do OptiScaler (download, cache local, listagem)
- `GameCardWidget` responsivo com layout otimizado

### Melhorado
- Spec do PyInstaller corrigido e expandido com imports completos
- AppRun do AppImage corrigido (heredoc com indentação inválida quebrava o shebang)
- Paths corrigidos para compatibilidade com executável PyInstaller (`sys._MEIPASS`)
- Suporte a console de debug no executável PyInstaller
- `sys.path` corrigido em modo frozen para localizar módulos `src/`

### Corrigido
- Caminhos graváveis no AppImage (sistema de arquivos Read-only)
- `main()` restaurada após remoção acidental
- Indentação e legibilidade do código em `main.py`
- Sintaxe do arquivo spec corrompido
- Geração de ícone substituída de ImageMagick para Pillow (compatibilidade)

## [0.0.1] - 2026-03-18

### Adicionado
- Versão inicial do **OptiScaler Center**
- Estrutura base seguindo **Clean Architecture** (presentation, application, domain, infrastructure)
- Interface gráfica com **PyQt6** — tema dark estilo Steam (`#1b2838`)
- Grid de jogos com cards visuais, capas carregadas da Steam e badges de tecnologia (DLSS/FSR/XeSS)
- Scanner automático de bibliotecas Steam (Windows e Linux via VDF parser)
- Análise inteligente de DLLs compatíveis por jogo (DLSS, FSR, XeSS)
- Download de releases do OptiScaler via GitHub API
- Instalação e desinstalação com **backup automático** dos arquivos originais
- Suporte ao **FSR4 SDK** com DLLs padrão (`standard/`) e versões INT8
- Banco de dados **SQLite** para persistência de dados
- Configuração via arquivo **YAML** (`data/config.yaml`)
- Sistema de **logging** integrado
- Responsividade do grid de jogos
- Priorização de imagens verticais nos cards (evitar distorção de imagens horizontais)
- Ícone de controle nos cards de jogo

[Unreleased]: https://github.com/JhonathanDomingues/OptiScaler-Center/compare/v0.1.6...HEAD
[0.1.6]: https://github.com/JhonathanDomingues/OptiScaler-Center/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/JhonathanDomingues/OptiScaler-Center/releases/tag/v0.1.5
[0.1.3]: https://github.com/JhonathanDomingues/OptiScaler-Center/releases/tag/v0.1.3
[0.0.1]: https://github.com/JhonathanDomingues/OptiScaler-Center/compare/fbc49b5...v0.1.3
