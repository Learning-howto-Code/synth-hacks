# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`synth-hacks` is a decentralized P2P Bluetooth mesh emergency communication system — no internet, no central server. Devices discover each other via BLE and chat through a local FastAPI + WebSocket backend with a React frontend.

## Commands

### Backend
```bash
cd backend
pip install -r requirements.txt   # Python 3.10+ required
python server.py                   # FastAPI on http://0.0.0.0:8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # Vite dev server
npm run build    # TypeScript check + production build
npm run lint     # ESLint
```

### One-line installer (end-user)
```bash
curl -sSL https://raw.githubusercontent.com/Learning-howto-Code/synth-hacks/main/install.sh | bash
```

## Architecture

### Backend (`backend/`)
- **`server.py`** — FastAPI app with a WebSocket hub (`/ws`) and REST endpoints (`/peers`, `/messages`). Uses Apple MultipeerConnectivity (via PyObjC) for peer discovery and real P2P message delivery. The Cocoa RunLoop runs on a daemon thread; MPC callbacks post events to the asyncio loop via `asyncio.run_coroutine_threadsafe`. Peer name defaults to `socket.gethostname()`; override with `--name`.
- **`mpc_chat.py`** — Standalone CLI chat using the same MPC stack. Kept as a reference/debug tool.
- **`advertise.py`** — BLE GATT server (Bless) that advertises the mesh service UUID `12345678-1234-5678-1234-56789abcdef0`.
- **`search.py`** — Standalone BLE scanner; prints discovered devices with RSSI.
- **`encryption.py`** — RSA-2048 helpers (`encrypt_message` / `decrypt_message`). **Not yet wired into `server.py`** — the planned crypto stack is ECDH (Curve25519) + AES-256-GCM (see GEMINI.md).

### Frontend (`frontend/src/`)
- **`App.tsx`** — Single-file app with two views:
  - **Landing page** — marketing sections, smooth-scroll nav, install CTA.
  - **Chat interface** — connects to backend WebSocket, shows peer list with RSSI, live message thread.
- WebSocket target: `localhost:8000` in dev; `VITE_BACKEND_HOST` env var in production (Vercel).
- Stack: React 19, TypeScript, Vite, TailwindCSS 4, Three.js / React Three Fiber, Framer Motion, GSAP.

### Data flow
```
MPC advertise/browse → peer discovered → peer list pushed to all WS clients
User sends message → WS → server.py → MPC send → remote peer's MPC → their server.py → their WS clients
Remote peer sends → MPC receive callback (daemon thread) → asyncio broadcast → local WS clients
```

## Key design constraints
- **No central server at runtime** — the FastAPI process runs locally on each device.
- **Encryption gap** — `encryption.py` exists but is not called from `server.py`; integrating it (or replacing with ECDH+AES-GCM) is the primary security TODO.
- **macOS only** — MultipeerConnectivity requires PyObjC and macOS. First run will prompt for Local Network permission; allow it.
