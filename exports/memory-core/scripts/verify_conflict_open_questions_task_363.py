#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "outputs" / "task-363-conflict-open-questions-2026-05-07"

CASES = [
    {
        "name": "mixed-authority-ambiguous-architecture",
        "query": "architecture baseline memory core 2026-05-05 2026-05-06",
        "expected_request_class": "architecture_design_recall",
        "expect_conflicts": True,
        "expect_open_questions": True,
        "expect_conflict_types": {"authority_layer_disagreement"},
        "expected_open_question_any_fragments": [
            "highest-priority layer",
            "lower-layer artifacts",
            "competing evidence",
        ],
    },
    {
        "name": "thin-single-artifact-factual",
        "query": "task 347 memory core schema conformance",
        "expected_request_class": "factual_lookup",
        "expect_conflicts": True,
        "expect_open_questions": True,
        "expect_conflict_types": {"freshness_ambiguity"},
        "expected_open_question_any_fragments": [
            "freshest authority",
            "Candidates:",
            "2026-05-06",
            "2026-05-07",
        ],
    },
]


def run_query(query: str, output_name: str) -> dict:
    output_path = OUTDIR / output_name
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
        "--output",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, cwd=ROOT.parent)
    return json.loads(output_path.read_text(encoding="utf-8"))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    results = []

    for case in CASES:
        payload = run_query(case["query"], f"{case['name']}.json")
        serve_pack = payload.get("serve_pack", {})
        conflicts = serve_pack.get("conflicts", [])
        open_questions = serve_pack.get("open_questions", [])
        trace = (serve_pack.get("trace", {}) or {}).get("synthesis", {}) or {}
        classification = payload.get("request_classification", {})

        assert_true(classification.get("request_class") == case["expected_request_class"], f"{case['name']}: unexpected request class")
        assert_true(bool(conflicts) == case["expect_conflicts"], f"{case['name']}: conflicts presence mismatch")
        assert_true(bool(open_questions) == case["expect_open_questions"], f"{case['name']}: open_questions presence mismatch")
        assert_true(trace.get("conflict_count") == len(conflicts), f"{case['name']}: conflict trace mismatch")
        assert_true(trace.get("open_question_count") == len(open_questions), f"{case['name']}: open question trace mismatch")

        if case.get("expect_conflict_types"):
            seen = {conflict.get("type") for conflict in conflicts}
            assert_true(case["expect_conflict_types"].issubset(seen), f"{case['name']}: missing expected conflict types")
        if case.get("expected_open_question_any_fragments"):
            joined = " | ".join(open_questions)
            assert_true(
                any(fragment in joined for fragment in case["expected_open_question_any_fragments"]),
                f"{case['name']}: missing expected open-question semantic invariant",
            )

        results.append({
            "name": case["name"],
            "query": case["query"],
            "request_class": classification.get("request_class"),
            "conflicts": conflicts,
            "open_questions": open_questions,
            "synthesis_trace": trace,
        })

    summary = {"verified": True, "cases": results}
    (OUTDIR / "verification-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
