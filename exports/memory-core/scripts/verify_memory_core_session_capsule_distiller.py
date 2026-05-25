#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISTILLER = ROOT / "memory_core_session_capsule_distiller.py"
WRITER = ROOT / "memory_core_decisions_sessions.py"
INPUT = ROOT / "fixtures" / "memory_core_session_capsule_distiller_input.sample.json"
DISTILLED = ROOT / "state" / "sql-dumps" / "task356-memory-core-session-capsule-distilled.json"
SQL_DUMP = ROOT / "state" / "sql-dumps" / "task356-memory-core-session-capsule-distilled.sql"
EXPANDED = ROOT / "state" / "sql-dumps" / "task356-memory-core-session-capsule-expanded.json"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT.parent, text=True, capture_output=True, check=True)


def assert_contains(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"Expected to find {needle!r}")


def main() -> int:
    DISTILLED.parent.mkdir(parents=True, exist_ok=True)

    run([
        sys.executable,
        str(DISTILLER),
        "--input",
        str(INPUT),
        "--output",
        str(DISTILLED),
    ])
    distilled = json.loads(DISTILLED.read_text(encoding="utf-8"))
    objects = distilled.get("objects", [])
    if len(objects) != 1:
        raise AssertionError("Expected exactly one distilled session capsule object")
    capsule = objects[0]
    if capsule["family"] != "session_capsule":
        raise AssertionError("Distiller must emit session_capsule family")
    meta = capsule.get("metadata", {})
    if not meta.get("capsule_text"):
        raise AssertionError("capsule_text must be populated")
    if meta.get("open_questions") != ["Should capsule distillation remain write-only in Stage 3.4?"]:
        raise AssertionError("open_questions should round-trip")
    if len(meta.get("active_entities") or []) != 3:
        raise AssertionError("active_entities should round-trip")
    if len(meta.get("next_steps") or []) != 2:
        raise AssertionError("next_steps should round-trip")
    if len(capsule.get("session_capsule_memory_refs") or []) != 2:
        raise AssertionError("Only mem_* relevant refs should materialize into memory ref rows")
    if capsule["metadata"]["relevant_memory_refs"][-1] != "wiki_memory_core_stage3":
        raise AssertionError("Non-mem relevant refs should be preserved in metadata")

    writer_input = {
        "session_capsules": distilled["session_capsules"],
    }
    writer_path = DISTILLED.with_name("task356-memory-core-session-capsule-writer-input.json")
    writer_path.write_text(json.dumps(writer_input, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    run([
        sys.executable,
        str(WRITER),
        str(writer_path),
        "--persist-mode",
        "sql-dump",
        "--sql-dump-path",
        str(SQL_DUMP),
        "--emit-registry-payload-path",
        str(EXPANDED),
    ])

    sql_text = SQL_DUMP.read_text(encoding="utf-8")
    assert_contains(sql_text, "INSERT INTO mc_session_capsules")
    assert_contains(sql_text, "INSERT INTO mc_session_capsule_memory_refs")
    assert_contains(sql_text, "DELETE FROM mc_session_capsule_memory_refs")
    assert_contains(sql_text, "'sess_task356_active_run'")

    expanded = json.loads(EXPANDED.read_text(encoding="utf-8"))
    if len(expanded.get("objects", [])) != 1:
        raise AssertionError("Expanded writer payload must contain one object")
    out_capsule = expanded["objects"][0]
    if out_capsule["record"]["handoff_ref"] != "task-manager/artifacts/task-355-memory-core-v1-decision-ingest-update-path-handoff-2026-05-06.md":
        raise AssertionError("handoff_ref provenance must persist")
    if out_capsule["object_evidence"][0]["evidence_id"] != "ev_task_356":
        raise AssertionError("evidence provenance must persist")
    if out_capsule["object_sources"][0]["source_ref"] != "src_task_manager_system":
        raise AssertionError("source provenance must persist")

    task_distilled = run([
        sys.executable,
        str(DISTILLER),
        "--task-id",
        "356",
        "--expires-at",
        "2026-05-07T12:30:00Z",
    ])
    task_capsule = json.loads(task_distilled.stdout)["objects"][0]
    task_meta = task_capsule["metadata"]
    if not task_meta.get("next_steps"):
        raise AssertionError("task-db distillation must infer next_steps from task next_action")
    if task_capsule["record"]["scope_ref"] != "task:356":
        raise AssertionError("task-db distillation must target task scope")
    if task_capsule["object_evidence"][0]["evidence_id"] != "ev_task_356":
        raise AssertionError("task-db distillation must infer task evidence ref")

    print("task356 verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
