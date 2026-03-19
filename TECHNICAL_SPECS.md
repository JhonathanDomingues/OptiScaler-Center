# Especificações Técnicas - OptiScaler Center

## 📋 Índice
1. [Detecção de Jogos](#detecção-de-jogos)
2. [Análise de DLLs](#análise-de-dlls)
3. [Sistema de Instalação](#sistema-de-instalação)
4. [Integração GitHub](#integração-github)
5. [Banco de Dados](#banco-de-dados)
6. [Sistema de Configuração](#sistema-de-configuração)
7. [Gerenciamento de Backups](#gerenciamento-de-backups)

---

## 🔍 Detecção de Jogos

### Steam - Windows

#### Localização do Steam
```
C:\Program Files (x86)\Steam\
ou via registro:
HKEY_LOCAL_MACHINE\SOFTWARE\Wow6432Node\Valve\Steam
```

#### Library Folders
```
C:\Program Files (x86)\Steam\steamapps\libraryfolders.vdf
```

Formato VDF:
```
"libraryfolders"
{
    "0"
    {
        "path"        "C:\\Program Files (x86)\\Steam"
        "label"       ""
        "contentid"   "1234567890"
    }
    "1"
    {
        "path"        "D:\\SteamLibrary"
        ...
    }
}
```

#### App Manifests
Localização: `<library_path>/steamapps/appmanifest_<appid>.acf`

Exemplo (`appmanifest_730.acf` - Counter-Strike 2):
```
"AppState"
{
    "appid"           "730"
    "Universe"        "1"
    "name"            "Counter-Strike 2"
    "StateFlags"      "4"
    "installdir"      "Counter-Strike Global Offensive"
    "LastUpdated"     "1710777600"
    "SizeOnDisk"      "32000000000"
    "buildid"         "123456"
    ...
}
```

### Steam - Linux

#### Localizações Padrão
```
~/.steam/steam/
~/.local/share/Steam/
```

#### Paths Relativos (idênticos ao Windows)
```
steamapps/libraryfolders.vdf
steamapps/appmanifest_*.acf
steamapps/common/<game_folder>/
```

#### Jogos Proton/Wine
- Executáveis Windows (.exe) rodando via Proton
- DLLs Windows funcionam diretamente
- Path de prefixo: `steamapps/compatdata/<appid>/pfx/`

### Algoritmo de Detecção

```python
def detect_steam_games():
    """
    1. Detectar SO (Windows/Linux)
    2. Localizar instalação do Steam
    3. Ler libraryfolders.vdf
    4. Para cada library:
        a. Listar arquivos appmanifest_*.acf
        b. Parser VDF de cada manifest
        c. Extrair: appid, name, installdir
        d. Construir path completo do jogo
        e. Verificar se pasta existe
        f. Procurar executável principal
        g. Analisar DLLs presentes
    5. Salvar no banco de dados
    6. Retornar lista de jogos
    """
```

### Detecção de Executável Principal

Heurísticas (em ordem de prioridade):
1. Arquivo com mesmo nome da pasta
2. Executável com maior tamanho
3. Executável com data de modificação mais recente
4. Nome contendo "game", "launcher", nome do jogo

---

## 🔧 Análise de DLLs

### DLLs a Detectar

#### DLSS (NVIDIA)
```
nvngx_dlss.dll          # Windows
libnvidia-ngx-dlss.so   # Linux (raro)
```

Características:
- Tamanho: ~30-50 MB
- Exporta funções NGX
- Geralmente em subpasta `nvngx/` ou raiz

#### FSR (AMD)
```
amd_fidelityfx_*.dll
amd_fidelityfx_dx12.dll
amd_fidelityfx_vk.dll
ffx_fsr2_api_*.dll
```

Características:
- Tamanho: ~5-15 MB
- Múltiplas variantes (DX11, DX12, Vulkan)

#### XeSS (Intel)
```
libxess.dll             # Windows
libxess.so              # Linux
```

Características:
- Tamanho: ~10-20 MB
- Suporte DX11, DX12, Vulkan

### Algoritmo de Análise

```python
def analyze_game_dlls(game_path: Path) -> Dict[str, DLLInfo]:
    """
    1. Escanear recursivamente até 3 níveis de profundidade
    2. Filtrar apenas .dll (Windows) ou .so (Linux)
    3. Para cada arquivo:
        a. Verificar nome contra padrões conhecidos
        b. Extrair metadados (tamanho, data, versão)
        c. Calcular hash SHA256 (para backup)
        d. Identificar tipo (DLSS/FSR/XeSS)
        e. Detectar API gráfica (DX11/DX12/Vulkan)
    4. Retornar dicionário {dll_type: DLLInfo}
    """
```

### Extração de Metadados (Windows)

Usando `win32api` (pywin32):
```python
import win32api

def get_dll_version(dll_path):
    info = win32api.GetFileVersionInfo(dll_path, '\\')
    version = f"{info['FileVersionMS'] >> 16}.{info['FileVersionMS'] & 0xFFFF}"
    return version
```

### Verificação de Exports

Para confirmar tipo de DLL:
```python
import pefile

def check_dll_exports(dll_path):
    pe = pefile.PE(dll_path)
    exports = [exp.name for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols]
    
    if b'NVSDK_NGX' in exports:
        return 'DLSS'
    elif b'ffxFsr2' in exports:
        return 'FSR'
    # ...
```

---

## 📦 Sistema de Instalação

### Estrutura do OptiScaler

Arquivos incluídos em cada release:
```
OptiScaler-v1.x.x/
├── nvngx.dll           # Substitui DLSS
├── amd_fidelityfx_*.dll # Substitui FSR
├── libxess.dll         # Substitui XeSS
├── OptiScaler.ini      # Configuração
└── README.txt
```

### Processo de Instalação

```
┌─────────────────────────┐
│ 1. Verificar DLLs       │
│    suportadas pelo jogo │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│ 2. Criar timestamp      │
│    backup_YYYYMMDD_HHMMSS│
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│ 3. Backup de DLLs       │
│    originais            │
│    data/backups/{game}_│
│    {timestamp}/         │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│ 4. Copiar DLLs          │
│    OptiScaler           │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│ 5. Copiar/criar .ini    │
│    com configurações    │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│ 6. Registrar instalação │
│    no banco de dados    │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│ 7. Verificar integridade│
└─────────────────────────┘
```

### Mapeamento de DLLs

```python
DLL_MAPPING = {
    'DLSS': {
        'original': 'nvngx_dlss.dll',
        'optiscaler': 'nvngx.dll',
        'rename_to': 'nvngx_dlss.dll'
    },
    'FSR': {
        'original': 'amd_fidelityfx_dx12.dll',
        'optiscaler': 'amd_fidelityfx_dx12.dll',
        'rename_to': None  # Mantém nome
    },
    'XeSS': {
        'original': 'libxess.dll',
        'optiscaler': 'libxess.dll',
        'rename_to': None
    }
}
```

### Configuração .ini

Arquivo `OptiScaler.ini`:
```ini
[General]
UpscalerMode=FSR  ; DLSS, FSR, XeSS, Auto
QualityMode=Quality  ; UltraQuality, Quality, Balanced, Performance, UltraPerformance
SharpnessOverride=0.5  ; 0.0-1.0
EnableSharpening=true

[Advanced]
DisableReactiveMask=false
OutputScalingEnabled=false
LogLevel=Info  ; Debug, Info, Warning, Error

[Compatibility]
SkipFirstFrames=0
HookDelay=0
```

### Desinstalação

```
┌─────────────────────────┐
│ 1. Verificar backup     │
│    existe               │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│ 2. Deletar DLLs         │
│    OptiScaler           │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│ 3. Restaurar DLLs       │
│    originais do backup  │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│ 4. Remover .ini         │
│    (opcional)           │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│ 5. Atualizar banco      │
└────────┬────────────────┘
         │
         v
┌─────────────────────────┐
│ 6. Manter backup        │
│    (não deletar auto)   │
└─────────────────────────┘
```

---

## 🌐 Integração GitHub

### API Endpoints

#### Listar Releases
```
GET https://api.github.com/repos/optiscaler/OptiScaler/releases
```

Resposta:
```json
[
  {
    "tag_name": "v1.2.0",
    "name": "OptiScaler v1.2.0",
    "published_at": "2024-03-15T10:00:00Z",
    "body": "## Changes\n- Feature X\n- Bug fix Y",
    "assets": [
      {
        "name": "OptiScaler-v1.2.0-win64.zip",
        "browser_download_url": "https://github.com/.../download/.../file.zip",
        "size": 10485760
      }
    ]
  }
]
```

#### Download de Asset
```python
import requests

def download_release(url: str, save_path: Path):
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(save_path, 'wb') as f:
        downloaded = 0
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            progress = (downloaded / total_size) * 100
            # Emitir sinal de progresso para UI
```

### Cache de Versões

Estrutura:
```
resources/optiscaler_cache/
├── v1.2.0/
│   ├── nvngx.dll
│   ├── amd_fidelityfx_dx12.dll
│   ├── libxess.dll
│   ├── OptiScaler.ini
│   ├── metadata.json
│   └── checksums.txt
├── v1.1.5/
│   └── ...
└── latest -> v1.2.0/  # Symlink
```

metadata.json:
```json
{
  "version": "1.2.0",
  "tag_name": "v1.2.0",
  "download_date": "2024-03-18T15:30:00Z",
  "changelog": "...",
  "files": [
    {
      "name": "nvngx.dll",
      "size": 5242880,
      "sha256": "abc123..."
    }
  ]
}
```

### Verificação de Integridade

```python
import hashlib

def verify_file_integrity(file_path: Path, expected_hash: str) -> bool:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest() == expected_hash
```

---

## 💾 Banco de Dados

### Schema SQLite

```sql
-- Jogos detectados/adicionados
CREATE TABLE games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,
    executable TEXT,
    platform TEXT,  -- 'steam', 'epic', 'gog', 'manual'
    steam_appid INTEGER,
    detected_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_scanned DATETIME,
    notes TEXT
);

-- DLLs detectadas em cada jogo
CREATE TABLE game_dlls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    dll_type TEXT NOT NULL,  -- 'DLSS', 'FSR', 'XeSS'
    dll_path TEXT NOT NULL,
    dll_size INTEGER,
    dll_hash TEXT,
    version TEXT,
    api_type TEXT,  -- 'DX11', 'DX12', 'Vulkan'
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
    UNIQUE(game_id, dll_type)
);

-- Instalações do OptiScaler
CREATE TABLE installations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    version TEXT NOT NULL,
    install_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    backup_path TEXT,
    config_path TEXT,
    status TEXT DEFAULT 'active',  -- 'active', 'removed'
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

-- Versões do OptiScaler em cache
CREATE TABLE optiscaler_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL UNIQUE,
    tag_name TEXT,
    release_date DATETIME,
    download_date DATETIME,
    cache_path TEXT,
    changelog TEXT,
    file_count INTEGER,
    total_size INTEGER
);

-- Backups realizados
CREATE TABLE backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    backup_path TEXT NOT NULL,
    backup_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    file_count INTEGER,
    total_size INTEGER,
    notes TEXT,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

-- Configurações da aplicação
CREATE TABLE app_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Logs de operações
CREATE TABLE operation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_type TEXT NOT NULL,  -- 'install', 'uninstall', 'scan', etc
    game_id INTEGER,
    status TEXT,  -- 'success', 'error', 'warning'
    message TEXT,
    details TEXT,  -- JSON com detalhes
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE SET NULL
);

-- Índices para performance
CREATE INDEX idx_games_platform ON games(platform);
CREATE INDEX idx_installations_game ON installations(game_id);
CREATE INDEX idx_installations_status ON installations(status);
CREATE INDEX idx_logs_operation ON operation_logs(operation_type);
CREATE INDEX idx_logs_created ON operation_logs(created_at);
```

### Repository Pattern

```python
from abc import ABC, abstractmethod
from typing import List, Optional

class GameRepository(ABC):
    @abstractmethod
    def add(self, game: Game) -> int:
        pass
    
    @abstractmethod
    def get_by_id(self, game_id: int) -> Optional[Game]:
        pass
    
    @abstractmethod
    def get_all(self) -> List[Game]:
        pass
    
    @abstractmethod
    def update(self, game: Game) -> bool:
        pass
    
    @abstractmethod
    def delete(self, game_id: int) -> bool:
        pass
    
    @abstractmethod
    def find_by_path(self, path: str) -> Optional[Game]:
        pass

class SQLiteGameRepository(GameRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def add(self, game: Game) -> int:
        # Implementação SQLite
        pass
```

---

## ⚙️ Sistema de Configuração

### Arquivo config.yaml

```yaml
# Configurações Gerais
general:
  language: pt-BR
  theme: dark  # dark, light, auto
  check_updates_on_startup: true
  minimize_to_tray: true

# Paths
paths:
  download_cache: resources/optiscaler_cache
  backups: data/backups
  database: data/games.db
  logs: logs/

# Steam
steam:
  auto_detect: true
  custom_libraries: []
  scan_on_startup: false
  include_proton_games: true  # Linux only

# OptiScaler
optiscaler:
  default_quality: Quality
  default_upscaler: Auto
  auto_backup: true
  keep_old_backups: true
  max_cached_versions: 5

# FSR4 SDK
fsr4_sdk:
  use_int8: false
  default_enabled: false

# Network
network:
  download_threads: 4
  connection_timeout: 30
  max_retries: 3
  use_proxy: false
  proxy_url: null

# Logging
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR
  max_file_size: 10485760  # 10 MB
  backup_count: 5
  console_output: true

# UI
ui:
  window_width: 1200
  window_height: 800
  remember_window_state: true
  show_tooltips: true
  animation_duration: 200

# Advanced
advanced:
  verify_downloads: true
  parallel_installations: false
  developer_mode: false
```

### Gerenciamento de Configuração

```python
from pathlib import Path
import yaml
from typing import Any, Dict

class ConfigManager:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Carrega config do arquivo"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = self._get_default_config()
            self.save()
    
    def save(self):
        """Salva config no arquivo"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, default_flow_style=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtém valor por chave (suporta nested: 'general.theme')"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def set(self, key: str, value: Any):
        """Define valor por chave"""
        keys = key.split('.')
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save()
```

---

## 💾 Gerenciamento de Backups

### Estrutura de Backup

```
data/backups/
└── {game_id}_{game_name_sanitized}/
    └── {timestamp}/
        ├── backup_info.json
        ├── nvngx_dlss.dll
        ├── amd_fidelityfx_dx12.dll
        └── libxess.dll
```

### backup_info.json

```json
{
  "game_id": 123,
  "game_name": "Cyberpunk 2077",
  "game_path": "C:\\Games\\Cyberpunk 2077",
  "backup_date": "2024-03-18T15:30:00Z",
  "reason": "optiscaler_install",
  "files": [
    {
      "original_path": "bin/x64/nvngx_dlss.dll",
      "backup_name": "nvngx_dlss.dll",
      "size": 45678901,
      "sha256": "abc123...",
      "dll_type": "DLSS"
    }
  ],
  "total_size": 45678901,
  "can_restore": true
}
```

### BackupManager

```python
class BackupManager:
    def create_backup(self, game: Game, dll_infos: List[DLLInfo]) -> Backup:
        """
        1. Criar pasta de backup com timestamp
        2. Copiar cada DLL original
        3. Calcular hashes
        4. Criar backup_info.json
        5. Registrar no banco
        6. Retornar objeto Backup
        """
        pass
    
    def restore_backup(self, backup: Backup) -> bool:
        """
        1. Verificar integridade do backup
        2. Para cada arquivo no backup:
            a. Deletar arquivo atual (se existir)
            b. Copiar backup de volta
        3. Verificar sucesso
        4. Atualizar status no banco
        """
        pass
    
    def list_backups(self, game_id: int) -> List[Backup]:
        """Lista todos os backups de um jogo"""
        pass
    
    def delete_backup(self, backup_id: int) -> bool:
        """Deleta um backup do disco e banco"""
        pass
    
    def verify_backup(self, backup: Backup) -> bool:
        """Verifica integridade usando hashes"""
        pass
```

### Política de Limpeza

```python
class BackupCleanupPolicy:
    def should_clean(self, backups: List[Backup]) -> List[Backup]:
        """
        Mantém:
        - Backup mais recente sempre
        - Backups dos últimos 30 dias
        - Máximo de 5 backups por jogo
        
        Remove o resto (mais antigos primeiro)
        """
        pass
```

---

## 🎨 Considerações de UI/UX

### Threading

```python
from PyQt6.QtCore import QThread, pyqtSignal

class ScanGamesWorker(QThread):
    """Worker thread para não travar a UI"""
    progress = pyqtSignal(int, str)  # (percentage, message)
    finished = pyqtSignal(list)  # (games)
    error = pyqtSignal(str)
    
    def run(self):
        try:
            # Operação pesada
            games = scan_steam_games()
            self.finished.emit(games)
        except Exception as e:
            self.error.emit(str(e))
```

### Signals/Slots para Comunicação

```python
class GameInstaller(QObject):
    install_started = pyqtSignal(str)  # game_name
    install_progress = pyqtSignal(int)  # percentage
    install_finished = pyqtSignal(bool, str)  # success, message
```

### Async Operations

```python
async def download_with_progress(url: str, dest: Path, 
                                 progress_callback):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            total = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(dest, 'wb') as f:
                async for chunk in response.content.iter_chunked(8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    progress = (downloaded / total) * 100
                    progress_callback(progress)
```

---

## 🔐 Segurança

### Validação de Paths

```python
def is_safe_path(base_path: Path, target_path: Path) -> bool:
    """Previne path traversal attacks"""
    try:
        target_path.resolve().relative_to(base_path.resolve())
        return True
    except ValueError:
        return False
```

### Verificação de Permissões

```python
def check_write_permission(path: Path) -> bool:
    """Verifica se tem permissão de escrita"""
    try:
        test_file = path / '.write_test'
        test_file.touch()
        test_file.unlink()
        return True
    except (PermissionError, OSError):
        return False
```

---

**Documento atualizado**: 18 de março de 2026
