#!/usr/bin/env python3
"""Structured trace emitter scaffold for architecture formalization Stage 2."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class TraceEvent:
    step: int
    event_type: str
    module: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp_utc: str = field(default_factory=utc_now_iso)


@dataclass
class TraceRecord:
    trace_id: str
    request_id: str
    architecture_id: str
    architecture_version: str
    started_at_utc: str = field(default_factory=utc_now_iso)
    status: str = "running"
    events: list[TraceEvent] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)
    trace_summary: dict[str, Any] = field(default_factory=dict)
    evaluation_hooks: dict[str, Any] = field(default_factory=dict)

    def add_event(self, event_type: str, module: str, payload: dict[str, Any] | None = None) -> None:
        self.events.append(
            TraceEvent(
                step=len(self.events) + 1,
                event_type=event_type,
                module=module,
                payload=payload or {},
            )
        )

    def finalize(
        self,
        *,
        status: str,
        result: dict[str, Any],
        protected_case_tags: list[str] | None = None,
        score_inputs: dict[str, Any] | None = None,
    ) -> None:
        self.status = status
        self.result = result
        tool_calls = sum(1 for event in self.events if event.event_type == "tool_call")
        policy_events = [event.payload for event in self.events if event.event_type == "policy_check"]
        warnings = [event.payload for event in self.events if event.event_type == "warning"]
        self.trace_summary = {
            "modules_used": sorted({event.module for event in self.events}),
            "tool_calls": tool_calls,
            "policy_events": policy_events,
            "warnings": warnings,
            "event_count": len(self.events),
        }
        self.evaluation_hooks = {
            "trace_id": self.trace_id,
            "protected_case_tags": protected_case_tags or [],
            "score_inputs": score_inputs or {},
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "request_id": self.request_id,
            "architecture": {
                "id": self.architecture_id,
                "version": self.architecture_version,
            },
            "started_at_utc": self.started_at_utc,
            "status": self.status,
            "events": [event.__dict__ for event in self.events],
            "result": self.result,
            "trace_summary": self.trace_summary,
            "evaluation_hooks": self.evaluation_hooks,
        }


class TraceEmitter:
    def __init__(self, output_dir: str | Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def new_trace(self, *, request_id: str, architecture_id: str, architecture_version: str) -> TraceRecord:
        trace_id = f"trace-{uuid.uuid4()}"
        return TraceRecord(
            trace_id=trace_id,
            request_id=request_id,
            architecture_id=architecture_id,
            architecture_version=architecture_version,
        )

    def write_trace(self, trace: TraceRecord) -> Path:
        path = self.output_dir / f"{trace.trace_id}.json"
        path.write_text(json.dumps(trace.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path


def build_demo_trace() -> TraceRecord:
    trace = TraceRecord(
        trace_id="trace-demo-001",
        request_id="req-demo-001",
        architecture_id="openclaw-agent-arch",
        architecture_version="0.1",
    )
    trace.add_event("module_enter", "normalizer", {"request_tags": ["artifact-task"], "complexity": 2})
    trace.add_event("policy_check", "policy_gate", {"policy_id": "artifact-delivery", "result": "allow"})
    trace.add_event("module_enter", "planner", {"plan_created": True})
    trace.add_event("tool_call", "executor", {"tool": "write", "artifact_path": "docs/demo-output.txt"})
    trace.add_event("module_exit", "executor", {"artifacts": ["docs/demo-output.txt"]})
    trace.finalize(
        status="success",
        result={
            "status": "success",
            "user_visible_output": "Created requested demo artifact.",
            "artifacts": ["docs/demo-output.txt"],
            "side_effects": [],
        },
        protected_case_tags=["workflow-critical"],
        score_inputs={
            "task_success": 1.0,
            "constraint_compliance": 1.0,
            "artifact_quality": 0.9,
            "tool_efficiency": 0.9,
            "user_fit": 0.95,
            "trace_clarity": 0.95,
        },
    )
    return trace


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Emit a structured architecture trace")
    parser.add_argument("output_dir", help="Directory where trace JSON files are written")
    parser.add_argument("--demo", action="store_true", help="Write a demo trace")
    args = parser.parse_args()

    emitter = TraceEmitter(args.output_dir)
    if args.demo:
        trace = build_demo_trace()
    else:
        trace = emitter.new_trace(
            request_id="req-manual-001",
            architecture_id="openclaw-agent-arch",
            architecture_version="0.1",
        )
        trace.add_event("module_enter", "normalizer", {"note": "manual scaffold trace"})
        trace.finalize(status="partial", result={"status": "partial"})
    path = emitter.write_trace(trace)
    print(path)
