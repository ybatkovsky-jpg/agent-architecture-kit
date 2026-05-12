from datetime import datetime, timedelta

from agent_architecture_kit.memory import choose_canonical_memory, filter_distill_worthy_items
from agent_architecture_kit.models import MemoryItem, TaskSummary
from agent_architecture_kit.tasks import active_tasks, task_lookup
from agent_architecture_kit.truth import resolve_truth_source


NOW = datetime(2026, 5, 12, 0, 0, 0)


def test_filter_distill_worthy_items_keeps_decisions_and_protected_items() -> None:
    items = [
        MemoryItem(id="1", kind="decision", body="d", source="s", updated_at=NOW),
        MemoryItem(id="2", kind="note", body="n", source="s", updated_at=NOW),
        MemoryItem(id="3", kind="note", body="p", source="s", updated_at=NOW, protected=True),
    ]

    result = filter_distill_worthy_items(items)
    assert [item.id for item in result] == ["1", "3"]


def test_choose_canonical_memory_prefers_active_canonical_item() -> None:
    items = [
        MemoryItem(id="old", kind="decision", body="old", source="s", updated_at=NOW - timedelta(days=1), canonical=True),
        MemoryItem(id="new", kind="decision", body="new", source="s", updated_at=NOW, canonical=True),
        MemoryItem(id="sup", kind="decision", body="sup", source="s", updated_at=NOW + timedelta(days=1), canonical=True, superseded_by="new"),
    ]

    result = choose_canonical_memory(items)
    assert result is not None
    assert result.id == "new"


def test_task_lookup_and_active_tasks() -> None:
    tasks = [
        TaskSummary(id="1", title="Open", status="open"),
        TaskSummary(id="2", title="Closed", status="closed"),
    ]

    assert task_lookup(tasks, "1") is not None
    assert task_lookup(tasks, "404") is None
    assert [task.id for task in active_tasks(tasks)] == ["1"]


def test_truth_source_prefers_task_registry_for_task_status() -> None:
    assert resolve_truth_source("task_status") == "task_registry"
    assert resolve_truth_source("unknown") == "memory_then_artifacts"
