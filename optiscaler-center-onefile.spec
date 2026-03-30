# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for OptiScaler Center - ONEFILE VERSION
Use se a versão onedir apresentar problemas de DLL no Windows
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
    ('resources/locales',  'resources/locales'),
    ('resources/icons',    'resources/icons'),
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
]

# Binaries específicos (vazio por padrão, PyInstaller detecta automaticamente)
binaries = []

a = Analysis(
    ['src/main.py'],
    pathex=[],
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

# ONEFILE - Um único executável
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Desabilitar UPX em onefile para maior compatibilidade
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # TEMPORARIAMENTE habilitado para debug - mudar para False após testar
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
