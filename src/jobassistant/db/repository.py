import sqlite3
from datetime import datetime, timezone

from jobassistant.models import JobPosting

import json

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

def get_unscored_jobs(conn, limit: int = 10) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT j.* FROM jobs j
        LEFT JOIN scores s ON s.job_id = j.id
        WHERE s.job_id IS NULL
        ORDER BY j.posted_at DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()


def save_score(conn, job_id: int, score, model: str) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO scores
            (job_id, best_profile, score, level_evidence, reasons,
             missing_skills, model, scored_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id,
            score.best_profile,
            score.score,
            score.level_evidence,
            json.dumps(score.reasons, ensure_ascii=False),
            json.dumps(score.missing_skills, ensure_ascii=False),
            model,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()


def list_ranked(conn, min_score: int = 0) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT j.title, j.company, j.location, j.url,
               s.score, s.best_profile, s.level_evidence,
               s.reasons, s.missing_skills
        FROM jobs j JOIN scores s ON s.job_id = j.id
        WHERE s.score >= ?
        ORDER BY s.score DESC
        """,
        (min_score,),
    ).fetchall()