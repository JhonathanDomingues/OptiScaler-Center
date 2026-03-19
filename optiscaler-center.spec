# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for OptiScaler Center
"""

import sys
import os
from pathlib import Path

block_cipher = None

# Detectar plataforma
is_windows = sys.platform.startswith('win')
is_linux = sys.platform.startswith('linux')

# Configurar nome do executável e extensão
exe_name = 'OptiScalerCenter'
if is_windows:
    exe_name += '.exe'

# Adicionar data files (recursos, configurações, etc) - apenas se existirem
datas = []

# Adicionar apenas arquivos que existem
optional_files = [
    ('README.md', '.'),
    ('LICENSE', '.'),
]

for src, dst in optional_files:
    if os.path.exists(src):
        datas.append((src, dst))

# Adicionar diretórios que existem
optional_dirs = [
    ('resources/fsr4_sdk', 'resources/fsr4_sdk'),
]

for src, dst in optional_dirs:
    if os.path.exists(src):
        datas.append((src, dst))

# Hidden imports necessários - PyQt6 completo
hiddenimports = [
    # PyQt6 core
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtSvg',
    'PyQt6.sip',
    
    # Backends Qt
    'PyQt6.QtCore.Qt',
    
    # HTTP e async
    'aiohttp',
    'aiofiles',
    'aiohttp.connector',
    'aiohttp.client',
    'aiohttp.http',
    'async_timeout',
    
    # Steam/VDF
    'vdf',
    
    # Config
    'yaml',
    
    # Logging
    'colorlog',
    'colorlog.colorlog',
    
    # Arquivos compactados
    'py7zr',
    'py7zr.properties',
    'py7zr.archiveinfo',
    'libarchive',
    
    # Outros
    'requests',
    'psutil',
    'appdirs',
    'dateutil',
    'dateutil.parser',
    'packaging',
    'packaging.version',

    # Módulos do próprio app (src/)
    'utils',
    'utils.logger',
    'utils.constants',
    'infrastructure',
    'infrastructure.config',
    'infrastructure.config.config_service',
    'infrastructure.database',
    'infrastructure.database.db_service',
    'infrastructure.filesystem',
    'infrastructure.github',
    'infrastructure.github.github_service',
    'infrastructure.steam',
    'infrastructure.steam.steam_service',
    'infrastructure.steam.vdf_parser',
    'domain',
    'domain.entities',
    'domain.entities.backup',
    'domain.entities.dll_info',
    'domain.entities.game',
    'domain.entities.installation',
    'domain.entities.optiscaler_version',
    'domain.enums',
    'domain.enums.dll_type',
    'domain.enums.installation_status',
    'domain.enums.platform',
    'domain.repositories',
    'domain.repositories.backup_repository',
    'domain.repositories.game_repository',
    'domain.repositories.installation_repository',
    'domain.repositories.version_repository',
    'application',
    'application.services',
    'application.services.dll_analyzer',
    'application.services.game_scanner',
    'application.use_cases',
    'application.use_cases.download_version',
    'application.use_cases.fetch_versions',
    'application.use_cases.install_optiscaler',
    'application.use_cases.scan_games',
    'application.use_cases.uninstall_optiscaler',
    'presentation',
    'presentation.main_window',
    'presentation.resources',
    'presentation.resources.app_icon',
    'presentation.styles',
    'presentation.styles.modern_theme',
    'presentation.widgets',
]

# Binaries específicos (vazio por padrão, PyInstaller detecta automaticamente)
binaries = []

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'tkinter',
        'unittest',
        'pytest',
        '_pytest',
        'IPython',
        'notebook',
        'tornado',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # TEMPORARIAMENTE habilitado para debug - mudar para False após testar
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # TODO: Adicionar ícone .ico/.icns se disponível
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[
        # Excluir DLLs Qt do UPX para evitar corrupção
        'Qt6Core.dll',
        'Qt6Gui.dll',
        'Qt6Widgets.dll',
        'Qt6Svg.dll',
        'libQt6Core.so.6',
        'libQt6Gui.so.6',
        'libQt6Widgets.so.6',
        'libQt6Svg.so.6',
    ],
    name='OptiScalerCenter',
)

# Para MacOS, criar app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='OptiScalerCenter.app',
        icon=None,
        bundle_identifier='com.optiscaler.center',
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
        },
    )
