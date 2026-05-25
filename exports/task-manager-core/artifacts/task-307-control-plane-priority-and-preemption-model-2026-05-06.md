# Task #307 — Control-plane priority and preemption model

Date: 2026-05-06
Owner task: #307
Parent task: #304
Status: bounded implementation-facing policy artifact
Purpose: turn the `#304` baseline claim that the control-plane contour supports priority and preemption into a concrete model that later implementation tasks can apply without reopening the architecture frame.

Depends on:
- `task-manager/artifacts/task-304-agent-system-architecture-control-plane-spec-2026-05-05.md`
- `task-manager/artifacts/task-305-define-304-architecture-baseline-and-glossary-2026-05-06.md`
- `task-manager/artifacts/task-306-truth-boundary-and-implementation-contract-2026-05-06.md`

Out of scope:
- routing-class design from `#308`
- continuation/reopen state-machine design from `#309`
- observability and enforcement details from later child tasks except where minimally referenced here

---

## 1. What #307 fixes

`#304` and `#305` already establish that:
- the contour has priority bands;
- preemption exists;
- interrupted work must leave a resume basis;
- silent transcript drift is not an acceptable interruption mechanism.

`#307` makes that operationally concrete.

It defines:
- the priority classes the control plane may use;
- who may cause priority changes or preemption;
- when preemption is allowed, forbidden, or review-gated;
- what canonical writes must happen before the system may claim a preemption took place;
- how active bounded work and newly admitted work compete for attention.

In one line:

> Priority decides what should run next; preemption decides whether the currently active bounded front must yield now; both must be explicit in canonical state, never only implied by chat flow.

---

## 2. Model scope

This model applies to the `#304` control-plane contour at the level of:
- `main` as thin orchestrator;
- task control-plane sequencing;
- bounded isolated continuations (`ХеРТИК` lanes);
- operator-visible interruptions and urgent insertions.

This model does **not** require:
- a global OS-like scheduler;
- multi-tenant fairness machinery;
- speculative background parallelism policy;
- branch-lineage redesign.

It is intentionally the smallest honest model that can govern one operator-facing contour with bounded active work.

---

## 3. Core concepts

### 3.1 Priority
Priority is the declared importance and urgency class of a bounded work unit relative to other candidate work.

Priority answers:
- should this work start now or later?
- if another front is already active, does this new work outrank it?
- if the operator asks “what should the system do next?”, which front wins?

### 3.2 Preemption
Preemption is the explicit interruption of one active bounded front so that another front may take execution focus.

Preemption is not:
- mere delay before a task starts;
- concurrent fan-out within one already-authorized bounded slice;
- transcript drift that causes the system to forget the old front.

### 3.3 Active front
An active front is the current bounded work unit that owns execution focus in the contour.

For this model, the contour should behave as if there is **one primary active front per operator-facing execution path** unless later implementation deliberately proves a safe broader concurrency model.

### 3.4 Resume basis after preemption
A preempted front is valid only if its continuation can later be reconstructed from canonical state.

That means preemption must leave:
- lifecycle state,
- next action,
- blocker or yield reason,
- and where relevant a run-state / resume-basis anchor.

---

## 4. Priority bands

Use four practical bands.

### `P0 emergency`
Use for:
- production outage or availability threat;
- data-loss / destructive-risk containment;
- active safety or security issue;
- explicit operator interrupt that must override current work immediately.

Default behavior:
- may preempt any lower-priority front;
- should be admitted immediately if authority is sufficient;
- if mutation/destructive response is requested, normal rights checks still apply.

### `P1 urgent`
Use for:
- operator-declared urgent work;
- time-sensitive review/recovery actions;
- bounded incidents that materially block the operator’s current mission.

Default behavior:
- may preempt `P2` or `P3` fronts;
- normally should not preempt an active `P0` front;
- if competing with another `P1`, use the tie-break rules below rather than silent replacement.

### `P2 active-default`
Use for:
- the normal current execution focus;
- bounded implementation or analysis slices that the operator intends to move now.

Default behavior:
- does not preempt `P0` or `P1`;
- may supersede `P3` backlog work when admitted as the current focus;
- should usually remain active until done, blocked, yielded, or explicitly preempted.

### `P3 backlog`
Use for:
- queued or deferred work;
- useful but non-urgent candidate slices;
- work captured for later sequencing.

Default behavior:
- never preempts an already active higher band;
- should remain inactive until promoted or selected.

---

## 5. Priority fields and minimum representation

