"""
FastAPI server for mesh chat with rooms + SQLite persistence.

- On macOS, uses Apple MultipeerConnectivity for peer discovery + delivery.
- On other platforms, runs in local-only mode.
- Messages persisted to mesh.db (SQLite, stdlib). Survive restarts.
- IRC-style rooms: messages tagged with room, default '#general'.
"""

import argparse
import asyncio
import json
import os
import socket
import sqlite3
import subprocess
import sys
import threading
import time
import uuid
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Deque, Dict, List, Optional, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

try:
    from bleak import BleakScanner
    BLE_AVAILABLE = True
except ImportError:
    BLE_AVAILABLE = False

IS_MACOS = sys.platform == "darwin"
SERVICE_TYPE = "synth-chat"
DEFAULT_ROOM = "#general"
DB_PATH = Path(__file__).parent / "mesh.db"
REPO_DIR = Path(__file__).parent.parent
BLE_SCAN_INTERVAL = 6.0
MAX_TTL = 6              # max hops a message can travel
SEEN_CAPACITY = 4096     # how many recent message IDs we remember to dedupe

if IS_MACOS:
    try:
        import objc
        from Foundation import NSData, NSDate, NSObject, NSRunLoop
        from MultipeerConnectivity import (
            MCEncryptionRequired,
            MCNearbyServiceAdvertiser,
            MCNearbyServiceBrowser,
            MCPeerID,
            MCSession,
            MCSessionStateConnected,
            MCSessionStateConnecting,
            MCSessionStateNotConnected,
        )
        MPC_AVAILABLE = True
    except ImportError as e:
        print(f"[mpc] pyobjc-framework-MultipeerConnectivity missing: {e}")
        MPC_AVAILABLE = False
else:
    MPC_AVAILABLE = False


# ── Storage ───────────────────────────────────────────────────────────────────

def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    with _db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room TEXT NOT NULL,
                sender TEXT NOT NULL,
                text TEXT NOT NULL,
                ts REAL NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_room_ts ON messages(room, ts)")


def store_message(room: str, sender: str, text: str, ts: float) -> dict:
    with _db() as conn:
        cur = conn.execute(
            "INSERT INTO messages (room, sender, text, ts) VALUES (?, ?, ?, ?)",
            (room, sender, text, ts),
        )
        return {
            "type": "message",
            "id": cur.lastrowid,
            "room": room,
            "from": sender,
            "text": text,
            "ts": ts,
        }


def load_messages(room: str, limit: int = 200) -> List[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT id, room, sender, text, ts FROM messages WHERE room = ? ORDER BY ts DESC LIMIT ?",
            (room, limit),
        ).fetchall()
    return [
        {"type": "message", "id": r["id"], "room": r["room"], "from": r["sender"], "text": r["text"], "ts": r["ts"]}
        for r in reversed(rows)
    ]


def list_rooms() -> List[str]:
    with _db() as conn:
        rows = conn.execute("SELECT DISTINCT room FROM messages ORDER BY room").fetchall()
    rooms = [r["room"] for r in rows]
    if DEFAULT_ROOM not in rooms:
        rooms.insert(0, DEFAULT_ROOM)
    return rooms


# ── State ─────────────────────────────────────────────────────────────────────

@dataclass
class Peer:
    name: str
    state: str


@dataclass
class BLEDevice:
    address: str
    name: Optional[str]
    rssi: Optional[int]


@dataclass
class AppState:
    peers: Dict[str, Peer] = field(default_factory=dict)
    ble_devices: Dict[str, BLEDevice] = field(default_factory=dict)
    sockets: Set[WebSocket] = field(default_factory=set)


app_state = AppState()
_loop: Optional[asyncio.AbstractEventLoop] = None
_bridge = None

# Gossip de-dupe: bounded set of recently seen message IDs
_seen_ids: Deque[str] = deque(maxlen=SEEN_CAPACITY)
_seen_set: Set[str] = set()


def _seen(msg_id: str) -> bool:
    """Return True if we've already processed this message id; record it otherwise."""
    if msg_id in _seen_set:
        return True
    if len(_seen_ids) == _seen_ids.maxlen:
        old = _seen_ids[0]
        _seen_set.discard(old)
    _seen_ids.append(msg_id)
    _seen_set.add(msg_id)
    return False


