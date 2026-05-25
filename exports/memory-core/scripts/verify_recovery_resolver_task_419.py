#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "fixtures" / "recovery-resolver-task-419" / "fixture.json"
OUTDIR = ROOT / "outputs" / "task-419-recovery-resolver-prototype-2026-05-12"
SUMMARY_PATH = OUTDIR / "verification-report.json"
PRECEDENCE_REPORT_PATH = ROOT / "outputs" / "task-418-canonical-recovery-precedence-2026-05-12" / "verification-report.json"

DEFAULT_LAYER_WEIGHTS = {
    "canonical_task_state": 1000,
    "continuation_basis": 950,
    "evidence_record": 900,
    "execution_evidence": 880,
    "memory_note": 500,
    "summary_claim": 250,
    "transcript_residue": 150,
    "ephemeral_projection": 100,
}

DEFAULT_LAYER_REASONS = {
    "canonical_task_state": "canonical task state outranks ephemeral projection",
    "continuation_basis": "explicit continuation basis outranks transcript residue",
    "evidence_record": "evidence-backed artifact outranks summary-only claim",
    "execution_evidence": "memory is reusable context but not execution proof",
    "memory_note": "memory can be reused as context but remains non-proof by default",
    "summary_claim": "summary-only claim is weak without attached evidence",
    "transcript_residue": "transcript-first reconstruction is forbidden by default",
    "ephemeral_projection": "projection cannot displace task truth",
}


def load_precedence_pack() -> dict[str, Any]:
    if PRECEDENCE_REPORT_PATH.exists():
        return json.loads(PRECEDENCE_REPORT_PATH.read_text(encoding="utf-8"))
    return {
        "task_id": 418,
        "all_passed": False,
        "precedence_rules": [],
        "fallback": True,
    }


def classify_candidate(candidate: dict[str, Any], layer_weights: dict[str, int]) -> tuple[int, list[str]]:
    layer = candidate["layer"]
    if layer not in layer_weights:
        raise ValueError(f"unsupported_layer:{layer}")

    reasons = [DEFAULT_LAYER_REASONS[layer]]
    score = layer_weights[layer]
    score += int(candidate.get("truth_rank", 0)) * 3
    score += int(candidate.get("freshness_rank", 0))

    if candidate.get("execution_proof"):
        score += 120
        reasons.append("has execution proof")
    if candidate.get("summary_only"):
        score -= 80
    if candidate.get("ephemeral"):
        score -= 60

    return score, reasons


def resolve_case(case: dict[str, Any], layer_weights: dict[str, int]) -> dict[str, Any]:
    try:
        ranked: list[dict[str, Any]] = []
        for candidate in case.get("candidates", []):
            score, reasons = classify_candidate(candidate, layer_weights)
            ranked.append({**candidate, "score": score, "reasons": reasons})

        ranked.sort(key=lambda item: item["score"], reverse=True)
        winner = ranked[0]

        checks = [
            {
                "name": "winner_anchor",
                "passed": winner["anchor_id"] == case.get("expected_winner"),
                "expected": case.get("expected_winner"),
                "actual": winner["anchor_id"],
            },
            {
                "name": "winner_layer",
                "passed": winner["layer"] == case.get("expected_winner_layer"),
                "expected": case.get("expected_winner_layer"),
                "actual": winner["layer"],
            },
        ]

        return {
            "id": case["id"],
            "query_shape": case["query_shape"],
            "status": "pass",
            "winner": {
                "anchor_id": winner["anchor_id"],
                "layer": winner["layer"],
                "source": winner["source"],
                "score": winner["score"],
                "reasons": winner["reasons"],
            },
            "ranked_candidates": [
                {
                    "anchor_id": item["anchor_id"],
                    "layer": item["layer"],
                    "score": item["score"],
                    "source": item["source"],
                }
                for item in ranked
            ],
            "checks": checks,
            "passed": all(check["passed"] for check in checks),
        }
    except ValueError as exc:
        failure = str(exc)
        expected_failure = case.get("expected_failure")
        passed = bool(expected_failure) and failure.startswith(expected_failure)
        return {
            "id": case["id"],
            "query_shape": case["query_shape"],
            "status": "expected_failure" if passed else "unexpected_failure",
            "failure": failure,
            "checks": [
                {
                    "name": "expected_failure",
                    "passed": passed,
                    "expected_prefix": expected_failure,
                    "actual": failure,
                }
            ],
            "passed": passed,
        }


def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    precedence_pack = load_precedence_pack()
    layer_weights = dict(DEFAULT_LAYER_WEIGHTS)

    results = [resolve_case(case, layer_weights) for case in fixture["cases"]]
    summary = {
        "task_id": 419,
        "title": "A2 — recovery resolver prototype",
        "artifact": "pkm-memory/scripts/verify_recovery_resolver_task_419.py",
        "fixture": str(FIXTURE_PATH.relative_to(ROOT)),
        "contract_version": fixture["contract_version"],
        "precedence_dependency": {
            "path": str(PRECEDENCE_REPORT_PATH.relative_to(ROOT)),
            "present": PRECEDENCE_REPORT_PATH.exists(),
            "task_id": precedence_pack.get("task_id"),
            "all_passed": precedence_pack.get("all_passed"),
        },
        "layer_weights": layer_weights,
        "all_passed": all(result["passed"] for result in results),
        "results": results,
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
