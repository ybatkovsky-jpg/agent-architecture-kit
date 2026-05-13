#!/usr/bin/env python3
"""Bounded continuation verifier v0.

Checks compact continuation fixtures against the OpenClaw Frame continuation
contract and emits machine-readable verdicts.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_DIR = ROOT / "scripts/architecture/fixtures/continuation_verifier"
SCHEMA_VERSION = "continuation_verdict/v0"
TOOL_VERSION = "0.1.0"
ALLOWED_STATES = {"PREPARED", "ACK", "RUNNING", "DONE", "BLOCKED"}
TERMINAL_STATES = {"DONE", "BLOCKED"}
ALLOWED_TRANSITIONS = {
    ("PREPARED", "ACK"),
    ("ACK", "RUNNING"),
    ("RUNNING", "DONE"),
    ("RUNNING", "BLOCKED"),
    ("PREPARED", "BLOCKED"),
}


REQUIRED_HANDOFF_FIELDS = [
    "handoff_id",
    "parent_task_id",
    "continuation_scope",
    "execution_owner_target",
    "decision_owner",
    "resume_basis",
    "expected_next_step",
    "return_target",
    "created_at",
    "created_by",
]
REQUIRED_TRIGGER_FIELDS = [
    "resume_trigger_id",
    "handoff_id",
    "trigger_type",
    "trigger_summary",
    "basis_anchor",
    "authorized_by",
    "triggered_at",
]
REQUIRED_CONTINUATION_FIELDS = [
    "continuation_id",
    "handoff_id",
    "resume_trigger_id",
    "status",
    "execution_owner",
    "decision_owner",
    "scope",
    "resume_basis_snapshot",
    "started_at",
]
REQUIRED_RETURN_FIELDS = [
    "return_id",
    "continuation_id",
    "handoff_id",
    "status",
    "execution_owner",
    "decision_owner",
    "summary",
    "next_action",
    "returned_at",
]
REQUIRED_DONE_FIELDS = ["durable_result_anchor", "result_kind"]
REQUIRED_BLOCKED_FIELDS = ["blocked_reason", "owner_for_decision", "recovery_suggestion"]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def add_issue(issues: list[dict[str, Any]], severity: str, code: str, message: str, path: str | None = None) -> None:
    item = {"severity": severity, "code": code, "message": message}
    if path:
        item["path"] = path
    issues.append(item)


def require_fields(obj: dict[str, Any] | None, fields: list[str], base_path: str, issues: list[dict[str, Any]], severity: str = "error") -> None:
    if obj is None:
        add_issue(issues, severity, "missing_object", f"Missing object at {base_path}", base_path)
        return
    for field in fields:
        if field not in obj or obj[field] in (None, "", []):
            add_issue(issues, severity, "missing_field", f"Missing required field '{field}'", f"{base_path}.{field}")


def validate_trace(trace: list[str], issues: list[dict[str, Any]]) -> dict[str, Any]:
    observed: list[str] = []
    if not trace:
        add_issue(issues, "error", "missing_trace", "Transition trace is empty", "trace")
        return {"observed_states": observed, "terminal_state": None, "ack_seen": False}

    for idx, state in enumerate(trace):
        observed.append(state)
        if state not in ALLOWED_STATES:
            add_issue(issues, "error", "invalid_state", f"Unknown state '{state}'", f"trace[{idx}]")
        if idx == 0 and state != "PREPARED":
            add_issue(issues, "error", "invalid_start_state", "Trace must start at PREPARED", f"trace[{idx}]")
        if idx > 0:
            prev = trace[idx - 1]
            if (prev, state) not in ALLOWED_TRANSITIONS:
                add_issue(issues, "error", "invalid_transition", f"Transition {prev} -> {state} is not allowed", f"trace[{idx - 1}:{idx + 1}]")

    terminal_state = trace[-1]
    if terminal_state not in TERMINAL_STATES:
        add_issue(issues, "error", "non_terminal_end", "Trace must end in DONE or BLOCKED", f"trace[{len(trace) - 1}]")
    ack_seen = "ACK" in trace
    if ack_seen and trace.index("ACK") > 0 and trace[trace.index("ACK") - 1] != "PREPARED":
        add_issue(issues, "error", "ack_position_invalid", "ACK must be entered from PREPARED", "trace")
    if "DONE" in trace and not ack_seen:
        add_issue(issues, "error", "done_without_ack", "DONE requires prior ACK ownership acceptance", "trace")
    if "RUNNING" in trace and not ack_seen:
        add_issue(issues, "error", "running_without_ack", "RUNNING requires prior ACK", "trace")
    if len(trace) >= 2 and trace[1] == "BLOCKED" and ack_seen:
        add_issue(issues, "error", "blocked_before_ack_conflict", "Direct PREPARED -> BLOCKED path must not also include ACK", "trace")
    return {"observed_states": observed, "terminal_state": terminal_state, "ack_seen": ack_seen}


def validate_fixture(payload: dict[str, Any], rel_path: str) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    fixture_id = payload.get("fixture_id") or Path(rel_path).stem
    expected = payload.get("expected", {})
    handoff = payload.get("handoff")
    resume_trigger = payload.get("resume_trigger")
    continuation = payload.get("continuation")
    return_package = payload.get("return_package")
    trace = payload.get("trace", [])

    require_fields(handoff, REQUIRED_HANDOFF_FIELDS, "handoff", issues)
    require_fields(continuation, REQUIRED_CONTINUATION_FIELDS, "continuation", issues)

    if trace == ["PREPARED", "BLOCKED"]:
        if resume_trigger is not None:
            add_issue(warnings, "warning", "trigger_present_on_direct_block", "Direct PREPARED -> BLOCKED case usually does not need a resume trigger", "resume_trigger")
    else:
        require_fields(resume_trigger, REQUIRED_TRIGGER_FIELDS, "resume_trigger", issues)

    if return_package is not None:
        require_fields(return_package, REQUIRED_RETURN_FIELDS, "return_package", issues)
    else:
        add_issue(issues, "error", "missing_object", "Missing terminal return_package", "return_package")

    trace_info = validate_trace(trace, issues)
    terminal_state = trace_info["terminal_state"]
    ack_seen = trace_info["ack_seen"]

    if handoff and resume_trigger and handoff.get("handoff_id") != resume_trigger.get("handoff_id"):
        add_issue(issues, "error", "handoff_trigger_mismatch", "resume_trigger.handoff_id must match handoff.handoff_id", "resume_trigger.handoff_id")
    if handoff and continuation and handoff.get("handoff_id") != continuation.get("handoff_id"):
        add_issue(issues, "error", "handoff_continuation_mismatch", "continuation.handoff_id must match handoff.handoff_id", "continuation.handoff_id")
    if continuation and return_package:
        if continuation.get("continuation_id") != return_package.get("continuation_id"):
            add_issue(issues, "error", "continuation_return_mismatch", "return_package.continuation_id must match continuation.continuation_id", "return_package.continuation_id")
        if continuation.get("handoff_id") != return_package.get("handoff_id"):
            add_issue(issues, "error", "return_handoff_mismatch", "return_package.handoff_id must match continuation.handoff_id", "return_package.handoff_id")

    if continuation and terminal_state and continuation.get("status") != terminal_state:
        add_issue(issues, "error", "continuation_status_mismatch", "continuation.status must match terminal trace state in v0 fixtures", "continuation.status")
    if return_package and terminal_state and return_package.get("status") != terminal_state:
        add_issue(issues, "error", "return_status_mismatch", "return_package.status must match terminal trace state", "return_package.status")

    if return_package and terminal_state == "DONE":
        require_fields(return_package, REQUIRED_DONE_FIELDS, "return_package", issues)
        if not ack_seen:
            add_issue(issues, "error", "done_without_ack", "DONE return is not valid without prior ACK", "return_package.status")
    if return_package and terminal_state == "BLOCKED":
        require_fields(return_package, REQUIRED_BLOCKED_FIELDS, "return_package", issues)

    basis_anchor = (resume_trigger or {}).get("basis_anchor") if resume_trigger else None
    basis_text = (handoff or {}).get("resume_basis")
    if terminal_state != "BLOCKED" or trace != ["PREPARED", "BLOCKED"]:
        if not basis_anchor:
            add_issue(issues, "error", "missing_basis_anchor", "Resume basis must be anchorable via basis_anchor", "resume_trigger.basis_anchor")
    if basis_text and isinstance(basis_text, str) and "transcript" in basis_text.lower():
        add_issue(issues, "error", "transcript_only_basis", "Transcript-only resume basis is not allowed by default", "handoff.resume_basis")

    verdict = "pass" if not [i for i in issues if i["severity"] == "error"] else "fail"
    matches_expectation = verdict == expected.get("verdict") if expected.get("verdict") else None

    return {
        "fixture_id": fixture_id,
        "fixture_path": rel_path,
        "schema_version": SCHEMA_VERSION,
        "tool_version": TOOL_VERSION,
        "evaluated_at": now_iso(),
        "verdict": verdict,
        "matches_expected_verdict": matches_expectation,
        "summary": {
            "terminal_state": terminal_state,
            "ack_seen": ack_seen,
            "trace_length": len(trace),
            "error_count": sum(1 for item in issues if item["severity"] == "error"),
            "warning_count": sum(1 for item in warnings if item["severity"] == "warning"),
        },
        "trace": trace_info,
        "issues": issues,
        "warnings": warnings,
        "expected": expected,
    }


def collect_fixture_paths(args: argparse.Namespace) -> list[Path]:
    if args.fixture:
        return [Path(args.fixture).resolve()]
    return sorted(FIXTURE_DIR.glob("*.json"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify continuation fixtures against the v0 contract checks")
    parser.add_argument("--fixture", help="Single fixture path to verify")
    args = parser.parse_args()

    results = []
    failures = []
    for path in collect_fixture_paths(args):
        payload = load_json(path)
        rel_path = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        result = validate_fixture(payload, rel_path)
        results.append(result)
        if result["verdict"] != "pass":
            failures.append(result["fixture_id"])

    report = {
        "runner": "scripts/architecture/verify_continuation_cases.py",
        "schema_version": SCHEMA_VERSION,
        "tool_version": TOOL_VERSION,
        "fixture_dir": str(FIXTURE_DIR.relative_to(ROOT)),
        "evaluated_at": now_iso(),
        "case_count": len(results),
        "passed_count": sum(1 for item in results if item["verdict"] == "pass"),
        "failed_count": len(failures),
        "failures": failures,
        "results": results,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
