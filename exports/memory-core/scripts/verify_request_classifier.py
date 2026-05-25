#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "fixtures" / "request-classifier-task-359" / "baseline-cases.json"
DEFAULT_OUTPUT = ROOT / "outputs" / "task-359-request-classifier-baseline-2026-05-07"


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
        "4",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def evaluate_case(expected: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    classification = payload.get("request_classification", {})
    checks = []
    ok = True
    for field, expected_value in expected.items():
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
        "pass": ok,
        "classification": classification,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify request classifier baseline fixtures for task #359")
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    fixture_path = Path(args.fixture).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    report: dict[str, Any] = {
        "fixture": str(fixture_path),
        "fixture_pack": fixture.get("fixture_pack"),
        "version": fixture.get("version"),
        "contract_version": fixture.get("contract_version"),
        "cases": [],
        "summary": {},
    }

    failed_cases: list[str] = []

    for case in fixture.get("cases", []):
        raw = run_query(case["query"])
        raw_path = output_dir / f"{case['id']}.raw.json"
        raw_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        case_result: dict[str, Any] = {
            "id": case["id"],
            "query": case["query"],
            "raw_output": str(raw_path.relative_to(ROOT.parent)),
        }

        if raw["returncode"] != 0:
            case_result.update({
                "pass": False,
                "error": raw["stderr"][-2000:],
            })
            failed_cases.append(case["id"])
            report["cases"].append(case_result)
            continue

        payload = json.loads(raw["stdout"])
        payload_path = output_dir / f"{case['id']}.result.json"
        payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        evaluated = evaluate_case(case.get("expected", {}), payload)
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
