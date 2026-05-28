# Task 458 — Track C mature async transport design

**Date:** 2026-05-26
**Status:** design direction / bounded architectural proposal

## Purpose

This document defines the next maturity lane after the verified Track A and Track B slices.

- **Track A** established the delegated execution seam and clarified transport-vs-Hermes failure classification.
- **Track B** hardened the bounded operational contour around persisted async lifecycle handling: submit/poll/cancel wiring, handle recovery, degraded reload policy, and durable lifecycle reload metadata.

The next step for maximum maturity is not more ad hoc hardening alone. It is an explicit:

## Track C — mature async transport design

The goal of Track C is to define a transport/lifecycle model that is:
- authoritative,
- restart-safe,
- idempotent,
- operator-readable,
- and explicit about ownership boundaries between task-manager, runtime state, and Hermes.

## Current contour recap

Today the bounded contour already has these verified properties:
- delegated Hermes runs can persist a run-state lite record,
- async local-file transport can persist a run handle,
- lifecycle reload can recover from `run_handle.handle_ref`, `transport.handle_ref`, or conventional run path,
- unsafe reload paths normalize into structured failures,
- reload provenance survives in `delegation.lifecycle_reload`.

This is enough for a bounded operational contour, but not yet a mature architecture because the authoritative contracts remain implicit and local-skeleton oriented.

## Track C design principles

### 1. Single authoritative async handle contract
Each delegated Hermes async run should have one canonical handle contract.

The handle contract should specify at minimum:
- `delegation_id`
- `hermes_run_id`
- `transport_id`
- `transport_mode`
- `handle_version`
- `submitted_at`
- `state_ref`
- `lease_ref` or equivalent liveliness anchor if introduced
- `integrity_ref` or checksum anchor if artifacts become separately mutable

### 2. Explicit ownership model
Track C should remove ambiguity about who owns what.

Recommended ownership split:
- **task-manager** owns task intent, operator-facing status, and high-level task history.
- **runtime state** owns delegated run lifecycle state and recovery metadata.
- **Hermes transport layer** owns transport-specific execution facts and remote-facing state transitions.

This avoids overloading task-manager as a low-level packet log while still keeping it authoritative for task progress.

### 3. Source-of-truth state model
Track C should define which state is authoritative for each question.

Suggested model:
- "What task is trying to happen?" → task-manager / task brief
- "What delegated run exists?" → runtime run-state
- "What does the transport currently know?" → transport state/handle artifacts
- "What should the operator be told?" → task-manager notes + summarized status surfaces

This should be documented as a contract rather than inferred from current codepaths.

## Proposed state machine

The mature async transport lane should standardize a small explicit state model.

### Proposed transport lifecycle states
- `submitted`
- `running`
- `polling`
- `awaiting_cancel`
- `cancelled`
- `completed`
- `failed`
- `orphaned`
- `stale`
- `recovery_blocked`

### Proposed state transition expectations
- `submitted -> running|polling|completed|failed`
- `running|polling -> completed|failed|awaiting_cancel|stale`
- `awaiting_cancel -> cancelled|failed|stale`
- `stale -> recovery_blocked|running|polling|failed`
- `orphaned -> recovery_blocked|failed`

This gives a vocabulary richer than the current bounded local skeleton without requiring immediate deep runtime changes.

## Idempotent lifecycle contract

Track C should specify idempotent semantics for repeated lifecycle calls.

### Submit
Repeated `submit` with the same delegation intent must be explicitly classified as one of:
- duplicate-safe no-op returning canonical handle,
- reject_duplicate,
- or resumed_existing.

### Poll
Repeated `poll` should:
- never invent new runs,
- return stable status semantics,
- distinguish `still_running` from `stale` and from `recovery_blocked`.

### Cancel
Repeated `cancel` should be explicitly idempotent.
Possible normalized responses:
- `cancel_requested`
- `already_cancel_requested`
- `already_cancelled`
- `cancel_not_supported`
- `cancel_rejected_invalid_state`

