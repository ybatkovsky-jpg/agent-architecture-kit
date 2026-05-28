from __future__ import annotations

import json
import io
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
TEST_ROOT = Path(tempfile.mkdtemp(prefix="tm-test-autonomy-false-arm-guard-"))
os.environ["TASK_MANAGER_ROOT"] = str(TEST_ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autonomy_state import load_autonomy_state
import task_manager as tm_mod

TM = WORKSPACE / "task-manager" / "task_manager.py"
TEST_ENV = dict(os.environ)


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run([sys.executable, str(TM), *args], cwd=str(WORKSPACE), env=TEST_ENV, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise AssertionError(f"command failed: {' '.join(args)}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def _age_task(task_id: int) -> None:
    import sqlite3
    con = sqlite3.connect(str(TEST_ROOT / "tasks.db"))
    try:
        con.execute("UPDATE tasks SET updated_at = '2026-05-20T00:00:00Z' WHERE id = ?", (task_id,))
        con.commit()
    finally:
        con.close()


def main() -> int:
    created = json.loads(_run("add", "tmp autonomy false arm guard", "--details", "requested vs armed proof", "--next-action", "Arm the continuation honestly").stdout)
    task_id = int(created["task_id"])
    _run("start", str(task_id), "--note", "Start false-arm guard proof", "--next-action", "Arm the continuation honestly")

    init_payload = json.loads(
        _run(
            "autonomy-init",
            str(task_id),
            "--note",
            "Autonomy requested before executor is armed",
            "--next-action",
            "Arm the continuation honestly",
            "--non-armed-reason",
            "operator_promised_autonomy_but_no_executor_armed",
        ).stdout
    )
    assert init_payload["autonomy_state"]["execution"]["autonomy_requested"] is True
    assert init_payload["autonomy_state"]["execution"]["autonomy_armed"] is False
    assert init_payload["autonomy_state"]["execution"]["non_armed_reason"] == "operator_promised_autonomy_but_no_executor_armed"

    shown = json.loads(_run("autonomy-show", str(task_id)).stdout)
    assert shown["execution"]["autonomy_requested"] is True
    assert shown["execution"]["autonomy_armed"] is False
    assert shown["execution_mode"] == "degraded_manual"
    assert shown["continuation"]["router_decision"] == "surface_to_user"
    assert shown["continuation"]["surface_reason"] == "autonomy_launch_failed"

    status = json.loads(_run("autonomy-status", str(task_id)).stdout)
    assert status["autonomous_status"] == "requested_not_armed"
    assert status["autonomy"]["execution_state"] == "requested_not_armed"
    assert status["autonomy"]["execution_mode"] == "degraded_manual"
    assert status["autonomy_claim_honest"] is False

    shown_task = json.loads(_run("show", str(task_id)).stdout)
    assert shown_task["autonomy"]["execution_state"] == "requested_not_armed"
    assert shown_task["autonomy"]["execution"]["non_armed_reason"] == "operator_promised_autonomy_but_no_executor_armed"

    _age_task(task_id)
    watchdog = json.loads(_run("watchdog", "--hours", "1").stdout)
    promised_entry = next(item for item in watchdog["promised_not_armed_autonomy"] if item["id"] == task_id)
    assert promised_entry["non_armed_reason"] == "operator_promised_autonomy_but_no_executor_armed"
    assert task_id not in {item["id"] for item in watchdog["resumable_autonomy"]}

    def _fake_cron_run(cmd, cwd=None, capture_output=True, text=True):
        assert cmd[:4] == ["openclaw", "cron", "add", "--json"]
        job_name = cmd[cmd.index("--name") + 1]
        return SimpleNamespace(returncode=0, stdout=json.dumps({"id": "job-false-arm-1", "name": job_name}), stderr="")

    with patch.object(tm_mod.subprocess, "run", side_effect=_fake_cron_run):
        buf = io.StringIO()
        with redirect_stdout(buf):
            tm_mod.autonomy_resume_task(SimpleNamespace(task_id=task_id, hours=1.0, cooldown_minutes=15, simulate_failure=False, failure_class="resume_failed"))
        resumed = json.loads(buf.getvalue())

    assert resumed["resumed"] is True
    resumed_state = load_autonomy_state(task_id)
    assert resumed_state["execution"]["autonomy_requested"] is True
    assert resumed_state["execution"]["autonomy_armed"] is True
    assert resumed_state["execution"]["execution_mode"] == "openclaw_cron_agent_turn"
    assert resumed_state["execution"]["anchor_kind"] == "openclaw_cron_agent_turn"
    assert resumed_state["execution"]["anchor_id"] == "job-false-arm-1"
    assert resumed_state["execution"]["non_armed_reason"] == ""

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
