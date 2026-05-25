from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

TASK_MANAGER_ROOT = Path((os.environ.get("TASK_MANAGER_ROOT") or Path(__file__).resolve().parent)).resolve()
RUNTIME_AUTONOMY_DIR = TASK_MANAGER_ROOT / "runtime" / "autonomy"

ALLOWED_ROUTER_DECISIONS = {
    "continue_now",
    "resume_later",
    "escalate_internal",
    "surface_to_user",
    "schedule_next_slice",
    "split_followup_task",
    "run_closure_pass",
    "none",
}
ALLOWED_SURFACE_REASONS = {"done", "blocked_external", "approval_needed", "risk_alert", ""}
ALLOWED_COMPLETION_SCOPES = {"leaf", "child_chain", "parent", "user_goal", "unknown"}
ALLOWED_EXECUTION_MODES = {
    "none",
    "current_run",
    "spawned_session",
    "openclaw_cron_agent_turn",
    "background_exec",
    "manual_hold",
}
ALLOWED_SURFACE_SUPPRESSION_REASONS = {
    "",
    "leaf_done_parent_open_frontier_known",
    "status_ping_non_terminal",
    "non_terminal_surface_denied",
    "closure_incomplete_parent_frontier_open",
}
ALLOWED_CLOSURE_LOOP_STAGES = {
    "idle",
    "scoping",
    "implementing",
    "verifying",
    "closing",
    "blocked",
    "terminal",
}
ALLOWED_CLOSURE_LOOP_RESULTS = {"unknown", "non_terminal", "terminal", "blocked", "waiting_user"}


def default_autonomy_state(*, task_id: int = 0) -> dict[str, Any]:
    return {
        "task_id": int(task_id or 0),
        "autonomy_mode": False,
        "mode": "manual",
        "delivery_gate": "internal_only_until_terminal",
        "parent_status_at_entry": "",
        "active_child": {
            "kind": "none",
            "id": "",
            "started_at": "",
        },
        "execution": {
            "autonomy_requested": False,
            "autonomy_armed": False,
            "execution_mode": "none",
            "anchor_kind": "",
            "anchor_id": "",
            "requested_at": "",
            "armed_at": "",
            "last_armed_by": "",
            "non_armed_reason": "",
        },
        "last_child_result": {
            "status": "none",
            "summary": "",
            "artifact_refs": [],
            "verification_refs": [],
            "outcome_class": "",
            "payload_class": "",
            "returned_at": "",
        },
        "continuation": {
            "router_decision": "none",
            "decision_reason": "",
            "surface_reason": "",
            "suppression_reason": "",
            "suppressed_surface_count": 0,
            "surface_suppressed": False,
            "surface_suppressed_reason": "",
            "would_have_surfaced_as": "",
            "suppressed_child_status": "",
            "suppressed_outcome_class": "",
            "suppressed_payload_class": "",
            "suppressed_next_frontier": "",
            "last_process_status": "none",
            "goal_complete": False,
            "parent_goal_complete": False,
            "parent_goal_blocked": False,
            "next_action": "",
            "frontier_next_action": "",
            "awaiting_user": False,
            "approval_needed": False,
            "risk_alert": False,
            "done_criteria_met": False,
            "parent_goal_open": False,
            "frontier_known": False,
            "frontier_remaining": False,
            "frontier_exhausted": False,
            "last_completion_scope": "unknown",
        },
        "watchdog": {
            "eligible_for_resume": True,
            "last_resume_check_at": "",
            "resume_after": "",
            "retry_count": 0,
            "last_failure_class": "",
            "cooldown_until": "",
            "last_progress_at": "",
            "last_user_informing_at": "",
            "anti_silence_due_at": "",
            "forced_reroute_reason": "",
            "current_mode": "",
            "step_goal": "",
            "expected_output": "",
            "step_started_at": "",
            "step_due_at": "",
            "if_fail_route": "",
            "last_nudge_at": "",
            "nudge_count": 0,
            "final_surface_required": False,
        },
        "integrity": {
            "last_surface_at": "",
            "last_surface_kind": "",
            "last_progress_note_at": "",
            "progress_note_count": 0,
            "surface_required": False,
            "surface_due_at": "",
            "stale_in_progress_reason": "",
            "orphan_evidence_status": "unknown",
        },
        "closure_loop": {
            "execution_stage": "idle",
            "slice_goal": "",
            "slice_done": False,
            "closure_required": False,
            "followup_split_needed": False,
            "next_slice_required": False,
            "next_slice_reason": "",
            "next_slice_scope": "",
            "last_terminality_check": "",
            "last_terminality_result": "unknown",
        },
        "updated_at": "",
    }