## Recovery contract

Track C should formalize recovery beyond today's bounded handle search.

### Recovery inputs
A recovery attempt should resolve from:
- canonical run-state,
- canonical handle artifact,
- optional transport-native state artifact,
- bounded recovery metadata.

### Recovery outcomes
Normalize into:
- `reload_ok_direct`
- `reload_ok_recovered`
- `reload_rejected_context_missing`
- `reload_rejected_handle_missing`
- `reload_rejected_integrity_mismatch`
- `reload_rejected_ownership_conflict`
- `reload_rejected_transport_ineligible`

### Integrity constraints
Track C should decide whether reload is allowed only when:
- run-state and handle version agree,
- transport id/mode agree,
- task id/run id/delegation id remain consistent,
- any remote-facing lease or freshness window remains valid.

## Staleness / lease / heartbeat policy

Maximum maturity likely requires an explicit staleness policy.

### Questions Track C must answer
- When is a delegated run considered stale?
- Is stale detection timestamp-only or transport-ack-based?
- Does cancellation require lease ownership?
- Is there a heartbeat, lease renewal, or freshness marker?
- What operator action is required when the run becomes stale?

### Minimal recommended direction
Even before full heartbeat design, Track C should at least define:
- a `last_observed_at` field,
- a bounded stale threshold policy,
- and a normalized stale operator action.

## Operator surfacing policy

Track C should preserve the distinction between low-level truth and operator history.

### Persist in runtime/run-state
Keep technical details such as:
- handle refs,
- transport refs,
- poll counts,
- lifecycle reload provenance,
- transport-native diagnostics,
- integrity/version markers.

### Surface in task-manager notes only when significant
Recommended significant note-worthy outcomes:
- delegated Hermes run started,
- degraded recovery succeeded,
- reload rejected,
- stale/orphaned state requiring intervention,
- cancel requested,
- cancelled,
- terminal completion,
- terminal blocked/failed outcome with operator action.

### Do not note low-level noise
Do not emit notes for:
- every poll,
- every artifact refresh,
- every handle read,
- purely internal transport counters.

## Compatibility with current code

The current code already suggests the seeds of Track C:
- `HermesRunHandle` in `kinetic/hermes_transport.py`
- persisted `delegation.run_handle` and `delegation.transport`
- reload provenance in `delegation.lifecycle_reload`
- structured reload rejection mapping in `runner.py`

Track C should build on these instead of replacing them blindly.

## Recommended incremental implementation order

### C1. Canonical handle schema artifact
Define/document the canonical async handle schema and version it.

### C2. State ownership contract
Document authoritative ownership across task-manager, runtime state, and transport.

### C3. Idempotent poll/cancel normalization
Extend lifecycle results to distinguish duplicate-safe / stale / already-cancelled semantics.

### C4. Significant lifecycle note surfacing
Implement bounded automatic task-manager note emission for significant lifecycle outcomes only.

### C5. Staleness policy
Add `last_observed_at`, stale threshold, and normalized stale/recovery states.

### C6. Transport maturity checkpoint
Reassess whether the existing transport skeleton can be extended safely or whether a new process-backed or remote-native async transport is warranted.

## Final recommendation

The most mature path is:
1. accept Track B as a verified bounded operational contour,
2. continue with Track C as an explicit architecture lane,
3. implement only significant lifecycle note surfacing into task-manager,
4. avoid pretending that the current bounded local skeleton is already a final async transport system.

## Suggested concise statement

> Track C should convert the current bounded Hermes async contour into an explicit mature transport contract: authoritative handle ownership, idempotent lifecycle semantics, restart-safe recovery, stale-run policy, and operator surfacing boundaries. Task-manager remains human-facing and should receive only significant lifecycle outcomes, while low-level transport truth remains in runtime state and artifacts.
