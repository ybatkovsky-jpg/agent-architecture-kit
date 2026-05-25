# OpenClaw-like runtime module/interface blueprint — implementation-facing v1

**Date:** 2026-04-28  
**Scope:** practical module/interface blueprint for an OpenClaw-like contour with isolated runs, file-first artifacts, topic-aware delivery, and bounded delegation.  
**Primary inputs:**
- `/home/openclaw/.openclaw/workspace/task-manager/artifacts/openclaw-execution-context-schema-implementation-facing-v1-2026-04-28.md`
- `/home/openclaw/.openclaw/workspace/task-manager/artifacts/openclaw-runtime-continuity-design-note-2026-04-28.md`
- `/home/openclaw/.openclaw/workspace/task-manager/artifacts/openclaw-file-first-storage-layout-lifecycle-note-2026-04-28.md`
- `/home/openclaw/.openclaw/workspace/task-manager/STRUCTURED_ADAPTER_CONTRACT.md`

---

## 1. Purpose

This blueprint answers, at implementation level:
1. which modules are needed,
2. where their responsibility boundaries are,
3. which minimal interfaces/contracts are required between them,
4. who reads and validates `TaskBrief`,
5. who owns `RunState`,
6. who owns lineage/resume/handoff,
7. who owns `ChildTask`/`ChildResult` delegation contract,
8. who owns `TopicContext`/routing/delivery,
9. who owns verification/acceptance,
10. where the hard boundaries sit between runtime core, storage layer, delivery layer, and memory layer.

This is **not** a general architecture overview. It is the recommended module cut for building v1.

---

## 2. Boundary model: the four major layers

## 2.1 Runtime core
Owns execution semantics and control flow.

Includes:
- task intake + launch preparation,
- run lifecycle,
- continuity transitions,
- child delegation,
- verification state transitions,
- context assembly for execution.

Must **not** directly own:
- filesystem path conventions,
- Telegram API details,
- long-term memory persistence internals.

## 2.2 Storage layer
Owns canonical persistence and retrieval of runtime objects/artifacts.

Includes:
- canonical file paths,
- atomic read/write/update of `TaskBrief`, `RunState`, `ChildTask`, `ChildResult`, `TopicContext`,
- artifact write/read/list/resolve.

Must **not** decide:
- whether a run should start,
- whether a child result is acceptable,
- how messages should be phrased to users.

## 2.3 Delivery layer
Owns inbound/outbound surface adaptation and delivery execution.

Includes:
- surface event normalization,
- topic/thread/chat metadata extraction,
- outbound message/media/status delivery,
- delivery receipts.

Must **not** own:
- run step loop,
- durable run state semantics,
- acceptance decisions.

## 2.4 Memory layer
Owns long-lived recall inputs that are **not** canonical runtime state.

Includes:
- durable memory facts,
- recall/search,
- optional operator profile / long-horizon facts,
- memory retrieval for context assembly.

Must **not** be treated as source of truth for:
- active run status,
- current waiting/blocked/terminal state,
- delegation lineage,
- acceptance outcome.

---

## 3. Recommended v1 module set

Minimum recommended module set:
1. `brief_registry`
2. `run_orchestrator`
3. `continuity_manager`
4. `delegation_manager`
5. `verification_manager`
6. `topic_router`
7. `delivery_gateway`
8. `context_assembler`
9. `state_store`
10. `artifact_store`
11. `memory_adapter`

If implementing in a small codebase, `state_store` and `artifact_store` may live in one package, but they should remain separate interfaces.

---

## 4. Module definitions, boundaries, and interfaces

## 4.1 `brief_registry`

### Purpose
Own the durable task contract lifecycle around `TaskBrief`.

### Owns
- load/create/update-version of `TaskBrief`,
- schema validation of `TaskBrief`,
- normalization/defaulting of bounded brief fields,
- refusal when required brief fields are missing.

### Must not own
- live run progression,
- topic delivery,
- artifact storage internals beyond calling storage interfaces.

### Answers key question
**Who reads/validates `TaskBrief`?**  
`brief_registry` is the authoritative reader/validator. `run_orchestrator` may consume a validated brief, but does not define brief validity.

### Minimal interfaces
```ts
loadTaskBrief(taskId): TaskBrief
loadTaskBriefByRef(taskBriefRef): TaskBrief
validateTaskBrief(candidate): ValidationResult
createTaskBrief(input): TaskBrief
reviseTaskBrief(taskId, patch, reason): TaskBriefVersion
```

