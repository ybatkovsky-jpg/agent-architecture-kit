#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "fixtures" / "retrieval-regression-task-121" / "known-good-queries.json"
DEFAULT_OUTPUT = ROOT / "outputs" / "task-121-retrieval-regression-fixture-pack-2026-04-26"


def run_query(query: str, mode: str, env_file: Path) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(ROOT / "retrieve_memory.py"),
        query,
        "--mode",
        mode,
        "--workspace-root",
        str(ROOT.parent),
        "--registry",
        str(ROOT / "config" / "source_registry.seed.yaml"),
        "--max-items",
        "6",
    ]
    if mode == "psql":
        cmd.extend(["--env-file", str(env_file)])
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "command": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def extract_paths(payload: dict[str, Any]) -> list[str]:
    return [item.get("document", {}).get("workspace_path", "") for item in payload.get("items", [])]


def evaluate_mode(expectation: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    paths = extract_paths(payload)
    top1_actual = paths[0] if paths else None
    top1_expected = expectation.get("top1_path")
    top3 = paths[:3]
    contains = expectation.get("top3_contains", [])

    checks = []
    ok = True

    if top1_expected:
        pass_top1 = top1_actual == top1_expected
        checks.append({
            "name": "top1_path",
            "expected": top1_expected,
            "actual": top1_actual,
            "pass": pass_top1,
        })
        ok = ok and pass_top1

    for expected_path in contains:
        present = expected_path in top3
        checks.append({
            "name": "top3_contains",
            "expected": expected_path,
            "actual_top3": top3,
            "pass": present,
        })
        ok = ok and present

    return {
        "pass": ok,
        "top_paths": paths,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify durable retrieval regression fixtures for task #121")
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--env-file", default=str(ROOT / "config" / "memory.env"))
    args = parser.parse_args()

    fixture_path = Path(args.fixture).resolve()
    output_dir = Path(args.output_dir).resolve()
    env_file = Path(args.env_file).resolve()
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

    total_mode_checks = 0
    passed_mode_checks = 0
    failed_cases = []

    for case in fixture.get("cases", []):
        case_result: dict[str, Any] = {
            "id": case["id"],
            "kind": case.get("kind"),
            "query": case["query"],
            "modes": {},
        }
        case_ok = True

        for mode in ["local", "psql"]:
            raw = run_query(case["query"], mode, env_file)
            raw_path = output_dir / f"{case['id']}-{mode}.raw.json"
            raw_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            mode_result: dict[str, Any] = {
                "returncode": raw["returncode"],
                "raw_output": str(raw_path.relative_to(ROOT.parent)),
            }

            if raw["returncode"] != 0:
                mode_result["pass"] = False
                mode_result["error"] = raw["stderr"][-2000:]
                case_ok = False
                total_mode_checks += 1
                case_result["modes"][mode] = mode_result
                continue

            payload = json.loads(raw["stdout"])
            payload_path = output_dir / f"{case['id']}-{mode}.result.json"
            payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            evaluated = evaluate_mode(case.get("expectations", {}).get(mode, {}), payload)
            evaluated["payload_output"] = str(payload_path.relative_to(ROOT.parent))
            mode_result.update(evaluated)
            total_mode_checks += 1
            if evaluated["pass"]:
                passed_mode_checks += 1
            else:
                case_ok = False
            case_result["modes"][mode] = mode_result

        case_result["pass"] = case_ok
        if not case_ok:
            failed_cases.append(case["id"])
        report["cases"].append(case_result)

    report["summary"] = {
        "total_cases": len(report["cases"]),
        "passed_cases": len(report["cases"]) - len(failed_cases),
        "failed_cases": failed_cases,
        "total_mode_checks": total_mode_checks,
        "passed_mode_checks": passed_mode_checks,
    }

    report_path = output_dir / "verification-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    return 0 if not failed_cases else 1


if __name__ == "__main__":
    raise SystemExit(main())
