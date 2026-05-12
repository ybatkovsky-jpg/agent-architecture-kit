from __future__ import annotations

from .models import MemoryItem

DISTILL_WORTHY_KINDS = {
    "decision",
    "pattern",
    "anti_pattern",
    "blocker",
    "reference",
    "mapping",
    "invariant",
    "lesson",
}


def is_distill_worthy(item: MemoryItem) -> bool:
    if item.protected:
        return True
    return item.kind in DISTILL_WORTHY_KINDS


def filter_distill_worthy_items(items: list[MemoryItem]) -> list[MemoryItem]:
    return [item for item in items if is_distill_worthy(item)]


def choose_canonical_memory(items: list[MemoryItem]) -> MemoryItem | None:
    if not items:
        return None
    canonical_items = [item for item in items if item.canonical and not item.superseded_by]
    if canonical_items:
        return sorted(canonical_items, key=lambda item: item.updated_at, reverse=True)[0]
    active_items = [item for item in items if not item.superseded_by]
    if active_items:
        return sorted(active_items, key=lambda item: item.updated_at, reverse=True)[0]
    return sorted(items, key=lambda item: item.updated_at, reverse=True)[0]
