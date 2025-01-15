# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(
    ["eyetrackvr_backend/__main__.py"],
    pathex=[],
    binaries=[],
    datas=[
      ("eyetrackvr_backend/assets", "eyetrackvr_backend/assets")
    ],
    hiddenimports=["cv2", "numpy"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='ETVR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="eyetrackvr_backend/assets/images/logo.ico"
)
