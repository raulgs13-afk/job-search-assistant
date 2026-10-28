import json
from pathlib import Path

from jobassistant.sources.adzuna import parse_job


def test_parse_all_sample_jobs():
    data = json.loads(Path("data/sample_response.json").read_text(encoding="utf-8"))
    jobs = [parse_job(raw) for raw in data["results"]]
    assert len(jobs) == data["count"] or len(jobs) == len(data["results"])
    assert all(job.title for job in jobs)