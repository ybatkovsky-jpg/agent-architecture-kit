# Fresh task-scoped bootstrap contract

Purpose: provide one reusable launch surface for fresh execution sessions and background watchdog-style runs.

## Default rule
Start new independent work from task-manager state, not from the old main-chat transcript.

## Required bootstrap payload
1. Invariants
   - operator/requester identity
   - safety and behavior constraints
   - workspace root
   - task id and title

2. Task state
   - task details
   - status and priority
   - next_action
   - blocked_reason when present
   - most recent proof-bearing notes

3. Resume aids
   - context summary
   - next-session instructions
   - linked artifacts
   - handoff path/summary when available

4. Optional extra context
   - only a narrow recent conversation excerpt
   - include it only if it contains material not yet externalized elsewhere

## Startup sequence
1. Read the task first.
2. Read only the linked artifacts needed for the next concrete step.
3. Perform one bounded, measurable step.
4. Write durable updates back to task-manager/artifacts.
5. Return only a concise summary/verdict/escalation to main.

## OpenClaw exec preflight rule
When a fresh run needs to execute a local script through the OpenClaw exec tool, prefer a direct interpreter invocation with the tool's `workdir` set instead of a shell-chained command.

Preferred pattern:
- `python3 task-manager/task_manager.py ...` with `workdir=/home/openclaw/.openclaw/workspace`

Avoid as the default bootstrap pattern:
- `cd /home/openclaw/.openclaw/workspace && python3 task-manager/task_manager.py ...`

Reason:
- in this runtime, exec preflight may reject complex interpreter invocations even when the underlying command is safe;
- direct interpreter + explicit `workdir` is the more reliable launch surface for fresh task-scoped runs.

## Stay-in-main vs spawn-fresh
Stay in main for:
- active dialogue with Yuri
- short interactive reasoning
- orchestration
- concise user-facing summaries

Spawn fresh task-scoped execution for:
- independent work
- long-running implementation/validation
- backgroundable work
- anything likely to outlive the current turn
- work where old chat tail would mostly be irrelevant baggage

## Durable-resume minimum
Before cutting context or handing off, ensure these live outside ephemeral chat:
- current goal
- current bottleneck
- proof/evidence so far
- next_action
- linked artifacts
- blocking conditions

## Expected output shape
A fresh run should leave behind one externally resumable state transition:
- progress note, or
- blocker note, or
- updated next_action/context, or
- review-ready note with claim, evidence, verification

## Why this is the next architectural step
Written task state shows the architecture question is largely settled already:
- #53 says watchdog migration and session hygiene now share one operating model
- #67/#68 show task-manager-scoped background execution is already materially more stable and cheaper
- #63/#64 define the policy and main-session playbook

So the highest-value next step is to standardize the launch package that future fresh runs actually consume.
