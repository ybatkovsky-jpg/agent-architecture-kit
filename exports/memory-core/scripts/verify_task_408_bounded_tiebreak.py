#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "outputs" / "task-408-aligned-verification-2026-05-12"

CASES = [
    {
        "id": "anchored-resume-protected",
        "query": "Resume Memory Core v1 after task-363 handoff and continue with the next bounded hardening slice.",
        "expected": {
            "request_class": "resume_reopen_continuation",
            "top_path_contains": "task-363-memory-core-v1-conflict-open-question-synthesis-handoff-2026-05-07.md",
            "top_authority": "canonical_handoff",
            "top_match_reason_contains": ["continuation_task_id_exact_match"],
            "history_tiebreak_applied": False,
        },
    },
    {
        "id": "weak-case-cleanup-improved",
        "query": "continue after conflict/open-question synthesis",
        "expected": {
            "request_class": "factual_lookup",
            "top1_path_contains": "task-363-memory-core-v1-conflict-open-question-synthesis-handoff-2026-05-07.md",
            "top2_path_contains": "task-362-memory-core-v1-citation-envelope-handoff-2026-05-07.md",
            "history_tiebreak_applied": True,
            "history_anchor": "conflict/open-question synthesis",
            "top5_must_not_contain": [
                "task-147-rollout-handoff-next-session-2026-04-29.md",
                "task-410-context-engine-memory-retrieval-handoff-integration-2026-05-12.md",
                "verification-task-371-continuation-regression-pack/q3-natural-language-continue-after.json",
            ],
        },
    },
    {
        "id": "explicit-meta-not-rerouted",
        "query": "Покажи evaluation artifacts Stage 5 и из каких файлов видно baseline fail/pass summary.",
        "expected": {
            "request_class": "meta_evaluation_recall",
            "history_tiebreak_applied": False,
        },
    },
]


def run_query(query: str, output_path: Path) -> dict[str, Any]:
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
        "5",
        "--output",
        str(output_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT.parent)
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def path_of(item: dict[str, Any]) -> str:
    return str(item.get("document", {}).get("workspace_path", ""))


def authority_of(item: dict[str, Any]) -> str:
    return str(item.get("authority", {}).get("layer", ""))


def match_reason_of(item: dict[str, Any]) -> str:
    return str(item.get("match_reason", ""))


def evaluate_case(case: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    expected = case["expected"]
    items = payload.get("items", []) or []
    top = items[0] if items else {}
    top2 = items[1] if len(items) > 1 else {}
    top5_paths = [path_of(item) for item in items[:5]]
    classification = payload.get("request_classification", {}) or {}
    trace = payload.get("serve_pack", {}).get("history_assisted_continuation_tiebreak", {}) or {}
    checks: list[dict[str, Any]] = []
    ok = True

    def add(name: str, passed: bool, expected_value: Any, actual_value: Any) -> None:
        nonlocal ok
        checks.append({"field": name, "expected": expected_value, "actual": actual_value, "pass": passed})
        ok = ok and passed

    if "request_class" in expected:
        add("request_class", classification.get("request_class") == expected["request_class"], expected["request_class"], classification.get("request_class"))
    if "top_path_contains" in expected:
        add("top_path_contains", expected["top_path_contains"] in path_of(top), expected["top_path_contains"], path_of(top))
    if "top1_path_contains" in expected:
        add("top1_path_contains", expected["top1_path_contains"] in path_of(top), expected["top1_path_contains"], path_of(top))
    if "top2_path_contains" in expected:
        add("top2_path_contains", expected["top2_path_contains"] in path_of(top2), expected["top2_path_contains"], path_of(top2))
    if "top_authority" in expected:
        add("top_authority", authority_of(top) == expected["top_authority"], expected["top_authority"], authority_of(top))
    for needle in expected.get("top_match_reason_contains", []):
        add(f"top_match_reason_contains:{needle}", needle in match_reason_of(top), needle, match_reason_of(top))
    if "history_tiebreak_applied" in expected:
        add("history_tiebreak_applied", bool(trace.get("applied")) == expected["history_tiebreak_applied"], expected["history_tiebreak_applied"], bool(trace.get("applied")))
    if "history_anchor" in expected:
        add("history_anchor", str(trace.get("anchor", "")) == expected["history_anchor"], expected["history_anchor"], str(trace.get("anchor", "")))
    for needle in expected.get("top5_must_not_contain", []):
        add(f"top5_must_not_contain:{needle}", all(needle not in path for path in top5_paths), f"absent from top5: {needle}", top5_paths)

    return {
        "pass": ok,
        "checks": checks,
        "top5_paths": top5_paths,
        "top_item": {
            "workspace_path": path_of(top),
            "authority": authority_of(top),
            "match_reason": match_reason_of(top),
        },
        "history_tiebreak": trace,
        "request_classification": classification,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Aligned verification for task #408 bounded history-assisted tiebreak")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {"cases": [], "summary": {}}
    failed: list[str] = []

    for case in CASES:
        payload_path = output_dir / f"{case['id']}.result.json"
        raw = run_query(case["query"], payload_path)
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

        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        evaluated = evaluate_case(case, payload)
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
