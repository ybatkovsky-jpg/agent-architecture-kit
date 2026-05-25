#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from memory_core_registry import DEFAULT_ENV_FILE, build_registry_write_sql, ensure_psql_env
OUTPUT_DIR = ROOT / "outputs" / "task-546-lifecycle-slice-verification-2026-05-21"
PAYLOAD_PATH = OUTPUT_DIR / "lifecycle-slice-payload.json"
EXPANDED_PATH = OUTPUT_DIR / "lifecycle-slice-expanded.json"
SQL_PATH = OUTPUT_DIR / "lifecycle-slice-write.sql"
REPORT_PATH = OUTPUT_DIR / "verification-report.json"


def build_payload() -> dict:
    now = "2026-05-21T23:58:00Z"
    return {
        "objects": [
            {
                "family": "source_record",
                "record": {
                    "id": "src_task546_lifecycle_samples",
                    "kind": "source_record",
                    "status": "active",
                    "scope": "task",
                    "authority_class": "source_of_truth",
                    "serving_class": "never_ambient",
                    "created_at": now,
                    "updated_at": now,
                    "source_type": "artifact_bundle",
                    "path": "task-manager/artifacts/task-546-memory-v1-lifecycle-loop-contract-and-rollout-slice-2026-05-20.md",
                    "owner_scope": "project",
                    "retrieval_scope": "explicit_only",
                    "enabled": True,
                    "created_by": "task-546-lifecycle-slice",
                },
            },
            {
                "family": "evidence_record",
                "record": {
                    "id": "ev_task546_ballast_archive_only",
                    "kind": "evidence_record",
                    "status": "archived",
                    "scope": "task",
                    "authority_class": "source_of_truth",
                    "serving_class": "on_demand",
                    "created_at": now,
                    "updated_at": now,
                    "source_id": "src_task546_lifecycle_samples",
                    "artifact_ref": "memory/2026-05-21-task-closure.md",
                    "evidence_type": "artifact",
                    "title": "Archived closure-chat ballast sample",
                    "provenance_path": "memory/2026-05-21-task-closure.md",
                    "provenance_locator": "memory/2026-05-21-task-closure.md#L1",
                    "captured_from": "task546-lifecycle-slice",
                    "created_by": "task-546-lifecycle-slice",
                },
                "object_sources": [
                    {
                        "object_id": "ev_task546_ballast_archive_only",
                        "source_ref": "src_task546_lifecycle_samples",
                        "position": 0,
                    }
                ],
            },
            {
                "family": "evidence_record",
                "record": {
                    "id": "ev_task546_preserve_evidence_only",
                    "kind": "evidence_record",
                    "status": "active",
                    "scope": "task",
                    "authority_class": "source_of_truth",
                    "serving_class": "on_demand",
                    "created_at": now,
                    "updated_at": now,
                    "source_id": "src_task546_lifecycle_samples",
                    "artifact_ref": "memory/2026-05-21-memory-hygiene-distilled.md",
                    "evidence_type": "artifact",
                    "title": "Evidence-only distilled hygiene note",
                    "provenance_path": "memory/2026-05-21-memory-hygiene-distilled.md",
                    "provenance_locator": "memory/2026-05-21-memory-hygiene-distilled.md#L1",
                    "captured_from": "task546-lifecycle-slice",
                    "created_by": "task-546-lifecycle-slice",
                },
                "object_sources": [
                    {
                        "object_id": "ev_task546_preserve_evidence_only",
                        "source_ref": "src_task546_lifecycle_samples",
                        "position": 0,
                    }
                ],
            },
            {
                "family": "memory_note",
                "record": {
                    "id": "mem_task546_promoted_durable_fact",
                    "kind": "memory_note",
                    "status": "active",
                    "scope": "task",
                    "authority_class": "canonical_reusable",
                    "serving_class": "on_demand",
                    "created_at": now,
                    "updated_at": now,
                    "created_by": "task-546-lifecycle-slice",
                    "subtype": "decision",
                    "title": "Memory v1 lifecycle closure needs explicit non-destructive outcome seams",
                    "statement": "Representative lifecycle execution promoted a durable closure fact while keeping ballast archived and risky material out of hot serving.",
                    "why_it_matters": "This gives a real promoted durable note for the lifecycle slice without relying on transcript residue.",
                    "source_of_truth_ref": "ev_task546_preserve_evidence_only",
                    "confidence": "accepted",
                    "expires_at": None,
                    "superseded_by": None,
                },
                "object_sources": [
                    {
                        "object_id": "mem_task546_promoted_durable_fact",
                        "source_ref": "src_task546_lifecycle_samples",
                        "position": 0,
                    }
                ],
                "object_evidence": [
                    {
                        "object_id": "mem_task546_promoted_durable_fact",
                        "evidence_id": "ev_task546_preserve_evidence_only",
                        "position": 0,
                        "relation_role": "supporting",
                    }
                ],
            },
            {
                "family": "memory_note",
                "record": {
                    "id": "mem_task546_hold_for_review",
                    "kind": "memory_note",
                    "status": "draft",
                    "scope": "task",
                    "authority_class": "canonical_reusable",
                    "serving_class": "never_ambient",
                    "created_at": now,
                    "updated_at": now,
                    "created_by": "task-546-lifecycle-slice",
                    "subtype": "decision",
                    "title": "Ambiguous sensitive note held for review",
                    "statement": "Potentially reusable but ambiguous material is preserved as a draft object instead of being destructively deleted or promoted prematurely.",
                    "why_it_matters": "The lifecycle loop needs a safe review buffer for risky residue.",
                    "source_of_truth_ref": "ev_task546_preserve_evidence_only",
                    "confidence": "tentative",
                    "expires_at": None,
                    "superseded_by": None,
                },
                "object_sources": [
                    {
                        "object_id": "mem_task546_hold_for_review",
                        "source_ref": "src_task546_lifecycle_samples",
                        "position": 0,
                    }
                ],
                "object_evidence": [
                    {
                        "object_id": "mem_task546_hold_for_review",
                        "evidence_id": "ev_task546_preserve_evidence_only",
                        "position": 0,
                        "relation_role": "supporting",
                    }
                ],
            },
        ]
    }


