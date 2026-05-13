#!/usr/bin/env python3
"""Build regression diff/report from current eval and optional baseline outputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent

import sys

if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from load_arch_config import load_arch_config  # noqa: E402


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def index_eval_results(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["trace_id"]: item for item in payload.get("results", []) or [] if item.get("trace_id")}


def index_protected_verdicts(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["case_id"]: item for item in payload.get("verdicts", []) or [] if item.get("case_id")}


def average_valid_score(payload: dict[str, Any]) -> float:
    return float((payload.get("summary") or {}).get("average_valid_score", 0.0) or 0.0)


def split_dataset_trace_diffs(trace_diffs: list[dict[str, Any]], protected_trace_ids: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sampled = [item for item in trace_diffs if item.get("trace_id") not in protected_trace_ids]
    protected = [item for item in trace_diffs if item.get("trace_id") in protected_trace_ids]
    return sampled, protected


def index_eval_paths(payload: dict[str, Any]) -> dict[str, str]:
    return {
        item["trace_id"]: item.get("trace_path", "")
        for item in payload.get("results", []) or []
        if item.get("trace_id")
    }


def index_eval_tags(payload: dict[str, Any]) -> dict[str, set[str]]:
    return {
        item["trace_id"]: set(item.get("protected_case_tags", []) or [])
        for item in payload.get("results", []) or []
        if item.get("trace_id")
    }


def filter_memory_contour_trace_diffs(
    sampled_trace_diffs: list[dict[str, Any]],
    eval_payload: dict[str, Any],
    memory_tags: set[str],
) -> list[dict[str, Any]]:
    path_index = index_eval_paths(eval_payload)
    tag_index = index_eval_tags(eval_payload)
    selected: list[dict[str, Any]] = []
    for item in sampled_trace_diffs:
        trace_id = item.get("trace_id")
        trace_path = path_index.get(trace_id, "")
        trace_tags = tag_index.get(trace_id, set())
        if any(tag in trace_id for tag in memory_tags) or any(tag in trace_path for tag in memory_tags) or bool(trace_tags & memory_tags):
            selected.append(item)
    return selected


def summarize_trace_diffs(items: list[dict[str, Any]]) -> dict[str, Any]:
    comparable = [item for item in items if item.get("delta") is not None]
    current_scored = [float(item.get("current_valid_score", 0.0) or 0.0) for item in items if item.get("current_valid_score") is not None]
    baseline_scored = [float(item.get("baseline_valid_score", 0.0) or 0.0) for item in items if item.get("baseline_valid_score") is not None]
    trace_count = len(items)
    comparable_count = len(comparable)
    return {
        "trace_count": trace_count,
        "comparable_trace_count": comparable_count,
        "baseline_coverage_ratio": round(comparable_count / trace_count, 6) if trace_count else None,
        "improved": sum(1 for item in items if item.get("status") == "improved"),
        "regressed": sum(1 for item in items if item.get("status") == "regressed"),
        "unchanged": sum(1 for item in items if item.get("status") == "unchanged"),
        "new": sum(1 for item in items if item.get("status") == "new"),
        "missing_in_current": sum(1 for item in items if item.get("status") == "missing_in_current"),
        "avg_current_valid_score": round(sum(current_scored) / len(current_scored), 6) if current_scored else 0.0,
        "avg_baseline_valid_score": round(sum(baseline_scored) / len(baseline_scored), 6) if baseline_scored else 0.0,
        "avg_score_delta": round(sum(float(item.get("delta", 0.0)) for item in comparable) / len(comparable), 6) if comparable else None,
    }


def build_dataset_feasibility(sampled_trace_diffs: list[dict[str, Any]], min_dataset_score_delta: float | None) -> dict[str, Any]:
    comparable = [item for item in sampled_trace_diffs if item.get("delta") is not None]
    if not comparable:
        return {
            "comparable_trace_count": 0,
            "score_ceiling": 1.0,
            "avg_remaining_headroom": None,
            "reachable_max_avg_score_delta": None,
            "required_min_dataset_score_delta": min_dataset_score_delta,
            "delta_gap_to_requirement": None,
            "requirement_reachable": None,
            "verdict": "unknown",
        }

    current_scores = [float(item.get("current_valid_score", 0.0) or 0.0) for item in comparable]
    baseline_scores = [float(item.get("baseline_valid_score", 0.0) or 0.0) for item in comparable]
    avg_current = sum(current_scores) / len(current_scores)
    avg_baseline = sum(baseline_scores) / len(baseline_scores)
    avg_remaining_headroom = max(0.0, 1.0 - avg_current)
    reachable_max_avg_score_delta = max(0.0, 1.0 - avg_baseline)

    requirement_reachable = None
    delta_gap = None
    verdict = "no_requirement"
    if min_dataset_score_delta is not None:
        required = float(min_dataset_score_delta)
        requirement_reachable = reachable_max_avg_score_delta >= required
        delta_gap = required - (sum(float(item.get("delta", 0.0)) for item in comparable) / len(comparable))
        verdict = "reachable" if requirement_reachable else "unreachable_under_score_ceiling"

    return {
        "comparable_trace_count": len(comparable),
        "score_ceiling": 1.0,
        "avg_remaining_headroom": round(avg_remaining_headroom, 6),
        "reachable_max_avg_score_delta": round(reachable_max_avg_score_delta, 6),
        "required_min_dataset_score_delta": min_dataset_score_delta,
        "delta_gap_to_requirement": round(delta_gap, 6) if delta_gap is not None else None,
        "requirement_reachable": requirement_reachable,
        "verdict": verdict,
    }


def build_proposal(report: dict[str, Any]) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    sampled = report.get("dataset_summary", {}).get("sampled_cases", {})
    min_delta = report.get("candidate_requirements", {}).get("min_dataset_score_delta")
    if sampled.get("comparable_trace_count", 0) > 0 and min_delta is not None:
        avg_delta = sampled.get("avg_score_delta")
        if avg_delta is not None and avg_delta < float(min_delta):
            feasibility = report.get("dataset_feasibility", {})
            if feasibility.get("verdict") == "unreachable_under_score_ceiling":
                proposals.append({
                    "id": "proposal_recalibrate_unreachable_dataset_delta_gate",
                    "what": "Recalibrate dataset-delta gate or redesign the comparable sampled set before promotion",
                    "why": (
                        f"Average sampled-case score delta {avg_delta:.6f} is below required {float(min_delta):.6f}, "
                        f"and the current comparable set can reach at most {float(feasibility.get('reachable_max_avg_score_delta', 0.0)):.6f} under the 1.0 score ceiling"
                    ),
                    "expected_effect": "Turns an impossible gate into an honest promotion contract or forces a more representative sampled set with real headroom",
                    "risk": "Medium: recalibration can weaken pressure if not paired with explicit feasibility evidence and protected-case preservation",
                })
            else:
                proposals.append({
                    "id": "proposal_raise_sampled_dataset_delta",
                    "what": "Improve policy/config against sampled dataset before baseline promotion",
                    "why": f"Average sampled-case score delta {avg_delta:.6f} is below required {float(min_delta):.6f}",
                    "expected_effect": "Moves regression verdict toward candidate readiness using non-protected traces, not only protected-case pass/fail",
                    "risk": "Medium: tuning for sampled cases may overfit if dataset remains too small or unrepresentative",
                })

    if report.get("fail_summary"):
        proposals.append({
            "id": "proposal_fix_failing_protected_cases",
            "what": "Fix protected-case failures before promoting config/baseline",
            "why": "Protected failures still exist in current run",
            "expected_effect": "Restores safety gate and prevents shipping known regressions",
            "risk": "Low: this is direct defect correction, but local fixes can still create new regressions elsewhere",
        })

    regressed = report.get("dataset_summary", {}).get("sampled_cases", {}).get("regressed", 0)
    if regressed:
        proposals.append({
            "id": "proposal_review_sampled_regressions",
            "what": "Inspect regressed sampled traces and cluster by penalty/hard-fail pattern",
            "why": f"There are {regressed} regressed sampled traces in the current compare",
            "expected_effect": "Produces targeted next edits instead of broad policy churn",
            "risk": "Low: analysis-only step, but depends on having enough trace diversity",
        })
    return proposals


def _safe_ratio(numerator: float, denominator: float) -> float:
    return 0.0 if not denominator else float(numerator) / float(denominator)


def build_calibration_summary(
    report: dict[str, Any],
    current_eval: dict[str, Any],
    current_protected: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    calibration = (config.get("calibration") or {}) if config else {}
    thresholds = calibration.get("thresholds") or {}
    bootstrap = calibration.get("bootstrap_refresh") or {}
    dataset_feasibility_cfg = calibration.get("dataset_feasibility") or {}

    sampled_floor = thresholds.get("sampled_trace_min_valid_score")
    protected_floor = thresholds.get("protected_prevent_min_valid_score")

    protected_expectations = {
        case.get("id"): case.get("expectation", "prevent")
        for case in (config.get("protected_cases") or [])
        if isinstance(case, dict) and case.get("id")
    }

    sampled_results = [
        item for item in (current_eval.get("results", []) or [])
        if item.get("trace_id") not in {v.get("trace_id") for v in (current_protected.get("verdicts", []) or [])}
    ]
    protected_verdicts = current_protected.get("verdicts", []) or []

    sampled_below_floor = []
    if sampled_floor is not None:
        for item in sampled_results:
            valid_score = float(item.get("valid_score", 0.0) or 0.0)
            if valid_score < float(sampled_floor):
                sampled_below_floor.append({
                    "trace_id": item.get("trace_id"),
                    "valid_score": valid_score,
                    "required_min": float(sampled_floor),
                })

    protected_prevent_below_floor = []
    if protected_floor is not None:
        for item in protected_verdicts:
            if protected_expectations.get(item.get("case_id")) != "prevent":
                continue
            valid_score = float(item.get("valid_score", 0.0) or 0.0)
            if valid_score < float(protected_floor):
                protected_prevent_below_floor.append({
                    "case_id": item.get("case_id"),
                    "trace_id": item.get("trace_id"),
                    "valid_score": valid_score,
                    "required_min": float(protected_floor),
                })

    sampled_summary = report.get("dataset_summary", {}).get("sampled_cases", {})
    dataset_feasibility = report.get("dataset_feasibility", {})
    sampled_trace_count = int(sampled_summary.get("trace_count", 0) or 0)
    new_sampled_count = int(sampled_summary.get("new", 0) or 0)
    sampled_baseline_coverage_ratio = float(sampled_summary.get("baseline_coverage_ratio", 0.0) or 0.0)
    new_sampled_trace_share = _safe_ratio(new_sampled_count, sampled_trace_count)
    protected_all_pass = report.get("summary", {}).get("protected_cases_passed") == report.get("summary", {}).get("protected_case_count")
    regressed_sampled_traces = int(sampled_summary.get("regressed", 0) or 0)
    dataset_delta_verdict = report.get("summary", {}).get("dataset_delta_verdict")

    bootstrap_allow = bootstrap.get("allow_when") or {}
    bootstrap_eligible = bool(bootstrap.get("enabled"))
    bootstrap_eligible = bootstrap_eligible and protected_all_pass == bool(bootstrap_allow.get("protected_cases_all_pass", True))
    bootstrap_eligible = bootstrap_eligible and regressed_sampled_traces <= int(bootstrap_allow.get("max_regressed_sampled_traces", 0))
    bootstrap_eligible = bootstrap_eligible and sampled_baseline_coverage_ratio >= float(bootstrap_allow.get("min_sampled_baseline_coverage_ratio", 1.0))
    bootstrap_eligible = bootstrap_eligible and new_sampled_trace_share <= float(bootstrap_allow.get("max_new_sampled_trace_share", 0.0))
    bootstrap_eligible = bootstrap_eligible and dataset_delta_verdict in {"insufficient_baseline", "incomplete_baseline_coverage"}

    owner_admission_cfg = calibration.get("owner_approved_admission") or {}
    owner_admission_allow = owner_admission_cfg.get("allow_when") or {}

    blockers = []
    if sampled_below_floor:
        blockers.append("sampled_trace_below_floor")
    if protected_prevent_below_floor:
        blockers.append("protected_prevent_case_below_floor")
    if report.get("fail_summary"):
        blockers.append("protected_case_failures_present")
    if regressed_sampled_traces:
        blockers.append("sampled_regressions_present")
    if dataset_feasibility.get("verdict") == "unreachable_under_score_ceiling" and bool(dataset_feasibility_cfg.get("block_promotion_when_unreachable", True)):
        blockers.append("dataset_delta_unreachable_under_score_ceiling")

    memory_tags_required = set(owner_admission_allow.get("only_for_new_traces_with_all_tags", []) or [])
    memory_contour_diffs = report.get("memory_contour_trace_diffs") or []
    owner_admission_trace_ids = [item.get("trace_id") for item in memory_contour_diffs if item.get("status") == "new" and item.get("trace_id")]
    owner_admission_new_share_ok = new_sampled_trace_share <= float(owner_admission_allow.get("max_new_trace_share", 0.0) or 0.0)
    owner_admission_blocker_required = owner_admission_allow.get("require_dataset_feasibility_blocker")
    owner_admission_recommendation_required = owner_admission_allow.get("require_recommendation", "hold_and_recalibrate")
    owner_admission_candidate = bool(owner_admission_cfg.get("enabled"))
    owner_admission_candidate = owner_admission_candidate and protected_all_pass == bool(owner_admission_allow.get("protected_cases_all_pass", True))
    owner_admission_candidate = owner_admission_candidate and regressed_sampled_traces <= int(owner_admission_allow.get("max_regressed_sampled_traces", 0))
    owner_admission_candidate = owner_admission_candidate and bool(owner_admission_trace_ids)
    owner_admission_candidate = owner_admission_candidate and owner_admission_new_share_ok
    owner_admission_candidate = owner_admission_candidate and all(
        memory_tags_required.issubset(set(index_eval_tags(current_eval).get(trace_id, set())))
        for trace_id in owner_admission_trace_ids
    )
    owner_admission_candidate = owner_admission_candidate and (
        owner_admission_blocker_required in blockers if owner_admission_blocker_required else True
    )

    if not blockers and report.get("summary", {}).get("dataset_delta_verdict") == "pass":
        recommendation = "promote_candidate"
    elif not blockers and bootstrap_eligible:
        recommendation = "bootstrap_refresh_baseline"
    else:
        recommendation = "hold_and_recalibrate"

    owner_admission_candidate = owner_admission_candidate and recommendation == owner_admission_recommendation_required

    return {
        "thresholds": thresholds,
        "dataset_feasibility": dataset_feasibility,
        "dataset_feasibility_contract": {
            "block_promotion_when_unreachable": bool(dataset_feasibility_cfg.get("block_promotion_when_unreachable", True)),
            "owner_action": dataset_feasibility_cfg.get("owner_action"),
            "threshold_change_requires_owner_signoff": bool(dataset_feasibility_cfg.get("threshold_change_requires_owner_signoff", False)),
            "prefer_dataset_redesign_before_threshold_edit": bool(dataset_feasibility_cfg.get("prefer_dataset_redesign_before_threshold_edit", False)),
            "explanation": dataset_feasibility_cfg.get("explanation"),
            "contract_block_active": dataset_feasibility.get("verdict") == "unreachable_under_score_ceiling" and bool(dataset_feasibility_cfg.get("block_promotion_when_unreachable", True)),
        },
        "bootstrap_refresh": {
            "enabled": bool(bootstrap.get("enabled")),
            "eligible": bootstrap_eligible,
            "sampled_baseline_coverage_ratio": round(sampled_baseline_coverage_ratio, 6),
            "new_sampled_trace_share": round(new_sampled_trace_share, 6),
            "regressed_sampled_traces": regressed_sampled_traces,
        },
        "owner_approved_admission": {
            "enabled": bool(owner_admission_cfg.get("enabled")),
            "candidate": owner_admission_candidate,
            "required_recommendation": owner_admission_recommendation_required,
            "required_blocker": owner_admission_blocker_required,
            "trace_ids": owner_admission_trace_ids,
            "new_trace_share": round(new_sampled_trace_share, 6),
            "max_new_trace_share": float(owner_admission_allow.get("max_new_trace_share", 0.0) or 0.0),
            "requires_owner_approval_manifest": bool(owner_admission_allow.get("require_owner_approval_manifest", False)),
            "requires_trace_rationale": bool(owner_admission_allow.get("require_trace_rationale", False)),
        },
        "sampled_below_floor": sampled_below_floor,
        "protected_prevent_below_floor": protected_prevent_below_floor,
        "blockers": blockers,
        "recommendation": recommendation,
    }


def build_trace_diffs(current: dict[str, Any], baseline: dict[str, Any] | None) -> list[dict[str, Any]]:
    current_idx = index_eval_results(current)
    baseline_idx = index_eval_results(baseline or {})
    trace_ids = sorted(set(current_idx) | set(baseline_idx))
    diffs = []
    for trace_id in trace_ids:
        now = current_idx.get(trace_id)
        old = baseline_idx.get(trace_id)
        if now and old:
            delta = round(float(now.get("valid_score", 0.0)) - float(old.get("valid_score", 0.0)), 6)
            status = "improved" if delta > 0 else "regressed" if delta < 0 else "unchanged"
            diffs.append({
                "trace_id": trace_id,
                "status": status,
                "current_valid_score": now.get("valid_score"),
                "baseline_valid_score": old.get("valid_score"),
                "delta": delta,
                "current_hard_fail": now.get("hard_fail"),
                "baseline_hard_fail": old.get("hard_fail"),
                "current_penalties": now.get("findings", {}).get("penalty_ids", []),
                "baseline_penalties": old.get("findings", {}).get("penalty_ids", []),
            })
        elif now:
            diffs.append({
                "trace_id": trace_id,
                "status": "new",
                "current_valid_score": now.get("valid_score"),
                "baseline_valid_score": None,
                "delta": None,
                "current_hard_fail": now.get("hard_fail"),
                "baseline_hard_fail": None,
                "current_penalties": now.get("findings", {}).get("penalty_ids", []),
                "baseline_penalties": [],
            })
        else:
            diffs.append({
                "trace_id": trace_id,
                "status": "missing_in_current",
                "current_valid_score": None,
                "baseline_valid_score": old.get("valid_score"),
                "delta": None,
                "current_hard_fail": None,
                "baseline_hard_fail": old.get("hard_fail"),
                "current_penalties": [],
                "baseline_penalties": old.get("findings", {}).get("penalty_ids", []),
            })
    return diffs


def build_case_diffs(current: dict[str, Any], baseline: dict[str, Any] | None) -> list[dict[str, Any]]:
    current_idx = index_protected_verdicts(current)
    baseline_idx = index_protected_verdicts(baseline or {})
    case_ids = sorted(set(current_idx) | set(baseline_idx))
    diffs = []
    for case_id in case_ids:
        now = current_idx.get(case_id)
        old = baseline_idx.get(case_id)
        current_status = now.get("status") if now else None
        baseline_status = old.get("status") if old else None
        if now and old:
            if current_status == baseline_status:
                status = "unchanged"
            elif current_status == "pass":
                status = "improved"
            else:
                status = "regressed"
        elif now:
            status = "new"
        else:
            status = "missing_in_current"
        diffs.append({
            "case_id": case_id,
            "status": status,
            "current": current_status,
            "baseline": baseline_status,
            "current_failures": now.get("failures", []) if now else [],
            "baseline_failures": old.get("failures", []) if old else [],
        })
    return diffs


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Architecture regression report",
        "",
        f"- Eval traces: {report['summary']['trace_count']}",
        f"- Improved traces: {report['summary']['improved_traces']}",
        f"- Regressed traces: {report['summary']['regressed_traces']}",
        f"- Hard fails now: {report['summary']['current_hard_fails']}",
        f"- Protected cases passed: {report['summary']['protected_cases_passed']}/{report['summary']['protected_case_count']}",
        f"- Dataset delta verdict: {report['summary']['dataset_delta_verdict']}",
        f"- Regression verdict: {report['summary']['regression_verdict']}",
        f"- Calibration recommendation: {report.get('calibration_summary', {}).get('recommendation')}",
        "",
        "## Dataset summary",
        f"- Sampled traces: {report['dataset_summary']['sampled_cases']['trace_count']}",
        f"- Sampled comparable to baseline: {report['dataset_summary']['sampled_cases']['comparable_trace_count']}",
        f"- Sampled baseline coverage ratio: {report['dataset_summary']['sampled_cases']['baseline_coverage_ratio']}",
        f"- Sampled avg current score: {report['dataset_summary']['sampled_cases']['avg_current_valid_score']}",
        f"- Sampled avg baseline score: {report['dataset_summary']['sampled_cases']['avg_baseline_valid_score']}",
        f"- Sampled avg delta: {report['dataset_summary']['sampled_cases']['avg_score_delta']}",
        f"- Protected traces inside eval dataset: {report['dataset_summary']['protected_cases']['trace_count']}",
        "",
        "## Calibration summary",
        f"- Bootstrap eligible: {report.get('calibration_summary', {}).get('bootstrap_refresh', {}).get('eligible')}",
        f"- Sampled below floor: {len(report.get('calibration_summary', {}).get('sampled_below_floor', []))}",
        f"- Protected prevent below floor: {len(report.get('calibration_summary', {}).get('protected_prevent_below_floor', []))}",
        f"- Dataset feasibility verdict: {report.get('dataset_feasibility', {}).get('verdict')}",
        f"- Reachable max sampled avg delta: {report.get('dataset_feasibility', {}).get('reachable_max_avg_score_delta')}",
        f"- Contract block active: {report.get('calibration_summary', {}).get('dataset_feasibility_contract', {}).get('contract_block_active')}",
        f"- Owner action: {report.get('calibration_summary', {}).get('dataset_feasibility_contract', {}).get('owner_action')}",
        f"- Threshold change requires owner signoff: {report.get('calibration_summary', {}).get('dataset_feasibility_contract', {}).get('threshold_change_requires_owner_signoff')}",
        f"- Prefer dataset redesign before threshold edit: {report.get('calibration_summary', {}).get('dataset_feasibility_contract', {}).get('prefer_dataset_redesign_before_threshold_edit')}",
        f"- Blockers: {', '.join(report.get('calibration_summary', {}).get('blockers', [])) or '-'}",
        "",
        "## Memory contour slice",
        f"- Memory contour traces: {report.get('dataset_summary', {}).get('memory_contour', {}).get('trace_count')}",
        f"- Memory contour comparable to baseline: {report.get('dataset_summary', {}).get('memory_contour', {}).get('comparable_trace_count')}",
        f"- Memory contour avg current score: {report.get('dataset_summary', {}).get('memory_contour', {}).get('avg_current_valid_score')}",
        f"- Memory contour avg baseline score: {report.get('dataset_summary', {}).get('memory_contour', {}).get('avg_baseline_valid_score')}",
        f"- Memory contour avg delta: {report.get('dataset_summary', {}).get('memory_contour', {}).get('avg_score_delta')}",
        "",
        "## Trace diffs",
    ]
    for item in report["trace_diffs"]:
        lines.append(
            f"- `{item['trace_id']}`: {item['status']}"
            f" | current={item['current_valid_score']} baseline={item['baseline_valid_score']} delta={item['delta']}"
            f" | penalties={','.join(item['current_penalties']) or '-'}"
        )
    if report.get("memory_contour_trace_diffs"):
        lines.append("")
        lines.append("## Memory contour trace diffs")
        for item in report["memory_contour_trace_diffs"]:
            lines.append(
                f"- `{item['trace_id']}`: {item['status']}"
                f" | current={item['current_valid_score']} baseline={item['baseline_valid_score']} delta={item['delta']}"
                f" | penalties={','.join(item['current_penalties']) or '-'}"
            )
    lines.append("")
    lines.append("## Protected case diffs")
    for item in report["protected_case_diffs"]:
        lines.append(
            f"- `{item['case_id']}`: {item['status']} | current={item['current']} baseline={item['baseline']}"
            f" | failures={'; '.join(item['current_failures']) if item['current_failures'] else '-'}"
        )
    if report.get("fail_summary"):
        lines.append("")
        lines.append("## Current failing protected cases")
        for item in report["fail_summary"]:
            lines.append(
                f"- `{item['case_id']}` from `{item['trace_id']}`"
                f" | hard_fail={item['hard_fail']}"
                f" | reasons={'; '.join(item['hard_fail_reasons']) if item['hard_fail_reasons'] else '-'}"
                f" | failures={'; '.join(item['failures']) if item['failures'] else '-'}"
            )
    if report.get("proposals"):
        lines.append("")
        lines.append("## Structured proposals")
        for item in report["proposals"]:
            lines.append(f"- `{item['id']}`: {item['what']}")
            lines.append(f"  - why: {item['why']}")
            lines.append(f"  - expected_effect: {item['expected_effect']}")
            lines.append(f"  - risk: {item['risk']}")
    return "\n".join(lines) + "\n"


def build_fail_summary(current_protected: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "case_id": item.get("case_id"),
            "trace_id": item.get("trace_id"),
            "trace_path": item.get("trace_path"),
            "hard_fail": item.get("hard_fail", False),
            "hard_fail_reasons": item.get("hard_fail_reasons", []),
            "failures": item.get("failures", []),
        }
        for item in (current_protected.get("verdicts", []) or [])
        if item.get("status") != "pass"
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build regression diff/report from evaluation outputs")
    parser.add_argument("current_eval", help="Current eval_policy output JSON")
    parser.add_argument("current_protected", help="Current protected_cases output JSON")
    parser.add_argument("--config", help="Architecture config path for candidate requirements")
    parser.add_argument("--baseline-eval", help="Baseline eval_policy output JSON")
    parser.add_argument("--baseline-protected", help="Baseline protected_cases output JSON")
    parser.add_argument("--output-json", help="Optional output JSON path")
    parser.add_argument("--output-md", help="Optional output markdown path")
    args = parser.parse_args()

    current_eval = load_json(args.current_eval)
    current_protected = load_json(args.current_protected)
    baseline_eval = load_json(args.baseline_eval) if args.baseline_eval else None
    baseline_protected = load_json(args.baseline_protected) if args.baseline_protected else None
    config = load_arch_config(args.config) if args.config else {}

    trace_diffs = build_trace_diffs(current_eval, baseline_eval)
    protected_case_diffs = build_case_diffs(current_protected, baseline_protected)
    protected_trace_ids = {item.get("trace_id") for item in (current_protected.get("verdicts", []) or []) if item.get("trace_id")}
    sampled_trace_diffs, protected_trace_diffs = split_dataset_trace_diffs(trace_diffs, protected_trace_ids)
    candidate_requirements = (((config.get("update_loop") or {}).get("candidate_requirements") or {}) if config else {})
    min_dataset_score_delta = candidate_requirements.get("min_dataset_score_delta")

    sampled_summary = summarize_trace_diffs(sampled_trace_diffs)
    protected_summary = summarize_trace_diffs(protected_trace_diffs)
    sampled_trace_count = sampled_summary.get("trace_count", 0)
    sampled_comparable_count = sampled_summary.get("comparable_trace_count", 0)
    sampled_has_full_baseline = sampled_trace_count > 0 and sampled_comparable_count == sampled_trace_count
    reporting_cfg = ((config.get("update_loop") or {}).get("reporting") or {}) if config else {}
    memory_tags = set(reporting_cfg.get("memory_contour_tags", []) or [])
    if sampled_trace_count == 0:
        dataset_delta_verdict = "no_sampled_cases"
    elif sampled_comparable_count == 0:
        dataset_delta_verdict = "insufficient_baseline"
    elif not sampled_has_full_baseline:
        dataset_delta_verdict = "incomplete_baseline_coverage"
    else:
        avg_delta = sampled_summary.get("avg_score_delta")
        dataset_delta_verdict = "pass" if min_dataset_score_delta is None or (avg_delta is not None and avg_delta >= float(min_dataset_score_delta)) else "fail"

    memory_contour_diffs = filter_memory_contour_trace_diffs(sampled_trace_diffs, current_eval, memory_tags)

    report = {
        "current_eval_path": str(Path(args.current_eval).resolve().relative_to(ROOT)),
        "current_protected_path": str(Path(args.current_protected).resolve().relative_to(ROOT)),
        "baseline_eval_path": str(Path(args.baseline_eval).resolve().relative_to(ROOT)) if args.baseline_eval else None,
        "baseline_protected_path": str(Path(args.baseline_protected).resolve().relative_to(ROOT)) if args.baseline_protected else None,
        "summary": {
            "trace_count": len(trace_diffs),
            "improved_traces": sum(1 for item in trace_diffs if item["status"] == "improved"),
            "regressed_traces": sum(1 for item in trace_diffs if item["status"] == "regressed"),
            "current_hard_fails": sum(1 for item in (current_eval.get("results", []) or []) if item.get("hard_fail")),
            "failing_hard_fails": sum(1 for item in build_fail_summary(current_protected) if item.get("hard_fail")),
            "protected_case_count": len(protected_case_diffs),
            "protected_cases_passed": sum(1 for item in protected_case_diffs if item.get("current") == "pass"),
            "sampled_trace_count": sampled_trace_count,
            "sampled_comparable_trace_count": sampled_comparable_count,
            "sampled_baseline_coverage_ratio": sampled_summary.get("baseline_coverage_ratio"),
            "dataset_delta_verdict": dataset_delta_verdict,
        },
        "candidate_requirements": candidate_requirements,
        "dataset_summary": {
            "sampled_cases": sampled_summary,
            "protected_cases": protected_summary,
            "memory_contour": summarize_trace_diffs(memory_contour_diffs),
        },
        "dataset_feasibility": build_dataset_feasibility(sampled_trace_diffs, min_dataset_score_delta),
        "trace_diffs": trace_diffs,
        "memory_contour_trace_diffs": memory_contour_diffs,
        "protected_case_diffs": protected_case_diffs,
    }

    report["fail_summary"] = build_fail_summary(current_protected)
    report["calibration_summary"] = build_calibration_summary(report, current_eval, current_protected, config)
    report["proposals"] = build_proposal(report)
    report["summary"]["regression_verdict"] = (
        "pass"
        if report["summary"]["regressed_traces"] == 0
        and report["summary"]["protected_cases_passed"] == report["summary"]["protected_case_count"]
        and report["summary"]["failing_hard_fails"] == 0
        and report["summary"]["dataset_delta_verdict"] == "pass"
        else "fail"
    )

    if args.output_json:
        output_json = Path(args.output_json)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(output_json)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.output_md:
        output_md = Path(args.output_md)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(build_markdown(report), encoding="utf-8")
        print(output_md)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
