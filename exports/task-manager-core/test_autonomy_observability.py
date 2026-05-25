from __future__ import annotations

import json
import io
import os
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
TEST_ROOT = Path(tempfile.mkdtemp(prefix="tm-test-autonomy-observability-"))
os.environ["TASK_MANAGER_ROOT"] = str(TEST_ROOT)
os.environ["TASK_MANAGER_RUNTIME_ROOT"] = str(TEST_ROOT / "runtime")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import task_manager as tm_mod
from autonomy_state import load_autonomy_state, save_autonomy_state

TM = WORKSPACE / "task-manager" / "task_manager.py"
TEST_ENV = dict(os.environ)


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run([sys.executable, str(TM), *args], cwd=str(WORKSPACE), env=TEST_ENV, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise AssertionError(f"command failed: {' '.join(args)}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def _create_task(title: str, next_action: str) -> int:
    created = json.loads(_run("add", title, "--details", "autonomy observability proof", "--next-action", next_action).stdout)
    task_id = int(created["task_id"])
    runtime_task_dir = TEST_ROOT / "runtime" / "tasks" / str(task_id)
    runtime_task_dir.mkdir(parents=True, exist_ok=True)
    (runtime_task_dir / "task-brief.v1.json").write_text(json.dumps({
        "task_id": task_id,
        "delivery_target": "telegram:chat:-1003880835934:topic:117",
        "topic_context_ref": "runtime/topics/telegram--1003880835934--117/topic-context.json",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _run("start", str(task_id), "--note", "Starting observability proof", "--next-action", next_action)
    _run(
        "autonomy-init",
        str(task_id),
        "--note",
        "Autonomous execution entered",
        "--next-action",
        next_action,
        "--arm",
        "yes",
        "--execution-mode",
        "current_run",
        "--anchor-kind",
        "current_run",
        "--anchor-id",
        f"task-{task_id}-current-run",
    )
    return task_id


def main() -> int:
    routed_id = _create_task("tmp autonomy observability routed", "Continue bounded slice")
    with tempfile.TemporaryDirectory() as tmp:
        child = Path(tmp) / "child.json"
        child.write_text(json.dumps({
            "status": "review_ready",
            "outcome_class": "frontier_progress",
            "payload_class": "canonical_result",
            "summary": "Checkpoint only",
            "next_action": "Continue bounded slice",
            "done_criteria_met": False,
            "artifact_refs": ["task-manager/test_autonomy_observability.py"],
        }), encoding="utf-8")
        routed = json.loads(_run("autonomy-route", str(routed_id), "--child-result-file", str(child)).stdout)
        assert routed["routing"]["router_decision"] in {"continue_now", "schedule_next_slice"}

    status = json.loads(_run("autonomy-status", str(routed_id)).stdout)
    assert status["autonomy"]["integrity"]["surface_required"] is True
    assert status["autonomy"]["integrity"]["stale_in_progress_reason"] == "significant_progress_not_surfaced"
    route_traces = [e for e in status["autonomy_trace"] if e["event_type"] == "autonomy_trace:route_decision"]
    assert route_traces, status
    last_route = route_traces[-1]["payload"]
    assert last_route["router_decision"] in {"continue_now", "schedule_next_slice"}
    assert last_route["next_action"] == "Continue bounded slice"
    assert "payload_status" in last_route

    forced_id = _create_task("tmp autonomy observability forced ping", "Keep advancing bounded slice")
    state = load_autonomy_state(forced_id)
    state["continuation"] = {
        "router_decision": "continue_now",
        "decision_reason": "Still working the current bounded slice.",
        "surface_reason": "",
        "next_action": "Keep advancing bounded slice",
        "awaiting_user": False,
        "approval_needed": False,
        "risk_alert": False,
        "done_criteria_met": False,
        "parent_goal_open": True,
        "frontier_known": True,
        "frontier_remaining": True,
    }
    state["watchdog"]["anti_silence_due_at"] = "2026-05-20T00:00:00Z"
    state["watchdog"]["last_progress_at"] = "2026-05-19T23:00:00Z"
    save_autonomy_state(forced_id, state)

    import sqlite3
    con = sqlite3.connect(str(TEST_ROOT / "tasks.db"))
    try:
        con.execute("UPDATE tasks SET updated_at = '2026-05-20T00:00:00Z' WHERE id = ?", (forced_id,))
        con.commit()
    finally:
        con.close()

    fake_send = subprocess.CompletedProcess(
        args=["openclaw", "message", "send"],
        returncode=0,
        stdout=json.dumps({"ok": True, "message_id": "forced-progress-1"}),
        stderr="",
    )
    with patch.object(tm_mod.subprocess, "run", return_value=fake_send) as mocked_send:
        with io.StringIO() as buf, redirect_stdout(buf):
            tm_mod.watchdog(SimpleNamespace(hours=1.0, run_resumes=False, cooldown_minutes=30))
            watchdog_payload = json.loads(buf.getvalue())
    send_calls = [call.args[0] for call in mocked_send.call_args_list if call.args]
    assert send_calls, mocked_send.call_args_list
    forced_send = send_calls[-1]
    assert "openclaw" == forced_send[0], forced_send
    assert "message" in forced_send and "send" in forced_send, forced_send
    assert "--channel" in forced_send and forced_send[forced_send.index("--channel") + 1] == "telegram", forced_send
    assert "--target" in forced_send and forced_send[forced_send.index("--target") + 1] == "-1003880835934", forced_send
    assert "--thread-id" in forced_send and forced_send[forced_send.index("--thread-id") + 1] == "117", forced_send
    assert watchdog_payload["excluded_autonomy"], watchdog_payload

    forced_status = json.loads(_run("autonomy-status", str(forced_id)).stdout)
    assert "integrity" in forced_status["autonomy"], forced_status
    assert forced_status["autonomy"]["integrity"]["orphan_evidence_status"] in {"unknown", "needs_surface", "integrity_ok", "orphan_evidence_suspected", "task_binding_missing"}
    forced_external = forced_status["forced_external_progress_ping"]
    assert forced_external is not None, forced_status
    assert forced_external["reason"] == "external_progress_ping_due"
    assert forced_external["single_next_bounded_step"] == "Keep advancing bounded slice"
    forced_traces = [e for e in forced_status["autonomy_trace"] if e["event_type"] == "autonomy_trace:watchdog_forced_ping"]
    assert forced_traces, forced_status
    last_forced = forced_traces[-1]["payload"]
    assert last_forced["forced_reroute_reason"] in {"missing_bounded_step", "long_active_slice_without_visible_outcome"}
    assert last_forced["next_action"] == "Keep advancing bounded slice"
    external_ping_traces = [e for e in forced_status["autonomy_trace"] if e["event_type"] == "autonomy_trace:external_progress_ping_due"]
    assert external_ping_traces, forced_status
    assert external_ping_traces[-1]["payload"]["reason"] == "external_progress_ping_due"
    sent_traces = [e for e in forced_status["autonomy_trace"] if e["event_type"] == "autonomy_trace:external_progress_ping_sent"]
    assert sent_traces, forced_status
    first_fingerprint = str(sent_traces[-1]["payload"].get("fingerprint") or "")
    assert first_fingerprint, sent_traces[-1]
    forced_events_before = [e for e in tm_mod.load_task_with_events(forced_id)[1] if "external_progress" in e["event_type"]]
    with patch.object(tm_mod.subprocess, "run", return_value=fake_send):
        with io.StringIO() as buf, redirect_stdout(buf):
            tm_mod.watchdog(SimpleNamespace(hours=1.0, run_resumes=False, cooldown_minutes=30))
            json.loads(buf.getvalue())
    forced_events_after = [e for e in tm_mod.load_task_with_events(forced_id)[1] if "external_progress" in e["event_type"]]
    assert len(forced_events_after) == len(forced_events_before), (forced_events_before, forced_events_after)

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
