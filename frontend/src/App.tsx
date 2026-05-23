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
          <span className="badge">⚡ Peer-to-peer · Offline-capable · Encrypted</span>
          <h1>
            Chat anywhere.<br />
            <span className="grad">Even off-grid.</span>
          </h1>
          <p className="lede">
            Mesh is a tiny, open-source chat that runs entirely on your machines.
            No servers. No accounts. No internet required.
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
          <p className="lede">One command. macOS, Linux, or Windows.</p>
        </div>

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
            <h3>No internet needed</h3>
            <p>Peers discover each other directly over local network and Bluetooth.</p>
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
              <p>Run the one-liner above. The local server starts on port 8000.</p>
            </div>
          </li>
          <li>
            <span className="step-num">2</span>
            <div>
              <h3>Open the web app</h3>
              <p>Visit <code>mesh.app</code>, pick a nickname, hit Enter. The web app connects to your local server.</p>
            </div>
          </li>
          <li>
            <span className="step-num">3</span>
            <div>
              <h3>Share &amp; chat</h3>
              <p>Tell a friend to do the same. Your machines find each other; messages flow peer-to-peer.</p>
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
        <form className="composer" onSubmit={(e) => { e.preventDefault(); send() }}>
          <input
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder={connected ? 'Type message…' : 'Connecting to localhost:8000… (is the server running?)'}
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