At minimum, a bounded work unit participating in sequencing should carry or be derivable to:
- `task_id` or bounded work unit id;
- `priority_band` = `P0 | P1 | P2 | P3`;
- `priority_reason` = short explicit rationale;
- `priority_source` = `operator | policy | inherited | escalation`;
- `preemptible` = `yes | no | review_required` for the currently active front;
- `last_priority_decision_ref` = canonical anchor for the latest promotion/preemption decision when relevant.

Implementation note:
- `priority_band` belongs to lifecycle/orchestration truth, not helper-only output.
- helper surfaces may display it, but `#306` still requires the authoritative anchor to live in canonical state.

---

## 6. Authority for priority and preemption decisions

### 6.1 Operator authority
The operator may:
- declare or change priority;
- explicitly interrupt current work;
- request that current work continue despite a candidate interruption;
- reopen or resume a front later according to continuation rules.

Operator decision becomes authoritative only once reflected into canonical state per `#306`.

### 6.2 Policy/orchestrator authority
`main` or another orchestration component may:
- assign an initial default priority;
- recommend promotion/demotion;
- auto-admit a higher-priority front when the rules clearly allow it;
- trigger preemption automatically for `P0` safety/emergency cases.

The orchestrator may **not**:
- invent human approval for authority-sensitive reprioritization;
- silently erase or orphan the interrupted front;
- widen rights because a task is urgent.

### 6.3 Worker authority
Workers may:
- report evidence that a front should be promoted, demoted, or interrupted;
- classify risk that may justify preemption;
- return `BLOCKED` when they cannot continue safely.

Workers may **not**:
- unilaterally self-promote to a stronger priority band as an authoritative state change;
- claim preemption occurred without the canonical writes required below.

---

## 7. Admission rules

### A1 — Default admission
If no front is active, the highest available priority candidate may become active.

### A2 — Lower-priority admission
If an active front exists, a lower-priority candidate is not admitted as the new active front. It stays queued/deferred unless the active front finishes, blocks, yields, or is explicitly demoted.

### A3 — Equal-priority admission
If a candidate has the same priority band as the active front, do not silently replace the active front.

Allowed outcomes:
- keep current front active;
- queue the candidate behind it;
- require operator choice;
- apply a narrow deterministic tie-break if later implementation introduces one explicitly.

### A4 — Higher-priority admission
If a candidate has a higher priority band than the active front, preemption becomes eligible but is not yet complete.

The system must then evaluate preemption rules.

---

## 8. Preemption eligibility rules

Preemption is allowed only when at least one of these conditions is true.

### E1 — Strict higher-priority arrival
A newly admitted or newly recognized front has a strictly higher priority band than the active front.

Examples:
- active `P2`, incoming `P1`;
- active `P1`, incoming `P0`.

### E2 — Active front is blocked or waiting
The current front cannot make bounded progress because it is waiting on:
- operator input;
- external dependency;
- review gate;
- missing authority;
- unavailable environment/resource.

In this case a ready lower-or-equal candidate may take focus without being considered an unsafe silent interruption, provided the blocked state is canonically recorded first.

### E3 — Safety / containment interrupt
The system detects a safety, security, destructive-risk, or availability condition that policy classifies as requiring immediate interruption.

This normally promotes the interrupting front to `P0`.

### E4 — Explicit operator interrupt
The operator explicitly says to stop current work and handle another front first.

This remains subject to truth-boundary and rights-boundary requirements, but does not require the assistant to pretend the old front finished.

---

## 9. Non-eligibility and fail-closed rules

Preemption is not allowed, or must stop for review, when any of the following holds.

### N1 — No resume basis can be written
If the system cannot leave reconstructable continuation state for the interrupted front, it must not claim a successful preemption.

Allowed fallback:
- downgrade to `BLOCKED` / review-needed recommendation;
- ask for operator decision;
- finish a small safe checkpoint first if that is already within granted scope.

### N2 — The active front is marked non-preemptible for a bounded critical section
Examples:
- a narrowly-scoped destructive or transactional mutation already in progress;
- a publish/mutate step that would leave canonical state inconsistent if interrupted mid-step.

In this case:
- do not silently interrupt;
- either finish the critical section then preempt, or escalate for review if the incoming front is `P0` and immediate interruption is still required.

### N3 — Priority claim lacks authority
If a worker or helper surface claims an item is urgent but cannot anchor the claim to operator decision or allowed policy classification, the system must treat it as a recommendation, not an authoritative preemption event.

### N4 — The incoming front would require rights that are not granted
Urgency does not widen authority.
If the urgent front needs `mutate`, `publish`, or `spend` and the lane lacks those rights, the preemption may still occur at the orchestration level, but execution must stop at the authority boundary.

