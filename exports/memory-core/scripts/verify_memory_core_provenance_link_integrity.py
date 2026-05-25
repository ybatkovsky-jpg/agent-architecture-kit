#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_WRITER = ROOT / "memory_core_registry.py"
TASK_WRITER = ROOT / "memory_core_task_metadata.py"
DECISION_WRITER = ROOT / "memory_core_decisions_sessions.py"
TYPED_LINK_WRITER = ROOT / "memory_core_typed_links.py"
OUTPUT_DIR = ROOT / "outputs" / "task-357-provenance-link-integrity"
SQL_DUMP = OUTPUT_DIR / "task357-registry-smoke.sql"
REPORT = OUTPUT_DIR / "verification-report.json"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT.parent, text=True, capture_output=True, check=True)


def run_expect_failure(payload: dict, label: str, expected_substring: str) -> dict[str, str]:
    payload_path = OUTPUT_DIR / f"{label}.payload.json"
    sql_path = OUTPUT_DIR / f"{label}.sql"
    payload_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(REGISTRY_WRITER), str(payload_path), "--persist-mode", "sql-dump", "--sql-dump-path", str(sql_path)],
        cwd=ROOT.parent,
        text=True,
        capture_output=True,
    )
    if result.returncode == 0:
        raise AssertionError(f"Expected {label} payload to fail validation")
    failure_text = (result.stderr or "") + (result.stdout or "")
    if expected_substring not in failure_text:
        raise AssertionError(f"Expected failure for {label} to include {expected_substring!r}; got: {failure_text}")
    return {"label": label, "matched": expected_substring}


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Positive anchors through existing ingest writers.
    task_positive = json.loads(run([
        sys.executable,
        str(TASK_WRITER),
        "357",
        "--persist-mode",
        "sql-dump",
        "--sql-dump-path",
        str(OUTPUT_DIR / "task357-task-metadata.sql"),
        "--emit-registry-payload-path",
        str(OUTPUT_DIR / "task357-task-metadata-expanded.json"),
        "--task-related-object-refs-json",
        '{"357":["wiki_memory_core_stage3","mem_task351_decision_write_path"]}',
    ]).stdout)

    decision_positive = json.loads(run([
        sys.executable,
        str(DECISION_WRITER),
        str(ROOT / "fixtures" / "memory_core_decisions_sessions_payload.sample.json"),
        "--persist-mode",
        "sql-dump",
        "--sql-dump-path",
        str(OUTPUT_DIR / "task357-decisions-sessions.sql"),
        "--emit-registry-payload-path",
        str(OUTPUT_DIR / "task357-decisions-sessions-expanded.json"),
    ]).stdout)

    typed_positive = json.loads(run([
        sys.executable,
        str(TYPED_LINK_WRITER),
        str(ROOT / "fixtures" / "memory_core_typed_links_payload.sample.json"),
        "--persist-mode",
        "sql-dump",
        "--sql-dump-path",
        str(OUTPUT_DIR / "task357-typed-links.sql"),
        "--emit-registry-payload-path",
        str(OUTPUT_DIR / "task357-typed-links-expanded.json"),
    ]).stdout)

    # Negative provenance/link integrity cases directly against the registry validator.
    failures = []

    failures.append(run_expect_failure(
        {
            "objects": [{
                "family": "retrieval_document",
                "record": {
                    "id": "doc_task357_orphan",
                    "kind": "retrieval_document",
                    "status": "active",
                    "scope": "task",
                    "authority_class": "derived_operational",
                    "serving_class": "on_demand",
                    "created_at": "2026-05-06T00:00:00Z",
                    "updated_at": "2026-05-06T00:00:00Z",
                    "created_by": "task357-test",
                    "source_id": "src_task_manager_system",
                    "doc_ref": "task:357",
                    "index_status": "active"
                },
                "object_sources": [{"object_id": "doc_task357_orphan", "source_ref": "src_task_manager_system", "position": 0}],
                "object_evidence": [],
                "retrieval_document_evidence": [],
                "retrieval_document_chunks": [{"retrieval_document_id": "doc_task357_orphan", "chunk_ref": "state/task-ingest/task-357-snapshot.json", "position": 0}]
            }]
        },
        "negative-missing-retrieval-provenance",
        "must include retrieval_document_evidence rows for provenance",
    ))

    failures.append(run_expect_failure(
        {
            "objects": [{
                "family": "memory_note",
                "record": {
                    "id": "mem_task357_orphan_decision",
                    "kind": "memory_note",
                    "status": "active",
                    "scope": "task",
                    "authority_class": "canonical_reusable",
                    "serving_class": "on_demand",
                    "created_at": "2026-05-06T00:00:00Z",
                    "updated_at": "2026-05-06T00:00:00Z",
                    "created_by": "task357-test",
                    "subtype": "decision",
                    "title": "orphan decision",
                    "statement": "missing evidence provenance",
                    "rationale": "",
                    "why_it_matters": "test",
                    "source_of_truth_ref": "",
                    "effective_scope": "task",
                    "confidence": "draft",
                    "expires_at": None,
                    "superseded_by": None
                },
                "object_sources": [{"object_id": "mem_task357_orphan_decision", "source_ref": "src_task_manager_system", "position": 0}],
                "object_evidence": [],
                "memory_note_supersedes": [],
                "memory_note_related_refs": []
            }]
        },
        "negative-memory-note-without-evidence",
        "must include provenance evidence via object_evidence[] or source_of_truth_ref",
    ))

    failures.append(run_expect_failure(
        {
            "objects": [
                {
                    "family": "typed_link",
                    "record": {
                        "id": "link_task357_dup_a",
                        "kind": "typed_link",
                        "status": "active",
                        "scope": "task",
                        "authority_class": "derived_operational",
                        "serving_class": "never_ambient",
                        "created_at": "2026-05-06T00:00:00Z",
                        "updated_at": "2026-05-06T00:00:00Z",
                        "created_by": "task357-test",
                        "link_type": "dependency",
                        "from_ref": "doc_task_357",
                        "to_ref": "wiki_memory_core_stage3",
                        "statement": "duplicate edge"
                    }
                },
                {
                    "family": "typed_link",
                    "record": {
                        "id": "link_task357_dup_b",
                        "kind": "typed_link",
                        "status": "active",
                        "scope": "task",
                        "authority_class": "derived_operational",
                        "serving_class": "never_ambient",
                        "created_at": "2026-05-06T00:00:01Z",
                        "updated_at": "2026-05-06T00:00:01Z",
                        "created_by": "task357-test",
                        "link_type": "dependency",
                        "from_ref": "doc_task_357",
                        "to_ref": "wiki_memory_core_stage3",
                        "statement": "duplicate edge"
                    }
                }
            ]
        },
        "negative-duplicate-typed-link",
        "Duplicate typed_link edge detected",
    ))

    failures.append(run_expect_failure(
        {
            "objects": [{
                "family": "session_capsule",
                "record": {
                    "id": "sess_task357_orphan",
                    "kind": "session_capsule",
                    "status": "active",
                    "scope": "task",
                    "authority_class": "ephemeral_projection",
                    "serving_class": "never_ambient",
                    "created_at": "2026-05-06T00:00:00Z",
                    "updated_at": "2026-05-06T00:00:00Z",
                    "created_by": "task357-test",
                    "owner": "subagent",
                    "scope_ref": "task:357",
                    "goal": "test",
                    "current_status": "active",
                    "handoff_ref": "",
                    "expires_at": None,
                    "superseded_by": None
                },
                "object_sources": [{"object_id": "sess_task357_orphan", "source_ref": "src_task_manager_system", "position": 0}],
                "object_evidence": [],
                "session_capsule_memory_refs": []
            }]
        },
        "negative-session-without-provenance",
        "must include provenance evidence via object_evidence[] or handoff_ref",
    ))

    report = {
        "task": 357,
        "verdict": "done",
        "positive_runs": {
            "task_metadata": {
                "registry_object_count": task_positive.get("registry_object_count"),
                "sql": str(OUTPUT_DIR / "task357-task-metadata.sql"),
                "expanded": str(OUTPUT_DIR / "task357-task-metadata-expanded.json"),
            },
            "decisions_sessions": {
                "registry_object_count": decision_positive.get("registry_object_count"),
                "sql": str(OUTPUT_DIR / "task357-decisions-sessions.sql"),
                "expanded": str(OUTPUT_DIR / "task357-decisions-sessions-expanded.json"),
            },
            "typed_links": {
                "registry_object_count": typed_positive.get("registry_object_count"),
                "sql": str(OUTPUT_DIR / "task357-typed-links.sql"),
                "expanded": str(OUTPUT_DIR / "task357-typed-links-expanded.json"),
            },
        },
        "negative_checks": failures,
        "changed_scope": [
            "registry-layer provenance contract enforcement",
            "registry-layer link integrity enforcement",
            "cross-writer verification anchors for task metadata / decisions+capsules / typed links",
        ],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
