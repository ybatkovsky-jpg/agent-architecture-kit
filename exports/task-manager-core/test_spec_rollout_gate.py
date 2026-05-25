from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TEST_ROOT = Path(tempfile.mkdtemp(prefix="tm-test-spec-rollout-gate-"))
os.environ["TASK_MANAGER_ROOT"] = str(TEST_ROOT)

import task_manager as tm  # noqa: E402


SCHEMA = """
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    details TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open',
    priority INTEGER NOT NULL DEFAULT 2,
    created_at TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT '',
    started_at TEXT NOT NULL DEFAULT '',
    waiting_since TEXT NOT NULL DEFAULT '',
    done_at TEXT NOT NULL DEFAULT '',
    due_at TEXT NOT NULL DEFAULT '',
    owner TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT '',
    blocked_reason TEXT NOT NULL DEFAULT '',
    next_action TEXT NOT NULL DEFAULT '',
    context_json TEXT NOT NULL DEFAULT '{}',
    parent_task_id INTEGER NOT NULL DEFAULT 0
)
"""


def _seed_task(con: sqlite3.Connection, *, task_id: int, title: str, details: str, status: str, parent_task_id: int = 0, source: str = "chat") -> None:
    con.execute(
        """
        INSERT INTO tasks (
            id, title, details, status, priority, created_at, updated_at, started_at,
            waiting_since, done_at, due_at, owner, source, blocked_reason,
            next_action, context_json, parent_task_id
        ) VALUES (?, ?, ?, ?, 2, '', '', '', '', '', '', '', ?, '', '', '{}', ?)
        """,
        (task_id, title, details, status, source, parent_task_id),
    )


def _reset_db() -> None:
    if Path(tm.DB_PATH).exists():
        Path(tm.DB_PATH).unlink()


def test_spec_rollout_gate_accepts_shared_parent_sibling_implementation_tasks() -> None:
    _reset_db()
    con = sqlite3.connect(tm.DB_PATH)
    con.execute(SCHEMA)
    _seed_task(
        con,
        task_id=543,
        title="Memory v1 program: from architecture/spec to production serving",
        details="Program parent for Memory v1 rollout.",
        status=tm.STATUS_IN_PROGRESS,
    )
    _seed_task(
        con,
        task_id=544,
        title="Memory v1 / A1: freeze canonical production spec and acceptance contract",
        details="Spec leaf under the shared program parent.",
        status=tm.STATUS_IN_PROGRESS,
        parent_task_id=543,
    )
    _seed_task(
        con,
        task_id=545,
        title="Memory v1 / B1: implement serving plane precedence, eligibility, and lexical fallback",
        details="Implementation rollout leaf under the same program parent.",
        status=tm.STATUS_DONE,
        parent_task_id=543,
    )
    con.commit()
    con.close()

    task, _events = tm.load_task_with_events(544)
    gate = tm.spec_rollout_gate_status(task, tm.STATUS_REVIEW)
    assert gate is not None, gate
    assert gate["passed"] is True, gate
    assert gate["linkage_mode"] == "shared_parent_siblings", gate
    assert gate["linkage_parent_task_id"] == 543, gate
    assert gate["done_execution_children"] == [545], gate
    assert gate["missing"] == [], gate


def test_spec_rollout_gate_still_fails_without_any_implementation_lineage() -> None:
    _reset_db()
    con = sqlite3.connect(tm.DB_PATH)
    con.execute(SCHEMA)
    _seed_task(
        con,
        task_id=600,
        title="Memory policy baseline",
        details="Formalize glossary mapping for acceptance.",
        status=tm.STATUS_IN_PROGRESS,
    )
    con.commit()
    con.close()

    task, _events = tm.load_task_with_events(600)
    gate = tm.spec_rollout_gate_status(task, tm.STATUS_REVIEW)
    assert gate is not None, gate
    assert gate["passed"] is False, gate
    assert gate["linkage_mode"] == "direct_children", gate
    assert "implementation_tasks" in gate["missing"], gate


if __name__ == "__main__":
    test_spec_rollout_gate_accepts_shared_parent_sibling_implementation_tasks()
    test_spec_rollout_gate_still_fails_without_any_implementation_lineage()
    print("ok")
