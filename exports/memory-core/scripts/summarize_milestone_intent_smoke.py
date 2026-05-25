#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def top_item(payload: dict) -> dict:
    items = payload.get("items") or []
    if not items:
        return {"title": None, "path": None, "score": None, "match_reason": None}
    item = items[0]
    doc = item.get("document") or {}
    return {
        "title": doc.get("title"),
        "path": doc.get("workspace_path"),
        "score": item.get("score"),
        "match_reason": item.get("match_reason"),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: summarize_milestone_intent_smoke.py <outdir>", file=sys.stderr)
        return 2
    outdir = Path(sys.argv[1])

    pairs = [
        {
            "query": "postgres activation milestone",
            "db": outdir / "query-postgres-activation-milestone-db.json",
            "local": outdir / "query-postgres-activation-milestone-local.json",
            "expected_top_path": "task-manager/artifacts/task-107-postgres-activation-and-first-live-ingest-2026-04-26.md",
            "status": "closed",
            "note": "Primary milestone-defining artifact should rank first for the intent-style postgres milestone query.",
        },
        {
            "query": "activation milestone",
            "db": outdir / "query-activation-milestone-db.json",
            "local": outdir / "query-activation-milestone-local.json",
            "expected_top_path": "task-manager/artifacts/task-107-postgres-activation-and-first-live-ingest-2026-04-26.md",
            "status": "bounded_remainder",
            "note": "Generic milestone query is still broader and currently prefers later retrieval-pass artifacts in DB mode.",
        },
        {
            "query": "postgres activation",
            "db": outdir / "query-postgres-activation-db.json",
            "local": outdir / "query-postgres-activation-local.json",
            "expected_top_path": "task-manager/artifacts/task-107-postgres-activation-and-first-live-ingest-2026-04-26.md",
            "status": "closed",
            "note": "Non-milestone postgres activation query should still resolve to the activation artifact.",
        },
    ]

    rows = []
    for pair in pairs:
        db_top = top_item(load(pair["db"]))
        local_top = top_item(load(pair["local"]))
        rows.append({
            "query": pair["query"],
            "expected_top_path": pair["expected_top_path"],
            "db_top": db_top,
            "local_top": local_top,
            "db_matches_expected": db_top.get("path") == pair["expected_top_path"],
            "local_matches_expected": local_top.get("path") == pair["expected_top_path"],
            "status": pair["status"],
            "note": pair["note"],
        })

    payload = {
        "summary_version": "2026-04-26.task118",
        "outdir": str(outdir),
        "overall": {
            "milestone_intent_specific_query_closed": rows[0]["db_matches_expected"],
            "generic_activation_milestone_still_broader": not rows[1]["db_matches_expected"],
            "postgres_activation_query_ok": rows[2]["db_matches_expected"],
        },
        "results": rows,
    }

    output = outdir / "task-118-milestone-intent-summary.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
