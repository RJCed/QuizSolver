# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('paths.py', '.'), ('config.py', '.'), ('gui.py', '.'), ('bot.py', '.'), ('screenshot.py', '.'), ('clicker.py', '.'), ('ai_solver.py', '.')],
    hiddenimports=['customtkinter', 'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageTk', 'cv2', 'numpy', 'requests', 'dotenv', 'keyboard', 'pyautogui'],
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
    [],
    exclude_binaries=True,
    name='QuizSolver',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='QuizSolver',
)
