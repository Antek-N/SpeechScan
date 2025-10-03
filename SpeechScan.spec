# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.building.datastruct import Tree

a = Analysis(
    ['src\\speechscan\\__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        Tree('src\\speechscan\\assets', prefix='assets'),
        Tree('src\\speechscan\\ui\\views', prefix='ui\\views'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SpeechScan',
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
    icon=['src\\speechscan\\assets\\img\\icon.ico'],
)
