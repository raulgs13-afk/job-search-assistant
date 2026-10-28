import sqlite3
from datetime import datetime, timezone

from jobassistant.models import JobPosting


def save_jobs(conn: sqlite3.Connection, jobs: list[JobPosting]) -> int:
    """Guarda ofertas ignorando duplicados. Devuelve cuántas son nuevas."""
    now = datetime.now(timezone.utc).isoformat()
    inserted = 0
    for job in jobs:
        cursor = conn.execute(
            """
            INSERT INTO jobs (source, external_id, title, company, location,
                              description, url, posted_at, salary_min,
                              salary_max, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (source, external_id) DO NOTHING
            """,
            (
                job.source,
                job.external_id,
                job.title,
                job.company,
                job.location,
                job.description,
                str(job.url),
                job.posted_at.isoformat() if job.posted_at else None,
                job.salary_min,
                job.salary_max,
                now,
            ),
        )
        inserted += cursor.rowcount
    conn.commit()
    return inserted


def list_jobs(conn: sqlite3.Connection, location: str | None = None) -> list[sqlite3.Row]:
    sql = "SELECT * FROM jobs"
    params: list = []
    if location:
        sql += " WHERE location LIKE ?"
        params.append(f"%{location}%")
    sql += " ORDER BY posted_at DESC"
    return conn.execute(sql, params).fetchall()