# PyInstaller spec for Mesh desktop app.
# Builds Mesh.app on macOS, Mesh.exe on Windows, Mesh on Linux.

import sys
from pathlib import Path

ROOT = Path(SPECPATH)

datas = [
    (str(ROOT / "frontend" / "dist"), "frontend/dist"),
    (str(ROOT / "backend"), "backend"),
]

hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "websockets",
    "bleak",
    "fastapi",
]

if sys.platform == "darwin":
    hiddenimports += [
        "objc",
        "Foundation",
        "MultipeerConnectivity",
    ]


a = Analysis(
    ["desktop.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Mesh",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="Mesh.app",
        icon=None,
        bundle_identifier="dev.synth.mesh",
        info_plist={
            "NSHighResolutionCapable": True,
            "NSLocalNetworkUsageDescription": "Mesh needs local network access to discover peers.",
            "NSBluetoothAlwaysUsageDescription": "Mesh uses Bluetooth to discover nearby devices.",
            "LSBackgroundOnly": False,
        },
    )
