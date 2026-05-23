import { useEffect, useRef, useState } from 'react'
import './App.css'

type Peer = {
  address: string
  name: string | null
  rssi: number | null
  last_seen: number
}

type Message = {
  type: 'message'
  from: string
  text: string
  ts: number
}

function Landing({ onEnter }: { onEnter: (nickname: string) => void }) {
  const [name, setName] = useState('')
  const ctaRef = useRef<HTMLDivElement | null>(null)
  const submit = () => {
    const trimmed = name.trim()
    if (trimmed) onEnter(trimmed)
  }
  const scrollToCta = () => ctaRef.current?.scrollIntoView({ behavior: 'smooth' })

  return (
    <div className="landing">
      <nav className="nav">
        <span className="logo">⛓ mesh</span>
        <div className="nav-links">
          <a href="#features">Features</a>
          <a href="#how">How it works</a>
          <a href="#download">Download</a>
          <a href="#start" onClick={(e) => { e.preventDefault(); scrollToCta() }}>Get started</a>
        </div>
      </nav>

      <section className="hero">
        <div className="hero-content">
          <span className="badge">Peer-to-peer · Offline-capable</span>
          <h1>
            Chat across <span className="grad">any Mac</span><br />
            with zero infrastructure.
          </h1>
          <p className="lede">
            Mesh uses Apple MultipeerConnectivity to discover and connect peers
            over Wi-Fi and Bluetooth — no router, no server, no internet required.
          </p>
          <div className="hero-actions">
            <button className="primary" onClick={scrollToCta}>Enter the mesh →</button>
            <a className="secondary" href="#how">See how it works</a>
          </div>
        </div>

        <div className="code-card">
          <div className="code-head">
            <span className="dot red" />
            <span className="dot yellow" />
            <span className="dot green" />
            <span className="title">mpc_chat.py</span>
          </div>
          <pre className="code-body">
<span className="c-comment"># Run on two Macs on the same Wi-Fi network</span>{'\n'}
<span className="c-prompt">$</span> python mpc_chat.py <span className="c-flag">--name</span> <span className="c-str">Jake</span>{'\n'}
<span className="c-prompt">$</span> python mpc_chat.py <span className="c-flag">--name</span> <span className="c-str">Shree</span>{'\n'}{'\n'}
<span className="c-log">[mpc] advertising + browsing as 'Jake' on 'synth-chat'</span>{'\n'}
<span className="c-log">[browser] found Shree {'->'} invite</span>{'\n'}
<span className="c-log">[session] Shree {'->'} Connected</span>{'\n'}
<span className="c-prompt">{'>'}</span> hello mesh{'\n'}
<span className="c-recv">[Shree] hey jake, signal locked</span>
          </pre>
        </div>
      </section>

      <section id="features" className="section">
        <h2>Why mesh?</h2>
        <div className="grid">
          <div className="card">
            <div className="icon">📡</div>
            <h3>No internet needed</h3>
            <p>Peers discover each other directly over Bluetooth and local Wi-Fi using Apple's MultipeerConnectivity stack.</p>
          </div>
          <div className="card">
            <div className="icon">🔐</div>
            <h3>End-to-end encrypted</h3>
            <p>Every session uses MCEncryptionRequired. Certificates are validated; payloads never travel in plaintext.</p>
          </div>
          <div className="card">
            <div className="icon">⚡</div>
            <h3>Zero config</h3>
            <p>Auto-advertise, auto-browse, auto-invite, auto-accept. Run it on two Macs and they find each other.</p>
          </div>
          <div className="card">
            <div className="icon">🪶</div>
            <h3>Native &amp; tiny</h3>
            <p>Pure pyobjc + Cocoa runloop. No daemons, no brokers, no third-party services.</p>
          </div>
        </div>
      </section>

      <section id="how" className="section alt">
        <h2>How it works</h2>
        <ol className="steps">
          <li>
            <span className="step-num">1</span>
            <div>
              <h3>Advertise &amp; browse</h3>
              <p>Each peer runs <code>MCNearbyServiceAdvertiser</code> and <code>MCNearbyServiceBrowser</code> on the same <code>serviceType</code>.</p>
            </div>
          </li>
          <li>
            <span className="step-num">2</span>
            <div>
              <h3>Auto-invite</h3>
              <p>When a peer is discovered, an invitation fires immediately via <code>invitePeer:toSession:withContext:timeout:</code>.</p>
            </div>
          </li>
          <li>
            <span className="step-num">3</span>
            <div>
              <h3>Auto-accept &amp; encrypt</h3>
              <p>Advertiser delegate accepts the invitation; the session negotiates encryption and reaches <code>MCSessionStateConnected</code>.</p>
            </div>
          </li>
          <li>
            <span className="step-num">4</span>
            <div>
              <h3>Send UTF-8</h3>
              <p>Messages flow as <code>NSData</code> via <code>sendData:toPeers:withMode:error:</code>. Bidirectional, low latency.</p>
            </div>
          </li>
        </ol>
      </section>

      <section id="download" className="section">
        <h2>Download &amp; run locally</h2>
        <p className="lede" style={{ marginBottom: 40 }}>
          The web app connects to a tiny Python backend running on your own machine.
          Your messages never touch our servers.
        </p>
        <div className="install">
          <div className="code-card" style={{ transform: 'none' }}>
            <div className="code-head">
              <span className="dot red" />
              <span className="dot yellow" />
              <span className="dot green" />
              <span className="title">install.sh</span>
            </div>
            <pre className="code-body">
<span className="c-comment"># 1. Clone the repo</span>{'\n'}
<span className="c-prompt">$</span> git clone https://github.com/Learning-howto-Code/synth-hacks{'\n'}
<span className="c-prompt">$</span> cd synth-hacks/backend{'\n'}{'\n'}
<span className="c-comment"># 2. Install deps</span>{'\n'}
<span className="c-prompt">$</span> python3 -m venv venv <span className="c-flag">&amp;&amp;</span> source venv/bin/activate{'\n'}
<span className="c-prompt">$</span> pip install <span className="c-flag">-r</span> requirements.txt{'\n'}{'\n'}
<span className="c-comment"># 3. Start the local server</span>{'\n'}
<span className="c-prompt">$</span> python server.py{'\n'}
<span className="c-log">Uvicorn running on http://0.0.0.0:8000</span>
            </pre>
          </div>
          <div className="install-notes">
            <h3>Then come back here</h3>
            <p>Once the server prints <code>Uvicorn running</code>, scroll up, enter a nickname, and the web app will connect automatically.</p>
            <h3>Requirements</h3>
            <ul>
              <li>Python 3.10+</li>
              <li>macOS, Linux, or Windows</li>
              <li>Optional: Bluetooth for peer discovery (macOS only)</li>
            </ul>
          </div>
        </div>
      </section>

      <section id="start" className="section cta" ref={ctaRef}>
        <h2>Pick a nickname. Step in.</h2>
        <p className="lede">Other peers on the network will see this name.</p>
        <form
          className="cta-form"
          onSubmit={(e) => { e.preventDefault(); submit() }}
        >
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. jake"
            maxLength={24}
            autoFocus
          />
          <button type="submit" disabled={!name.trim()}>Enter mesh →</button>
        </form>
        <p className="hint">First run will prompt macOS for Local Network permission. Allow it.</p>
      </section>

      <footer className="foot">
        <span>mesh · built on Apple MultipeerConnectivity</span>
      </footer>
    </div>
  )
}

