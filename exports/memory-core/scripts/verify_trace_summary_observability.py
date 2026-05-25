#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "outputs" / "task-466-trace-summary-observability-2026-05-14"
DEFAULT_CASES = [
    {
        "id": "artifact-trace-local",
        "query": "which file cites the routing policy artifact path",
        "mode": "local",
        "expected": {
            "request_class": "artifact_source_trace_request",
            "trace_summary_fields": [
                "request_class",
                "purpose",
                "citation_mode",
                "authority_priority_focus",
                "selected_phase",
                "selected_item_paths",
                "selected_source_refs",
                "selected_chunk_refs",
                "selected_source_keys",
                "typed_serving_applied",
                "changed_order",
                "conflict_count",
                "open_question_count",
            ],
            "top_authority_layers_contains_any": ["evidence_record"],
            "selected_source_keys_contains_any": ["task_manager_artifacts"],
        },
    },
    {
        "id": "current-task-local",
        "query": "current status for task 442",
        "mode": "local",
        "expected": {
            "request_class": "current_task_execution",
            "trace_summary_fields": [
                "request_class",
                "purpose",
                "citation_mode",
                "authority_priority_focus",
                "selected_phase",
                "selected_item_paths",
                "selected_source_refs",
                "selected_chunk_refs",
                "selected_source_keys",
                "typed_serving_applied",
                "typed_serving_eligible_count",
                "typed_serving_ineligible_count",
                "changed_order",
            ],
            "top_authority_layers_contains_any": ["memory_note", "evidence_record"],
        },
    },
    {
        "id": "continuation-local",
        "query": "Resume Memory Core v1 after task-363 handoff",
        "mode": "local",
        "expected": {
            "request_class": "resume_reopen_continuation",
            "trace_summary_fields": [
                "request_class",
                "purpose",
                "citation_mode",
                "authority_priority_focus",
                "selected_phase",
                "selected_item_paths",
                "selected_source_refs",
                "selected_chunk_refs",
                "selected_source_keys",
                "history_assisted_continuation_anchor",
                "typed_serving_applied",
                "changed_order",
            ],
            "top_authority_layers_contains_any": ["canonical_handoff", "task_state", "memory_note"],
        },
    },
    {
        "id": "meta-psql",
        "query": "Show Memory Core evaluation summary and hardening log for continuation retrieval",
        "mode": "psql",
        "expected": {
            "request_class": "meta_evaluation_recall",
            "trace_summary_fields": [
                "request_class",
                "purpose",
                "citation_mode",
                "authority_priority_focus",
                "selected_phase",
                "selected_item_paths",
                "selected_source_refs",
                "selected_chunk_refs",
                "selected_source_keys",
                "typed_serving_applied",
                "changed_order",
                "conflict_count",
                "open_question_count",
            ],
            "top_authority_layers_contains_any": ["evidence_record"],
            "selected_source_keys_contains_any": ["task_manager_artifacts"],
        },
    },
    {
        "id": "continuation-psql",
        "query": "Resume Memory Core v1 after task-363 handoff",
        "mode": "psql",
        "expected": {
            "request_class": "resume_reopen_continuation",
            "trace_summary_fields": [
                "request_class",
                "purpose",
                "citation_mode",
                "authority_priority_focus",
                "selected_phase",
                "selected_item_paths",
                "selected_source_refs",
                "selected_chunk_refs",
                "selected_source_keys",
                "history_assisted_continuation_anchor",
                "typed_serving_applied",
                "changed_order"
            ],
            "top_authority_layers_contains_any": ["canonical_handoff", "task_state", "memory_note"],
            "selected_source_keys_contains_any": ["task_manager_handoffs", "task_manager_artifacts", "openclaw_shared_memory"],
        },
    },
    {
        "id": "artifact-trace-psql",
        "query": "which file cites the routing policy artifact path",
        "mode": "psql",
        "expected": {
            "request_class": "artifact_source_trace_request",
            "trace_summary_fields": [
                "request_class",
                "purpose",
                "citation_mode",
                "authority_priority_focus",
                "selected_phase",
                "selected_item_paths",
                "selected_source_refs",
                "selected_chunk_refs",
                "selected_source_keys",
                "typed_serving_applied",
                "changed_order",
                "conflict_count",
                "open_question_count"
            ],
            "top_authority_layers_contains_any": ["evidence_record", "task_state"],
            "selected_source_keys_contains_any": ["task_manager_artifacts"],
        },
    },
]