### Required validations tied to schema note
Must enforce at least:
- `task_id`, `title`, `objective`, `scope`, `constraints`, `done_criteria`,
- `acceptance_criteria_ref`,
- `delivery_target`,
- `allowed_tools`,
- `topic_context_ref`,
- typed `input_artifact_refs`.

### Storage dependency
Uses `state_store` for canonical brief file and `artifact_store` for referenced inputs/acceptance artifacts.

---

## 4.2 `run_orchestrator`

### Purpose
Own the bounded execution lifecycle of one run.

### Owns
- creating a run from validated inputs,
- step loop ownership,
- state transition requests,
- stop reasons,
- handing off to context/tool/delegation/verification submodules,
- final run completion decision.

### Must not own
- raw filesystem layout,
- topic transport APIs,
- long-term memory writes,
- direct mutation of unvalidated task brief fields.

### Answers key question
**Who owns `RunState`?**  
`run_orchestrator` is the semantic owner of `RunState`; `state_store` is the persistence owner.

### Minimal interfaces
```ts
startRun(launchRequest): RunState
loadRun(runId): RunState
stepRun(runId): RunStepOutcome
resumeRun(runId, resumeInput): RunState
completeRun(runId, completionInput): RunState
failRun(runId, reason): RunState
cancelRun(runId, reason): RunState
```

### Required behavior
- persist after every meaningful state change,
- distinguish `waiting_user`, `waiting_external`, `blocked`, `completed`, `failed`, `cancelled`,
- never silently reactivate terminal runs,
- drive `verification_status` separately from `status`.

### Key dependencies
- validated `TaskBrief` from `brief_registry`,
- `RunState` persistence via `state_store`,
- context from `context_assembler`,
- delegation via `delegation_manager`,
- verification via `verification_manager`,
- routing/delivery via `topic_router` + `delivery_gateway`.

---

## 4.3 `continuity_manager`

### Purpose
Own lineage-safe pause/resume/handoff semantics.

### Owns
- same-run resume vs successor-run resume decision,
- `resume_from_run_id` linkage,
- handoff artifact requirements,
- continuity preconditions before yield/compression/wait,
- reopen rules for `blocked` or `waiting_*` states when new inputs arrive.

### Must not own
- actual step execution,
- child task semantics,
- message sending.

### Answers key questions
**Who manages lineage/resume/handoff?**  
`continuity_manager`.

### Minimal interfaces
```ts
preparePause(runId, pauseReason): ContinuityCheckpoint
prepareHandoff(runId, target): HandoffArtifactRef
resumeSameRun(runId, newInputs): RunState
createSuccessorRun(sourceRunId, resumeBasis): RunState
recordLineage(link): void
canTransitionFromBlocked(runId, newInputs): Decision
```

### Required rules tied to continuity/storage notes
- any intentional future continuation should write `handoff` artifact(s),
- terminal runs continue only via explicit successor lineage,
- `TaskBrief + TopicContext + artifact refs` must be sufficient for non-trivial restart,
- continuity state must be written before control is released.

### Key dependency split
- semantic decisions in `continuity_manager`,
- canonical writes in `state_store` / `artifact_store`.

---

## 4.4 `delegation_manager`

### Purpose
Own bounded parent/child delegation contract.

### Owns
- creation and validation of `ChildTask`,
- launch linkage from parent run to child run,
- ingestion and validation of `ChildResult`,
- parent-visible delegation status,
- enforcement that parent consumes structured child output rather than transcript replay.

### Must not own
- general run step loop for parent or child,
- routing to human delivery surfaces,
- final acceptance of top-level parent deliverable.

### Answers key question
**Who owns `ChildTask`/`ChildResult` delegation contract?**  
`delegation_manager`.

### Minimal interfaces
```ts
createChildTask(parentRunId, childSpec): ChildTask
launchChildRun(childTaskId): ChildRunRef
recordChildResult(childTaskId, result): ChildResult
validateChildResult(result): ValidationResult
listOpenChildren(parentRunId): ChildTaskRef[]
consumeChildResult(parentRunId, childTaskId): ParentMergeOutcome
```

### Required contract checks
On `ChildTask`:
- bounded `objective` and `scope`,
- `inputs`, `allowed_tools`, `output_contract`, `done_when`,
- `acceptance_criteria_ref`, `max_steps`, `timeout`, `topic_context_ref`.

