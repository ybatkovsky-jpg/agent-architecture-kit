#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any

from memory_core_registry import DEFAULT_ENV_FILE, build_registry_write_sql, persist_sql

ROOT = Path(__file__).resolve().parent
DEFAULT_TASK_DB = ROOT.parent / "task-manager" / "tasks.db"
DEFAULT_OUTPUT_DIR = ROOT / "state" / "task-ingest"
DEFAULT_SOURCE_ID = "src_task_manager_system"
ALLOWED_RELATED_REF_PREFIXES = ("mem_", "wiki_", "doc_", "ev_", "sess_", "src_")
STATUS_TO_INDEX_STATUS = {
    "open": "active",
    "in_progress": "active",
    "review": "active",
    "waiting_user": "stale",
    "done": "superseded",
}
STATUS_TO_MC_STATUS = {
    "open": "active",
    "in_progress": "active",
    "review": "active",
    "waiting_user": "stale",
    "done": "superseded",
}


def _require_prefix(value: str, field_name: str) -> None:
    if not any(str(value).startswith(prefix) for prefix in ALLOWED_RELATED_REF_PREFIXES):
        joined = ", ".join(repr(prefix) for prefix in ALLOWED_RELATED_REF_PREFIXES)
        raise ValueError(f"{field_name} must start with one of: {joined}; got {value!r}")


