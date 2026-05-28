from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
MANIFEST = ROOT / "artifacts" / "task-780-replay-scenarios-2026-05-27.json"
HARNESS = ROOT / "replay_scenario_harness.py"


def main() -> int:
    proc = subprocess.run(
        [sys.executable, str(HARNESS), str(MANIFEST)],
        cwd=str(WORKSPACE),
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(f"Harness failed\nstdout={proc.stdout}\nstderr={proc.stderr}")
    payload = json.loads(proc.stdout)
    assert payload["manifest_version"] == "replay_scenario_manifest.v1"
    assert payload["scenario_count"] >= 4
    assert payload["all_passed"] is True
    classes = {item["scenario_class"] for item in payload["results"]}
    assert {"normal_bounded_execution", "degraded_delivery_or_recovery", "false_closure_prevention", "delegated_interruption_resume"}.issubset(classes)
    assert all(item["passed"] for item in payload["results"])
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
