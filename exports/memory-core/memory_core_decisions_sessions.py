#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from memory_core_registry import DEFAULT_ENV_FILE, build_registry_write_sql, persist_sql

ROOT = Path(__file__).resolve().parent

DECISION_ALLOWED_MEMORY_REF_PREFIXES = ("mem_", "wiki_")
DECISION_ALLOWED_TRUTH_REF_PREFIXES = ("ev_", "doc_", "src_", "wiki_", "mem_")
DECISION_ALLOWED_RELATED_REF_PREFIXES = ("mem_", "wiki_", "ev_", "doc_", "src_", "sess_")
SESSION_ALLOWED_MEMORY_REF_PREFIXES = ("mem_", "wiki_")
SESSION_ALLOWED_SOURCE_REF_PREFIXES = ("src_",)
SESSION_ALLOWED_EVIDENCE_REF_PREFIXES = ("ev_",)
SESSION_ALLOWED_SCOPE_REF_PREFIXES = ("task:", "task_", "run:", "run_", "agent:", "agent_", "sess_", "lane:", "lane_")


def _require_prefix(value: str, allowed_prefixes: tuple[str, ...], field_name: str) -> None:
    if not any(str(value).startswith(prefix) for prefix in allowed_prefixes):
        joined = ", ".join(repr(prefix) for prefix in allowed_prefixes)
        raise ValueError(f"{field_name} must start with one of: {joined}; got {value!r}")


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Payload root must be an object")
    return payload


def _normalize_decision(entry: dict[str, Any]) -> dict[str, Any]:
    record = entry.get("record")
    if not isinstance(record, dict):
        raise ValueError("decision.record must be an object")

    record = dict(record)
    if record.get("subtype") != "decision":
        raise ValueError("decision.record.subtype must equal 'decision'")
    _require_prefix(str(record.get("id", "")), ("mem_",), "decision.record.id")
    _require_prefix(str(record.get("source_of_truth_ref", "")), DECISION_ALLOWED_TRUTH_REF_PREFIXES, "decision.record.source_of_truth_ref")

    object_sources = entry.get("object_sources") or []
    object_evidence = entry.get("object_evidence") or []
    spec_assumptions = entry.get("spec_assumptions") or []
    key_memory_refs = entry.get("key_memory_refs") or []
    supporting_object_refs = entry.get("supporting_object_refs") or []

    if not isinstance(object_sources, list) or not isinstance(object_evidence, list):
        raise ValueError("decision.object_sources and decision.object_evidence must be lists when present")
    if not isinstance(spec_assumptions, list) or not isinstance(key_memory_refs, list) or not isinstance(supporting_object_refs, list):
        raise ValueError("decision.spec_assumptions, decision.key_memory_refs, and decision.supporting_object_refs must be lists when present")

    supersedes_rows = []
    for ref in key_memory_refs:
        _require_prefix(str(ref), DECISION_ALLOWED_MEMORY_REF_PREFIXES, "decision.key_memory_refs[]")
        if str(ref).startswith("mem_"):
            supersedes_rows.append({
                "memory_note_id": record["id"],
                "supersedes_id": ref,
            })

    for ref in spec_assumptions:
        _require_prefix(str(ref), DECISION_ALLOWED_TRUTH_REF_PREFIXES, "decision.spec_assumptions[]")

    related_rows = []
    for idx, ref in enumerate(supporting_object_refs):
        _require_prefix(str(ref), DECISION_ALLOWED_RELATED_REF_PREFIXES, "decision.supporting_object_refs[]")
        related_rows.append({
            "memory_note_id": record["id"],
            "related_ref": ref,
            "relation_role": "supporting",
            "position": idx,
        })
    for idx, ref in enumerate(spec_assumptions, start=len(related_rows)):
        related_rows.append({
            "memory_note_id": record["id"],
            "related_ref": ref,
            "relation_role": "context",
            "position": idx,
        })
    if record.get("effective_scope") is None:
        record["effective_scope"] = record.get("scope")

    return {
        "family": "memory_note",
        "record": record,
        "object_sources": object_sources,
        "object_evidence": object_evidence,
        "memory_note_supersedes": supersedes_rows,
        "memory_note_related_refs": related_rows,
        "metadata": {
            "spec_assumptions": spec_assumptions,
            "key_memory_refs": key_memory_refs,
            "supporting_object_refs": supporting_object_refs,
        },
    }


