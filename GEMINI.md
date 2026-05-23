# P2P Bluetooth Emergency Mesh - Project Instructions

## Project Overview
A decentralized messaging network that works when nothing else does (emergencies, disasters, etc.).
- **Core Technology:** Bluetooth Mesh (BLE), Peer-to-Peer (P2P), Local Web Interface.
- **Key Goal:** No central server, no internet required.

## The Workforce (Jake's Team)
We operate under a delegated model managed by **Jake**. Each task should be assigned to or informed by the following specialized agents:

### **Leadership & Core Operations**
- **Jake (Manager):** Central control point. Manages state, connections, and user flow transitions.
- **Larry (ChatSessionManager):** Manages conversation threads and history.
- **Morgan (UISyncManager):** Translates technical events into human-readable status updates.
- **Reese (ErrorHandlingRouter):** Catches exceptions and handles recovery gracefully.

### **Connectivity & Mesh Networking**
- **Bart (DeviceScanner):** Scans for "P2P Mesh" signature devices.
- **Smith (ConnectionInitiator):** Handles initial secure handshakes with peers.
- **Samhith (BLEReadWriter):** Low-level reading/writing of data payloads.
- **Steve (AdvertisingManager):** Manages outgoing presence announcements.
- **Alex (MultiHopRelay):** Intermediary routing when direct paths fail.
- **Peter (NetworkDiagnoser):** Monitors signal strength and packet loss.

### **Security, Privacy & Encryption**
- **Ben (KeyPairGenerator):** Generates ECDH (Curve25519) key pairs.
- **Carl (KeyExchangeAgent):** Executes Diffie-Hellman key agreement.
- **Dan (SessionKeyDeriver):** Derives AES session keys via HKDF.
- **Esther (MessageEncryptor):** Authenticated encryption (AES-256 GCM).
- **Frank (MessageDecryptor):** Authenticated decryption and tampering verification.
- **Garry (CounterManager):** Replay attack prevention and message ordering.
- **Harry (AuditLogger):** Immutable record of security events.
- **MessageFormatter:** Standardized binary packet structure (Header | IV | Ciphertext | Tag).

### **Location & Context Services**
- **Nolan (BackgroundLocationService):** OS location APIs (iOS/Android).
- **Lester (LocationCoordinator):** Decides when to package location data.
- **LocationPayloadGenerator:** Formats GPS into structured payloads.
- **LocationEncryptor:** Encrypts location data for privacy.

### **Staff Engineering & Design**
- **Eva_2 (Creative/3D):** React Three Fiber, physics, high-end aesthetics.
- **Kai (UI Engineer):** Principal UI, alive interfaces, smooth animations.
- **Nova (Design/Brand):** Rapid design systems, visual hierarchy, luxury aesthetic.
- **Atlas (Staff/Infra):** Systems architecture, database schema, foundations.
- **Sage (Backend):** High-performance APIs (FastAPI/Fastify), documentation.
- **Rook (FAANG Generalist):** First-principles debugging, cross-language expertise.
- **Vex (Security/Performance):** Breach prevention, auth hardening, cloud optimization.

## Engineering Standards
- **P2P Focus:** Avoid central dependencies.
- **Security First:** ECDH + AES-GCM as per the agent specifications.
- **Robustness:** Handle timeouts and connection drops gracefully (Reese's mandate).
- **Visuals:** Eva_2, Kai, and Nova ensure a high-end, interactive user experience.

## Workspace Conventions
- `backend/`: Python services for BLE and logic.
- `frontend/`: (To be created) React-based web interface.
- Documentation: Keep `GEMINI.md` updated with system architecture decisions.
