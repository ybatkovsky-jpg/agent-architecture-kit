#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from memory_core_decisions_sessions import _normalize_session_capsule

ROOT = Path(__file__).resolve().parent
DEFAULT_TASK_DB = ROOT.parent / "task-manager" / "tasks.db"
ALLOWED_STATUS = {"ack", "active", "blocked", "waiting", "done"}


def _slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return value or "session"


def _trim(text: str, limit: int = 240) -> str:
    compact = " ".join(str(text).split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def _ensure_list(value: Any, field: str) -> list[Any]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list when present")
    return value


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Payload root must be an object")
    return payload


def load_task_context(task_db: Path, task_id: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
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


def build_capsule_payload(payload: dict[str, Any]) -> dict[str, Any]:
    session = payload.get("session")
    if not isinstance(session, dict):
        raise ValueError("session must be an object")

    capsule_id = str(session.get("id") or "").strip()
    owner = str(session.get("owner") or "").strip()
    scope_ref = str(session.get("scope_ref") or "").strip()
    goal = str(session.get("goal") or "").strip()
    current_status = str(session.get("current_status") or "").strip()
    handoff_ref = session.get("handoff_ref")
    created_at = str(session.get("created_at") or "").strip()
    updated_at = str(session.get("updated_at") or created_at).strip()
    created_by = str(session.get("created_by") or "session-capsule-distiller").strip()
    scope = str(session.get("scope") or "task").strip()
    status = str(session.get("status") or "active").strip()
    expires_at = session.get("expires_at")
    superseded_by = session.get("superseded_by")

    if not capsule_id.startswith("sess_"):
        raise ValueError("session.id must start with 'sess_'")
    if not owner:
        raise ValueError("session.owner is required")
    if not scope_ref:
        raise ValueError("session.scope_ref is required")
    if not goal:
        raise ValueError("session.goal is required")
    if current_status not in ALLOWED_STATUS:
        raise ValueError(f"session.current_status must be one of {sorted(ALLOWED_STATUS)}")
    if not created_at:
        raise ValueError("session.created_at is required")
    if not updated_at:
        raise ValueError("session.updated_at is required")

    open_questions = [str(x).strip() for x in _ensure_list(payload.get("open_questions"), "open_questions") if str(x).strip()]
    active_entities = [str(x).strip() for x in _ensure_list(payload.get("active_entities"), "active_entities") if str(x).strip()]
    next_steps = [str(x).strip() for x in _ensure_list(payload.get("next_steps"), "next_steps") if str(x).strip()]
    relevant_memory_refs = [str(x).strip() for x in _ensure_list(payload.get("relevant_memory_refs"), "relevant_memory_refs") if str(x).strip()]
    evidence_refs = [str(x).strip() for x in _ensure_list(payload.get("evidence_refs"), "evidence_refs") if str(x).strip()]
    source_refs = [str(x).strip() for x in _ensure_list(payload.get("source_refs"), "source_refs") if str(x).strip()]

    capsule_lines = [
        f"goal: {goal}",
        f"current_status: {current_status}",
    ]
    if next_steps:
        capsule_lines.append("next_steps: " + " | ".join(_trim(step, 120) for step in next_steps[:3]))
    if open_questions:
        capsule_lines.append("open_questions: " + " | ".join(_trim(item, 120) for item in open_questions[:3]))
    if active_entities:
        capsule_lines.append("active_entities: " + ", ".join(active_entities[:5]))
    capsule_text = "\n".join(capsule_lines)

    entry = {
        "record": {
            "id": capsule_id,
            "kind": "session_capsule",
            "status": status,
            "scope": scope,
            "authority_class": "ephemeral_projection",
            "serving_class": "never_ambient",
            "created_at": created_at,
            "updated_at": updated_at,
            "created_by": created_by,
            "owner": owner,
            "scope_ref": scope_ref,
            "goal": goal,
            "current_status": current_status,
            "handoff_ref": handoff_ref,
            "expires_at": expires_at,
            "superseded_by": superseded_by,
        },
        "object_sources": [
            {"object_id": capsule_id, "source_ref": ref, "position": idx}
            for idx, ref in enumerate(source_refs)
        ],
        "object_evidence": [
            {"object_id": capsule_id, "evidence_id": ref, "position": idx, "relation_role": "supporting"}
            for idx, ref in enumerate(evidence_refs)
        ],
        "relevant_memory_refs": relevant_memory_refs,
    }

    normalized = _normalize_session_capsule(entry)
    normalized.setdefault("metadata", {})
    normalized["metadata"].update({
        "capsule_text": capsule_text,
        "open_questions": open_questions,
        "active_entities": active_entities,
        "next_steps": next_steps,
    })
    return {"session_capsules": [entry], "objects": [normalized]}


def build_payload_from_task(task: dict[str, Any], events: list[dict[str, Any]], *, owner: str, created_by: str, expires_at: str | None) -> dict[str, Any]:
    task_id = int(task["id"])
    title = str(task.get("title") or f"task-{task_id}")
    status = str(task.get("status") or "open")
    updated_at = str(task.get("updated_at") or task.get("created_at") or "")
    created_at = updated_at
    next_action = str(task.get("next_action") or "").strip()
    blocked_reason = str(task.get("blocked_reason") or "").strip()

    latest_notes = [str(e.get("note") or "").strip() for e in events if str(e.get("note") or "").strip()]
    open_questions = []
    if blocked_reason:
        open_questions.append(blocked_reason)
    if status != "done" and next_action:
        open_questions.append(f"Pending next action: {next_action}")

    next_steps = [next_action] if next_action else []
    active_entities = [f"task:{task_id}", _slug(title)]
    evidence_refs = [f"ev_task_{task_id}"]
    source_refs = ["src_task_manager_system"]
    handoff_ref = None
    for note in reversed(latest_notes):
        match = re.search(r"(task-manager/artifacts/\S+\.md)", note)
        if match:
            handoff_ref = match.group(1)
            break

    return {
        "session": {
            "id": f"sess_task_{task_id}_distilled",
            "owner": owner,
            "scope_ref": f"task:{task_id}",
            "goal": _trim(title, 180),
            "current_status": "done" if status == "done" else ("blocked" if blocked_reason else "active"),
            "handoff_ref": handoff_ref,
            "created_at": created_at,
            "updated_at": updated_at,
            "created_by": created_by,
            "scope": "task",
            "status": "active" if status != "done" else "superseded",
            "expires_at": expires_at,
        },
        "open_questions": open_questions[:3],
        "active_entities": active_entities,
        "next_steps": next_steps[:3],
        "relevant_memory_refs": [],
        "evidence_refs": evidence_refs,
        "source_refs": source_refs,
        "latest_notes": latest_notes[-3:],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a bounded Memory Core session capsule payload from task/session context")
    parser.add_argument("--input", help="Path to JSON payload describing session/open_questions/active_entities/next_steps")
    parser.add_argument("--task-id", type=int, help="Build bounded capsule input from task-manager/tasks.db")
    parser.add_argument("--task-db", default=str(DEFAULT_TASK_DB), help="Path to tasks.db when using --task-id")
    parser.add_argument("--owner", default="subagent")
    parser.add_argument("--created-by", default="session-capsule-distiller")
    parser.add_argument("--expires-at", default="")
    parser.add_argument("--output", default="", help="Optional path to write distilled payload JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if bool(args.input) == bool(args.task_id):
        raise ValueError("Use exactly one of --input or --task-id")

    if args.input:
        payload = load_json(Path(args.input).resolve())
    else:
        task, events = load_task_context(Path(args.task_db).resolve(), args.task_id)
        payload = build_payload_from_task(
            task,
            events,
            owner=args.owner,
            created_by=args.created_by,
            expires_at=args.expires_at or None,
        )

    distilled = build_capsule_payload(payload)
    text = json.dumps(distilled, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        path = Path(args.output).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