def _post(coro) -> None:
    if _loop:
        asyncio.run_coroutine_threadsafe(coro, _loop)


async def _broadcast(payload: dict) -> None:
    dead = []
    for ws in app_state.sockets:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        app_state.sockets.discard(ws)


async def _push_peers() -> None:
    await _broadcast({
        "type": "peers",
        "peers": [{"name": p.name, "state": p.state} for p in app_state.peers.values()],
    })


async def _push_ble() -> None:
    await _broadcast({
        "type": "ble",
        "devices": [
            {"address": d.address, "name": d.name, "rssi": d.rssi}
            for d in app_state.ble_devices.values()
        ],
    })


async def _ble_scan_loop() -> None:
    if not BLE_AVAILABLE:
        return
    while True:
        try:
            devices = await BleakScanner.discover(timeout=BLE_SCAN_INTERVAL, return_adv=True)
            current: Dict[str, BLEDevice] = {}
            for d, adv in devices.values():
                name = d.name or adv.local_name
                if not name and not adv.service_uuids:
                    continue
                current[d.address] = BLEDevice(
                    address=d.address,
                    name=name,
                    rssi=adv.rssi,
                )
            app_state.ble_devices = current
            await _push_ble()
        except Exception as e:
            print(f"[ble] scan error: {e}")
            await asyncio.sleep(2.0)


# ── MPC bridge (Mac only) ─────────────────────────────────────────────────────

if MPC_AVAILABLE:
    _STATE_NAMES = {
        MCSessionStateNotConnected: "NotConnected",
        MCSessionStateConnecting: "Connecting",
        MCSessionStateConnected: "Connected",
    }

    class MPCBridge(NSObject):
        def initWithDisplayName_(self, name: str):
            self = objc.super(MPCBridge, self).init()
            if self is None:
                return None
            self._peer_id = MCPeerID.alloc().initWithDisplayName_(name)
            self._session = MCSession.alloc().initWithPeer_securityIdentity_encryptionPreference_(
                self._peer_id, None, MCEncryptionRequired
            )
            self._session.setDelegate_(self)
            self._advertiser = MCNearbyServiceAdvertiser.alloc().initWithPeer_discoveryInfo_serviceType_(
                self._peer_id, None, SERVICE_TYPE
            )
            self._advertiser.setDelegate_(self)
            self._browser = MCNearbyServiceBrowser.alloc().initWithPeer_serviceType_(
                self._peer_id, SERVICE_TYPE
            )
            self._browser.setDelegate_(self)
            return self

        def start(self) -> None:
            self._advertiser.startAdvertisingPeer()
            self._browser.startBrowsingForPeers()
            print(f"[mpc] advertising + browsing as {self._peer_id.displayName()!r} on '{SERVICE_TYPE}'")

        def stop(self) -> None:
            self._advertiser.stopAdvertisingPeer()
            self._browser.stopBrowsingForPeers()
            self._session.disconnect()

        def send_envelope(self, envelope: dict, exclude_peer=None) -> None:
            peers = list(self._session.connectedPeers() or [])
            if exclude_peer is not None:
                peers = [p for p in peers if p != exclude_peer]
            if not peers:
                return
            encoded = json.dumps(envelope).encode("utf-8")
            data = NSData.dataWithBytes_length_(encoded, len(encoded))
            ok, err = self._session.sendData_toPeers_withMode_error_(data, peers, 0, None)
            if not ok:
                print(f"[mpc] send error: {err}")

        def session_peer_didChangeState_(self, session, peer, peer_state):
            name = peer.displayName()
            label = _STATE_NAMES.get(peer_state, str(peer_state))
            if peer_state == MCSessionStateNotConnected:
                app_state.peers.pop(name, None)
            else:
                app_state.peers[name] = Peer(name=name, state=label)
            print(f"[mpc] {name} → {label}")
            _post(_push_peers())

        def session_didReceiveData_fromPeer_(self, session, data, peer):
            raw = bytes(data)
            try:
                envelope = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                envelope = {"room": DEFAULT_ROOM, "from": peer.displayName(), "text": raw.decode("utf-8", "replace")}

            # Gossip relay: dedupe by msg_id, decrement TTL, forward to other neighbors
            msg_id = envelope.get("msg_id") or uuid.uuid4().hex
            envelope["msg_id"] = msg_id
            if _seen(msg_id):
                return  # already processed and relayed once; drop

            room = envelope.get("room", DEFAULT_ROOM)
            sender = envelope.get("from", peer.displayName())
            text = envelope.get("text", "")
            ts = envelope.get("ts", time.time())
            hops = int(envelope.get("hops", 0)) + 1
            envelope["hops"] = hops

            stored = store_message(room, sender, text, ts)
            stored["hops"] = hops
            stored["msg_id"] = msg_id
            _post(_broadcast(stored))

            ttl = int(envelope.get("ttl", 0)) - 1
            if ttl > 0:
                relay = dict(envelope, ttl=ttl)
                print(f"[mesh] relay msg {msg_id[:8]} from {sender!r} ttl={ttl} hops={hops}")
                self.send_envelope(relay, exclude_peer=peer)

        def session_didReceiveStream_withName_fromPeer_(self, session, stream, name, peer): pass
        def session_didStartReceivingResourceWithName_fromPeer_withProgress_(self, session, name, peer, progress): pass
        def session_didFinishReceivingResourceWithName_fromPeer_atURL_withError_(self, session, name, peer, url, err): pass

        def session_didReceiveCertificate_fromPeer_certificateHandler_(self, session, cert, peer, handler):
            handler(True)

        def advertiser_didReceiveInvitationFromPeer_withContext_invitationHandler_(
            self, advertiser, peer, context, handler
        ):
            print(f"[mpc] invitation from {peer.displayName()} → accept")
            handler(True, self._session)

        def advertiser_didNotStartAdvertisingPeer_(self, advertiser, err):
            print(f"[mpc] advertiser error: {err}")

        def browser_foundPeer_withDiscoveryInfo_(self, browser, peer, info):
            if peer.displayName() == self._peer_id.displayName():
                return
            print(f"[mpc] found {peer.displayName()} → invite")
            browser.invitePeer_toSession_withContext_timeout_(peer, self._session, None, 30.0)

        def browser_lostPeer_(self, browser, peer):
            app_state.peers.pop(peer.displayName(), None)
            print(f"[mpc] lost {peer.displayName()}")
            _post(_push_peers())

        def browser_didNotStartBrowsingForPeers_(self, browser, err):
            print(f"[mpc] browser error: {err}")


    def _run_runloop() -> None:
        rl = NSRunLoop.currentRunLoop()
        while True:
            rl.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.1))


