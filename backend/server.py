import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Dict, List, Set

from bleak import BleakScanner
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

MESH_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
SCAN_INTERVAL = 5.0


@dataclass
class Peer:
    address: str
    name: str | None
    rssi: int | None
    last_seen: float


@dataclass
class State:
    peers: Dict[str, Peer] = field(default_factory=dict)
    messages: List[dict] = field(default_factory=list)
    sockets: Set[WebSocket] = field(default_factory=set)


state = State()


async def broadcast(payload: dict) -> None:
    dead = []
    for ws in state.sockets:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        state.sockets.discard(ws)


async def scan_loop() -> None:
    loop = asyncio.get_event_loop()
    while True:
        try:
            devices = await BleakScanner.discover(timeout=SCAN_INTERVAL, return_adv=True)
            now = loop.time()
            new_peers: Dict[str, Peer] = {}
            for d, adv in devices.values():
                uuids = [u.lower() for u in (adv.service_uuids or [])]
                is_mesh = MESH_SERVICE_UUID.lower() in uuids
                if not is_mesh and not d.name:
                    continue
                new_peers[d.address] = Peer(
                    address=d.address,
                    name=d.name or adv.local_name,
                    rssi=adv.rssi,
                    last_seen=now,
                )
            state.peers = new_peers
            await broadcast({"type": "peers", "peers": [p.__dict__ for p in state.peers.values()]})
        except Exception as e:
            print(f"scan error: {e}")
            await asyncio.sleep(1.0)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(scan_loop())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/peers")
async def get_peers():
    return [p.__dict__ for p in state.peers.values()]


@app.get("/messages")
async def get_messages():
    return state.messages


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    state.sockets.add(ws)
    try:
        await ws.send_json({"type": "peers", "peers": [p.__dict__ for p in state.peers.values()]})
        await ws.send_json({"type": "history", "messages": state.messages})
        while True:
            data = await ws.receive_json()
            if data.get("type") == "message":
                msg = {
                    "type": "message",
                    "from": data.get("from", "me"),
                    "text": data.get("text", ""),
                    "ts": asyncio.get_event_loop().time(),
                }
                state.messages.append(msg)
                await broadcast(msg)
    except WebSocketDisconnect:
        pass
    finally:
        state.sockets.discard(ws)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
