from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class MemoryItem:
    id: str
    kind: str
    body: str
    source: str
    updated_at: datetime
    subject: str | None = None
    tags: list[str] = field(default_factory=list)
    protected: bool = False
    canonical: bool = False
    superseded_by: str | None = None


@dataclass(slots=True)
class TaskSummary:
    id: str
    title: str
    status: str
    priority: str | None = None
    next_action: str | None = None
    artifact_refs: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TraceSummary:
    status: str
    modules_used: list[str]
    tool_calls: int
    policy_events: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    protected_case_tags: list[str] = field(default_factory=list)


def to_dict(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "__dataclass_fields__"):
        return {key: getattr(obj, key) for key in obj.__dataclass_fields__}
    raise TypeError(f"Unsupported object type: {type(obj)!r}")
