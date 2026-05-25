#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

OUTDIR = Path("pkm-memory/outputs/smoke-db-retrieval-generic-milestone-pass-2026-04-26")
OUTDIR.mkdir(parents=True, exist_ok=True)

COMMANDS = [
    ["python3", "pkm-memory/retrieve_memory.py", "activation milestone", "--mode", "psql", "--env-file", "pkm-memory/config/memory.env", "--output", str(OUTDIR / "query-activation-milestone-db.json")],
    ["python3", "pkm-memory/retrieve_memory.py", "activation milestone", "--mode", "local", "--output", str(OUTDIR / "query-activation-milestone-local.json")],
    ["python3", "pkm-memory/retrieve_memory.py", "postgres activation milestone", "--mode", "psql", "--env-file", "pkm-memory/config/memory.env", "--output", str(OUTDIR / "query-postgres-activation-milestone-db.json")],
    ["python3", "pkm-memory/retrieve_memory.py", "postgres activation", "--mode", "psql", "--env-file", "pkm-memory/config/memory.env", "--output", str(OUTDIR / "query-postgres-activation-db.json")],
]

results = []
for cmd in COMMANDS:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    results.append({
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    })
    if proc.returncode != 0:
        break

(OUTDIR / "task-119-smoke-rerun-log.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

failed = next((r for r in results if r["returncode"] != 0), None)
if failed:
    raise SystemExit(failed["returncode"])
