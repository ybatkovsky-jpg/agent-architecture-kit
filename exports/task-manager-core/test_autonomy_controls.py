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
TEST_ROOT = Path(tempfile.mkdtemp(prefix="tm-test-autonomy-controls-"))
os.environ["TASK_MANAGER_ROOT"] = str(TEST_ROOT)
TEST_ENV = dict(os.environ)


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run([sys.executable, str(TM), *args], cwd=str(WORKSPACE), env=TEST_ENV, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise AssertionError(f"command failed: {' '.join(args)}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def main() -> int:
    created = json.loads(_run("add", "tmp autonomy controls", "--details", "autonomy controls proof", "--next-action", "Continue operator-visible chain").stdout)
    task_id = int(created["task_id"])
    _run("start", str(task_id), "--note", "Start controls proof", "--next-action", "Continue operator-visible chain")

    enabled = json.loads(_run("autonomy-enable", str(task_id), "--note", "Enable autonomy for controls proof", "--next-action", "Continue operator-visible chain").stdout)
    assert enabled["autonomy_state"]["autonomy_mode"] is True
    assert enabled["autonomy_state"]["watchdog"]["eligible_for_resume"] is True
    assert enabled["autonomy_state"]["execution"]["autonomy_requested"] is True
    assert enabled["autonomy_state"]["execution"]["autonomy_armed"] is False
    assert enabled["autonomy_state"]["execution"]["non_armed_reason"] in {"autonomy_requested_without_live_anchor", ""}

    status = json.loads(_run("autonomy-status", str(task_id)).stdout)
    assert status["task_id"] == task_id
    assert status["autonomy"]["autonomy_mode"] is True
    assert status["autonomy"]["execution"]["autonomy_requested"] is True
    assert status["autonomy"]["execution"]["autonomy_armed"] is False
    assert status["autonomy"]["execution_state"] == "requested_not_armed"
    assert status["autonomous_status"] == "requested_not_armed"
    assert status["autonomy_claim_honest"] is False
    assert status["autonomy"]["continuation"]["next_action"] == "Continue operator-visible chain"
    assert status["process_complete"] is False
    assert status["goal_complete"] is False
    assert "execution_state" in status
    assert "resume_reason" in status
    assert "lineage" in status

    rejected = _run(
        "autonomy-stop",
        str(task_id),
        "--note",
        "Stop autonomy for controls proof",
        "--next-action",
        "Return to manual handling",
        check=False,
    )
    assert rejected.returncode != 0
    assert "manual_fallback_forbidden=true" in (rejected.stderr or rejected.stdout)

    stopped = json.loads(
        _run(
            "autonomy-stop",
            str(task_id),
            "--note",
            "Stop autonomy for controls proof",
            "--next-action",
            "Return to manual handling",
            "--allow-manual-fallback",
            "yes",
        ).stdout
    )
    assert stopped["autonomy_state"]["autonomy_mode"] is False
    assert stopped["autonomy_state"]["mode"] == "manual"
    assert stopped["autonomy_state"]["watchdog"]["eligible_for_resume"] is False
    assert stopped["autonomy_state"]["execution"]["autonomy_requested"] is False
    assert stopped["autonomy_state"]["execution"]["autonomy_armed"] is False
    assert stopped["autonomy_state"]["continuation"]["next_action"] == "Return to manual handling"
    assert stopped["autonomy_state"]["active_child"]["kind"] == "none"

    shown = json.loads(_run("autonomy-show", str(task_id)).stdout)
    assert shown["autonomy_mode"] is False
    assert shown["watchdog"]["eligible_for_resume"] is False
    assert shown["execution"]["autonomy_requested"] is False
    assert shown["execution"]["autonomy_armed"] is False
    assert shown["continuation"]["decision_reason"] == "Stop autonomy for controls proof"

    shown_task = json.loads(_run("show", str(task_id)).stdout)
    assert shown_task["task"]["status"] == "in_progress"
    assert shown_task["autonomy"]["autonomy_mode"] is False
    assert shown_task["autonomy"]["mode"] == "manual"
    assert shown_task["autonomy"]["execution_state"] == "manual"

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
