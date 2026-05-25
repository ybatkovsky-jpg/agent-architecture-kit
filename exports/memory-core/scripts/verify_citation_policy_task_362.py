#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = ROOT / "outputs" / "task-362-citation-policy-2026-05-07"


CASES = [
    {
        "name": "architecture-memory-wiki-shape",
        "query": "show the architecture spec baseline for memory retrieval",
        "expected_request_class": "architecture_design_recall",
        "expected_answer_shape": "memory_wiki_synthesis",
        "expected_citation_mode": "memory_wiki_backing",
        "expected_fact_ref_style": "document_locator",
        "expected_min_cited_facts": 2,
    },
    {
        "name": "factual-direct-source-shape",
        "query": "task-107-postgres-activation-and-first-live-ingest",
        "expected_request_class": "factual_lookup",
        "expected_answer_shape": "fact_trace",
        "expected_citation_mode": "direct_source_path_section",
        "expected_fact_ref_style": "chunk_locator",
        "expected_min_cited_facts": 2,
    },
    {
        "name": "artifact-trace-direct-file-shape",
        "query": "which file contains the source citation path",
        "expected_request_class": "artifact_source_trace_request",
        "expected_answer_shape": "artifact_trace",
        "expected_citation_mode": "direct_artifact_file_refs",
        "expected_fact_ref_style": "source_locator",
        "expected_min_cited_facts": 2,
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
        classification = payload.get("request_classification", {})
        serve_pack = payload.get("serve_pack", {})
        policy = serve_pack.get("citation_policy", {})
        cited_facts = serve_pack.get("cited_facts", [])
        trace = serve_pack.get("trace", {})

        assert_true(classification.get("request_class") == case["expected_request_class"], f"{case['name']}: unexpected request_class")
        assert_true(policy.get("answer_shape") == case["expected_answer_shape"], f"{case['name']}: unexpected answer_shape")
        assert_true(policy.get("citation_mode") == case["expected_citation_mode"], f"{case['name']}: unexpected citation_mode")
        assert_true(policy.get("fact_ref_style") == case["expected_fact_ref_style"], f"{case['name']}: unexpected fact_ref_style")
        assert_true(policy.get("expected_citation") == classification.get("expected_citation"), f"{case['name']}: expected_citation not carried into policy")
        assert_true(len(cited_facts) >= case["expected_min_cited_facts"], f"{case['name']}: insufficient cited_facts")
        assert_true(bool(trace.get("top_authority_layers")), f"{case['name']}: missing trace top_authority_layers")
        assert_true(bool(serve_pack.get("authority_notes")), f"{case['name']}: missing authority_notes")

        refs = [ref for fact in cited_facts for ref in fact.get("refs", [])]
        if case["expected_fact_ref_style"] == "chunk_locator":
            assert_true(any("#chunk-" in ref and "::" in ref for ref in refs), f"{case['name']}: missing chunk locator refs")
        elif case["expected_fact_ref_style"] == "source_locator":
            assert_true(all("::" not in ref for ref in refs), f"{case['name']}: expected direct file refs, got chunk refs")
        elif case["expected_fact_ref_style"] == "document_locator":
            assert_true(any("(" in ref and ")" in ref for ref in refs), f"{case['name']}: expected document locator refs")

        results.append({
            "name": case["name"],
            "query": case["query"],
            "request_class": classification.get("request_class"),
            "expected_citation": classification.get("expected_citation"),
            "answer_shape": policy.get("answer_shape"),
            "citation_mode": policy.get("citation_mode"),
            "fact_ref_style": policy.get("fact_ref_style"),
            "cited_fact_count": len(cited_facts),
            "sample_refs": refs[:3],
            "top_authority_layers": trace.get("top_authority_layers"),
        })

    summary = {"verified": True, "cases": results}
    (OUTDIR / "verification-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
