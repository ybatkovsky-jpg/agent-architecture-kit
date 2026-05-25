# OpenClaw runtime continuity design note

**Date:** 2026-04-28  
**Status:** Draft / implementation-facing  
**Scope:** OpenClaw-like runtime with isolated runs, file-first artifacts, bounded delegation, and Telegram/topic-aware operator surfaces.

---

## 1. Problem

An OpenClaw-like system cannot rely on one long-lived chat/session buffer as its continuity mechanism.

In practice, work spans:
- multiple model turns,
- compression events,
- child-task delegation,
- waiting periods for users or external systems,
- soft backgrounding and later resumption,
- operator handoff across sessions or surfaces.

Without an explicit runtime continuity model, the system drifts into the usual failure modes:
- the current session transcript becomes the accidental source of truth,
- resumption depends on prompt luck rather than written state,
- compression discards action-critical context,
- active tasks are forgotten when a run pauses,
- waiting vs blocked vs done are conflated,
- child work returns without durable lineage,
- resources stay “open” because the runtime has no soft-close discipline,
- handoff becomes narrative rather than executable.

This note defines the continuity model that should govern runtime state, transitions, compression, and resume discipline.

---

## 2. Design goals

1. **Make run continuity explicit and durable.**
   A run must remain resumable even if the live session context is compressed, swapped, or lost.

2. **Separate session continuity from run continuity.**
   Session history is useful but must not be the primary execution substrate.

3. **Preserve active work through pauses and compression.**
   Pending tasks, waiting reasons, and next-resume conditions must survive every boundary.

4. **Keep lineage inspectable.**
   Parent/child runs, resumed runs, and handoffs must be reconstructable from file-first state.

5. **Support bounded delegation and bounded resumption.**
   A resumed run must know what it inherited, what remains open, and what contract still applies.

6. **Release resources safely without destroying continuity.**
   The runtime should be able to reduce active footprint while keeping resumable state intact.

7. **Be implementation-friendly.**
   The model should map directly onto `RunState`, `TaskBrief`, `ChildTask`, `ChildResult`, `TopicContext`, and artifact files.

---

## 3. Non-goals

This note does **not** attempt to:
- define a full event-sourcing architecture,
- preserve every token of every session forever,
- make one run mutable across arbitrary time horizons,
- model every platform-specific delivery detail,
- specify storage engine internals beyond file-first runtime contracts,
- reproduce Hermes in full.

---

## 4. Core continuity principles

### P1. The run, not the chat session, is the primary unit of execution continuity
A **run** is the bounded execution envelope that owns step progression, active objective, open dependencies, and stop reason.

A session may contain multiple runs. A run may survive across multiple sessions. Therefore:
- run continuity must be durable outside session transcript,
- session continuity is supportive, not authoritative,
- resumption must target a `run_id` or explicit successor run lineage, not “whatever was being discussed.”

### P2. Every non-trivial state change must become written state before control is released
Before the runtime yields, compresses, waits, hands off, or soft-releases resources, it must persist enough state for deterministic continuation.

Minimum persisted state:
- current run status,
- current objective/phase,
- open tasks and child tasks,
- latest relevant artifacts,
- waiting reason or terminal reason,
- explicit resume trigger or next action.

### P3. Compression is a boundary, not just a summarization convenience
Compression changes what remains live in the model-visible context. Therefore it must be treated as a lifecycle boundary with preconditions and outputs.

A compression boundary is valid only if:
- active-task extraction has completed,
- next-action obligations are externalized,
- waiting/blocked/terminal semantics are preserved,
- the compressed continuation artifact is linked into run state.

### P4. Active-task preservation is mandatory
At any time, the system must be able to answer:
- what task/run is active,
- what subtasks are still open,
- what is waiting on whom,
- what evidence/artifacts matter for resume,
- what the next executable step is.

If that cannot be answered from written state, continuity is considered broken.

### P5. Waiting is not blocked; blocked is not terminal
The runtime must distinguish:
- **waiting_user** — progress can resume once a user/operator answers,
- **waiting_external** — progress can resume once an external dependency changes,
- **blocked** — no valid next step exists under current constraints,
- **terminal** — this run will not continue.

