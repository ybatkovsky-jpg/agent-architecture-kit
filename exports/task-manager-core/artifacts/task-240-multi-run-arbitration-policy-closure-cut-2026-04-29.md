# Task #240 — multi-run arbitration policy for resumable runs under one task

**Date:** 2026-04-29  
**Owner-task linkage:** #240

## Purpose

This slice answers the next closure question after resume-admission hardening:

> When multiple persisted runs exist under a single task, what is the smallest honest arbitration policy for task-scoped automatic resume, and is any additional patch required right now?

Scope is intentionally narrow:
- read the latest continuity/admission artifacts;
- inspect the current selector in `kinetic/runner.py` plus the durable gate semantics in `kinetic/runtime_bridge.py` and `kinetic/resume_semantics.py`;
- decide whether the current multi-run behavior is already honest enough for pilot closure trajectory, or whether one more tiny hardening patch is needed.

No scheduler redesign, no explicit manual reopen UX, and no generalized run-merging semantics.

## Current landed behavior

The current selector is `kinetic/runner.py:discover_resumable_run_for_task(...)`.

As of the already-landed admission hardening, task-scoped auto-resume now does this:

1. scan `runtime/tasks/<task_id>/runs/*/run-state-lite.json`;
2. ignore missing/unreadable/nonexistent run-state payloads;
3. require `resume_basis.resume_gate.resume_allowed == true`;
4. require a present `resume_basis.ref` whose target file exists on disk;
5. sort remaining candidates by `(updated_at-ish timestamp, run_id)` descending;
6. auto-select exactly one winner;
7. pass that run into the existing resume helper.

So the current arbitration rule is not status-based anymore. It is effectively:

> **Among auto-resumable candidates for a task, choose the most recently updated candidate with an existing durable resume basis file.**

This is consistent with the current code:
- `kinetic/runner.py:287-317`
- `kinetic/resume_semantics.py:14-54`
- `kinetic/runtime_bridge.py:206-241`

## What this means in practice

The selector now already distinguishes between two different questions:

### A. Admission
Is this run eligible for task-scoped automatic resume at all?

Current answer:
- only if `resume_gate.resume_allowed == true`.

### B. Arbitration
If multiple eligible runs exist for the same task, which one wins?

Current answer:
- newest eligible run by persisted update timestamp wins.

That separation is important because the prior policy bug was mostly about **admission truthfulness**, not about tie-breaking among multiple eligible runs.

## Failure/risk cases that still exist

The remaining risks are now narrower and more honest.

### 1. Two or more `resume_allowed=true` runs can coexist under one task

This is not forbidden by current storage or finalize logic.

If it happens, the selector will silently pick the newest one. That is deterministic enough for the pilot, but it does not prove the newer run is semantically the "correct" continuation lineage.

### 2. `updated_at` is only a recency heuristic, not lineage proof

The winner is based on timestamp ordering, not on:
- an explicit `supersedes_run_id` chain,
- a single-active-run invariant per task,
- executor ownership semantics,
- or a human-approved branch decision.

So if two autonomous runs diverge under the same task, recency may select the latest writer rather than the intended canonical branch.

### 3. Manual explicit resume can still bypass task-scoped arbitration

`kinetic/runner.py --resume-task-id <task> --resume-run-id <run>` remains an explicit direct-target path.

That is acceptable for now, but it means the honesty claim in this slice must stay narrow:
- **task-scoped auto-resume arbitration** is governed by `resume_allowed` + newest eligible candidate;
- **explicit operator-targeted resume** is still a separate path and should not be described as using the same arbitration policy.

### 4. Older proof artifacts still describe pre-hardening selector semantics

Some older #240 proof artifacts still say the selector keeps `status == handoff_ready` runs or auto-resumes review-gated runs.

Those artifacts remain useful as historical continuity proof, but they are no longer the current policy contract.

## Smallest honest arbitration policy

For the current pilot, the smallest honest policy is:

> **Task-scoped automatic resume may only select runs whose durable `resume_gate.resume_allowed` is true. If more than one such run exists for the same task, select the most recently updated eligible run whose `resume_basis.ref` exists.**

