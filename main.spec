# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # 1. LOCAL CODE PACKAGES (ui and backend)
        # (SOURCE, DESTINATION)
        ('src/ui', 'ui'),
        ('src/backend', 'backend'),
        
        # 2. ASSETS (The 'gorosei.mp3' file and any other assets)
        ('src/assets', 'assets'),
        
        # 3. STORAGE/DATA FILES (If your app reads/writes data files)
        ('src/storage', 'storage'),
    ],
    hiddenimports=['sqlite3', 'spotipy', 'yt_dlp'], # Force inclusion of sqlite3's C library
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
    name='main',
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
    # NOTE: PyInstaller needs a .ico file for Windows, even if Flet handles PNG.
    # It's safest to use a converted ICO file here.
    # If 'logo.png' is the icon, PyInstaller will attempt to convert it.
    icon=['logo.png'],
)