This distinction drives routing, reminders, resume eligibility, and operator expectations.

### P6. Soft resource release should preserve continuity; hard close should end it cleanly
A run may stop holding active runtime resources without becoming terminal.

Soft release means:
- in-memory context may be dropped,
- background workers may stop,
- ephemeral handles may be released,
- but the run remains resumable from durable state.

Hard close means:
- the run enters a terminal state,
- no further mutation of that run occurs,
- any future continuation must create explicit successor lineage.

### P7. Resume must be explicit, disciplined, and lineage-preserving
Resumption is not “keep talking.” It is a controlled transition from written state back into execution.

A resume operation must identify:
- source run,
- resume basis artifact(s),
- what changed since pause/stop,
- whether continuation is same-run or successor-run,
- what obligations are inherited.

---

## 5. Continuity objects and their roles

## 5.1 `TaskBrief`
`TaskBrief` is the durable execution contract for the bounded unit of work.

It should carry:
- objective,
- scope,
- constraints,
- done criteria,
- delivery target,
- allowed tools,
- topic ownership/context,
- expected output classes.

**Continuity role:** stable contract across fresh runs, resumed runs, and handoffs.  
**Rule:** a run may pause, compress, fail, or be resumed, but the `TaskBrief` remains the reference contract unless explicitly superseded.

## 5.2 `RunState`
`RunState` is the authoritative live continuity object for one run.

It should carry at minimum:
- `run_id`, `task_id`, `parent_run_id`, optional `resume_from_run_id`,
- status,
- step count / max steps,
- current phase,
- current goal,
- stop reason,
- waiting reason,
- linked typed artifacts,
- child run refs,
- verification state,
- timestamps.

**Continuity role:** single canonical resumable state for the bounded execution envelope.

## 5.3 `ChildTask`
`ChildTask` is the delegation contract from a parent run to a child run.

It should define:
- delegated objective,
- scope bounds,
- inputs,
- allowed tools,
- output contract,
- done criteria,
- timeout / step bounds,
- return target.

**Continuity role:** preserves why the child exists and what parent obligation it satisfies.

## 5.4 `ChildResult`
`ChildResult` is the structured return from child execution.

It should capture:
- child status,
- output artifact refs,
- evidence refs,
- unresolved issues,
- verification notes,
- recommended parent next step.

**Continuity role:** allows parent resumption without replaying child transcript.

## 5.5 `TopicContext`
`TopicContext` binds work to its operational surface.

It should capture:
- execution-group/topic identity,
- delivery target,
- ownership conventions,
- local routing constraints,
- surface-specific expectations for updates/handoffs.

**Continuity role:** preserves where results, clarifications, and resumptions belong without leaking surface transcript into core run state.

---

## 6. Run lineage model

## 6.1 Lineage entities
We need explicit lineage across three relationships:

1. **Spawn lineage**
   - parent run creates child run to execute a bounded subtask.
   - represented by `parent_run_id` on child and `child_run_ids` on parent.

2. **Resume lineage**
   - a new run continues work from a terminal or non-mutable prior run.
   - represented by `resume_from_run_id` on successor run.

3. **Handoff lineage**
   - another operator/agent/session takes responsibility for continuation using a handoff artifact.
   - represented by handoff artifact refs plus new run linkage to source run.

## 6.2 Same-run resume vs successor-run resume
### Same-run resume
Allowed when the source run is non-terminal and was only soft-released.

Examples:
- `waiting_user -> running`
- `waiting_external -> running`
- `blocked -> running` after new input/constraint change

In same-run resume:
- `run_id` stays the same,
- `RunState` remains canonical,
- resume event appends state and artifacts but does not create a new run.

### Successor-run resume
Required when the prior run is terminal or intentionally immutable after closure/compression policy.

Examples:
- `failed` run is repaired by a new recovery run,
- `cancelled` run is re-opened as a new attempt,
- `completed` run produces a follow-up implementation run,
- old run was hard-closed and only a handoff remains.

In successor-run resume:
- new `run_id`,
- `resume_from_run_id` points backward,
- new run inherits `TaskBrief` or explicit revised brief,
- source run remains immutable.

