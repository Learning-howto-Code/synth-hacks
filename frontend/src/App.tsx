import { useEffect, useRef, useState } from 'react'
import './App.css'

type Peer = {
  name: string
  state: string
}

type BLEDevice = {
  address: string
  name: string | null
  rssi: number | null
}

type Message = {
  type: 'message'
  id?: number
  msg_id?: string
  room?: string
  from: string
  text: string
  ts: number
  hops?: number
}

type PlatformInfo = {
  type: 'platform'
  platform: string
  mode: 'p2p' | 'local-only'
}

type VersionInfo = {
  type: 'version'
  local: string
  remote: string
  update_available: boolean
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const onClick = async () => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }
  return (
    <button className={`copy-btn ${copied ? 'copied' : ''}`} onClick={onClick} type="button">
      {copied ? 'Copied!' : 'Copy'}
    </button>
  )
}

type OS = 'mac' | 'windows' | 'linux'

function detectOS(): OS {
  const ua = navigator.userAgent.toLowerCase()
  if (ua.includes('win')) return 'windows'
  if (ua.includes('mac')) return 'mac'
  return 'linux'
}

const INSTALL_CMDS: Record<OS, { label: string; cmd: string }> = {
  mac: {
    label: 'macOS',
    cmd: 'curl -sSL https://raw.githubusercontent.com/Learning-howto-Code/synth-hacks/main/install.sh | bash',
  },
  linux: {
    label: 'Linux',
    cmd: 'curl -sSL https://raw.githubusercontent.com/Learning-howto-Code/synth-hacks/main/install.sh | bash',
  },
  windows: {
    label: 'Windows',
    cmd: 'iwr https://raw.githubusercontent.com/Learning-howto-Code/synth-hacks/main/install.ps1 -useb | iex',
  },
}

function OneLinerCard() {
  const [os, setOs] = useState<OS>(() => detectOS())
  const { cmd } = INSTALL_CMDS[os]
  return (
    <div className="oneliner">
      <div className="oneliner-head">
        <div className="oneliner-label">One-line install</div>
        <div className="os-tabs">
          {(['mac', 'linux', 'windows'] as OS[]).map((o) => (
            <button
              key={o}
              className={`os-tab ${o === os ? 'active' : ''}`}
              onClick={() => setOs(o)}
              type="button"
            >
              {INSTALL_CMDS[o].label}
            </button>
          ))}
        </div>
      </div>
      <div className="oneliner-row">
        <code className="oneliner-cmd">{cmd}</code>
        <CopyButton text={cmd} />
      </div>
      <div className="oneliner-hint">
        {os === 'windows'
          ? 'Run in PowerShell. Requires Python 3.10+ and git.'
          : 'Run in Terminal. Requires Python 3.10+ and git.'}
      </div>
    </div>
  )
}

function CodeBlock({ title, lines, copyText }: { title: string; lines: React.ReactNode; copyText: string }) {
  return (
    <div className="code-card">
      <div className="code-head">
        <span className="dot red" />
        <span className="dot yellow" />
        <span className="dot green" />
        <span className="title">{title}</span>
        <CopyButton text={copyText} />
      </div>
      <pre className="code-body">{lines}</pre>
    </div>
  )
}

