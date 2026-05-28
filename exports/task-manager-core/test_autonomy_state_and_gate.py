from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
TEST_ROOT = Path(tempfile.mkdtemp(prefix="tm-test-autonomy-gate-"))
os.environ["TASK_MANAGER_ROOT"] = str(TEST_ROOT)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autonomy_state import load_autonomy_state
from blind_judge_validator import validate_status_transition


TM = WORKSPACE / "task-manager" / "task_manager.py"
TEST_ENV = dict(os.environ)


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run([sys.executable, str(TM), *args], cwd=str(WORKSPACE), env=TEST_ENV, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise AssertionError(f"command failed: {' '.join(args)}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def main() -> int:
    title = "tmp autonomy gate proof"
    created = json.loads(_run("add", title, "--details", "autonomy gate proof", "--next-action", "Do the bounded thing").stdout)
    task_id = int(created["task_id"])
    _run("start", str(task_id), "--note", "Starting proof slice with evidence artifact task-manager/test_autonomy_state_and_gate.py and verification command python3 task-manager/test_autonomy_state_and_gate.py", "--next-action", "Do the bounded thing")

    init_payload = json.loads(_run("autonomy-init", str(task_id), "--note", "Autonomous execution entered", "--next-action", "Do the bounded thing").stdout)
    assert init_payload["autonomy_state"]["autonomy_mode"] is True
    assert init_payload["autonomy_state"]["watchdog"]["current_mode"] == "implementation"
    assert init_payload["autonomy_state"]["watchdog"]["step_goal"] == "Do the bounded thing"
    assert init_payload["autonomy_state"]["watchdog"]["expected_output"] == "bounded_progress_update_or_terminal_route"
    assert init_payload["autonomy_state"]["watchdog"]["step_started_at"]
    assert init_payload["autonomy_state"]["watchdog"]["step_due_at"]
    assert init_payload["autonomy_state"]["watchdog"]["if_fail_route"] == "forced_status_ping"
    assert init_payload["autonomy_state"]["watchdog"]["nudge_count"] == 0
    assert init_payload["autonomy_state"]["watchdog"]["final_surface_required"] is True
    assert init_payload["autonomy_state"]["continuation"]["surface_reason"] == "autonomy_launch_failed"
    assert init_payload["autonomy_state"]["continuation"]["router_decision"] == "surface_to_user"
    state = load_autonomy_state(task_id)
    assert state["autonomy_mode"] is True
    assert state["watchdog"]["current_mode"] == "implementation"
    assert state["watchdog"]["step_goal"] == "Do the bounded thing"
    assert state["watchdog"]["if_fail_route"] == "forced_status_ping"

    armed_created = json.loads(_run("add", "tmp autonomy gate armed proof", "--details", "armed gate proof", "--next-action", "Do the bounded thing").stdout)
    armed_task_id = int(armed_created["task_id"])
    _run(
        "start",
        str(armed_task_id),
        "--note",
        "Starting armed proof slice with evidence artifact task-manager/test_autonomy_state_and_gate.py and verification command python3 task-manager/test_autonomy_state_and_gate.py",
        "--next-action",
        "Do the bounded thing",
    )

    armed_payload = json.loads(
        _run(
            "autonomy-init",
            str(armed_task_id),
            "--note",
            "Autonomous execution entered with armed lane",
            "--next-action",
            "Do the bounded thing",
            "--arm",
            "yes",
            "--execution-mode",
            "current_run",
            "--anchor-kind",
            "current_run",
            "--anchor-id",
            "gate-proof-lane",
        ).stdout
    )
    assert armed_payload["autonomy_state"]["watchdog"]["final_surface_required"] is False
    assert armed_payload["autonomy_state"]["continuation"]["surface_reason"] == ""
    assert armed_payload["autonomy_state"]["continuation"]["router_decision"] != "surface_to_user"

    with tempfile.TemporaryDirectory() as tmp:
        child = Path(tmp) / "child.json"
        child.write_text(json.dumps({
            "status": "review_ready",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "Local slice complete only",
            "next_action": "Continue internally",
            "done_criteria_met": False,
            "artifact_refs": ["task-manager/test_autonomy_router.py"],
            "verification_refs": ["python3 task-manager/test_autonomy_router.py"],
        }), encoding="utf-8")
        routed = json.loads(_run("autonomy-route", str(armed_task_id), "--child-result-file", str(child)).stdout)
        assert routed["routing"]["router_decision"] in {"continue_now", "schedule_next_slice"}
        auto_resume = routed["auto_resume"]
        assert auto_resume is not None
        assert auto_resume["resumed"] is True
        assert auto_resume["resume_basis"] == "immediate_followup_slice"
        assert auto_resume["spawn"]["job_id"]
        assert auto_resume["autonomy_state"]["active_child"]["kind"] == "openclaw_cron_agent_turn"

    shown_progress = json.loads(_run("autonomy-show", str(armed_task_id)).stdout)
    assert shown_progress["integrity"]["surface_required"] is True
    assert shown_progress["integrity"]["stale_in_progress_reason"] == "significant_progress_not_surfaced"

    with tempfile.TemporaryDirectory() as tmp:
        child = Path(tmp) / "status-ping.json"
        child.write_text(json.dumps({
            "status": "in_progress",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "Still working; status ping should remain internal",
            "next_action": "Continue internally",
            "parent_goal_open": True,
            "frontier_known": True,
            "frontier_remaining": True,
            "done_criteria_met": False,
            "status_ping": True,
            "artifact_refs": ["task-manager/test_autonomy_state_and_gate.py"],
        }), encoding="utf-8")
        routed = json.loads(_run("autonomy-route", str(armed_task_id), "--child-result-file", str(child)).stdout)
        assert routed["routing"]["router_decision"] in {"continue_now", "schedule_next_slice"}
        assert routed["routing"]["surface_suppressed"] is True
        assert routed["routing"]["surface_suppressed_reason"] == "status_ping_non_terminal"
        assert routed["routing"]["would_have_surfaced_as"] == "status_reply"

    shown_non_terminal = json.loads(_run("autonomy-show", str(armed_task_id)).stdout)
    assert shown_non_terminal["continuation"]["router_decision"] in {"continue_now", "schedule_next_slice"}
    assert shown_non_terminal["continuation"]["surface_suppressed_reason"] == "status_ping_non_terminal"

    status_snapshot = json.loads(_run("autonomy-status", str(armed_task_id)).stdout)
    assert status_snapshot["forced_status_ping"] is not None
    assert status_snapshot["forced_status_ping"]["reason"] == "significant_progress_not_surfaced"

    blocked = _run("review", str(armed_task_id), "--note", "Attempted premature review with evidence artifact task-manager/test_autonomy_router.py and verification python3 task-manager/test_autonomy_router.py", "--next-action", "Continue internally", check=False)
    assert blocked.returncode != 0
    gate_output = (blocked.stderr or "") + (blocked.stdout or "")
    assert "Autonomy delivery gate blocked user-facing transition" in gate_output

    waiting = _run("wait", str(armed_task_id), "--blocked-reason", "Convenient checkpoint only", "--note", "Attempted fake waiting_user transition", "--next-action", "Continue internally", check=False)
    assert waiting.returncode != 0
    waiting_output = (waiting.stderr or "") + (waiting.stdout or "")
    assert "Autonomy delivery gate blocked user-facing transition" in waiting_output

    with tempfile.TemporaryDirectory() as tmp:
        child = Path(tmp) / "done.json"
        child.write_text(json.dumps({
            "status": "done",
            "outcome_class": "terminal_done",
            "payload_class": "canonical_result",
            "summary": "Parent DoD satisfied with evidence artifact task-manager/test_autonomy_state_and_gate.py and verification python3 task-manager/test_autonomy_state_and_gate.py",
            "next_action": "",
            "done_criteria_met": True,
            "parent_goal_complete": True,
            "frontier_remaining": False,
            "artifact_refs": ["task-manager/test_autonomy_state_and_gate.py"],
        }), encoding="utf-8")
        done_route = json.loads(_run("autonomy-route", str(armed_task_id), "--child-result-file", str(child)).stdout)
        assert done_route["routing"]["router_decision"] == "surface_to_user"
        assert done_route["routing"]["surface_reason"] == "done"

    shown = json.loads(_run("autonomy-show", str(armed_task_id)).stdout)
    assert shown["continuation"]["router_decision"] == "surface_to_user"
    assert shown["continuation"]["surface_reason"] == "done"
    assert shown["continuation"]["last_completion_scope"] == "parent"
    assert shown["watchdog"]["final_surface_required"] is True

    shown_task = json.loads(_run("show", str(armed_task_id), "--state-card", "--format", "json").stdout)
    assert shown_task["identity"]["task_id"] == armed_task_id
    assert shown_task["health"]["autonomy_mode"] is True
    assert shown_task["proof"]["closure_readiness"] == "not-closure-ready"
    assert shown_task["proof"]["latest_event_envelope"]["family"] in {"work_event", "proof_event", "incident_event", "recovery_event"}
    assert shown_task["proof"]["latest_event_envelope"]["surface_policy"]
    assert shown_task["operator_action"]["recommended_action"]

    list_snapshot = json.loads(_run("list", "--format", "json", "--limit", "20").stdout)
    listed = next(item for item in list_snapshot if int(item["id"]) == armed_task_id)
    assert listed["summary_row"]["task_id"] == armed_task_id
    assert listed["summary_row"]["health_posture"] == "healthy"
    assert listed["summary_row"]["closure_readiness"] == "not-closure-ready"
    assert listed["summary_row"]["latest_event_envelope"]["family"] in {"work_event", "proof_event", "incident_event", "recovery_event"}
    assert listed["summary_row"]["recommended_action"] == shown_task["operator_action"]["recommended_action"]

    list_text = _run("list", "--limit", "20").stdout
    assert f"#{armed_task_id} [in_progress]" in list_text
    assert "summary: health=healthy continuity=delegated closure=not-closure-ready" in list_text
    assert f"action: {shown_task['operator_action']['recommended_action']}" in list_text

    state_card_list_text = _run("list", "--state-card", "--limit", "20").stdout
    assert f"Task #{armed_task_id} — tmp autonomy gate armed proof" in state_card_list_text
    assert "event_family:" in state_card_list_text
    assert "[operator_action]" in state_card_list_text

    done_status = json.loads(_run("autonomy-status", str(armed_task_id)).stdout)
    assert done_status["forced_status_ping"] is not None
    assert done_status["forced_status_ping"]["reason"] == "final_result_not_surfaced"
    assert any("terminal result appears ready internally" in item for item in done_status["forced_status_ping"]["what_is_red"])

    with tempfile.TemporaryDirectory() as tmp:
        child = Path(tmp) / "blocked_external.json"
        child.write_text(json.dumps({
            "status": "blocked",
            "outcome_class": "approval_needed",
            "payload_class": "canonical_result",
            "blocked_reason": "Need exact user approval for external deploy",
            "waiting_is_external": True,
            "approval_needed": True,
            "artifact_refs": ["task-manager/test_autonomy_state_and_gate.py"],
        }), encoding="utf-8")
        wait_route = json.loads(_run("autonomy-route", str(armed_task_id), "--child-result-file", str(child)).stdout)
        assert wait_route["routing"]["router_decision"] == "surface_to_user"
        assert wait_route["routing"]["surface_reason"] == "approval_needed"
        assert wait_route["routing"]["awaiting_user"] is True

    allowed_wait = _run("wait", str(armed_task_id), "--blocked-reason", "Need exact user approval for external deploy", "--note", "Allowed waiting_user after approval-needed autonomy route", "--next-action", "Wait for user approval")
    allowed_payload = json.loads(allowed_wait.stdout)
    assert allowed_payload["status"] == "waiting_user"
    assert allowed_payload["judge_feedback"]["autonomy_state"]["surface_reason"] == "approval_needed"

    external_surface_status = json.loads(_run("autonomy-status", str(armed_task_id)).stdout)
    assert external_surface_status["forced_status_ping"] is None

    envelope_task = json.loads(_run("add", "tmp autonomy envelope proof", "--details", "autonomy envelope proof", "--next-action", "Implement bounded slice").stdout)
    envelope_task_id = int(envelope_task["task_id"])
    _run("start", str(envelope_task_id), "--note", "Starting envelope proof", "--next-action", "Implement bounded slice")
    _run(
        "autonomy-init",
        str(envelope_task_id),
        "--note",
        "Autonomous execution entered",
        "--next-action",
        "Implement bounded slice",
        "--arm",
        "yes",
        "--execution-mode",
        "current_run",
        "--anchor-kind",
        "current_run",
        "--anchor-id",
        "envelope-proof-lane",
    )

    with tempfile.TemporaryDirectory() as tmp:
        child = Path(tmp) / "done-envelope.txt"
        child.write_text(
            """DONE\n- task_id: 999\n- summary: Local slice complete only\n- result_anchor: task-manager/test_autonomy_state_and_gate.py\n- next_action: Continue bounded slice\n""",
            encoding="utf-8",
        )
        routed = json.loads(_run("autonomy-route", str(envelope_task_id), "--child-result-file", str(child)).stdout)
        assert routed["routing"]["router_decision"] in {"continue_now", "schedule_next_slice"}
        assert routed["routing"]["surface_reason"] == ""
        assert routed["autonomy_state"]["last_child_result"]["outcome_class"] == "local_progress"
        assert routed["autonomy_state"]["last_child_result"]["payload_class"] == "canonical_result"

    with tempfile.TemporaryDirectory() as tmp:
        child = Path(tmp) / "blocked-envelope.txt"
        child.write_text(
            """BLOCKED\n- task_id: 999\n- summary: Need explicit approval\n- blocked_reason: Need exact user approval for deploy\n- owner_for_decision: human:operator\n- resume_mode: await_unblock\n- next_action: Wait for exact approval\n""",
            encoding="utf-8",
        )
        routed = json.loads(_run("autonomy-route", str(envelope_task_id), "--child-result-file", str(child)).stdout)
        assert routed["routing"]["router_decision"] == "surface_to_user"
        assert routed["routing"]["surface_reason"] == "blocked_external"

    with tempfile.TemporaryDirectory() as tmp:
        child = Path(tmp) / "invalid-missing-outcome.json"
        child.write_text(json.dumps({
            "status": "done",
            "payload_class": "canonical_result",
            "summary": "Malformed child result without outcome class",
            "done_criteria_met": True,
        }), encoding="utf-8")
        routed = json.loads(_run("autonomy-route", str(envelope_task_id), "--child-result-file", str(child)).stdout)
        assert routed["routing"]["router_decision"] == "escalate_internal"
        assert "missing required outcome_class" in routed["routing"]["decision_reason"]

    with tempfile.TemporaryDirectory() as tmp:
        child = Path(tmp) / "invalid-state-dump.json"
        child.write_text(json.dumps({
            "status": "done",
            "outcome_class": "terminal_done",
            "payload_class": "state_dump",
            "summary": "This should never surface",
            "done_criteria_met": True,
        }), encoding="utf-8")
        routed = json.loads(_run("autonomy-route", str(envelope_task_id), "--child-result-file", str(child)).stdout)
        assert routed["routing"]["router_decision"] == "escalate_internal"
        assert "non-deliverable" in routed["routing"]["decision_reason"]

    with tempfile.TemporaryDirectory() as tmp:
        child = Path(tmp) / "command-running-envelope.txt"
        child.write_text(
            """ACK\n- summary: command-still-running on remote child\n- next_action: Wait for durable completion\n""",
            encoding="utf-8",
        )
        routed = json.loads(_run("autonomy-route", str(envelope_task_id), "--child-result-file", str(child)).stdout)
        assert routed["routing"]["router_decision"] == "escalate_internal"
        assert routed["autonomy_state"]["last_child_result"]["payload_class"] == "orchestration_artifact"

    with tempfile.TemporaryDirectory() as tmp:
        child = Path(tmp) / "stale-snapshot-envelope.txt"
        child.write_text(
            """ACK\n- summary: stale snapshot from prior pass\n- parent_next_action: Continue fresh bounded pass\n""",
            encoding="utf-8",
        )
        routed = json.loads(_run("autonomy-route", str(envelope_task_id), "--child-result-file", str(child)).stdout)
        assert routed["routing"]["router_decision"] in {"resume_later", "schedule_next_slice"}
        assert routed["autonomy_state"]["last_child_result"]["payload_class"] == "stale_snapshot"
        assert routed["autonomy_state"]["continuation"]["frontier_next_action"] == "Continue fresh bounded pass"

    legacy_task = json.loads(_run("add", "tmp legacy autonomy state normalization", "--details", "legacy continuation state should still resume", "--next-action", "Resume bounded pass").stdout)
    legacy_task_id = int(legacy_task["task_id"])
    _run("start", str(legacy_task_id), "--note", "Start legacy normalization task", "--next-action", "Resume bounded pass")
    _run(
        "autonomy-init",
        str(legacy_task_id),
        "--note",
        "Enter autonomous mode",
        "--next-action",
        "Resume bounded pass",
        "--arm",
        "yes",
        "--execution-mode",
        "current_run",
        "--anchor-kind",
        "current_run",
        "--anchor-id",
        "legacy-proof-lane",
    )
    legacy_state_path = TEST_ROOT / "runtime" / "autonomy" / f"task-{legacy_task_id}.json"
    legacy_state = json.loads(legacy_state_path.read_text(encoding="utf-8"))
    legacy_state["continuation"].update({
        "router_decision": "none",
        "surface_reason": "",
        "next_action": "Resume bounded pass",
        "frontier_next_action": "",
        "parent_goal_open": False,
        "frontier_known": False,
        "frontier_remaining": False,
        "frontier_exhausted": False,
        "awaiting_user": False,
        "approval_needed": False,
        "risk_alert": False,
        "parent_goal_complete": False,
        "parent_goal_blocked": False,
    })
    legacy_state_path.write_text(json.dumps(legacy_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shown_legacy = json.loads(_run("autonomy-show", str(legacy_task_id)).stdout)
    assert shown_legacy["continuation"]["parent_goal_open"] is True
    assert shown_legacy["continuation"]["frontier_known"] is True
    assert shown_legacy["continuation"]["frontier_remaining"] is True
    assert shown_legacy["watchdog"]["current_mode"] == "implementation"
    assert shown_legacy["watchdog"]["step_goal"] == "Resume bounded pass"
    assert shown_legacy["watchdog"]["expected_output"] == "bounded_progress_update_or_terminal_route"
    assert shown_legacy["watchdog"]["step_started_at"]
    assert shown_legacy["watchdog"]["step_due_at"]
    assert shown_legacy["watchdog"]["if_fail_route"] == "forced_status_ping"
    assert shown_legacy["watchdog"]["last_nudge_at"] == ""
    assert shown_legacy["watchdog"]["nudge_count"] == 0
    assert shown_legacy["watchdog"]["final_surface_required"] is False

    import sqlite3
    con = sqlite3.connect(str(TEST_ROOT / "tasks.db"))
    try:
        con.execute("UPDATE tasks SET updated_at = '2026-05-20T00:00:00Z' WHERE id = ?", (legacy_task_id,))
        con.commit()
    finally:
        con.close()
    legacy_state_path = TEST_ROOT / "runtime" / "autonomy" / f"task-{legacy_task_id}.json"
    legacy_state = json.loads(legacy_state_path.read_text(encoding="utf-8"))
    legacy_state["watchdog"]["anti_silence_due_at"] = "2026-05-20T00:00:00Z"
    legacy_state["watchdog"]["forced_reroute_reason"] = "missing_bounded_step"
    legacy_state["watchdog"]["current_mode"] = ""
    legacy_state["watchdog"]["step_goal"] = ""
    legacy_state["continuation"]["router_decision"] = "continue_now"
    legacy_state["continuation"]["decision_reason"] = "Autonomous execution is still active."
    legacy_state["last_child_result"]["summary"] = "Partial progress exists but no honest closure yet"
    legacy_state["last_child_result"]["artifact_refs"] = ["task-manager/test_autonomy_state_and_gate.py"]
    legacy_state_path.write_text(json.dumps(legacy_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    forced_status = json.loads(_run("autonomy-status", str(legacy_task_id)).stdout)
    forced_ping = forced_status["forced_status_ping"]
    assert forced_ping["required"] is True
    assert forced_ping["reason"] == "missing_bounded_step"
    assert forced_ping["honest_closure"] is False
    assert forced_ping["single_next_bounded_step"] == "Resume bounded pass"
    assert any("Partial progress exists" in item for item in forced_ping["what_is_proven"])
    assert any("bounded-step contract is missing" in item for item in forced_ping["what_is_red"])

    research_task = json.loads(_run("add", "tmp semantic red regression", "--details", "semantic regression should switch to research mode", "--next-action", "Implement bounded pass").stdout)
    research_task_id = int(research_task["task_id"])
    _run("start", str(research_task_id), "--note", "Start semantic-red proof", "--next-action", "Implement bounded pass")
    _run("autonomy-init", str(research_task_id), "--note", "Autonomous execution entered", "--next-action", "Implement bounded pass")
    with tempfile.TemporaryDirectory() as tmp:
        child = Path(tmp) / "semantic-red.json"
        child.write_text(json.dumps({
            "status": "review_ready",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "Two test families now show semantic mismatch; switch to research mode before more implementation churn",
            "next_action": "Audit contract expectations across test families",
            "parent_goal_open": True,
            "frontier_known": True,
            "frontier_remaining": True,
            "done_criteria_met": False,
            "failing_test_families": ["state_and_gate", "watchdog"],
        }), encoding="utf-8")
        routed = json.loads(_run("autonomy-route", str(research_task_id), "--child-result-file", str(child)).stdout)
        assert routed["routing"]["router_decision"] == "schedule_next_slice"
    research_state = json.loads(_run("autonomy-show", str(research_task_id)).stdout)
    assert research_state["watchdog"]["current_mode"] == "research"
    assert research_state["watchdog"]["forced_reroute_reason"] == "semantic_red_regression"
    assert research_state["watchdog"]["step_goal"] == "Audit contract expectations across test families"

    with tempfile.TemporaryDirectory() as tmp:
        child = Path(tmp) / "bad-scope-done.json"
        child.write_text(json.dumps({
            "status": "done",
            "outcome_class": "terminal_done",
            "payload_class": "canonical_result",
            "summary": "Bad completion scope should not surface",
            "done_criteria_met": True,
            "parent_goal_complete": True,
            "frontier_remaining": False,
            "last_completion_scope": "leaf",
        }), encoding="utf-8")
        routed = json.loads(_run("autonomy-route", str(envelope_task_id), "--child-result-file", str(child)).stdout)
        assert routed["routing"]["router_decision"] == "escalate_internal"
        assert "completion scope is below parent/user-goal closure" in routed["routing"]["decision_reason"]

    closure_incomplete_task = json.loads(_run("add", "tmp closure incomplete normalization", "--details", "done surface must collapse if frontier still open", "--next-action", "Finish remaining child closure").stdout)
    closure_incomplete_task_id = int(closure_incomplete_task["task_id"])
    _run("start", str(closure_incomplete_task_id), "--note", "Start closure incomplete task", "--next-action", "Finish remaining child closure")
    _run(
        "autonomy-init",
        str(closure_incomplete_task_id),
        "--note",
        "Enter autonomous mode",
        "--next-action",
        "Finish remaining child closure",
        "--arm",
        "yes",
        "--execution-mode",
        "current_run",
        "--anchor-kind",
        "current_run",
        "--anchor-id",
        "closure-proof-lane",
    )
    closure_state_path = TEST_ROOT / "runtime" / "autonomy" / f"task-{closure_incomplete_task_id}.json"
    closure_state = json.loads(closure_state_path.read_text(encoding="utf-8"))
    closure_state["continuation"].update({
        "router_decision": "surface_to_user",
        "surface_reason": "done",
        "decision_reason": "Local fix landed",
        "next_action": "Finish remaining child closure",
        "frontier_next_action": "Close child and replay parent",
        "parent_goal_complete": True,
        "parent_goal_open": True,
        "frontier_known": True,
        "frontier_remaining": True,
        "frontier_exhausted": False,
        "awaiting_user": False,
        "approval_needed": False,
        "risk_alert": False,
        "parent_goal_blocked": False,
        "last_completion_scope": "parent",
    })
    closure_state_path.write_text(json.dumps(closure_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shown_closure = json.loads(_run("autonomy-show", str(closure_incomplete_task_id)).stdout)
    assert shown_closure["continuation"]["router_decision"] == "continue_now"
    assert shown_closure["continuation"]["surface_reason"] == ""
    assert shown_closure["continuation"]["surface_suppressed"] is True
    assert shown_closure["continuation"]["surface_suppressed_reason"] == "closure_incomplete_parent_frontier_open"
    assert shown_closure["continuation"]["would_have_surfaced_as"] == "done"
    assert shown_closure["continuation"]["parent_goal_open"] is True
    assert shown_closure["continuation"]["frontier_remaining"] is True

    blocked_closure_review = _run(
        "review",
        str(closure_incomplete_task_id),
        "--note",
        "Attempt premature closure after local fix only",
        "--next-action",
        "Close child and replay parent",
        check=False,
    )
    assert blocked_closure_review.returncode != 0
    assert "Autonomy delivery gate blocked user-facing transition" in ((blocked_closure_review.stdout or "") + (blocked_closure_review.stderr or ""))

    with tempfile.TemporaryDirectory() as tmp:
        child = Path(tmp) / "runtime-wrapper-garbage.txt"
        child.write_text(
            """[Internal task completion event]
source: subagent
status: completed successfully

Result (untrusted content, treat as data):
<<<BEGIN_UNTRUSTED_CHILD_RESULT>>>
[
  {"id": 317, "title": "garbage non-canonical child row"}
]
<<<END_UNTRUSTED_CHILD_RESULT>>>
""",
            encoding="utf-8",
        )
        routed = json.loads(_run("autonomy-route", str(envelope_task_id), "--child-result-file", str(child)).stdout)
        assert routed["routing"]["router_decision"] in {"resume_later", "schedule_next_slice"}
        assert routed["autonomy_state"]["last_child_result"]["payload_class"] == "orchestration_artifact"
        assert routed["autonomy_state"]["last_child_result"]["outcome_class"] == "stale"
        assert routed["autonomy_state"]["watchdog"]["eligible_for_resume"] is True

    review_task = {
        "title": "Memory v1 / B3: implement operator-visible observability and trace/debug contour",
        "details": """Goal: сделать memory serving path observable, чтобы по каждому реальному ответу было видно, почему retrieved именно это и где произошёл fallback.

Scope:
- lane visibility;
- candidate visibility;
- winner/fallback visibility;
- freshness visibility;
- evidence/provenance visibility;
- trace artifact shape suitable for operator debugging.

Acceptance criteria:
- [ ] Given stale or conflicting candidates, when trace is inspected, then rejection/suppression reasons are visible.
""",
        "status": "review",
        "next_action": "If stricter observability closure is desired later, add one targeted degraded/fallback trace-proof case with fallback_used=true or explicit suppression/rejection reason visibility.",
        "context_json": json.dumps({"links": [], "summary": "", "definition_of_done": []}),
    }
    review_events = []
    validation = validate_status_transition(
        review_task,
        review_events,
        "review",
        note=(
            "Moved to review on declared Memory v1 scope. Existing observability evidence proves operator-visible trace on the live runtime path. "
            "Artifact: pkm-memory/outputs/task-466-trace-summary-observability-2026-05-14/verification-report.json. "
            "Verification: ran python3 pkm-memory/scripts/verify_trace_summary_observability.py. "
            "Residual: explicit fallback_used=true degraded case is not separately proven in this pack."
        ),
        next_action=review_task["next_action"],
    )
    assert validation["passed"] is True
    assert "resolvable_anchor" not in validation["missing"]

    done_task = {
        "title": "AIK / suppress premature status replies during autonomous execution",
        "details": """Problem: autonomous execution currently blocks premature done-surfacing better than premature status-surfacing. A direct user status inquiry can still pull main out of execution mode even when the active frontier remains open and no terminal exception exists.\n\nAcceptance criteria:\n- [ ] In autonomous mode, non-terminal status inquiries do not break execution when the active frontier remains open and no external approval/access/business decision is requested.\n- [ ] A canonical suppression reason is persisted for this case (for example: status_ping_non_terminal / user_ping_while_frontier_open).\n- [ ] There is executable regression proof that status pings are suppressed while terminal/approval-needed cases still surface.\n- [ ] Thin-main under autonomy is reinforced in the canonical TM control path rather than as a prompt-only convention.\n""",
        "status": "review",
        "next_action": "",
        "context_json": json.dumps({"links": [], "summary": "", "definition_of_done": []}),
    }
    done_events = [{"event_type": "status:review", "note": "Moved to review after canonical autonomy terminalization"}]
    done_validation = validate_status_transition(
        done_task,
        done_events,
        "done",
        note=(
            "Done: #748 canonical autonomy hardening is complete. "
            "Evidence: task-manager/autonomy_router.py suppresses non-terminal status pings while task-manager/autonomy_state.py persists status_ping_non_terminal. "
            "Verification: ran python3 task-manager/test_autonomy_router.py and python3 task-manager/test_autonomy_state_and_gate.py. "
            "Anchor: task-manager/autonomy_router.py, task-manager/autonomy_state.py. "
            "Residual semantic labels approval/access/business and terminal/approval-needed are policy labels only, not path anchors."
        ),
        next_action="",
    )
    assert done_validation["passed"] is True
    assert "resolvable_anchor" not in done_validation["missing"]
    assert "claimed_outcome" not in done_validation["missing"]
    assert all(anchor not in done_validation["signals"]["all_anchors"] for anchor in ["approval/access/business", "terminal/approval-needed"])

    validator_fix_task = {
        "title": "AIK / fix TM closure validator false-positive on semantic slash-pairs in done/review notes",
        "details": """Problem: TM closure validation still misreads semantic slash-pairs embedded in natural-language acceptance/details/notes (for example approval/access/business and terminal/approval-needed) as resolvable path anchors during done/review gating.\n\nAcceptance criteria:\n- [ ] Semantic slash-pairs used as concept labels in notes/details no longer count as path anchors.\n- [ ] Existing true path/file anchors still resolve normally.\n- [ ] There is regression proof covering the #748 closure case and similar semantic slash-pairs.\n""",
        "status": "in_progress",
        "next_action": "Move to review",
        "context_json": json.dumps({"links": [], "summary": "", "definition_of_done": []}),
    }
    validator_fix_validation = validate_status_transition(
        validator_fix_task,
        [],
        "review",
        note=(
            "Review-ready: validator fix is implemented. "
            "Evidence: task-manager/blind_judge_validator.py now ignores semantic slash labels in acceptance/details/notes and notes/details while keeping task-manager/test_autonomy_state_and_gate.py as a real anchor. "
            "Verification: ran python3 task-manager/test_autonomy_state_and_gate.py and python3 task-manager/test_autonomy_router.py."
        ),
        next_action="Move to done after review gate",
    )
    assert validator_fix_validation["passed"] is True
    assert "resolvable_anchor" not in validator_fix_validation["missing"]
    assert all(anchor not in validator_fix_validation["signals"]["all_anchors"] for anchor in ["acceptance/details/notes", "notes/details", "path/file"])

    critical_review_task = {
        "title": "Closure gate hardening: require fresh executable verification before done for system-critical tasks",
        "details": "Prevent autonomy-hardening and production-readiness tasks from reaching review/done without fresh executable verification in the transition note.",
        "status": "in_progress",
        "next_action": "Move to review",
        "context_json": json.dumps({"links": [], "summary": "", "definition_of_done": []}),
    }
    critical_missing_fresh = validate_status_transition(
        critical_review_task,
        [],
        "review",
        note=(
            "Review-ready: closure gate contour is drafted. "
            "Evidence: task-manager/blind_judge_validator.py contains the first-pass critical-task gate. "
            "Verification: verified conceptually and checked the validator path."
        ),
        next_action="Move to done after review gate",
    )
    assert critical_missing_fresh["passed"] is False
    assert "fresh_executable_verification" in critical_missing_fresh["missing"]

    critical_with_fresh = validate_status_transition(
        critical_review_task,
        [],
        "review",
        note=(
            "Review-ready: closure gate contour is implemented. "
            "Evidence: task-manager/blind_judge_validator.py contains the first-pass critical-task gate and task-manager/test_autonomy_state_and_gate.py covers it. "
            "Verification: ran python3 task-manager/test_autonomy_state_and_gate.py and it passed green."
        ),
        next_action="Move to done after review gate",
    )
    assert critical_with_fresh["passed"] is True
    assert critical_with_fresh["signals"]["fresh_executable_verification_present"] is True

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
