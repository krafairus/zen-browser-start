# zen-browser-start.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['zen-browser-start.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources/logo.png', 'resources'),
        ('resources/zn_en.qm', 'resources'),
        ('resources/zn_pt.qm', 'resources')
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui', 
        'PySide6.QtWidgets',
        'shiboken6',
        'bs4',
        'requests',
        'logging',  # Añadido
        'urllib.parse',
        'urllib.request'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # SOLO excluir paquetes muy pesados que NO son esenciales
        'matplotlib', 
        'pandas', 
        'numpy', 
        'scipy',
        'tkinter',
        
        # NO excluir estos módulos esenciales:
        # 'logging',    # NECESARIO para shiboken6
        # 'email',      # Puede ser necesario
        # 'http',       # Puede ser necesario
        # 'ssl',        # Puede ser necesario para requests
        # 'multiprocessing', # Puede ser necesario
        
        # Módulos PySide6 opcionales (pueden excluirse de forma segura)
        'PySide6.QtBluetooth',
        'PySide6.QtCharts', 
        'PySide6.QtDataVisualization',
        'PySide6.QtHelp', 
        'PySide6.QtLocation', 
        'PySide6.QtMultimedia',
        'PySide6.QtNetwork',
        'PySide6.QtOpenGL', 
        'PySide6.QtOpenGLWidgets',
        'PySide6.QtPdf', 
        'PySide6.QtPositioning', 
        'PySide6.QtPrintSupport',
        'PySide6.QtQml', 
        'PySide6.QtQuick', 
        'PySide6.QtQuick3D',
        'PySide6.QtQuickWidgets', 
        'PySide6.QtRemoteObjects', 
        'PySide6.QtSensors',
        'PySide6.QtSerialPort', 
        'PySide6.QtSql', 
        'PySide6.QtSvg',
        'PySide6.QtTest', 
        'PySide6.QtTextToSpeech', 
        'PySide6.QtWebChannel',
        'PySide6.QtWebEngineCore', 
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebSockets', 
        'PySide6.QtXml', 
        'PySide6.QtXmlPatterns',
        'PySide6.3DCore', 
        'PySide6.3DRender', 
        'PySide6.3DInput',
        'PySide6.3DLogic', 
        'PySide6.3DAnimation', 
        'PySide6.3DExtras'
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='zen-browser-start',
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
    icon=['resources/logo.png'],
)