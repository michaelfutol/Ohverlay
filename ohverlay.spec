# -*- mode: python ; coding: utf-8 -*-
"""
Ohverlay - PyInstaller Spec File
Builds a portable Windows executable
"""

import sys
import os

block_cipher = None

# Single source of truth: every overlay HTML (and its bundled assets) is derived
# from the overlay registry, so the build can never drift from the app.
_spec_dir = globals().get('SPECPATH', os.path.abspath('.'))
sys.path.insert(0, _spec_dir)
from modules.overlay_registry import bundled_data_files
OVERLAY_DATAS = list(bundled_data_files())

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('windows_file_version_info.txt', '.'),
    ] + OVERLAY_DATAS,
    hiddenimports=[
        'ui.tray',
        'modules.overlay_manager',
        'config.settings',
        'modules.overlay_registry',
        'modules.telegrama_service',
        'modules.telegrama_controller',
        'ui.telegrama_dialog',
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
