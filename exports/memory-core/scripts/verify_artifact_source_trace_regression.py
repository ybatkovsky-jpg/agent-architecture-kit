#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "fixtures" / "artifact-source-trace-regression-2026-05-12" / "cases.json"
DEFAULT_OUTPUT = ROOT / "outputs" / "artifact-source-trace-regression-2026-05-12"


def run_query(query: str, output_path: Path) -> dict[str, Any]:
    cmd = [sys.executable, str(ROOT / "retrieve_memory.py"), query, "--mode", "local", "--workspace-root", str(ROOT.parent), "--registry", str(ROOT / "config" / "source_registry.seed.yaml"), "--max-items", "5", "--output", str(output_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT.parent)
    return {"command": cmd, "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def path_of(item: dict[str, Any]) -> str:
    return str(item.get("document", {}).get("workspace_path", ""))


def contains_any_path(items: list[dict[str, Any]], needles: list[str]) -> bool:
    hay = [path_of(item) for item in items]
    return any(any(needle in path for needle in needles) for path in hay)


def evaluate_case(case: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    expected = case.get("expected", {})
    classification = payload.get("request_classification", {}) or {}
    items = payload.get("items", []) or []
    checks: list[dict[str, Any]] = []
    ok = True

    def add_check(name: str, passed: bool, expected_value: Any, actual_value: Any) -> None:
        nonlocal ok
        checks.append({"field": name, "expected": expected_value, "actual": actual_value, "pass": passed})
        ok = ok and passed

    if "request_class" in expected:
        add_check("request_class", classification.get("request_class") == expected["request_class"], expected["request_class"], classification.get("request_class"))
    if "top5_path_contains_any" in expected:
        needles = list(expected["top5_path_contains_any"])
        actual = [path_of(item) for item in items[:5]]
        add_check("top5_path_contains_any", contains_any_path(items[:5], needles), needles, actual)

    return {"pass": ok, "checks": checks, "request_classification": classification, "top5_paths": [path_of(item) for item in items[:5]]}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify artifact/source-trace regression fixtures")
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()
    fixture_path = Path(args.fixture).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    report: dict[str, Any] = {"fixture": str(fixture_path), "fixture_pack": fixture.get("fixture_pack"), "version": fixture.get("version"), "contract_version": fixture.get("contract_version"), "contract_path": fixture.get("contract_path"), "cases": [], "summary": {}}
    failed_cases: list[str] = []
    for case in fixture.get("cases", []):
        raw_path = output_dir / f"{case['id']}.raw.json"
        payload_path = output_dir / f"{case['id']}.result.json"
        raw = run_query(case["query"], payload_path)
        raw_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        case_result: dict[str, Any] = {"id": case["id"], "query": case["query"], "raw_output": str(raw_path.relative_to(ROOT.parent))}
        if raw["returncode"] != 0:
            case_result.update({"pass": False, "error": raw["stderr"][-2000:]})
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
    report["summary"] = {"total_cases": len(report["cases"]), "passed_cases": len(report["cases"]) - len(failed_cases), "failed_cases": failed_cases, "all_pass": not failed_cases}
    report_path = output_dir / "verification-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not failed_cases else 1


if __name__ == "__main__":
    raise SystemExit(main())
