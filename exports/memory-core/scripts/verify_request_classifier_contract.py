#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "fixtures" / "request-classifier-task-359" / "r2-hardening-cases.json"
DEFAULT_OUTPUT = ROOT / "outputs" / "task-359-request-classifier-r2-hardening-2026-05-10"


def load_classifier_module():
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("retrieve_memory", ROOT / "retrieve_memory.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def evaluate_case(module: Any, case: dict[str, Any]) -> dict[str, Any]:
    classification = module.classify_request(case["query"])
    checks = []
    ok = True
    for field, expected_value in case.get("expected", {}).items():
        actual_value = classification.get(field)
        passed = actual_value == expected_value
        checks.append({
            "field": field,
            "expected": expected_value,
            "actual": actual_value,
            "pass": passed,
        })
        ok = ok and passed
    return {
        "id": case["id"],
        "query": case["query"],
        "pass": ok,
        "classification": classification,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify request classifier contract fixtures without full retrieval")
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    fixture_path = Path(args.fixture).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    module = load_classifier_module()

    cases = [evaluate_case(module, case) for case in fixture.get("cases", [])]
    failed = [case["id"] for case in cases if not case["pass"]]
    report = {
        "fixture": str(fixture_path),
        "fixture_pack": fixture.get("fixture_pack"),
        "version": fixture.get("version"),
        "contract_version": fixture.get("contract_version"),
        "cases": cases,
        "summary": {
            "total_cases": len(cases),
            "passed_cases": len(cases) - len(failed),
            "failed_cases": failed,
            "all_pass": not failed,
        },
    }
    report_path = output_dir / "classification-contract-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
