from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TM = WORKSPACE / "task-manager" / "task_manager.py"
TEST_ROOT = Path(tempfile.mkdtemp(prefix="tm-test-autonomy-closure-loop-"))
os.environ["TASK_MANAGER_ROOT"] = str(TEST_ROOT)
TEST_ENV = dict(os.environ)


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run([sys.executable, str(TM), *args], cwd=str(WORKSPACE), env=TEST_ENV, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise AssertionError(f"command failed: {' '.join(args)}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def main() -> int:
    created = json.loads(_run("add", "tmp closure loop", "--details", "closure loop proof", "--next-action", "Implement bounded slice").stdout)
    task_id = int(created["task_id"])
    _run("start", str(task_id), "--note", "Start closure loop proof", "--next-action", "Implement bounded slice")
    _run(
        "autonomy-init",
        str(task_id),
        "--note",
        "Autonomous closure loop entered",
        "--next-action",
        "Implement bounded slice",
        "--arm",
        "yes",
        "--execution-mode",
        "current_run",
        "--anchor-kind",
        "current_run",
        "--anchor-id",
        f"task-{task_id}-run",
    )

    status = json.loads(_run("autonomy-status", str(task_id)).stdout)
    assert status["autonomy"]["closure_loop"]["execution_stage"] == "implementing"
    assert status["closure_loop_pending"] is True

    with tempfile.TemporaryDirectory() as tmp:
        payload = Path(tmp) / "slice.json"
        payload.write_text(json.dumps({
            "status": "done",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "Bounded slice implemented; follow-up frontier is explicit",
            "frontier_next_action": "Run targeted verification slice",
            "parent_goal_open": True,
            "frontier_known": True,
            "done_criteria_met": True,
            "artifact_refs": ["task-manager/autonomy_state.py"],
            "verification_refs": ["python3 test_autonomy_closure_loop.py"],
        }), encoding="utf-8")
        routed = json.loads(_run("autonomy-route", str(task_id), "--child-result-file", str(payload)).stdout)
    assert routed["routing"]["router_decision"] == "schedule_next_slice"
    saved = routed["autonomy_state"]
    assert saved["closure_loop"]["slice_done"] is True
    assert saved["closure_loop"]["next_slice_required"] is True
    assert saved["closure_loop"]["next_slice_scope"] == "Run targeted verification slice"
    assert saved["closure_loop"]["last_terminality_result"] == "non_terminal"

    shown = json.loads(_run("autonomy-status", str(task_id)).stdout)
    assert shown["terminality_decision_required"] is False
    assert shown["next_slice_missing"] is False
    assert shown["autonomy"]["closure_loop"]["next_slice_scope"] == "Run targeted verification slice"

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
