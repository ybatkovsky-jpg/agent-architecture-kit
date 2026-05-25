#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
DEFAULT_OUTPUT = ROOT / "outputs" / "task-125-live-retrieval-smoke-unified"

STEPS = [
    {
        "id": "baseline_retrieval_smoke",
        "kind": "shell",
        "cmd": ["bash", str(ROOT / "scripts" / "run_retrieval_smoke.sh"), str(WORKSPACE)],
        "outputs": [
            "pkm-memory/artifacts/retrieval-smoke-memory-rollout-plan-2026-04-26.json",
            "pkm-memory/artifacts/retrieval-smoke-task-105-db-path-status-2026-04-26.json",
        ],
    },
    {
        "id": "precision_smoke",
        "kind": "shell",
        "cmd": ["bash", str(ROOT / "scripts" / "run_precision_smoke.sh")],
        "outputs": [
            "pkm-memory/outputs/smoke-db-retrieval-precision-2026-04-26/comparison-summary.json",
        ],
    },
    {
        "id": "milestone_rerun",
        "kind": "python",
        "cmd": [sys.executable, str(ROOT / "scripts" / "task118_smoke_rerun.py")],
        "outputs": [
            "pkm-memory/outputs/smoke-db-retrieval-milestone-pass-2026-04-26/task-118-milestone-intent-summary.json",
            "pkm-memory/outputs/smoke-db-retrieval-milestone-pass-2026-04-26/task-118-smoke-rerun-log.json",
        ],
    },
    {
        "id": "generic_milestone_rerun",
        "kind": "python",
        "cmd": [sys.executable, str(ROOT / "scripts" / "task119_generic_milestone_smoke.py")],
        "outputs": [
            "pkm-memory/outputs/smoke-db-retrieval-generic-milestone-pass-2026-04-26/task-119-smoke-rerun-log.json",
        ],
    },
]


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def run_step(step: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    proc = subprocess.run(step["cmd"], cwd=WORKSPACE, capture_output=True, text=True)
    log_path = run_dir / f"{step['id']}.log.json"
    payload = {
        "id": step["id"],
        "kind": step["kind"],
        "command": step["cmd"],
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "declared_outputs": step.get("outputs", []),
        "existing_outputs": [p for p in step.get("outputs", []) if (WORKSPACE / p).exists()],
    }
    log_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload["log"] = str(log_path.relative_to(WORKSPACE))
    return payload


def run_fixture_verifier(run_dir: Path, fixture_output_dir: Path) -> dict[str, Any]:
    fixture_output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "verify_retrieval_fixtures.py"),
        "--output-dir",
        str(fixture_output_dir),
    ]
    proc = subprocess.run(cmd, cwd=WORKSPACE, capture_output=True, text=True)
    log_path = run_dir / "fixture_verifier.log.json"
    payload = {
        "id": "fixture_verifier",
        "kind": "python",
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "declared_outputs": [
            str(fixture_output_dir.relative_to(WORKSPACE) / "verification-report.json")
        ],
        "existing_outputs": [
            str(fixture_output_dir.relative_to(WORKSPACE) / "verification-report.json")
        ] if (fixture_output_dir / "verification-report.json").exists() else [],
    }
    log_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload["log"] = str(log_path.relative_to(WORKSPACE))
    return payload


def write_latest_pointer(base_output: Path, run_dir: Path, manifest_path: Path) -> None:
    latest = {
        "latest_run": str(run_dir.relative_to(WORKSPACE)),
        "manifest": str(manifest_path.relative_to(WORKSPACE)),
        "updated_at": utc_stamp(),
    }
    (base_output / "latest.json").write_text(json.dumps(latest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_summary(run_dir: Path, manifest: dict[str, Any]) -> Path:
    lines = [
        "# Unified live retrieval smoke runner report",
        "",
        f"- status: **{manifest['status']}**",
        f"- started_at: `{manifest['started_at']}`",
        f"- finished_at: `{manifest['finished_at']}`",
        f"- run_dir: `{run_dir.relative_to(WORKSPACE)}`",
        "",
        "## Steps",
    ]
    for step in manifest["steps"]:
        state = "ok" if step["returncode"] == 0 else f"failed ({step['returncode']})"
        lines.extend([
            f"- `{step['id']}`: {state}",
            f"  - log: `{step['log']}`",
        ])
        if step.get("existing_outputs"):
            lines.append("  - outputs:")
            for output in step["existing_outputs"]:
                lines.append(f"    - `{output}`")
    summary_path = run_dir / "report.md"
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Unified wrapper for existing live retrieval smoke runners")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT), help="Stable base output dir for wrapper manifests/logs")
    parser.add_argument("--run-label", default=None, help="Optional run subdir name; defaults to utc timestamp")
    parser.add_argument("--skip-fixtures", action="store_true", help="Skip regression fixture verification")
    args = parser.parse_args()

    base_output = Path(args.output_dir).resolve()
    base_output.mkdir(parents=True, exist_ok=True)
    run_label = args.run_label or utc_stamp()
    run_dir = base_output / run_label
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "task": 125,
        "title": "Memory rollout: live retrieval smoke runner unification",
        "started_at": utc_stamp(),
        "base_output_dir": str(base_output.relative_to(WORKSPACE)),
        "run_dir": str(run_dir.relative_to(WORKSPACE)),
        "steps": [],
        "status": "running",
        "rerun_command": f"python3 pkm-memory/scripts/run_live_retrieval_smoke_unified.py --output-dir {base_output.relative_to(WORKSPACE)}",
    }

    for step in STEPS:
        result = run_step(step, run_dir)
        manifest["steps"].append(result)
        if result["returncode"] != 0:
            manifest["status"] = "failed"
            manifest["finished_at"] = utc_stamp()
            manifest_path = run_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            write_summary(run_dir, manifest)
            write_latest_pointer(base_output, run_dir, manifest_path)
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
            return result["returncode"]

    if not args.skip_fixtures:
        fixture_output_dir = run_dir / "fixtures"
        fixture_result = run_fixture_verifier(run_dir, fixture_output_dir)
        manifest["steps"].append(fixture_result)
        if fixture_result["returncode"] != 0:
            manifest["status"] = "failed"
            manifest["finished_at"] = utc_stamp()
            manifest_path = run_dir / "manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            write_summary(run_dir, manifest)
            write_latest_pointer(base_output, run_dir, manifest_path)
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
            return fixture_result["returncode"]

    manifest["status"] = "ok"
    manifest["finished_at"] = utc_stamp()
    manifest_path = run_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary_path = write_summary(run_dir, manifest)
    write_latest_pointer(base_output, run_dir, manifest_path)

    print(json.dumps({
        "status": manifest["status"],
        "run_dir": manifest["run_dir"],
        "manifest": str(manifest_path.relative_to(WORKSPACE)),
        "report": str(summary_path.relative_to(WORKSPACE)),
        "rerun_command": manifest["rerun_command"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