### N5 — Equal-priority replacement by drift
A same-priority new request must not implicitly erase the active front just because the chat moved on.

---

## 10. Preemption decision table

| Active | Incoming | Allowed default | Notes |
|---|---|---|---|
| none | any | admit highest available | no preemption needed |
| `P3` | `P2`/`P1`/`P0` | yes | higher band outranks backlog |
| `P2` | `P3` | no | queue/defer incoming |
| `P2` | `P2` | no silent replace | keep active or require tie-break/review |
| `P2` | `P1`/`P0` | yes, if resume basis can be written | canonical preemption record required |
| `P1` | `P2`/`P3` | no | incoming waits unless active blocks/yields |
| `P1` | `P1` | no silent replace | require queue or operator choice unless deterministic tie-break is defined |
| `P1` | `P0` | yes, if safe checkpoint/preemption package can be written | safety/emergency outranks urgent |
| any | any | yes when active is canonically blocked | blocked front yields after state write |
| any | any | stop/review when no canonical anchor can be left | fail closed |

---

## 11. Canonical preemption protocol

A preemption event is complete only if these steps occur in order.

### Step 1 — Identify the active front and interrupting front
Required minimum:
- active bounded work id / task id;
- interrupting bounded work id / task id or explicit operator interrupt marker;
- priority comparison or interrupt reason.

### Step 2 — Decide the preemption basis
The basis must be one of:
- higher priority;
- active blocked/waiting;
- safety/containment;
- explicit operator interrupt.

### Step 3 — Persist interrupted-front state
Before focus moves, record in canonical state:
- current status or pause/block state;
- last safe checkpoint or summary;
- next action to resume;
- reason for yielding;
- owner/unblock condition if blocked;
- resume basis / continuation anchor where relevant.

### Step 4 — Reflect the preemption decision
Canonical state must capture:
- that front A yielded to front B;
- who/what authorized the shift;
- when relevant, the expected return condition.

This may be represented by task events, run-state update, or both, but must remain reconstructable under `#306` rules.

### Step 5 — Admit the interrupting front
Only after the interrupted front has a valid anchor may the new front claim `ACK` as the active focus.

### Step 6 — Project to helper surfaces
Operator summaries, envelopes, or chat updates may then say the preemption happened, but only as projections of the canonical record.

---

## 12. Required state after preemption

After a valid preemption, the interrupted front must be left in one of these states:
- `paused_for_preemption`
- `blocked`
- `awaiting_review`
- equivalent explicit lifecycle state with the same semantics

And it must carry enough information to answer:
- what was interrupted?
- why was it interrupted?
- what should happen to resume?
- what front replaced it?

The interrupting front must carry enough information to answer:
- why is it now active?
- what priority or safety basis caused admission?
- what canonical anchor owns this new active state?

### 12.1 Mandatory persist set before preemption

Before focus moves away from the active front, the control plane must persist at least this minimum package in canonical state:
- `task_id` or bounded front id of the interrupted front;
- resulting lifecycle state (`paused_for_preemption`, `blocked`, `awaiting_review`, or equivalent);
- `priority_band` at time of interruption;
- `yield_reason` / preemption basis (`higher_priority`, `blocked_waiting`, `safety_containment`, `operator_interrupt`);
- `next_action` for the interrupted front;
- `resume_condition` describing what must be true to resume;
- `replaced_by` / interrupting front id when one exists;
- `last_safe_checkpoint_summary` or equivalent bounded checkpoint note;
- `last_priority_decision_ref` pointing to the canonical event or decision record;
- `resume_basis_ref` / continuation anchor when runtime continuity exists outside bare task state.

If any of the above cannot be written, the system must not claim that a valid preemption completed.

### 12.2 Resume package / writeback fields

A minimal resume package for the interrupted front should be derivable or explicitly stored with these fields:

| Field | Meaning | Canonical layer |
|---|---|---|
| `front_id` | interrupted bounded work unit id | lifecycle / orchestration |
| `status` | paused/blocked/review state after yield | lifecycle truth |
| `priority_band` | band held when preempted | lifecycle / orchestration |
| `preempted_at` | timestamp of shift | lifecycle event / run state |
| `preemption_reason` | principal reason for yield | lifecycle event |
| `preempted_by` | new active front id or operator interrupt marker | lifecycle event |
| `next_action` | first concrete step on resume | task state |
| `resume_condition` | gate for resuming | task or run state |
| `checkpoint_summary` | last safe durable checkpoint | run state / artifact-linked note |
| `resume_basis_ref` | pointer to run-state / artifact / checkpoint record | continuation truth |
| `owner_or_lane` | who should resume it | lifecycle / run state |
| `rights_boundary_note` | whether resume is blocked by missing rights/review | lifecycle / decision truth |

