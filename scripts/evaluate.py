import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

from anthropic import Anthropic

from jobassistant.db.database import get_connection
from jobassistant.scoring.scorer import MODEL, load_profiles, score_job, skip_reason

CASES_PATH = Path("tests/eval_cases.json")
HISTORY_PATH = Path("data/eval_history.jsonl")
VALID_LABELS = {"alta", "media", "baja"}


def predicted_label(score: int) -> str:
    if score >= 65:
        return "alta"
    if score >= 50:
        return "media"
    return "baja"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--note", default="", help="Descripción de esta versión del prompt")
    args = parser.parse_args()

    cases = [
        c
        for c in json.loads(CASES_PATH.read_text(encoding="utf-8"))
        if c["label"] in VALID_LABELS
    ]
    conn = get_connection()
    client = Anthropic()
    profiles = load_profiles()

    results = []
    for case in cases:
        job = conn.execute(
            "SELECT * FROM jobs WHERE source = ? AND external_id = ?",
            (case["source"], case["external_id"]),
        ).fetchone()
        if job is None:
            print(f"No está en la BD: {case['title']}")
            continue
        if skip_reason(job["title"], job["description"]):
            score, level = 0, "rules"
        else:
            result = score_job(client, profiles, job)
            score, level = result.score, result.level_evidence
        results.append({**case, "score": score, "level": level, "predicted": predicted_label(score)})

    correct = sum(r["label"] == r["predicted"] for r in results)
    severe = [
        r for r in results
        if {r["label"], r["predicted"]} == {"alta", "baja"}
    ]

    by_label = {
        lab: [r["score"] for r in results if r["label"] == lab]
        for lab in ("alta", "media", "baja")
    }
    highs, lows = by_label["alta"], by_label["baja"]
    pairs = [(h, l) for h in highs for l in lows]
    ordering = sum(h > l for h, l in pairs) / len(pairs) if pairs else None

    print(f"\n{'Etiqueta':8} {'Predicha':8} {'Score':>5}  Nivel  Oferta")
    for r in sorted(results, key=lambda r: -r["score"]):
        flag = "OK " if r["label"] == r["predicted"] else "XX "
        print(
            f"{flag}{r['label']:8} {r['predicted']:8} {r['score']:>5}  "
            f"[{r['level']}]  {r['title']} | {r['company']}"
        )
        if flag == "XX " and r["notes"]:
            print(f"      nota: {r['notes']}")

    print(f"\nAciertos exactos: {correct}/{len(results)}")
    print(f"Errores graves (alta vs baja): {len(severe)}")
    severe_unknown = sum(r["level"] == "unknown" for r in severe)
    pred_alta = [r for r in results if r["predicted"] == "alta"]
    for lvl in ("explicit_junior", "unknown", "explicit_senior"):
        group = [r for r in pred_alta if r["level"] == lvl]
        if group:
            hits = sum(r["label"] == "alta" for r in group)
            print(f"  predichas 'alta' con nivel {lvl}: {hits}/{len(group)} correctas")
    print(f"  de ellos con nivel 'unknown': {severe_unknown}/{len(severe)}")
    for lab, scores in by_label.items():
        if scores:
            print(f"Media de score en '{lab}': {mean(scores):.1f} ({len(scores)} casos)")
    if ordering is not None:
        print(f"Pares alta>baja bien ordenados: {ordering:.0%}")

    record = {
        "date": datetime.now(timezone.utc).isoformat(),
        "model": MODEL,
        "note": args.note,
        "cases": len(results),
        "exact_accuracy": round(correct / len(results), 3),
        "severe_errors": len(severe),
        "severe_unknown_level": severe_unknown,
        "pair_ordering": None if ordering is None else round(ordering, 3),
    }
    with HISTORY_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()