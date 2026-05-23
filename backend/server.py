"""
FastAPI server for mesh chat.

- On macOS, uses Apple MultipeerConnectivity for real peer-to-peer discovery + delivery.
- On other platforms, runs in local-only mode (no peer discovery yet).
- The browser UI always connects via the WebSocket on port 8000.

Run:
    python server.py [--name MyName]
"""

import argparse
import asyncio
import socket
import sys
import threading
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

IS_MACOS = sys.platform == "darwin"
SERVICE_TYPE = "synth-chat"

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


@dataclass
class Peer:
    name: str
    state: str


@dataclass
class AppState:
    peers: Dict[str, Peer] = field(default_factory=dict)
    messages: List[dict] = field(default_factory=list)
    sockets: Set[WebSocket] = field(default_factory=set)


app_state = AppState()
_loop: Optional[asyncio.AbstractEventLoop] = None
_bridge = None  # MPCBridge on Mac, None elsewhere


def _post(coro) -> None:
    """Thread-safe: schedule a coroutine on the asyncio event loop from any thread."""
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


if MPC_AVAILABLE:
    _STATE_NAMES = {
        MCSessionStateNotConnected: "NotConnected",
        MCSessionStateConnecting: "Connecting",
        MCSessionStateConnected: "Connected",
    }

    class MPCBridge(NSObject):
        """Delegate for MCSession, MCNearbyServiceAdvertiser, and MCNearbyServiceBrowser."""

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

        def send_text(self, text: str) -> None:
            peers = list(self._session.connectedPeers() or [])
            if not peers:
                return
            encoded = text.encode("utf-8")
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
            try:
                text = bytes(data).decode("utf-8")
            except UnicodeDecodeError:
                text = repr(bytes(data))
            msg = {
                "type": "message",
                "from": peer.displayName(),
                "text": text,
                "ts": 0,
            }
            app_state.messages.append(msg)
            _post(_broadcast(msg))

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


@asynccontextmanager
async def lifespan(_: FastAPI):
    global _loop, _bridge
    _loop = asyncio.get_running_loop()

    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--name", default=socket.gethostname())
    args, _unknown = ap.parse_known_args()

    if MPC_AVAILABLE:
        _bridge = MPCBridge.alloc().initWithDisplayName_(args.name)
        _bridge.start()
        t = threading.Thread(target=_run_runloop, daemon=True)
        t.start()
    else:
        print(f"[mesh] running on {sys.platform} in local-only mode (no peer discovery)")
        print(f"[mesh] display name: {args.name}")

    try:
        yield
    finally:
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


@app.get("/messages")
async def get_messages():
    return app_state.messages


@app.get("/platform")
async def get_platform():
    return {
        "platform": sys.platform,
        "mpc_available": MPC_AVAILABLE,
        "mode": "p2p" if MPC_AVAILABLE else "local-only",
    }


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    app_state.sockets.add(ws)
    try:
        await ws.send_json({
            "type": "peers",
            "peers": [{"name": p.name, "state": p.state} for p in app_state.peers.values()],
        })
        await ws.send_json({"type": "history", "messages": app_state.messages})
        await ws.send_json({
            "type": "platform",
            "platform": sys.platform,
            "mode": "p2p" if MPC_AVAILABLE else "local-only",
        })
        while True:
            data = await ws.receive_json()
            if data.get("type") == "message":
                text = data.get("text", "")
                sender = data.get("from", "me")
                msg = {
                    "type": "message",
                    "from": sender,
                    "text": text,
                    "ts": _loop.time() if _loop else 0,
                }
                app_state.messages.append(msg)
                await _broadcast(msg)
                if _bridge:
                    _bridge.send_text(text)
    except WebSocketDisconnect:
        pass
    finally:
        app_state.sockets.discard(ws)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
