# PyInstaller Spec — PINK IPTV
# Gera um único PINK-IPTV.exe com tudo dentro (codecs, VPN, dependências).

# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# Recolhe tudo do Flet, VLC e httpx
flet_datas, flet_binaries, flet_hidden = collect_all('flet')
vlc_datas, vlc_binaries, vlc_hidden = collect_all('vlc')

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=vlc_binaries + flet_binaries,
    datas=[
        ('vpn_config.conf', '.'),
        ('profiles.json', '.'),
    ] + flet_datas + vlc_datas,
    hiddenimports=[
        'vlc',
        'httpx',
        'xtream',
        'vpn',
    ] + flet_hidden + vlc_hidden,
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PINK-IPTV',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