def autonomy_state_path(task_id: int) -> Path:
    return RUNTIME_AUTONOMY_DIR / f"task-{int(task_id)}.json"


def _normalize_bool(value: Any) -> bool:
    return bool(value)


def derive_execution_anchor(state: dict[str, Any] | None) -> dict[str, str]:
    normalized = state if isinstance(state, dict) else {}
    active_child = normalized.get("active_child") if isinstance(normalized.get("active_child"), dict) else {}
    kind = str(active_child.get("kind") or "").strip()
    anchor_id = str(active_child.get("id") or "").strip()
    started_at = str(active_child.get("started_at") or "").strip()
    if kind and kind != "none":
        execution_mode = kind if kind in ALLOWED_EXECUTION_MODES else "spawned_session"
        return {
            "execution_mode": execution_mode,
            "anchor_kind": kind,
            "anchor_id": anchor_id,
            "armed_at": started_at,
        }
    return {
        "execution_mode": "none",
        "anchor_kind": "",
        "anchor_id": "",
        "armed_at": "",
    }


def autonomy_arm_detected(state: dict[str, Any] | None) -> bool:
    normalized = normalize_autonomy_state(state or {})
    execution = normalized.get("execution") or {}
    return bool(execution.get("autonomy_armed"))


def autonomy_requested_but_not_armed(state: dict[str, Any] | None) -> bool:
    normalized = normalize_autonomy_state(state or {})
    execution = normalized.get("execution") or {}
    return bool(execution.get("autonomy_requested")) and not bool(execution.get("autonomy_armed"))


def closure_loop_pending(state: dict[str, Any] | None) -> bool:
    normalized = normalize_autonomy_state(state or {})
    loop = normalized.get("closure_loop") or {}
    return bool(loop.get("closure_required")) and str(loop.get("execution_stage") or "idle") != "terminal"


def terminality_decision_required(state: dict[str, Any] | None) -> bool:
    normalized = normalize_autonomy_state(state or {})
    loop = normalized.get("closure_loop") or {}
    return bool(loop.get("closure_required")) and bool(loop.get("slice_done")) and str(loop.get("last_terminality_result") or "unknown") == "unknown"


def next_slice_missing(state: dict[str, Any] | None) -> bool:
    normalized = normalize_autonomy_state(state or {})
    loop = normalized.get("closure_loop") or {}
    if not bool(loop.get("next_slice_required")):
        return False
    return not str(loop.get("next_slice_scope") or "").strip()


