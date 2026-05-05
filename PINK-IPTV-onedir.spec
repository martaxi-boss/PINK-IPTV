# PyInstaller — pasta completa (onedir) para o Setup.exe
# Executa NA RAIZ do projeto:  pyinstaller --noconfirm installer/PINK-IPTV-onedir.spec
# Saída: dist\PINK-IPTV\

# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all

block_cipher = None

flet_datas, flet_binaries, flet_hidden = collect_all('flet')
vlc_datas, vlc_binaries, vlc_hidden = collect_all('vlc')

a = Analysis(
    ['app.py'],
    pathex=['.'],
    binaries=vlc_binaries + flet_binaries,
    datas=flet_datas + vlc_datas,
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
    [],
    exclude_binaries=True,
    name='PINK-IPTV',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='PINK-IPTV',
)
