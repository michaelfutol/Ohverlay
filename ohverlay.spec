# -*- mode: python ; coding: utf-8 -*-
"""
Ohverlay - PyInstaller Spec File
Builds a portable Windows executable
"""

import sys
import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('fireflies-overlay.html', '.'),
        ('dragonflies-overlay.html', '.'),
        ('marketplace-overlays/butterflies-overlay.html', 'marketplace-overlays'),
        ('marketplace-overlays/butterflies-blue-overlay.html', 'marketplace-overlays'),
        ('marketplace-overlays/butterflies-yellow-overlay.html', 'marketplace-overlays'),
        ('marketplace-overlays/butterflies-orange-overlay.html', 'marketplace-overlays'),
        ('dandelions-overlay.html', '.'),
        ('marketplace-overlays/cosmos-overlay.html', 'marketplace-overlays'),
        ('marketplace-overlays/assets/cosmos-sulphureus-flower.png', 'marketplace-overlays/assets'),
        ('marketplace-overlays/orchid-overlay.html', 'marketplace-overlays'),
        ('marketplace-overlays/moon-overlay.html', 'marketplace-overlays'),
        ('windows_file_version_info.txt', '.'),
    ],
    hiddenimports=[
        'ui.tray',
        'modules.overlay_manager',
        'config.settings',
        'utils.logger',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineCore',
        'pynput',
        'pynput.keyboard',
        'pynput.keyboard._win32',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'pytest_qt',
        'hypothesis',
        'black',
        'flake8',
        'mypy',
        'pylint',
        'isort',
        'sphinx',
        'jupyter',
        'IPython',
        'notebook',
        'matplotlib',
        'tkinter',
        '_tkinter',
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
    name='Ohverlay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='windows_file_version_info.txt',
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Ohverlay',
)
