import csv
import sqlite3
from core.config import DB_PATH, DATA_DIR

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id TEXT PRIMARY KEY,
    company TEXT,
    title TEXT,
    phone TEXT,
    email TEXT,
    url TEXT,
    status TEXT DEFAULT 'NEW',
    human_intervention_required INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

# Columns added after the base schema via idempotent ALTERs, so older
# databases created by previous versions are upgraded in place.
EXTRA_COLUMNS = ["email", "url", "status", "human_intervention_required"]


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(SCHEMA)
    existing = {row[1] for row in cursor.execute("PRAGMA table_info(leads)").fetchall()}
    for col in EXTRA_COLUMNS:
        if col not in existing:
            cursor.execute(f"ALTER TABLE leads ADD COLUMN {col} TEXT")
    conn.commit()
    conn.close()


def insert_lead(lead_id, company, title, phone=None, email=None, url=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO leads (id, company, title, phone, email, url) VALUES (?, ?, ?, ?, ?, ?)",
        (lead_id, company, title, phone, email, url),
    )
    conn.commit()
    conn.close()


def lead_exists(lead_id, phone=None, email=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = "SELECT 1 FROM leads WHERE id=?"
    params = [lead_id]
    if phone:
        query += " OR phone=?"
        params.append(phone)
    if email:
        query += " OR email=?"
        params.append(email)
    found = cursor.execute(query, params).fetchone() is not None
    conn.close()
    return found


def update_lead_status(lead_id, status, intervention=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE leads SET status = ?, human_intervention_required = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (status, 1 if intervention else 0, lead_id),
    )
    conn.commit()
    conn.close()


def fetch_all_leads():
    conn = _get_conn()
    rows = conn.execute(
        "SELECT id, company, title, phone, email, url, status FROM leads ORDER BY created_at"
    ).fetchall()
    conn.close()
    return rows


def export_leads(out_path=None):
    """Dump every stored lead to a CSV file. Returns the written path.

    Output columns mirror sample_leads.csv so the file can be opened in any
    spreadsheet app for manual review.
    """
    out_path = out_path or (DATA_DIR / "leads.csv")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rows = fetch_all_leads()
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "company", "title", "phone", "email", "url", "status"])
        writer.writerows([tuple(r) for r in rows])
    return str(out_path)
