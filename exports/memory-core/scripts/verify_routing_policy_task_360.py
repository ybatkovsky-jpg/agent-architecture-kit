#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "outputs" / "task-360-routing-policy-2026-05-07"

CASES = [
    {
        "id": "current-task-execution-routes-to-task-scoped-sources",
        "query": "что уже готово по текущей задаче 360 и на каком этапе сейчас",
        "expected_request_class": "current_task_execution",
        "must_include_sources": ["openclaw_shared_memory", "task_manager_artifacts", "task_manager_handoffs"],
        "must_exclude_sources": [],
    },
    {
        "id": "resume-prefers-handoffs-over-memory",
        "query": "continue from handoff for task 359",
        "expected_request_class": "resume_reopen_continuation",
        "must_include_sources": ["task_manager_handoffs"],
        "must_exclude_sources": [],
    },
    {
        "id": "preference-recall-routes-to-verified-memory-notes",
        "query": "как лучше отвечать: коротко по делу или с длинным разбором",
        "expected_request_class": "preference_operating_style_recall",
        "must_include_sources": ["openclaw_shared_memory"],
        "must_exclude_sources": [],
    },
    {
        "id": "policy-decision-routes-to-memory-notes",
        "query": "почему решили сначала ужесточить classifier before routing enforcement",
        "expected_request_class": "policy_decision_lookup",
        "must_include_sources": ["openclaw_shared_memory"],
        "must_exclude_sources": [],
    },
    {
        "id": "artifact-trace-routes-to-evidence-files",
        "query": "Покажи, из каких именно файлов видно routing policy enforcement для memory-core",
        "expected_request_class": "artifact_source_trace_request",
        "must_include_sources": ["task_manager_artifacts", "task_manager_handoffs"],
        "must_exclude_sources": [],
    },
    {
        "id": "architecture-keeps-memory-in-selected-sources",
        "query": "show the architecture spec baseline for memory retrieval",
        "expected_request_class": "architecture_design_recall",
        "must_include_sources": ["openclaw_shared_memory"],
        "must_exclude_sources": [],
    },
]


def run_query(query: str) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(ROOT / "retrieve_memory.py"),
        query,
        "--mode",
        "local",
        "--workspace-root",
        str(ROOT.parent),
        "--registry",
        str(ROOT / "config" / "source_registry.seed.yaml"),
        "--max-items",
        "8",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def evaluate(case: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    routing = payload.get("routing", {})
    classification = payload.get("request_classification", {})
    selected_source_keys = routing.get("selected_source_keys")
    items = payload.get("items", [])

    must_include_sources = case.get("must_include_sources", [])
    must_exclude_sources = case.get("must_exclude_sources", [])

    checks = [
        {
            "name": "request_class",
            "expected": case["expected_request_class"],
            "actual": classification.get("request_class"),
            "pass": classification.get("request_class") == case["expected_request_class"],
        },
        {
            "name": "selected_source_keys_present",
            "expected": "non-empty list",
            "actual": selected_source_keys,
            "pass": isinstance(selected_source_keys, list) and len(selected_source_keys) > 0,
        },
        {
            "name": "must_include_sources",
            "expected": must_include_sources,
            "actual": selected_source_keys,
            "pass": isinstance(selected_source_keys, list) and all(source in selected_source_keys for source in must_include_sources),
        },
        {
            "name": "must_exclude_sources",
            "expected": must_exclude_sources,
            "actual": selected_source_keys,
            "pass": isinstance(selected_source_keys, list) and all(source not in selected_source_keys for source in must_exclude_sources),
        },
    ]
    return {
        "pass": all(check["pass"] for check in checks),
        "checks": checks,
        "routing": {"selected_source_keys": selected_source_keys},
        "items_source_keys": [item.get("source", {}).get("key") for item in items],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify task #360 routing policy enforcement")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {"cases": [], "summary": {}}
    failed: list[str] = []

    for case in CASES:
        raw = run_query(case["query"])
        raw_path = output_dir / f"{case['id']}.raw.json"
        raw_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        result_case: dict[str, Any] = {
            "id": case["id"],
            "query": case["query"],
            "raw_output": str(raw_path.relative_to(ROOT.parent)),
        }
        if raw["returncode"] != 0:
            result_case.update({"pass": False, "error": raw["stderr"][-2000:]})
            failed.append(case["id"])
            report["cases"].append(result_case)
            continue

        payload = json.loads(raw["stdout"])
        payload_path = output_dir / f"{case['id']}.result.json"
        payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        evaluated = evaluate(case, payload)
        result_case.update(evaluated)
        result_case["payload_output"] = str(payload_path.relative_to(ROOT.parent))
        if not evaluated["pass"]:
            failed.append(case["id"])
        report["cases"].append(result_case)

    report["summary"] = {
        "total_cases": len(report["cases"]),
        "passed_cases": len(report["cases"]) - len(failed),
        "failed_cases": failed,
        "all_pass": not failed,
    }
    report_path = output_dir / "verification-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