On `ChildResult`:
- `status`, `stop_reason`, `summary`,
- `final_artifact_refs`, `evidence_artifact_refs`, `handoff_artifact_refs`,
- `verification_status`, `unresolved_issues`, `recommendation`, `completed_at`.

### Storage dependency
Uses `state_store` for child contract/result canonical files and `artifact_store` for referenced outputs/evidence.

---

## 4.5 `verification_manager`

### Purpose
Own verification/acceptance semantics independent of raw completion.

### Owns
- run-level verification state transitions,
- child-result verification state transitions,
- acceptance checks against `TaskBrief.acceptance_criteria_ref`,
- review gates and explicit acceptance/rejection recording,
- generation/linking of verification artifacts if needed.

### Must not own
- task brief intent,
- topic routing,
- file layout policy.

### Answers key question
**Who owns verification/acceptance?**  
`verification_manager`.

### Minimal interfaces
```ts
evaluateRunCompletion(runId): VerificationOutcome
evaluateChildResult(childTaskId): VerificationOutcome
markAccepted(subjectRef, actor, notes?): void
markRejected(subjectRef, actor, reason): void
requiresReview(subjectRef): boolean
```

### Required rules tied to schema note
- `completed` is not equivalent to `accepted`,
- `TaskBrief` defines acceptance criteria,
- `RunState` stores top-level verification state,
- `ChildResult` stores delegated-output verification state.

### Dependency boundary
May read from `brief_registry`, `state_store`, and `artifact_store`, but only `verification_manager` should decide acceptance transition semantics.

---

## 4.6 `topic_router`

### Purpose
Own `TopicContext` interpretation and execution routing decisions.

### Owns
- loading/validating `TopicContext`,
- mapping inbound normalized events to `task_id` / launch / no-op / status-only decisions,
- execution-group and topic-level policy checks,
- determining delivery target defaults from topic context.

### Must not own
- transport-specific parsing,
- run persistence,
- memory retrieval internals.

### Answers key question
**Who owns `TopicContext` and routing?**  
`topic_router` owns semantics of `TopicContext` and routing decisions.

### Minimal interfaces
```ts
loadTopicContext(topicContextId): TopicContext
validateTopicContext(candidate): ValidationResult
routeInboundEvent(event): RoutingDecision
resolveDeliveryTarget(topicContextId, event?): DeliveryTarget
```

### Required rules
Must enforce/interpret:
- `routing_mode`,
- `default_delivery_target`,
- `mention_policy`,
- `visibility_policy`,
- execution-group linkage.

### Storage dependency
Canonical `TopicContext` file from `state_store`.

---

## 4.7 `delivery_gateway`

### Purpose
Own inbound/outbound delivery-surface integration.

### Owns
- surface adapters (Telegram first in v1),
- normalized inbound event extraction,
- outbound send/edit/reply/media operations,
- delivery receipts and transient API errors.

### Must not own
- run lifecycle,
- task acceptance,
- resume lineage.

### Answers key question
**Who owns delivery?**  
`delivery_gateway`, with routing instructions from `topic_router` and output intents from `run_orchestrator`.

### Minimal interfaces
```ts
normalizeInbound(rawEvent): NormalizedEvent
sendDelivery(target, payload): DeliveryReceipt
sendStatus(target, statusPayload): DeliveryReceipt
sendArtifact(target, artifactRef, caption?): DeliveryReceipt
```

### Important boundary
`delivery_gateway` executes delivery; it does not decide *whether* a run should deliver, pause, or accept.

---

## 4.8 `context_assembler`

### Purpose
Build execution-facing context from canonical runtime state plus optional memory.

### Owns
- ordered context layer assembly,
- loading `TaskBrief`, `RunState`, `TopicContext`, open child summaries, relevant artifacts,
- bounded recall requests to memory,
- shaping model input.

### Must not own
- run lifecycle,
- storage path policy,
- acceptance decisions.

### Minimal interfaces
```ts
assembleForRun(runId): AssembledContext
assembleForChild(childTaskId): AssembledContext
collectRequiredArtifacts(runId): ArtifactRef[]
collectRecallInputs(runId): MemoryQuery[]
```

### Required boundary
Canonical runtime state comes from `brief_registry` + `state_store` + `artifact_store`; optional long-term recall comes through `memory_adapter` only.

---

## 4.9 `state_store`

### Purpose
Own canonical persistence of runtime state objects.

