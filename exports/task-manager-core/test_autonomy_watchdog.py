from __future__ import annotations

import json
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
TEST_ROOT = Path(tempfile.mkdtemp(prefix="tm-test-autonomy-watchdog-"))
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
    created = json.loads(_run("add", title, "--details", "autonomy watchdog proof", "--next-action", next_action).stdout)
    task_id = int(created["task_id"])
    _run("start", str(task_id), "--note", "Starting watchdog proof slice", "--next-action", next_action)
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
    _run("note", str(task_id), "--note", "Backdate watchdog proof task", "--next-action", load_autonomy_state(task_id)["continuation"].get("next_action") or "Continue")
    import sqlite3
    con = sqlite3.connect(str(TEST_ROOT / "tasks.db"))
    try:
        con.execute("UPDATE tasks SET updated_at = '2026-05-20T00:00:00Z' WHERE id = ?", (task_id,))
        con.commit()
    finally:
        con.close()


def main() -> int:
    promised_not_armed_id = _create_autonomous_task("tmp autonomy watchdog promised not armed", "Arm the continuation honestly")
    promised_state = load_autonomy_state(promised_not_armed_id)
    promised_state["execution"]["autonomy_requested"] = True
    promised_state["execution"]["autonomy_armed"] = False
    promised_state["execution"]["execution_mode"] = "none"
    promised_state["execution"]["anchor_kind"] = ""
    promised_state["execution"]["anchor_id"] = ""
    promised_state["execution"]["non_armed_reason"] = "operator_promised_autonomy_but_no_executor_armed"
    save_autonomy_state(promised_not_armed_id, promised_state)
    _age_task(promised_not_armed_id)

    stale_resume_id = _create_autonomous_task("tmp autonomy watchdog resumable", "Resume stale chain")
    stale_state = load_autonomy_state(stale_resume_id)
    stale_state["last_child_result"] = {
        "status": "none",
        "summary": "Stale chain pending internal resume",
        "artifact_refs": ["task-manager/test_autonomy_watchdog.py"],
        "returned_at": "",
    }
    stale_state["continuation"] = {
        "router_decision": "resume_later",
        "decision_reason": "Autonomous task is stale but still resumable; schedule another bounded internal pass.",
        "surface_reason": "",
        "next_action": "Resume stale chain",
        "awaiting_user": False,
        "approval_needed": False,
        "risk_alert": False,
        "done_criteria_met": False,
    }
    stale_state["watchdog"]["eligible_for_resume"] = True
    save_autonomy_state(stale_resume_id, stale_state)
    _age_task(stale_resume_id)

    stale_continue_id = _create_autonomous_task("tmp autonomy watchdog continue", "Continue bounded slice")
    with tempfile.TemporaryDirectory() as tmp:
        payload = Path(tmp) / "continue.json"
        payload.write_text(json.dumps({
            "status": "review_ready",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "Checkpoint only",
            "next_action": "Continue bounded slice",
            "done_criteria_met": False,
            "artifact_refs": ["task-manager/test_autonomy_watchdog.py"],
        }), encoding="utf-8")
        routed = json.loads(_run("autonomy-route", str(stale_continue_id), "--child-result-file", str(payload)).stdout)
        assert routed["routing"]["router_decision"] == "schedule_next_slice"
    _age_task(stale_continue_id)

    closure_gap_id = _create_autonomous_task("tmp autonomy watchdog closure gap", "Decide explicit next slice")
    closure_gap_state = load_autonomy_state(closure_gap_id)
    closure_gap_state["last_child_result"] = {
        "status": "review_ready",
        "summary": "Useful progress exists but no closure routing was recorded",
        "artifact_refs": ["task-manager/autonomy_router.py"],
        "verification_refs": ["python3 test_autonomy_watchdog.py"],
        "outcome_class": "frontier_progress",
        "payload_class": "canonical_result",
        "returned_at": "",
    }
    closure_gap_state["closure_loop"] = {
        "execution_stage": "verifying",
        "slice_goal": "Run closure audit",
        "slice_done": True,
        "closure_required": True,
        "followup_split_needed": False,
        "next_slice_required": True,
        "next_slice_reason": "Need next bounded slice but none was recorded",
        "next_slice_scope": "",
        "last_terminality_check": "",
        "last_terminality_result": "non_terminal",
    }
    save_autonomy_state(closure_gap_id, closure_gap_state)
    _age_task(closure_gap_id)

    anti_silence_id = _create_autonomous_task("tmp autonomy watchdog anti silence", "Keep advancing bounded slice")
    anti_silence_state = load_autonomy_state(anti_silence_id)
    anti_silence_state["continuation"] = {
        "router_decision": "continue_now",
        "decision_reason": "Still working the current bounded slice.",
        "surface_reason": "",
        "next_action": "Keep advancing bounded slice",
        "awaiting_user": False,
        "approval_needed": False,
        "risk_alert": False,
        "done_criteria_met": False,
        "parent_goal_open": True,
        "frontier_known": True,
        "frontier_remaining": True,
    }
    anti_silence_state["watchdog"]["anti_silence_due_at"] = "2026-05-20T00:00:00Z"
    anti_silence_state["watchdog"]["last_progress_at"] = "2026-05-19T23:00:00Z"
    save_autonomy_state(anti_silence_id, anti_silence_state)
    _age_task(anti_silence_id)
    anti_silence_state = load_autonomy_state(anti_silence_id)
    anti_silence_state["watchdog"]["anti_silence_due_at"] = "2026-05-20T00:00:00Z"
    anti_silence_state["watchdog"]["last_progress_at"] = "2026-05-19T23:00:00Z"
    save_autonomy_state(anti_silence_id, anti_silence_state)

    integrity_due_id = _create_autonomous_task("tmp autonomy watchdog integrity due", "Surface bounded execution proof")
    integrity_due_state = load_autonomy_state(integrity_due_id)
    integrity_due_state["integrity"]["surface_required"] = True
    integrity_due_state["integrity"]["surface_due_at"] = "2026-05-20T00:00:00Z"
    integrity_due_state["integrity"]["stale_in_progress_reason"] = "significant_progress_not_surfaced"
    integrity_due_state["integrity"]["orphan_evidence_status"] = "orphan_evidence_suspected"
    integrity_due_state["integrity"]["last_surface_at"] = "2026-05-19T23:00:00Z"
    integrity_due_state["watchdog"]["current_mode"] = "implementation"
    integrity_due_state["watchdog"]["step_goal"] = "Surface bounded execution proof"
    save_autonomy_state(integrity_due_id, integrity_due_state)
    _age_task(integrity_due_id)
    integrity_due_state = load_autonomy_state(integrity_due_id)
    integrity_due_state["integrity"]["surface_required"] = True
    integrity_due_state["integrity"]["surface_due_at"] = "2026-05-20T00:00:00Z"
    integrity_due_state["integrity"]["stale_in_progress_reason"] = "significant_progress_not_surfaced"
    integrity_due_state["integrity"]["orphan_evidence_status"] = "orphan_evidence_suspected"
    integrity_due_state["integrity"]["last_surface_at"] = "2026-05-19T23:00:00Z"
    integrity_due_state["watchdog"]["current_mode"] = "implementation"
    integrity_due_state["watchdog"]["step_goal"] = "Surface bounded execution proof"
    save_autonomy_state(integrity_due_id, integrity_due_state)

    final_surface_id = _create_autonomous_task("tmp autonomy watchdog final result not surfaced", "Surface final result honestly")
    final_surface_state = load_autonomy_state(final_surface_id)
    final_surface_state["continuation"] = {
        "router_decision": "surface_to_user",
        "decision_reason": "Parent closure criteria are satisfied.",
        "surface_reason": "done",
        "next_action": "Surface final result honestly",
        "awaiting_user": False,
        "approval_needed": False,
        "risk_alert": False,
        "done_criteria_met": True,
        "parent_goal_complete": True,
        "parent_goal_open": False,
        "frontier_known": False,
        "frontier_remaining": False,
        "frontier_exhausted": True,
    }
    final_surface_state["last_child_result"] = {
        "status": "done",
        "summary": "Parent DoD satisfied but final user-facing surfacing has not been completed yet",
        "artifact_refs": ["task-manager/test_autonomy_watchdog.py"],
        "verification_refs": ["python3 test_autonomy_watchdog.py"],
        "outcome_class": "terminal_done",
        "payload_class": "canonical_result",
        "returned_at": "",
    }
    final_surface_state["watchdog"]["final_surface_required"] = True
    final_surface_state["watchdog"]["forced_reroute_reason"] = "final_result_not_surfaced"
    final_surface_state["watchdog"]["anti_silence_due_at"] = "2026-05-20T00:00:00Z"
    save_autonomy_state(final_surface_id, final_surface_state)
    _age_task(final_surface_id)
    final_surface_state = load_autonomy_state(final_surface_id)
    final_surface_state["continuation"] = {
        "router_decision": "surface_to_user",
        "decision_reason": "Parent closure criteria are satisfied.",
        "surface_reason": "done",
        "next_action": "Surface final result honestly",
        "awaiting_user": False,
        "approval_needed": False,
        "risk_alert": False,
        "done_criteria_met": True,
        "parent_goal_complete": True,
        "parent_goal_open": False,
        "frontier_known": False,
        "frontier_remaining": False,
        "frontier_exhausted": True,
    }
    final_surface_state["watchdog"]["final_surface_required"] = True
    final_surface_state["watchdog"]["forced_reroute_reason"] = "final_result_not_surfaced"
    final_surface_state["watchdog"]["anti_silence_due_at"] = "2026-05-20T00:00:00Z"
    save_autonomy_state(final_surface_id, final_surface_state)

    missing_step_id = _create_autonomous_task("tmp autonomy watchdog missing bounded step", "Recover explicit bounded step")
    missing_step_state = load_autonomy_state(missing_step_id)
    missing_step_state["continuation"] = {
        "router_decision": "continue_now",
        "decision_reason": "Still working but bounded-step contract was not preserved.",
        "surface_reason": "",
        "next_action": "Recover explicit bounded step",
        "awaiting_user": False,
        "approval_needed": False,
        "risk_alert": False,
        "done_criteria_met": False,
        "parent_goal_open": True,
        "frontier_known": True,
        "frontier_remaining": True,
    }
    missing_step_state["watchdog"]["anti_silence_due_at"] = "2026-05-20T00:00:00Z"
    missing_step_state["watchdog"]["last_progress_at"] = "2026-05-19T23:00:00Z"
    missing_step_state["watchdog"]["current_mode"] = ""
    missing_step_state["watchdog"]["step_goal"] = ""
    save_autonomy_state(missing_step_id, missing_step_state)
    _age_task(missing_step_id)
    missing_step_state = load_autonomy_state(missing_step_id)
    missing_step_state["watchdog"]["anti_silence_due_at"] = "2026-05-20T00:00:00Z"
    missing_step_state["watchdog"]["last_progress_at"] = "2026-05-19T23:00:00Z"
    missing_step_state["watchdog"]["current_mode"] = ""
    missing_step_state["watchdog"]["step_goal"] = ""
    save_autonomy_state(missing_step_id, missing_step_state)

    waiting_id = _create_autonomous_task("tmp autonomy watchdog awaiting user", "Wait for approval")
    with tempfile.TemporaryDirectory() as tmp:
        payload = Path(tmp) / "waiting.json"
        payload.write_text(json.dumps({
            "status": "blocked",
            "outcome_class": "approval_needed",
            "payload_class": "canonical_result",
            "blocked_reason": "Need exact user approval",
            "waiting_is_external": True,
            "approval_needed": True,
            "artifact_refs": ["task-manager/test_autonomy_watchdog.py"],
        }), encoding="utf-8")
        routed = json.loads(_run("autonomy-route", str(waiting_id), "--child-result-file", str(payload)).stdout)
        assert routed["routing"]["router_decision"] == "surface_to_user"
    _run("wait", str(waiting_id), "--blocked-reason", "Need exact user approval", "--note", "Allowed waiting after approval-needed route", "--next-action", "Wait for approval")
    _age_task(waiting_id)

    watchdog = json.loads(_run("watchdog", "--hours", "1").stdout)
    resumable_ids = {item["id"] for item in watchdog["resumable_autonomy"]}
    excluded_ids = {item["id"] for item in watchdog["excluded_autonomy"]}
    promised_ids = {item["id"] for item in watchdog["promised_not_armed_autonomy"]}
    closure_gap_ids = {item["id"] for item in watchdog["progressed_not_closure_routed"]}
    anti_silence_ids = {item["id"] for item in watchdog["anti_silence_due"]}
    integrity_due_ids = {item["id"] for item in watchdog["integrity_surface_due"]}

    assert stale_resume_id in resumable_ids
    assert stale_continue_id in resumable_ids
    assert promised_not_armed_id not in resumable_ids
    assert promised_not_armed_id in promised_ids
    assert waiting_id not in resumable_ids
    assert waiting_id in excluded_ids
    assert closure_gap_id in closure_gap_ids
    assert anti_silence_id in anti_silence_ids
    assert missing_step_id in anti_silence_ids
    assert integrity_due_id in integrity_due_ids
    assert final_surface_id in excluded_ids

    promised_entry = next(item for item in watchdog["promised_not_armed_autonomy"] if item["id"] == promised_not_armed_id)
    assert promised_entry["non_armed_reason"] == "operator_promised_autonomy_but_no_executor_armed"
    assert f"autonomy-enable {promised_not_armed_id}" in promised_entry["suggested_fix_command"]

    resume_entry = next(item for item in watchdog["resumable_autonomy"] if item["id"] == stale_resume_id)
    assert resume_entry["router_decision"] == "resume_later"
    assert resume_entry["resume_basis"] == "router_decision=resume_later"
    assert resume_entry["resume_command"] == f"python3 task-manager/task_manager.py autonomy-resume {stale_resume_id}"

    continue_entry = next(item for item in watchdog["resumable_autonomy"] if item["id"] == stale_continue_id)
    assert continue_entry["router_decision"] == "schedule_next_slice"
    assert continue_entry["resume_basis"] == "frontier_remaining_parent_open"

    waiting_entry = next(item for item in watchdog["excluded_autonomy"] if item["id"] == waiting_id)
    assert waiting_entry["awaiting_user"] is True
    assert waiting_entry["approval_needed"] is True

    missing_step_excluded = next(item for item in watchdog["excluded_autonomy"] if item["id"] == missing_step_id)
    assert missing_step_excluded["forced_status_ping_required"] is True
    assert missing_step_excluded["eligible_for_resume"] is False
    assert missing_step_excluded["forced_status_ping"]["reason"] == "missing_bounded_step"

    final_surface_excluded = next(item for item in watchdog["excluded_autonomy"] if item["id"] == final_surface_id)
    assert final_surface_excluded["forced_status_ping_required"] is True
    assert final_surface_excluded["forced_status_ping"]["reason"] == "final_result_not_surfaced"
    assert final_surface_excluded["forced_reroute_reason"] == "final_result_not_surfaced"

    closure_gap_entry = next(item for item in watchdog["progressed_not_closure_routed"] if item["id"] == closure_gap_id)
    assert closure_gap_entry["execution_stage"] == "verifying"
    assert "next explicit bounded slice" in closure_gap_entry["missing_closure_decision"]

    anti_silence_entry = next(item for item in watchdog["anti_silence_due"] if item["id"] == anti_silence_id)
    assert anti_silence_entry["forced_reroute_reason"] == "long_active_slice_without_visible_outcome"
    assert "Progress ping:" in anti_silence_entry["suggested_ping"]

    integrity_due_entry = next(item for item in watchdog["integrity_surface_due"] if item["id"] == integrity_due_id)
    assert integrity_due_entry["forced_reroute_reason"] == "significant_progress_not_surfaced"
    assert integrity_due_entry["orphan_evidence_status"] == "orphan_evidence_suspected"
    assert "Integrity ping:" in integrity_due_entry["suggested_ping"]
    assert "task-manager/task_manager.py note" in integrity_due_entry["suggested_fix_command"]

    missing_step_entry = next(item for item in watchdog["anti_silence_due"] if item["id"] == missing_step_id)
    assert missing_step_entry["forced_reroute_reason"] == "missing_bounded_step"
    assert missing_step_entry["missing_bounded_step"] is True
    assert missing_step_entry["current_mode"] == ""
    assert missing_step_entry["step_goal"] == ""
    assert "missing an explicit bounded-step contract" in missing_step_entry["suggested_ping"]

    counter = {"value": 0}

    def _fake_cron_run(cmd, cwd=None, capture_output=True, text=True):
        assert cmd[:4] == ["openclaw", "cron", "add", "--json"]
        job_name = cmd[cmd.index("--name") + 1]
        counter["value"] += 1
        return SimpleNamespace(returncode=0, stdout=json.dumps({"id": f"job-watchdog-{counter['value']}", "name": job_name}), stderr="")

    with patch.object(tm_mod.subprocess, "run", side_effect=_fake_cron_run):
        buf = io.StringIO()
        with redirect_stdout(buf):
            tm_mod.watchdog(SimpleNamespace(hours=1.0, run_resumes=True, cooldown_minutes=15))
        executed = json.loads(buf.getvalue())
    resumed_ids = {item["id"] for item in executed["resumed_autonomy"]}
    assert stale_resume_id in resumed_ids
    assert stale_continue_id in resumed_ids
    assert anti_silence_id not in resumed_ids
    assert missing_step_id not in resumed_ids
    assert integrity_due_id not in resumed_ids
    assert final_surface_id not in resumed_ids
    assert promised_not_armed_id not in resumed_ids
    assert waiting_id not in resumed_ids
    assert executed["resume_failures"] == []

    resumed_entry = next(item for item in executed["resumed_autonomy"] if item["id"] == stale_resume_id)
    assert "handoffs/autonomy-task-" in resumed_entry["handoff_path"]
    assert resumed_entry["spawn"]["job_id"]
    assert resumed_entry["spawn"]["job_name"].startswith(f"autonomy-resume-{stale_resume_id}-")

    resumed_state = load_autonomy_state(stale_resume_id)
    assert resumed_state["active_child"]["kind"] == "openclaw_cron_agent_turn"
    assert resumed_state["active_child"]["id"] == resumed_entry["spawn"]["job_id"]
    assert resumed_state["watchdog"]["cooldown_until"]
    assert resumed_state["execution"]["autonomy_armed"] is True
    assert resumed_state["execution"]["anchor_id"] == resumed_entry["spawn"]["job_id"]

    continue_state = load_autonomy_state(stale_continue_id)
    assert continue_state["active_child"]["kind"] == "openclaw_cron_agent_turn"
    assert continue_state["execution"]["autonomy_armed"] is True

    anti_silence_state_after = load_autonomy_state(anti_silence_id)
    assert anti_silence_state_after["active_child"]["kind"] != "openclaw_cron_agent_turn"
    assert anti_silence_state_after["watchdog"]["forced_reroute_reason"] == "long_active_slice_without_visible_outcome"

    missing_step_state_after = load_autonomy_state(missing_step_id)
    assert missing_step_state_after["active_child"]["kind"] != "openclaw_cron_agent_turn"
    assert missing_step_state_after["watchdog"]["forced_reroute_reason"] == "missing_bounded_step"
    assert missing_step_state_after["watchdog"]["step_goal"] == ""
    assert missing_step_state_after["watchdog"]["current_mode"] == ""

    final_surface_state_after = load_autonomy_state(final_surface_id)
    assert final_surface_state_after["active_child"]["kind"] != "openclaw_cron_agent_turn"
    assert final_surface_state_after["watchdog"]["forced_reroute_reason"] == "final_result_not_surfaced"
    assert final_surface_state_after["watchdog"]["final_surface_required"] is True

    waiting_state = load_autonomy_state(waiting_id)
    assert waiting_state["continuation"]["router_decision"] == "surface_to_user"
    assert waiting_state["watchdog"]["eligible_for_resume"] is False
    assert waiting_state["active_child"]["kind"] != "openclaw_cron_agent_turn"

    promised_state_after = load_autonomy_state(promised_not_armed_id)
    assert promised_state_after["execution"]["autonomy_requested"] is True
    assert promised_state_after["execution"]["autonomy_armed"] is False

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
