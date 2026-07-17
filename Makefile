# Ghost Agent - convenience targets (Linux / macOS). Windows: use scripts\*.bat
.PHONY: setup run cli telegram export clean help

help:
	@echo "Ghost Agent targets:"
	@echo "  make setup     create venv + install deps + browser + .env"
	@echo "  make run        start the Telegram bot (default mode)"
	@echo "  make cli        run the interactive CLI"
	@echo "  make telegram   start the Telegram bot"
	@echo "  make export     export stored leads to data/leads.csv"
	@echo "  make clean      remove venv, logs, browser sessions, and the DB"

setup:
	@case "$$(uname -s)" in \
	  Darwin) ./scripts/setup_mac.sh ;; \
	  Linux)  ./scripts/setup_linux.sh ;; \
	  *)      echo "[-] No make target for this OS. Use scripts\\setup_windows.bat on Windows." ;; \
	esac

run: telegram

cli:
	@test -f ghost_env/bin/activate || (echo "[-] Run 'make setup' first"; exit 1)
	@. ghost_env/bin/activate && python main.py --interactive

telegram:
	@test -f ghost_env/bin/activate || (echo "[-] Run 'make setup' first"; exit 1)
	@. ghost_env/bin/activate && python telegram_agent.py

export:
	@test -f ghost_env/bin/activate || (echo "[-] Run 'make setup' first"; exit 1)
	@. ghost_env/bin/activate && python main.py --export

clean:
	rm -rf ghost_env .venv logs data/web_session data/tailored_outputs data/leads.csv
	find . -name "*.db" -not -path "./.git/*" -delete
