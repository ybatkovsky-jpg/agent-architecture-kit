#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "outputs" / "task-379-task-id-dominance-done-next-2026-05-10"
RETRIEVER = ROOT / "retrieve_memory.py"

CASES = [
    ("en-task363-done", "what is already done for task 363"),
    ("en-task363-next", "what next for task 363"),
    ("en-task363-now", "where is task 363 now"),
    ("ru-task363-done", "что уже сделано по task 363"),
    ("ru-task363-next", "что дальше по task 363"),
    ("ru-task363-now", "где сейчас task 363"),
    ("en-task360-status", "what is already done for task 360 and where is it now"),
    ("ru-task360-status", "что уже готово по текущей задаче 360 и на каком этапе сейчас"),
]

TARGETS = {
    "task363": "task-manager/artifacts/task-363-memory-core-v1-conflict-open-question-synthesis-handoff-2026-05-07.md",
    "task360": "task-manager/artifacts/task-360-memory-core-v1-routing-policy-enforcement-handoff-2026-05-07.md",
}

BAD_TOP1 = {
    "task-manager/artifacts/task-374-audit-trace-bounded-boost-note-2026-05-10.md",
    "task-manager/notes/task-363-verifier-sync-verdict-2026-05-10.md",
    "task-manager/artifacts/task-362-memory-core-v1-citation-envelope-handoff-2026-05-07.md",
}


def run_case(slug: str, query: str) -> dict:
    output_path = OUTDIR / f"{slug}.json"
    cmd = [
        "python3",
        str(RETRIEVER),
        "--mode", "local",
        "--max-items", "6",
        "--output", str(output_path),
        query,
    ]
    subprocess.run(cmd, check=True, cwd=str(ROOT.parent))
    return json.loads(output_path.read_text(encoding="utf-8"))


def top_paths(payload: dict) -> list[str]:
    return [item.get("document", {}).get("workspace_path", "") for item in payload.get("items", [])]


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    results = []
    all_pass = True
    for slug, query in CASES:
        payload = run_case(slug, query)
        paths = top_paths(payload)
        top1 = paths[0] if paths else ""
        if "task363" in slug:
            expected = TARGETS["task363"]
        else:
            expected = TARGETS["task360"]
        pass_top1 = top1 == expected
        contamination = top1 in BAD_TOP1
        if not pass_top1:
            all_pass = False
        if contamination:
            all_pass = False
        results.append({
            "slug": slug,
            "query": query,
            "request_class": payload.get("request_classification", {}).get("request_class"),
            "top1": top1,
            "top3": paths[:3],
            "pass_top1": pass_top1,
            "top1_contamination": contamination,
        })

    summary = {
        "verdict": "pass" if all_pass else "partial-success",
        "results": results,
    }
    (OUTDIR / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
