#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from memory_core_registry import DEFAULT_ENV_FILE, build_registry_write_sql, persist_sql

ROOT = Path(__file__).resolve().parent
ALLOWED_REF_PREFIXES = ("src_", "ev_", "mem_", "wiki_", "doc_", "sess_")
ALLOWED_LINK_TYPES = ("provenance", "scope", "lifecycle", "semantic", "supersession", "dependency")


def _require_prefix(value: str, field_name: str) -> None:
    if not any(str(value).startswith(prefix) for prefix in ALLOWED_REF_PREFIXES):
        joined = ", ".join(repr(prefix) for prefix in ALLOWED_REF_PREFIXES)
        raise ValueError(f"{field_name} must start with one of: {joined}; got {value!r}")



def _normalize_typed_link(entry: dict[str, Any]) -> dict[str, Any]:
    record = entry.get("record")
    if not isinstance(record, dict):
        raise ValueError("typed_link.record must be an object")

    record = dict(record)
    if record.get("kind") != "typed_link":
        raise ValueError("typed_link.record.kind must equal 'typed_link'")
    if record.get("link_type") not in ALLOWED_LINK_TYPES:
        raise ValueError(f"typed_link.record.link_type must be one of {ALLOWED_LINK_TYPES!r}; got {record.get('link_type')!r}")

    if not str(record.get("id", "")).startswith("link_"):
        raise ValueError(f"typed_link.record.id must start with 'link_'; got {record.get('id')!r}")
    _require_prefix(str(record.get("from_ref", "")), "typed_link.record.from_ref")
    _require_prefix(str(record.get("to_ref", "")), "typed_link.record.to_ref")

    from_ref = str(record.get("from_ref", ""))
    to_ref = str(record.get("to_ref", ""))
    if from_ref == to_ref:
        raise ValueError("typed_link.record.from_ref and typed_link.record.to_ref must differ")

    statement = record.get("statement")
    if statement is not None and not isinstance(statement, str):
        raise ValueError("typed_link.record.statement must be a string or null")

    return {
        "family": "typed_link",
        "record": record,
        "metadata": {
            "stage_boundary": "stage2_storage_only",
            "runtime_graph_logic": "deferred",
        },
    }



def build_domain_payload(payload: dict[str, Any]) -> dict[str, Any]:
    typed_links = payload.get("typed_links") or []
    if not isinstance(typed_links, list) or not typed_links:
        raise ValueError("Payload must contain a non-empty typed_links[] list")

    objects = []
    for entry in typed_links:
        if not isinstance(entry, dict):
            raise ValueError("typed_links[] entries must be objects")
        objects.append(_normalize_typed_link(entry))
    return {"objects": objects}



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write Memory Core typed links via the registry surface")
    parser.add_argument("payload", help="Path to JSON payload containing typed_links[]")
    parser.add_argument("--persist-mode", choices=["sql-dump", "psql"], default="sql-dump")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE), help="Path to PostgreSQL env file for psql persistence")
    parser.add_argument(
        "--sql-dump-path",
        default=str(ROOT / "state" / "sql-dumps" / "memory-core-typed-links-write.sql"),
        help="Where to write generated SQL when persist-mode=sql-dump",
    )
    parser.add_argument(
        "--emit-registry-payload-path",
        default="",
        help="Optional path to also write the expanded registry payload for verification/debugging",
    )
    return parser



def main() -> int:
    args = build_parser().parse_args()
    payload_path = Path(args.payload).resolve()
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Payload root must be an object")
    registry_payload = build_domain_payload(payload)
    if args.emit_registry_payload_path:
        emit_path = Path(args.emit_registry_payload_path).resolve()
        emit_path.parent.mkdir(parents=True, exist_ok=True)
        emit_path.write_text(json.dumps(registry_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sql_script = build_registry_write_sql(registry_payload)
    result = persist_sql(
        sql_script,
        env_file=Path(args.env_file).resolve(),
        dry_run_path=Path(args.sql_dump_path).resolve() if args.persist_mode == "sql-dump" else None,
    )
    print(json.dumps({
        "payload": str(payload_path),
        "registry_object_count": len(registry_payload["objects"]),
        "result": result,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
