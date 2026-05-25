#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "outputs" / "memory-core-task-metadata-verification"
SINGLE_SQL_DUMP_PATH = ROOT / "state" / "sql-dumps" / "task353-memory-core-task-metadata-sample.sql"
SINGLE_REGISTRY_PAYLOAD_PATH = ROOT / "state" / "sql-dumps" / "task353-memory-core-task-metadata-expanded-payload.json"
SINGLE_SNAPSHOT_PATH = ROOT / "state" / "task-ingest" / "task-353-snapshot.json"
BATCH_SQL_DUMP_PATH = ROOT / "state" / "sql-dumps" / "task354-memory-core-task-metadata-batch-sample.sql"
BATCH_REGISTRY_PAYLOAD_PATH = ROOT / "state" / "sql-dumps" / "task354-memory-core-task-metadata-batch-expanded-payload.json"
REINGEST_SQL_DUMP_PATH = ROOT / "state" / "sql-dumps" / "task354-memory-core-task-metadata-reingest-sample.sql"
REINGEST_REGISTRY_PAYLOAD_PATH = ROOT / "state" / "sql-dumps" / "task354-memory-core-task-metadata-reingest-expanded-payload.json"
FIXTURE_PATH = ROOT / "fixtures" / "memory_core_task_metadata_payload.sample.json"
SCRIPT_PATH = ROOT / "memory_core_task_metadata.py"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT.parent, capture_output=True, text=True, check=True)


def index_objects(payload: dict) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for obj in payload["objects"]:
        out.setdefault(obj["family"], []).append(obj)
    return out


