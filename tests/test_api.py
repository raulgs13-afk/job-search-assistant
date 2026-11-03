import sqlite3

from fastapi.testclient import TestClient

from jobassistant.api.main import app, get_db
from jobassistant.db.database import init_db
from jobassistant.db.repository import save_jobs, save_score
from jobassistant.models import JobPosting, JobScore


def make_client():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    app.dependency_overrides[get_db] = lambda: conn
    return TestClient(app), conn


def seed(conn, score=80):
    job = JobPosting(
        source="test",
        external_id="1",
        title="AI Engineer",
        location="Madrid",
        description="...",
        url="https://example.com/job/1",
    )
    save_jobs(conn, [job])
    job_id = conn.execute("SELECT id FROM jobs").fetchone()["id"]
    save_score(
        conn,
        job_id,
        JobScore(best_profile="software_ia", score=score, reasons=["Python"], missing_skills=["AWS"]),
        "test-model",
    )


def test_health():
    client, _ = make_client()
    assert client.get("/health").json() == {"status": "ok"}
    app.dependency_overrides.clear()


def test_ranked_filters_by_min_score():
    client, conn = make_client()
    seed(conn, score=80)
    assert len(client.get("/jobs/ranked?min_score=60").json()) == 1
    assert client.get("/jobs/ranked?min_score=90").json() == []
    app.dependency_overrides.clear()


def test_invalid_min_score_is_rejected():
    client, _ = make_client()
    assert client.get("/jobs/ranked?min_score=500").status_code == 422
    app.dependency_overrides.clear()