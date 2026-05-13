#!/usr/bin/env python3
"""One-command architecture regression run with optional baseline compare/promotion."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from load_arch_config import ArchConfigError, load_arch_config  # noqa: E402

DEFAULT_CONFIG = ROOT / "docs/learning/architecture-config.v0_1.example.yaml"
DEFAULT_CASES_DIR = ROOT / "evals/architecture/protected_cases"
DEFAULT_SAMPLED_DIR = ROOT / "evals/architecture/sampled_cases"
DEFAULT_EVAL_OUTPUT = ROOT / "evals/architecture/score_reports/current_eval.json"
DEFAULT_PROTECTED_OUTPUT = ROOT / "evals/architecture/score_reports/current_protected.json"
DEFAULT_PROTECTED_COMPANION_EVAL = ROOT / "evals/architecture/score_reports/current_protected_eval.json"
DEFAULT_REGRESSION_JSON = ROOT / "evals/architecture/regression_reports/current_regression.json"
DEFAULT_REGRESSION_MD = ROOT / "evals/architecture/regression_reports/current_regression.md"
DEFAULT_REFRESH_LEDGER = ROOT / "evals/architecture/baselines/refresh_history.jsonl"


def resolve_root_path(raw: str | Path | None, fallback: Path) -> Path:
    if raw is None:
        return fallback
    path = Path(raw)
    return path if path.is_absolute() else ROOT / path


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_python(script: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def maybe_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run protected cases + regression compare in one command")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Architecture config path")
    parser.add_argument("--cases-dir", default=str(DEFAULT_CASES_DIR), help="Protected cases directory")
    parser.add_argument("--sampled-dir", default=str(DEFAULT_SAMPLED_DIR), help="Sampled cases directory")
    parser.add_argument("--eval-output", default=str(DEFAULT_EVAL_OUTPUT), help="Current eval output JSON")
    parser.add_argument("--protected-output", default=str(DEFAULT_PROTECTED_OUTPUT), help="Current protected output JSON")
    parser.add_argument("--regression-json", help="Regression report JSON path")
    parser.add_argument("--regression-md", help="Regression report markdown path")
    parser.add_argument("--baseline-eval", help="Baseline eval JSON path")
    parser.add_argument("--baseline-protected", help="Baseline protected JSON path")
    parser.add_argument("--use-config-baseline", action="store_true", help="Read baseline/report paths from config.update_loop.baseline")
    parser.add_argument("--promote-baseline", action="store_true", help="Copy current outputs into baseline paths after a successful run")
    parser.add_argument("--refresh-baseline-on-bootstrap", action="store_true", help="Apply guarded baseline refresh when calibration recommends bootstrap refresh")
    args = parser.parse_args()

    try:
        config_path = resolve_root_path(args.config, DEFAULT_CONFIG)
        config = load_arch_config(config_path)
        baseline_cfg = ((config.get("update_loop") or {}).get("baseline") or {}) if args.use_config_baseline else {}

        cases_dir = resolve_root_path(args.cases_dir, DEFAULT_CASES_DIR)
        sampled_dir = resolve_root_path(args.sampled_dir, DEFAULT_SAMPLED_DIR)
        eval_output = resolve_root_path(args.eval_output, DEFAULT_EVAL_OUTPUT)
        protected_output = resolve_root_path(args.protected_output, DEFAULT_PROTECTED_OUTPUT)
        protected_companion_eval = DEFAULT_PROTECTED_COMPANION_EVAL
        regression_json = resolve_root_path(args.regression_json or baseline_cfg.get("regression_json_path"), DEFAULT_REGRESSION_JSON)
        regression_md = resolve_root_path(args.regression_md or baseline_cfg.get("regression_md_path"), DEFAULT_REGRESSION_MD)
        baseline_eval = resolve_root_path(args.baseline_eval or baseline_cfg.get("eval_path"), ROOT / "evals/architecture/baselines/latest_eval.json")
        baseline_protected = resolve_root_path(args.baseline_protected or baseline_cfg.get("protected_path"), ROOT / "evals/architecture/baselines/latest_protected.json")

        protected_runner = SCRIPT_DIR / "run_protected_cases.py"
        eval_runner = SCRIPT_DIR / "eval_policy.py"
        regression_builder = SCRIPT_DIR / "regression_report.py"

        eval_inputs: list[str] = []
        if sampled_dir.exists() and sampled_dir.is_dir():
            eval_inputs.append(str(sampled_dir))
        if cases_dir.exists() and cases_dir.is_dir():
            eval_inputs.append(str(cases_dir))
        if not eval_inputs:
            print("ERROR: no sampled/protected trace directories found", file=sys.stderr)
            return 1

        eval_run = run_python(
            eval_runner,
            [
                str(config_path),
                *eval_inputs,
                "--output",
                str(eval_output),
            ],
        )
        if eval_run.returncode != 0:
            sys.stderr.write(eval_run.stderr or eval_run.stdout)
            return eval_run.returncode

        protected_run = run_python(
            protected_runner,
            [
                str(config_path),
                str(cases_dir),
                "--eval-output",
                str(protected_companion_eval),
                "--output",
                str(protected_output),
            ],
        )
        if protected_run.returncode != 0:
            sys.stderr.write(protected_run.stderr or protected_run.stdout)
            return protected_run.returncode

        regression_args = [
            str(eval_output),
            str(protected_output),
            "--config",
            str(config_path),
            "--output-json",
            str(regression_json),
            "--output-md",
            str(regression_md),
        ]
        if baseline_eval.exists():
            regression_args.extend(["--baseline-eval", str(baseline_eval)])
        if baseline_protected.exists():
            regression_args.extend(["--baseline-protected", str(baseline_protected)])

        regression_run = run_python(regression_builder, regression_args)
        if regression_run.returncode != 0:
            sys.stderr.write(regression_run.stderr or regression_run.stdout)
            return regression_run.returncode

        report = load_json(regression_json)
        summary = report.get("summary", {})

        baseline_status = "present" if baseline_eval.exists() and baseline_protected.exists() else "missing"
        promoted = False
        baseline_refresh = None
        if args.promote_baseline and summary.get("regression_verdict") == "pass":
            maybe_copy(eval_output, baseline_eval)
            maybe_copy(protected_output, baseline_protected)
            promoted = True
        elif args.refresh_baseline_on_bootstrap:
            calibration = report.get("calibration_summary", {})
            refresh = calibration.get("bootstrap_refresh", {})
            if calibration.get("recommendation") == "bootstrap_refresh_baseline" and refresh.get("eligible"):
                refresh_runner = SCRIPT_DIR / "controlled_baseline_refresh.py"
                refresh_run = run_python(
                    refresh_runner,
                    [
                        "--config",
                        str(config_path),
                        "--eval-output",
                        str(eval_output),
                        "--protected-output",
                        str(protected_output),
                        "--regression-json",
                        str(regression_json),
                        "--ledger",
                        str(DEFAULT_REFRESH_LEDGER),
                    ],
                )
                if refresh_run.returncode != 0:
                    sys.stderr.write(refresh_run.stderr or refresh_run.stdout)
                    return refresh_run.returncode
                baseline_refresh = json.loads(refresh_run.stdout)

        dataset_summary = report.get("dataset_summary", {})
        rendered = {
            "config_path": str(config_path.relative_to(ROOT)),
            "cases_dir": str(cases_dir.relative_to(ROOT)),
            "sampled_dir": str(sampled_dir.relative_to(ROOT)) if sampled_dir.exists() else None,
            "baseline_status": baseline_status,
            "promoted_baseline": promoted,
            "baseline_refresh": baseline_refresh,
            "artifacts": {
                "current_eval": str(eval_output.relative_to(ROOT)),
                "current_protected": str(protected_output.relative_to(ROOT)),
                "regression_json": str(regression_json.relative_to(ROOT)),
                "regression_md": str(regression_md.relative_to(ROOT)),
                "baseline_eval": str(baseline_eval.relative_to(ROOT)),
                "baseline_protected": str(baseline_protected.relative_to(ROOT)),
            },
            "summary": summary,
            "dataset_summary": {
                "sampled_cases": dataset_summary.get("sampled_cases", {}),
                "protected_cases": dataset_summary.get("protected_cases", {}),
            },
            "fail_summary": report.get("fail_summary", []),
        }
        print(json.dumps(rendered, ensure_ascii=False, indent=2))
        return 0
    except ArchConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