def _normalize_session_capsule(entry: dict[str, Any]) -> dict[str, Any]:
    record = entry.get("record")
    if not isinstance(record, dict):
        raise ValueError("session_capsule.record must be an object")

    record = dict(record)
    _require_prefix(str(record.get("id", "")), ("sess_",), "session_capsule.record.id")
    _require_prefix(str(record.get("scope_ref", "")), SESSION_ALLOWED_SCOPE_REF_PREFIXES, "session_capsule.record.scope_ref")

    object_sources = entry.get("object_sources") or []
    object_evidence = entry.get("object_evidence") or []
    relevant_memory_refs = entry.get("relevant_memory_refs") or []

    if not isinstance(object_sources, list) or not isinstance(object_evidence, list) or not isinstance(relevant_memory_refs, list):
        raise ValueError("session_capsule relation fields must be lists when present")

    memory_rows = []
    for idx, ref in enumerate(relevant_memory_refs):
        _require_prefix(str(ref), SESSION_ALLOWED_MEMORY_REF_PREFIXES, "session_capsule.relevant_memory_refs[]")
        if not str(ref).startswith("mem_"):
            continue
        memory_rows.append({
            "session_capsule_id": record["id"],
            "memory_note_id": ref,
            "position": idx,
        })

    for row in object_sources:
        _require_prefix(str(row.get("source_ref", "")), SESSION_ALLOWED_SOURCE_REF_PREFIXES, "session_capsule.object_sources[].source_ref")
    for row in object_evidence:
        _require_prefix(str(row.get("evidence_id", "")), SESSION_ALLOWED_EVIDENCE_REF_PREFIXES, "session_capsule.object_evidence[].evidence_id")

    return {
        "family": "session_capsule",
        "record": record,
        "object_sources": object_sources,
        "object_evidence": object_evidence,
        "session_capsule_memory_refs": memory_rows,
        "metadata": {
            "relevant_memory_refs": relevant_memory_refs,
        },
    }


def build_domain_payload(payload: dict[str, Any]) -> dict[str, Any]:
    decisions = payload.get("decisions") or []
    session_capsules = payload.get("session_capsules") or []
    if not decisions and not session_capsules:
        raise ValueError("Payload must contain at least one of: decisions[], session_capsules[]")
    if not isinstance(decisions, list) or not isinstance(session_capsules, list):
        raise ValueError("decisions and session_capsules must be lists when present")

    objects = []
    for entry in decisions:
        if not isinstance(entry, dict):
            raise ValueError("decisions[] entries must be objects")
        objects.append(_normalize_decision(entry))
    for entry in session_capsules:
        if not isinstance(entry, dict):
            raise ValueError("session_capsules[] entries must be objects")
        objects.append(_normalize_session_capsule(entry))
    return {"objects": objects}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Write Memory Core decision and session capsule payloads via the registry surface")
    parser.add_argument("payload", help="Path to JSON payload containing decisions[] and/or session_capsules[]")
    parser.add_argument("--persist-mode", choices=["sql-dump", "psql"], default="sql-dump")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE), help="Path to PostgreSQL env file for psql persistence")
    parser.add_argument(
        "--sql-dump-path",
        default=str(ROOT / "state" / "sql-dumps" / "memory-core-decisions-sessions-write.sql"),
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
    domain_payload = _load_json(payload_path)
    registry_payload = build_domain_payload(domain_payload)
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