def get_record(payload: dict, family: str, record_id: str) -> dict:
    for obj in payload["objects"]:
        if obj["family"] == family and obj["record"]["id"] == record_id:
            return obj
    raise AssertionError(f"Missing {family} record {record_id}")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    single_cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        str(fixture["task_id"]),
        "--persist-mode",
        "sql-dump",
        "--sql-dump-path",
        str(SINGLE_SQL_DUMP_PATH),
        "--emit-registry-payload-path",
        str(SINGLE_REGISTRY_PAYLOAD_PATH),
    ]
    for ref in fixture.get("related_object_refs", []):
        single_cmd.extend(["--related-object-ref", ref])

    single_result = run(single_cmd)
    single_summary = json.loads(single_result.stdout)
    single_payload = json.loads(SINGLE_REGISTRY_PAYLOAD_PATH.read_text(encoding="utf-8"))
    single_snapshot = json.loads(SINGLE_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    single_sql_dump = SINGLE_SQL_DUMP_PATH.read_text(encoding="utf-8")
    single_index = index_objects(single_payload)

    assert len(single_index["retrieval_document"]) == 1, "Expected exactly one retrieval_document"
    assert len(single_index["evidence_record"]) == 1, "Expected exactly one evidence_record"
    assert len(single_index["typed_link"]) == len(fixture["related_object_refs"]), "Typed link count mismatch"

    document_record = single_index["retrieval_document"][0]["record"]
    evidence_record = single_index["evidence_record"][0]["record"]
    assert document_record["doc_ref"] == "task:353"
    assert document_record["index_status"] == "active"
    assert evidence_record["provenance_locator"] == "tasks.id=353"
    assert evidence_record["artifact_ref"] == "state/task-ingest/task-353-snapshot.json"
    assert single_snapshot["task"]["id"] == 353
    assert single_snapshot["ingest_contract"]["authority_owner"] == "task-system"
    assert single_snapshot["ingest_contract"]["authority_duplication"] == "forbidden"
    assert single_snapshot["related_object_refs"] == fixture["related_object_refs"]

    for idx, ref in enumerate(fixture["related_object_refs"], start=1):
        link = get_record(single_payload, "typed_link", f"link_task_353_{idx}")["record"]
        assert link["from_ref"] == "doc_task_353"
        assert link["to_ref"] == ref
        assert link["link_type"] == "dependency"

    required_sql_markers = [
        "INSERT INTO mc_source_records",
        "INSERT INTO mc_evidence_records",
        "INSERT INTO mc_retrieval_documents",
        "INSERT INTO mc_typed_links",
        "task:353",
        "tasks.id=353",
    ]
    for marker in required_sql_markers:
        assert marker in single_sql_dump, f"Missing SQL marker: {marker}"

    batch_task_ids = [347, 353, 371]
    batch_related = {
        "347": ["wiki_memory_core_stage2"],
        "353": fixture["related_object_refs"],
        "371": ["mem_agent_arch_split_boundary", "wiki_agent_architecture_plan"],
    }
    batch_cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "--task-id", "347",
        "--task-id", "353",
        "--task-id", "371",
        "--persist-mode", "sql-dump",
        "--sql-dump-path", str(BATCH_SQL_DUMP_PATH),
        "--emit-registry-payload-path", str(BATCH_REGISTRY_PAYLOAD_PATH),
        "--task-related-object-refs-json", json.dumps(batch_related, ensure_ascii=False),
    ]
    batch_result = run(batch_cmd)
    batch_summary = json.loads(batch_result.stdout)
    batch_payload = json.loads(BATCH_REGISTRY_PAYLOAD_PATH.read_text(encoding="utf-8"))
    batch_sql_dump = BATCH_SQL_DUMP_PATH.read_text(encoding="utf-8")
    batch_index = index_objects(batch_payload)

    assert batch_summary["task_ids"] == batch_task_ids
    assert batch_summary["task_count"] == len(batch_task_ids)
    assert len(batch_index["source_record"]) == 1
    assert len(batch_index["retrieval_document"]) == 3
    assert len(batch_index["evidence_record"]) == 3
    assert len(batch_index["typed_link"]) == 5

    task371_doc = get_record(batch_payload, "retrieval_document", "doc_task_371")
    task371_ev = get_record(batch_payload, "evidence_record", "ev_task_371")
    assert task371_doc["record"]["index_status"] == "active"
    assert task371_doc["record"]["updated_at"] == "2026-05-06T11:25:29Z"
    assert task371_ev["record"]["provenance_locator"] == "tasks.id=371"
    assert "task:371" in batch_sql_dump
    assert "tasks.id=347" in batch_sql_dump
    assert "tasks.id=371" in batch_sql_dump

    reingest_related = {"371": ["wiki_agent_architecture_plan"]}
    reingest_cmd = [
        sys.executable,
        str(SCRIPT_PATH),
        "371",
        "--persist-mode", "sql-dump",
        "--sql-dump-path", str(REINGEST_SQL_DUMP_PATH),
        "--emit-registry-payload-path", str(REINGEST_REGISTRY_PAYLOAD_PATH),
        "--task-related-object-refs-json", json.dumps(reingest_related, ensure_ascii=False),
    ]
    reingest_result = run(reingest_cmd)
    reingest_summary = json.loads(reingest_result.stdout)
    reingest_payload = json.loads(REINGEST_REGISTRY_PAYLOAD_PATH.read_text(encoding="utf-8"))
    reingest_sql = REINGEST_SQL_DUMP_PATH.read_text(encoding="utf-8")
    reingest_index = index_objects(reingest_payload)

    assert reingest_summary["task_ids"] == [371]
    assert reingest_summary["task_count"] == 1
    assert len(reingest_index["typed_link"]) == 1
    reingest_doc = get_record(reingest_payload, "retrieval_document", "doc_task_371")
    assert reingest_doc["record"]["updated_at"] == "2026-05-06T11:25:29Z"
    assert "DELETE FROM mc_typed_links WHERE from_ref = 'doc_task_371';" in reingest_sql
    assert "DELETE FROM mc_object_sources WHERE object_id = 'doc_task_371';" in reingest_sql
    assert "DELETE FROM mc_retrieval_document_chunks WHERE retrieval_document_id = 'doc_task_371';" in reingest_sql
    assert "link_task_371_1" in reingest_sql
    assert "link_task_371_2" not in reingest_sql

    verification = {
        "status": "ok",
        "single_task": {
            "task_id": 353,
            "checks": {
                "retrieval_document_count": len(single_index["retrieval_document"]),
                "evidence_record_count": len(single_index["evidence_record"]),
                "typed_link_count": len(single_index["typed_link"]),
                "snapshot_path": str(SINGLE_SNAPSHOT_PATH),
                "sql_dump_path": str(SINGLE_SQL_DUMP_PATH),
                "registry_payload_path": str(SINGLE_REGISTRY_PAYLOAD_PATH),
            },
            "command": single_cmd,
            "summary": single_summary,
        },
        "batch_task_ids": batch_task_ids,
        "batch_summary": batch_summary,
        "reingest_summary": reingest_summary,
    }
    report_path = OUTPUT_DIR / "verification-report.json"
    report_path.write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verification, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
