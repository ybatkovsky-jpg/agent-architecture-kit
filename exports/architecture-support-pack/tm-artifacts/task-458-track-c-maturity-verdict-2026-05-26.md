# Task 458 — Track B maturity verdict and Track C direction

**Date:** 2026-05-26
**Status:** decision artifact / bounded recommendation

## Executive verdict

`Track A + Track B` now provide a **bounded operational contour** for delegated Hermes execution on the OpenClaw/Kinetic side.

That contour is now strong enough to support:
- a transport seam with clearer failure classification,
- persisted async run-state,
- bounded handle recovery,
- degraded reload/operator policy,
- durable lifecycle reload provenance in run-state.

However, this should **not** be overclaimed as a fully mature async transport architecture.

### Honest conclusion
- **Track B is sufficient as a bounded operational contour.**
- **Track B is not sufficient as the final maximum-maturity async architecture.**
- Therefore the next maturity step should be a distinct:
  - **Track C — mature async transport design**

## What Track B now means operationally

Track B should be understood as:
- the system can persist delegated Hermes async state,
- reload it later,
- recover boundedly when direct handle refs are missing,
- reject unsafe reloads with structured operator-readable outcomes,
- preserve reload provenance for later inspection.

This is a real improvement in operator reliability and debugging clarity.

It means the system is no longer forced into:
- opaque raw exceptions,
- silent loss of reload provenance,
- confusion between direct reload, degraded recovery, and rejected reload.

## What Track B does NOT mean

Track B should **not** be interpreted as proof that the system already has:
- a complete long-lived async execution architecture,
- an authoritative distributed lifecycle model,
- production-grade idempotent semantics across every failure mode,
- a final canonical contract for async ownership between task-manager, runtime state, and Hermes.

## Policy on task-manager notes

The correct mature policy is **not** to dump all Hermes actions into task-manager notes.

That would turn task history into noisy transport telemetry.

### Recommended note-surfacing rule
Write only **significant lifecycle outcomes** into task-manager notes, for example:
- delegated Hermes execution started,
- lifecycle reload succeeded via degraded recovery,
- lifecycle reload rejected with actionable reason,
- cancel requested,
- cancelled,
- terminal completion,
- terminal blocked/failed summary with operator action.

### Do NOT auto-note low-level noise
Do not write every:
- poll tick,
- handle read,
- transport metadata refresh,
- internal low-level artifact change.

### Why
Because:
- `run-state` and runtime artifacts are the correct place for low-level technical truth,
- `task-manager notes` should remain a human-meaningful operator history.

## Track C — mature async transport design

If the program goal is maximum maturity rather than merely bounded operational viability, the next track should be explicit and architectural.

### Proposed Track C scope
1. **Canonical run handle contract**
   - what the authoritative async handle is,
   - where it lives,
   - who owns it,
   - how it is versioned or replaced.

2. **Authoritative async state model**
   - which layer is source-of-truth,
   - how task-manager, runtime state, and Hermes transport relate,
   - how state transitions are reconciled after restart.

3. **Idempotent lifecycle semantics**
   - repeated poll,
   - repeated cancel,
   - poll-after-cancel,
   - poll-after-completion,
   - safe no-op vs hard error behavior.

4. **Crash/restart recovery model**
   - stale run detection,
   - orphaned handle policy,
   - missing artifact policy,
   - forced restart vs safe resume criteria.

5. **Operator surfacing contract**
   - what lives only in run-state,
   - what gets summarized into notes,
   - what should trigger alerts or intervention.

6. **Timeout / lease / heartbeat policy**
   - when a run is considered stuck,
   - when intervention is required,
   - whether heartbeat or lease semantics are needed.

## Recommendation

The most honest and mature path from here is:
1. accept current Track B as a bounded operational success,
2. keep task-manager notes limited to significant lifecycle outcomes,
3. open/continue Track C as the explicit maturity lane for a real async transport design.

## Suggested concise verdict

> Track B is accepted as a bounded operational contour for Hermes async lifecycle handling on the OpenClaw/Kinetic side, but maximum maturity still requires a separate Track C for mature async transport design. Task-manager notes should surface only significant lifecycle outcomes, while low-level transport and reload details remain in persisted run-state and runtime artifacts.
