# Session Lifecycle Prevention Spec

## 1. Problem

A gateway or runtime can look superficially healthy while the execution layer is already degrading.

A common failure contour is long-lived session-state growth:
- stale bounded runs remain open after useful completion;
- checkpoint files accumulate;
- compaction and recovery churn increase;
- websocket or execution-layer instability appears before an obvious top-level outage.

This document defines a prevention-oriented lifecycle model for bounded execution sessions.

---

## 2. Goals

This spec aims to:
- prevent disposable execution sessions from lingering after completion;
- reduce session-store and checkpoint pressure;
- separate readiness from execution-layer health;
- preserve useful artifacts and handoff anchors while aggressively minimizing hot runtime state.

---

## 3. Non-goals

This spec does not aim to:
- delete user-facing deliverables as part of routine cleanup;
- destroy intentionally persistent conversational sessions;
- treat every large session as a bug;
- replace task, artifact, or handoff truth with session residue.

---

## 4. Session classes

### 4.1 Persistent conversational sessions

Examples:
- main direct chat;
- long-lived human coordination topics;
- intentionally persistent operator threads.

Policy:
- keep alive by default;
- compact opportunistically;
- warn on abnormal growth or checkpoint fan-out.

### 4.2 Bounded isolated execution sessions

Examples:
- task-scoped isolated runs;
- one-shot subagent execution units;
- detached sessions created to return a result, patch, or artifact.

Policy:
- default expectation is closure after result delivery;
- keep only minimal resumable state when explicit review or blocking conditions justify it.

### 4.3 Review-hold sessions

Examples:
- runs finished technically, but waiting for human approval or explicit review.

Policy:
- freeze rather than remain hot;
- avoid continued checkpoint churn while waiting;
- expire to archived state after a TTL when appropriate.

---

## 5. Required terminal dispositions for bounded runs

Every bounded isolated run should end in one explicit terminal disposition:

1. `closed_delivered`
   - result delivered;
   - artifact or handoff persisted;
   - execution session may leave the active set.

2. `closed_no_artifact`
   - nothing useful produced;
   - session closed with reason.

3. `frozen_waiting_review`
   - useful result exists but awaits review;
   - retain minimal resumable state only.

4. `frozen_blocked`
   - blocked on dependency, input, or decision;
   - preserve a minimal resume capsule rather than a fully hot session.

Anything else should be treated as lifecycle drift.

---

## 6. Prevention rules

### Rule A — Default auto-close after artifact handoff

If a bounded run has:
- produced its artifact or handoff;
- delivered the result to the parent or current session;
- no explicit keep-alive request;

then it should transition to `closed_delivered` automatically.

### Rule B — Preserve a minimal capsule, not a full hot session

For runs that may need later audit or resume:
- keep artifact links;
- keep final status;
- keep blockers, decisions, and resume prerequisites;
- do not keep the entire execution session hot unless necessary.

### Rule C — Checkpoint budgets

Each bounded-session class should have hard budgets for:
- maximum checkpoints per session;
- maximum cumulative checkpoint bytes;
- maximum idle age after last useful output.

Budget crossings should trigger a staged response:
1. warning;
2. freeze or compact;
3. auto-close or archive.

### Rule D — Idle stale-run sweeper

A periodic sweeper should identify:
- isolated sessions with no active owner or process;
- sessions older than TTL after final delivery;
- review-hold sessions older than review TTL;
- orphaned checkpoints whose base session is already terminal.

Actions may include:
- marking the session terminal;
- compacting or archiving it;
- removing it from the active execution registry.

### Rule E — Active-set hygiene

A runtime should keep its active execution set intentionally small.
Historical session files may remain for audit, but they should not remain part of hot execution paths without cause.

---

## 7. Telemetry and guardrails

Minimum useful telemetry includes:
- total session count by class;
- total active session count;
- checkpoint count per session;
- cumulative session or checkpoint bytes by session and by topic;
- stale bounded run count;
- frozen review or blocked counts;
- session-store lock hold time or compaction duration;
- websocket handshake failures correlated with session pressure.

Suggested warning classes:
- `session_pressure_warn`
- `checkpoint_fanout_warn`
- `stale_bounded_runs_warn`
- `topic_hotspot_warn`
- `session_store_compaction_slow`

---

## 8. Cleanup policy

### Safe cleanup targets

Safe-by-default candidates include:
- completed isolated sessions with delivered artifact and no reopen signal;
- orphaned checkpoints of terminal bounded sessions;
- stale review-hold sessions past TTL when an artifact already exists;
- duplicate or superseded checkpoints beyond retention budget.

### Unsafe cleanup targets

Do not auto-delete without stronger safeguards:
- the current live main session;
- active human coordination topics;
- sessions with recent inbound activity;
- blocked sessions that still lack a proper resume or handoff capsule.

---

## 9. Acceptance criteria

A good implementation of this spec should make the following true:

- sessions can be classified into persistent, bounded, and review-hold classes using runtime metadata or deterministic heuristics;
- bounded runs receive explicit terminal dispositions instead of silently lingering;
- delivered bounded runs can be closed without losing their artifact or handoff trace;
- checkpoint and session growth have enforceable budgets and warnings;
- a sweeper can identify stale or orphaned execution state;
- the runtime exposes enough telemetry to detect session pressure before visible user-facing degradation.

---

## 10. Recommended first implementation slices

### Slice 1 — Evidence and classifier
Inventory sessions by class, age, size, last activity, and checkpoint fan-out.

### Slice 2 — Terminal disposition contract
Add explicit final state markers such as `closed_delivered` and `frozen_waiting_review`.

### Slice 3 — Stale sweeper
Add a periodic scanner that freezes or closes stale bounded runs and prunes orphaned checkpoints.

### Slice 4 — Hot-set protection
Ensure hot runtime paths load only active or minimally frozen metadata instead of every historical heavy session.

### Slice 5 — Observability
Expose status or doctor-style output for session pressure and checkpoint churn.

---

## 11. Design principle

Session state is a continuity aid, not a license to keep every execution surface alive forever.

Persistent conversations and bounded runs have different lifecycle needs. Treating them the same creates pressure, ambiguity, and avoidable runtime fragility.
