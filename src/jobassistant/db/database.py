import sqlite3
from pathlib import Path

DB_PATH = Path("data/jobs.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    external_id TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    description TEXT NOT NULL,
    url TEXT NOT NULL,
    posted_at TEXT,
    salary_min REAL,
    salary_max REAL,
    fetched_at TEXT NOT NULL,
    UNIQUE (source, external_id)
);

CREATE TABLE IF NOT EXISTS scores (
    job_id INTEGER PRIMARY KEY,
    best_profile TEXT NOT NULL,
    score INTEGER NOT NULL,
    level_evidence TEXT NOT NULL DEFAULT 'unknown',
    reasons TEXT NOT NULL,          -- JSON como texto
    missing_skills TEXT NOT NULL,   -- JSON como texto
    model TEXT NOT NULL,
    scored_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs (id)
);
"""


def get_connection(
    db_path: Path | str = DB_PATH, check_same_thread: bool = True
) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=check_same_thread)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(scores)")]
    if "level_evidence" not in cols:
        conn.execute(
            "ALTER TABLE scores ADD COLUMN level_evidence TEXT NOT NULL DEFAULT 'unknown'"
        )
    conn.commit()