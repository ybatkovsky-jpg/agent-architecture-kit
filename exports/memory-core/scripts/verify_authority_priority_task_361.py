#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "outputs" / "task-361-authority-priority-2026-05-07"


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

    architecture = run_query("architecture spec memory retrieval", "architecture-local.json")
    factual = run_query("memory retrieval runbook", "factual-local.json")

    arch_pack = architecture.get("serve_pack", {})
    fact_pack = factual.get("serve_pack", {})
    arch_items = architecture.get("items", [])
    fact_items = factual.get("items", [])

    assert_true(bool(arch_items), "architecture query returned no items")
    assert_true(bool(fact_items), "factual query returned no items")
    assert_true(arch_pack.get("applied") is True, "architecture serve_pack not marked applied")
    assert_true(fact_pack.get("applied") is True, "factual serve_pack not marked applied")

    arch_trace = arch_pack.get("trace", {})
    fact_trace = fact_pack.get("trace", {})
    assert_true("authority_priority_focus" in arch_trace, "architecture trace missing authority_priority_focus")
    assert_true("authority_priority_focus" in fact_trace, "factual trace missing authority_priority_focus")
    assert_true(isinstance(arch_trace.get("top_authority_layers"), list), "architecture trace missing top_authority_layers")
    assert_true(isinstance(fact_trace.get("top_authority_layers"), list), "factual trace missing top_authority_layers")

    arch_top = arch_items[0].get("authority", {}).get("layer")
    fact_top = fact_items[0].get("authority", {}).get("layer")
    assert_true(arch_top == "evidence_record", f"expected architecture top authority evidence_record, got {arch_top}")
    assert_true(fact_top == "task_state", f"expected factual top authority task_state, got {fact_top}")
    assert_true(arch_trace.get("top_authority_layers", [None])[0] == arch_top, "architecture trace top authority does not match top item")
    assert_true(fact_trace.get("top_authority_layers", [None])[0] == fact_top, "factual trace top authority does not match top item")

    summary = {
        "verified": True,
        "cases": [
            {
                "query": architecture.get("query"),
                "request_class": architecture.get("request_classification", {}).get("request_class"),
                "authority_focus": architecture.get("request_classification", {}).get("authority_priority_focus"),
                "top_authority": arch_top,
                "changed_order": arch_pack.get("changed_order"),
                "trace_changed_order": arch_trace.get("serve_pack_changed_order"),
                "baseline_top_paths": arch_pack.get("baseline_top_paths"),
                "final_top_paths": arch_pack.get("final_top_paths"),
            },
            {
                "query": factual.get("query"),
                "request_class": factual.get("request_classification", {}).get("request_class"),
                "authority_focus": factual.get("request_classification", {}).get("authority_priority_focus"),
                "top_authority": fact_top,
                "changed_order": fact_pack.get("changed_order"),
                "trace_changed_order": fact_trace.get("serve_pack_changed_order"),
                "baseline_top_paths": fact_pack.get("baseline_top_paths"),
                "final_top_paths": fact_pack.get("final_top_paths"),
            },
        ],
    }
    (OUTDIR / "verification-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
