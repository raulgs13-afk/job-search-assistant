import sqlite3

from jobassistant.db.database import init_db
from jobassistant.db.repository import list_jobs, save_jobs
from jobassistant.models import JobPosting


def make_job(external_id="1", location="Madrid"):
    return JobPosting(
        source="test",
        external_id=external_id,
        title="Python Developer",
        location=location,
        description="...",
        url="https://example.com/job",
    )


def make_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def test_save_ignores_duplicates():
    conn = make_conn()
    assert save_jobs(conn, [make_job("1"), make_job("2")]) == 2
    assert save_jobs(conn, [make_job("1")]) == 0
    assert len(list_jobs(conn)) == 2


def test_list_filters_by_location():
    conn = make_conn()
    save_jobs(conn, [make_job("1", "Madrid"), make_job("2", "Málaga")])
    assert len(list_jobs(conn, location="Madrid")) == 1