# ── Version / update ──────────────────────────────────────────────────────────

def _git(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(REPO_DIR), *args],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return ""


def get_version_info() -> dict:
    local = _git("rev-parse", "HEAD")[:8]
    try:
        subprocess.run(
            ["git", "-C", str(REPO_DIR), "fetch", "--quiet"],
            stderr=subprocess.DEVNULL, timeout=5,
        )
    except Exception:
        pass
    remote = _git("rev-parse", "origin/main")[:8]
    return {
        "local": local or "unknown",
        "remote": remote or "unknown",
        "update_available": bool(local and remote and local != remote),
    }


def apply_update() -> dict:
    """git pull + pip install + rebuild frontend. Caller must restart."""
    out_lines = []
    try:
        pull = subprocess.run(
            ["git", "-C", str(REPO_DIR), "pull", "--ff-only"],
            capture_output=True, text=True, timeout=30,
        )
        out_lines.append(("git pull", pull.returncode, pull.stdout + pull.stderr))
        if pull.returncode != 0:
            return {"ok": False, "steps": out_lines, "message": "git pull failed"}

        pip = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", "-r", str(REPO_DIR / "backend" / "requirements.txt")],
            capture_output=True, text=True, timeout=120,
        )
        out_lines.append(("pip install", pip.returncode, pip.stdout + pip.stderr))

        # Try to rebuild frontend if npm available
        frontend = REPO_DIR / "frontend"
        if (frontend / "package.json").exists():
            try:
                build = subprocess.run(
                    ["npm", "run", "build"],
                    cwd=frontend, capture_output=True, text=True, timeout=120,
                )
                out_lines.append(("npm run build", build.returncode, build.stdout + build.stderr))
            except FileNotFoundError:
                out_lines.append(("npm run build", 1, "npm not found, skipped frontend build"))

        return {
            "ok": True,
            "steps": out_lines,
            "message": "Update applied. Restart to load new code.",
            "new_version": _git("rev-parse", "HEAD")[:8],
        }
    except Exception as e:
        return {"ok": False, "steps": out_lines, "message": f"Update error: {e}"}


