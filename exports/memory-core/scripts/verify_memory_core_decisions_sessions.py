#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PAYLOAD = ROOT / "fixtures" / "memory_core_decisions_sessions_payload.sample.json"
SQL_DUMP = ROOT / "state" / "sql-dumps" / "task351-memory-core-decisions-sessions-sample.sql"
REGISTRY_DUMP = ROOT / "state" / "sql-dumps" / "task351-memory-core-decisions-sessions-expanded-payload.json"
WRITER = ROOT / "memory_core_decisions_sessions.py"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT.parent, text=True, capture_output=True, check=True)


def assert_contains(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"Expected to find {needle!r} in generated output")


def main() -> int:
    SQL_DUMP.parent.mkdir(parents=True, exist_ok=True)
    result = run([
        sys.executable,
        str(WRITER),
        str(SAMPLE_PAYLOAD),
        "--persist-mode",
        "sql-dump",
        "--sql-dump-path",
        str(SQL_DUMP),
        "--emit-registry-payload-path",
        str(REGISTRY_DUMP),
    ])
    output = json.loads(result.stdout)
    if output.get("registry_object_count") != 2:
        raise AssertionError(f"Expected 2 registry objects, got {output.get('registry_object_count')!r}")

    sql_text = SQL_DUMP.read_text(encoding="utf-8")
    assert_contains(sql_text, "INSERT INTO mc_memory_notes")
    assert_contains(sql_text, "'decision'")
    assert_contains(sql_text, "rationale")
    assert_contains(sql_text, "effective_scope")
    assert_contains(sql_text, "INSERT INTO mc_session_capsules")
    assert_contains(sql_text, "INSERT INTO mc_memory_note_supersedes")
    assert_contains(sql_text, "INSERT INTO mc_memory_note_related_refs")
    assert_contains(sql_text, "INSERT INTO mc_session_capsule_memory_refs")
    assert_contains(sql_text, "DELETE FROM mc_session_capsule_memory_refs")

    expanded = json.loads(REGISTRY_DUMP.read_text(encoding="utf-8"))
    objects = expanded.get("objects", [])
    if len(objects) != 2:
        raise AssertionError("Expanded registry payload must contain exactly 2 objects")
    decision = next(obj for obj in objects if obj["family"] == "memory_note")
    capsule = next(obj for obj in objects if obj["family"] == "session_capsule")
    if decision["record"]["subtype"] != "decision":
        raise AssertionError("Decision record subtype mismatch")
    if decision["record"]["rationale"] == "":
        raise AssertionError("Decision rationale should be populated in the bounded Stage 3.3 payload")
    if decision["record"]["effective_scope"] != "task":
        raise AssertionError("Decision effective_scope should round-trip through the registry payload")
    if not decision["memory_note_supersedes"]:
        raise AssertionError("Decision write path should materialize key mem_ refs into mc_memory_note_supersedes rows")
    if len(decision["memory_note_related_refs"]) != 4:
        raise AssertionError("Decision write path should materialize supporting + context related refs")
    if len(capsule["session_capsule_memory_refs"]) != 2:
        raise AssertionError("Only mem_* relevant refs should materialize into mc_session_capsule_memory_refs")
    if capsule["metadata"]["relevant_memory_refs"][-1] != "wiki_runtime_continuity":
        raise AssertionError("Original relevant_memory_refs metadata should be preserved for non-mem refs too")

    print("task351 verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
