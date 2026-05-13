#!/usr/bin/env python3
"""Run protected architecture cases and emit score, verdict, and regression-ready outputs.

Default behavior is intentionally one-command friendly:
- evaluate all protected traces
- write/update current eval + protected JSON artifacts
- print a concise summary with fail details

Optional baseline inputs can be supplied to help downstream regression tooling, but are
not required for the protected-case runner itself.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from load_arch_config import ArchConfigError, load_arch_config  # noqa: E402
from eval_policy import evaluate_trace  # noqa: E402


DEFAULT_SCORE_OUTPUT = ROOT / "evals/architecture/score_reports/current_eval.json"
DEFAULT_PROTECTED_OUTPUT = ROOT / "evals/architecture/score_reports/current_protected.json"


def _contains_any(haystack: str, needles: list[str]) -> bool:
    lowered = haystack.lower()
    return any(str(needle).lower() in lowered for needle in needles if needle)


def infer_case_id(trace_result: dict[str, Any], config: dict[str, Any]) -> str | None:
    tags = set(trace_result.get("protected_case_tags", []) or [])
    trace_path = trace_result.get("trace_path", "")
    trace_name = Path(trace_path).name

    for case in config.get("protected_cases", []) or []:
        case_id = case.get("id")
        if not case_id:
            continue

        match = case.get("match") or {}
        any_tags = set(match.get("any_tags", []) or [])
        all_tags = set(match.get("all_tags", []) or [])
        path_contains_any = list(match.get("path_contains_any", []) or [])
        file_name_contains_any = list(match.get("file_name_contains_any", []) or [])

        if any_tags and not (tags & any_tags):
            continue
        if all_tags and not all_tags.issubset(tags):
            continue
        if path_contains_any and not _contains_any(trace_path, path_contains_any):
            continue
        if file_name_contains_any and not _contains_any(trace_name, file_name_contains_any):
            continue
        if any_tags or all_tags or path_contains_any or file_name_contains_any:
            return case_id

        suffix = case_id.removeprefix("pc_")
        if case_id in tags or suffix in tags or case_id in trace_name or suffix in trace_name:
            return case_id
    return None


def verdict_for_case(trace_result: dict[str, Any], case_spec: dict[str, Any]) -> dict[str, Any]:
    score_threshold = float(case_spec.get("score_threshold", 0.0))
    final_valid_score = float(trace_result.get("valid_score", 0.0))
    hard_fail = bool(trace_result.get("hard_fail"))
    hard_fail_reasons = set(trace_result.get("hard_fail_reasons", []) or [])
    applied_penalties = set(trace_result.get("findings", {}).get("penalty_ids", []) or [])
    validation_issues = trace_result.get("validation_issues", []) or []
    failures: list[str] = []

    expectation = str(case_spec.get("expectation", "prevent"))
    expect_hard_fail = bool(case_spec.get("require_hard_fail", expectation == "detect"))
    skip_score_threshold = bool(case_spec.get("skip_score_threshold", expectation == "detect"))
    required_hard_fail_present = case_spec.get("require_hard_fail_reasons", []) or []
    required_hard_fail_absent = case_spec.get("forbid_hard_fail_reasons", []) or []
    required_penalty_present = case_spec.get("require_penalties", []) or []
    required_penalty_absent = case_spec.get("forbid_penalties", []) or []

    if validation_issues:
        failures.append("trace_validation_failed")
    if hard_fail and not expect_hard_fail:
        failures.append("unexpected_hard_fail")
    if not hard_fail and expect_hard_fail:
        failures.append("expected_hard_fail_missing")
    if not skip_score_threshold and final_valid_score < score_threshold:
        failures.append(f"score_below_threshold:{final_valid_score:.4f}<{score_threshold:.4f}")

    for reason in required_hard_fail_absent:
        if reason in hard_fail_reasons:
            failures.append(f"forbidden_hard_fail_reason_present:{reason}")
    for reason in required_hard_fail_present:
        if reason not in hard_fail_reasons:
            failures.append(f"required_hard_fail_reason_missing:{reason}")
    for penalty_id in required_penalty_present:
        if penalty_id not in applied_penalties:
            failures.append(f"required_penalty_missing:{penalty_id}")
    for penalty_id in required_penalty_absent:
        if penalty_id in applied_penalties:
            failures.append(f"forbidden_penalty_present:{penalty_id}")

    return {
        "case_id": case_spec.get("id"),
        "description": case_spec.get("description"),
        "expectation": expectation,
        "trace_id": trace_result.get("trace_id"),
        "trace_path": trace_result.get("trace_path"),
        "score_threshold": score_threshold,
        "valid_score": final_valid_score,
        "hard_fail": hard_fail,
        "validation_passed": trace_result.get("validation_passed", False),
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "penalty_ids": sorted(applied_penalties),
        "hard_fail_reasons": sorted(hard_fail_reasons),
    }


def load_case_specs(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {case["id"]: case for case in (config.get("protected_cases", []) or []) if isinstance(case, dict) and case.get("id")}


def build_eval_payload(config_path: str, trace_results: list[dict[str, Any]]) -> dict[str, Any]:
    hard_fail_count = sum(1 for item in trace_results if item.get("hard_fail"))
    invalid_count = sum(1 for item in trace_results if not item.get("validation_passed"))
    avg_valid = round(sum(float(item.get("valid_score", 0.0)) for item in trace_results) / len(trace_results), 6) if trace_results else 0.0
    return {
        "config_path": str(Path(config_path).resolve().relative_to(ROOT)),
        "summary": {
            "trace_count": len(trace_results),
            "hard_fail_count": hard_fail_count,
            "invalid_count": invalid_count,
            "average_valid_score": avg_valid,
        },
        "results": trace_results,
    }


def fail_summary(verdicts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": item.get("case_id"),
            "trace_id": item.get("trace_id"),
            "trace_path": item.get("trace_path"),
            "failures": item.get("failures", []),
            "hard_fail": item.get("hard_fail", False),
            "hard_fail_reasons": item.get("hard_fail_reasons", []),
        }
        for item in verdicts
        if item.get("status") != "pass"
    ]


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run protected architecture cases")
    parser.add_argument("config", help="Path to architecture config")
    parser.add_argument("cases_dir", help="Directory with protected-case trace JSON files")
    parser.add_argument("--output", default=str(DEFAULT_PROTECTED_OUTPUT), help="Protected-case verdict JSON path")
    parser.add_argument("--eval-output", default=str(DEFAULT_SCORE_OUTPUT), help="Companion eval-policy style JSON path")
    args = parser.parse_args()

    try:
        config = load_arch_config(args.config)
        cases_dir = Path(args.cases_dir).resolve()
        if not cases_dir.is_dir():
            raise FileNotFoundError(f"Protected cases dir not found: {cases_dir}")

        case_specs = load_case_specs(config)
        trace_paths = sorted(cases_dir.glob("*.json"))
        if not trace_paths:
            raise FileNotFoundError(f"No protected case traces found in {cases_dir}")

        verdicts = []
        unmatched = []
        trace_results = []
        for trace_path in trace_paths:
            trace_result = evaluate_trace(trace_path, config)
            trace_results.append(trace_result)
            case_id = infer_case_id(trace_result, config)
            if not case_id or case_id not in case_specs:
                unmatched.append(trace_result.get("trace_path"))
                continue
            verdicts.append(verdict_for_case(trace_result, case_specs[case_id]))

        passed = sum(1 for item in verdicts if item["status"] == "pass")
        eval_payload = build_eval_payload(args.config, trace_results)
        payload = {
            "config_path": str(Path(args.config).resolve().relative_to(ROOT)),
            "cases_dir": str(cases_dir.relative_to(ROOT)),
            "summary": {
                "case_count": len(verdicts),
                "passed": passed,
                "failed": len(verdicts) - passed,
                "all_passed": passed == len(verdicts) and not unmatched,
                "unmatched_trace_count": len(unmatched),
            },
            "unmatched_traces": unmatched,
            "score_summary": eval_payload["summary"],
            "fail_summary": fail_summary(verdicts),
            "verdicts": verdicts,
        }
    except (ArchConfigError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    output_path = Path(args.output)
    eval_output_path = Path(args.eval_output)
    write_json(eval_output_path, eval_payload)
    write_json(output_path, payload)

    rendered = {
        "eval_output": str(eval_output_path.relative_to(ROOT) if eval_output_path.is_absolute() else eval_output_path),
        "protected_output": str(output_path.relative_to(ROOT) if output_path.is_absolute() else output_path),
        "summary": payload["summary"],
        "score_summary": payload["score_summary"],
        "fail_summary": payload["fail_summary"],
    }
    print(json.dumps(rendered, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
