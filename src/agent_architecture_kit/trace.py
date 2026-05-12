from __future__ import annotations

from .models import TraceSummary


def make_trace_summary(status: str, modules_used: list[str], tool_calls: int) -> TraceSummary:
    return TraceSummary(status=status, modules_used=modules_used, tool_calls=tool_calls)


def is_regression_sensitive(trace: TraceSummary) -> bool:
    return bool(trace.protected_case_tags) or "regression" in trace.policy_events