These writeback fields are the implementation-facing bridge between `#304`'s anti-drift rule and `#306`'s truth-boundary contract:
- task state/event owns lifecycle truth;
- run-state / resume-basis owns continuation truth;
- artifacts own reusable result truth when a richer checkpoint note is needed.

---

## 13. Tie-break and anti-thrash policy

### T1 — No same-band churn by default
For equal-priority fronts, the system should prefer stability over churn.

Default behavior:
- keep current active focus;
- queue the new equal-priority front;
- or ask for operator choice if the distinction matters.

### T2 — Prefer checkpoint boundaries over arbitrary interruption
When interruption is allowed but not emergency-critical, preempt at the next safe checkpoint rather than in the middle of a critical mutation step.

### T3 — Do not oscillate between fronts without new authority
Once a front has been preempted, the system should not bounce back and forth between two fronts on every new message unless:
- priority changed again;
- the now-active front blocked/finished;
- the operator explicitly reprioritized.

### T4 — One canonical reason per shift
Each priority shift should have one principal stated reason.
Do not mix multiple vague justifications when one clear basis exists.

---

## 14. Interaction with truth-boundary contract

This artifact inherits `#306` directly.

### P1 — Priority is lifecycle/orchestration truth, not chat truth
If a summary says something is now urgent, the canonical task/orchestration state must carry that fact.

### P2 — Preemption claims require canonical anchors
A chat message saying “switching to X” is not enough.
There must be a task/run/event record that the old front yielded and the new front was admitted.

### P3 — Blocked-by-preemption must name the resume path
If a front is interrupted, helper surfaces must not be the only place where the resume condition is readable.

### P4 — Human reprioritization outranks worker suggestion
Workers may recommend urgency escalation; only allowed policy or explicit operator decision may make it authoritative.

---

## 15. Interaction with rights model

Priority changes sequencing, not authority.

Hard rules:
- a `P0` or `P1` front does not automatically gain `mutate`, `publish`, or `spend`;
- emergency handling may justify immediate focus, but still cannot bypass rights gates;
- when urgent work crosses an authority boundary, the correct state is often `ACK` or `BLOCKED`, not unauthorized execution.

Implementation-facing implication:
- later rights enforcement (`#312`) should treat priority and rights as orthogonal dimensions.

---

## 16. Minimal implementation contract for later tasks

Any implementation claiming `#307` compliance should be able to represent or derive:
- one current active front;
- one priority band per relevant front;
- whether the active front is preemptible now;
- the reason for any priority change;
- the canonical anchor of the latest preemption or yield event;
- the resume condition for interrupted work.

A minimal compliant system does **not** need:
- perfect automated scheduling;
- branch lineage across all historical runs;
- predictive priority scoring.

It does need:
- explicit priority bands;
- explicit preemption basis;
- explicit preemption writeback.

---

## 17. Review checklist for #307-compliant behavior

A priority/preemption implementation passes this artifact only if all relevant checks pass:

- [ ] Every active or queued bounded front has a visible priority band or a deterministic default.
- [ ] Higher-priority arrival does not silently erase the active front.
- [ ] Preemption writes a resume basis / next action before focus moves.
- [ ] Equal-priority work does not cause transcript-drift replacement.
- [ ] Urgency does not widen rights.
- [ ] `BLOCKED` by interruption identifies owner/unblock condition when relevant.
- [ ] Helper surfaces describe preemption only as a projection of canonical state.
- [ ] An interrupted front can be reconstructed later without relying on chat residue.

---

## 18. Definition of done for #307

Task `#307` is satisfied when:
- the priority bands are concrete enough for implementation-facing use;
- preemption eligibility and non-eligibility rules are explicit;
- the canonical preemption protocol is defined;
- truth-boundary and rights-boundary interactions are fixed;
- later child tasks can build routing, continuation, observability, and enforcement on top of one shared priority/preemption model.

---

## 19. Compact conclusion

`#307` turns the `#304` control-plane contour’s priority idea into a concrete bounded policy.

After this artifact, later work should assume:
- four practical priority bands: `P0` to `P3`;
- one primary active front per operator-facing execution path by default;
- preemption only for higher priority, blocked state, safety/containment, or explicit operator interrupt;
- no valid preemption without canonical writeback of interrupted-state and resume basis;
- no same-priority replacement by chat drift;
- no urgency-based bypass of scoped rights.
