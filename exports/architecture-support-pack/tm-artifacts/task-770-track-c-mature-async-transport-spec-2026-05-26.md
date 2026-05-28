# Task #770 — Delegated execution Track C mature async transport and lifecycle contract

Date: 2026-05-26
Task: #770
Parent: #768
Status: canonical Track C specification draft

## 1. Purpose

Track A and Track B established a bounded delegated-execution contour.
That contour is real and useful, but it is not yet the final mature async architecture.

This task defines **Track C** as the explicit maturity lane for delegated execution.
Its purpose is to turn the current bounded Hermes/OpenClaw async seam into a clearer platform contract with:
- authoritative ownership;
- explicit state transitions;
- idempotent lifecycle semantics;
- restart/crash recovery rules;
- stale/orphan handle policy;
- timeout / lease / heartbeat policy;
- operator-facing surfacing boundaries.

---

## 2. Core design rule

**task-manager remains the source of truth for task state, while delegated run-state is the source of truth for delegated runtime continuity.**

That means:
- task-manager owns task intent, progress meaning, operator history, and closure state;
- delegated run-state owns live execution continuity and transport lifecycle facts;
- transport adapters do not get to create parallel human workflow truth;
- task notes should summarize only significant lifecycle outcomes, not low-level transport chatter.

Track C is therefore not "put everything into one place".
It is an explicit contract for how task truth, runtime truth, and transport truth relate.

---

## 3. Questions Track C must answer

A mature delegated async model must answer:

1. What is the canonical async handle?
2. Which layer owns authoritative lifecycle state at each phase?
3. What transitions are legal, idempotent, or terminal?
4. How does restart/reload recover without lying about continuity?
5. What happens when handles are stale, missing, ambiguous, or orphaned?
6. When is a run merely slow vs stuck vs intervention-required?
7. What must stay in run-state, and what deserves task-manager surfacing?

---

## 4. Canonical model

## A. Objects

### Task
Human-meaningful work unit tracked by task-manager.
Owns:
- intent;
- operator-facing next action;
- status and closure state;
- significant lifecycle notes;
- proof/verification trail.

### Delegated run
A concrete delegated execution instance.
Owns:
- runtime continuity;
- transport lifecycle state;
- authoritative async handle reference;
- adapter/runtime metadata;
- recovery provenance.

### Transport handle
A stable reference used to continue lifecycle operations.
May point to:
- persisted run handle;
- transport-native reference;
- reconstructed fallback reference.

The handle is not the task, and not the operator history.
It is a runtime continuity token.

---

## 5. Canonical async handle contract

A mature Track C handle contract should require:

1. **Stable identity**
   - each delegated run has a unique run id;
   - the current active handle ref is explicit;
   - handle replacement is versioned rather than implicit.

2. **Explicit provenance**
   - direct transport-issued handle;
   - persisted local handle;
   - recovered fallback handle;
   - unrecoverable / absent handle.

3. **Reloadability semantics**
   - reload attempts must declare whether they are direct, recovered, or degraded;
   - reload success must preserve provenance;
   - reload failure must preserve actionable reason.

4. **Handle invalidation rules**
   - completion may retire a handle;
   - cancel completion must retire or mark terminally inactive;
   - replaced handles must leave an audit trail;
   - stale handles must not silently masquerade as valid continuity.

---

## 6. Authoritative ownership and source-of-truth model

## A. task-manager owns
- task status;
- next_action;
- operator-visible progress meaning;
- closure/readiness posture;
- significant note history.

## B. delegated run-state owns
- live delegated lifecycle phase;
- handle provenance;
- reload/recovery outcomes;
- timeout / heartbeat / lease facts;
- transport error classification.

## C. transport adapter owns
- raw transport invocation;
- normalization of external transport results;
- adapter-level classification into stable reason/outcome classes.

## D. Critical rule
No layer should infer stronger truth than the layer below actually proved.

Examples:
- a recovered handle means continuity is degraded-but-recovered, not fully direct;
- missing heartbeat may justify `stuck_or_ambiguous`, not silent completion;
- a task note may say "delegated run entered degraded recovery" but should not overwrite runtime facts.

---

## 7. Canonical lifecycle state-transition model

Suggested delegated run phases:
- `created`
- `submitted`
- `running`
- `completion_pending_confirmation`
- `completed_success`
- `completed_failed`
- `cancel_requested`
- `cancelled`
- `stuck_or_ambiguous`
- `unrecoverable`

### Transition rules

1. `created -> submitted -> running`
2. `running -> completion_pending_confirmation | completed_success | completed_failed | cancel_requested | stuck_or_ambiguous`
3. `cancel_requested -> cancelled | completed_success | completed_failed | stuck_or_ambiguous`
4. `stuck_or_ambiguous -> running | completed_success | completed_failed | unrecoverable`
5. terminal states:
   - `completed_success`
   - `completed_failed`
   - `cancelled`
   - `unrecoverable`