function Landing({ onEnter }: { onEnter: (nickname: string) => void }) {
  const [name, setName] = useState('')
  const installRef = useRef<HTMLDivElement | null>(null)
  const ctaRef = useRef<HTMLDivElement | null>(null)
  const submit = () => {
    const trimmed = name.trim()
    if (trimmed) onEnter(trimmed)
  }
  const scrollTo = (ref: React.RefObject<HTMLDivElement | null>) =>
    ref.current?.scrollIntoView({ behavior: 'smooth' })

  const manualInstall = `git clone https://github.com/Learning-howto-Code/synth-hacks
cd synth-hacks/backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python server.py`

  return (
    <div className="landing">
      <nav className="nav">
        <span className="logo">⛓ mesh</span>
        <div className="nav-links">
          <a href="#install" onClick={(e) => { e.preventDefault(); scrollTo(installRef) }}>Install</a>
          <a href="#features">Features</a>
          <a href="#how">How it works</a>
          <button className="nav-cta" onClick={() => scrollTo(installRef)}>Get started →</button>
        </div>
      </nav>

      <section className="hero">
        <div className="hero-content">
          <span className="badge">⚡ Bluetooth mesh · Multi-hop · Encrypted</span>
          <h1>
            Chat with no Wi-Fi.<br />
            <span className="grad">Mesh through your friends.</span>
          </h1>
          <p className="lede">
            Mesh hops messages device-to-device over Bluetooth. No internet, no router,
            no cell tower. Each device relays for the next — reach friends out of range
            through people in between.
          </p>
          <div className="hero-actions">
            <button className="primary big" onClick={() => scrollTo(installRef)}>
              Install in 30 seconds →
            </button>
            <a className="secondary" href="https://github.com/Learning-howto-Code/synth-hacks" target="_blank" rel="noreferrer">
              View on GitHub
            </a>
          </div>
          <div className="trust">
            <span>★ MIT licensed</span>
            <span>•</span>
            <span>macOS · Linux · Windows</span>
            <span>•</span>
            <span>Zero dependencies on cloud</span>
          </div>
        </div>

        <div className="hero-visual">
          <CodeBlock
            title="mesh in action"
            copyText="python server.py"
            lines={
              <>
                <span className="c-comment"># Two friends, two laptops, one mesh</span>{'\n'}
                <span className="c-prompt">jake $</span> python server.py{'\n'}
                <span className="c-log">Uvicorn running on http://0.0.0.0:8000</span>{'\n'}
                <span className="c-log">[mesh] advertising as 'jake'</span>{'\n'}{'\n'}
                <span className="c-prompt">shree $</span> python server.py{'\n'}
                <span className="c-log">[mesh] found jake → connected</span>{'\n'}{'\n'}
                <span className="c-prompt">{'>'}</span> hey, you up?{'\n'}
                <span className="c-recv">[shree] yeah, what's up</span>
              </>
            }
          />
        </div>
      </section>

      <section id="install" className="section install-hero" ref={installRef}>
        <div className="install-header">
          <span className="kicker">Get started</span>
          <h2>Install in 30 seconds.</h2>
          <p className="lede">Download the native app, or run a one-liner.</p>
        </div>

        <div className="dl-grid">
          <a
            className="dl-btn mac"
            href="https://github.com/Learning-howto-Code/synth-hacks/releases/latest/download/Mesh-macos.zip"
          >
            <span className="dl-os"></span>
            <span className="dl-label">
              <span className="dl-title">Download for macOS</span>
              <span className="dl-sub">Mesh.app · Apple silicon &amp; Intel</span>
            </span>
          </a>
          <a
            className="dl-btn win"
            href="https://github.com/Learning-howto-Code/synth-hacks/releases/latest/download/Mesh-windows.zip"
          >
            <span className="dl-os">⊞</span>
            <span className="dl-label">
              <span className="dl-title">Download for Windows</span>
              <span className="dl-sub">Mesh.exe · 64-bit</span>
            </span>
          </a>
        </div>
        <p className="hint" style={{ marginTop: 16 }}>
          <strong>Works offline.</strong> Once installed, app opens its own UI at <code>localhost:8000</code> —
          no internet, no this website needed. Unsigned binaries. macOS: right-click → Open.
          Windows: SmartScreen → More info → Run anyway.
        </p>

        <div className="install-divider"><span>or use the script installer</span></div>

        <OneLinerCard />

        <div className="install-divider"><span>or install manually</span></div>

        <CodeBlock
          title="manual install"
          copyText={manualInstall}
          lines={
            <>
              <span className="c-comment"># Clone, install, run</span>{'\n'}
              <span className="c-prompt">$</span> git clone https://github.com/Learning-howto-Code/synth-hacks{'\n'}
              <span className="c-prompt">$</span> cd synth-hacks/backend{'\n'}
              <span className="c-prompt">$</span> python3 -m venv venv <span className="c-flag">&amp;&amp;</span> source venv/bin/activate{'\n'}
              <span className="c-prompt">$</span> pip install <span className="c-flag">-r</span> requirements.txt{'\n'}
              <span className="c-prompt">$</span> python server.py
            </>
          }
        />

        <div className="install-cta">
          <p>Server running? <button className="link-btn" onClick={() => scrollTo(ctaRef)}>Open the chat →</button></p>
        </div>
      </section>

      <section id="features" className="section">
        <h2>Why mesh?</h2>
        <div className="grid">
          <div className="card">
            <div className="icon">📡</div>
            <h3>No Wi-Fi required</h3>
            <p>Bluetooth + peer-to-peer Wi-Fi link devices directly. Works in airplane mode, dead zones, disaster scenarios.</p>
          </div>
          <div className="card">
            <div className="icon">🕸</div>
            <h3>Multi-hop relay</h3>
            <p>Friends out of range? Messages hop through devices in between. Up to {6} hops by default.</p>
          </div>
          <div className="card">
            <div className="icon">🔐</div>
            <h3>End-to-end encrypted</h3>
            <p>Every session uses required encryption. Payloads never travel in plaintext.</p>
          </div>
          <div className="card">
            <div className="icon">⚡</div>
            <h3>Zero config</h3>
            <p>Auto-advertise, auto-browse, auto-invite, auto-accept. Just run it.</p>
          </div>
          <div className="card">
            <div className="icon">🪶</div>
            <h3>Native &amp; tiny</h3>
            <p>One Python file. No daemons, no brokers, no third-party services.</p>
          </div>
        </div>
      </section>

      <section id="how" className="section alt">
        <h2>How it works</h2>
        <ol className="steps">
          <li>
            <span className="step-num">1</span>
            <div>
              <h3>Install &amp; run</h3>
              <p>Run the one-liner above. A tiny local server starts and begins advertising over Bluetooth + peer-to-peer Wi-Fi.</p>
            </div>
          </li>
          <li>
            <span className="step-num">2</span>
            <div>
              <h3>Find each other automatically</h3>
              <p>No router, no internet, no cell tower. Devices discover each other via Apple MultipeerConnectivity over Bluetooth and direct Wi-Fi.</p>
            </div>
          </li>
          <li>
            <span className="step-num">3</span>
            <div>
              <h3>Hop through neighbors</h3>
              <p>Friends out of direct range? Your message travels through devices in between. Up to 6 hops, gossip-relayed, encrypted per hop.</p>
            </div>
          </li>
          <li>
            <span className="step-num">4</span>
            <div>
              <h3>Want pure Bluetooth?</h3>
              <p>Turn Wi-Fi <em>off</em>. Mesh switches to Bluetooth-only — works in airplane mode (Bluetooth on), at festivals, on planes, anywhere.</p>
            </div>
          </li>
        </ol>
      </section>

      <section id="start" className="section cta" ref={ctaRef}>
        <h2>Already installed?</h2>
        <p className="lede">Pick a nickname to join the mesh.</p>
        <form className="cta-form" onSubmit={(e) => { e.preventDefault(); submit() }}>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. jake"
            maxLength={24}
          />
          <button type="submit" disabled={!name.trim()}>Enter mesh →</button>
        </form>
        <p className="hint">Need to install first? <button className="link-btn" onClick={() => scrollTo(installRef)}>Jump to install</button></p>
      </section>

      <footer className="foot">
        <span>mesh · open source on <a href="https://github.com/Learning-howto-Code/synth-hacks" target="_blank" rel="noreferrer">GitHub</a></span>
      </footer>
    </div>
  )
}

