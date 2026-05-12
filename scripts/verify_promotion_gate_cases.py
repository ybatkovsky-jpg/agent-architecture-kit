#!/usr/bin/env python3
"""Verification runner for promotion gate markdown fixtures."""
from __future__ import annotations

import json
from pathlib import Path

from promotion_gate import evaluate_candidate, load_candidate

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "examples/promotion-gate/fixtures"

CASES = [
    {
        "id": "known-pass-schema",
        "path": FIXTURE_DIR / "known-pass-schema.md",
        "expected_verdict": "promote",
        "expected_bucket": "docs/schemas",
        "expected_action": "copy_or_rewrite_for_product_repo",
    },
    {
        "id": "known-hold-internal",
        "path": FIXTURE_DIR / "known-hold-internal.md",
        "expected_verdict": "hold_internal",
        "expected_bucket": None,
        "expected_action": "retain_internal_reference",
    },
    {
        "id": "known-sanitize-architecture",
        "path": FIXTURE_DIR / "known-sanitize-architecture.md",
        "expected_verdict": "sanitize_then_promote",
        "expected_bucket": "docs/architecture",
        "expected_action": "sanitize_then_rerun_gate",
    },
    {
        "id": "known-review-competing-buckets",
        "path": FIXTURE_DIR / "known-review-competing-buckets.md",
        "expected_verdict": "needs_review",
        "expected_bucket": "docs/evaluation",
        "expected_action": "request_architecture_review",
    },
]


def main() -> int:
    results = []
    failures = []

    for case in CASES:
        verdict = evaluate_candidate(load_candidate(str(case["path"])))
        observed = {
            "verdict": verdict["verdict"],
            "bucket": verdict["suggested_destination"].get("bucket"),
            "action": verdict["next_action"]["code"],
            "aggregate": verdict["score"]["aggregate"],
            "ambiguity_flags": verdict["confidence"]["ambiguity_flags"],
            "blocker_codes": [item["code"] for item in verdict["blockers"]],
        }
        checks = {
            "verdict": observed["verdict"] == case["expected_verdict"],
            "bucket": observed["bucket"] == case["expected_bucket"],
            "action": observed["action"] == case["expected_action"],
        }
        passed = all(checks.values())
        row = {
            "id": case["id"],
            "fixture": str(case["path"].relative_to(ROOT)),
            "expected": {
                "verdict": case["expected_verdict"],
                "bucket": case["expected_bucket"],
                "action": case["expected_action"],
            },
            "observed": observed,
            "checks": checks,
            "passed": passed,
        }
        results.append(row)
        if not passed:
            failures.append(case["id"])

    payload = {
        "runner": "scripts/architecture/verify_promotion_gate_cases.py",
        "fixture_dir": str(FIXTURE_DIR.relative_to(ROOT)),
        "case_count": len(results),
        "passed_count": sum(1 for item in results if item["passed"]),
        "failed_count": len(failures),
        "failures": failures,
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
