import json
from collections.abc import Iterator
from sqlite3 import Connection

from fastapi import Depends, FastAPI, Query
from pydantic import BaseModel

from jobassistant.db.database import get_connection, init_db
from jobassistant.db.repository import list_jobs, list_ranked

app = FastAPI(
    title="Job Search Assistant",
    description="Ofertas de empleo puntuadas con IA contra tus perfiles de CV.",
    version="0.1.0",
)


class JobOut(BaseModel):
    id: int
    source: str
    title: str
    company: str | None
    location: str | None
    url: str
    posted_at: str | None


class RankedJobOut(BaseModel):
    title: str
    company: str | None
    location: str | None
    url: str
    score: int
    best_profile: str
    reasons: list[str]
    missing_skills: list[str]


def get_db() -> Iterator[Connection]:
    conn = get_connection(check_same_thread=False)
    init_db(conn)
    try:
        yield conn
    finally:
        conn.close()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/jobs", response_model=list[JobOut])
def get_jobs(
    location: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    conn: Connection = Depends(get_db),
):
    rows = list_jobs(conn, location=location)[:limit]
    return [JobOut(**{k: row[k] for k in JobOut.model_fields}) for row in rows]


@app.get("/jobs/ranked", response_model=list[RankedJobOut])
def get_ranked(
    min_score: int = Query(0, ge=0, le=100),
    profile: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    conn: Connection = Depends(get_db),
):
    rows = list_ranked(conn, min_score=min_score)
    if profile:
        rows = [r for r in rows if r["best_profile"] == profile]
    return [
        RankedJobOut(
            title=r["title"],
            company=r["company"],
            location=r["location"],
            url=r["url"],
            score=r["score"],
            best_profile=r["best_profile"],
            reasons=json.loads(r["reasons"]),
            missing_skills=json.loads(r["missing_skills"]),
        )
        for r in rows[:limit]
    ]