def run_query(query: str, mode: str, output_path: Path) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(ROOT / "retrieve_memory.py"),
        query,
        "--mode",
        mode,
        "--workspace-root",
        str(ROOT.parent),
        "--registry",
        str(ROOT / "config" / "source_registry.seed.yaml"),
        "--max-items",
        "5",
        "--output",
        str(output_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT.parent)
    return {"command": cmd, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, expected: Any, actual: Any) -> bool:
    checks.append({"field": name, "expected": expected, "actual": actual, "pass": passed})
    return passed


def contains_any(values: list[str], needles: list[str]) -> bool:
    value_set = {str(v) for v in values}
    return any(needle in value_set for needle in needles)


def evaluate_case(case: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    expected = case.get("expected", {})
    checks: list[dict[str, Any]] = []
    ok = True

    classification = payload.get("request_classification", {}) or {}
    trace_summary = (payload.get("serve_pack", {}) or {}).get("trace_summary", {}) or {}

    if "request_class" in expected:
        ok &= add_check(
            checks,
            "request_class",
            classification.get("request_class") == expected["request_class"],
            expected["request_class"],
            classification.get("request_class"),
        )

    for field in expected.get("trace_summary_fields", []):
        actual = trace_summary.get(field)
        present = field in trace_summary
        nonempty = actual not in (None, "", [])
        ok &= add_check(checks, f"trace_summary.{field}", present and nonempty, "present+nonempty", actual)

    if "top_authority_layers_contains_any" in expected:
        actual_layers = [str(x) for x in trace_summary.get("top_authority_layers", [])]
        ok &= add_check(
            checks,
            "trace_summary.top_authority_layers_contains_any",
            contains_any(actual_layers, list(expected["top_authority_layers_contains_any"])),
            expected["top_authority_layers_contains_any"],
            actual_layers,
        )

    if "selected_source_keys_contains_any" in expected:
        actual_keys = [str(x) for x in trace_summary.get("selected_source_keys", [])]
        ok &= add_check(
            checks,
            "trace_summary.selected_source_keys_contains_any",
            contains_any(actual_keys, list(expected["selected_source_keys_contains_any"])),
            expected["selected_source_keys_contains_any"],
            actual_keys,
        )

    return {
        "pass": ok,
        "checks": checks,
        "request_classification": classification,
        "trace_summary": trace_summary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify trace_summary observability contract across representative retrieval lanes")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "verification_pack": "task-466-trace-summary-observability-2026-05-14",
        "cases": [],
        "summary": {},
    }
    failed_cases: list[str] = []

    for case in DEFAULT_CASES:
        payload_path = output_dir / f"{case['id']}.result.json"
        raw_path = output_dir / f"{case['id']}.raw.json"
        raw = run_query(case["query"], case["mode"], payload_path)
        raw_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        case_result: dict[str, Any] = {
            "id": case["id"],
            "query": case["query"],
            "mode": case["mode"],
            "raw_output": str(raw_path.relative_to(ROOT.parent)),
        }
        if raw["returncode"] != 0:
            case_result.update({"pass": False, "error": raw["stderr"][-4000:]})
            failed_cases.append(case["id"])
            report["cases"].append(case_result)
            continue
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        evaluated = evaluate_case(case, payload)
        case_result.update(evaluated)
        case_result["payload_output"] = str(payload_path.relative_to(ROOT.parent))
        if not evaluated["pass"]:
            failed_cases.append(case["id"])
        report["cases"].append(case_result)

    report["summary"] = {
        "total_cases": len(report["cases"]),
        "passed_cases": len(report["cases"]) - len(failed_cases),
        "failed_cases": failed_cases,
        "all_pass": not failed_cases,
    }

    report_path = output_dir / "verification-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failed_cases else 1


if __name__ == "__main__":
    raise SystemExit(main())