## 6.3 Lineage rules
1. A terminal run is never mutated back into `running`.
2. Any post-terminal continuation creates a successor run.
3. Child runs never silently become parent continuation; they must return via `ChildResult`.
4. Handoff without lineage metadata is invalid for implementation-facing continuity.

---

## 7. Session continuity vs run continuity

## 7.1 Session continuity
Session continuity is the conversational and local-interaction thread across user-visible exchanges.

It may include:
- recent messages,
- local clarifications,
- transient discussion context,
- ephemeral prompt history.

Session continuity is useful for user experience and short-horizon coherence, but it is **not sufficient** for reliable execution continuity.

## 7.2 Run continuity
Run continuity is the durable ability to continue execution correctly.

It depends on:
- `TaskBrief`,
- `RunState`,
- typed artifact refs,
- child contracts/results,
- waiting/blocked semantics,
- explicit resume or handoff data.

## 7.3 Design rule
If a run can only be resumed by replaying chat/session history, the design has failed.

## 7.4 Practical implication
Prompt assembly may use session context opportunistically, but the runtime must always be able to rebuild a resumable execution context from:
- `TaskBrief`,
- canonical `RunState`,
- linked artifacts,
- relevant `TopicContext`,
- optional concise continuation summary.

---

## 8. Compression boundaries

## 8.1 What compression is for
Compression exists to reduce live context footprint while preserving enough continuity for safe continuation.

It is not a substitute for state persistence.

## 8.2 Valid compression boundaries
Compression may occur at:
- step-count threshold,
- token/context budget threshold,
- planned pause/wait transition,
- parent-child return boundary,
- operator handoff boundary,
- soft resource release boundary.

## 8.3 Invalid compression timing
Compression is invalid if any of the following are still only implicit in the live context:
- active task list,
- unresolved child dependencies,
- waiting reasons,
- required next action,
- delivery target,
- key evidence refs,
- acceptance/verification obligations.

## 8.4 Compression outputs
A compression boundary should produce or refresh a continuity artifact containing:
- run identity,
- current objective and phase,
- active/open tasks,
- latest material decisions,
- outstanding dependencies,
- next resume condition,
- artifact refs to evidence/work products,
- recommended next action on resume.

This artifact may be a handoff note, continuation brief, or structured state snapshot depending on runtime layer.

---

## 9. Pre-compression extraction hooks

Before any compression event, the runtime should run extraction hooks that externalize the state most likely to be lost.

## 9.1 Required extraction hooks

### Hook A — active-task extraction
Produce/update a compact structured view of:
- primary task,
- active subtasks,
- child runs in flight,
- unresolved issues,
- next actionable step.

### Hook B — dependency extraction
Produce/update:
- waiting target,
- dependency kind (`user`, `external`, `internal decision`, `child result`),
- unblock condition,
- timeout/escalation hint if applicable.

### Hook C — artifact capture
Ensure new working/final/evidence/handoff refs are attached to `RunState` before context is reduced.

### Hook D — decision capture
Persist short-form decisions that would otherwise remain only in transcript.

### Hook E — resume contract extraction
Persist the minimal resume contract:
- what to load,
- what changed since last active step,
- what the first next step should be.

## 9.2 Design rule
Compression must call extraction hooks **before** summarization and **before** any in-memory context is released.

## 9.3 Failure policy
If required extraction fails, the runtime should:
- defer compression if possible, or
- mark continuity risk explicitly in `RunState`, and
- create a high-priority handoff artifact rather than silently compress.

---

## 10. Active-task preservation model

## 10.1 Active-task set
Each run should maintain an explicit active-task set, even if v1 stores it as lightweight structured fields/artifacts rather than a full task graph.

Minimum preserved elements:
- current primary objective,
- current phase,
- open checklist/subtasks,
- child runs still pending,
- blocked/waiting reason per open item,
- next step owner.

## 10.2 Preservation points
Active-task preservation is required at:
- every wait transition,
- every delegation boundary,
- every compression boundary,
- every handoff,
- every terminalization.

## 10.3 Preservation rule
Do not rely on a free-text “summary” alone when open work still exists. At least a minimal structured active-task representation must survive.

