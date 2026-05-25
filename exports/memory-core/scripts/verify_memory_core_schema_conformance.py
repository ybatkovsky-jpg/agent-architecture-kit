#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
import memory_core_registry as registry  # type: ignore

BASELINE_SQL = ROOT / "sql" / "040_memory_core_v1_baseline.sql"
SAMPLE_PAYLOAD = ROOT / "fixtures" / "memory_core_registry_payload.sample.json"
DEFAULT_OUTPUT = ROOT / "outputs" / "memory-core-schema-conformance"

EXPECTED_TABLES: dict[str, str] = {
    "source_record": "mc_source_records",
    "evidence_record": "mc_evidence_records",
    "memory_note": "mc_memory_notes",
    "wiki_page": "mc_wiki_pages",
    "retrieval_document": "mc_retrieval_documents",
    "session_capsule": "mc_session_capsules",
    "typed_link": "mc_typed_links",
}

EXPECTED_RELATIONS: dict[str, tuple[str, list[str]]] = {
    "object_sources": ("mc_object_sources", ["object_id", "source_ref", "position"]),
    "object_evidence": ("mc_object_evidence", ["object_id", "evidence_id", "position", "relation_role"]),
    "memory_note_supersedes": ("mc_memory_note_supersedes", ["memory_note_id", "supersedes_id"]),
    "memory_note_related_refs": ("mc_memory_note_related_refs", ["memory_note_id", "related_ref", "relation_role", "position"]),
    "wiki_backing_memory": ("mc_wiki_backing_memory", ["wiki_page_id", "memory_note_id", "role", "position"]),
    "wiki_backing_evidence": ("mc_wiki_backing_evidence", ["wiki_page_id", "evidence_id", "role", "position"]),
    "retrieval_document_evidence": ("mc_retrieval_document_evidence", ["retrieval_document_id", "evidence_id", "position"]),
    "retrieval_document_chunks": ("mc_retrieval_document_chunks", ["retrieval_document_id", "chunk_ref", "position"]),
    "session_capsule_memory_refs": ("mc_session_capsule_memory_refs", ["session_capsule_id", "memory_note_id", "position"]),
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_sql() -> str:
    return BASELINE_SQL.read_text(encoding="utf-8")


def load_sample_payload() -> dict[str, Any]:
    return json.loads(SAMPLE_PAYLOAD.read_text(encoding="utf-8"))


def verify_declared_contract(sql_text: str) -> list[str]:
    checks: list[str] = []
    assert_true(registry.OBJECT_TABLES == EXPECTED_TABLES, "OBJECT_TABLES diverged from expected Memory Core families")
    checks.append("OBJECT_TABLES matches expected supported runtime families")

    for family, table in EXPECTED_TABLES.items():
        assert_true(f"CREATE TABLE IF NOT EXISTS {table} (" in sql_text, f"Baseline SQL missing table {table}")
        assert_true(registry.ID_PREFIXES[family] in ("src_", "ev_", "mem_", "wiki_", "doc_", "sess_", "link_"), f"Unexpected id prefix for {family}")
        record_columns = registry.OBJECT_COLUMNS[family]
        for column in record_columns:
            assert_true(f"  {column} " in sql_text or f"  {column}\n" in sql_text or f"  {column} TEXT" in sql_text or f"  {column} BOOLEAN" in sql_text or f"  {column} TIMESTAMPTZ" in sql_text, f"Column {column} for {family} not found in baseline SQL")
        checks.append(f"{family} table/column contract present in baseline SQL")

    assert_true(registry.RELATION_TABLES == EXPECTED_RELATIONS, "RELATION_TABLES diverged from expected baseline relation mappings")
    for payload_key, (table, columns) in EXPECTED_RELATIONS.items():
        assert_true(f"CREATE TABLE IF NOT EXISTS {table} (" in sql_text, f"Baseline SQL missing relation table {table}")
        for column in columns:
            assert_true(f"  {column} " in sql_text or f"  {column}\n" in sql_text or f"  {column} TEXT" in sql_text or f"  {column} INTEGER" in sql_text, f"Relation column {table}.{column} not found in baseline SQL")
        checks.append(f"{payload_key} relation contract matches baseline SQL table/columns")

    return checks


def verify_sql_generation(sample_payload: dict[str, Any]) -> list[str]:
    checks: list[str] = []
    sql_script = registry.build_registry_write_sql(sample_payload)
    assert_true(sql_script.startswith("BEGIN;\n"), "Generated SQL must start with BEGIN")
    assert_true(sql_script.rstrip().endswith("COMMIT;"), "Generated SQL must end with COMMIT")
    for table in ["mc_source_records", "mc_evidence_records", "mc_memory_notes"]:
        assert_true(f"INSERT INTO {table}" in sql_script, f"Generated SQL missing insert into {table}")
    for table in ["mc_object_sources", "mc_object_evidence"]:
        assert_true(f"DELETE FROM {table}" in sql_script, f"Generated SQL missing relation replacement delete for {table}")
    checks.append("Sample payload generates transactional object upserts and relation replacement SQL")
    return checks


def verify_negative_contract_checks(sample_payload: dict[str, Any]) -> list[str]:
    checks: list[str] = []

    bad_extra = json.loads(json.dumps(sample_payload))
    bad_extra["objects"][0]["record"]["unexpected_column"] = "boom"
    try:
        registry.validate_payload(bad_extra)
        raise AssertionError("Unexpected object column should fail validation")
    except ValueError as exc:
        assert_true("unexpected columns" in str(exc), f"Unexpected-column error message mismatch: {exc}")
    checks.append("Unexpected record columns are rejected")

    bad_owner = json.loads(json.dumps(sample_payload))
    bad_owner["objects"][1]["object_sources"][0]["object_id"] = "mem_wrong_owner"
    try:
        registry.validate_payload(bad_owner)
        raise AssertionError("Relation owner mismatch should fail validation")
    except ValueError as exc:
        assert_true("must equal owning record id" in str(exc), f"Owner-mismatch error message mismatch: {exc}")
    checks.append("Relation owner-column mismatches are rejected")

    bad_prefix = json.loads(json.dumps(sample_payload))
    bad_prefix["objects"][2]["object_evidence"][0]["evidence_id"] = "src_not_evidence"
    try:
        registry.validate_payload(bad_prefix)
        raise AssertionError("Relation id-prefix mismatch should fail validation")
    except ValueError as exc:
        assert_true("must start with" in str(exc), f"Prefix-mismatch error message mismatch: {exc}")
    checks.append("Relation id-family mismatches are rejected")

    return checks


def main() -> int:
    output_dir = DEFAULT_OUTPUT
    output_dir.mkdir(parents=True, exist_ok=True)

    sql_text = load_sql()
    sample_payload = load_sample_payload()

    all_checks: list[str] = []
    all_checks.extend(verify_declared_contract(sql_text))
    all_checks.extend(verify_sql_generation(sample_payload))
    all_checks.extend(verify_negative_contract_checks(sample_payload))

    report = {
        "status": "ok",
        "baseline_sql": str(BASELINE_SQL.relative_to(ROOT.parent)),
        "sample_payload": str(SAMPLE_PAYLOAD.relative_to(ROOT.parent)),
        "checks": all_checks,
    }
    report_path = output_dir / "verification-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