function Chat({ nickname, onSignOut }: { nickname: string; onSignOut: () => void }) {
  const [peers, setPeers] = useState<Peer[]>([])
  const [bleDevices, setBleDevices] = useState<BLEDevice[]>([])
  const [showNoPeersHelp, setShowNoPeersHelp] = useState(false)
  const [rooms, setRooms] = useState<string[]>(['#general'])
  const [currentRoom, setCurrentRoom] = useState<string>('#general')
  const [messagesByRoom, setMessagesByRoom] = useState<Record<string, Message[]>>({})
  const [draft, setDraft] = useState('')
  const [connected, setConnected] = useState(false)
  const [mode, setMode] = useState<'p2p' | 'local-only' | null>(null)
  const [version, setVersion] = useState<VersionInfo | null>(null)
  const [newRoomInput, setNewRoomInput] = useState('')
  const wsRef = useRef<WebSocket | null>(null)
  const threadRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const backendHost = import.meta.env.VITE_BACKEND_HOST || 'localhost:8000'
    const isDev = location.hostname === 'localhost' || location.hostname === '127.0.0.1'
    const url = isDev
      ? `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`
      : `ws://${backendHost}/ws`
    const ws = new WebSocket(url)
    wsRef.current = ws
    ws.onopen = () => setConnected(true)
    ws.onclose = () => setConnected(false)
    ws.onmessage = (ev) => {
      const data = JSON.parse(ev.data)
      if (data.type === 'peers') setPeers(data.peers)
      else if (data.type === 'ble') setBleDevices(data.devices)
      else if (data.type === 'rooms') setRooms(data.rooms)
      else if (data.type === 'history') {
        setMessagesByRoom((prev) => ({ ...prev, [data.room]: data.messages }))
      } else if (data.type === 'message') {
        const room = data.room || '#general'
        setMessagesByRoom((prev) => ({
          ...prev,
          [room]: [...(prev[room] || []), data],
        }))
        setRooms((prev) => (prev.includes(room) ? prev : [...prev, room]))
      } else if (data.type === 'platform') {
        setMode((data as PlatformInfo).mode)
      } else if (data.type === 'version') {
        setVersion(data as VersionInfo)
      }
    }
    return () => ws.close()
  }, [])

  // Show troubleshooting after 10s with no peers (when in p2p mode)
  useEffect(() => {
    if (mode !== 'p2p') return
    if (peers.length > 0) {
      setShowNoPeersHelp(false)
      return
    }
    const t = setTimeout(() => setShowNoPeersHelp(true), 10000)
    return () => clearTimeout(t)
  }, [mode, peers.length])

  // Request history when switching rooms
  useEffect(() => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    if (messagesByRoom[currentRoom]) return // already loaded
    wsRef.current.send(JSON.stringify({ type: 'history', room: currentRoom }))
  }, [currentRoom, connected])

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight })
  }, [messagesByRoom, currentRoom])

  const send = () => {
    const text = draft.trim()
    if (!text || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    wsRef.current.send(JSON.stringify({ type: 'message', from: nickname, text, room: currentRoom }))
    setDraft('')
  }

  const createRoom = (e: React.FormEvent) => {
    e.preventDefault()
    let name = newRoomInput.trim()
    if (!name) return
    if (!name.startsWith('#')) name = '#' + name
    name = name.toLowerCase().replace(/[^#a-z0-9-]/g, '-').slice(0, 24)
    if (!rooms.includes(name)) setRooms((prev) => [...prev, name])
    setCurrentRoom(name)
    setNewRoomInput('')
  }

  const messages = messagesByRoom[currentRoom] || []

  return (
    <div className="app">
      <aside className="peers">
        <header>
          <h2>Channels</h2>
          <span className={`dot-status ${connected ? 'on' : 'off'}`} title={connected ? 'connected' : 'disconnected'} />
        </header>

        {version?.update_available && (
          <div className="update-banner">
            <strong>Update available</strong>
            <p>
              v{version.local} → v{version.remote}. Pull + restart:
            </p>
            <code>git pull && python server.py</code>
          </div>
        )}

        <ul className="rooms">
          {rooms.map((r) => (
            <li
              key={r}
              className={`room ${r === currentRoom ? 'active' : ''}`}
              onClick={() => setCurrentRoom(r)}
            >
              {r}
            </li>
          ))}
        </ul>

        <form className="room-add" onSubmit={createRoom}>
          <input
            value={newRoomInput}
            onChange={(e) => setNewRoomInput(e.target.value)}
            placeholder="+ new channel"
            maxLength={24}
          />
        </form>

        <div className="peer-section">
          <h3>Peers</h3>
          {mode === 'local-only' && (
            <div className="peer-banner">
              <strong>Local-only mode</strong>
              <p>Peer discovery is macOS only. Windows/Linux soon.</p>
            </div>
          )}
          {mode === 'p2p' && peers.length === 0 && !showNoPeersHelp && (
            <p className="empty"><small>Waiting for peers… have a friend run <code>python server.py</code> on the same Wi-Fi.</small></p>
          )}
          {mode === 'p2p' && peers.length === 0 && showNoPeersHelp && (
            <div className="peer-banner help">
              <strong>No peers after 10s</strong>
              <p>Most common cause: macOS denied Local Network permission.</p>
              <ol>
                <li>System Settings → Privacy &amp; Security → <b>Local Network</b></li>
                <li>Enable Terminal (or whatever runs Python)</li>
                <li>Restart server.py</li>
              </ol>
              <p>Also check: same Wi-Fi, friend's server actually running, friend has latest code.</p>
            </div>
          )}
          <ul>
            {peers.map((p) => (
              <li key={p.name}>
                <div className="name">{p.name}</div>
                <div className="meta">
                  <span className={`pill ${p.state.toLowerCase()}`}>{p.state}</span>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className="peer-section">
          <h3>Nearby Bluetooth <span className="count">{bleDevices.length}</span></h3>
          {bleDevices.length === 0 && (
            <p className="empty"><small>Scanning…</small></p>
          )}
          <ul className="ble-list">
            {bleDevices
              .sort((a, b) => (b.rssi ?? -200) - (a.rssi ?? -200))
              .slice(0, 30)
              .map((d) => (
                <li key={d.address}>
                  <div className="name">{d.name || <span className="unknown">Unknown</span>}</div>
                  <div className="meta">
                    <span className="addr">{d.address.slice(0, 8)}…</span>
                    {d.rssi != null && <span className="rssi">{d.rssi} dBm</span>}
                  </div>
                </li>
              ))}
          </ul>
        </div>

        <footer className="peers-foot">
          <small>v{version?.local || '...'} · messages persist locally</small>
        </footer>
      </aside>

      <main className="chat">
        <header>
          <h2>{currentRoom}</h2>
          <div className="header-right">
            <span className="me">{nickname}</span>
            <button className="signout-btn" onClick={onSignOut} title="Sign out">↻</button>
          </div>
        </header>
        <div className="thread" ref={threadRef}>
          {messages.length === 0 && <p className="empty">No messages in {currentRoom} yet. Say hi.</p>}
          {messages.map((m, i) => (
            <div key={m.msg_id ?? m.id ?? i} className={`msg ${m.from === nickname ? 'mine' : ''}`}>
              <div className="who">
                {m.from}
                {m.hops != null && m.hops > 0 && (
                  <span className="hops" title={`Relayed through ${m.hops} hop${m.hops > 1 ? 's' : ''}`}>
                    {' · '}{m.hops}↪
                  </span>
                )}
              </div>
              <div className="bubble">{m.text}</div>
            </div>
          ))}
        </div>
        <form className="composer" onSubmit={(e) => { e.preventDefault(); send() }}>
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder={connected ? `Message ${currentRoom}…` : 'Connecting to localhost:8000… (is the server running?)'}
            disabled={!connected}
          />
          <button type="submit" disabled={!connected || !draft.trim()}>
            Send
          </button>
        </form>
      </main>
    </div>
  )
}

const NICK_KEY = 'mesh.nickname'

function App() {
  const [nickname, setNickname] = useState<string | null>(() => {
    try { return localStorage.getItem(NICK_KEY) } catch { return null }
  })
  const setAndPersist = (n: string | null) => {
    setNickname(n)
    try {
      if (n) localStorage.setItem(NICK_KEY, n)
      else localStorage.removeItem(NICK_KEY)
    } catch {}
  }
  if (!nickname) return <Landing onEnter={setAndPersist} />
  return <Chat nickname={nickname} onSignOut={() => setAndPersist(null)} />
}

export default App
