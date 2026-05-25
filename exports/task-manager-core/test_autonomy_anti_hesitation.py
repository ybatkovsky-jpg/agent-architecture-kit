from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from task_manager import build_coach_summary


def _task(next_action: str = "Prove sufficiency or make the minimal fix") -> dict:
    return {
        "id": 757,
        "title": "tmp anti-hesitation proof",
        "status": "in_progress",
        "next_action": next_action,
        "blocked_reason": "",
        "updated_at": "2030-01-01T00:00:00Z",
        "details": "bounded anti-hesitation proof",
        "context_json": "{}",
    }


def _event(event_id: int, event_type: str, note: str, next_action: str | None = None) -> dict:
    payload = {}
    if next_action is not None:
        payload["next_action"] = next_action
    return {
        "id": event_id,
        "task_id": 757,
        "ts": "2030-01-01T00:00:00Z",
        "event_type": event_type,
        "note": note,
        "payload_json": __import__("json").dumps(payload, ensure_ascii=False),
    }


def main() -> int:
    repeated_action = "Decide whether current contour is already enough"
    stalled_events = [
        _event(1, "status:in_progress", "Implemented executable contour with evidence artifact task-manager/task_manager.py and verified via python3 test_autonomy_router.py", repeated_action),
        _event(2, "note", "Re-checking whether current contour is already enough before deciding proof or minimal fix", repeated_action),
        _event(3, "note", "Re-checking whether current contour is already enough before deciding proof or minimal fix", repeated_action),
    ]
    stalled = build_coach_summary(_task(repeated_action), stalled_events, mode="blind")
    assert stalled["execution_state"] == "resume_now"
    assert "прекрати analysis stall" in stalled["attention_return"]
    assert "либо дай fresh proof" in stalled["completion_pressure"]
    assert stalled["anti_spin"]["repeated_next_action_count"] > 1
    assert stalled["completion_gate"]["evidence_present"] is True

    normal_events = [
        _event(1, "status:in_progress", "Started bounded implementation slice", "Implement the next bounded slice"),
        _event(2, "note", "Wired the next executable step with artifact task-manager/autonomy_router.py", "Run the targeted verification"),
    ]
    normal = build_coach_summary(_task("Run the targeted verification"), normal_events, mode="blind")
    assert normal["execution_state"] == "resume_now"
    assert "прекрати analysis stall" not in normal["attention_return"]
    assert "либо дай fresh proof" not in normal["completion_pressure"]

    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