---

## 11. Waiting, blocked, and terminal semantics

## 11.1 Waiting states
### `waiting_user`
Use when the next valid step depends on user/operator input that has been requested or is expected.

Required fields/artifacts:
- `waiting_reason`,
- outstanding question/request,
- delivery target,
- resume condition.

### `waiting_external`
Use when the next valid step depends on an external event, system result, or scheduled availability.

Required fields/artifacts:
- `waiting_reason`,
- dependency reference,
- expected signal/event,
- optional retry/check policy.

## 11.2 `blocked`
Use when the system currently has no valid next step under constraints, and progress will not resume merely by waiting passively.

Examples:
- missing permissions,
- contradictory task constraints,
- insufficient required inputs with no authorized path to obtain them,
- child result invalid and no auto-repair path allowed.

Required fields/artifacts:
- `waiting_reason` or explicit block reason,
- what constraint prevents progress,
- what change would re-enable execution.

## 11.3 Terminal states
### `completed`
Execution contract finished. May still await verification/acceptance.

### `failed`
Run ended due to unrecoverable execution failure under current contract.

### `cancelled`
Run intentionally stopped by operator/system.

## 11.4 Semantic rules
1. Waiting states are resumable without lineage fork.
2. Blocked is non-terminal but requires a recorded change before re-entering `running`.
3. Terminal states never transition directly back to `running`.
4. Acceptance/verification is orthogonal to terminality; a run may be `completed` but not yet `accepted`.

---

## 12. Soft resource release vs hard close

## 12.1 Soft resource release
Soft release is for preserving continuity while reducing active runtime cost.

Typical cases:
- long `waiting_external`,
- user has been asked a question and no immediate follow-up is possible,
- background monitoring is not justified,
- child run has returned and parent is waiting for review.

Soft release actions may include:
- drop expanded prompt context,
- persist refreshed `RunState`,
- persist continuation/handoff artifact,
- release ephemeral tool handles,
- stop active loop/timer,
- keep run status non-terminal.

**Rule:** soft release must not discard the minimum resume contract.

## 12.2 Hard close
Hard close is the explicit end of a run.

Typical cases:
- contract completed,
- irrecoverable failure recorded,
- run cancelled,
- parent decides to supersede with a fresh run.

Hard close actions should include:
- move run to terminal state,
- set stop reason,
- finalize artifact refs,
- write terminal handoff/result if needed,
- guarantee immutability except metadata-safe append or lineage links.

## 12.3 Design rule
Use soft release by default for pauses; use hard close only when the run’s execution contract is truly over or intentionally terminated.

---

## 13. Resume and handoff discipline

## 13.1 Resume prerequisites
Before a run can be resumed, the runtime should be able to load:
- `TaskBrief`,
- canonical `RunState`,
- required input/working/evidence/handoff artifacts,
- `TopicContext`,
- any child results relevant to the next step.

## 13.2 Resume procedure
Recommended resume sequence:
1. identify target run or successor lineage source,
2. load `TaskBrief` and latest `RunState`,
3. load active-task preservation artifact if separate,
4. apply post-pause delta: what new input/event changed,
5. validate status transition legality,
6. re-enter `running` with explicit first next step.

## 13.3 Handoff artifact minimum contract
A handoff artifact should minimally state:
- source run and task identifiers,
- current status,
- what is done,
- what remains open,
- what is being waited on or blocked by,
- what artifacts matter,
- exact recommended next step,
- whether continuation should be same-run or successor-run.

## 13.4 Handoff discipline rules
1. Handoff must never require transcript archaeology as the primary recovery path.
2. Handoff must identify ownership and delivery target.
3. Handoff after terminal close should point to successor-run expectations, not imply re-opening the closed run.
4. Parent/child handoff must preserve the parent’s outstanding obligation, not just the child’s local output.

---

## 14. Recommended lifecycle model

## 14.1 States
Recommended v1 run lifecycle states:
- `pending`
- `running`
- `waiting_user`
- `waiting_external`
- `blocked`
- `completed`
- `failed`
- `cancelled`