function Chat({ nickname }: { nickname: string }) {
  const [peers, setPeers] = useState<Peer[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [draft, setDraft] = useState('')
  const [connected, setConnected] = useState(false)
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
      else if (data.type === 'history') setMessages(data.messages)
      else if (data.type === 'message') setMessages((m) => [...m, data])
    }
    return () => ws.close()
  }, [])

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight })
  }, [messages])

  const send = () => {
    const text = draft.trim()
    if (!text || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return
    wsRef.current.send(JSON.stringify({ type: 'message', from: nickname, text }))
    setDraft('')
  }

  return (
    <div className="app">
      <aside className="peers">
        <header>
          <h2>Peers</h2>
          <span className={`dot-status ${connected ? 'on' : 'off'}`} title={connected ? 'connected' : 'disconnected'} />
        </header>
        {peers.length === 0 && <p className="empty">No peers found yet…</p>}
        <ul>
          {peers.map((p) => (
            <li key={p.address}>
              <div className="name">{p.name || 'Unknown'}</div>
              <div className="meta">
                <span className="addr">{p.address.slice(0, 8)}…</span>
                {p.rssi != null && <span className="rssi">{p.rssi} dBm</span>}
              </div>
            </li>
          ))}
        </ul>
      </aside>

      <main className="chat">
        <header>
          <h2>Mesh chat</h2>
          <span className="me">{nickname}</span>
        </header>
        <div className="thread" ref={threadRef}>
          {messages.length === 0 && <p className="empty">No messages yet. Say hi.</p>}
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.from === nickname ? 'mine' : ''}`}>
              <div className="who">{m.from}</div>
              <div className="bubble">{m.text}</div>
            </div>
          ))}
        </div>
        <form
          className="composer"
          onSubmit={(e) => { e.preventDefault(); send() }}
        >
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder={connected ? 'Type message…' : 'Connecting…'}
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

function App() {
  const [nickname, setNickname] = useState<string | null>(null)
  if (!nickname) return <Landing onEnter={setNickname} />
  return <Chat nickname={nickname} />
}

export default App
