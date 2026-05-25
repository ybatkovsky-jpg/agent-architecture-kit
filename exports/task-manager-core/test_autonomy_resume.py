from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
TEST_ROOT = Path(tempfile.mkdtemp(prefix="tm-test-autonomy-resume-"))
os.environ["TASK_MANAGER_ROOT"] = str(TEST_ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autonomy_state import load_autonomy_state, save_autonomy_state
import task_manager as tm_mod

TM = WORKSPACE / "task-manager" / "task_manager.py"
TEST_ENV = dict(os.environ)


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run([sys.executable, str(TM), *args], cwd=str(WORKSPACE), env=TEST_ENV, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise AssertionError(f"command failed: {' '.join(args)}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def _create_autonomous_task(title: str, next_action: str) -> int:
    created = json.loads(_run("add", title, "--details", "autonomy resume proof", "--next-action", next_action).stdout)
    task_id = int(created["task_id"])
    _run("start", str(task_id), "--note", "Starting resume proof slice", "--next-action", next_action)
    _run(
        "autonomy-init",
        str(task_id),
        "--note",
        "Autonomous execution entered",
        "--next-action",
        next_action,
        "--arm",
        "yes",
        "--execution-mode",
        "current_run",
        "--anchor-kind",
        "current_run",
        "--anchor-id",
        f"task-{task_id}-current-run",
    )
    return task_id


def _age_task(task_id: int) -> None:
    import sqlite3
    con = sqlite3.connect(str(TEST_ROOT / "tasks.db"))
    try:
        con.execute("UPDATE tasks SET updated_at = '2026-05-20T00:00:00Z' WHERE id = ?", (task_id,))
        con.commit()
    finally:
        con.close()


def main() -> int:
    task_id = _create_autonomous_task("tmp autonomy thin resume", "Resume bounded chain")
    state = load_autonomy_state(task_id)
    state["continuation"] = {
        "router_decision": "resume_later",
        "decision_reason": "Stale autonomous task should resume internally.",
        "surface_reason": "",
        "next_action": "Resume bounded chain",
        "awaiting_user": False,
        "approval_needed": False,
        "risk_alert": False,
        "done_criteria_met": False,
    }
    state["watchdog"]["eligible_for_resume"] = True
    save_autonomy_state(task_id, state)
    _age_task(task_id)

    watchdog_before = json.loads(_run("watchdog", "--hours", "1").stdout)
    resume_entry = next(item for item in watchdog_before["resumable_autonomy"] if item["id"] == task_id)
    assert resume_entry["resume_command"] == f"python3 task-manager/task_manager.py autonomy-resume {task_id}"

    def _fake_cron_run(cmd, cwd=None, capture_output=True, text=True):
        assert cmd[:4] == ["openclaw", "cron", "add", "--json"]
        job_name = cmd[cmd.index("--name") + 1]
        return SimpleNamespace(returncode=0, stdout=json.dumps({"id": f"job-{task_id}", "name": job_name}), stderr="")

    with patch.object(tm_mod.subprocess, "run", side_effect=_fake_cron_run):
        resumed = tm_mod.autonomy_resume_task_result(SimpleNamespace(
            task_id=task_id,
            hours=1.0,
            cooldown_minutes=15,
            simulate_failure=False,
            failure_class="resume_failed",
        ))
    assert resumed["resumed"] is True
    assert resumed["resume_basis"] == "router_decision=resume_later"
    assert "handoffs/autonomy-task-" in resumed["handoff_path"]
    assert resumed["spawn"]["job_id"]
    assert resumed["spawn"]["job_name"].startswith(f"autonomy-resume-{task_id}-")
    assert resumed["spawn"]["when"] == "1m"
    assert resumed["spawn"]["command"][:6] == ["openclaw", "cron", "add", "--json", "--name", resumed["spawn"]["job_name"]]
    handoff_path = Path(resumed["handoff_path"])
    if not handoff_path.is_absolute():
        handoff_path = (TEST_ROOT.parent / resumed["handoff_path"]).resolve()
    assert handoff_path.exists()
    handoff_text = handoff_path.read_text(encoding="utf-8")
    assert f"Task #{task_id}" in handoff_text
    assert "Resume basis: router_decision=resume_later" in handoff_text
    assert "Next action: Resume bounded chain" in handoff_text
    assert f"Task #{task_id}" in resumed["spawn"]["message"]
    assert "Resume bounded chain" in resumed["spawn"]["message"]
    shown = json.loads(_run("autonomy-show", str(task_id)).stdout)
    assert shown["continuation"]["router_decision"] == "continue_now"
    assert shown["watchdog"]["cooldown_until"]
    assert shown["active_child"]["kind"] == "openclaw_cron_agent_turn"
    assert shown["active_child"]["id"] == resumed["spawn"]["job_id"]

    watchdog_after = json.loads(_run("watchdog", "--hours", "1").stdout)
    resumable_ids_after = {item["id"] for item in watchdog_after["resumable_autonomy"]}
    assert task_id not in resumable_ids_after

    anti_silence_id = _create_autonomous_task("tmp autonomy thin resume anti silence", "Advance long active slice")
    anti_silence_state = load_autonomy_state(anti_silence_id)
    anti_silence_state["continuation"] = {
        "router_decision": "continue_now",
        "decision_reason": "",
        "surface_reason": "",
        "next_action": "Advance long active slice",
        "awaiting_user": False,
        "approval_needed": False,
        "risk_alert": False,
        "done_criteria_met": False,
        "parent_goal_open": True,
        "frontier_remaining": True,
    }
    anti_silence_state["watchdog"]["eligible_for_resume"] = True
    anti_silence_state["watchdog"]["current_mode"] = "execution"
    anti_silence_state["watchdog"]["step_goal"] = "Advance long active slice"
    anti_silence_state["watchdog"]["anti_silence_due_at"] = "2026-05-20T00:00:00Z"
    save_autonomy_state(anti_silence_id, anti_silence_state)
    _age_task(anti_silence_id)

    watchdog_anti_silence = json.loads(_run("watchdog", "--hours", "1").stdout)
    anti_silence_excluded = next(item for item in watchdog_anti_silence["excluded_autonomy"] if item["id"] == anti_silence_id)
    assert anti_silence_excluded["forced_status_ping_required"] is True
    assert anti_silence_excluded["eligible_for_resume"] is False
    assert anti_silence_excluded["forced_status_ping"]["reason"] == "long_active_slice_without_visible_outcome"

    anti_silence_shown = json.loads(_run("autonomy-show", str(anti_silence_id)).stdout)
    assert anti_silence_shown["watchdog"]["forced_reroute_reason"] == "long_active_slice_without_visible_outcome"
    anti_silence_status = json.loads(_run("autonomy-status", str(anti_silence_id)).stdout)
    assert anti_silence_status["forced_status_ping"]["reason"] == "long_active_slice_without_visible_outcome"

    failing_id = _create_autonomous_task("tmp autonomy thin resume fail", "Retry bounded chain")
    failing_state = load_autonomy_state(failing_id)
    failing_state["continuation"] = {
        "router_decision": "resume_later",
        "decision_reason": "Retry path proof.",
        "surface_reason": "",
        "next_action": "Retry bounded chain",
        "awaiting_user": False,
        "approval_needed": False,
        "risk_alert": False,
        "done_criteria_met": False,
    }
    failing_state["watchdog"]["eligible_for_resume"] = True
    save_autonomy_state(failing_id, failing_state)
    _age_task(failing_id)

    for expected_retry in (1, 2, 3):
        failed = tm_mod.autonomy_resume_task_result(SimpleNamespace(
            task_id=failing_id,
            hours=1.0,
            cooldown_minutes=1,
            simulate_failure=True,
            failure_class="unit_test_failure",
        ))
        assert failed["resumed"] is False
        assert failed["autonomy_state"]["watchdog"]["retry_count"] == expected_retry
        tmp_state = load_autonomy_state(failing_id)
        tmp_state["watchdog"]["cooldown_until"] = ""
        save_autonomy_state(failing_id, tmp_state)
        _age_task(failing_id)

    watchdog_fail = json.loads(_run("watchdog", "--hours", "1").stdout)
    failing_ids = {item["id"] for item in watchdog_fail["resumable_autonomy"]}
    assert failing_id not in failing_ids
    excluded_entry = next(item for item in watchdog_fail["excluded_autonomy"] if item["id"] == failing_id)
    assert excluded_entry["eligible_for_resume"] is True

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
