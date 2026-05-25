#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_ENV_FILE = ROOT / "config" / "memory.env"

OBJECT_TABLES: dict[str, str] = {
    "source_record": "mc_source_records",
    "evidence_record": "mc_evidence_records",
    "memory_note": "mc_memory_notes",
    "wiki_page": "mc_wiki_pages",
    "retrieval_document": "mc_retrieval_documents",
    "session_capsule": "mc_session_capsules",
    "typed_link": "mc_typed_links",
}

ID_PREFIXES: dict[str, str] = {
    "source_record": "src_",
    "evidence_record": "ev_",
    "memory_note": "mem_",
    "wiki_page": "wiki_",
    "retrieval_document": "doc_",
    "session_capsule": "sess_",
    "typed_link": "link_",
}

ALL_ID_PREFIXES: tuple[str, ...] = tuple(ID_PREFIXES.values())

OBJECT_COLUMNS: dict[str, list[str]] = {
    "source_record": [
        "id", "kind", "status", "scope", "authority_class", "serving_class",
        "created_at", "updated_at", "source_type", "path", "owner_scope",
        "retrieval_scope", "enabled", "created_by",
    ],
    "evidence_record": [
        "id", "kind", "status", "scope", "authority_class", "serving_class",
        "created_at", "updated_at", "source_id", "artifact_ref", "evidence_type",
        "title", "provenance_path", "provenance_locator", "captured_from", "created_by",
    ],
    "memory_note": [
        "id", "kind", "status", "scope", "authority_class", "serving_class",
        "created_at", "updated_at", "created_by", "subtype", "title", "statement",
        "rationale", "why_it_matters", "source_of_truth_ref", "effective_scope", "confidence", "expires_at", "superseded_by",
    ],
    "wiki_page": [
        "id", "kind", "status", "scope", "authority_class", "serving_class",
        "created_at", "updated_at", "created_by", "topic", "summary",
    ],
    "retrieval_document": [
        "id", "kind", "status", "scope", "authority_class", "serving_class",
        "created_at", "updated_at", "created_by", "source_id", "doc_ref", "index_status",
    ],
    "session_capsule": [
        "id", "kind", "status", "scope", "authority_class", "serving_class",
        "created_at", "updated_at", "created_by", "owner", "scope_ref", "goal",
        "current_status", "handoff_ref", "expires_at", "superseded_by",
    ],
    "typed_link": [
        "id", "kind", "status", "scope", "authority_class", "serving_class",
        "created_at", "updated_at", "created_by", "link_type", "from_ref", "to_ref", "statement",
    ],
}

REQUIRED_RECORD_FIELDS: dict[str, set[str]] = {
    "source_record": {"id", "kind", "status", "scope", "authority_class", "serving_class", "created_at", "updated_at", "source_type", "path", "owner_scope", "retrieval_scope", "enabled", "created_by"},
    "evidence_record": {"id", "kind", "status", "scope", "authority_class", "serving_class", "created_at", "updated_at", "source_id", "artifact_ref", "evidence_type", "title", "created_by"},
    "memory_note": {"id", "kind", "status", "scope", "authority_class", "serving_class", "created_at", "updated_at", "created_by", "subtype", "title", "statement", "why_it_matters", "source_of_truth_ref", "confidence"},
    "wiki_page": {"id", "kind", "status", "scope", "authority_class", "serving_class", "created_at", "updated_at", "created_by", "topic", "summary"},
    "retrieval_document": {"id", "kind", "status", "scope", "authority_class", "serving_class", "created_at", "updated_at", "created_by", "source_id", "doc_ref", "index_status"},
    "session_capsule": {"id", "kind", "status", "scope", "authority_class", "serving_class", "created_at", "updated_at", "created_by", "owner", "scope_ref", "goal", "current_status"},
    "typed_link": {"id", "kind", "status", "scope", "authority_class", "serving_class", "created_at", "updated_at", "created_by", "link_type", "from_ref", "to_ref"},
}