def normalize_autonomy_state(payload: dict[str, Any] | None, *, task_id: int = 0) -> dict[str, Any]:
    base = default_autonomy_state(task_id=task_id)
    if isinstance(payload, dict):
        base.update(payload)
    base["task_id"] = int(base.get("task_id") or task_id or 0)
    base["autonomy_mode"] = _normalize_bool(base.get("autonomy_mode"))
    raw_mode = str(base.get("mode") or "").strip()
    base["mode"] = "autonomous_until_done" if (base["autonomy_mode"] or raw_mode == "autonomous_until_done") else "manual"
    base["autonomy_mode"] = base["mode"] == "autonomous_until_done"
    base["delivery_gate"] = str(base.get("delivery_gate") or "internal_only_until_terminal").strip() or "internal_only_until_terminal"
    base["parent_status_at_entry"] = str(base.get("parent_status_at_entry") or "").strip()

    active_child = base.get("active_child") if isinstance(base.get("active_child"), dict) else {}
    base["active_child"] = {
        "kind": str(active_child.get("kind") or "none").strip() or "none",
        "id": str(active_child.get("id") or "").strip(),
        "started_at": str(active_child.get("started_at") or "").strip(),
    }

    execution = base.get("execution") if isinstance(base.get("execution"), dict) else {}
    inferred_anchor = derive_execution_anchor(base)
    requested = _normalize_bool(execution.get("autonomy_requested"))
    armed = _normalize_bool(execution.get("autonomy_armed"))
    execution_mode = str(execution.get("execution_mode") or "none").strip() or "none"
    if execution_mode not in ALLOWED_EXECUTION_MODES:
        execution_mode = "none"
    anchor_kind = str(execution.get("anchor_kind") or "").strip()
    anchor_id = str(execution.get("anchor_id") or "").strip()
    requested_at = str(execution.get("requested_at") or "").strip()
    armed_at = str(execution.get("armed_at") or "").strip()
    last_armed_by = str(execution.get("last_armed_by") or "").strip()
    non_armed_reason = str(execution.get("non_armed_reason") or "").strip()

    if base["autonomy_mode"]:
        requested = True if requested or base["autonomy_mode"] else requested
        if inferred_anchor["anchor_kind"] and inferred_anchor["anchor_id"]:
            armed = True
            execution_mode = inferred_anchor["execution_mode"]
            anchor_kind = inferred_anchor["anchor_kind"]
            anchor_id = inferred_anchor["anchor_id"]
            armed_at = armed_at or inferred_anchor["armed_at"]
            non_armed_reason = ""
        elif not armed:
            execution_mode = execution_mode if execution_mode in ALLOWED_EXECUTION_MODES else "none"
            if execution_mode == "none":
                non_armed_reason = non_armed_reason or "autonomy_requested_without_live_anchor"
    else:
        requested = False
        armed = False
        execution_mode = "none"
        anchor_kind = ""
        anchor_id = ""
        armed_at = ""
        last_armed_by = ""
        non_armed_reason = ""

    base["execution"] = {
        "autonomy_requested": requested,
        "autonomy_armed": armed,
        "execution_mode": execution_mode,
        "anchor_kind": anchor_kind,
        "anchor_id": anchor_id,
        "requested_at": requested_at,
        "armed_at": armed_at,
        "last_armed_by": last_armed_by,
        "non_armed_reason": non_armed_reason,
    }

    last_child_result = base.get("last_child_result") if isinstance(base.get("last_child_result"), dict) else {}
    base["last_child_result"] = {
        "status": str(last_child_result.get("status") or "none").strip() or "none",
        "summary": str(last_child_result.get("summary") or "").strip(),
        "artifact_refs": [str(item).strip() for item in (last_child_result.get("artifact_refs") or []) if str(item).strip()],
        "verification_refs": [str(item).strip() for item in (last_child_result.get("verification_refs") or []) if str(item).strip()],
        "outcome_class": str(last_child_result.get("outcome_class") or "").strip(),
        "payload_class": str(last_child_result.get("payload_class") or "").strip(),
        "returned_at": str(last_child_result.get("returned_at") or "").strip(),
    }

    continuation = base.get("continuation") if isinstance(base.get("continuation"), dict) else {}
    router_decision = str(continuation.get("router_decision") or "none").strip() or "none"
    if router_decision not in ALLOWED_ROUTER_DECISIONS:
        router_decision = "none"
    surface_reason = str(continuation.get("surface_reason") or "").strip()
    if surface_reason not in ALLOWED_SURFACE_REASONS:
        surface_reason = ""
    normalized_parent_goal_complete = _normalize_bool(continuation.get("parent_goal_complete"))
    normalized_parent_goal_open = _normalize_bool(continuation.get("parent_goal_open"))
    if normalized_parent_goal_complete:
        normalized_parent_goal_open = False
    last_completion_scope = str(continuation.get("last_completion_scope") or "unknown").strip() or "unknown"
    if last_completion_scope not in ALLOWED_COMPLETION_SCOPES:
        last_completion_scope = "unknown"

    normalized_next_action = str(continuation.get("next_action") or "").strip()
    normalized_frontier_next_action = str(continuation.get("frontier_next_action") or "").strip()
    awaiting_user = _normalize_bool(continuation.get("awaiting_user"))
    approval_needed = _normalize_bool(continuation.get("approval_needed"))
    risk_alert = _normalize_bool(continuation.get("risk_alert"))
    parent_goal_blocked = _normalize_bool(continuation.get("parent_goal_blocked"))
    frontier_known = _normalize_bool(continuation.get("frontier_known"))
    frontier_remaining = _normalize_bool(continuation.get("frontier_remaining"))
    frontier_exhausted = _normalize_bool(continuation.get("frontier_exhausted"))
    if normalized_parent_goal_complete:
        frontier_known = False
        frontier_remaining = False
        frontier_exhausted = True

    has_resumable_frontier_signal = bool(normalized_frontier_next_action or normalized_next_action)
    has_terminal_surface = router_decision == "surface_to_user" and surface_reason in {"done", "blocked_external", "approval_needed", "risk_alert"}
    if (
        base["autonomy_mode"]
        and has_resumable_frontier_signal
        and not normalized_parent_goal_complete
        and not parent_goal_blocked
        and not has_terminal_surface
        and not awaiting_user
        and not approval_needed
        and not risk_alert
    ):
        normalized_parent_goal_open = True
        frontier_known = True
        frontier_remaining = True
        frontier_exhausted = False

    normalized_surface_suppressed = _normalize_bool(continuation.get("surface_suppressed"))
    normalized_surface_suppressed_reason = (
        str(continuation.get("surface_suppressed_reason") or "").strip()
        if str(continuation.get("surface_suppressed_reason") or "").strip() in ALLOWED_SURFACE_SUPPRESSION_REASONS
        else ""
    )
    normalized_would_have_surfaced_as = str(continuation.get("would_have_surfaced_as") or "").strip()
    normalized_decision_reason = str(continuation.get("decision_reason") or "").strip()
    closure_incomplete = False
    if base["autonomy_mode"] and surface_reason == "done":
        scope_allows_done_surface = last_completion_scope in {"parent", "user_goal"}
        frontier_still_open = normalized_parent_goal_open or frontier_remaining or has_resumable_frontier_signal
        if (not normalized_parent_goal_complete) or parent_goal_blocked or frontier_still_open or (not scope_allows_done_surface):
            closure_incomplete = True
            router_decision = "continue_now"
            surface_reason = ""
            has_terminal_surface = False
            normalized_surface_suppressed = True
            normalized_surface_suppressed_reason = "closure_incomplete_parent_frontier_open"
            normalized_would_have_surfaced_as = "done"
            frontier_exhausted = False
            if not parent_goal_blocked:
                normalized_parent_goal_open = True
                frontier_known = frontier_known or has_resumable_frontier_signal
                frontier_remaining = True
            normalized_decision_reason = (
                normalized_decision_reason
                or "Autonomous closure remains incomplete: local success cannot surface as done while parent/user-goal frontier is still open."
            )

    base["continuation"] = {
        "router_decision": router_decision,
        "decision_reason": normalized_decision_reason,
        "surface_reason": surface_reason,
        "suppression_reason": str(continuation.get("suppression_reason") or "").strip(),
        "suppressed_surface_count": max(0, int(continuation.get("suppressed_surface_count") or 0)),
        "surface_suppressed": normalized_surface_suppressed,
        "surface_suppressed_reason": normalized_surface_suppressed_reason,
        "would_have_surfaced_as": normalized_would_have_surfaced_as,
        "suppressed_child_status": str(continuation.get("suppressed_child_status") or "").strip(),
        "suppressed_outcome_class": str(continuation.get("suppressed_outcome_class") or "").strip(),
        "suppressed_payload_class": str(continuation.get("suppressed_payload_class") or "").strip(),
        "suppressed_next_frontier": str(continuation.get("suppressed_next_frontier") or "").strip(),
        "last_process_status": str(continuation.get("last_process_status") or "none").strip() or "none",
        "goal_complete": _normalize_bool(continuation.get("goal_complete")),
        "parent_goal_complete": normalized_parent_goal_complete,
        "parent_goal_blocked": parent_goal_blocked,
        "next_action": normalized_next_action,
        "frontier_next_action": normalized_frontier_next_action,
        "awaiting_user": awaiting_user,
        "approval_needed": approval_needed,
        "risk_alert": risk_alert,
        "done_criteria_met": _normalize_bool(continuation.get("done_criteria_met")),
        "parent_goal_open": normalized_parent_goal_open,
        "frontier_known": frontier_known,
        "frontier_remaining": frontier_remaining,
        "frontier_exhausted": frontier_exhausted,
        "last_completion_scope": last_completion_scope,
    }

    watchdog = base.get("watchdog") if isinstance(base.get("watchdog"), dict) else {}
    try:
        retry_count = int(watchdog.get("retry_count") or 0)
    except Exception:
        retry_count = 0
    try:
        nudge_count = int(watchdog.get("nudge_count") or 0)
    except Exception:
        nudge_count = 0
    base["watchdog"] = {
        "eligible_for_resume": _normalize_bool(watchdog.get("eligible_for_resume", True)),
        "last_resume_check_at": str(watchdog.get("last_resume_check_at") or "").strip(),
        "resume_after": str(watchdog.get("resume_after") or "").strip(),
        "retry_count": retry_count,
        "last_failure_class": str(watchdog.get("last_failure_class") or "").strip(),
        "cooldown_until": str(watchdog.get("cooldown_until") or "").strip(),
        "last_progress_at": str(watchdog.get("last_progress_at") or "").strip(),
        "last_user_informing_at": str(watchdog.get("last_user_informing_at") or "").strip(),
        "last_external_progress_ping_at": str(watchdog.get("last_external_progress_ping_at") or "").strip(),
        "last_external_progress_ping_fingerprint": str(watchdog.get("last_external_progress_ping_fingerprint") or "").strip(),
        "anti_silence_due_at": str(watchdog.get("anti_silence_due_at") or "").strip(),
        "forced_reroute_reason": str(watchdog.get("forced_reroute_reason") or "").strip(),
        "current_mode": str(watchdog.get("current_mode") or "").strip(),
        "step_goal": str(watchdog.get("step_goal") or "").strip(),
        "expected_output": str(watchdog.get("expected_output") or "").strip(),
        "step_started_at": str(watchdog.get("step_started_at") or "").strip(),
        "step_due_at": str(watchdog.get("step_due_at") or "").strip(),
        "if_fail_route": str(watchdog.get("if_fail_route") or "").strip(),
        "last_nudge_at": str(watchdog.get("last_nudge_at") or "").strip(),
        "nudge_count": max(0, nudge_count),
        "final_surface_required": _normalize_bool(watchdog.get("final_surface_required")),
    }

    integrity = base.get("integrity") if isinstance(base.get("integrity"), dict) else {}
    try:
        progress_note_count = int(integrity.get("progress_note_count") or 0)
    except Exception:
        progress_note_count = 0
    orphan_evidence_status = str(integrity.get("orphan_evidence_status") or "unknown").strip() or "unknown"
    if orphan_evidence_status not in {"unknown", "integrity_ok", "needs_surface", "orphan_evidence_suspected", "task_binding_missing"}:
        orphan_evidence_status = "unknown"
    base["integrity"] = {
        "last_surface_at": str(integrity.get("last_surface_at") or "").strip(),
        "last_surface_kind": str(integrity.get("last_surface_kind") or "").strip(),
        "last_progress_note_at": str(integrity.get("last_progress_note_at") or "").strip(),
        "progress_note_count": max(0, progress_note_count),
        "surface_required": _normalize_bool(integrity.get("surface_required")),
        "surface_due_at": str(integrity.get("surface_due_at") or "").strip(),
        "stale_in_progress_reason": str(integrity.get("stale_in_progress_reason") or "").strip(),
        "orphan_evidence_status": orphan_evidence_status,
    }

    closure_loop = base.get("closure_loop") if isinstance(base.get("closure_loop"), dict) else {}
    execution_stage = str(closure_loop.get("execution_stage") or "idle").strip() or "idle"
    if execution_stage not in ALLOWED_CLOSURE_LOOP_STAGES:
        execution_stage = "idle"
    last_terminality_result = str(closure_loop.get("last_terminality_result") or "unknown").strip() or "unknown"
    if last_terminality_result not in ALLOWED_CLOSURE_LOOP_RESULTS:
        last_terminality_result = "unknown"
    closure_required = _normalize_bool(closure_loop.get("closure_required"))
    slice_done = _normalize_bool(closure_loop.get("slice_done"))
    followup_split_needed = _normalize_bool(closure_loop.get("followup_split_needed"))
    next_slice_required = _normalize_bool(closure_loop.get("next_slice_required"))
    if base["autonomy_mode"] and execution_stage != "terminal":
        closure_required = True
    if slice_done and execution_stage not in {"terminal", "blocked"} and last_terminality_result == "non_terminal":
        next_slice_required = True
    if execution_stage == "terminal":
        closure_required = False
        next_slice_required = False
        followup_split_needed = False
    base["closure_loop"] = {
        "execution_stage": execution_stage,
        "slice_goal": str(closure_loop.get("slice_goal") or "").strip(),
        "slice_done": slice_done,
        "closure_required": closure_required,
        "followup_split_needed": followup_split_needed,
        "next_slice_required": next_slice_required,
        "next_slice_reason": str(closure_loop.get("next_slice_reason") or "").strip(),
        "next_slice_scope": str(closure_loop.get("next_slice_scope") or "").strip(),
        "last_terminality_check": str(closure_loop.get("last_terminality_check") or "").strip(),
        "last_terminality_result": last_terminality_result,
    }
    base["updated_at"] = str(base.get("updated_at") or "").strip()
    return base


def load_autonomy_state(task_id: int) -> dict[str, Any]:
    path = autonomy_state_path(task_id)
    if not path.exists():
        return default_autonomy_state(task_id=task_id)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
    if not isinstance(payload, dict):
        payload = {}
    return normalize_autonomy_state(payload, task_id=task_id)


def save_autonomy_state(task_id: int, state: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_autonomy_state(state, task_id=task_id)
    path = autonomy_state_path(task_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return normalized


def autonomy_surface_allowed(state: dict[str, Any] | None) -> bool:
    normalized = normalize_autonomy_state(state or {})
    if not normalized.get("autonomy_mode"):
        return True
    continuation = normalized.get("continuation") or {}
    return (
        continuation.get("router_decision") == "surface_to_user"
        and str(continuation.get("surface_reason") or "") in {"done", "blocked_external", "approval_needed", "risk_alert"}
    )
