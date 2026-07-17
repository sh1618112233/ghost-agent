#!/usr/bin/env bash
# ============================================================
#  Ghost Agent - macOS run
#  Runs the Telegram agent. Pass "main" to run the CLI instead.
# ============================================================
set -e

if [ ! -f "ghost_env/bin/activate" ]; then
    echo "[-] Virtual environment not found. Run: ./scripts/setup_mac.sh"
    exit 1
fi

# shellcheck disable=SC1091
source ghost_env/bin/activate

# Optional tuning:
# export BROWSER_CHANNEL=chrome        # use installed Google Chrome
# export HEADLESS=false

if [ "$1" = "main" ]; then
    python main.py
else
    python telegram_agent.py
fi