RELATION_TABLES = {
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

RELATION_ROW_ID_PREFIXES: dict[str, dict[str, str | tuple[str, ...]]] = {
    "mc_object_sources": {
        "object_id": ALL_ID_PREFIXES,
        "source_ref": "src_",
    },
    "mc_object_evidence": {
        "object_id": ALL_ID_PREFIXES,
        "evidence_id": "ev_",
    },
    "mc_memory_note_supersedes": {
        "memory_note_id": "mem_",
        "supersedes_id": "mem_",
    },
    "mc_memory_note_related_refs": {
        "memory_note_id": "mem_",
        "related_ref": ALL_ID_PREFIXES,
    },
    "mc_wiki_backing_memory": {
        "wiki_page_id": "wiki_",
        "memory_note_id": "mem_",
    },
    "mc_wiki_backing_evidence": {
        "wiki_page_id": "wiki_",
        "evidence_id": "ev_",
    },
    "mc_retrieval_document_evidence": {
        "retrieval_document_id": "doc_",
        "evidence_id": "ev_",
    },
    "mc_retrieval_document_chunks": {
        "retrieval_document_id": "doc_",
    },
    "mc_session_capsule_memory_refs": {
        "session_capsule_id": "sess_",
        "memory_note_id": "mem_",
    },
}

RELATION_CONFIG: dict[str, list[dict[str, Any]]] = {
    "source_record": [],
    "evidence_record": [
        {
            "payload_key": "object_sources",
            "table": "mc_object_sources",
            "owner_column": "object_id",
            "owner_value": lambda record: record["id"],
        }
    ],
    "memory_note": [
        {
            "payload_key": "object_sources",
            "table": "mc_object_sources",
            "owner_column": "object_id",
            "owner_value": lambda record: record["id"],
        },
        {
            "payload_key": "object_evidence",
            "table": "mc_object_evidence",
            "owner_column": "object_id",
            "owner_value": lambda record: record["id"],
        },
        {
            "payload_key": "memory_note_supersedes",
            "table": "mc_memory_note_supersedes",
            "owner_column": "memory_note_id",
            "owner_value": lambda record: record["id"],
        },
        {
            "payload_key": "memory_note_related_refs",
            "table": "mc_memory_note_related_refs",
            "owner_column": "memory_note_id",
            "owner_value": lambda record: record["id"],
        },
    ],
    "wiki_page": [
        {
            "payload_key": "object_sources",
            "table": "mc_object_sources",
            "owner_column": "object_id",
            "owner_value": lambda record: record["id"],
        },
        {
            "payload_key": "object_evidence",
            "table": "mc_object_evidence",
            "owner_column": "object_id",
            "owner_value": lambda record: record["id"],
        },
        {
            "payload_key": "wiki_backing_memory",
            "table": "mc_wiki_backing_memory",
            "owner_column": "wiki_page_id",
            "owner_value": lambda record: record["id"],
        },
        {
            "payload_key": "wiki_backing_evidence",
            "table": "mc_wiki_backing_evidence",
            "owner_column": "wiki_page_id",
            "owner_value": lambda record: record["id"],
        },
    ],
    "retrieval_document": [
        {
            "payload_key": "object_sources",
            "table": "mc_object_sources",
            "owner_column": "object_id",
            "owner_value": lambda record: record["id"],
        },
        {
            "payload_key": "object_evidence",
            "table": "mc_object_evidence",
            "owner_column": "object_id",
            "owner_value": lambda record: record["id"],
        },
        {
            "payload_key": "retrieval_document_evidence",
            "table": "mc_retrieval_document_evidence",
            "owner_column": "retrieval_document_id",
            "owner_value": lambda record: record["id"],
        },
        {
            "payload_key": "retrieval_document_chunks",
            "table": "mc_retrieval_document_chunks",
            "owner_column": "retrieval_document_id",
            "owner_value": lambda record: record["id"],
        },
    ],
    "session_capsule": [
        {
            "payload_key": "object_sources",
            "table": "mc_object_sources",
            "owner_column": "object_id",
            "owner_value": lambda record: record["id"],
        },
        {
            "payload_key": "object_evidence",
            "table": "mc_object_evidence",
            "owner_column": "object_id",
            "owner_value": lambda record: record["id"],
        },
        {
            "payload_key": "session_capsule_memory_refs",
            "table": "mc_session_capsule_memory_refs",
            "owner_column": "session_capsule_id",
            "owner_value": lambda record: record["id"],
        },
    ],
    "typed_link": [],
}

PROVENANCE_REQUIRED_FAMILIES = {"evidence_record", "memory_note", "wiki_page", "retrieval_document", "session_capsule"}
HIGH_LEVEL_OBJECT_FAMILIES = {"memory_note", "wiki_page", "retrieval_document", "session_capsule"}


def load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def ensure_psql_env(env_file: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(load_env_file(env_file))
    required = ["PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD"]
    missing = [name for name in required if not env.get(name)]
    if missing:
        raise RuntimeError(f"Missing PostgreSQL env vars: {', '.join(missing)}")
    return env


def sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def _value_has_prefix(value: Any, expected_prefix: str | tuple[str, ...]) -> bool:
    text = str(value)
    if isinstance(expected_prefix, tuple):
        return any(text.startswith(prefix) for prefix in expected_prefix)
    return text.startswith(expected_prefix)


def validate_relation_rows(
    *,
    family: str,
    payload_key: str,
    table: str,
    owner_column: str,
    owner_value: str,
    rows: list[dict[str, Any]],
) -> None:
    expected_columns = RELATION_TABLES[payload_key][1]
    prefix_contract = RELATION_ROW_ID_PREFIXES.get(table, {})
    for row_index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"{family}.{payload_key}[{row_index}] must be an object")
        missing = [column for column in expected_columns if column not in row]
        if missing:
            raise ValueError(f"Relation row for {table} is missing columns: {', '.join(missing)}")
        unexpected = [column for column in row.keys() if column not in expected_columns]
        if unexpected:
            raise ValueError(f"Relation row for {table} has unexpected columns: {', '.join(unexpected)}")
        if str(row[owner_column]) != str(owner_value):
            raise ValueError(
                f"{family}.{payload_key}[{row_index}].{owner_column} must equal owning record id {owner_value!r}; got {row[owner_column]!r}"
            )
        for column, expected_prefix in prefix_contract.items():
            value = row.get(column)
            if value is None:
                continue
            if not _value_has_prefix(value, expected_prefix):
                raise ValueError(
                    f"{family}.{payload_key}[{row_index}].{column} must start with {expected_prefix!r}; got {value!r}"
                )


def validate_typed_link_record(record: dict[str, Any]) -> None:
    from_ref = str(record.get("from_ref", ""))
    to_ref = str(record.get("to_ref", ""))
    if not _value_has_prefix(from_ref, ALL_ID_PREFIXES):
        raise ValueError(f"typed_link.record.from_ref must start with one of {ALL_ID_PREFIXES!r}; got {from_ref!r}")
    if not _value_has_prefix(to_ref, ALL_ID_PREFIXES):
        raise ValueError(f"typed_link.record.to_ref must start with one of {ALL_ID_PREFIXES!r}; got {to_ref!r}")
    if from_ref == to_ref:
        raise ValueError("typed_link.record.from_ref and typed_link.record.to_ref must differ")


def _relation_rows(entry: dict[str, Any], payload_key: str) -> list[dict[str, Any]]:
    rows = entry.get(payload_key, [])
    if rows is None:
        return []
    if not isinstance(rows, list):
        raise ValueError(f"{entry.get('family')}.{payload_key} must be a list when present")
    return rows


def validate_provenance_contract(entry: dict[str, Any]) -> None:
    family = str(entry["family"])
    record = entry["record"]
    record_id = str(record.get("id", ""))
    object_sources = _relation_rows(entry, "object_sources")
    object_evidence = _relation_rows(entry, "object_evidence")

    if family in PROVENANCE_REQUIRED_FAMILIES and not object_sources:
        raise ValueError(f"{family}.record {record_id!r} must include at least one object_sources row for provenance")

    if family in HIGH_LEVEL_OBJECT_FAMILIES:
        if family == "memory_note":
            if not object_evidence and not str(record.get("source_of_truth_ref", "")):
                raise ValueError(
                    f"{family}.record {record_id!r} must include provenance evidence via object_evidence[] or source_of_truth_ref"
                )
        elif family == "retrieval_document":
            if not _relation_rows(entry, "retrieval_document_evidence"):
                raise ValueError(
                    f"{family}.record {record_id!r} must include retrieval_document_evidence rows for provenance"
                )
        elif family == "session_capsule":
            if not object_evidence and not str(record.get("handoff_ref", "")):
                raise ValueError(
                    f"{family}.record {record_id!r} must include provenance evidence via object_evidence[] or handoff_ref"
                )
        elif family == "wiki_page":
            if not object_evidence and not _relation_rows(entry, "wiki_backing_evidence"):
                raise ValueError(
                    f"{family}.record {record_id!r} must include provenance evidence via object_evidence[] or wiki_backing_evidence[]"
                )


def validate_link_integrity(validated: list[dict[str, Any]]) -> None:
    object_ids = {str(entry["record"]["id"]) for entry in validated}
    seen_typed_links: set[tuple[str, str, str, str]] = set()

    for entry in validated:
        family = str(entry["family"])
        record = entry["record"]
        record_id = str(record["id"])

        if family == "typed_link":
            key = (
                str(record.get("link_type", "")),
                str(record.get("from_ref", "")),
                str(record.get("to_ref", "")),
                str(record.get("statement", "")),
            )
            if key in seen_typed_links:
                raise ValueError(f"Duplicate typed_link edge detected for {record_id!r}: {key!r}")
            seen_typed_links.add(key)

        for row in _relation_rows(entry, "object_sources"):
            if str(row.get("object_id", "")) != record_id:
                raise ValueError(f"{family}.object_sources contains orphan owner ref for {record_id!r}")

        for row in _relation_rows(entry, "object_evidence"):
            if str(row.get("object_id", "")) != record_id:
                raise ValueError(f"{family}.object_evidence contains orphan owner ref for {record_id!r}")
            evidence_id = str(row.get("evidence_id", ""))
            if evidence_id in object_ids:
                target_family = next(obj["family"] for obj in validated if str(obj["record"]["id"]) == evidence_id)
                if target_family != "evidence_record":
                    raise ValueError(
                        f"{family}.object_evidence[{evidence_id!r}] must target an evidence_record when the target is present in-payload"
                    )

        for row in _relation_rows(entry, "memory_note_supersedes"):
            if str(row.get("memory_note_id", "")) != record_id:
                raise ValueError(f"memory_note_supersedes contains orphan owner ref for {record_id!r}")
            if str(row.get("supersedes_id", "")) == record_id:
                raise ValueError(f"memory_note {record_id!r} cannot supersede itself")

        for row in _relation_rows(entry, "memory_note_related_refs"):
            if str(row.get("memory_note_id", "")) != record_id:
                raise ValueError(f"memory_note_related_refs contains orphan owner ref for {record_id!r}")
            if str(row.get("related_ref", "")) == record_id:
                raise ValueError(f"memory_note {record_id!r} cannot relate to itself")

        for row in _relation_rows(entry, "session_capsule_memory_refs"):
            if str(row.get("session_capsule_id", "")) != record_id:
                raise ValueError(f"session_capsule_memory_refs contains orphan owner ref for {record_id!r}")
            if str(row.get("memory_note_id", "")) == record_id:
                raise ValueError(f"session_capsule {record_id!r} cannot reference itself as memory")



def validate_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    objects = payload.get("objects")
    if not isinstance(objects, list) or not objects:
        raise ValueError("Payload must contain a non-empty 'objects' list")

    validated: list[dict[str, Any]] = []
    for index, entry in enumerate(objects, start=1):
        if not isinstance(entry, dict):
            raise ValueError(f"objects[{index}] must be an object")
        family = entry.get("family")
        record = entry.get("record")
        if family not in OBJECT_TABLES:
            raise ValueError(f"objects[{index}] has unsupported family: {family!r}")
        if not isinstance(record, dict):
            raise ValueError(f"objects[{index}].record must be an object")
        record_id = str(record.get("id", ""))
        expected_prefix = ID_PREFIXES[family]
        if not record_id.startswith(expected_prefix):
            raise ValueError(
                f"objects[{index}].record.id must start with {expected_prefix!r} for family {family!r}; got {record_id!r}"
            )
        expected_columns = OBJECT_COLUMNS[family]
        missing = [column for column in expected_columns if column in REQUIRED_RECORD_FIELDS[family] and column not in record]
        if missing:
            raise ValueError(f"objects[{index}].record is missing required columns for {family!r}: {', '.join(missing)}")
        unexpected = [column for column in record.keys() if column not in expected_columns]
        if unexpected:
            raise ValueError(f"objects[{index}].record has unexpected columns for {family!r}: {', '.join(unexpected)}")
        if family == "typed_link":
            validate_typed_link_record(record)
        for relation in RELATION_CONFIG[family]:
            rows = entry.get(relation["payload_key"], [])
            if rows is None:
                rows = []
            if not isinstance(rows, list):
                raise ValueError(f"{family}.{relation['payload_key']} must be a list when present")
            validate_relation_rows(
                family=family,
                payload_key=relation["payload_key"],
                table=relation["table"],
                owner_column=relation["owner_column"],
                owner_value=relation["owner_value"](record),
                rows=rows,
            )
        validate_provenance_contract(entry)
        validated.append(entry)
    validate_link_integrity(validated)
    return validated


def build_upsert_sql(table: str, record: dict[str, Any]) -> str:
    columns = list(record.keys())
    values = [sql_literal(record[column]) for column in columns]
    assignments = [f"{column} = EXCLUDED.{column}" for column in columns if column != "id"]
    return (
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)}) "
        f"ON CONFLICT (id) DO UPDATE SET {', '.join(assignments)};"
    )


