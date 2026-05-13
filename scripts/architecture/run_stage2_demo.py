#!/usr/bin/env python3
"""Minimal local smoke/demo runner for Stage 2 architecture formalization scaffold."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "docs/learning/architecture-config.v0_1.example.yaml"
TRACE_DIR = ROOT / "evals/architecture/sampled_cases"
SCORE_REPORT = ROOT / "evals/architecture/score_reports/demo_score_report.json"
EMIT_SCRIPT = ROOT / "scripts/architecture/emit_trace.py"
SCORE_SCRIPT = ROOT / "scripts/architecture/score_trace.py"


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def latest_trace_file() -> Path:
    traces = sorted(TRACE_DIR.glob("trace-*.json"), key=lambda p: p.stat().st_mtime)
    if not traces:
        raise RuntimeError("No trace files generated")
    return traces[-1]


def main() -> int:
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    SCORE_REPORT.parent.mkdir(parents=True, exist_ok=True)

    run([sys.executable, str(EMIT_SCRIPT), str(TRACE_DIR), "--demo"])
    trace_path = latest_trace_file()
    run([sys.executable, str(SCORE_SCRIPT), str(CONFIG), str(trace_path), "--output", str(SCORE_REPORT)])

    report = json.loads(SCORE_REPORT.read_text(encoding="utf-8"))
    summary = {
        "trace_path": str(trace_path.relative_to(ROOT)),
        "score_report_path": str(SCORE_REPORT.relative_to(ROOT)),
        "valid_score": report["valid_score"],
        "hard_fail": report["hard_fail"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
