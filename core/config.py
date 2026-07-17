import os
import logging
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "tailored_outputs"
SESSION_DIR = DATA_DIR / "web_session"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "ghost_agent.log"

load_dotenv(BASE_DIR / ".env")

DB_PATH = str(BASE_DIR / "core" / "ghost_protocol.db")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.2:3b")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))


def setup_logging():
    """Configure root logging once: console + rotating-ish log file.

    Logs stream to the console (so the Telegram bot can read them over its
    subprocess pipe) AND are persisted to logs/ghost_agent.log for review.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )


def browser_launch_kwargs():
    """Cross-platform browser launch options.

    BROWSER_CHANNEL: "chrome" / "msedge" / "" (empty = Playwright's bundled Chromium).
    HEADLESS: "true"/"false"; default false because the first run needs a visible
    window to log in to job sites and scan the WhatsApp Web QR code.
    """
    kwargs = {
        "headless": os.getenv("HEADLESS", "false").lower() in ("1", "true", "yes"),
        "args": ["--disable-blink-features=AutomationControlled"],
    }
    channel = os.getenv("BROWSER_CHANNEL", "").strip()
    if channel:
        kwargs["channel"] = channel
    return kwargs
