# OpenClaw-like architecture implementation plan for our contour

**Date:** 2026-04-28  
**Type:** practical step-by-step implementation plan  
**Scope:** implementation sequence for our current OpenClaw-like architecture, using the already-produced schema / continuity / storage-layout / module-boundary artifacts as the primary design base.

## 1. Intent

This plan is for implementing the architecture we have already framed, not for inventing a new roadmap.

It assumes these stabilized inputs are the main contract base:
- `task-manager/artifacts/openclaw-execution-context-schema-implementation-facing-v1-2026-04-28.md`
- `task-manager/artifacts/openclaw-runtime-continuity-design-note-2026-04-28.md`
- `task-manager/artifacts/openclaw-file-first-storage-layout-lifecycle-note-2026-04-28.md`
- `task-manager/artifacts/openclaw-module-interface-blueprint-2026-04-28.md`
- `task-manager/artifacts/openclaw-hermes-pattern-adoption-implementation-backlog-2026-04-28.md`
- `task-manager/artifacts/task-227-openclaw-frame-current-architecture-as-is-draft-2026-04-28.md`
- `task-manager/artifacts/task-105-implementation-slice-plan-2026-04-26.md` (as sequencing/style precedent for narrow slices)

The implementation posture here is:
- keep `main` thin;
- move execution continuity into written runtime state;
- keep task/control state separate from substantive artifacts;
- introduce the runtime spine before adding delegation/scheduler complexity;
- ship a minimum safe path first, then widen.

---

## 2. What must be true before calling this rollout “working”

Minimum architecture outcomes:
1. A non-trivial task can be launched from a written `TaskBrief`.
2. A run has a canonical `RunState` persisted outside chat context.
3. A run can move through `running`, `waiting_user`, `waiting_external`, `blocked`, and terminal states without ambiguity.
4. Artifacts are written into stable file-first locations and referenced from state instead of embedded inline.
5. Context assembly becomes deterministic from runtime layers rather than ad hoc prompt accumulation.
6. Telegram/platform handling is normalized before runtime execution logic sees it.
7. Resume/handoff works from written state + artifacts, not from transcript luck.

If these are not true, we have not implemented the architecture; we have only added partial pieces.

---

## 3. Must-do first vs can-wait

## Must-do first
These are required to create the runtime spine.

1. Normalize canonical runtime objects and schemas in code
2. Create file-first runtime storage layout and atomic state persistence
3. Implement bounded run engine with explicit lifecycle semantics
4. Implement deterministic context assembly using the new runtime objects
5. Add Telegram event normalization + routing boundary
6. Prove resume/handoff on real tasks through a thin vertical slice

## Can-wait
These should not block the first implementation cycle.

1. Full child delegation runtime
2. Scheduler/background proactive execution beyond bounded manual triggers
3. Rich memory write-policy automation beyond existing baseline retrieval posture
4. DB mirrors/indexes for runtime state beyond file-first canonical storage
5. Expanded delivery surfaces beyond current Telegram contour
6. Fancy dashboards, event sourcing, or generalized orchestration framework work

---

## 4. Minimal safe path

The minimal safe path is intentionally narrower than “full architecture”.

### Safe path target
Ship one vertical slice where:
- a Telegram-triggered bounded task becomes a `TaskBrief`;
- runtime creates a canonical `RunState` under file-first storage;
- run engine executes a bounded multi-step tool loop;
- artifacts land in typed folders (`working`, `evidence`, `final`, `handoff`, `verification`);
- run can pause in `waiting_user` or `waiting_external` and later resume from file state;
- final delivery is routed back via explicit delivery target.

### Explicitly excluded from the safe path
- nested child-task orchestration at scale;
- autonomous background swarms;
- generalized cross-platform gateway;
- deep memory automation redesign;
- replacing the whole task-manager stack at once.

### Why this is the safe path
Because it validates the core architectural claim — written run continuity + file-first artifacts + deterministic context assembly — without forcing all optional modules to stabilize simultaneously.

