#!/usr/bin/env python3
"""Score calculator scaffold for architecture formalization Stage 2."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from load_arch_config import load_arch_config


@dataclass
class ScoreResult:
    trace_id: str
    metric_scores: dict[str, float]
    metric_weights: dict[str, float]
    weighted_metric_total: float
    penalties_applied: list[dict[str, Any]]
    penalty_total: float
    hard_fail: bool
    hard_fail_reasons: list[str]
    final_score: float
    valid_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "metric_scores": self.metric_scores,
            "metric_weights": self.metric_weights,
            "weighted_metric_total": round(self.weighted_metric_total, 6),
            "penalties_applied": self.penalties_applied,
            "penalty_total": round(self.penalty_total, 6),
            "hard_fail": self.hard_fail,
            "hard_fail_reasons": self.hard_fail_reasons,
            "final_score": round(self.final_score, 6),
            "valid_score": round(self.valid_score, 6),
        }


def clamp_score(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, numeric))


def load_trace(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def calculate_score(trace: dict[str, Any], config: dict[str, Any]) -> ScoreResult:
    metric_weights = config.get("scoring", {}).get("metrics", {}) or {}
    penalties_config = config.get("scoring", {}).get("penalties", {}) or {}
    score_inputs = trace.get("evaluation_hooks", {}).get("score_inputs", {}) or {}

    metric_scores = {metric: clamp_score(score_inputs.get(metric, 0.0)) for metric in metric_weights}
    weighted_metric_total = sum(metric_scores[m] * float(metric_weights[m]) for m in metric_weights)

    trace_penalties = score_inputs.get("penalties", []) or []
    penalties_applied: list[dict[str, Any]] = []
    penalty_total = 0.0
    hard_fail = False
    hard_fail_reasons: list[str] = []

    for penalty_id in trace_penalties:
        penalty_rule = penalties_config.get(penalty_id)
        if penalty_rule is None:
            penalties_applied.append({"id": penalty_id, "amount": 0.0, "recognized": False})
            continue

        if isinstance(penalty_rule, dict):
            amount = float(penalty_rule.get("amount", 0.0))
            if penalty_rule.get("hard_fail"):
                hard_fail = True
                hard_fail_reasons.append(penalty_id)
        else:
            amount = float(penalty_rule)

        penalty_total += amount
        penalties_applied.append({"id": penalty_id, "amount": amount, "recognized": True})

    final_score = max(0.0, weighted_metric_total - penalty_total)
    valid_score = 0.0 if hard_fail else final_score

    return ScoreResult(
        trace_id=trace.get("trace_id", "unknown-trace"),
        metric_scores=metric_scores,
        metric_weights={k: float(v) for k, v in metric_weights.items()},
        weighted_metric_total=weighted_metric_total,
        penalties_applied=penalties_applied,
        penalty_total=penalty_total,
        hard_fail=hard_fail,
        hard_fail_reasons=hard_fail_reasons,
        final_score=final_score,
        valid_score=valid_score,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Score a trace against the architecture config")
    parser.add_argument("config", help="Path to architecture config YAML/JSON")
    parser.add_argument("trace", help="Path to emitted trace JSON")
    parser.add_argument("--output", help="Optional output path for JSON score report")
    args = parser.parse_args()

    config = load_arch_config(args.config)
    trace = load_trace(args.trace)
    result = calculate_score(trace, config)
    rendered = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        print(args.output)
    else:
        print(rendered)