Corollaries:
- review/handoff runs with `resume_mode=await_review_decision` are excluded from task-scoped auto-resume;
- waiting runs with `resume_mode=await_unblock` are excluded from task-scoped auto-resume;
- a task may have historical persisted runs, but only the eligible subset participates in arbitration;
- among that eligible subset, recency is the current canonical tiebreaker;
- this is a **pilot heuristic**, not yet a fully modeled lineage contract.

## Why this policy is enough right now

Because #240's remaining risk was that the system previously *said* a run was not resumable while still auto-selecting it.
That mismatch is already fixed.

What remains is a narrower product question:
- should the platform eventually enforce one active resumable branch per task,
- or represent branch lineage explicitly,
- or force human arbitration when more than one eligible run exists?

Those are real future questions, but they are not required to make the current pilot claim honest.

The current code already has a coherent, implementable, and inspectable answer for multi-run auto-selection. It is heuristic, but not hidden.

## Is a tiny safe patch needed?

**Recommendation: no additional code patch is warranted in this slice.**

Reason:
- the selector already implements a deterministic arbitration rule;
- the admission rule is already hardened to the durable gate bit;
- no concrete bug was found where current code contradicts its own intended task-scoped auto-resume semantics;
- adding stronger arbitration now would cross into broader product/state-model decisions rather than a tiny local hardening.

A patch here would likely be premature unless the goal changed to one of these stronger contracts:
- fail closed when more than one eligible candidate exists;
- require explicit lineage metadata to break ties;
- or encode single-autonomous-run-per-task invariants at write time.

Those are not "tiny safe" changes for this closure cut.

## Validation performed

I re-read the latest #240 artifacts and inspected the live code that now governs the decision:
- `task-manager/artifacts/task-240-resume-admission-policy-hardening-2026-04-29.md`
- `task-manager/artifacts/task-240-watchdog-to-runner-wiring-proof-2026-04-29.md`
- `task-manager/artifacts/task-240-selector-resume-path-proof-2026-04-29.md`
- `kinetic/runner.py`
- `kinetic/runtime_bridge.py`
- `kinetic/resume_semantics.py`
- `kinetic/test_runner_resume_admission_policy.py`
- `kinetic/test_runner_resume_gate_consumption.py`

Key observed live selector facts:
- `discover_resumable_run_for_task(...)` now filters on `resume_gate.resume_allowed`;
- it requires a durable existing `resume_basis.ref`;
- it sorts candidates by recency and chooses one winner;
- the existing admission-policy test already covers one important multi-run case:
  - newer disallowed review run + older allowed running run -> allowed run wins.

That is enough to state the current arbitration policy honestly.

## Closure assessment for #240 trajectory

**Yes: this is enough for #240 to move toward closure trajectory.**

Why:
- continuity is already proved;
- task-id-based selection is already proved;
- auto-resume admission is already hardened to the durable gate contract;
- the remaining multi-run arbitration rule is now simple enough to describe honestly: newest eligible candidate wins.

What would keep #240 open indefinitely is demanding a full branch-lineage model before acknowledging that the pilot already has an honest automatic-path contract. That would be over-scoping this owner task.

## Strong recommendation for the immediate next closure step

The next closure step should **not** be another proof tail on selector behavior.

It should be a short final closure artifact that consolidates the current honest pilot claim for #240 into one owner-facing summary:
- what continuity is now landed;
- what task-scoped auto-resume can truthfully claim;
- what watchdog wiring is and is not landed;
- what remains explicitly out of scope (`await_review_decision` manual reopen / richer branch-lineage policy).

If one more implementation task is opened after that, it should be a **separate bounded follow-up** for explicit manual reopen policy of review-gated runs, not more #240 continuity proofing.

## Bottom line

The smallest honest multi-run arbitration policy is already present in the landed code:

> admit only `resume_allowed=true` runs, then pick the most recently updated eligible candidate.

That policy is heuristic but truthful, deterministic enough for the pilot, and does not justify another patch in this slice.
