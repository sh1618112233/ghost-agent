#!/usr/bin/env bash
# ============================================================
#  Ghost Agent - macOS setup
#  Creates a virtual environment and installs dependencies
# ============================================================
set -e

PYTHON_BIN="python3"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "[-] python3 was not found. Install Python 3.10+ (e.g. via 'brew install python')."
    exit 1
fi

echo "[*] Creating virtual environment..."
"$PYTHON_BIN" -m venv ghost_env

echo "[*] Installing Python dependencies..."
# shellcheck disable=SC1091
source ghost_env/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "[*] Installing Playwright Chromium browser..."
playwright install chromium

if [ ! -f ".env" ]; then
    echo "[*] Creating .env from .env.example ..."
    cp .env.example .env
    echo "[!] Edit .env and add your TELEGRAM_BOT_TOKEN before running the agent."
fi

echo ""
echo "[+] Setup complete. Run: ./scripts/run_mac.sh"
