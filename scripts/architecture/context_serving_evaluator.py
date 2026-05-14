#!/usr/bin/env python3
"""Minimal context-serving evaluator v0.

Given a request class and candidate object classes, classify each candidate into:
- always_on
- on_demand
- suppressed (forbidden ambient injection)

Behavior is derived conservatively from the exported serving-class matrix.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "examples" / "serving-policy" / "openclaw-frame-serving-class-matrix-v1.json"
FIXTURES_PATH = ROOT / "evals" / "architecture" / "fixtures" / "context-serving-fixtures.json"


class EvaluationError(Exception):
    pass


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_request(matrix_doc: Dict[str, Any], request_class: str, candidates: List[str]) -> Dict[str, Any]:
    matrix = matrix_doc["matrix"]
    if request_class not in matrix:
        raise EvaluationError(f"unknown request_class: {request_class}")

    request_matrix = matrix[request_class]
    buckets: Dict[str, List[Dict[str, Any]]] = {
        "always_on": [],
        "on_demand": [],
        "suppressed": [],
    }

    for object_class in candidates:
        if object_class not in request_matrix:
            raise EvaluationError(
                f"unknown object_class '{object_class}' for request_class '{request_class}'"
            )
        rule = request_matrix[object_class]
        serving = rule["serving"]
        item = {
            "object_class": object_class,
            "authority_rank": rule.get("authority_rank"),
            "note": rule.get("note", ""),
        }
        if serving == "forbidden":
            buckets["suppressed"].append(item)
        else:
            buckets[serving].append(item)

    for bucket_name in buckets:
        buckets[bucket_name].sort(
            key=lambda item: (
                item["authority_rank"] is None,
                item["authority_rank"] if item["authority_rank"] is not None else 10**9,
                item["object_class"],
            )
        )

    return {
        "request_class": request_class,
        "always_on": buckets["always_on"],
        "on_demand": buckets["on_demand"],
        "suppressed": buckets["suppressed"],
    }


def run_fixtures() -> Dict[str, Any]:
    matrix_doc = load_json(MATRIX_PATH)
    fixtures_doc = load_json(FIXTURES_PATH)
    results = []

    for fixture in fixtures_doc["fixtures"]:
        actual = evaluate_request(matrix_doc, fixture["request_class"], fixture["candidates"])
        expected = fixture["expected"]
        actual_compact = {
            "always_on": [item["object_class"] for item in actual["always_on"]],
            "on_demand": [item["object_class"] for item in actual["on_demand"]],
            "suppressed": [item["object_class"] for item in actual["suppressed"]],
        }
        expected_normalized = {key: sorted(value) for key, value in expected.items()}
        actual_normalized = {key: sorted(value) for key, value in actual_compact.items()}
        passed = actual_normalized == expected_normalized
        results.append(
            {
                "name": fixture["name"],
                "request_class": fixture["request_class"],
                "passed": passed,
                "expected": expected_normalized,
                "actual": actual_normalized,
            }
        )

    return {
        "matrix_artifact": str(MATRIX_PATH.relative_to(ROOT)),
        "fixtures_artifact": str(FIXTURES_PATH.relative_to(ROOT)),
        "results": results,
        "all_passed": all(item["passed"] for item in results),
    }


if __name__ == "__main__":
    print(json.dumps(run_fixtures(), ensure_ascii=False, indent=2))
