"""
Mesh desktop app.

Starts the FastAPI server in a background thread, opens a native window
pointing at http://localhost:8000. Menu: Check for updates, Apply update, Restart.

Run:
    python desktop.py
"""

import os
import sys
import threading
import time
import urllib.request
from pathlib import Path

import webview

# When bundled by PyInstaller, data files live in sys._MEIPASS
if hasattr(sys, "_MEIPASS"):
    ROOT = Path(sys._MEIPASS)
    BUNDLED = True
else:
    ROOT = Path(__file__).parent
    BUNDLED = False

BACKEND = ROOT / "backend"
DIST = ROOT / "frontend" / "dist"
HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}/"


def _ensure_frontend_built() -> bool:
    if (DIST / "index.html").exists():
        return True
    if BUNDLED:
        # Bundled binary should already have dist embedded; missing means a build problem.
        print("[desktop] FATAL: frontend dist missing from bundle")
        return False
    print("[desktop] frontend not built; building now (npm run build)...")
    import subprocess
    fe = ROOT / "frontend"
    if not (fe / "node_modules").exists():
        try:
            subprocess.run(["npm", "install"], cwd=fe, check=True)
        except Exception as e:
            print(f"[desktop] npm install failed: {e}")
            return False
    try:
        subprocess.run(["npm", "run", "build"], cwd=fe, check=True)
        return (DIST / "index.html").exists()
    except Exception as e:
        print(f"[desktop] npm build failed: {e}")
        return False


def _start_server() -> None:
    sys.path.insert(0, str(BACKEND))
    import server  # noqa: F401
    import uvicorn
    uvicorn.run(server.app, host=HOST, port=PORT, log_level="warning")


def _wait_for_server(timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://{HOST}:{PORT}/platform", timeout=1) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


class API:
    """JS-callable bridge."""

    def check_for_updates(self) -> dict:
        with urllib.request.urlopen(f"http://{HOST}:{PORT}/version") as r:
            import json
            return json.loads(r.read())

    def apply_update(self) -> dict:
        req = urllib.request.Request(f"http://{HOST}:{PORT}/update", method="POST")
        with urllib.request.urlopen(req, timeout=180) as r:
            import json
            return json.loads(r.read())

    def restart(self) -> None:
        """Re-exec the current process to load updated code."""
        # Force flush + exec
        sys.stdout.flush()
        os.execv(sys.executable, [sys.executable, __file__])


def main() -> None:
    _ensure_frontend_built()

    t = threading.Thread(target=_start_server, daemon=True)
    t.start()

    if not _wait_for_server():
        print("[desktop] server did not start in time")
        return

    window = webview.create_window(
        title="Mesh",
        url=URL,
        width=1100,
        height=720,
        min_size=(800, 500),
        js_api=API(),
    )

    def _add_menu():
        # Inject a tiny floating update button via JS that calls the bridge
        js = """
        (() => {
          if (document.getElementById('mesh-update-btn')) return;
          const b = document.createElement('button');
          b.id = 'mesh-update-btn';
          b.textContent = 'Check for updates';
          Object.assign(b.style, {
            position: 'fixed', top: '12px', right: '12px', zIndex: 9999,
            padding: '8px 14px', fontSize: '13px', borderRadius: '8px',
            border: '1px solid rgba(255,255,255,0.15)', cursor: 'pointer',
            background: 'rgba(170,59,255,0.15)', color: '#c084fc',
            fontFamily: 'system-ui, sans-serif', backdropFilter: 'blur(8px)',
          });
          b.onclick = async () => {
            b.textContent = 'Checking...';
            const v = await window.pywebview.api.check_for_updates();
            if (!v.update_available) {
              b.textContent = `Up to date (v${v.local})`;
              setTimeout(() => b.textContent = 'Check for updates', 2500);
              return;
            }
            if (!confirm(`Update available: v${v.local} → v${v.remote}\\n\\nApply now? App will restart.`)) {
              b.textContent = 'Check for updates';
              return;
            }
            b.textContent = 'Updating...';
            const r = await window.pywebview.api.apply_update();
            if (r.ok) {
              b.textContent = 'Restarting...';
              setTimeout(() => window.pywebview.api.restart(), 600);
            } else {
              b.textContent = 'Update failed';
              alert('Update failed: ' + r.message);
            }
          };
          document.body.appendChild(b);
        })();
        """
        window.evaluate_js(js)

    webview.start(_add_menu, debug=False)


if __name__ == "__main__":
    main()
