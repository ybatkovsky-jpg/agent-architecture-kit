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
TEST_ROOT = Path(tempfile.mkdtemp(prefix="tm-test-active-front-hygiene-"))
os.environ["TASK_MANAGER_ROOT"] = str(TEST_ROOT)
TEST_ENV = dict(os.environ)


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run([sys.executable, str(TM), *args], cwd=str(WORKSPACE), env=TEST_ENV, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise AssertionError(f"command failed: {' '.join(args)}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def main() -> int:
    created = json.loads(_run("add", "tmp active front hygiene", "--details", "proof for active-front cleanup", "--next-action", "Move through lifecycle").stdout)
    task_id = int(created["task_id"])

    _run("start", str(task_id), "--note", "Start active-front hygiene proof", "--next-action", "Claim active front")
    claimed = json.loads(_run("claim-active", str(task_id), "--priority-band", "P2", "--priority-reason", "test focus").stdout)
    assert claimed["active_front"]["task_id"] == task_id

    waiting = json.loads(_run("wait", str(task_id), "--note", "Pause task", "--blocked-reason", "waiting proof", "--next-action", "Resume later").stdout)
    waiting_payload = waiting["judge_feedback"]["completion_gate"] if waiting.get("judge_feedback") else None
    shown_after_wait = json.loads(_run("show-active").stdout)
    assert shown_after_wait["active_front"] is None, shown_after_wait
    assert shown_after_wait.get("last_cleared_reason") == "status_transition:waiting_user"

    _run("reopen", str(task_id), "--note", "Reopen for completion", "--next-action", "Return to in_progress")
    _run("start", str(task_id), "--note", "Restart task", "--next-action", "Claim again")
    claimed_again = json.loads(_run("claim-active", str(task_id), "--priority-band", "P2", "--priority-reason", "test focus again").stdout)
    assert claimed_again["active_front"]["task_id"] == task_id

    note = (
        "CLAIM: active-front cleanup on non-in_progress status transitions is implemented.\n\n"
        "EVIDENCE:\n"
        "- task-manager/task_manager.py clears active_front_state.json when the claimed task leaves in_progress.\n"
        "- task-manager/test_active_front_hygiene.py proves claim-active -> wait clears the stale front and allows clean reclaim.\n\n"
        "VERIFICATION:\n"
        "- python3 task-manager/test_active_front_hygiene.py\n\n"
        "ANCHOR:\n"
        "- task-manager/task_manager.py\n"
        "- task-manager/test_active_front_hygiene.py"
    )
    _run("review", str(task_id), "--note", note, "--next-action", "Close after review")
    shown_after_review = json.loads(_run("show-active").stdout)
    assert shown_after_review["active_front"] is None, shown_after_review
    assert shown_after_review.get("last_cleared_reason") == "status_transition:review"

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
