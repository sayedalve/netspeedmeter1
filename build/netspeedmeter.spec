# netspeedmeter.spec
# PyInstaller build spec for the focused internet speed meter.
# Removed: matplotlib, graph window, hardware monitoring hooks.

block_cipher = None

my_hidden_imports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'psutil',
    'win32api',
    'win32com.shell.shell',
    'numpy',
    'signal',
    'wmi',
]

a = Analysis(
    ['..\\src\\speedmeter.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('..\\assets', 'assets'),
        ('..\\src\\speed_core\\constants\\locales', 'speed_core/constants/locales'),
    ],
    hiddenimports=my_hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    # Exclude heavy libs that are no longer needed
    excludes=['pandas', 'matplotlib', 'scipy', 'sklearn'],
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
    a.binaries,
    a.datas,
    name='NetSpeedMeter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='..\\assets\\speed_core.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='NetSpeedMeter',
)
