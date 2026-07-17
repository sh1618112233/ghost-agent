#!/usr/bin/env bash
# ============================================================
#  Ghost Agent - Linux setup
#  Creates a virtual environment and installs dependencies
# ============================================================
set -e

if ! command -v python3 >/dev/null 2>&1; then
    echo "[-] python3 was not found. Install Python 3.10+ first."
    exit 1
fi

echo "[*] Creating virtual environment..."
python3 -m venv ghost_env

echo "[*] Installing Python dependencies..."
# shellcheck disable=SC1091
source ghost_env/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo "[*] Installing Playwright Chromium browser + system deps..."
# Install OS-level libraries Chromium needs (Debian/Ubuntu). Safe to skip on other distros.
if command -v apt-get >/dev/null 2>&1; then
    echo "[*] Installing Playwright system dependencies (sudo may prompt)..."
    sudo playwright install-deps chromium || echo "[!] Optional: run 'sudo playwright install-deps chromium' later."
fi
playwright install chromium

if [ ! -f ".env" ]; then
    echo "[*] Creating .env from .env.example ..."
    cp .env.example .env
    echo "[!] Edit .env and add your TELEGRAM_BOT_TOKEN before running the agent."
fi

echo ""
echo "[+] Setup complete. Run: ./scripts/run_linux.sh"