### Owns
- file layout and path resolution for:
  - `TaskBrief`,
  - `RunState`,
  - `ChildTask`,
  - `ChildResult`,
  - `TopicContext`,
- atomic writes,
- version-safe reads,
- optional derived index rebuild hooks.

### Must not own
- state transition legality,
- acceptance logic,
- routing semantics.

### Minimal interfaces
```ts
readTaskBrief(taskId): TaskBrief
writeTaskBrief(taskBrief): TaskBriefRef
readRunState(runId): RunState
writeRunState(runState): RunStateRef
readChildTask(childTaskId): ChildTask
writeChildTask(childTask): ChildTaskRef
readChildResult(childTaskId): ChildResult|null
writeChildResult(childResult): ChildResultRef
readTopicContext(topicContextId): TopicContext
writeTopicContext(topicContext): TopicContextRef
```

### Tied storage rules
Must map to canonical file-first layout from storage note, especially:
- one canonical `task-brief` per task,
- one canonical `run-state.json` per run,
- child contract/result under parent run lineage,
- topic context under topic scope.

---

## 4.10 `artifact_store`

### Purpose
Own file-first artifact persistence and typed artifact resolution.

### Owns
- typed artifact class validation,
- artifact path creation under task/run scope,
- write/read/list/resolve-latest for artifact files,
- handoff/evidence/final/verification artifact access.

### Must not own
- run semantics,
- child acceptance,
- message transport.

### Minimal interfaces
```ts
writeArtifact(scope, kind, content, metadata): ArtifactRef
readArtifact(ref): Artifact
listArtifacts(scope, filter?): ArtifactRef[]
resolveLatest(scope, kind): ArtifactRef|null
validateArtifactRef(ref): ValidationResult
```

### Required rules
Must preserve typed artifact classes:
- `input`
- `working`
- `final`
- `evidence`
- `handoff`
- `verification`

---

## 4.11 `memory_adapter`

### Purpose
Provide a narrow interface between runtime core and long-term memory systems.

### Owns
- recall/search API to long-term memory,
- optional memory write API if enabled by policy,
- conversion of memory results into context-safe references.

### Must not own
- active run state,
- task brief truth,
- topic routing,
- continuity lineage.

### Minimal interfaces
```ts
searchMemory(query, scope?): MemoryHit[]
getMemory(ref): MemoryRecord
writeMemory(entry): MemoryRef   // optional in v1
```

### Hard boundary
If the runtime needs to know whether work is active, waiting, blocked, resumed, or accepted, it must ask runtime state modules, not memory.

---

## 5. Minimal cross-module contracts

## 5.1 Launch contract
```ts
RunLaunchRequest {
  task_id: string
  task_brief_ref: string
  topic_context_ref: string
  delivery_target: string
  trigger_event_ref?: string
  resume_from_run_id?: string
}
```

Produced by: `topic_router` or explicit operator action.  
Consumed by: `run_orchestrator`.

## 5.2 Run persistence contract
`run_orchestrator` may change run state only through `state_store.writeRunState()` after semantic validation.

## 5.3 Delegation contract
- `delegation_manager.createChildTask()` creates canonical `ChildTask`.
- child execution returns canonical `ChildResult`.
- parent consumes child result by summary + artifact refs, not transcript replay.

## 5.4 Verification contract
- `verification_manager` reads acceptance criteria from `TaskBrief.acceptance_criteria_ref`.
- acceptance outcome is written back into `RunState` or `ChildResult`.
- no other module should silently infer acceptance from `completed`.

## 5.5 Routing/delivery contract
- `delivery_gateway` normalizes inbound surface events.
- `topic_router` decides whether/how the event maps to execution.
- `delivery_gateway` sends outbound payloads once runtime requests delivery.

---

## 6. Ownership answers to the 10 requested questions

1. **Main modules/subsystems needed**  
   `brief_registry`, `run_orchestrator`, `continuity_manager`, `delegation_manager`, `verification_manager`, `topic_router`, `delivery_gateway`, `context_assembler`, `state_store`, `artifact_store`, `memory_adapter`.

2. **Responsibility boundaries**  
   Runtime core = execution semantics; storage = canonical persistence; delivery = surface I/O; memory = long-term recall only.

3. **Minimal interfaces/contracts**  
   Validated `TaskBrief`, canonical `RunState`, canonical `ChildTask`/`ChildResult`, canonical `TopicContext`, typed `ArtifactRef`, and explicit launch/routing/verification contracts.

