from __future__ import annotations

from .models import TaskSummary


def task_lookup(tasks: list[TaskSummary], task_id: str) -> TaskSummary | None:
    for task in tasks:
        if task.id == task_id:
            return task
    return None


def active_tasks(tasks: list[TaskSummary]) -> list[TaskSummary]:
    return [task for task in tasks if task.status in {"open", "active", "blocked"}]
