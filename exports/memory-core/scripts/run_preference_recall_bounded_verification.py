#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTDIR = ROOT / "pkm-memory" / "outputs" / "task-375-preference-recall-bounded-verification-2026-05-10"
RETRIEVE = ROOT / "pkm-memory" / "retrieve_memory.py"

QUERIES = {
    "q1": "Как Юрию лучше отвечать: коротко по делу или с длинным разбором?",
    "q2": "Какие у Юрия предпочтения по стилю ответа?",
    "q3": "Как лучше говорить с Юрием — прямо и по делу или мягче?",
    "q4": "What reply style does Yuriy prefer?",
}


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    summary: dict[str, object] = {"queries": {}}
    for key, query in QUERIES.items():
        out_path = OUTDIR / f"{key}.json"
        subprocess.run(
            [
                "python3",
                str(RETRIEVE),
                "--mode",
                "local",
                "--max-items",
                "6",
                "--output",
                str(out_path),
                query,
            ],
            cwd=ROOT,
            check=True,
        )
        payload = json.loads(out_path.read_text(encoding="utf-8"))
        items = payload.get("items", [])
        summary["queries"][key] = {
            "query": query,
            "request_class": payload.get("request_classification", {}).get("request_class"),
            "top_paths": [item.get("document", {}).get("workspace_path") for item in items[:4]],
            "top_match_reasons": [item.get("match_reason") for item in items[:4]],
        }
    (OUTDIR / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
