# Task-Manager Structured Adapter Contract (Phase 1)

Date: 2026-04-26
Status: experimental

## Purpose

This document constrains the **phase-1 machine-facing contract** for the task-manager structured / MCP adapter.

It exists to keep the adapter useful **and** thin:
- useful enough to remove ad hoc shell/text parsing for the most common task operations;
- thin enough to avoid becoming a second task system, orchestration layer, or shadow state surface.

The governing boundary remains:
- `task-manager/task_manager.py` is the task behavior authority;
- `task-manager/tasks.db` remains the execution-state store;
- the adapter is only a structured delegation layer.

## Phase-1 operation set

The minimum justified phase-1 tool surface is:

1. `task_list`
   - purpose: read a bounded task list for machine callers;
   - delegates to: `task_manager.py list --format json`;
   - allowed inputs: `status`, `limit`.

2. `task_show`
   - purpose: read one task plus its event history;
   - delegates to: `task_manager.py show <task_id>`;
   - allowed inputs: `task_id`.

3. `task_add`
   - purpose: create a new task through the existing task-manager path;
   - delegates to: `task_manager.py add ...`;
   - allowed inputs: `title`, optional bounded metadata already supported by the CLI.

4. `task_start`
   - purpose: perform the narrowest useful status-change path for active execution;
   - delegates to: `task_manager.py start <task_id> ...`;
   - allowed inputs: `task_id`, optional `note`, optional `next_action`.

## Why these four only

This set is the smallest useful machine surface that proves the architecture direction without broadening the boundary too early.

It is enough to support a real caller path:
- inspect work;
- read task detail;
- create bounded work;
- begin execution.

It is intentionally **not** trying to cover the full lifecycle yet.

## Allowed adapter responsibilities

The adapter may do only the following:
- validate incoming arguments against the declared tool schema;
- translate structured inputs into existing `task_manager.py` CLI calls;
- return machine-readable JSON/text payloads;
- surface real command failures without inventing alternate state semantics.

## Explicitly out of scope in phase 1

The adapter must **not** do any of the following:
- own or mutate task state outside `task-manager/tasks.db`;
- implement business/task workflow logic separately from `task_manager.py`;
- create a second task database, cache, or writeback layer;
- add orchestration semantics such as routing, retries, planners, queues, watchdog policy, or background coordination beyond what the CLI already does;
- expose the full task lifecycle just because the CLI supports it;
- define new task states, state transitions, or event models;
- add convenience abstractions that hide which real task-manager command was called;
- become the governing documentation surface for task rules.

## Caller guidance

- **Machine callers** should prefer this phase-1 structured surface when one of the four operations is sufficient.
- **Human/admin callers** may continue using the raw CLI directly.
- If an operation is not in the phase-1 set, callers should use the existing CLI rather than expanding the adapter by default.

## Promotion criteria beyond phase 1

Do not expand the contract unless there is evidence that:
- a real caller path remains awkward with the current four-tool surface; and
- the next addition can still delegate cleanly without duplicate logic or shadow orchestration.

Any broader lifecycle coverage should be treated as a separate bounded review/decision step, not an automatic consequence of having a wrapper.