---

## 5. Sequential implementation plan

## Step 0 — Freeze the v1 architecture contract into implementation-owned specs
**Priority:** must-do first  
**Goal:** stop architecture drift before code changes start.

**Scope**
- Convert the current schema/continuity/storage/blueprint notes into implementation-owned v1 contracts.
- Resolve terminology mismatches across docs before code exists.
- Decide canonical field names and required/optional sets for `TaskBrief`, `RunState`, `TopicContext`, `ChildTask`, `ChildResult`, `ArtifactRef`.
- Define status/transition matrix and stop-reason enum in one implementation source.

**Dependencies**
- Existing implementation-facing schema artifact
- Continuity note
- Storage-layout note
- Module/interface blueprint

**Expected artifact / code outcome**
- One architecture contract pack, e.g.:
  - `runtime-contracts/README.md`
  - `runtime-contracts/schemas/*.json|yaml|py`
  - `runtime-contracts/lifecycle.md`
- Decision note for any fields/status names changed from drafts.

**Risk**
- Coding directly from multiple drafts creates silent schema divergence.
- If naming is left fuzzy now, migrations and runtime logic will fork quickly.

**Decision gate / checkpoint**
- Proceed only when one engineer can answer: “what is the canonical shape of a run and where is it stored?” from one place, not four notes.

---

## Step 1 — Implement canonical runtime data models and validators
**Priority:** must-do first  
**Goal:** make runtime state machine-readable and reject malformed state early.

**Scope**
- Define typed code models for:
  - `TaskBrief`
  - `RunState`
  - `TopicContext`
  - `ArtifactRef`
  - optional stubs for `ChildTask` / `ChildResult`
- Add validation for:
  - required fields
  - status enum validity
  - allowed lifecycle transitions
  - artifact-ref kind validity
  - terminal-state invariants
- Add version fielding if needed for future migrations.

**Dependencies**
- Step 0 contract freeze

**Expected artifact / code outcome**
- `runtime/models/*`
- serialization/deserialization helpers
- validation tests for positive/negative fixtures
- fixture pack with sample valid `TaskBrief` and `RunState`

**Risk**
- Under-validating produces state drift.
- Over-designing for every future case delays the spine.

**Decision gate / checkpoint**
- Do not continue until sample fixtures can be loaded, validated, updated, and rewritten losslessly.

---

## Step 2 — Build file-first runtime storage layout and atomic persistence
**Priority:** must-do first  
**Goal:** make filesystem-backed runtime state real and safe to mutate.

**Scope**
- Create the canonical runtime layout described in the storage note:
  - `runtime/topics/<topic_context_id>/topic-context.json`
  - `runtime/tasks/<task_id>/task-brief.v1.json`
  - `runtime/tasks/<task_id>/runs/<run_id>/run-state.json`
  - scoped artifact folders
- Add atomic write discipline for `run-state.json`.
- Add path helpers and artifact write/read APIs.
- Keep transcripts/delivery metadata outside canonical run files.

**Dependencies**
- Step 1 models
- Storage-layout note

**Expected artifact / code outcome**
- `runtime/store/pathing.*`
- `runtime/store/file_store.*`
- atomic write helper
- sample runtime tree created from test fixtures

**Risk**
- Mixing canonical, derived, and ephemeral files will destroy inspectability.
- Non-atomic writes will create corrupt or half-written run state.

**Decision gate / checkpoint**
- Inspect an example run directory manually. If a reviewer cannot identify the current state, latest artifacts, and resume basis in under a few minutes, layout is not ready.

---

## Step 3 — Add lifecycle manager for run state transitions
**Priority:** must-do first  
**Goal:** centralize status changes so waiting/blocked/done semantics do not fragment.

**Scope**
- Implement transition APIs rather than ad hoc field mutation.
- Enforce legal transitions from schema note.
- Require `waiting_reason`, `stop_reason`, and verification metadata where applicable.
- Add update hooks to persist after every state-changing step.

**Dependencies**
- Steps 1–2
- Continuity design note

