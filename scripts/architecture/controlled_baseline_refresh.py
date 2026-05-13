#!/usr/bin/env python3
"""Apply a guarded baseline refresh when calibration explicitly recommends bootstrap refresh,
or when an owner-approved special admission manifest authorizes memory-contour baseline admission."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from load_arch_config import ArchConfigError, load_arch_config  # noqa: E402

DEFAULT_CONFIG = ROOT / "docs/learning/architecture-config.v0_1.example.yaml"
DEFAULT_EVAL_OUTPUT = ROOT / "evals/architecture/score_reports/current_eval.json"
DEFAULT_PROTECTED_OUTPUT = ROOT / "evals/architecture/score_reports/current_protected.json"
DEFAULT_REGRESSION_JSON = ROOT / "evals/architecture/regression_reports/current_regression.json"
DEFAULT_LEDGER = ROOT / "evals/architecture/baselines/refresh_history.jsonl"
DEFAULT_OWNER_APPROVAL_MANIFEST = ROOT / "evals/architecture/baselines/owner_approved_memory_contour_admission.json"


def resolve_root_path(raw: str | Path | None, fallback: Path) -> Path:
    if raw is None:
        return fallback
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def append_ledger(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def copy_with_parent(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def merge_owner_approved_memory_traces(
    current_eval: dict[str, Any],
    baseline_eval: dict[str, Any],
    allowed_trace_ids: set[str],
) -> dict[str, Any]:
    baseline_results = list((baseline_eval.get("results") or []))
    baseline_index = {item.get("trace_id"): idx for idx, item in enumerate(baseline_results) if item.get("trace_id")}
    for item in (current_eval.get("results") or []):
        trace_id = item.get("trace_id")
        if trace_id not in allowed_trace_ids:
            continue
        if trace_id in baseline_index:
            baseline_results[baseline_index[trace_id]] = item
        else:
            baseline_results.append(item)
    merged = dict(baseline_eval)
    merged["results"] = baseline_results
    summary = dict((baseline_eval.get("summary") or {}))
    summary["trace_count"] = len(baseline_results)
    if baseline_results:
        summary["average_valid_score"] = round(
            sum(float(item.get("valid_score", 0.0) or 0.0) for item in baseline_results) / len(baseline_results),
            6,
        )
        summary["hard_fail_count"] = sum(1 for item in baseline_results if item.get("hard_fail"))
        summary["invalid_count"] = sum(1 for item in baseline_results if not item.get("validation_passed", True))
    merged["summary"] = summary
    return merged


def main() -> int:
    parser = argparse.ArgumentParser(description="Guarded baseline refresh for architecture regression loop")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Architecture config path")
    parser.add_argument("--eval-output", default=str(DEFAULT_EVAL_OUTPUT), help="Current eval output JSON")
    parser.add_argument("--protected-output", default=str(DEFAULT_PROTECTED_OUTPUT), help="Current protected output JSON")
    parser.add_argument("--regression-json", default=str(DEFAULT_REGRESSION_JSON), help="Regression report JSON path")
    parser.add_argument("--baseline-eval", help="Override baseline eval JSON path")
    parser.add_argument("--baseline-protected", help="Override baseline protected JSON path")
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER), help="Append-only refresh ledger path")
    parser.add_argument("--allow-recommendation", default="bootstrap_refresh_baseline", help="Required calibration recommendation")
    parser.add_argument("--require-zero-blockers", action="store_true", default=True, help="Require calibration blockers to be empty")
    parser.add_argument("--owner-approval-manifest", default=str(DEFAULT_OWNER_APPROVAL_MANIFEST), help="Owner approval manifest path for special admission")
    parser.add_argument("--admission-mode", choices=["bootstrap", "owner-approved-memory-contour"], default="bootstrap", help="Refresh mode")
    parser.add_argument("--dry-run", action="store_true", help="Validate refresh eligibility without copying files")
    args = parser.parse_args()

    try:
        config_path = resolve_root_path(args.config, DEFAULT_CONFIG)
        config = load_arch_config(config_path)
        baseline_cfg = ((config.get("update_loop") or {}).get("baseline") or {})

        eval_output = resolve_root_path(args.eval_output, DEFAULT_EVAL_OUTPUT)
        protected_output = resolve_root_path(args.protected_output, DEFAULT_PROTECTED_OUTPUT)
        regression_json = resolve_root_path(args.regression_json, DEFAULT_REGRESSION_JSON)
        baseline_eval = resolve_root_path(args.baseline_eval or baseline_cfg.get("eval_path"), ROOT / "evals/architecture/baselines/latest_eval.json")
        baseline_protected = resolve_root_path(args.baseline_protected or baseline_cfg.get("protected_path"), ROOT / "evals/architecture/baselines/latest_protected.json")
        ledger_path = resolve_root_path(args.ledger, DEFAULT_LEDGER)
        owner_manifest_path = resolve_root_path(args.owner_approval_manifest, DEFAULT_OWNER_APPROVAL_MANIFEST)

        report = load_json(regression_json)
        calibration = report.get("calibration_summary") or {}
        refresh = calibration.get("bootstrap_refresh") or {}
        blockers = calibration.get("blockers") or []
        recommendation = calibration.get("recommendation")
        summary = report.get("summary") or {}

        owner_admission = calibration.get("owner_approved_admission") or {}

        if args.admission_mode == "bootstrap":
            if recommendation != args.allow_recommendation:
                raise ArchConfigError(
                    f"Refusing baseline refresh: recommendation={recommendation!r}, expected {args.allow_recommendation!r}"
                )
            if not refresh.get("eligible"):
                raise ArchConfigError("Refusing baseline refresh: bootstrap refresh is not eligible in calibration summary")
            if args.require_zero_blockers and blockers:
                raise ArchConfigError(f"Refusing baseline refresh: blockers present: {', '.join(blockers)}")
            if summary.get("protected_cases_passed") != summary.get("protected_case_count"):
                raise ArchConfigError("Refusing baseline refresh: not all protected cases passed")
            if int(refresh.get("regressed_sampled_traces", 0) or 0) != 0:
                raise ArchConfigError("Refusing baseline refresh: sampled regressions are present")
        else:
            if not owner_admission.get("enabled"):
                raise ArchConfigError("Refusing owner-approved admission: path is disabled in calibration summary")
            if not owner_admission.get("candidate"):
                raise ArchConfigError("Refusing owner-approved admission: current run is not a candidate for owner-approved memory-contour admission")
            if recommendation != owner_admission.get("required_recommendation"):
                raise ArchConfigError(
                    f"Refusing owner-approved admission: recommendation={recommendation!r}, expected {owner_admission.get('required_recommendation')!r}"
                )
            required_blocker = owner_admission.get("required_blocker")
            if required_blocker and required_blocker not in blockers:
                raise ArchConfigError(
                    f"Refusing owner-approved admission: blocker {required_blocker!r} not present"
                )
            if summary.get("protected_cases_passed") != summary.get("protected_case_count"):
                raise ArchConfigError("Refusing owner-approved admission: not all protected cases passed")
            if int(refresh.get("regressed_sampled_traces", 0) or 0) != 0:
                raise ArchConfigError("Refusing owner-approved admission: sampled regressions are present")
            manifest = load_json(owner_manifest_path)
            if manifest.get("status") != "approved":
                raise ArchConfigError("Refusing owner-approved admission: manifest status is not 'approved'")
            approved_trace_ids = set(((manifest.get("scope") or {}).get("trace_ids") or []))
            candidate_trace_ids = set(owner_admission.get("trace_ids") or [])
            if not approved_trace_ids or approved_trace_ids != candidate_trace_ids:
                raise ArchConfigError("Refusing owner-approved admission: approved trace set does not exactly match current candidate trace set")
            if manifest.get("owner") in {None, "", "OPEN_REQUIRED"} or manifest.get("approved_at_utc") in {None, "", "OPEN_REQUIRED"}:
                raise ArchConfigError("Refusing owner-approved admission: owner identity or approval timestamp is missing")
            if not (manifest.get("trace_rationales") or {}):
                raise ArchConfigError("Refusing owner-approved admission: trace rationales are missing")

        record = {
            "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "config_path": str(config_path.relative_to(ROOT)),
            "source_eval": str(eval_output.relative_to(ROOT)),
            "source_protected": str(protected_output.relative_to(ROOT)),
            "target_baseline_eval": str(baseline_eval.relative_to(ROOT)),
            "target_baseline_protected": str(baseline_protected.relative_to(ROOT)),
            "admission_mode": args.admission_mode,
            "recommendation": recommendation,
            "dataset_delta_verdict": summary.get("dataset_delta_verdict"),
            "protected_cases_passed": summary.get("protected_cases_passed"),
            "protected_case_count": summary.get("protected_case_count"),
            "sampled_baseline_coverage_ratio": refresh.get("sampled_baseline_coverage_ratio"),
            "new_sampled_trace_share": refresh.get("new_sampled_trace_share"),
            "regressed_sampled_traces": refresh.get("regressed_sampled_traces"),
            "blockers": blockers,
            "dry_run": bool(args.dry_run),
        }

        if not args.dry_run:
            if args.admission_mode == "bootstrap":
                copy_with_parent(eval_output, baseline_eval)
                copy_with_parent(protected_output, baseline_protected)
            else:
                current_eval_payload = load_json(eval_output)
                baseline_eval_payload = load_json(baseline_eval)
                merged_eval_payload = merge_owner_approved_memory_traces(
                    current_eval_payload,
                    baseline_eval_payload,
                    set(owner_admission.get("trace_ids") or []),
                )
                baseline_eval.parent.mkdir(parents=True, exist_ok=True)
                baseline_eval.write_text(json.dumps(merged_eval_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            append_ledger(ledger_path, record)

        print(json.dumps({
            "status": "dry_run_ok" if args.dry_run else "baseline_refreshed",
            "ledger_path": str(ledger_path.relative_to(ROOT)),
            "record": record,
        }, ensure_ascii=False, indent=2))
        return 0
    except (ArchConfigError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
