import os

import requests
from dotenv import load_dotenv

from jobassistant.models import JobPosting, JobSearch

load_dotenv()

BASE_URL = "https://api.adzuna.com/v1/api/jobs/es/search/1"


def parse_job(raw: dict) -> JobPosting:
    """Convierte UNA oferta cruda de Adzuna al modelo común."""
    return JobPosting(
        source="adzuna",
        external_id=raw["id"],
        title=raw["title"],
        company=(raw.get("company") or {}).get("display_name"),
        location=(raw.get("location") or {}).get("display_name"),
        description=raw.get("description", ""),
        url=raw["redirect_url"],
        posted_at=raw.get("created"),
        salary_min=raw.get("salary_min"),
        salary_max=raw.get("salary_max"),
    )


def fetch_jobs(search: JobSearch) -> list[JobPosting]:
    """Llama a Adzuna una vez por ciudad y devuelve las ofertas filtradas."""
    jobs: list[JobPosting] = []

    for city in search.locations:
        params = {
            "app_id": os.getenv("ADZUNA_APP_ID"),
            "app_key": os.getenv("ADZUNA_APP_KEY"),
            "what": search.query,
            "where": city,
            "max_days_old": search.max_days_old,
            "results_per_page": search.results_per_page,
            "sort_by": "date",
        }
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()

        for raw in response.json().get("results", []):
            job = parse_job(raw)
            if job.matches(search):
                jobs.append(job)

    return jobs