#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
RETRIEVE = ROOT / "retrieve_memory.py"
OUT_DIR = WORKSPACE / "task-manager" / "artifacts" / "verification-task-371-continuation-regression-pack"

CASES: list[dict[str, Any]] = [
    {
        "id": "q1-explicit-task-resume",
        "query": "Resume Memory Core v1 after task-363 handoff",
        "mode": "psql",
        "expect_request_class": "resume_reopen_continuation",
        "expect_top_path_contains": ["task-363", "handoff"],
        "expect_top_authority": ["canonical_handoff"],
        "forbid_top_path_contains": ["task-368", "task-369"],
    },
    {
        "id": "q2-predecessor-reopen",
        "query": "Reopen Memory Core continuation around task-363/task-362 after the previous handoff",
        "mode": "psql",
        "expect_request_class": "resume_reopen_continuation",
        "expect_top_path_contains": ["task-363", "handoff"],
        "expect_top_authority": ["canonical_handoff"],
        "forbid_top_path_contains": ["task-368", "task-369"],
    },
    {
        "id": "q3-natural-language-continue-after",
        "query": "Продолжи Memory Core evaluation с места после conflict/open-question synthesis handoff",
        "mode": "psql",
        "expect_request_class": "resume_reopen_continuation",
        "expect_top_path_contains": ["task-363", "handoff"],
        "expect_top_authority": ["canonical_handoff"],
        "forbid_top_path_contains": ["task-368", "task-369"],
    },
    {
        "id": "q4-ambiguous-handoff-without-task-id",
        "query": "Продолжи Memory Core дальше после последнего handoff по Memory Core",
        "mode": "psql",
        "expect_request_class": "resume_reopen_continuation",
        "expect_any_top_path_contains": ["handoff", "task-363"],
        "expect_top_authority": ["canonical_handoff", "evidence_record"],
        "forbid_top_path_contains": ["task-368", "task-369"],
    },
    {
        "id": "q5-explicit-meta-query",
        "query": "Show Memory Core evaluation summary and hardening log for continuation retrieval",
        "mode": "psql",
        "expect_request_class": "architecture_design_recall",
        "expect_any_top_path_contains": ["task-368", "task-369", "evaluation", "hardening"],
        "allow_meta_top": True,
    },
]


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    out_path = OUT_DIR / f"{case['id']}.json"
    cmd = [
        "python3",
        str(RETRIEVE),
        case["query"],
        "--mode",
        case.get("mode", "psql"),
        "--max-items",
        "6",
        "--output",
        str(out_path),
    ]
    subprocess.run(cmd, cwd=str(WORKSPACE), check=True, capture_output=True, text=True)
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    top_items = payload.get("items", [])[:3]
    top_path = str(top_items[0].get("document", {}).get("workspace_path", "")) if top_items else ""
    top_authority = str(top_items[0].get("authority", {}).get("layer", "")) if top_items else ""
    request_class = str(payload.get("request_classification", {}).get("request_class", ""))

    checks: list[dict[str, Any]] = []

    checks.append({
        "name": "request_class",
        "passed": request_class == case.get("expect_request_class"),
        "expected": case.get("expect_request_class"),
        "actual": request_class,
    })

    expected_all = case.get("expect_top_path_contains", [])
    if expected_all:
        checks.append({
            "name": "top_path_contains_all",
            "passed": all(token in top_path.lower() for token in expected_all),
            "expected": expected_all,
            "actual": top_path,
        })

    expected_any = case.get("expect_any_top_path_contains", [])
    if expected_any:
        checks.append({
            "name": "top_path_contains_any",
            "passed": any(token in top_path.lower() for token in expected_any),
            "expected": expected_any,
            "actual": top_path,
        })

    expected_authorities = case.get("expect_top_authority", [])
    if expected_authorities:
        checks.append({
            "name": "top_authority_allowed",
            "passed": top_authority in expected_authorities,
            "expected": expected_authorities,
            "actual": top_authority,
        })

    forbidden = case.get("forbid_top_path_contains", [])
    if forbidden:
        checks.append({
            "name": "top_path_forbidden_tokens_absent",
            "passed": all(token not in top_path.lower() for token in forbidden),
            "expected_absent": forbidden,
            "actual": top_path,
        })

    meta_hits = [
        str(item.get("document", {}).get("workspace_path", ""))
        for item in payload.get("items", [])[:6]
        if any(token in str(item.get("document", {}).get("workspace_path", "")).lower() for token in ["task-366", "task-367", "task-368", "task-369", "hardening", "evaluation"])
    ]
    checks.append({
        "name": "meta_noise_policy",
        "passed": bool(meta_hits) if case.get("allow_meta_top") else not bool(meta_hits),
        "allow_meta_top": bool(case.get("allow_meta_top")),
        "actual_meta_hits": meta_hits,
    })

    passed = all(check["passed"] for check in checks)
    return {
        "id": case["id"],
        "query": case["query"],
        "mode": case.get("mode", "psql"),
        "passed": passed,
        "top_path": top_path,
        "top_authority": top_authority,
        "checks": checks,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = [run_case(case) for case in CASES]
    summary = {
        "pack": "task-371-continuation-regression-pack",
        "all_passed": all(result["passed"] for result in results),
        "results": results,
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
