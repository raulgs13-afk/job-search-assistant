import argparse
import json

from anthropic import Anthropic

from jobassistant.db.database import get_connection, init_db
from jobassistant.db.repository import (
    get_unscored_jobs,
    list_jobs,
    list_ranked,
    save_jobs,
    save_score,
)
from jobassistant.models import JobScore, JobSearch
from jobassistant.scoring.scorer import MODEL, load_profiles, score_job, skip_reason
from jobassistant.sources.adzuna import fetch_jobs


def main() -> None:
    parser = argparse.ArgumentParser(description="Asistente de búsqueda de empleo")
    parser.add_argument("--query", default="python")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--locations", nargs="+", default=["Málaga", "Madrid"])
    parser.add_argument("--no-fetch", action="store_true", help="No llamar a Adzuna")
    parser.add_argument("--score", action="store_true", help="Puntuar ofertas con Claude")
    parser.add_argument("--limit", type=int, default=10, help="Máx. ofertas a puntuar")
    parser.add_argument("--top", type=int, default=15, help="Cuántas mostrar en el ranking")
    parser.add_argument("--rescore", action="store_true", help="Borrar scores y puntuar de nuevo")
    args = parser.parse_args()

    conn = get_connection()
    init_db(conn)

    if args.rescore:
        conn.execute("DELETE FROM scores")
        conn.commit()

    if not args.no_fetch:
        search = JobSearch(query=args.query, locations=args.locations, max_days_old=args.days)
        jobs = fetch_jobs(search)
        print(f"Descargadas: {len(jobs)} | Nuevas guardadas: {save_jobs(conn, jobs)}\n")

    if args.score:
        profiles = load_profiles()
        client = Anthropic()
        pending = get_unscored_jobs(conn, args.limit)
        print(f"Puntuando {len(pending)} ofertas con {MODEL}...")
        skipped = 0
        for job in pending:
            reason = skip_reason(job["title"], job["description"])
            if reason:
                skipped += 1
                save_score(
                    conn,
                    job["id"],
                    JobScore(
                        best_profile="none",
                        score=0,
                        reasons=[f"Descartada por regla: {reason}"],
                        missing_skills=[],
                    ),
                    "rules",
                )
                print(f"  SKIP  {job['title']} ({reason})")
                continue
            try:
                save_score(conn, job["id"], score_job(client, profiles, job), MODEL)
                print(f"  OK  {job['title']}")
            except Exception as exc:
                print(f"  ERROR  {job['title']}: {exc}")
        print(f"\nDescartadas por regla (sin gastar API): {skipped}")

        for row in list_ranked(conn)[: args.top]:
            print(f"\n[{row['score']}] {row['title']} | {row['company']} | {row['location']}")
            print(f"    CV recomendado: {row['best_profile']}")
            print(f"    Motivos: {'; '.join(json.loads(row['reasons']))}")
            print(f"    Faltan: {', '.join(json.loads(row['missing_skills'])) or '-'}")
            print(f"    {row['url']}")
        return

    for row in list_jobs(conn):
        print(f"{row['posted_at']} | {row['title']} | {row['company']} | {row['location']}")


if __name__ == "__main__":
    main()