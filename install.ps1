# Mesh installer for Windows (PowerShell)
# Usage:
#   iwr https://raw.githubusercontent.com/Learning-howto-Code/synth-hacks/main/install.ps1 -useb | iex

$ErrorActionPreference = 'Stop'

$Repo = 'https://github.com/Learning-howto-Code/synth-hacks'
$Target = if ($env:MESH_DIR) { $env:MESH_DIR } else { Join-Path $env:USERPROFILE '.mesh' }

function Bold($t) { Write-Host $t -ForegroundColor White }
function Ok($t)   { Write-Host "[ok] $t" -ForegroundColor Green }
function Info($t) { Write-Host "[..] $t" -ForegroundColor Cyan }
function Err($t)  { Write-Host "[!!] $t" -ForegroundColor Red }

Bold "Installing mesh"
Write-Host "Target: $Target"
Write-Host ""

# Find Python
$python = $null
foreach ($cmd in @('python', 'python3', 'py')) {
    try {
        $v = & $cmd --version 2>$null
        if ($LASTEXITCODE -eq 0) { $python = $cmd; break }
    } catch {}
}
if (-not $python) {
    Err "Python not found. Install Python 3.10+ from https://www.python.org/downloads/ and re-run."
    exit 1
}
Ok "$python found ($v)"

# Find git
try { git --version | Out-Null } catch {
    Err "git not found. Install from https://git-scm.com/download/win and re-run."
    exit 1
}
Ok "git found"

# Clone or pull
if (Test-Path (Join-Path $Target '.git')) {
    Info "Existing install at $Target -- pulling latest"
    git -C $Target pull --ff-only
} else {
    Info "Cloning into $Target"
    git clone --depth 1 $Repo $Target
}
Ok "Source ready"

# Set up venv
Info "Setting up Python venv"
& $python -m venv (Join-Path $Target 'venv')
$venvPython = Join-Path $Target 'venv\Scripts\python.exe'
& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install --quiet -r (Join-Path $Target 'backend\requirements.txt')
Ok "Dependencies installed"

Write-Host ""
Bold "Installed at $Target"
Write-Host ""
Bold "Start the server:"
Write-Host "  cd $Target\backend; ..\venv\Scripts\python.exe server.py"
Write-Host ""
Bold "Then open:"
Write-Host "  https://frontend-gold-five-84.vercel.app"
Write-Host ""
