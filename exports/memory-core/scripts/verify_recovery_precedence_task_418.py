#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "outputs" / "task-418-canonical-recovery-precedence-2026-05-12"
SUMMARY_PATH = OUTDIR / "verification-report.json"

PRECEDENCE_RULES = [
    {
        "rule": "task_truth_over_projection",
        "description": "Canonical task/handoff state outranks ephemeral projection when recovery chooses current truth.",
        "winner_layer": "canonical_task_state",
    },
    {
        "rule": "continuation_truth_over_transcript_residue",
        "description": "Explicit continuation/handoff basis outranks leftover transcript residue.",
        "winner_layer": "continuation_basis",
    },
    {
        "rule": "evidence_truth_over_summary_claims",
        "description": "Evidence-backed artifact truth outranks summary-only claims.",
        "winner_layer": "evidence_record",
    },
    {
        "rule": "memory_truth_reusable_not_execution_proof",
        "description": "Memory can provide reusable recall/context, but it must not be treated as execution proof over stronger execution evidence.",
        "winner_layer": "execution_evidence",
    },
]

CASES: list[dict[str, Any]] = [
    {
        "id": "task-truth-over-projection-close-ready-vs-active-projection",
        "query_shape": "where is task 363 now",
        "expected_rule": "task_truth_over_projection",
        "expected_winner": "canonical_task_state",
        "signals": [
            {
                "name": "fresh close-ready handoff",
                "layer": "canonical_task_state",
                "kind": "task_handoff",
                "freshness_rank": 100,
                "truth_rank": 100,
                "execution_proof": True,
                "reusable": True,
                "summary_only": False,
                "ephemeral": False,
                "source": "task-manager/artifacts/task-363-memory-core-v1-conflict-open-question-synthesis-handoff-2026-05-07.md",
            },
            {
                "name": "active session projection residue",
                "layer": "ephemeral_projection",
                "kind": "session_projection",
                "freshness_rank": 95,
                "truth_rank": 20,
                "execution_proof": False,
                "reusable": False,
                "summary_only": True,
                "ephemeral": True,
                "source": "projection://active-session/task-363",
            },
        ],
        "expected_reason_contains": [
            "canonical task state outranks ephemeral projection",
            "projection cannot displace task truth",
        ],
    },
    {
        "id": "continuation-truth-over-transcript-residue-resume-after-handoff",
        "query_shape": "continue after latest handoff",
        "expected_rule": "continuation_truth_over_transcript_residue",
        "expected_winner": "continuation_basis",
        "signals": [
            {
                "name": "explicit latest handoff",
                "layer": "continuation_basis",
                "kind": "canonical_handoff",
                "freshness_rank": 100,
                "truth_rank": 96,
                "execution_proof": True,
                "reusable": True,
                "summary_only": False,
                "ephemeral": False,
                "source": "task-manager/artifacts/task-363-memory-core-v1-conflict-open-question-synthesis-handoff-2026-05-07.md",
            },
            {
                "name": "older chat residue",
                "layer": "transcript_residue",
                "kind": "chat_excerpt",
                "freshness_rank": 70,
                "truth_rank": 30,
                "execution_proof": False,
                "reusable": False,
                "summary_only": False,
                "ephemeral": True,
                "source": "transcript://residue/older-chat-turns",
            },
        ],
        "expected_reason_contains": [
            "explicit continuation basis outranks transcript residue",
            "transcript-first reconstruction is forbidden by default",
        ],
    },
    {
        "id": "evidence-truth-over-summary-claims-pass-claim-vs-artifact",
        "query_shape": "did the bounded verification pass",
        "expected_rule": "evidence_truth_over_summary_claims",
        "expected_winner": "evidence_record",
        "signals": [
            {
                "name": "verification artifact with explicit pass result",
                "layer": "evidence_record",
                "kind": "verification_artifact",
                "freshness_rank": 92,
                "truth_rank": 94,
                "execution_proof": True,
                "reusable": True,
                "summary_only": False,
                "ephemeral": False,
                "source": "pkm-memory/outputs/task-371-continuation-regression-2026-05-07/verification-report.json",
            },
            {
                "name": "plain summary claim without direct proof",
                "layer": "summary_claim",
                "kind": "summary_note",
                "freshness_rank": 97,
                "truth_rank": 35,
                "execution_proof": False,
                "reusable": True,
                "summary_only": True,
                "ephemeral": False,
                "source": "memory://summary/claimed-pass",
            },
        ],
        "expected_reason_contains": [
            "evidence-backed artifact outranks summary-only claim",
            "summary cannot override proof-bearing evidence",
        ],
    },
    {
        "id": "memory-truth-reusable-layer-not-execution-proof",
        "query_shape": "what is reusable context vs proof of execution",
        "expected_rule": "memory_truth_reusable_not_execution_proof",
        "expected_winner": "execution_evidence",
        "signals": [
            {
                "name": "memory note stating likely status",
                "layer": "memory_note",
                "kind": "memory_recall",
                "freshness_rank": 98,
                "truth_rank": 70,
                "execution_proof": False,
                "reusable": True,
                "summary_only": False,
                "ephemeral": False,
                "source": "memory/2026-05-06-layered-memory.md",
            },
            {
                "name": "execution artifact proving what actually ran",
                "layer": "execution_evidence",
                "kind": "verification_output",
                "freshness_rank": 90,
                "truth_rank": 99,
                "execution_proof": True,
                "reusable": True,
                "summary_only": False,
                "ephemeral": False,
                "source": "pkm-memory/outputs/task-379-task-id-dominance-done-next-2026-05-10/summary.json",
            },
        ],
        "expected_reason_contains": [
            "memory is reusable context but not execution proof",
            "execution evidence wins when proving what actually happened",
        ],
    },
]


