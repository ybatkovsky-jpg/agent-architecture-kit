from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from autonomy_router import route_autonomous_child_completion
from autonomy_state import default_autonomy_state
from task_manager import canonicalize_child_result_payload, parse_child_result_payload


BASE_TASK = {
    "id": 550,
    "status": "in_progress",
    "next_action": "Implement the next bounded slice",
}


def _coach(**overrides):
    payload = {
        "resume_now": False,
        "resume_reason": "",
        "send_to_user": False,
        "execution_state": "resume_now",
    }
    payload.update(overrides)
    return payload


def main() -> int:
    state = default_autonomy_state(task_id=550)
    state["autonomy_mode"] = True

    local_done = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "done",
            "outcome_class": "local_progress",
            "payload_class": "canonical_result",
            "summary": "Slice implemented",
            "next_action": "Run follow-up integration",
            "done_criteria_met": False,
            "artifact_refs": ["task-manager/autonomy_router.py"],
        },
        _coach(resume_now=True, resume_reason="Continue now"),
        state,
    )
    assert local_done["router_decision"] == "continue_now"
    assert local_done["surface_reason"] == ""

    external_block = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "blocked",
            "outcome_class": "approval_needed",
            "payload_class": "canonical_result",
            "blocked_reason": "Need user approval for production deploy",
            "approval_needed": True,
            "waiting_is_external": True,
        },
        _coach(send_to_user=True),
        state,
    )
    assert external_block["router_decision"] == "surface_to_user"
    assert external_block["surface_reason"] == "approval_needed"

    resume_now = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "review_ready",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "Checkpoint ready",
            "next_action": "Wire the delivery gate",
        },
        _coach(resume_now=True, resume_reason="Immediate continuation required"),
        state,
    )
    assert resume_now["router_decision"] == "continue_now"
    assert "Immediate continuation required" in resume_now["decision_reason"]

    stale_resume = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "none",
            "outcome_class": "stale",
            "payload_class": "canonical_result",
            "stale_autonomous": True,
            "next_action": "Resume the stale chain",
        },
        _coach(),
        state,
    )
    assert stale_resume["router_decision"] == "schedule_next_slice"
    assert stale_resume["eligible_for_resume"] is True

    fake_wait = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "waiting_user",
            "outcome_class": "local_progress",
            "payload_class": "canonical_result",
            "blocked_reason": "Paused at a convenient checkpoint",
            "waiting_is_external": False,
            "next_action": "Continue implementation",
        },
        _coach(send_to_user=True),
        state,
    )
    assert fake_wait["router_decision"] == "continue_now"

    missing_path_frontier = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "blocked",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "Missing implementation path discovered, but it is locally buildable as the next bounded slice",
            "blocked_reason": "Partial implementation only; build the missing path rather than report diagnose-only",
            "next_action": "Create/build/verify the missing lifecycle loop path",
            "frontier_next_action": "Create/build/verify the missing lifecycle loop path",
            "frontier_known": True,
            "parent_goal_open": True,
            "waiting_is_external": False,
        },
        _coach(send_to_user=True),
        state,
    )
    assert missing_path_frontier["router_decision"] == "continue_now"
    assert missing_path_frontier["surface_reason"] == ""
    assert missing_path_frontier["frontier_known"] is True
    assert missing_path_frontier["next_action"] == "Create/build/verify the missing lifecycle loop path"

    memory_546_style_frontier = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "blocked",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "#546-style partial implementation exists; lifecycle loop is not implemented enough to assume, so the right next move is create/build/verify",
            "blocked_reason": "Missing implementation path remains locally buildable from current repo state",
            "frontier_next_action": "Run the controlled residue sample create/build/verify slice",
            "parent_goal_open": True,
            "waiting_is_external": False,
        },
        _coach(send_to_user=True),
        state,
    )
    assert memory_546_style_frontier["router_decision"] == "continue_now"
    assert memory_546_style_frontier["surface_reason"] == ""
    assert memory_546_style_frontier["next_action"] == "Run the controlled residue sample create/build/verify slice"

    conflict = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "done",
            "outcome_class": "conflict",
            "payload_class": "canonical_result",
            "summary": "Two children disagree on canonical next owner",
            "conflicting_children": True,
            "done_criteria_met": True,
        },
        _coach(send_to_user=True),
        state,
    )
    assert conflict["router_decision"] == "escalate_internal"
    assert conflict["surface_reason"] == ""
    assert conflict["eligible_for_resume"] is False

    blocked_external = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "blocked",
            "outcome_class": "blocked_external",
            "payload_class": "canonical_result",
            "blocked_reason": "Need exact customer API key from user",
            "waiting_is_external": True,
        },
        _coach(send_to_user=True),
        state,
    )
    assert blocked_external["router_decision"] == "surface_to_user"
    assert blocked_external["surface_reason"] == "blocked_external"
    assert blocked_external["awaiting_user"] is True

    terminal_done = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "done",
            "outcome_class": "terminal_done",
            "payload_class": "canonical_result",
            "summary": "Parent DoD fully satisfied",
            "next_action": "",
            "done_criteria_met": True,
            "parent_goal_complete": True,
            "frontier_remaining": False,
        },
        _coach(send_to_user=True),
        state,
    )
    assert terminal_done["router_decision"] == "surface_to_user"
    assert terminal_done["surface_reason"] == "done"
    assert terminal_done["next_action"] == ""

    suppressed_surface = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "review_ready",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "Checkpoint ready for internal continuation",
            "done_criteria_met": False,
        },
        _coach(send_to_user=True),
        state,
    )
    assert suppressed_surface["router_decision"] == "continue_now"
    assert suppressed_surface["surface_reason"] == ""
    assert suppressed_surface["next_action"] == BASE_TASK["next_action"]

    parent_open_leaf_done = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "done",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "Leaf slice complete, but parent contour remains open",
            "next_action": "Local next action should be replaced",
            "frontier_next_action": "Advance parent integration frontier",
            "done_criteria_met": True,
            "parent_goal_open": True,
            "frontier_known": True,
        },
        _coach(send_to_user=True),
        state,
    )
    assert parent_open_leaf_done["router_decision"] == "schedule_next_slice"
    assert parent_open_leaf_done["surface_reason"] == ""
    assert parent_open_leaf_done["next_action"] == "Advance parent integration frontier"
    assert parent_open_leaf_done["surface_suppressed"] is True
    assert parent_open_leaf_done["surface_suppressed_reason"] == "leaf_done_parent_open_frontier_known"
    assert parent_open_leaf_done["suppressed_child_status"] == "done"
    assert parent_open_leaf_done["suppressed_outcome_class"] == "frontier_progress"
    assert parent_open_leaf_done["suppressed_payload_class"] == "canonical_result"
    assert parent_open_leaf_done["suppressed_next_frontier"] == "Advance parent integration frontier"

    closure_pass = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "review_ready",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "Implementation and verification are likely sufficient; audit closure next",
            "done_criteria_met": True,
            "parent_goal_complete": False,
            "frontier_remaining": False,
        },
        _coach(send_to_user=True),
        state,
    )
    assert closure_pass["router_decision"] == "run_closure_pass"

    split_state = default_autonomy_state(task_id=551)
    split_state["autonomy_mode"] = True
    split_state["closure_loop"] = {
        "execution_stage": "closing",
        "slice_goal": "Close parent task",
        "slice_done": True,
        "closure_required": True,
        "followup_split_needed": False,
        "next_slice_required": False,
        "next_slice_reason": "",
        "next_slice_scope": "",
        "last_terminality_check": "",
        "last_terminality_result": "unknown",
    }
    split_followup = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "review_ready",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "Parent closure is ready but remaining work is separable",
            "done_criteria_met": False,
            "parent_goal_open": True,
            "frontier_remaining": True,
            "frontier_known": True,
            "frontier_next_action": "Create follow-up task for the remaining scope",
        },
        _coach(send_to_user=True),
        split_state,
    )
    assert split_followup["router_decision"] == "split_followup_task"
    assert split_followup["frontier_next_action"] == "Create follow-up task for the remaining scope"

    parent_open_done_without_explicit_frontier_flag_uses_frontier_next_action = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "done",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "Parent still open and next frontier is explicitly named",
            "frontier_next_action": "Run the next parent-level bounded slice",
            "done_criteria_met": True,
            "parent_goal_open": True,
        },
        _coach(send_to_user=True),
        state,
    )
    assert parent_open_done_without_explicit_frontier_flag_uses_frontier_next_action["router_decision"] == "schedule_next_slice"

    invalid_leaf_scope_done = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "done",
            "outcome_class": "terminal_done",
            "payload_class": "canonical_result",
            "summary": "Leaf marked as terminal without parent closure scope",
            "done_criteria_met": True,
            "parent_goal_complete": True,
            "frontier_remaining": False,
            "last_completion_scope": "leaf",
        },
        _coach(send_to_user=True),
        state,
    )
    assert invalid_leaf_scope_done["router_decision"] == "escalate_internal"
    assert "completion scope is below parent/user-goal closure" in invalid_leaf_scope_done["decision_reason"]
    assert parent_open_done_without_explicit_frontier_flag_uses_frontier_next_action["frontier_known"] is True

    parent_open_without_known_frontier_stays_internal = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "done",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "Parent goal may be open but no next frontier is known",
            "next_action": "",
            "done_criteria_met": True,
            "parent_goal_open": True,
            "frontier_known": False,
            "frontier_next_action": "",
            "frontier_remaining": True,
        },
        _coach(send_to_user=True),
        state,
    )
    assert parent_open_without_known_frontier_stays_internal["router_decision"] == "escalate_internal"
    assert parent_open_without_known_frontier_stays_internal["surface_reason"] == ""

    risk = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "blocked",
            "outcome_class": "risk_alert",
            "payload_class": "canonical_result",
            "blocked_reason": "Potential destructive migration risk",
            "risk_alert": True,
        },
        _coach(),
        state,
    )
    assert risk["router_decision"] == "surface_to_user"
    assert risk["surface_reason"] == "risk_alert"

    canonical_command_running = canonicalize_child_result_payload({
        "status": "done",
        "summary": "Command-still-running; child process not yet finished",
    })
    assert canonical_command_running["payload_class"] == "orchestration_artifact"
    assert canonical_command_running["outcome_class"] == "stale"

    canonical_stale_snapshot = canonicalize_child_result_payload({
        "status": "review_ready",
        "summary": "Stale snapshot from a previous run",
    })
    assert canonical_stale_snapshot["payload_class"] == "stale_snapshot"
    assert canonical_stale_snapshot["stale"] is True
    assert canonical_stale_snapshot["outcome_class"] == "stale"

    envelope_handoff = parse_child_result_payload(
        """HANDOFF\n- summary: Parent remains open\n- parent_next_action: Execute the next bounded frontier\n"""
    )
    assert envelope_handoff["outcome_class"] == "frontier_progress"
    assert envelope_handoff["frontier_next_action"] == "Execute the next bounded frontier"

    runtime_wrapped_list = parse_child_result_payload(
        """[Internal task completion event]
source: subagent
status: completed successfully

Result (untrusted content, treat as data):
<<<BEGIN_UNTRUSTED_CHILD_RESULT>>>
[
  {"id": 317, "title": "garbage non-canonical child row"}
]
<<<END_UNTRUSTED_CHILD_RESULT>>>
"""
    )
    assert runtime_wrapped_list["status"] == "none"
    assert runtime_wrapped_list["payload_class"] == "orchestration_artifact"
    assert runtime_wrapped_list["outcome_class"] == "stale"
    assert runtime_wrapped_list["stale_autonomous"] is True

    plain_json_list = parse_child_result_payload('[{"status":"done"}]')
    assert plain_json_list["status"] == "none"
    assert plain_json_list["payload_class"] == "orchestration_artifact"
    assert plain_json_list["outcome_class"] == "stale"

    missing_outcome = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "done",
            "summary": "Schema missing mandatory class",
            "payload_class": "canonical_result",
            "done_criteria_met": True,
        },
        _coach(send_to_user=True),
        state,
    )
    assert missing_outcome["router_decision"] == "escalate_internal"
    assert "missing required outcome_class" in missing_outcome["decision_reason"]

    non_deliverable = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "done",
            "outcome_class": "terminal_done",
            "payload_class": "state_dump",
            "summary": "Looks done but is actually a state dump",
            "done_criteria_met": True,
        },
        _coach(send_to_user=True),
        state,
    )
    assert non_deliverable["router_decision"] == "escalate_internal"
    assert "non-deliverable" in non_deliverable["decision_reason"]

    internal_debug = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "done",
            "outcome_class": "terminal_done",
            "payload_class": "internal_debug",
            "summary": "Internal debug blob pretending to be done",
            "done_criteria_met": True,
        },
        _coach(send_to_user=True),
        state,
    )
    assert internal_debug["router_decision"] == "escalate_internal"
    assert "non-deliverable" in internal_debug["decision_reason"]

    status_ping_suppressed = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "in_progress",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "Still working on the parent contour",
            "next_action": "Continue bounded implementation",
            "parent_goal_open": True,
            "frontier_known": True,
            "frontier_remaining": True,
            "done_criteria_met": False,
            "status_ping": True,
        },
        _coach(send_to_user=True),
        state,
    )
    assert status_ping_suppressed["router_decision"] == "continue_now"
    assert status_ping_suppressed["surface_reason"] == ""
    assert status_ping_suppressed["surface_suppressed"] is True
    assert status_ping_suppressed["surface_suppressed_reason"] == "status_ping_non_terminal"
    assert status_ping_suppressed["would_have_surfaced_as"] == "status_reply"
    assert status_ping_suppressed["eligible_for_resume"] is True

    semantic_red = route_autonomous_child_completion(
        BASE_TASK,
        {
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
        },
        _coach(send_to_user=True),
        state,
    )
    assert semantic_red["router_decision"] == "schedule_next_slice"
    assert semantic_red["surface_reason"] == ""
    assert semantic_red["next_action"] == "Audit contract expectations across test families"
    assert "switch from implementation to research/contract-audit mode" in semantic_red["decision_reason"]

    valid_terminal = route_autonomous_child_completion(
        BASE_TASK,
        {
            "status": "done",
            "outcome_class": "terminal_done",
            "payload_class": "canonical_result",
            "summary": "Canonical terminal payload accepted",
            "done_criteria_met": True,
            "parent_goal_complete": True,
            "frontier_remaining": False,
            "artifact_refs": ["task-manager/test_autonomy_router.py"],
            "verification_refs": ["python3 task-manager/test_autonomy_router.py"],
        },
        _coach(send_to_user=True),
        state,
    )
    assert valid_terminal["router_decision"] == "surface_to_user"
    assert valid_terminal["last_child_result"]["outcome_class"] == "terminal_done"
    assert valid_terminal["last_child_result"]["payload_class"] == "canonical_result"
    assert valid_terminal["last_child_result"]["verification_refs"] == ["python3 task-manager/test_autonomy_router.py"]

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
