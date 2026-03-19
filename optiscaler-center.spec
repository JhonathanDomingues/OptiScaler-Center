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

# Hidden imports necessários
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'aiohttp',
    'aiofiles',
    'vdf',
    'yaml',
    'colorlog',
    'py7zr',
    'libarchive',
]

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
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
    console=False,  # Não mostrar console (GUI app)
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
    upx_exclude=[],
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
