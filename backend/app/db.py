"""
app/db.py
---------
Thin sqlite wrapper. Batches are durable (survive a server restart / reload)
but this stays a single small file — no migration framework needed at this scale.
"""

import os
import sqlite3
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "data", "batches.db")

_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS batches (
    id          TEXT PRIMARY KEY,
    entity      TEXT NOT NULL,
    raw         TEXT NOT NULL,       -- exact JSON as received, never mutated
    normalized  TEXT NOT NULL,       -- JSON list[dict]
    flattened   TEXT NOT NULL,       -- JSON list[dict], denested + aliased
    status      TEXT NOT NULL,       -- pending | validating | validated | validated_with_errors
                                      -- | loading | loaded | loaded_with_errors
    count       INTEGER NOT NULL,
    results     TEXT,                -- JSON: per-row outcome from last validate/load run
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _lock:
        conn = get_connection()
        try:
            conn.execute(SCHEMA)
            conn.commit()
        finally:
            conn.close()
