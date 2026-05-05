# PyInstaller — pasta completa (onedir) para o Setup.exe
# Executa NA RAIZ do projeto:  pyinstaller --noconfirm installer/PINK-IPTV-onedir.spec
# Saída: dist\PINK-IPTV\

# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

block_cipher = None

flet_datas, flet_binaries, flet_hidden = collect_all('flet')
flet_desktop_datas, flet_desktop_binaries, flet_desktop_hidden = collect_all(
    'flet_desktop'
)
vlc_datas, vlc_binaries, vlc_hidden = collect_all('vlc')

_spec_path = Path(SPEC)
_project_root = (
    _spec_path.parent.parent
    if _spec_path.parent.name.lower() == 'installer'
    else _spec_path.parent
)
_flet_win_zip = _project_root / 'build-assets' / 'flet-windows.zip'
_flet_offline = (
    [(str(_flet_win_zip.resolve()), os.path.join('flet_desktop', 'app'))]
    if _flet_win_zip.is_file()
    else []
)

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=vlc_binaries + flet_binaries + flet_desktop_binaries,
    datas=flet_datas + vlc_datas + flet_desktop_datas + _flet_offline,
    hiddenimports=[
        'vlc',
        'httpx',
        'xtream',
        'vpn',
        'flet_desktop',
        'flet_desktop.version',
    ] + flet_hidden + vlc_hidden + flet_desktop_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['flask', 'jinja2', 'werkzeug', 'click', 'itsdangerous'],
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
    name='PINK-IPTV',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='PINK-IPTV',
)
