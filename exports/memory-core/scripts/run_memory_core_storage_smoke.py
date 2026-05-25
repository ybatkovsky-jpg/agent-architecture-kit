#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
ENV_FILE = ROOT / "config" / "memory.env"
STATE_DIR = ROOT / "state" / "sql-dumps"
OUTPUT_DIR = ROOT / "outputs" / "memory-core-storage-smoke"

REGISTRY_FIXTURE = ROOT / "fixtures" / "memory_core_registry_payload.sample.json"
TYPED_LINKS_FIXTURE = ROOT / "fixtures" / "memory_core_typed_links_payload.sample.json"
DECISIONS_FIXTURE = ROOT / "fixtures" / "memory_core_decisions_sessions_payload.sample.json"

REGISTRY_SQL_DUMP = STATE_DIR / "task352-memory-core-registry-smoke.sql"
TYPED_LINKS_SQL_DUMP = STATE_DIR / "task352-memory-core-typed-links-smoke.sql"
DECISIONS_SQL_DUMP = STATE_DIR / "task352-memory-core-decisions-sessions-smoke.sql"
TASK_METADATA_SQL_DUMP = STATE_DIR / "task353-memory-core-task-metadata-smoke.sql"
TASK_METADATA_REINGEST_SQL_DUMP = STATE_DIR / "task354-memory-core-task-metadata-reingest-smoke.sql"
TYPED_LINKS_EXPANDED = STATE_DIR / "task352-memory-core-typed-links-expanded-payload.json"
DECISIONS_EXPANDED = STATE_DIR / "task352-memory-core-decisions-sessions-expanded-payload.json"
TASK_METADATA_EXPANDED = STATE_DIR / "task353-memory-core-task-metadata-expanded-payload.json"
TASK_METADATA_REINGEST_EXPANDED = STATE_DIR / "task354-memory-core-task-metadata-reingest-expanded-payload.json"
SUMMARY_PATH = OUTPUT_DIR / "summary.json"


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=WORKSPACE, text=True, capture_output=True, check=check)


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


