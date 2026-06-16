#!/usr/bin/env bash
#
# ClaudeCard one-line installer.
#
#   curl -fsSL https://raw.githubusercontent.com/meetp06/claude-wallpaper/main/install.sh | bash
#
# It finds (or installs) Python 3, sets up an isolated virtual environment,
# installs all dependencies + headless Chromium, and drops a `claudecard`
# launcher on your PATH. Downloaded images go to your Downloads folder.
#
set -euo pipefail

REPO_URL="https://github.com/meetp06/claude-wallpaper.git"
RAW_BASE="https://raw.githubusercontent.com/meetp06/claude-wallpaper/main"
INSTALL_DIR="${CLAUDECARD_DIR:-$HOME/.claudecard}"
BIN_DIR="$HOME/.local/bin"

say()  { printf '\033[1;32m==>\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m==>\033[0m %s\n' "$*"; }
die()  { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }

# 1. Find a working Python 3 (try common names and versions).
find_python() {
  local c
  for c in python3 python3.13 python3.12 python3.11 python3.10 python3.9 python; do
    if command -v "$c" >/dev/null 2>&1 \
       && "$c" -c 'import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 8) else 1)' 2>/dev/null; then
      command -v "$c"
      return 0
    fi
  done
  return 1
}

PY="$(find_python || true)"

# 2. No Python 3? Install it automatically (Homebrew on macOS).
if [ -z "$PY" ]; then
  if [ "$(uname)" = "Darwin" ]; then
    if ! command -v brew >/dev/null 2>&1; then
      say "Installing Homebrew (needed to install Python)..."
      NONINTERACTIVE=1 /bin/bash -c \
        "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
      [ -x /opt/homebrew/bin/brew ] && eval "$(/opt/homebrew/bin/brew shellenv)"
      [ -x /usr/local/bin/brew ]    && eval "$(/usr/local/bin/brew shellenv)"
    fi
    say "Installing Python 3 via Homebrew..."
    brew install python
  elif command -v apt-get >/dev/null 2>&1; then
    say "Installing Python 3 via apt..."
    sudo apt-get update -y && sudo apt-get install -y python3 python3-venv python3-pip
  else
    die "Python 3 not found. Install Python 3.8+ and re-run this installer."
  fi
  PY="$(find_python || true)"
  [ -n "$PY" ] || die "Python 3 still not found after install."
fi
say "Using Python: $("$PY" --version 2>&1)  ($PY)"

# 3. Fetch the source (git if available, otherwise plain curl).
say "Downloading ClaudeCard into $INSTALL_DIR ..."
if command -v git >/dev/null 2>&1; then
  if [ -d "$INSTALL_DIR/.git" ]; then
    git -C "$INSTALL_DIR" pull --ff-only --quiet || true
  else
    rm -rf "$INSTALL_DIR"
    git clone --depth 1 --quiet "$REPO_URL" "$INSTALL_DIR"
  fi
else
  mkdir -p "$INSTALL_DIR"
  curl -fsSL "$RAW_BASE/claudecard.py"     -o "$INSTALL_DIR/claudecard.py"
  curl -fsSL "$RAW_BASE/requirements.txt"  -o "$INSTALL_DIR/requirements.txt"
fi

# 4. Virtual environment + Python dependencies.
say "Creating virtual environment and installing dependencies..."
"$PY" -m venv "$INSTALL_DIR/.venv"
VENV_PY="$INSTALL_DIR/.venv/bin/python"
"$VENV_PY" -m pip install --quiet --upgrade pip
"$VENV_PY" -m pip install --quiet -r "$INSTALL_DIR/requirements.txt"

# 5. Headless Chromium for Playwright (one-time, ~150 MB).
say "Installing headless Chromium (one-time download)..."
"$VENV_PY" -m playwright install chromium

# 6. Launcher on PATH.
say "Creating 'claudecard' launcher in $BIN_DIR ..."
mkdir -p "$BIN_DIR"
cat > "$BIN_DIR/claudecard" <<EOF
#!/usr/bin/env bash
exec "$VENV_PY" "$INSTALL_DIR/claudecard.py" "\$@"
EOF
chmod +x "$BIN_DIR/claudecard"

# Make sure BIN_DIR is on PATH (add to the user's shell rc if missing).
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    RC="$HOME/.zshrc"; [ -n "${BASH_VERSION:-}" ] && RC="$HOME/.bashrc"
    printf '\nexport PATH="%s:$PATH"\n' "$BIN_DIR" >> "$RC"
    warn "Added $BIN_DIR to PATH in $RC — run 'source $RC' or open a new terminal."
    ;;
esac

echo
say "Installed! Images save to your Downloads folder."
echo
echo "  Run it:        claudecard          # then paste a Claude link when asked"
echo "  One link:      claudecard \"https://claude.com/blog/...\""
echo "  Clipboard:     claudecard --watch  # auto-grab whenever you copy a Claude link"
echo
