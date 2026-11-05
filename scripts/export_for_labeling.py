import argparse
import json
import random
from pathlib import Path

from jobassistant.db.database import get_connection
from jobassistant.scoring.scorer import skip_reason

parser = argparse.ArgumentParser()
parser.add_argument("--n", type=int, default=12, help="Casos nuevos a exportar")
parser.add_argument("--seed", type=int, default=7)
parser.add_argument("--out", default="tests/eval_cases.json")
args = parser.parse_args()

out_path = Path(args.out)
existing = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else []

# Ofertas ya usadas en cualquier conjunto
known = set()
for p in Path("tests").glob("*_cases.json"):
    for c in json.loads(p.read_text(encoding="utf-8")):
        known.add((c["source"], c["external_id"]))

conn = get_connection()
rows = conn.execute(
    "SELECT source, external_id, title, company, location, url, description FROM jobs"
).fetchall()
rows = [
    r for r in rows
    if (r["source"], r["external_id"]) not in known
    and skip_reason(r["title"], r["description"]) is None
]
random.Random(args.seed).shuffle(rows)
sample = rows[: args.n]

new_cases = [
    {
        "source": r["source"],
        "external_id": r["external_id"],
        "title": r["title"],
        "company": r["company"],
        "label": "",
        "notes": "",
    }
    for r in sample
]
out_path.write_text(
    json.dumps(existing + new_cases, ensure_ascii=False, indent=2), encoding="utf-8"
)

lines = [
    f"## {i}. {r['title']} | {r['company']} | {r['location']}\n"
    f"{r['url']}\n\n{r['description']}\n"
    for i, r in enumerate(sample)
]
Path("data/eval_to_read.md").write_text("\n".join(lines), encoding="utf-8")

print(f"{len(new_cases)} casos nuevos añadidos a {out_path} (total {len(existing) + len(new_cases)})")