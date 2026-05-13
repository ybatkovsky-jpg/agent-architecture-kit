#!/usr/bin/env python3
"""Evaluate one or more architecture traces against config and emit structured reports."""
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
from score_trace import calculate_score, load_trace  # noqa: E402


class EvalError(RuntimeError):
    pass


REQUIRED_TRACE_TOP_LEVEL_KEYS = {
    "trace_id",
    "request_id",
    "architecture",
    "status",
    "events",
    "result",
    "trace_summary",
    "evaluation_hooks",
}

REQUIRED_SCORE_INPUT_METRICS = {
    "task_success",
    "constraint_compliance",
    "artifact_quality",
    "tool_efficiency",
    "user_fit",
    "trace_clarity",
}


def validate_trace(trace: dict[str, Any], config: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    missing_top = sorted(REQUIRED_TRACE_TOP_LEVEL_KEYS - set(trace.keys()))
    if missing_top:
        issues.append(f"missing_top_level_keys:{','.join(missing_top)}")

    arch = trace.get("architecture") or {}
    if not isinstance(arch, dict):
        issues.append("architecture_not_object")
    else:
        if arch.get("id") != config.get("architecture", {}).get("id"):
            issues.append("architecture_id_mismatch")
        if not arch.get("version"):
            issues.append("architecture_version_missing")

    events = trace.get("events")
    if not isinstance(events, list) or not events:
        issues.append("events_missing_or_empty")
    else:
        for idx, event in enumerate(events, start=1):
            if not isinstance(event, dict):
                issues.append(f"event_{idx}_not_object")
                continue
            for key in ("step", "event_type", "module", "timestamp_utc"):
                if key not in event:
                    issues.append(f"event_{idx}_missing_{key}")
            step = event.get("step")
            if step != idx:
                issues.append(f"event_{idx}_step_sequence_invalid")

    hooks = trace.get("evaluation_hooks") or {}
    if not isinstance(hooks, dict):
        issues.append("evaluation_hooks_not_object")
        return issues

    score_inputs = hooks.get("score_inputs") or {}
    if not isinstance(score_inputs, dict):
        issues.append("score_inputs_not_object")
        return issues

    for metric in REQUIRED_SCORE_INPUT_METRICS:
        if metric not in score_inputs:
            issues.append(f"missing_metric:{metric}")
            continue
        value = score_inputs.get(metric)
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            issues.append(f"metric_not_numeric:{metric}")
            continue
        if numeric < 0.0 or numeric > 1.0:
            issues.append(f"metric_out_of_range:{metric}")

    penalties = score_inputs.get("penalties", [])
    if penalties is not None and not isinstance(penalties, list):
        issues.append("penalties_not_list")

    return issues


def derive_penalty_findings(result_dict: dict[str, Any]) -> dict[str, Any]:
    penalties_applied = result_dict.get("penalties_applied", []) or []
    recognized = [p for p in penalties_applied if p.get("recognized")]
    unrecognized = [p.get("id") for p in penalties_applied if not p.get("recognized")]
    return {
        "penalty_count": len(recognized),
        "penalty_ids": [p.get("id") for p in recognized],
        "unrecognized_penalty_ids": unrecognized,
    }


def evaluate_trace(trace_path: Path, config: dict[str, Any]) -> dict[str, Any]:
    trace = load_trace(trace_path)
    validation_issues = validate_trace(trace, config)
    score_result = calculate_score(trace, config)
    score_dict = score_result.to_dict()
    score_dict["validation_issues"] = validation_issues
    score_dict["validation_passed"] = not validation_issues
    score_dict["trace_path"] = str(trace_path.relative_to(ROOT)) if trace_path.is_absolute() else str(trace_path)
    score_dict["protected_case_tags"] = trace.get("evaluation_hooks", {}).get("protected_case_tags", []) or []
    score_dict["findings"] = derive_penalty_findings(score_dict)
    return score_dict


def collect_trace_paths(inputs: list[str]) -> list[Path]:
    paths: list[Path] = []
    for raw in inputs:
        path = Path(raw)
        if path.is_dir():
            paths.extend(sorted(p for p in path.glob("*.json") if p.is_file()))
        else:
            paths.append(path)
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(resolved)
    return unique


def build_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    hard_fail_count = sum(1 for item in results if item.get("hard_fail"))
    invalid_count = sum(1 for item in results if not item.get("validation_passed"))
    avg_valid = round(sum(item.get("valid_score", 0.0) for item in results) / len(results), 6) if results else 0.0
    return {
        "trace_count": len(results),
        "hard_fail_count": hard_fail_count,
        "invalid_count": invalid_count,
        "average_valid_score": avg_valid,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate architecture traces against config")
    parser.add_argument("config", help="Path to architecture config YAML/JSON")
    parser.add_argument("traces", nargs="+", help="Trace file(s) or directory/directories")
    parser.add_argument("--output", help="Optional output JSON path")
    args = parser.parse_args()

    try:
        config = load_arch_config(args.config)
        trace_paths = collect_trace_paths(args.traces)
        if not trace_paths:
            raise EvalError("No trace files found")
        results = [evaluate_trace(path, config) for path in trace_paths]
        payload = {
            "config_path": str(Path(args.config).resolve().relative_to(ROOT)),
            "summary": build_summary(results),
            "results": results,
        }
    except (ArchConfigError, EvalError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
        print(output_path)
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
