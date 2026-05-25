from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import task_manager as tm
from blind_judge_validator import _extract_inline_anchors

TM = WORKSPACE / "task-manager" / "task_manager.py"
TEST_ROOT = Path(tempfile.mkdtemp(prefix="tm-test-blind-judge-anchor-guard-"))
os.environ["TASK_MANAGER_ROOT"] = str(TEST_ROOT)
TEST_ENV = dict(os.environ)


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run([sys.executable, str(TM), *args], cwd=str(WORKSPACE), env=TEST_ENV, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise AssertionError(f"command failed: {' '.join(args)}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


def main() -> int:
    created = json.loads(
        _run(
            "add",
            "tmp blind judge anchor guard",
            "--details",
            (
                "Exercise blind judge summary on an anchor-heavy note that previously caused "
                "regex/anchor classification to hang in sync post-transition feedback."
            ),
            "--next-action",
            "Move through lifecycle",
        ).stdout
    )
    task_id = int(created["task_id"])

    _run("start", str(task_id), "--note", "Start anchor-heavy guard repro", "--next-action", "Prepare heavy inline proof")

    heavy_segments = [f"semantic/path/{i:03d}" for i in range(200)]
    extracted = _extract_inline_anchors(" ".join(heavy_segments))
    assert len(extracted) <= 64, extracted

    review_note = (
        "CLAIMED_OUTCOME: bounded anchor-heavy review note is accepted without sync blind-judge hang. "
        "EVIDENCE: task-manager/test_blind_judge_anchor_guard.py records the regression path, while "
        f"{' '.join(heavy_segments)} task-manager/test_blind_judge_anchor_guard.py prove mixed inline anchor candidates exist. "
        "ANCHOR: /home/openclaw/.openclaw/workspace/task-manager/test_blind_judge_anchor_guard.py. "
        "VERIFICATION: review transition plus a subsequent coach run both complete under timeout and preserve a strong gate outcome."
    )
    review_proc = _run(
        "review",
        str(task_id),
        "--note",
        review_note,
        "--next-action",
        "Close after review",
    )
    review_payload = json.loads(review_proc.stdout)
    assert review_payload["status"] == "review", review_payload
    assert review_payload["judge_feedback"]["quality_verdict"] in {"mixed", "strong"}, review_payload

    done_note = (
        "CLAIMED_OUTCOME: bounded anchor-heavy task closes cleanly after review without sync blind-judge hang. "
        "EVIDENCE: task-manager/test_blind_judge_anchor_guard.py and the review/done transitions provide the fresh closure proof, while "
        "task-manager/test_blind_judge_anchor_guard.py remains the durable anchor. "
        "ANCHOR: /home/openclaw/.openclaw/workspace/task-manager/test_blind_judge_anchor_guard.py. "
        "VERIFICATION: coach mode blind finishes successfully after done, confirming the synchronous post-transition judge path no longer stalls. "
        "DONE_CLAIM_EVIDENCE_MATCH: the task asks for a lifecycle pass through the anchor-heavy path, and these transitions plus the test file provide that exact evidence."
    )
    done_proc = _run("done", str(task_id), "--note", done_note)
    done_payload = json.loads(done_proc.stdout)
    assert done_payload["status"] == "done", done_payload
    assert done_payload["judge_feedback"]["execution_state"] == "done", done_payload

    coach_proc = _run("coach", str(task_id), "--mode", "blind", "--format", "json")
    coach_payload = json.loads(coach_proc.stdout)
    assert coach_payload["execution_state"] == "done", coach_payload
    assert coach_payload["quality_verdict"] == "strong", coach_payload

    con = sqlite3.connect(TEST_ROOT / "tasks.db")
    events = con.execute(
        "select event_type from task_events where task_id = ? and event_type = 'blind_judge_feedback'",
        (task_id,),
    ).fetchall()
    assert events, events

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