def psql_query(sql: str) -> str:
    env = os.environ.copy()
    env.update(load_env_file(ENV_FILE))
    required = ["PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD"]
    missing = [name for name in required if not env.get(name)]
    if missing:
        raise RuntimeError(f"Missing PostgreSQL env vars for smoke query: {', '.join(missing)}")
    result = subprocess.run(
        [
            "psql", "-v", "ON_ERROR_STOP=1", "-X", "-A", "-t",
            "-h", env["PGHOST"], "-p", env["PGPORT"], "-U", env["PGUSER"], "-d", env["PGDATABASE"],
            "-c", sql,
        ],
        cwd=WORKSPACE,
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def assert_eq(actual: str, expected: str, message: str) -> None:
    if actual != expected:
        raise AssertionError(f"{message}: expected {expected!r}, got {actual!r}")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    steps: list[dict[str, object]] = []

    command_sets = [
        [sys.executable, "-m", "py_compile", "pkm-memory/memory_core_registry.py", "pkm-memory/memory_core_typed_links.py", "pkm-memory/memory_core_decisions_sessions.py", "pkm-memory/memory_core_task_metadata.py", "pkm-memory/scripts/verify_memory_core_schema_conformance.py", "pkm-memory/scripts/verify_memory_core_typed_links.py", "pkm-memory/scripts/verify_memory_core_decisions_sessions.py", "pkm-memory/scripts/verify_memory_core_task_metadata.py", "pkm-memory/scripts/verify_memory_core_provenance_link_integrity.py", "pkm-memory/scripts/run_memory_core_storage_smoke.py"],
        ["bash", "-n", "pkm-memory/scripts/bootstrap_storage.sh"],
        ["bash", "-n", "pkm-memory/scripts/validate_storage.sh"],
        [sys.executable, "pkm-memory/scripts/verify_memory_core_schema_conformance.py"],
        [sys.executable, "pkm-memory/scripts/verify_memory_core_typed_links.py"],
        [sys.executable, "pkm-memory/scripts/verify_memory_core_decisions_sessions.py"],
        [sys.executable, "pkm-memory/scripts/verify_memory_core_task_metadata.py"],
        [sys.executable, "pkm-memory/scripts/verify_memory_core_provenance_link_integrity.py"],
        [sys.executable, "pkm-memory/memory_core_registry.py", str(REGISTRY_FIXTURE), "--persist-mode", "sql-dump", "--sql-dump-path", str(REGISTRY_SQL_DUMP)],
        [sys.executable, "pkm-memory/memory_core_typed_links.py", str(TYPED_LINKS_FIXTURE), "--persist-mode", "sql-dump", "--sql-dump-path", str(TYPED_LINKS_SQL_DUMP), "--emit-registry-payload-path", str(TYPED_LINKS_EXPANDED)],
        [sys.executable, "pkm-memory/memory_core_decisions_sessions.py", str(DECISIONS_FIXTURE), "--persist-mode", "sql-dump", "--sql-dump-path", str(DECISIONS_SQL_DUMP), "--emit-registry-payload-path", str(DECISIONS_EXPANDED)],
        [sys.executable, "pkm-memory/memory_core_task_metadata.py", "--task-id", "347", "--task-id", "353", "--task-id", "371", "--persist-mode", "sql-dump", "--sql-dump-path", str(TASK_METADATA_SQL_DUMP), "--emit-registry-payload-path", str(TASK_METADATA_EXPANDED), "--task-related-object-refs-json", '{"347":["wiki_memory_core_stage2"],"353":["mem_task_353_decision_a","wiki_memory_core_stage3"],"371":["mem_agent_arch_split_boundary","wiki_agent_architecture_plan"]}'],
        [sys.executable, "pkm-memory/memory_core_task_metadata.py", "371", "--persist-mode", "sql-dump", "--sql-dump-path", str(TASK_METADATA_REINGEST_SQL_DUMP), "--emit-registry-payload-path", str(TASK_METADATA_REINGEST_EXPANDED), "--task-related-object-refs-json", '{"371":["wiki_agent_architecture_plan"]}'],
        ["bash", "pkm-memory/scripts/bootstrap_storage.sh"],
        ["bash", "pkm-memory/scripts/validate_storage.sh"],
        [sys.executable, "pkm-memory/memory_core_registry.py", str(REGISTRY_FIXTURE), "--persist-mode", "psql", "--env-file", str(ENV_FILE)],
        [sys.executable, "pkm-memory/memory_core_typed_links.py", str(TYPED_LINKS_FIXTURE), "--persist-mode", "psql", "--env-file", str(ENV_FILE)],
        [sys.executable, "pkm-memory/memory_core_decisions_sessions.py", str(DECISIONS_FIXTURE), "--persist-mode", "psql", "--env-file", str(ENV_FILE)],
        [sys.executable, "pkm-memory/memory_core_task_metadata.py", "--task-id", "347", "--task-id", "353", "--task-id", "371", "--persist-mode", "psql", "--env-file", str(ENV_FILE), "--task-related-object-refs-json", '{"347":["wiki_memory_core_stage2"],"353":["mem_task_353_decision_a","wiki_memory_core_stage3"],"371":["mem_agent_arch_split_boundary","wiki_agent_architecture_plan"]}'],
        [sys.executable, "pkm-memory/memory_core_task_metadata.py", "371", "--persist-mode", "psql", "--env-file", str(ENV_FILE), "--task-related-object-refs-json", '{"371":["wiki_agent_architecture_plan"]}'],
    ]

    for cmd in command_sets:
        result = run(cmd)
        steps.append({
            "command": " ".join(cmd),
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        })

    db_checks = {
        "mc_source_records.sample": "SELECT COUNT(*) FROM mc_source_records WHERE id = 'src_sample_registry_root';",
        "mc_evidence_records.sample": "SELECT COUNT(*) FROM mc_evidence_records WHERE id = 'ev_sample_registry_handoff';",
        "mc_memory_notes.registry": "SELECT COUNT(*) FROM mc_memory_notes WHERE id = 'mem_sample_registry_note';",
        "mc_memory_notes.decision": "SELECT COUNT(*) FROM mc_memory_notes WHERE id = 'mem_task351_decision_write_path' AND subtype = 'decision';",
        "mc_session_capsules.sample": "SELECT COUNT(*) FROM mc_session_capsules WHERE id = 'sess_task351_active_run';",
        "mc_typed_links.sample": "SELECT COUNT(*) FROM mc_typed_links WHERE id IN ('link_task350_decision_evidence', 'link_task350_capsule_dependency');",
        "mc_object_sources.registry": "SELECT COUNT(*) FROM mc_object_sources WHERE object_id IN ('ev_sample_registry_handoff', 'mem_sample_registry_note', 'mem_task351_decision_write_path', 'sess_task351_active_run');",
        "mc_object_evidence.registry": "SELECT COUNT(*) FROM mc_object_evidence WHERE object_id IN ('mem_sample_registry_note', 'mem_task351_decision_write_path', 'sess_task351_active_run');",
        "mc_memory_note_supersedes.sample": "SELECT COUNT(*) FROM mc_memory_note_supersedes WHERE memory_note_id = 'mem_task351_decision_write_path' AND supersedes_id = 'mem_sample_registry_note';",
        "mc_memory_note_related_refs.sample": "SELECT COUNT(*) FROM mc_memory_note_related_refs WHERE memory_note_id = 'mem_task351_decision_write_path';",
        "mc_memory_notes.decision_rationale": "SELECT COUNT(*) FROM mc_memory_notes WHERE id = 'mem_task351_decision_write_path' AND rationale IS NOT NULL AND effective_scope = 'task';",
        "mc_session_capsule_memory_refs.sample": "SELECT COUNT(*) FROM mc_session_capsule_memory_refs WHERE session_capsule_id = 'sess_task351_active_run';",
        "mc_source_records.task_system": "SELECT COUNT(*) FROM mc_source_records WHERE id = 'src_task_manager_system';",
        "mc_evidence_records.tasks_batch": "SELECT COUNT(*) FROM mc_evidence_records WHERE id IN ('ev_task_347', 'ev_task_353', 'ev_task_371');",
        "mc_retrieval_documents.tasks_batch": "SELECT COUNT(*) FROM mc_retrieval_documents WHERE id IN ('doc_task_347', 'doc_task_353', 'doc_task_371');",
        "mc_retrieval_documents.task347_status": "SELECT COUNT(*) FROM mc_retrieval_documents WHERE id = 'doc_task_347' AND doc_ref = 'task:347' AND status = 'active' AND index_status = 'active';",
        "mc_retrieval_documents.task371_updated": "SELECT COUNT(*) FROM mc_retrieval_documents WHERE id = 'doc_task_371' AND updated_at = '2026-05-06T11:25:29Z';",
        "mc_typed_links.task_batch_total_after_reingest": "SELECT COUNT(*) FROM mc_typed_links WHERE from_ref IN ('doc_task_347', 'doc_task_353', 'doc_task_371');",
        "mc_typed_links.task371_reingest": "SELECT COUNT(*) FROM mc_typed_links WHERE from_ref = 'doc_task_371';",
        "mc_typed_links.task371_reingest_target": "SELECT COUNT(*) FROM mc_typed_links WHERE from_ref = 'doc_task_371' AND to_ref = 'wiki_agent_architecture_plan';",
    }

    query_results: dict[str, str] = {}
    for name, sql in db_checks.items():
        query_results[name] = psql_query(sql)

    assert_eq(query_results["mc_source_records.sample"], "1", "registry source row missing")
    assert_eq(query_results["mc_evidence_records.sample"], "1", "registry evidence row missing")
    assert_eq(query_results["mc_memory_notes.registry"], "1", "registry memory row missing")
    assert_eq(query_results["mc_memory_notes.decision"], "1", "decision memory row missing")
    assert_eq(query_results["mc_session_capsules.sample"], "1", "session capsule row missing")
    assert_eq(query_results["mc_typed_links.sample"], "2", "typed link rows missing")
    assert_eq(query_results["mc_object_sources.registry"], "4", "object_sources rows mismatch")
    assert_eq(query_results["mc_object_evidence.registry"], "3", "object_evidence rows mismatch")
    assert_eq(query_results["mc_memory_note_supersedes.sample"], "1", "memory_note_supersedes row missing")
    assert_eq(query_results["mc_memory_note_related_refs.sample"], "4", "memory_note_related_refs rows mismatch")
    assert_eq(query_results["mc_memory_notes.decision_rationale"], "1", "decision rationale/effective_scope columns missing")
    assert_eq(query_results["mc_session_capsule_memory_refs.sample"], "2", "session capsule memory refs row mismatch")
    assert_eq(query_results["mc_source_records.task_system"], "1", "task-system source row missing")
    assert_eq(query_results["mc_evidence_records.tasks_batch"], "3", "batch task evidence rows missing")
    assert_eq(query_results["mc_retrieval_documents.tasks_batch"], "3", "batch task retrieval documents missing")
    assert_eq(query_results["mc_retrieval_documents.task347_status"], "1", "task347 retrieval document status mismatch")
    assert_eq(query_results["mc_retrieval_documents.task371_updated"], "1", "task371 updated_at mismatch")
    assert_eq(query_results["mc_typed_links.task_batch_total_after_reingest"], "4", "task typed links should reflect reingest-reduced final set")
    assert_eq(query_results["mc_typed_links.task371_reingest"], "1", "task371 reingest should leave exactly one typed link")
    assert_eq(query_results["mc_typed_links.task371_reingest_target"], "1", "task371 reingest target mismatch")

    summary = {
        "status": "ok",
        "env_file": str(ENV_FILE.relative_to(WORKSPACE)),
        "steps": steps,
        "db_checks": query_results,
        "artifacts": [
            str(REGISTRY_SQL_DUMP.relative_to(WORKSPACE)),
            str(TYPED_LINKS_SQL_DUMP.relative_to(WORKSPACE)),
            str(DECISIONS_SQL_DUMP.relative_to(WORKSPACE)),
            str(TASK_METADATA_SQL_DUMP.relative_to(WORKSPACE)),
            str(TASK_METADATA_REINGEST_SQL_DUMP.relative_to(WORKSPACE)),
            str(TYPED_LINKS_EXPANDED.relative_to(WORKSPACE)),
            str(DECISIONS_EXPANDED.relative_to(WORKSPACE)),
            str(TASK_METADATA_EXPANDED.relative_to(WORKSPACE)),
            str(TASK_METADATA_REINGEST_EXPANDED.relative_to(WORKSPACE)),
        ],
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
