import argparse

from jobassistant.db.database import get_connection, init_db
from jobassistant.db.repository import list_jobs, save_jobs
from jobassistant.models import JobSearch
from jobassistant.sources.adzuna import fetch_jobs


def main() -> None:
    parser = argparse.ArgumentParser(description="Asistente de búsqueda de empleo")
    parser.add_argument("--query", default="python", help="Palabra clave a buscar")
    parser.add_argument("--days", type=int, default=7, help="Antigüedad máxima en días")
    parser.add_argument(
        "--locations", nargs="+", default=["Málaga", "Madrid"], help="Ciudades"
    )
    parser.add_argument(
        "--no-fetch", action="store_true", help="No llamar a la API, solo listar la BD"
    )
    args = parser.parse_args()

    conn = get_connection()
    init_db(conn)

    if not args.no_fetch:
        search = JobSearch(
            query=args.query, locations=args.locations, max_days_old=args.days
        )
        jobs = fetch_jobs(search)
        new = save_jobs(conn, jobs)
        print(f"Descargadas: {len(jobs)} | Nuevas guardadas: {new}\n")

    for row in list_jobs(conn):
        print(f"{row['posted_at']} | {row['title']} | {row['company']} | {row['location']}")


if __name__ == "__main__":
    main()