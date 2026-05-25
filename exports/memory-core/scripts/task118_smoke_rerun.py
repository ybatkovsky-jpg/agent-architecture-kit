#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path("/home/openclaw/.openclaw/workspace")
OUTDIR = ROOT / "pkm-memory/outputs/smoke-db-retrieval-milestone-pass-2026-04-26"
OUTDIR.mkdir(parents=True, exist_ok=True)

COMMANDS = [
    ["python3", "pkm-memory/retrieve_memory.py", "postgres activation milestone", "--mode", "psql", "--env-file", "pkm-memory/config/memory.env", "--output", str(OUTDIR / "query-postgres-activation-milestone-db.json")],
    ["python3", "pkm-memory/retrieve_memory.py", "postgres activation milestone", "--mode", "local", "--output", str(OUTDIR / "query-postgres-activation-milestone-local.json")],
    ["python3", "pkm-memory/retrieve_memory.py", "postgres activation", "--mode", "psql", "--env-file", "pkm-memory/config/memory.env", "--output", str(OUTDIR / "query-postgres-activation-db.json")],
    ["python3", "pkm-memory/retrieve_memory.py", "postgres activation", "--mode", "local", "--output", str(OUTDIR / "query-postgres-activation-local.json")],
    ["python3", "pkm-memory/retrieve_memory.py", "activation milestone", "--mode", "psql", "--env-file", "pkm-memory/config/memory.env", "--output", str(OUTDIR / "query-activation-milestone-db.json")],
    ["python3", "pkm-memory/retrieve_memory.py", "activation milestone", "--mode", "local", "--output", str(OUTDIR / "query-activation-milestone-local.json")],
    ["python3", "pkm-memory/retrieve_memory.py", "task-107-postgres-activation-and-first-live-ingest", "--mode", "psql", "--env-file", "pkm-memory/config/memory.env", "--output", str(OUTDIR / "query-task-107-db.json")],
    ["python3", "pkm-memory/retrieve_memory.py", "task-107-postgres-activation-and-first-live-ingest", "--mode", "local", "--output", str(OUTDIR / "query-task-107-local.json")],
    ["python3", "pkm-memory/scripts/compare_milestone_precision_smoke.py"],
    ["python3", "pkm-memory/scripts/summarize_milestone_intent_smoke.py", str(OUTDIR)],
]


def main() -> int:
    run_log: list[dict] = []
    for cmd in COMMANDS:
        completed = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        run_log.append({
            "cmd": cmd,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        })
        if completed.returncode != 0:
            (OUTDIR / "task-118-smoke-rerun-log.json").write_text(
                json.dumps(run_log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            print(json.dumps(run_log, ensure_ascii=False, indent=2))
            return completed.returncode

    (OUTDIR / "task-118-smoke-rerun-log.json").write_text(
        json.dumps(run_log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": "ok",
        "outdir": str(OUTDIR),
        "commands": len(COMMANDS),
        "log": str(OUTDIR / "task-118-smoke-rerun-log.json"),
        "summary": str(OUTDIR / "task-118-milestone-intent-summary.json"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
