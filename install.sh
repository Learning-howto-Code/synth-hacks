#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/Learning-howto-Code/synth-hacks"
TARGET_DIR="${MESH_DIR:-$HOME/.mesh}"
PYTHON="${PYTHON:-python3}"

bold() { printf "\033[1m%s\033[0m\n" "$1"; }
ok()   { printf "\033[32m✓\033[0m %s\n" "$1"; }
info() { printf "\033[36m→\033[0m %s\n" "$1"; }
err()  { printf "\033[31m✗\033[0m %s\n" "$1" >&2; }

bold "Installing mesh"
echo "Target: $TARGET_DIR"
echo

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  err "$PYTHON not found. Install Python 3.10+ and re-run."
  exit 1
fi
ok "$PYTHON found"

if ! command -v git >/dev/null 2>&1; then
  err "git not found. Install git and re-run."
  exit 1
fi
ok "git found"

if [ -d "$TARGET_DIR/.git" ]; then
  info "Existing install at $TARGET_DIR — pulling latest"
  git -C "$TARGET_DIR" pull --ff-only
else
  info "Cloning into $TARGET_DIR"
  git clone --depth 1 "$REPO_URL" "$TARGET_DIR"
fi
ok "Source ready"

info "Setting up Python venv"
"$PYTHON" -m venv "$TARGET_DIR/venv"
# shellcheck disable=SC1091
source "$TARGET_DIR/venv/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "$TARGET_DIR/backend/requirements.txt"
ok "Dependencies installed"

echo
bold "Installed at $TARGET_DIR"
echo
bold "Start the server:"
echo "  cd $TARGET_DIR/backend && source ../venv/bin/activate && python server.py"
echo
bold "Then open:"
echo "  https://frontend-gold-five-84.vercel.app"
echo
