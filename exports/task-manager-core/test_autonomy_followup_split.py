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
TEST_ROOT = Path(tempfile.mkdtemp(prefix="tm-test-autonomy-followup-split-"))
os.environ["TASK_MANAGER_ROOT"] = str(TEST_ROOT)
TEST_ENV = dict(os.environ)


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run([sys.executable, str(TM), *args], cwd=str(WORKSPACE), env=TEST_ENV, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise AssertionError(f"command failed: {' '.join(args)}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def main() -> int:
    created = json.loads(_run("add", "tmp followup split parent", "--details", "follow-up split proof", "--next-action", "Close parent scope").stdout)
    task_id = int(created["task_id"])
    _run("start", str(task_id), "--note", "Start follow-up split proof", "--next-action", "Close parent scope")
    _run(
        "autonomy-init",
        str(task_id),
        "--note",
        "Autonomous closure split entered",
        "--next-action",
        "Close parent scope",
        "--arm",
        "yes",
        "--execution-mode",
        "current_run",
        "--anchor-kind",
        "current_run",
        "--anchor-id",
        f"task-{task_id}-run",
    )

    shown = json.loads(_run("autonomy-show", str(task_id)).stdout)
    shown["closure_loop"]["execution_stage"] = "closing"
    shown["closure_loop"]["slice_done"] = True
    shown["closure_loop"]["closure_required"] = True
    (TEST_ROOT / "runtime" / "autonomy" / f"task-{task_id}.json").write_text(json.dumps(shown, ensure_ascii=False, indent=2), encoding="utf-8")

    with tempfile.TemporaryDirectory() as tmp:
        payload = Path(tmp) / "split.json"
        payload.write_text(json.dumps({
            "status": "review_ready",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "Parent can close but residual work should be separated",
            "parent_goal_open": True,
            "frontier_remaining": True,
            "frontier_known": True,
            "frontier_next_action": "Implement the residual split scope",
            "done_criteria_met": False,
            "artifact_refs": ["task-manager/task_manager.py"],
        }), encoding="utf-8")
        routed = json.loads(_run("autonomy-route", str(task_id), "--child-result-file", str(payload)).stdout)

    assert routed["routing"]["router_decision"] == "split_followup_task"
    followup = routed["followup_task"]
    assert followup and int(followup["task_id"]) > 0

    parent = json.loads(_run("show", str(task_id)).stdout)
    child_id = int(followup["task_id"])
    child = json.loads(_run("show", str(child_id)).stdout)

    assert child["task"]["parent_task_id"] == task_id
    assert child["task"]["status"] == "open"
    assert child["task"]["next_action"] == "Implement the residual split scope"
    assert f"task:{child_id}" in json.loads(parent["task"]["context_json"])["links"]
    assert f"task:{task_id}" in json.loads(child["task"]["context_json"])["links"]
    assert any(event["event_type"] == "followup_spawned" for event in parent["events"])
    assert any(event["event_type"] == "spawned_followup" for event in child["events"])

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