def load_task(task_db: Path, task_id: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    con = sqlite3.connect(task_db)
    con.row_factory = sqlite3.Row
    try:
        task = con.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        events = [
            dict(r)
            for r in con.execute(
                "SELECT * FROM task_events WHERE task_id = ? ORDER BY id ASC",
                (task_id,),
            ).fetchall()
        ]
    finally:
        con.close()
    return dict(task), events


def build_task_snapshot(task: dict[str, Any], events: list[dict[str, Any]], related_object_refs: list[str]) -> dict[str, Any]:
    context_json = task.get("context_json") or "{}"
    try:
        context = json.loads(context_json)
    except Exception:
        context = {"_raw_context_json": context_json}
    if not isinstance(context, dict):
        context = {"_raw_context_json": context_json}

    return {
        "task": task,
        "events": events,
        "related_object_refs": related_object_refs,
        "ingest_contract": {
            "authority_owner": "task-system",
            "memory_core_role": "indexed_projection",
            "authority_duplication": "forbidden",
        },
        "derived_context": context,
    }


def build_source_record(*, created_at: str, updated_at: str) -> dict[str, Any]:
    return {
        "family": "source_record",
        "record": {
            "id": DEFAULT_SOURCE_ID,
            "kind": "source_record",
            "status": "active",
            "scope": "project",
            "authority_class": "source_of_truth",
            "serving_class": "never_ambient",
            "created_at": created_at,
            "updated_at": updated_at,
            "source_type": "artifact_bundle",
            "path": "task-manager/tasks.db",
            "owner_scope": "project",
            "retrieval_scope": "explicit_only",
            "enabled": True,
            "created_by": "task-system",
        },
    }


def build_task_registry_objects(
    *,
    task: dict[str, Any],
    events: list[dict[str, Any]],
    snapshot_rel_path: str,
    related_object_refs: list[str],
) -> list[dict[str, Any]]:
    del events  # events are stored in the snapshot artifact, not duplicated into object records.
    task_id = int(task["id"])
    created_at = task["created_at"]
    updated_at = task["updated_at"] or created_at
    task_status = str(task["status"])
    mc_status = STATUS_TO_MC_STATUS.get(task_status, "active")
    index_status = STATUS_TO_INDEX_STATUS.get(task_status, "active")

    evidence_id = f"ev_task_{task_id}"
    document_id = f"doc_task_{task_id}"
    object_sources = [{
        "object_id": document_id,
        "source_ref": DEFAULT_SOURCE_ID,
        "position": 0,
    }]
    object_evidence = [{
        "object_id": document_id,
        "evidence_id": evidence_id,
        "position": 0,
        "relation_role": "supporting",
    }]

    evidence_record = {
        "family": "evidence_record",
        "record": {
            "id": evidence_id,
            "kind": "evidence_record",
            "status": mc_status,
            "scope": "task",
            "authority_class": "source_of_truth",
            "serving_class": "on_demand",
            "created_at": created_at,
            "updated_at": updated_at,
            "source_id": DEFAULT_SOURCE_ID,
            "artifact_ref": snapshot_rel_path,
            "evidence_type": "note",
            "title": f"Task #{task_id} metadata snapshot",
            "provenance_path": "task-manager/tasks.db",
            "provenance_locator": f"tasks.id={task_id}",
            "captured_from": "task-system",
            "created_by": "task-ingest-adapter",
        },
        "object_sources": [{
            "object_id": evidence_id,
            "source_ref": DEFAULT_SOURCE_ID,
            "position": 0,
        }],
    }

    retrieval_document = {
        "family": "retrieval_document",
        "record": {
            "id": document_id,
            "kind": "retrieval_document",
            "status": mc_status,
            "scope": "task",
            "authority_class": "derived_operational",
            "serving_class": "on_demand",
            "created_at": created_at,
            "updated_at": updated_at,
            "created_by": "task-ingest-adapter",
            "source_id": DEFAULT_SOURCE_ID,
            "doc_ref": f"task:{task_id}",
            "index_status": index_status,
        },
        "object_sources": object_sources,
        "object_evidence": object_evidence,
        "retrieval_document_evidence": [{
            "retrieval_document_id": document_id,
            "evidence_id": evidence_id,
            "position": 0,
        }],
        "retrieval_document_chunks": [{
            "retrieval_document_id": document_id,
            "chunk_ref": snapshot_rel_path,
            "position": 0,
        }],
    }

    objects: list[dict[str, Any]] = [evidence_record, retrieval_document]

    for idx, ref in enumerate(related_object_refs):
        _require_prefix(ref, f"related_object_refs[{idx}]")
        objects.append({
            "family": "typed_link",
            "record": {
                "id": f"link_task_{task_id}_{idx + 1}",
                "kind": "typed_link",
                "status": mc_status,
                "scope": "task",
                "authority_class": "derived_operational",
                "serving_class": "never_ambient",
                "created_at": created_at,
                "updated_at": updated_at,
                "created_by": "task-ingest-adapter",
                "link_type": "dependency",
                "from_ref": document_id,
                "to_ref": ref,
                "statement": f"task:{task_id} references related memory object {ref}",
            },
            "metadata": {
                "link_path": "task_to_related_memory_object",
            },
        })

    return objects


def build_registry_payload(
    *,
    task: dict[str, Any],
    events: list[dict[str, Any]],
    snapshot_rel_path: str,
    related_object_refs: list[str],
) -> dict[str, Any]:
    created_at = task["created_at"]
    updated_at = task["updated_at"] or created_at
    objects = [build_source_record(created_at=created_at, updated_at=updated_at)]
    objects.extend(
        build_task_registry_objects(
            task=task,
            events=events,
            snapshot_rel_path=snapshot_rel_path,
            related_object_refs=related_object_refs,
        )
    )
    return {"objects": objects}


def write_snapshot(output_dir: Path, task_id: int, snapshot: dict[str, Any]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"task-{task_id}-snapshot.json"
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def ingest_task(
    *,
    task_db: Path,
    output_dir: Path,
    task_id: int,
    related_object_refs: list[str],
) -> dict[str, Any]:
    task, events = load_task(task_db, task_id)
    snapshot = build_task_snapshot(task, events, related_object_refs)
    snapshot_path = write_snapshot(output_dir, task_id, snapshot)
    snapshot_rel_path = snapshot_path.relative_to(ROOT).as_posix()
    registry_payload = build_registry_payload(
        task=task,
        events=events,
        snapshot_rel_path=snapshot_rel_path,
        related_object_refs=related_object_refs,
    )
    return {
        "task": task,
        "events": events,
        "snapshot": snapshot,
        "snapshot_path": snapshot_path,
        "registry_payload": registry_payload,
    }


def merge_registry_payloads(task_results: list[dict[str, Any]]) -> dict[str, Any]:
    if not task_results:
        raise ValueError("At least one task result is required")
    objects: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    all_created = [result["task"]["created_at"] for result in task_results]
    all_updated = [result["task"]["updated_at"] or result["task"]["created_at"] for result in task_results]
    source_record = build_source_record(created_at=min(all_created), updated_at=max(all_updated))
    objects.append(source_record)
    seen_ids.add(source_record["record"]["id"])

    for result in task_results:
        for entry in result["registry_payload"]["objects"]:
            entry_id = str(entry["record"]["id"])
            if entry_id in seen_ids:
                continue
            seen_ids.add(entry_id)
            if entry["family"] == "source_record" and entry_id == DEFAULT_SOURCE_ID:
                continue
            objects.append(entry)
    return {"objects": objects}


def build_task_registry_write_sql(registry_payload: dict[str, Any], task_ids: list[int]) -> str:
    sql_script = build_registry_write_sql(registry_payload)
    if not task_ids:
        return sql_script
    lines = sql_script.splitlines()
    if len(lines) < 2 or lines[0] != "BEGIN;" or lines[-1] != "COMMIT;":
        raise ValueError("Unexpected registry SQL envelope")
    cleanup_lines = [f"DELETE FROM mc_typed_links WHERE from_ref = 'doc_task_{task_id}';" for task_id in task_ids]
    return "\n".join([lines[0], *cleanup_lines, *lines[1:-1], lines[-1]]) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest Task Manager task metadata into the Memory Core registry surface")
    parser.add_argument("task_id", nargs="?", type=int, help="Single task id from task-manager/tasks.db")
    parser.add_argument("--task-db", default=str(DEFAULT_TASK_DB), help="Path to task-manager sqlite DB")
    parser.add_argument("--persist-mode", choices=["sql-dump", "psql"], default="sql-dump")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE), help="Path to PostgreSQL env file for psql persistence")
    parser.add_argument(
        "--sql-dump-path",
        default=str(ROOT / "state" / "sql-dumps" / "memory-core-task-metadata-write.sql"),
        help="Where to write generated SQL when persist-mode=sql-dump",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for emitted task snapshot JSON artifacts",
    )
    parser.add_argument(
        "--emit-registry-payload-path",
        default="",
        help="Optional path to also write the expanded registry payload for verification/debugging",
    )
    parser.add_argument(
        "--related-object-ref",
        action="append",
        default=[],
        help="Related Memory Core object ref to link from the ingested task document; repeatable",
    )
    parser.add_argument(
        "--task-id",
        dest="task_ids",
        action="append",
        type=int,
        default=[],
        help="Task id to ingest; repeatable for batch mode",
    )
    parser.add_argument(
        "--task-related-object-refs-json",
        default="",
        help="Optional JSON object mapping task id -> [related object refs] for batch/reingest runs",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    task_db = Path(args.task_db).resolve()
    output_dir = Path(args.output_dir).resolve()

    task_ids = list(args.task_ids or [])
    if args.task_id is not None:
        task_ids.insert(0, args.task_id)
    if not task_ids:
        raise SystemExit("Provide a positional task_id or one/more --task-id values")

    per_task_related_refs = {str(task_id): list(args.related_object_ref or []) for task_id in task_ids}
    if args.task_related_object_refs_json:
        extra = json.loads(args.task_related_object_refs_json)
        if not isinstance(extra, dict):
            raise ValueError("--task-related-object-refs-json must decode to an object")
        for key, value in extra.items():
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise ValueError(f"task-related-object-refs-json[{key!r}] must be a list of strings")
            per_task_related_refs[str(key)] = value

    task_results = [
        ingest_task(
            task_db=task_db,
            output_dir=output_dir,
            task_id=task_id,
            related_object_refs=per_task_related_refs.get(str(task_id), []),
        )
        for task_id in task_ids
    ]
    registry_payload = merge_registry_payloads(task_results)

    if args.emit_registry_payload_path:
        emit_path = Path(args.emit_registry_payload_path).resolve()
        emit_path.parent.mkdir(parents=True, exist_ok=True)
        emit_path.write_text(json.dumps(registry_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sql_script = build_task_registry_write_sql(registry_payload, task_ids)
    result = persist_sql(
        sql_script,
        env_file=Path(args.env_file).resolve(),
        dry_run_path=Path(args.sql_dump_path).resolve() if args.persist_mode == "sql-dump" else None,
    )
    print(json.dumps({
        "task_ids": task_ids,
        "task_count": len(task_results),
        "authority_owner": "task-system",
        "snapshots": [
            {
                "task_id": result_item["task"]["id"],
                "task_status": result_item["task"]["status"],
                "snapshot_path": str(result_item["snapshot_path"]),
                "event_count": len(result_item["events"]),
                "related_object_refs": per_task_related_refs.get(str(result_item["task"]["id"]), []),
            }
            for result_item in task_results
        ],
        "registry_object_count": len(registry_payload["objects"]),
        "result": result,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
