from __future__ import annotations

import io
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
TEST_ROOT = Path(tempfile.mkdtemp(prefix="tm-test-autonomy-e2e-"))
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


def _create_autonomous_task(title: str, next_action: str, details: str = "autonomy exhaustive e2e proof") -> int:
    created = json.loads(_run("add", title, "--details", details, "--next-action", next_action).stdout)
    task_id = int(created["task_id"])
    _run("start", str(task_id), "--note", "Starting exhaustive autonomy proof", "--next-action", next_action)
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
    con = sqlite3.connect(str(TEST_ROOT / "tasks.db"))
    try:
        con.execute("UPDATE tasks SET updated_at = '2026-05-20T00:00:00Z' WHERE id = ?", (task_id,))
        con.commit()
    finally:
        con.close()


def _route(task_id: int, payload: dict) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        child = Path(tmp) / "child.json"
        child.write_text(json.dumps(payload), encoding="utf-8")
        return json.loads(_run("autonomy-route", str(task_id), "--child-result-file", str(child)).stdout)


def main() -> int:
    # 1. Non-terminal local completion stays internal and blocks premature surfacing.
    continue_id = _create_autonomous_task("tmp autonomy e2e continue", "Continue bounded chain")
    routed_continue = _route(
        continue_id,
        {
            "status": "review_ready",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "Local slice complete only",
            "next_action": "Continue bounded chain",
            "done_criteria_met": False,
            "artifact_refs": ["task-manager/test_autonomy_e2e_exhaustive.py"],
        },
    )
    assert routed_continue["routing"]["router_decision"] == "schedule_next_slice"
    blocked_review = _run(
        "review",
        str(continue_id),
        "--note",
        "Attempted premature review",
        "--next-action",
        "Continue bounded chain",
        check=False,
    )
    assert blocked_review.returncode != 0
    assert "Autonomy delivery gate blocked user-facing transition" in ((blocked_review.stdout or "") + (blocked_review.stderr or ""))

    blocked_wait = _run(
        "wait",
        str(continue_id),
        "--blocked-reason",
        "Convenient checkpoint only",
        "--note",
        "Attempted fake waiting_user transition",
        "--next-action",
        "Continue bounded chain",
        check=False,
    )
    assert blocked_wait.returncode != 0
    assert "Autonomy delivery gate blocked user-facing transition" in ((blocked_wait.stdout or "") + (blocked_wait.stderr or ""))

    _age_task(continue_id)

    # 2. Stale non-terminal work is resumable by watchdog and spawns the next bounded pass.
    stale_resume_id = _create_autonomous_task("tmp autonomy e2e stale resume", "Resume stale bounded chain")
    stale_state = load_autonomy_state(stale_resume_id)
    stale_state["continuation"] = {
        "router_decision": "resume_later",
        "decision_reason": "Autonomous task is stale but still resumable; schedule another bounded internal pass.",
        "surface_reason": "",
        "next_action": "Resume stale bounded chain",
        "awaiting_user": False,
        "approval_needed": False,
        "risk_alert": False,
        "done_criteria_met": False,
    }
    stale_state["watchdog"]["eligible_for_resume"] = True
    save_autonomy_state(stale_resume_id, stale_state)
    _age_task(stale_resume_id)

    # 3. Legit external blocker surfaces, but is excluded from autonomous resume.
    approval_id = _create_autonomous_task("tmp autonomy e2e approval", "Wait for exact approval")
    approval_route = _route(
        approval_id,
        {
            "status": "blocked",
            "outcome_class": "approval_needed",
            "payload_class": "canonical_result",
            "blocked_reason": "Need exact user approval for production deploy",
            "waiting_is_external": True,
            "approval_needed": True,
            "artifact_refs": ["task-manager/test_autonomy_e2e_exhaustive.py"],
        },
    )
    assert approval_route["routing"]["router_decision"] == "surface_to_user"
    assert approval_route["routing"]["surface_reason"] == "approval_needed"
    allowed_wait = json.loads(
        _run(
            "wait",
            str(approval_id),
            "--blocked-reason",
            "Need exact user approval for production deploy",
            "--note",
            "Allowed waiting after approval-needed route",
            "--next-action",
            "Wait for exact approval",
        ).stdout
    )
    assert allowed_wait["status"] == "waiting_user"
    _age_task(approval_id)

    # 4. Terminal done can surface legitimately.
    done_id = _create_autonomous_task("tmp autonomy e2e done", "Finish bounded chain")
    done_route = _route(
        done_id,
        {
            "status": "done",
            "outcome_class": "terminal_done",
            "payload_class": "canonical_result",
            "summary": "Parent DoD fully satisfied",
            "next_action": "",
            "done_criteria_met": True,
            "parent_goal_complete": True,
            "frontier_remaining": False,
            "artifact_refs": ["task-manager/test_autonomy_e2e_exhaustive.py"],
        },
    )
    assert done_route["routing"]["router_decision"] == "surface_to_user"
    assert done_route["routing"]["surface_reason"] == "done"

    watchdog_before = json.loads(_run("watchdog", "--hours", "1").stdout)
    resumable_ids = {item["id"] for item in watchdog_before["resumable_autonomy"]}
    excluded_ids = {item["id"] for item in watchdog_before["excluded_autonomy"]}
    assert continue_id not in resumable_ids
    assert continue_id in excluded_ids
    continue_excluded = next(item for item in watchdog_before["excluded_autonomy"] if item["id"] == continue_id)
    assert continue_excluded["forced_status_ping_required"] is True
    assert continue_excluded["forced_reroute_reason"] == "significant_progress_not_surfaced"
    assert stale_resume_id in resumable_ids
    assert approval_id not in resumable_ids
    assert approval_id in excluded_ids
    assert done_id in excluded_ids

    counter = {"value": 0}

    def _fake_cron_run(cmd, cwd=None, capture_output=True, text=True):
        assert cmd[:4] == ["openclaw", "cron", "add", "--json"]
        job_name = cmd[cmd.index("--name") + 1]
        counter["value"] += 1
        return SimpleNamespace(returncode=0, stdout=json.dumps({"id": f"job-e2e-{counter['value']}", "name": job_name}), stderr="")

    with patch.object(tm_mod.subprocess, "run", side_effect=_fake_cron_run):
        buf = io.StringIO()
        with redirect_stdout(buf):
            tm_mod.watchdog(SimpleNamespace(hours=1.0, run_resumes=True, cooldown_minutes=15))
        executed = json.loads(buf.getvalue())

    resumed_ids = {item["id"] for item in executed["resumed_autonomy"]}
    assert stale_resume_id in resumed_ids
    assert continue_id not in resumed_ids
    assert approval_id not in resumed_ids
    assert done_id not in resumed_ids
    assert executed["resume_failures"] == []

    continue_state = load_autonomy_state(continue_id)
    assert continue_state["active_child"]["kind"] != "openclaw_cron_agent_turn"
    assert continue_state["integrity"]["surface_required"] is True

    done_state = load_autonomy_state(done_id)
    assert done_state["active_child"]["kind"] != "openclaw_cron_agent_turn"
    assert done_state["watchdog"]["final_surface_required"] is True
    assert done_state["watchdog"]["forced_reroute_reason"] == "final_result_not_surfaced"

    stale_resumed_state = load_autonomy_state(stale_resume_id)
    assert stale_resumed_state["active_child"]["kind"] == "openclaw_cron_agent_turn"
    assert stale_resumed_state["watchdog"]["cooldown_until"]

    approval_state = load_autonomy_state(approval_id)
    assert approval_state["watchdog"]["eligible_for_resume"] is False
    assert approval_state["continuation"]["surface_reason"] == "approval_needed"

    # 4b. Leaf/local done does not surface when parent goal remains open and next frontier is known.
    parent_open_id = _create_autonomous_task("tmp autonomy e2e parent-open", "Original child-local next action")
    parent_open_route = _route(
        parent_open_id,
        {
            "status": "done",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "Local implementation slice finished, but parent goal stays open",
            "next_action": "Child-local cleanup",
            "frontier_next_action": "Execute parent integration frontier",
            "done_criteria_met": True,
            "parent_goal_open": True,
            "frontier_known": True,
            "artifact_refs": ["task-manager/test_autonomy_e2e_exhaustive.py"],
        },
    )
    assert parent_open_route["routing"]["router_decision"] == "schedule_next_slice"
    assert parent_open_route["routing"]["surface_reason"] == ""
    assert parent_open_route["routing"]["next_action"] == "Execute parent integration frontier"

    parent_open_show = json.loads(_run("autonomy-show", str(parent_open_id)).stdout)
    assert parent_open_show["continuation"]["parent_goal_open"] is True
    assert parent_open_show["continuation"]["frontier_known"] is True
    assert parent_open_show["continuation"]["frontier_next_action"] == "Execute parent integration frontier"

    parent_open_review = _run(
        "review",
        str(parent_open_id),
        "--note",
        "Attempted surface after leaf-only completion",
        "--next-action",
        "Execute parent integration frontier",
        check=False,
    )
    assert parent_open_review.returncode != 0
    assert "Autonomy delivery gate blocked user-facing transition" in ((parent_open_review.stdout or "") + (parent_open_review.stderr or ""))

    # 4c. Older blocker state is superseded by fresh proof-backed done for the same task.
    supersession_id = _create_autonomous_task("tmp autonomy e2e supersession", "Recover from stale blocker state")
    stale_block_route = _route(
        supersession_id,
        {
            "status": "blocked",
            "outcome_class": "approval_needed",
            "payload_class": "canonical_result",
            "blocked_reason": "Old blocker from prior pass",
            "waiting_is_external": True,
            "approval_needed": True,
            "artifact_refs": ["task-manager/test_autonomy_e2e_exhaustive.py:stale-blocker"],
        },
    )
    assert stale_block_route["routing"]["router_decision"] == "surface_to_user"
    assert stale_block_route["routing"]["surface_reason"] == "approval_needed"

    superseded_done_route = _route(
        supersession_id,
        {
            "status": "done",
            "outcome_class": "terminal_done",
            "payload_class": "canonical_result",
            "summary": "Fresh proof satisfied the parent closure gate",
            "next_action": "",
            "done_criteria_met": True,
            "parent_goal_complete": True,
            "frontier_remaining": False,
            "artifact_refs": ["task-manager/test_autonomy_e2e_exhaustive.py:fresh-proof"],
            "verification_refs": ["python3 task-manager/test_autonomy_e2e_exhaustive.py"],
        },
    )
    assert superseded_done_route["routing"]["router_decision"] == "surface_to_user"
    assert superseded_done_route["routing"]["surface_reason"] == "done"
    supersession_show = json.loads(_run("autonomy-show", str(supersession_id)).stdout)
    assert supersession_show["continuation"]["surface_reason"] == "done"
    assert supersession_show["continuation"]["approval_needed"] is False
    assert supersession_show["continuation"]["goal_complete"] is True

    # 4d. Missing but locally buildable implementation paths stay internal as frontiers instead of surfacing fake blockers.
    implementation_frontier_id = _create_autonomous_task("tmp autonomy e2e implementation frontier", "Build the missing local implementation path")
    implementation_frontier_route = _route(
        implementation_frontier_id,
        {
            "status": "blocked",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "Missing implementation path discovered, but it is locally buildable in this repo",
            "blocked_reason": "Partial implementation only; continue with create/build/verify instead of diagnose-only stop",
            "frontier_next_action": "Build and verify the missing local implementation path",
            "parent_goal_open": True,
            "frontier_known": True,
            "waiting_is_external": False,
            "artifact_refs": ["task-manager/test_autonomy_e2e_exhaustive.py:implementation-frontier"],
        },
    )
    assert implementation_frontier_route["routing"]["router_decision"] == "continue_now"
    assert implementation_frontier_route["routing"]["surface_reason"] == ""
    assert implementation_frontier_route["routing"]["next_action"] == "Build and verify the missing local implementation path"
    implementation_frontier_show = json.loads(_run("autonomy-show", str(implementation_frontier_id)).stdout)
    assert implementation_frontier_show["continuation"]["frontier_known"] is True
    assert implementation_frontier_show["continuation"]["frontier_next_action"] == "Build and verify the missing local implementation path"
    blocked_frontier_review = _run(
        "review",
        str(implementation_frontier_id),
        "--note",
        "Attempted diagnose-only surfacing for a locally buildable gap",
        "--next-action",
        "Build and verify the missing local implementation path",
        check=False,
    )
    assert blocked_frontier_review.returncode != 0
    assert "Autonomy delivery gate blocked user-facing transition" in ((blocked_frontier_review.stdout or "") + (blocked_frontier_review.stderr or ""))

    memory_546_id = _create_autonomous_task("tmp autonomy e2e memory 546 frontier", "Drive the controlled residue sample build/verify slice")
    memory_546_route = _route(
        memory_546_id,
        {
            "status": "blocked",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "#546-style partial implementation exists; lifecycle is specified enough to execute, but the missing implementation path should be built rather than surfaced as a blocker",
            "blocked_reason": "Create/build/verify the controlled residue sample lifecycle slice",
            "frontier_next_action": "Run the controlled residue sample create/build/verify slice",
            "parent_goal_open": True,
            "waiting_is_external": False,
            "artifact_refs": ["task-manager/artifacts/task-546-memory-v1-lifecycle-loop-contract-and-rollout-slice-2026-05-20.md"],
            "verification_refs": ["python3 task-manager/test_autonomy_e2e_exhaustive.py"],
        },
    )
    assert memory_546_route["routing"]["router_decision"] == "continue_now"
    assert memory_546_route["routing"]["surface_reason"] == ""
    assert memory_546_route["routing"]["next_action"] == "Run the controlled residue sample create/build/verify slice"

    # 4e. Invalid payload classes fail closed and never become resumable/deliverable progress.
    invalid_payload_id = _create_autonomous_task("tmp autonomy e2e invalid payload", "Recover from malformed child result")
    invalid_route = _route(
        invalid_payload_id,
        {
            "status": "done",
            "outcome_class": "terminal_done",
            "payload_class": "state_dump",
            "summary": "Fake completion carried as a state dump",
            "done_criteria_met": True,
        },
    )
    assert invalid_route["routing"]["router_decision"] == "escalate_internal"
    assert invalid_route["routing"]["surface_reason"] == ""
    invalid_show = json.loads(_run("autonomy-show", str(invalid_payload_id)).stdout)
    assert invalid_show["last_child_result"]["payload_class"] == "state_dump"
    assert invalid_show["last_child_result"]["outcome_class"] == "terminal_done"
    assert invalid_show["continuation"]["suppressed_surface_count"] >= 1
    assert invalid_show["continuation"]["goal_complete"] is False

    canonicalize_id = _create_autonomous_task("tmp autonomy e2e canonicalize", "Recover from canonicalized raw child output")
    with tempfile.TemporaryDirectory() as tmp:
        child = Path(tmp) / "command-running.txt"
        child.write_text(
            "ACK\n- summary: command-still-running while child is still executing\n- next_action: Wait for durable child completion\n",
            encoding="utf-8",
        )
        command_running_route = json.loads(_run("autonomy-route", str(canonicalize_id), "--child-result-file", str(child)).stdout)
    assert command_running_route["routing"]["router_decision"] == "escalate_internal"
    assert command_running_route["autonomy_state"]["last_child_result"]["payload_class"] == "orchestration_artifact"
    assert command_running_route["autonomy_state"]["continuation"]["suppressed_surface_count"] >= 1

    stale_snapshot_id = _create_autonomous_task("tmp autonomy e2e stale snapshot", "Resume after stale snapshot")
    with tempfile.TemporaryDirectory() as tmp:
        child = Path(tmp) / "stale-snapshot.txt"
        child.write_text(
            "ACK\n- summary: stale snapshot from previous child pass\n- parent_next_action: Resume after stale snapshot\n",
            encoding="utf-8",
        )
        stale_snapshot_route = json.loads(_run("autonomy-route", str(stale_snapshot_id), "--child-result-file", str(child)).stdout)
    assert stale_snapshot_route["routing"]["router_decision"] == "schedule_next_slice"
    assert stale_snapshot_route["autonomy_state"]["last_child_result"]["payload_class"] == "stale_snapshot"
    assert stale_snapshot_route["autonomy_state"]["continuation"]["frontier_next_action"] == "Resume after stale snapshot"

    _age_task(parent_open_id)

    watchdog_after_supersession = json.loads(_run("watchdog", "--hours", "1").stdout)
    resumable_after_supersession = {item["id"] for item in watchdog_after_supersession["resumable_autonomy"]}
    excluded_after_supersession = {item["id"] for item in watchdog_after_supersession["excluded_autonomy"]}
    assert supersession_id not in resumable_after_supersession
    assert supersession_id in excluded_after_supersession

    # 5. Repeated failures hit anti-loop guard and drop out of resumable autonomy.
    failing_id = _create_autonomous_task("tmp autonomy e2e fail", "Retry bounded chain")
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
        failed = tm_mod.autonomy_resume_task_result(
            SimpleNamespace(
                task_id=failing_id,
                hours=1.0,
                cooldown_minutes=1,
                simulate_failure=True,
                failure_class="unit_test_failure",
            )
        )
        assert failed["resumed"] is False
        assert failed["autonomy_state"]["watchdog"]["retry_count"] == expected_retry
        tmp_state = load_autonomy_state(failing_id)
        tmp_state["watchdog"]["cooldown_until"] = ""
        save_autonomy_state(failing_id, tmp_state)
        _age_task(failing_id)

    watchdog_after_failures = json.loads(_run("watchdog", "--hours", "1").stdout)
    resumable_after_failures = {item["id"] for item in watchdog_after_failures["resumable_autonomy"]}
    assert failing_id not in resumable_after_failures
    excluded_failure = next(item for item in watchdog_after_failures["excluded_autonomy"] if item["id"] == failing_id)
    assert excluded_failure["eligible_for_resume"] is True

    watchdog_after_parent_open = json.loads(_run("watchdog", "--hours", "1").stdout)
    resumable_after_parent_open = {item["id"] for item in watchdog_after_parent_open["resumable_autonomy"]}
    excluded_after_parent_open = {item["id"] for item in watchdog_after_parent_open["excluded_autonomy"]}
    assert parent_open_id not in resumable_after_parent_open
    assert parent_open_id in excluded_after_parent_open
    parent_open_excluded = next(item for item in watchdog_after_parent_open["excluded_autonomy"] if item["id"] == parent_open_id)
    assert parent_open_excluded["forced_status_ping_required"] is True
    assert parent_open_excluded["forced_reroute_reason"] == "significant_progress_not_surfaced"

    # 6. Completion gate must score claim/evidence adequacy from recent proof notes, not only a fresh transition note.
    gate_task = {
        "id": 999001,
        "title": "OpenClaw Frame: thin main follow-up — actual main slimming and hard enforcement",
        "details": "",
        "status": "in_progress",
        "next_action": "Move to review/done with closure artifact and focused passing tests",
        "context_json": json.dumps({"links": [], "summary": "", "definition_of_done": []}),
    }
    gate_events = [
        {
            "event_type": "note",
            "note": (
                "claim: bounded slice is complete because main startup prompt assembly now actually uses thin context slimming instead of metadata-only shaping.\n"
                "evidence: agents/hermes-workspace/hermes-agent/agent/prompt_builder.py switches to the thin budget when thin=True, and agents/hermes-workspace/hermes-agent/run_agent.py calls build_context_files_prompt(..., thin=True) on the real main startup path.\n"
                "anchor: task-manager/artifacts/task-481-thin-main-runtime-slimming-closure-2026-05-14.md.\n"
                "verification: pytest tests/run_agent/test_startup_metadata.py tests/agent/test_prompt_builder.py -q -n0 passed.\n"
                "claim_evidence_match: the task title asks for actual main startup/content slimming and hard enforcement; the runtime now uses thin=True in real main prompt assembly and focused tests verify that bounded outcome."
            ),
        }
    ]
    gate = tm_mod.completion_gate_status(gate_task, gate_events)
    assert gate["claim_present"] is True
    assert gate["evidence_present"] is True
    assert gate["verification_present"] is True
    assert gate["anchor_present"] is True
    assert gate["claim_match_present"] is True
    assert gate["adequacy_verdict"] in {"medium", "strong"}

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