**Expected artifact / code outcome**
- `runtime/run_state_manager.*`
- transition tests
- helper functions like `mark_waiting_user`, `mark_blocked`, `complete_run`, `fail_run`

**Risk**
- If state changes remain scattered, runtime semantics will regress into today’s implicit behavior.
- `blocked` may become a junk status for all pauses.

**Decision gate / checkpoint**
- Stop and reassess if the team still cannot cleanly distinguish `waiting_external` from `blocked` in code and tests.

---

## Step 4 — Implement `TaskBrief` creation flow from current task-manager contour
**Priority:** must-do first  
**Goal:** bridge today’s operating contour into the new runtime without rewriting everything.

**Scope**
- Introduce a thin adapter that turns a bounded task request into a `TaskBrief`.
- Reuse existing task-manager/task metadata where possible.
- Keep task-manager as control-plane input, not as the new runtime store.
- Add `TopicContext` resolution so delivery target and topic ownership are explicit.

**Dependencies**
- Steps 1–3
- Current task-manager boundary from as-is architecture

**Expected artifact / code outcome**
- adapter module from current execution request/task entry to `TaskBrief`
- sample generated task briefs for real task classes
- minimal `TopicContext` materialization

**Risk**
- If the adapter becomes a second orchestration layer, it violates the thin-boundary intent.
- If we skip the adapter and do greenfield-only launch, adoption will stall.

**Decision gate / checkpoint**
- Continue only if a real bounded task can be launched from a written brief without needing the entire prior chat transcript.

---

## Step 5 — Implement bounded run engine v1
**Priority:** must-do first  
**Goal:** create the actual execution spine around the new state model.

**Scope**
- Implement the bounded loop:
  1. load `TaskBrief` + `RunState`
  2. assemble context
  3. invoke model
  4. interpret response as final output or tool action
  5. execute tool via scoped runtime
  6. record tool observation and write artifacts
  7. update `RunState`
  8. stop on terminal or waiting condition
- Add max-step bounds and explicit stop reasons.
- Keep tool reinjection structured, not raw transcript paste.

**Dependencies**
- Steps 1–4
- Module blueprint for `run_engine` and `tool_runtime`

**Expected artifact / code outcome**
- `runtime/run_engine/*`
- run loop tests with multi-step tool usage
- normalized tool observation records linked from run state

**Risk**
- Biggest architecture failure mode: shipping model calls without an explicit run loop and calling it “runtime”.
- Tool outputs may leak back as prompt noise unless normalized.

**Decision gate / checkpoint**
- Pause rollout if the run engine cannot produce the same state/result deterministically from the same brief + artifacts + tool outputs.

---

## Step 6 — Implement deterministic context assembly
**Priority:** must-do first  
**Goal:** replace prompt accumulation by ordered context layers.

**Scope**
- Implement the proposed layer order:
  1. runtime policy
  2. task brief
  3. topic context
  4. linked artifacts
  5. durable memory facts
  6. relevant skill(s)
  7. recent local interaction
  8. toolset metadata
- Add explicit inclusion policy and truncation strategy.
- Record which artifacts/facts/skills were included in a given step when practical.

**Dependencies**
- Step 5 run engine
- Existing memory/skills baseline
- Blueprint for `context_assembly`

**Expected artifact / code outcome**
- `runtime/context_assembly/*`
- context assembly tests
- debug artifact or trace showing included layers for a run step

**Risk**
- Without this step, written state exists but model behavior still depends on hidden prompt assembly drift.
- Memory/artifact boundaries may collapse again.

**Decision gate / checkpoint**
- Reassess if context assembly still has Telegram-specific or ad hoc task-manager-specific branches inside the core renderer.

---

## Step 7 — Add Telegram event normalization and routing boundary
**Priority:** must-do first  
**Goal:** stop leaking Telegram/platform logic into the execution core.

**Scope**
- Define `NormalizedEvent` and delivery target contract.
- Implement Telegram adapter for:
  - topic/thread metadata
  - reply linkage
  - sender/mention/trigger state
  - media references