# ── App ───────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(_: FastAPI):
    global _loop, _bridge
    _loop = asyncio.get_running_loop()
    _init_db()

    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--name", default=socket.gethostname())
    args, _unknown = ap.parse_known_args()

    if MPC_AVAILABLE:
        _bridge = MPCBridge.alloc().initWithDisplayName_(args.name)
        _bridge.start()
        # NOTE: we do NOT spawn a background NSRunLoop thread anymore.
        # MPC delegate callbacks dispatch on the main thread's runloop,
        # which must be pumped by the launcher (see __main__ block).
        print()
        print("=" * 64)
        print("  [mesh] If peers don't appear within 10 seconds:")
        print("  1) System Settings → Privacy & Security → Local Network")
        print("     -> Enable Terminal (or whatever app is running Python)")
        print("  2) Both Macs must be on the SAME Wi-Fi network")
        print("  3) Restart the server after granting permission")
        print("=" * 64)
        print()
    else:
        print(f"[mesh] running on {sys.platform} in local-only mode (no peer discovery)")
        print(f"[mesh] display name: {args.name}")

    ble_task = None
    if BLE_AVAILABLE:
        print(f"[ble] starting scan loop every {BLE_SCAN_INTERVAL}s")
        ble_task = asyncio.create_task(_ble_scan_loop())

    try:
        yield
    finally:
        if ble_task:
            ble_task.cancel()
        if _bridge:
            _bridge.stop()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/peers")
async def get_peers():
    return [{"name": p.name, "state": p.state} for p in app_state.peers.values()]


@app.get("/ble")
async def get_ble():
    return [{"address": d.address, "name": d.name, "rssi": d.rssi} for d in app_state.ble_devices.values()]


@app.get("/rooms")
async def get_rooms():
    return list_rooms()


@app.get("/messages")
async def get_messages(room: str = DEFAULT_ROOM, limit: int = 200):
    return load_messages(room, limit)


@app.get("/platform")
async def get_platform():
    return {
        "platform": sys.platform,
        "mpc_available": MPC_AVAILABLE,
        "mode": "p2p" if MPC_AVAILABLE else "local-only",
    }


@app.get("/version")
async def get_version():
    return get_version_info()


def _awdl_state() -> dict:
    """Check AWDL (Apple Wireless Direct Link) — needed for peer-to-peer Wi-Fi."""
    if sys.platform != "darwin":
        return {"available": False, "reason": "non-mac"}
    try:
        out = subprocess.check_output(["ifconfig", "awdl0"], stderr=subprocess.DEVNULL, timeout=2).decode()
    except Exception:
        return {"available": False, "reason": "interface missing"}
    flags = "UP" in out and "RUNNING" in out
    return {
        "available": True,
        "up": "UP" in out,
        "running": "RUNNING" in out,
        "active": flags,
    }


def _wifi_state() -> dict:
    if sys.platform != "darwin":
        return {"adapter": "unknown"}
    try:
        # ifconfig en0 status. "status: active" means radio on.
        out = subprocess.check_output(["ifconfig", "en0"], stderr=subprocess.DEVNULL, timeout=2).decode()
        return {
            "adapter_on": "status: active" in out,
            "has_ip": "inet " in out,
        }
    except Exception:
        return {"adapter": "unknown"}


@app.get("/diag")
async def get_diag():
    bridge_ok = _bridge is not None
    connected_count = 0
    own_name = None
    if bridge_ok and MPC_AVAILABLE:
        try:
            connected_count = len(list(_bridge._session.connectedPeers() or []))
            own_name = _bridge._peer_id.displayName()
        except Exception:
            pass
    return {
        "platform": sys.platform,
        "mpc_available": MPC_AVAILABLE,
        "ble_available": BLE_AVAILABLE,
        "mpc_bridge_started": bridge_ok,
        "mpc_own_name": own_name,
        "mpc_service_type": SERVICE_TYPE,
        "mpc_connected_peer_count": connected_count,
        "mpc_peer_names": list(app_state.peers.keys()),
        "ble_device_count": len(app_state.ble_devices),
        "ws_client_count": len(app_state.sockets),
        "mesh_seen_msgs": len(_seen_set),
        "mesh_max_ttl": MAX_TTL,
        "awdl": _awdl_state(),
        "wifi": _wifi_state(),
        "hints": [
            "Most common failure: Local Network permission denied. System Settings → Privacy & Security → Local Network → enable Terminal/Python.",
            "For router-burned/offline scenarios: keep Wi-Fi adapter ON (radio active), no network needed. AWDL forms direct peer-to-peer Wi-Fi.",
            "If awdl.active=false, peer-to-peer Wi-Fi is off — toggle Wi-Fi off then back on in Control Center.",
        ],
    }