4. **Who reads/validates `TaskBrief`**  
   `brief_registry`.

5. **Who owns `RunState`**  
   Semantic ownership: `run_orchestrator`. Persistence ownership: `state_store`.

6. **Who owns lineage/resume/handoff**  
   `continuity_manager`.

7. **Who owns `ChildTask`/`ChildResult` delegation contract**  
   `delegation_manager`.

8. **Who owns `TopicContext`/routing/delivery**  
   `topic_router` owns `TopicContext` semantics and routing; `delivery_gateway` owns actual surface delivery.

9. **Who owns verification/acceptance**  
   `verification_manager`.

10. **Where the layer boundaries are**  
   Runtime core stops at semantic decisions; storage starts at canonical persistence; delivery starts at external surface adaptation/sending; memory starts at durable recall outside canonical runtime state.

---

## 7. Minimum v1 module set vs deferable pieces

## 7.1 Minimum v1 set (build now)

Must exist in v1:
- `brief_registry`
- `run_orchestrator`
- `continuity_manager`
- `delegation_manager`
- `verification_manager`
- `topic_router`
- `delivery_gateway` (Telegram-first adapter acceptable)
- `context_assembler`
- `state_store`
- `artifact_store`
- `memory_adapter` (read-only is enough)

Why this is the minimum:
- without `brief_registry`, `TaskBrief` validity is ambiguous,
- without `continuity_manager`, pause/resume/handoff becomes ad hoc,
- without `delegation_manager`, child lineage collapses into transcripts,
- without `verification_manager`, completion and acceptance get conflated,
- without separating `state_store` and `artifact_store`, canonical object state and large file artifacts get mixed.

## 7.2 Can be deferred safely

Can be postponed beyond v1:
- scheduler/background worker module,
- analytics/telemetry module,
- richer policy engine,
- multi-surface delivery adapters beyond Telegram,
- DB mirror/index layer over file-first storage,
- automated reminder/escalation services,
- advanced memory writeback.

These are useful, but not required to make the core contracts correct.

---

## 8. How this blueprint ties back to existing artifacts

## 8.1 Tied to execution-context schema
This blueprint is a module realization of the schema note’s entities and rules:
- `brief_registry` ↔ `TaskBrief`
- `run_orchestrator` + `continuity_manager` ↔ `RunState`
- `delegation_manager` ↔ `ChildTask` + `ChildResult`
- `topic_router` ↔ `TopicContext`
- `verification_manager` ↔ verification enums / acceptance distinction
- `artifact_store` ↔ typed `ArtifactRef` classes

## 8.2 Tied to continuity design note
This blueprint encodes the continuity note’s principles operationally:
- run continuity is owned by `run_orchestrator` + `continuity_manager`,
- written state before release is enforced through `state_store`/`artifact_store`,
- same-run vs successor-run resume is decided in `continuity_manager`,
- parent/child resumability is handled by `delegation_manager` using structured artifacts.

## 8.3 Tied to file-first storage/layout note
This blueprint assumes the storage note’s canonical locations:
- `TaskBrief` canonical file under task scope,
- `RunState` canonical file under run scope,
- child contract/result under parent lineage,
- `TopicContext` under topic scope,
- artifacts in typed folders (`input`, `working`, `final`, `evidence`, `handoff`, `verification`).

## 8.4 Tied to current adapter note
The structured adapter contract implies a useful boundary lesson for v1:
- adapters/wrappers should stay thin,
- execution semantics should remain in runtime core modules,
- machine-facing interfaces should delegate to governing state/logic modules rather than create shadow orchestration.

---

## 9. Practical implementation order

Recommended order:
1. `state_store` + `artifact_store`
2. `brief_registry`
3. `topic_router`
4. `run_orchestrator`
5. `continuity_manager`
6. `verification_manager`
7. `delegation_manager`
8. `context_assembler`
9. `delivery_gateway`
10. `memory_adapter`

Reason: canonical persistence and object validation must exist before reliable run semantics and delivery behavior.

---

## 10. Final implementation stance

If there is one architectural rule to preserve, it is this:

**Canonical runtime truth lives in `TaskBrief`, `RunState`, `ChildTask`, `ChildResult`, `TopicContext`, and typed artifacts — not in transcripts, not in delivery metadata, and not in memory.**

That rule is what keeps v1 resumable, inspectable, and safe to evolve.