- Implement routing decisions:
  - no-op
  - status-only
  - launch run
- Bind events to `TopicContext` and execution group semantics.

**Dependencies**
- Steps 4–6
- Module blueprint for `gateway.telegram`, `routing`, `delivery`

**Expected artifact / code outcome**
- `gateway/telegram/*`
- `routing/*`
- normalized event test fixtures
- topic-aware launch path into `TaskBrief` + `RunState`

**Risk**
- If runtime core still sees raw Telegram specifics, the boundary is fake.
- Routing mistakes will break operator trust faster than internal elegance can repair.

**Decision gate / checkpoint**
- Validate on a small set of real topic scenarios before widening. If topic attribution is unreliable, do not scale run launch.

---

## Step 8 — Prove pause/resume/handoff with a thin real vertical slice
**Priority:** must-do first  
**Goal:** validate the continuity model against real operating behavior.

**Scope**
- Select 2–3 bounded task types already common in this contour.
- For each, prove:
  - launch from brief
  - working/evidence/final artifact creation
  - `waiting_user` pause
  - `waiting_external` pause where applicable
  - resume from canonical file state
  - final delivery through explicit delivery target
- Write one handoff artifact format and test successor or same-run resume rules.

**Dependencies**
- Steps 1–7

**Expected artifact / code outcome**
- smoke fixtures and replayable vertical-slice tests
- handoff artifact template
- runbooks for operator/debug usage

**Risk**
- Architecture may look coherent on paper but fail at real pause/resume boundaries.
- If we postpone this proof, later modules will build on unverified continuity.

**Decision gate / checkpoint**
- This is the primary gate. If real resume requires “remembering what happened in chat”, the architecture is not yet implemented and the rollout should not expand.

---

## Step 9 — Add verification/acceptance plumbing
**Priority:** should follow immediately after safe path  
**Goal:** separate execution completion from actual acceptance.

**Scope**
- Add verification status handling from schema.
- Add acceptance/verification artifacts and hooks.
- Ensure `completed` does not imply `accepted`.

**Dependencies**
- Thin vertical slice from Step 8

**Expected artifact / code outcome**
- verification artifact conventions
- run/result acceptance handling
- tests for accepted vs rejected vs verification-failed cases

**Risk**
- Without this, the runtime will overstate success and muddy review loops.

**Decision gate / checkpoint**
- Reassess if operator workflows actually need run-level acceptance in all classes of work, or only selected ones.

---

## Step 10 — Introduce child-task delegation on the established runtime spine
**Priority:** can-wait until safe path is proven  
**Goal:** add bounded delegation without breaking continuity.

**Scope**
- Implement `ChildTask` / `ChildResult` contracts.
- Keep child work explicitly linked to parent run lineage.
- Start with one narrow delegation class only.

**Dependencies**
- Steps 1–9 stable

**Expected artifact / code outcome**
- child contract models
- child launch/return path
- parent resume on child result

**Risk**
- Delegation before core continuity works will multiply ambiguity.
- Parent/child lineage bugs will be hard to unwind later.

**Decision gate / checkpoint**
- Only proceed if parent resumption can be demonstrated from `ChildResult` alone, without replaying child transcript.

---

## Step 11 — Add scheduler/background execution carefully
**Priority:** can-wait  
**Goal:** support bounded proactive/background work without creating a second runtime.

**Scope**
- Add a scheduler that launches the same run engine with the same state contracts.
- Reuse `TaskBrief`, `RunState`, `TopicContext`, and delivery path.
- Ensure soft release vs hard close semantics remain intact.

**Dependencies**
- Steps 1–10

**Expected artifact / code outcome**
- narrow scheduler interface
- background launch policy
- watchdog/retry policy only for selected task classes

**Risk**
- Background execution often becomes a shadow architecture.
- If it bypasses canonical state updates, continuity breaks silently.