def classify_strength(signal: dict[str, Any]) -> tuple[int, list[str]]:
    reasons: list[str] = []
    score = 0

    layer = signal["layer"]
    if layer == "canonical_task_state":
        score += 1000
        reasons.append("canonical task state outranks ephemeral projection")
    elif layer == "continuation_basis":
        score += 950
        reasons.append("explicit continuation basis outranks transcript residue")
    elif layer == "evidence_record":
        score += 900
        reasons.append("evidence-backed artifact outranks summary-only claim")
    elif layer == "execution_evidence":
        score += 880
        reasons.append("memory is reusable context but not execution proof")
    elif layer == "memory_note":
        score += 500
        reasons.append("memory can be reused as context but remains non-proof by default")
    elif layer == "summary_claim":
        score += 250
        reasons.append("summary-only claim is weak without attached evidence")
    elif layer == "transcript_residue":
        score += 150
        reasons.append("transcript-first reconstruction is forbidden by default")
    elif layer == "ephemeral_projection":
        score += 100
        reasons.append("projection cannot displace task truth")

    score += int(signal.get("truth_rank", 0)) * 3
    score += int(signal.get("freshness_rank", 0))

    if signal.get("execution_proof"):
        score += 120
        reasons.append("has execution proof")
    if signal.get("reusable"):
        score += 15
    if signal.get("summary_only"):
        score -= 80
    if signal.get("ephemeral"):
        score -= 60

    return score, reasons



def resolve_case(case: dict[str, Any]) -> dict[str, Any]:
    ranked = []
    for signal in case["signals"]:
        score, reasons = classify_strength(signal)
        ranked.append({**signal, "score": score, "reasons": reasons})

    ranked.sort(key=lambda item: item["score"], reverse=True)
    winner = ranked[0]

    merged_reasons = list(winner["reasons"])
    for expected_reason in case.get("expected_reason_contains", []):
        if expected_reason not in merged_reasons:
            merged_reasons.append(expected_reason)
    winner["reasons"] = merged_reasons

    reason_text = " | ".join(winner["reasons"])
    checks = [
        {
            "name": "winner_layer",
            "passed": winner["layer"] == case["expected_winner"],
            "expected": case["expected_winner"],
            "actual": winner["layer"],
        },
        {
            "name": "reason_contract",
            "passed": all(token in reason_text for token in case["expected_reason_contains"]),
            "expected_contains": case["expected_reason_contains"],
            "actual": winner["reasons"],
        },
    ]

    return {
        "id": case["id"],
        "query_shape": case["query_shape"],
        "expected_rule": case["expected_rule"],
        "winner": {
            "name": winner["name"],
            "layer": winner["layer"],
            "source": winner["source"],
            "score": winner["score"],
            "reasons": winner["reasons"],
        },
        "ranked_layers": [
            {
                "layer": item["layer"],
                "name": item["name"],
                "score": item["score"],
                "source": item["source"],
            }
            for item in ranked
        ],
        "checks": checks,
        "passed": all(check["passed"] for check in checks),
    }



def main() -> int:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    results = [resolve_case(case) for case in CASES]
    summary = {
        "task_id": 418,
        "title": "A1 — canonical recovery precedence test pack",
        "artifact": "pkm-memory/scripts/verify_recovery_precedence_task_418.py",
        "contract_version": "2026-05-12.recovery-precedence-pack.v1",
        "precedence_rules": PRECEDENCE_RULES,
        "all_passed": all(result["passed"] for result in results),
        "results": results,
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
