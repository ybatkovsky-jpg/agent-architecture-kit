from datetime import datetime

from agent_architecture_kit.memory import filter_distill_worthy_items
from agent_architecture_kit.models import MemoryItem, TaskSummary
from agent_architecture_kit.tasks import active_tasks
from agent_architecture_kit.truth import resolve_truth_source


def main() -> None:
    now = datetime(2026, 5, 12, 0, 0, 0)
    items = [
        MemoryItem(id="1", kind="decision", body="d", source="s", updated_at=now),
        MemoryItem(id="2", kind="note", body="n", source="s", updated_at=now),
    ]
    assert len(filter_distill_worthy_items(items)) == 1

    tasks = [
        TaskSummary(id="1", title="Open", status="open"),
        TaskSummary(id="2", title="Closed", status="closed"),
    ]
    assert len(active_tasks(tasks)) == 1
    assert resolve_truth_source("task_status") == "task_registry"
    print("smoke_ok")


if __name__ == "__main__":
    main()
