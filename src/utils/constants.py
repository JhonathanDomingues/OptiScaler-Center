"""
Constantes globais do OptiScaler Center
"""
import os
import sys
from pathlib import Path

# Informações da aplicação
APP_NAME = "OptiScaler Center"
APP_VERSION = "0.1.7"
APP_AUTHOR = "OptiScaler Center Team"
APP_DESCRIPTION = "Gerenciador visual para instalação do OptiScaler"

# Detectar se está rodando como executável PyInstaller
if getattr(sys, 'frozen', False):
    # Rodando como executável empacotado (PyInstaller / AppImage)
    # O executável pode estar num filesystem somente-leitura (AppImage),
    # por isso dados graváveis ficam em ~/.local/share/optiscaler-center/
    BASE_DIR = Path(sys.executable).parent
    SRC_DIR = BASE_DIR  # No executável, tudo está no mesmo nível
    _xdg_data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    USER_DATA_DIR = _xdg_data / "optiscaler-center"
    # Recursos somente-leitura (locales, ícones, sdk) ficam em _MEIPASS no PyInstaller
    _meipass = Path(getattr(sys, '_MEIPASS', BASE_DIR))
    RESOURCES_DIR = _meipass / "resources"
else:
    # Rodando como script Python normal
    BASE_DIR = Path(__file__).parent.parent.parent
    SRC_DIR = Path(__file__).parent.parent
    USER_DATA_DIR = BASE_DIR
    RESOURCES_DIR = BASE_DIR / "resources"

# Paths graváveis (usam USER_DATA_DIR quando empacotado)
DATA_DIR = USER_DATA_DIR / "data"
LOGS_DIR = USER_DATA_DIR / "logs"

# Paths específicos
DATABASE_PATH = DATA_DIR / "games.db"
CONFIG_PATH = DATA_DIR / "config.yaml"
BACKUPS_DIR = DATA_DIR / "backups"
CACHE_DIR = USER_DATA_DIR / "optiscaler_cache"  # gravável
FSR4_SDK_DIR       = RESOURCES_DIR / "fsr4_sdk"         # somente-leitura (bundled)
FSR4_USER_SDK_DIR  = USER_DATA_DIR / "fsr4_sdk"         # gravável (DLLs adicionadas pelo usuário)
LOCALES_DIR        = RESOURCES_DIR / "locales"          # somente-leitura (bundled)

# URLs
OPTISCALER_REPO = "cdozdil/OptiScaler"
GITHUB_API_BASE = "https://api.github.com"
GITHUB_RELEASES_URL = f"{GITHUB_API_BASE}/repos/{OPTISCALER_REPO}/releases"

# DLL Types
DLL_TYPES = {
    'DLSS': {
        'patterns': ['nvngx_dlss.dll', 'nvngx.dll'],
        'display_name': 'NVIDIA DLSS',
        'color': '#76B900'  # NVIDIA Green
    },
    'FSR': {
        'patterns': ['amd_fidelityfx*.dll', 'ffx_fsr*.dll'],
        'display_name': 'AMD FSR',
        'color': '#ED1C24'  # AMD Red
    },
    'XeSS': {
        'patterns': ['libxess.dll', 'libxess*.dll'],
        'display_name': 'Intel XeSS',
        'color': '#0071C5'  # Intel Blue
    }
}

# Platform detection
PLATFORMS = {
    'steam': {
        'name': 'Steam',
        'color': '#1B2838',
        'icon': 'steam.png'
    },
    'epic': {
        'name': 'Epic Games',
        'color': '#0078F2',
        'icon': 'epic.png'
    },
    'gog': {
        'name': 'GOG',
        'color': '#B9A6FF',
        'icon': 'gog.png'
    },
    'manual': {
        'name': 'Manual',
        'color': '#808080',
        'icon': 'generic.png'
    }
}

# Steam paths (Windows)
STEAM_PATHS_WINDOWS = [
    "C:\\Program Files (x86)\\Steam",
    "C:\\Program Files\\Steam",
]

# Steam paths (Linux)
STEAM_PATHS_LINUX = [
    Path.home() / ".steam" / "steam",
    Path.home() / ".local" / "share" / "Steam",
]

# Registry keys (Windows)
STEAM_REGISTRY_KEY = r"SOFTWARE\Wow6432Node\Valve\Steam"
STEAM_REGISTRY_PATH_VALUE = "InstallPath"