def build_relation_replace_sql(table: str, owner_column: str, owner_value: str, rows: list[dict[str, Any]]) -> list[str]:
    statements = [f"DELETE FROM {table} WHERE {owner_column} = {sql_literal(owner_value)};"]
    if not rows:
        return statements
    expected_columns = RELATION_TABLES[next(key for key, value in RELATION_TABLES.items() if value[0] == table)][1]
    for row in rows:
        columns = expected_columns
        values = [sql_literal(row[column]) for column in columns]
        statements.append(f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(values)});")
    return statements


def build_registry_write_sql(payload: dict[str, Any]) -> str:
    statements = ["BEGIN;"]
    for entry in validate_payload(payload):
        family = entry["family"]
        record = entry["record"]
        table = OBJECT_TABLES[family]
        statements.append(build_upsert_sql(table, record))
        for relation in RELATION_CONFIG[family]:
            rows = entry.get(relation["payload_key"], [])
            if rows is None:
                rows = []
            statements.extend(
                build_relation_replace_sql(
                    table=relation["table"],
                    owner_column=relation["owner_column"],
                    owner_value=relation["owner_value"](record),
                    rows=rows,
                )
            )
    statements.append("COMMIT;")
    return "\n".join(statements) + "\n"


def persist_sql(sql_script: str, env_file: Path, dry_run_path: Path | None = None) -> dict[str, Any]:
    if dry_run_path is not None:
        dry_run_path.parent.mkdir(parents=True, exist_ok=True)
        dry_run_path.write_text(sql_script, encoding="utf-8")
        return {"mode": "sql-dump", "path": str(dry_run_path)}

    env = ensure_psql_env(env_file)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".sql", delete=False) as handle:
        handle.write(sql_script)
        sql_path = Path(handle.name)

    try:
        result = subprocess.run(
            [
                "psql", "-v", "ON_ERROR_STOP=1", "-X",
                "-h", env["PGHOST"], "-p", env["PGPORT"], "-U", env["PGUSER"], "-d", env["PGDATABASE"],
                "-f", str(sql_path),
            ],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        return {"mode": "postgres", "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Memory Core registry persistence failed\n"
            f"SQL file: {sql_path}\n"
            f"STDOUT:\n{exc.stdout}\n"
            f"STDERR:\n{exc.stderr}"
        ) from exc
    finally:
        sql_path.unlink(missing_ok=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write Memory Core registry objects into mc_* storage tables")
    parser.add_argument("payload", help="Path to JSON payload containing objects[] entries")
    parser.add_argument("--persist-mode", choices=["sql-dump", "psql"], default="sql-dump")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE), help="Path to PostgreSQL env file for psql persistence")
    parser.add_argument(
        "--sql-dump-path",
        default=str(ROOT / "state" / "sql-dumps" / "memory-core-registry-write.sql"),
        help="Where to write generated SQL when persist-mode=sql-dump",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload_path = Path(args.payload).resolve()
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    sql_script = build_registry_write_sql(payload)
    result = persist_sql(
        sql_script,
        env_file=Path(args.env_file).resolve(),
        dry_run_path=Path(args.sql_dump_path).resolve() if args.persist_mode == "sql-dump" else None,
    )
    print(json.dumps({"payload": str(payload_path), "result": result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
