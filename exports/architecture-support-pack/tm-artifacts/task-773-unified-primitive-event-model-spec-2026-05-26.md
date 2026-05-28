# Task #773 — Unified primitive/event model: execution, proof, incident, and significance semantics

Date: 2026-05-26
Task: #773
Parent: #768
Status: specification draft

## 1. Purpose

The system has grown real capabilities, but many contours still rely on adjacent special cases:
- task notes vs runtime state,
- proof vs progress,
- incident vs blocked vs degraded,
- resume vs recovery,
- memory significance vs user-visible importance.

This task defines a **unified primitive/event model** to reduce those special cases and give later implementation work a simpler shared vocabulary.

---

## 2. Core design rule

**Different planes may persist different views, but they should describe them using common primitives.**

The goal is shared semantics across:
- execution,
- proof,
- incident/degradation,
- recovery,
- significance,
- surfacing,
- authority.

---

## 3. Current pain points to unify

### Pain point 1 — progress vs proof split
Execution progress is not the same as closure proof, but current language often mixes them.

### Pain point 2 — runtime fact vs human-history note split
Low-level runtime truth belongs in run-state, but significant outcomes belong in notes.

### Pain point 3 — degraded/block/approval/risk overlap
Different contours describe "cannot continue normally" in partially overlapping ways.

### Pain point 4 — resume/recovery ambiguity
Resuming active work, recovering delegated continuity, and reopening stale work are related but not the same.

### Pain point 5 — significance scattered across tasking, runtime, memory, and user surfacing
The system needs one notion of significance to explain why something became a note, runtime fact, durable memory object, alert, or stayed internal.

---

## 4. Candidate common primitives

The minimum shared primitive set should be:
1. `work_event`
2. `proof_event`
3. `incident_event`
4. `recovery_event`
5. `significance_class`
6. `surface_policy`
7. `authority_scope`

---

## 5. Primitive definitions

### `work_event`
Represents something that happened in execution terms.

### `proof_event`
Represents evidence that changes what may honestly be claimed.

### `incident_event`
Represents a condition that reduces confidence or normal operability.

### `recovery_event`
Represents an attempt or outcome in restoring continuity/trust after interruption or ambiguity.

### `significance_class`
Proposed levels:
- `low_internal`
- `operator_meaningful`
- `closure_relevant`
- `memory_durable`
- `user_terminal`
- `risk_critical`

### `surface_policy`
Examples:
- `run_state_only`
- `task_note_if_significant`
- `memory_candidate`
- `operator_alert`
- `user_terminal_surface`

### `authority_scope`
Examples:
- `task_truth`
- `runtime_continuity`
- `transport_fact`
- `memory_truth`
- `verification_truth`

---

## 6. How the primitives simplify current semantics

- `work_event` becomes shared language for progress and delegated lifecycle.
- `proof_event` separates "something happened" from "something is now honestly claimable".
- `incident_event` unifies blocked, degraded, approval-needed, risk, and stale ambiguity states.
- `recovery_event` distinguishes restoring continuity from ordinary forward execution.
- `significance_class + surface_policy` explains why some things stay internal while others become notes, alerts, memory, or user-visible terminal messages.

---

## 7. Mapping current special-case seams

### Task notes
Should mostly contain events whose `surface_policy` resolves to `task_note_if_significant` or stronger.

### Autonomy state / watchdog
Many current booleans and reason classes could normalize into `work_event`, `incident_event`, and `recovery_event` projections.

### Memory promotion
`significance_class`, freshness, and proof posture can explain promotion more consistently.

### User surfacing
The existing gate remains, but can be expressed through `surface_policy=user_terminal_surface`.

---

## 8. Non-goals

This task does not require:
- immediate replacement of every existing schema;
- one mega-refactor before value is visible;
- flattening all runtime/task/memory data into one store.

---

## 9. Minimum implementation-first seam

**Introduce a normalized event-classification envelope for major task/runtime transitions, initially as projection metadata rather than a full storage rewrite.**

That seam should:
1. classify selected transitions into `work/proof/incident/recovery` families;
2. attach `significance_class`, `surface_policy`, and `authority_scope` projections;
3. use the envelope for operator/debug surfaces before replacing persistence internals;
4. identify which old booleans/reason strings can later collapse into the common model.

---

## 10. Acceptance shape

This task counts as complete when:
- a unification spec exists;
- current special-case pain points are mapped;
- candidate common primitives are defined.

---

## 11. Concise verdict

The system should converge on shared semantic primitives for work, proof, incident, recovery, significance, surfacing, and authority. The lowest-risk start is a projection-layer event envelope that classifies existing transitions before any deep persistence rewrite.