# File patterns
STEAM_LIBRARY_FILE = "libraryfolders.vdf"
STEAM_MANIFEST_PATTERN = "appmanifest_*.acf"

# OptiScaler files
OPTISCALER_FILES = {
    'DLSS': 'nvngx.dll',
    'FSR': 'amd_fidelityfx_dx12.dll',
    'XeSS': 'libxess.dll',
    'CONFIG': 'OptiScaler.ini'
}

# Quality modes
QUALITY_MODES = [
    {'value': 'UltraQuality', 'display': 'Ultra Quality', 'scale': 1.3},
    {'value': 'Quality', 'display': 'Quality', 'scale': 1.5},
    {'value': 'Balanced', 'display': 'Balanced', 'scale': 1.7},
    {'value': 'Performance', 'display': 'Performance', 'scale': 2.0},
    {'value': 'UltraPerformance', 'display': 'Ultra Performance', 'scale': 3.0},
]

# Upscaler modes
UPSCALER_MODES = ['Auto', 'DLSS', 'FSR', 'XeSS']

# Log levels
LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR']

# Default configuration
DEFAULT_CONFIG = {
    'general': {
        'language': 'pt_BR',
        'theme': 'dark',
        'check_updates_on_startup': True,
        'minimize_to_tray': True
    },
    'paths': {
        'download_cache': str(CACHE_DIR),
        'backups': str(BACKUPS_DIR),
        'database': str(DATABASE_PATH),
        'logs': str(LOGS_DIR)
    },
    'steam': {
        'auto_detect': True,
        'custom_libraries': [],
        'scan_on_startup': False,
        'include_proton_games': True
    },
    'optiscaler': {
        'default_quality': 'Quality',
        'default_upscaler': 'Auto',
        'auto_backup': True,
        'keep_old_backups': True,
        'max_cached_versions': 5
    },
    'fsr4_sdk': {
        'use_int8': False,
        'default_enabled': False,
        # Permite sobrepor as DLLs padrão com caminhos externos (str)
        'custom_standard_dlls': {},     # {'amd_fidelityfx_dx12.dll': '/path/to/dll', ...}
        'custom_int8_versions': {},     # {'4.0.1': '/path/to/dll', '4.0.2c': '/path/to/dll'}
    },
    'github': {
        'token': '',                             # Personal Access Token (para baixar artefatos de Actions)
        'stable_repo': 'cdozdil/OptiScaler',
        'beta_repo': 'cdozdil/OptiScaler',
        'beta_workflow': 'release_debug.yml',
        'beta_branch_pattern': r'release/0\.[0-9].*',
        'show_betas': False,
    },
    'network': {
        'download_threads': 4,
        'connection_timeout': 30,
        'max_retries': 3,
        'use_proxy': False,
        'proxy_url': None
    },
    'logging': {
        'level': 'INFO',
        'max_file_size': 10485760,  # 10 MB
        'backup_count': 5,
        'console_output': True
    },
    'ui': {
        'window_width': 1200,
        'window_height': 800,
        'remember_window_state': True,
        'show_tooltips': True,
        'animation_duration': 200
    },
    'advanced': {
        'verify_downloads': True,
        'parallel_installations': False,
        'developer_mode': False
    }
}

# UI Colors (Dark Theme)
COLORS_DARK = {
    'background': '#1e1e1e',
    'surface': '#2d2d2d',
    'primary': '#007acc',
    'secondary': '#00d9ff',
    'accent': '#ff6b00',
    'success': '#4caf50',
    'warning': '#ff9800',
    'error': '#f44336',
    'text': '#ffffff',
    'text_secondary': '#b0b0b0',
    'border': '#3e3e3e'
}

# UI Colors (Light Theme)
COLORS_LIGHT = {
    'background': '#ffffff',
    'surface': '#f5f5f5',
    'primary': '#0078d4',
    'secondary': '#00b7c3',
    'accent': '#ff8c00',
    'success': '#107c10',
    'warning': '#ff8c00',
    'error': '#e81123',
    'text': '#000000',
    'text_secondary': '#605e5c',
    'border': '#e1dfdd'
}

# File size units
SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB']

# Date format
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
DATE_FORMAT_SHORT = '%Y-%m-%d'

# Max values
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_CACHE_SIZE = 1024 * 1024 * 1024  # 1 GB
MAX_CONCURRENT_DOWNLOADS = 3