## 14.2 Main transitions
- `pending -> running`
- `running -> waiting_user`
- `running -> waiting_external`
- `running -> blocked`
- `running -> completed`
- `running -> failed`
- `running -> cancelled`
- `waiting_user -> running`
- `waiting_external -> running`
- `waiting_external -> blocked`
- `blocked -> running` only after recorded change in inputs/constraints/authority
- `waiting_* -> cancelled`
- `blocked -> cancelled`

## 14.3 Boundary actions per transition
### `running -> waiting_user`
Must persist:
- question/request,
- waiting reason,
- active tasks,
- next resume condition,
- delivery target.

### `running -> waiting_external`
Must persist:
- dependency reference,
- expected event,
- active tasks,
- optional recheck policy,
- soft-release eligibility.

### `running -> blocked`
Must persist:
- blocking constraint,
- why waiting alone is insufficient,
- what change would unblock,
- escalation/handoff suggestion if applicable.

### `running -> completed|failed|cancelled`
Must persist:
- stop reason,
- final/working/evidence refs,
- verification status,
- handoff/result note if any external consumer remains.

### `waiting|blocked -> running`
Must persist:
- trigger that changed state,
- updated active-task set,
- first next step after resume.

---

## 15. Mapping to file-first artifacts

A file-first implementation should treat artifact files as first-class continuity carriers rather than side effects.

## 15.1 Recommended artifact roles
- `TaskBrief` file — stable bounded task contract
- `RunState` file — canonical mutable state snapshot for one run
- continuation/handoff note — compact resume-facing summary
- child task file — parent-to-child contract
- child result file — child-to-parent structured return
- evidence artifacts — proof for decisions/results
- final artifacts — delivery outputs

## 15.2 Practical storage guidance
- keep one canonical current `RunState` per run,
- allow append-only history/events as optional secondary trace,
- store large payloads outside `RunState` and reference them,
- refresh handoff/continuation artifacts at major boundaries,
- use typed artifact references (`input`, `working`, `final`, `evidence`, `handoff`, `verification`).

## 15.3 Continuity invariant
At any pause or resume boundary, the combination of:
- `TaskBrief`,
- current `RunState`,
- relevant typed artifact refs,
- `TopicContext`,
- latest handoff/continuation artifact

must be sufficient to reconstruct safe next-step execution.

---

## 16. Hermes patterns that inspired this note

This design intentionally borrows only a narrow set of Hermes-derived control patterns:
- **bounded run loop** rather than free-form long-context drift,
- **layered context assembly** with written state outside the transcript,
- **strict memory boundary separation** so transcript, procedural guidance, and durable state are not conflated,
- **file-first artifacts** as continuity substrate,
- **bounded child delegation** with explicit return contracts,
- **platform/runtime separation** so operator surfaces do not define core continuity semantics.

What is transferred here is the discipline of explicit continuity control, not Hermes feature breadth.

---

## 17. Implementation guidance summary

1. Make `RunState` the canonical continuity record for each run.
2. Never rely on session transcript as the only source for resume.
3. Treat compression as a guarded boundary with mandatory extraction hooks.
4. Preserve active tasks and waiting semantics in structured form.
5. Distinguish soft release from hard close in runtime logic.
6. Enforce explicit lineage for child runs, resumed runs, and handoffs.
7. Use successor runs for any continuation after terminal closure.

---

## 18. Open questions for follow-on implementation work

1. Should active-task preservation live entirely inside `RunState` in v1, or as a companion artifact for larger runs?
2. What minimal event/history log is worth keeping alongside canonical state snapshots?
3. Which transitions should auto-generate handoff artifacts versus only updating `RunState`?
4. How should reminder/recheck policies attach to `waiting_user` and `waiting_external` without overcomplicating v1?
5. What exact file naming and directory conventions should be used for run-state and handoff artifacts?

---

## 19. Proposed adoption stance

Adopt this continuity model as the implementation baseline for OpenClaw-like bounded runtime orchestration.

If implementation must simplify, simplify storage mechanics first — **not** the semantic distinctions between:
- run vs session,
- waiting vs blocked vs terminal,
- soft release vs hard close,
- same-run resume vs successor-run lineage.