### State-transition principle
Transitions must be monotonic with respect to certainty.
Do not move from stronger terminal knowledge back to weaker active ambiguity unless a new delegated run is explicitly created.

---

## 8. Idempotent lifecycle semantics

Track C should define idempotent behavior for:

### Poll
- repeated poll on `running` => refresh state, no semantic duplication;
- poll on terminal run => safe no-op with terminal result replay;
- poll on unrecoverable handle => structured `handle_unrecoverable` outcome.

### Cancel
- repeated cancel on `cancel_requested` => safe no-op / already-requested result;
- cancel on terminal run => structured `already_terminal` outcome;
- cancel on unrecoverable handle => structured `cancel_unrecoverable` or equivalent actionable result.

### Reload
- reload via persisted handle => `reload_ok` with provenance;
- reload via degraded fallback => `reload_ok` plus degraded provenance;
- reload with no safe handle => `reload_rejected` with actionable reason.

### Completion replay
A terminal run may be surfaced multiple times, but the system must not emit duplicate human-meaningful completion notes unless the note policy explicitly deduplicates by event class/run id.

---

## 9. Crash / restart / orphan recovery model

A mature recovery model should distinguish:

## A. Safe resume
Conditions:
- run-state exists;
- handle provenance exists;
- transport reference is still reloadable;
- last known state is non-terminal.

Result:
- continue lifecycle with provenance preserved.

## B. Degraded recovery
Conditions:
- direct continuity artifact missing;
- fallback persisted handle or transport ref exists;
- continuity can be resumed but with reduced certainty.

Result:
- resume with degraded marker;
- operator surfacing allowed if significance threshold is met.

## C. Orphaned run
Conditions:
- task claims delegated work existed;
- no valid handle can be recovered;
- runtime continuity cannot be re-established.

Result:
- mark `stuck_or_ambiguous` or `unrecoverable` depending on evidence;
- emit actionable operator guidance;
- do not pretend the run is still healthy.

## D. Stale run
Conditions:
- expected heartbeat/lease window expired;
- no terminal proof;
- continuity unresolved.

Result:
- mark stale/intervention-needed in run-state;
- optionally project significant operator summary into task note.

---

## 10. Timeout / lease / heartbeat policy

Track C should make these explicit rather than heuristic-only.

### Recommended policy shape
- **timeout**: operation-level bound for a single transport call;
- **lease**: expected ownership freshness for a live delegated run;
- **heartbeat**: optional periodic proof that active work still exists.

### Policy implications
- timeout expiry alone does not prove delegated run death;
- expired lease without heartbeat should move posture toward `stuck_or_ambiguous`;
- repeated missing-heartbeat windows may require operator intervention or escalation;
- absence of heartbeat support is acceptable initially, but then lease/reload ambiguity must be surfaced honestly.

---

## 11. Operator surfacing contract

## A. Lives only in run-state
- low-level handle refs;
- every poll tick;
- every adapter metadata refresh;
- raw transport minutiae.

## B. Eligible for task-manager notes
Only significant lifecycle outcomes, such as:
- delegated execution started;
- degraded recovery succeeded;
- reload rejected with actionable reason;
- cancel requested;
- cancelled;
- terminal completion;
- terminal failure/block with operator action.

## C. Why this boundary matters
Without this boundary:
- task history becomes noisy transport telemetry;
- operator signal quality collapses;
- closure notes become harder to trust.

---

## 12. Minimum implementation-first seam

Track C should begin with the smallest seam that forces the mature contract into explicit code shape without attempting the whole transport redesign at once.

### Recommended first seam
Implement a **canonical delegated run-state machine + normalized lifecycle contract** in the OpenClaw/Kinetic layer before deeper transport expansion.

That first seam should:
1. define explicit delegated run phases;
2. normalize poll/cancel/reload outcomes into idempotent result classes;
3. persist handle provenance/version/recovery posture durably;
4. expose a small operator-facing summary projection from run-state;
5. keep Hermes transport implementation replaceable behind the contract.

### Why this first seam
Because it clarifies:
- ownership;
- legal transitions;
- recovery semantics;
- note-vs-run-state boundaries;
without forcing an immediate all-at-once transport rewrite.

---

## 13. Acceptance shape

This task should count as complete when:
- a canonical Track C spec exists;
- ownership/source-of-truth boundaries are explicit;
- lifecycle state transitions and idempotency policy are explicit;
- recovery/orphan/stale policy is explicit;
- operator surfacing boundaries are explicit;
- at least one implementation-first seam is identified.

---

## 14. Concise verdict

Track B should be accepted as a bounded operational contour.
Track C should define the mature delegated async contract by separating task truth from runtime continuity truth, making lifecycle semantics explicit, and hardening recovery/idempotency/operator surfacing rules before any broader transport evolution.