@app.post("/update")
async def post_update():
    return apply_update()


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    app_state.sockets.add(ws)
    try:
        await ws.send_json({
            "type": "peers",
            "peers": [{"name": p.name, "state": p.state} for p in app_state.peers.values()],
        })
        await ws.send_json({
            "type": "ble",
            "devices": [
                {"address": d.address, "name": d.name, "rssi": d.rssi}
                for d in app_state.ble_devices.values()
            ],
        })
        await ws.send_json({"type": "rooms", "rooms": list_rooms()})
        await ws.send_json({
            "type": "platform",
            "platform": sys.platform,
            "mode": "p2p" if MPC_AVAILABLE else "local-only",
        })
        await ws.send_json({"type": "version", **get_version_info()})

        # Initial history for default room
        for msg in load_messages(DEFAULT_ROOM):
            await ws.send_json(msg)

        while True:
            data = await ws.receive_json()
            kind = data.get("type")

            if kind == "message":
                room = data.get("room", DEFAULT_ROOM)
                sender = data.get("from", "anon")
                text = data.get("text", "").strip()
                if not text:
                    continue
                ts = time.time()
                msg_id = uuid.uuid4().hex
                _seen(msg_id)  # mark our own origin so we don't relay it back to ourselves
                stored = store_message(room, sender, text, ts)
                stored["msg_id"] = msg_id
                stored["hops"] = 0
                await _broadcast(stored)
                if _bridge:
                    _bridge.send_envelope({
                        "msg_id": msg_id,
                        "room": room,
                        "from": sender,
                        "text": text,
                        "ts": ts,
                        "ttl": MAX_TTL,
                        "hops": 0,
                    })

            elif kind == "history":
                room = data.get("room", DEFAULT_ROOM)
                msgs = load_messages(room)
                await ws.send_json({"type": "history", "room": room, "messages": msgs})

    except WebSocketDisconnect:
        pass
    finally:
        app_state.sockets.discard(ws)


if hasattr(sys, "_MEIPASS"):
    DIST_DIR = Path(sys._MEIPASS) / "frontend" / "dist"
else:
    DIST_DIR = REPO_DIR / "frontend" / "dist"
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")

    @app.get("/")
    async def index():
        return FileResponse(DIST_DIR / "index.html")

    # SPA fallback: serve index.html for unknown routes (but not /api ones above)
    @app.get("/{path:path}")
    async def spa(path: str):
        f = DIST_DIR / path
        if f.is_file():
            return FileResponse(f)
        return FileResponse(DIST_DIR / "index.html")
else:
    @app.get("/")
    async def index_dev():
        return {
            "message": "Frontend not built. Run `cd frontend && npm install && npm run build`, or open https://frontend-gold-five-84.vercel.app",
        }


def _serve(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Launch uvicorn + (on macOS) pump the main-thread Cocoa runloop so MPC works."""
    import uvicorn

    if IS_MACOS and MPC_AVAILABLE:
        try:
            from PyObjCTools import AppHelper
        except ImportError:
            AppHelper = None

        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server = uvicorn.Server(config)

        def _run_server():
            try:
                asyncio.run(server.serve())
            except Exception as e:
                print(f"[uvicorn] crashed: {e}")
                os._exit(1)

        threading.Thread(target=_run_server, daemon=True).start()

        # Block main thread on Cocoa runloop so MCNearbyServiceBrowser/Advertiser
        # delegate callbacks actually fire.
        if AppHelper:
            AppHelper.runConsoleEventLoop(installInterrupt=True)
        else:
            # Fallback: hand-rolled main-thread runloop
            try:
                while True:
                    NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(1.0))
            except KeyboardInterrupt:
                pass
    else:
        uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    _serve()
