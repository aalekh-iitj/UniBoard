# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for UniBoard.

Builds a one-directory bundle (fast startup) with unused Qt modules and
stdlib packages excluded to minimise size.  Run via:

    python -m PyInstaller build.spec --noconfirm

Non-English Qt locale files are stripped afterwards by build.ps1.
"""

block_cipher = None

# ---------------------------------------------------------------------------
# Qt modules that UniBoard does NOT use.  Excluding them stops PyInstaller
# from bundling their DLLs / plugins (each is 5–40 MB).
#
# KEEP: QtCore, QtGui, QtWidgets, QtNetwork, QtOpenGL (WebEngine fallback),
#       QtSvg (icon engine), QtWebEngineCore, QtWebEngineWidgets, QtWebChannel,
#       QtQuick (required transitively by QtWebEngine resource init on some
#       versions — cheap to keep, excluded only if proven unnecessary).
# ---------------------------------------------------------------------------
QT_EXCLUDES = [
    # 3D
    "PySide6.Qt3DAnimation", "PySide6.Qt3DCore", "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput", "PySide6.Qt3DLogic", "PySide6.Qt3DQuick",
    "PySide6.Qt3DQuickAnimation", "PySide6.Qt3DQuickExtras",
    "PySide6.Qt3DQuickInput", "PySide6.Qt3DRender",
    # Everything else unused
    "PySide6.QtAxContainer",
    "PySide6.QtBluetooth",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization", "PySide6.QtDataVisualizationQml",
    "PySide6.QtDesigner",
    "PySide6.QtGraphs", "PySide6.QtGraphsWidgets",
    "PySide6.QtHelp",
    "PySide6.QtLocation",
    "PySide6.QtMacExtras",
    "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets",
    "PySide6.QtNetworkAuth",
    "PySide6.QtNfc",
    "PySide6.QtPdf", "PySide6.QtPdfWidgets",   # PDF handled by PyMuPDF
    "PySide6.QtPositioning",
    "PySide6.QtPurchasing",
    "PySide6.QtRemoteObjects",
    "PySide6.QtScxml",
    "PySide6.QtSensors",
    "PySide6.QtSerialPort",
    "PySide6.QtSql",
    "PySide6.QtStateMachine",
    "PySide6.QtTest",
    "PySide6.QtTextToSpeech",
    "PySide6.QtUiTools",
    "PySide6.QtWebSockets",
    "PySide6.QtWebView",
    "PySide6.QtWinExtras",
    "PySide6.QtXml",
]

# Stdlib modules never imported by the app or its dependencies.
STDLIB_EXCLUDES = [
    "_tkinter", "tkinter",
    "unittest", "test",
    "pydoc_data",
    "lib2to3",
    "curses",
    "sqlite3",
]

EXCLUDES = QT_EXCLUDES + STDLIB_EXCLUDES


a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=[
        # WebEngine modules are loaded dynamically; make sure they ship.
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebChannel",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="UniBoard",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX disabled globally; enable selectively if desired
    console=False,      # GUI app — no console window
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
    upx=False,
    upx_exclude=[],
    name="UniBoard",
)
