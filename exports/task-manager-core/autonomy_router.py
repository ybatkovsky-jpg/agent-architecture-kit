from __future__ import annotations

from typing import Any

ALLOWED_SURFACE_REASONS = {"done", "blocked_external", "approval_needed", "risk_alert"}
ALLOWED_OUTCOME_CLASSES = {
    "local_progress",
    "frontier_progress",
    "bounded_slice_complete_parent_open",
    "terminal_done",
    "blocked_external",
    "approval_needed",
    "risk_alert",
    "conflict",
    "stale",
}
NON_DELIVERABLE_PAYLOAD_CLASSES = {
    "internal_debug",
    "state_dump",
    "orchestration_artifact",
    "stale_snapshot",
    "command_still_running",
    "command-still-running",
}
TERMINAL_OUTCOME_CLASSES = {"terminal_done", "blocked_external", "approval_needed", "risk_alert"}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _bool(value: Any) -> bool:
    return bool(value)


def _normalize_key(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def _normalize_completion_scope(value: Any) -> str:
    scope = _normalize_key(value) or "unknown"
    if scope not in {"leaf", "child_chain", "parent", "user_goal", "unknown"}:
        return "unknown"
    return scope


def _looks_like_locally_buildable_missing_path(child_result: dict[str, Any]) -> bool:
    text = " ".join(
        [
            _clean_text(child_result.get("summary")),
            _clean_text(child_result.get("blocked_reason") or child_result.get("failure_class")),
            _clean_text(child_result.get("next_action")),
            _clean_text(child_result.get("frontier_next_action") or child_result.get("parent_next_action")),
        ]
    ).lower()
    explicit_signal = any(
        _bool(child_result.get(key))
        for key in {
            "implementation_frontier",
            "missing_implementation_path",
            "locally_buildable",
            "buildable_locally",
        }
    )
    text_signal = any(
        token in text
        for token in {
            "missing implementation path",
            "missing implemented path",
            "not implemented yet",
            "not yet implemented",
            "partial implementation",
            "implementation frontier",
            "build the missing path",
            "create/build/verify",
        }
    )
    false_blocker_signal = any(
        token in text
        for token in {
            "need approval",
            "need user",
            "waiting for user",
            "customer api key",
            "access required",
            "permission required",
            "irreversible",
            "destructive",
            "expensive risk",
        }
    )
    return (explicit_signal or text_signal) and not false_blocker_signal


def _semantic_red_regression_detected(child_result: dict[str, Any]) -> bool:
    if _bool(child_result.get("semantic_red_regression") or child_result.get("switch_to_research_mode")):
        return True
    families = child_result.get("failing_test_families") or child_result.get("semantic_mismatch_families") or []
    if isinstance(families, list) and len([str(x).strip() for x in families if str(x).strip()]) >= 2:
        return True
    try:
        if int(child_result.get("semantic_mismatch_count") or 0) >= 2:
            return True
    except Exception:
        pass
    summary_text = " ".join(
        [
            _clean_text(child_result.get("summary")),
            _clean_text(child_result.get("blocked_reason") or child_result.get("failure_class")),
            _clean_text(child_result.get("next_action")),
        ]
    ).lower()
    return ("semantic mismatch" in summary_text or "contract audit" in summary_text or "research mode" in summary_text) and ("test" in summary_text or "regression" in summary_text)



def route_autonomous_child_completion(
    task: dict[str, Any],
    child_result: dict[str, Any],
    coach_summary: dict[str, Any],
    autonomy_state: dict[str, Any],
) -> dict[str, Any]:
    continuation_state = autonomy_state.get("continuation") if isinstance(autonomy_state.get("continuation"), dict) else {}
    status = _clean_text(child_result.get("status") or child_result.get("child_status")).lower() or "none"
    summary = _clean_text(child_result.get("summary"))
    outcome_class = _normalize_key(child_result.get("outcome_class"))
    payload_class = _normalize_key(child_result.get("payload_class") or child_result.get("result_kind"))
    child_next_action = _clean_text(child_result.get("next_action"))
    next_action = child_next_action or _clean_text(task.get("next_action"))
    frontier_next_action = _clean_text(child_result.get("frontier_next_action") or child_result.get("parent_next_action"))
    blocked_reason = _clean_text(child_result.get("blocked_reason") or child_result.get("failure_class"))
    waiting_is_external = _bool(child_result.get("waiting_is_external") or child_result.get("external_blocker"))
    approval_needed = _bool(child_result.get("approval_needed"))
    risk_alert = _bool(child_result.get("risk_alert"))
    conflicting_children = _bool(child_result.get("conflicting_children"))
    done_criteria_met = _bool(child_result.get("done_criteria_met"))
    parent_goal_open = _bool(child_result.get("parent_goal_open")) or _bool(continuation_state.get("parent_goal_open"))
    parent_goal_complete = _bool(child_result.get("parent_goal_complete")) or (_bool(continuation_state.get("parent_goal_complete")) and not parent_goal_open)
    parent_goal_blocked = _bool(child_result.get("parent_goal_blocked"))
    locally_buildable_missing_path = _looks_like_locally_buildable_missing_path(child_result)
    frontier_known = _bool(child_result.get("frontier_known")) or _bool(continuation_state.get("frontier_known")) or bool(frontier_next_action) or locally_buildable_missing_path
    frontier_remaining = _bool(child_result.get("frontier_remaining")) or parent_goal_open or frontier_known or locally_buildable_missing_path
    frontier_exhausted = not frontier_remaining
    last_completion_scope = _normalize_completion_scope(child_result.get("last_completion_scope")) or ("parent" if parent_goal_complete else ("leaf" if status in {"done", "completed", "review_ready"} else "unknown"))
    if parent_goal_complete:
        parent_goal_open = False
        frontier_remaining = False
        frontier_exhausted = True
    artifact_refs = [str(item).strip() for item in (child_result.get("artifact_refs") or child_result.get("artifacts") or []) if str(item).strip()]
    verification_refs = [str(item).strip() for item in (child_result.get("verification_refs") or []) if str(item).strip()]

    coach_resume_now = _bool(coach_summary.get("resume_now"))
    coach_send_to_user = _bool(coach_summary.get("send_to_user"))
    coach_execution_state = _clean_text(coach_summary.get("execution_state")).lower()
    stale_detected = _bool(child_result.get("stale_autonomous") or child_result.get("stale"))
    autonomy_mode = _bool(autonomy_state.get("autonomy_mode"))
    status_ping_requested = _bool(child_result.get("status_ping") or child_result.get("user_ping") or child_result.get("status_inquiry"))
    semantic_red_regression = _semantic_red_regression_detected(child_result)
    closure_loop_state = autonomy_state.get("closure_loop") if isinstance(autonomy_state.get("closure_loop"), dict) else {}
    current_stage = _clean_text(closure_loop_state.get("execution_stage")) or "idle"
    closure_required = _bool(closure_loop_state.get("closure_required")) or autonomy_mode

    decision = "continue_now"
    decision_reason = "Autonomous task should continue internally until a terminal reason exists."
    surface_reason = ""
    awaiting_user = False
    eligible_for_resume = True
    surface_suppressed = False
    surface_suppressed_reason = ""
    would_have_surfaced_as = ""

    validation_error = ""
    stale_resume_candidate = (
        stale_detected
        and autonomy_mode
        and payload_class in {"stale_snapshot", "orchestration_artifact"}
        and (frontier_next_action or next_action)
    )
    if stale_resume_candidate:
        pass
    elif not outcome_class:
        validation_error = "Child result missing required outcome_class; fail closed internally."
    elif outcome_class not in ALLOWED_OUTCOME_CLASSES:
        validation_error = f"Child result outcome_class '{outcome_class}' is not recognized; fail closed internally."
    elif payload_class in NON_DELIVERABLE_PAYLOAD_CLASSES:
        validation_error = f"Child result payload_class '{payload_class}' is non-deliverable; fail closed internally."
    elif outcome_class == "terminal_done" and not summary:
        validation_error = "Terminal child result outcome_class 'terminal_done' is missing summary; fail closed internally."
    elif outcome_class in {"blocked_external", "approval_needed", "risk_alert"} and not (summary or blocked_reason):
        validation_error = f"Terminal child result outcome_class '{outcome_class}' is missing summary/blocked_reason; fail closed internally."

    if validation_error:
        return {
            "router_decision": "escalate_internal",
            "decision_reason": validation_error,
            "surface_reason": "",
            "next_action": next_action,
            "frontier_next_action": frontier_next_action,
            "awaiting_user": False,
            "approval_needed": False,
            "risk_alert": False,
            "done_criteria_met": False,
            "parent_goal_open": parent_goal_open,
            "parent_goal_complete": False,
            "parent_goal_blocked": False,
            "frontier_known": frontier_known,
            "frontier_remaining": frontier_remaining,
            "frontier_exhausted": False,
            "last_completion_scope": last_completion_scope,
            "surface_suppressed": False,
            "surface_suppressed_reason": "",
            "would_have_surfaced_as": "",
            "eligible_for_resume": False,
            "last_child_result": {
                "status": status,
                "summary": summary,
                "artifact_refs": artifact_refs,
                "verification_refs": verification_refs,
                "outcome_class": outcome_class,
                "payload_class": payload_class,
                "returned_at": _clean_text(child_result.get("returned_at")),
            },
            "inputs": {
                "coach_execution_state": coach_execution_state,
                "coach_send_to_user": coach_send_to_user,
            },
        }

    if risk_alert:
        decision = "surface_to_user"
        surface_reason = "risk_alert"
        decision_reason = blocked_reason or summary or "Risk threshold crossed; user-facing risk alert allowed."
        awaiting_user = True
        eligible_for_resume = False
    elif approval_needed:
        decision = "surface_to_user"
        surface_reason = "approval_needed"
        decision_reason = blocked_reason or "Explicit approval/input is required from the user."
        awaiting_user = True
        eligible_for_resume = False
    elif conflicting_children:
        decision = "escalate_internal"
        decision_reason = "Conflicting child outcomes detected; require internal canonicalization before any surface delivery."
        eligible_for_resume = False
    elif semantic_red_regression:
        decision = "schedule_next_slice"
        next_action = child_next_action or frontier_next_action or "Switch to research/contract-audit mode and reconcile semantic regression before further implementation"
        decision_reason = "Semantic red regression detected across multiple test expectations; switch from implementation to research/contract-audit mode instead of indefinite implementation churn."
    elif locally_buildable_missing_path and not waiting_is_external:
        decision = "continue_now"
        next_action = frontier_next_action or child_next_action or next_action
        decision_reason = "Missing implementation path is locally buildable; treat it as an implementation frontier and continue with create/build/verify instead of surfacing a blocker."
    elif status in {"blocked", "waiting_user"} and waiting_is_external and blocked_reason:
        decision = "surface_to_user"
        surface_reason = "blocked_external"
        decision_reason = blocked_reason
        awaiting_user = True
        eligible_for_resume = False
    elif status in {"done", "completed", "review_ready"} and parent_goal_complete and not parent_goal_blocked and not frontier_remaining:
        decision = "surface_to_user"
        surface_reason = "done"
        decision_reason = summary or "Parent closure criteria are satisfied."
        eligible_for_resume = False
        if last_completion_scope == "unknown":
            last_completion_scope = "parent"
    elif outcome_class == "bounded_slice_complete_parent_open" and parent_goal_open and frontier_remaining:
        decision = "schedule_next_slice"
        next_action = frontier_next_action or next_action
        decision_reason = "Bounded slice completed, parent goal remains open, and the next frontier is known enough to continue autonomously."
        surface_suppressed = True
        surface_suppressed_reason = "bounded_slice_parent_open_frontier_known"
        would_have_surfaced_as = "progress"
        if last_completion_scope == "unknown":
            last_completion_scope = "leaf"
    elif status in {"done", "completed", "review_ready"} and closure_required and done_criteria_met and not parent_goal_complete and not frontier_remaining:
        decision = "run_closure_pass"
        decision_reason = "Bounded slice appears complete enough for a closure audit before any terminal/user-facing stop."
    elif status in {"done", "completed", "review_ready"} and parent_goal_open and frontier_known and frontier_remaining:
        decision = "schedule_next_slice"
        next_action = frontier_next_action or next_action
        decision_reason = "Leaf/local completion remains internal because parent goal is still open and the next frontier is known."
        surface_suppressed = True
        surface_suppressed_reason = "leaf_done_parent_open_frontier_known"
        would_have_surfaced_as = "progress"
    elif status in {"done", "completed", "review_ready"} and parent_goal_open and not frontier_known:
        decision = "escalate_internal"
        decision_reason = "Parent goal remains open, but no canonical next frontier is known; recompute/plan internally instead of surfacing or pretending continuation is ready."
        eligible_for_resume = False
    elif stale_resume_candidate or (stale_detected and autonomy_mode and next_action):
        decision = "schedule_next_slice"
        decision_reason = "Autonomous task is stale but still resumable; schedule another bounded internal pass."
    elif status_ping_requested and autonomy_mode and not awaiting_user and (parent_goal_open or frontier_remaining or frontier_known):
        decision = "continue_now"
        decision_reason = "Non-terminal status inquiry suppressed under autonomous execution because the parent/frontier remains open."
        surface_suppressed = True
        surface_suppressed_reason = "status_ping_non_terminal"
        would_have_surfaced_as = "status_reply"
    elif coach_resume_now and not blocked_reason:
        decision = "continue_now"
        decision_reason = _clean_text(coach_summary.get("resume_reason")) or "Judge requires immediate continuation without user surfacing."
    elif status in {"review_ready", "done", "completed"} and not done_criteria_met:
        decision = "continue_now"
        decision_reason = "Child/local slice finished, but parent DoD is not yet met; keep result internal and continue."
    elif status in {"waiting_user", "blocked"} and not waiting_is_external:
        decision = "continue_now"
        decision_reason = "Waiting/block condition is recoverable internally; do not surface a convenience stop."
    elif coach_send_to_user and not awaiting_user:
        decision = "continue_now"
        decision_reason = "Coach/user-delivery signal suppressed by autonomy gate because no terminal surface reason is present."
        surface_suppressed = True
        if parent_goal_open or frontier_remaining or frontier_known:
            surface_suppressed_reason = "status_ping_non_terminal"
            would_have_surfaced_as = "status_reply"
        else:
            surface_suppressed_reason = "non_terminal_surface_denied"
            would_have_surfaced_as = "progress"
    elif status == "none" and stale_detected and next_action:
        decision = "schedule_next_slice"
        decision_reason = "No active child result and task is stale; resume later via watchdog-safe path."

    if closure_required and current_stage == "closing" and status in {"done", "completed", "review_ready"} and not parent_goal_complete and frontier_remaining:
        decision = "split_followup_task"
        decision_reason = "Closure pass found remaining separable frontier; split follow-up task instead of holding parent open forever."

    if decision == "surface_to_user" and surface_reason == "done":
        next_action = ""

    result = {
        "router_decision": decision,
        "decision_reason": decision_reason,
        "surface_reason": surface_reason,
        "next_action": next_action,
        "frontier_next_action": frontier_next_action,
        "awaiting_user": awaiting_user,
        "approval_needed": approval_needed,
        "risk_alert": risk_alert,
        "done_criteria_met": done_criteria_met,
        "parent_goal_open": parent_goal_open,
        "parent_goal_complete": parent_goal_complete,
        "parent_goal_blocked": parent_goal_blocked,
        "frontier_known": frontier_known,
        "frontier_remaining": frontier_remaining,
        "frontier_exhausted": frontier_exhausted,
        "last_completion_scope": last_completion_scope,
        "surface_suppressed": surface_suppressed,
        "surface_suppressed_reason": surface_suppressed_reason,
        "would_have_surfaced_as": would_have_surfaced_as,
        "eligible_for_resume": eligible_for_resume and decision in {"continue_now", "resume_later", "schedule_next_slice", "run_closure_pass"},
        "last_child_result": {
            "status": status,
            "summary": summary,
            "artifact_refs": artifact_refs,
            "verification_refs": verification_refs,
            "outcome_class": outcome_class,
            "payload_class": payload_class,
            "returned_at": _clean_text(child_result.get("returned_at")),
        },
        "inputs": {
            "coach_execution_state": coach_execution_state,
            "coach_send_to_user": coach_send_to_user,
        },
    }
    if decision == "surface_to_user" and surface_reason not in ALLOWED_SURFACE_REASONS:
        result["router_decision"] = "escalate_internal"
        result["decision_reason"] = "Surface request carried non-terminal reason class; fail closed internally."
        result["surface_reason"] = ""
        result["awaiting_user"] = False
        result["eligible_for_resume"] = False
    if result["router_decision"] == "surface_to_user" and result["surface_reason"] == "done" and not result.get("parent_goal_complete"):
        result["router_decision"] = "escalate_internal"
        result["decision_reason"] = "Surface-to-user done denied: parent goal is not complete."
        result["surface_reason"] = ""
        result["awaiting_user"] = False
        result["eligible_for_resume"] = False
    if result["router_decision"] == "surface_to_user" and result["surface_reason"] == "done" and result.get("frontier_remaining"):
        result["router_decision"] = "escalate_internal"
        result["decision_reason"] = "Surface-to-user done denied: remaining frontier still exists."
        result["surface_reason"] = ""
        result["awaiting_user"] = False
        result["eligible_for_resume"] = False
    if result["router_decision"] == "surface_to_user" and result["surface_reason"] == "done" and result.get("last_completion_scope") not in {"parent", "user_goal"}:
        result["router_decision"] = "escalate_internal"
        result["decision_reason"] = "Surface-to-user done denied: completion scope is below parent/user-goal closure."
        result["surface_reason"] = ""
        result["awaiting_user"] = False
        result["eligible_for_resume"] = False
    if result["router_decision"] in {"continue_now", "resume_later", "schedule_next_slice", "run_closure_pass"} and result.get("surface_suppressed") and not result.get("suppressed_next_frontier"):
        result["suppressed_next_frontier"] = result.get("frontier_next_action") or result.get("next_action") or ""
    if result["router_decision"] in {"continue_now", "resume_later", "schedule_next_slice", "run_closure_pass"} and result.get("surface_suppressed") and not result.get("suppressed_child_status"):
        result["suppressed_child_status"] = status
    if result["router_decision"] in {"continue_now", "resume_later", "schedule_next_slice", "run_closure_pass"} and result.get("surface_suppressed") and not result.get("suppressed_outcome_class"):
        result["suppressed_outcome_class"] = outcome_class
    if result["router_decision"] in {"continue_now", "resume_later", "schedule_next_slice", "run_closure_pass"} and result.get("surface_suppressed") and not result.get("suppressed_payload_class"):
        result["suppressed_payload_class"] = payload_class
    return result