**Decision gate / checkpoint**
- Abort or narrow if scheduled runs introduce a second mutation path for run state.

---

## Step 12 — Add secondary indexes / DB mirrors / operational introspection
**Priority:** can-wait  
**Goal:** improve observability and queryability without moving canonical truth away from file-first runtime.

**Scope**
- Add derived indexes or DB mirrors for search/reporting if needed.
- Keep file-first state canonical.
- Reuse the existing “file truth + DB operational backbone” split already present elsewhere in the architecture.

**Dependencies**
- Prior steps stable

**Expected artifact / code outcome**
- derived indexer or mirror jobs
- rebuildable manifests/dashboards
- operational introspection views

**Risk**
- Premature mirroring creates source-of-truth confusion.
- Teams may begin debugging derived state instead of canonical files.

**Decision gate / checkpoint**
- Proceed only if file-first inspection has become a real bottleneck rather than a theoretical concern.

---

## 6. Recommended first implementation cycle

If we want a realistic first implementation cycle, cut it like this:

### Cycle A — Runtime spine (start here)
Ship Steps 0–5 only.

**Definition of done for Cycle A**
- schemas/models exist;
- file-first storage exists;
- lifecycle manager exists;
- task-manager-to-brief adapter exists;
- one bounded run can execute and persist state correctly.

### Cycle B — Context + routing + resume proof
Ship Steps 6–8.

**Definition of done for Cycle B**
- deterministic context assembly exists;
- Telegram normalization/routing boundary exists;
- 2–3 real task classes can pause/resume from written state.

### Cycle C — Hardening and careful widening
Ship Steps 9–12 selectively.

**Definition of done for Cycle C**
- verification semantics are real;
- one narrow delegation path works;
- any scheduler/index additions reuse the same runtime spine.

This is intentionally not a giant quarter-spanning roadmap. It is the minimum sequence that preserves architecture integrity.

---

## 7. Implementation anti-patterns to actively avoid

1. **Do not rewrite all of task-manager first.** Use a thin adapter.
2. **Do not introduce delegation before core run continuity works.**
3. **Do not let Telegram-specific logic leak into core run engine or context assembly.**
4. **Do not store substantive payloads inline inside `RunState`.** Use artifact refs.
5. **Do not treat transcript memory as resume state.**
6. **Do not add DB canonical runtime storage before file-first v1 is stable.**
7. **Do not collapse waiting, blocked, failed, and completed into one stop bucket.**

---

## 8. Key checkpoints where course correction is justified

### Gate A — after Step 2
Question: does the file layout feel inspectable and canonical in practice?  
If no: fix layout now before run-engine code deepens.

### Gate B — after Step 5
Question: do we truly have a bounded run engine, or just wrapped model calls with persistence?  
If no: pause feature work and stabilize lifecycle semantics.

### Gate C — after Step 6
Question: is context assembly deterministic and layered, or still ad hoc under the hood?  
If no: do not expand task classes yet.

### Gate D — after Step 8
Question: can a real paused run resume from written state without transcript dependence?  
If no: this is the architecture truth test; fix continuity before adding delegation/scheduler.

### Gate E — before Step 10
Question: has the safe path been proven on real tasks with acceptable operator clarity?  
If no: delegation should wait.

### Gate F — before Step 11/12
Question: are scheduler/DB/index additions solving a demonstrated bottleneck rather than adding platform surface?  
If no: defer.

---

## 9. Bottom line

The right implementation order for our contour is:

1. freeze contracts;
2. make runtime objects real;
3. make file-first continuity real;
4. build the bounded run engine;
5. assemble context deterministically;
6. normalize Telegram before execution;
7. prove pause/resume/handoff on thin real slices;
8. only then widen into verification, delegation, scheduler, and mirrors.

That sequence matches the current architecture’s actual principles:
- thin `main`;
- written resumable state;
- artifact-first proof;
- separated control/content layers;
- explicit human and routing boundaries.

Anything broader, earlier, or more “platform-like” than that is likely to create motion without implementing the core architecture correctly.