def psql_query(env: dict[str, str], sql: str) -> str:
    result = subprocess.run(
        [
            "psql", "-X", "-A", "-F", "\t", "-t",
            "-h", env["PGHOST"], "-p", env["PGPORT"], "-U", env["PGUSER"], "-d", env["PGDATABASE"],
            "-c", sql,
        ],
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_payload()
    PAYLOAD_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    EXPANDED_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    sql_script = build_registry_write_sql(payload)
    SQL_PATH.write_text(sql_script, encoding="utf-8")

    env = ensure_psql_env(DEFAULT_ENV_FILE)
    with NamedTemporaryFile("w", encoding="utf-8", suffix=".sql", delete=False) as handle:
        handle.write(sql_script)
        temp_sql_path = Path(handle.name)
    try:
        subprocess.run(
            [
                "psql", "-v", "ON_ERROR_STOP=1", "-X",
                "-h", env["PGHOST"], "-p", env["PGPORT"], "-U", env["PGUSER"], "-d", env["PGDATABASE"],
                "-f", str(temp_sql_path),
            ],
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        print(exc.stdout)
        print(exc.stderr)
        raise
    finally:
        temp_sql_path.unlink(missing_ok=True)

    verification = {
        "task": 546,
        "artifact": str(Path(__file__).resolve()),
        "payload_path": str(PAYLOAD_PATH.relative_to(ROOT.parent)),
        "sql_path": str(SQL_PATH.relative_to(ROOT.parent)),
        "checks": {
            "promote_active_memory_note": psql_query(env, "select status || '|' || serving_class from mc_memory_notes where id='mem_task546_promoted_durable_fact';"),
            "archive_ballast_evidence": psql_query(env, "select status || '|' || serving_class from mc_evidence_records where id='ev_task546_ballast_archive_only';"),
            "preserve_evidence_only": psql_query(env, "select status || '|' || serving_class from mc_evidence_records where id='ev_task546_preserve_evidence_only';"),
            "hold_for_review_note": psql_query(env, "select status || '|' || serving_class || '|' || confidence from mc_memory_notes where id='mem_task546_hold_for_review';"),
            "hot_serving_excludes_ballast": psql_query(env, "select count(*) from mc_evidence_records where id='ev_task546_ballast_archive_only' and status='active';"),
            "hot_serving_excludes_hold": psql_query(env, "select count(*) from mc_memory_notes where id='mem_task546_hold_for_review' and status='active' and serving_class!='never_ambient';"),
        },
    }
    verification["verdict"] = {
        "promote_path_ok": verification["checks"]["promote_active_memory_note"] == "active|on_demand",
        "archive_demote_ok": verification["checks"]["archive_ballast_evidence"] == "archived|on_demand",
        "preserve_evidence_only_ok": verification["checks"]["preserve_evidence_only"] == "active|on_demand",
        "hold_for_review_ok": verification["checks"]["hold_for_review_note"] == "draft|never_ambient|tentative",
        "ballast_not_hot_served": verification["checks"]["hot_serving_excludes_ballast"] == "0",
        "hold_not_hot_served": verification["checks"]["hot_serving_excludes_hold"] == "0",
    }
    verification["all_passed"] = all(verification["verdict"].values())
    REPORT_PATH.write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verification, ensure_ascii=False, indent=2))
    return 0 if verification["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
