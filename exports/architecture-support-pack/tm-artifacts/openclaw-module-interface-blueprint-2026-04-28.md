# OpenClaw module/interface blueprint — Hermes-pattern adoption

**Date:** 2026-04-28  
**Related RFC:** `/home/openclaw/.openclaw/workspace/task-manager/artifacts/openclaw-hermes-pattern-adoption-rfc-2026-04-28.md`  
**Related Backlog:** `/home/openclaw/.openclaw/workspace/task-manager/artifacts/openclaw-hermes-pattern-adoption-implementation-backlog-2026-04-28.md`

---

## 1. Purpose

This document proposes a concrete module boundary layout for an OpenClaw-like runtime that selectively adopts Hermes-style control patterns.

The design is optimized for:
- bounded isolated runs,
- Telegram operational contour,
- topic-aware routing,
- file-first artifacts,
- explicit memory boundaries,
- later addition of delegation and background execution.

This is not a code-level implementation spec. It is a **module/interface boundary blueprint**.

---

## 2. Design principles

1. **Core runtime must not know Telegram details directly.**
2. **Artifacts are first-class runtime state carriers.**
3. **Prompt/context assembly must be explicit and inspectable.**
4. **Memory classes must stay separated by interface, not only by convention.**
5. **Delegation and scheduling must plug into the run engine, not rewrite it.**
6. **Delivery is not execution.**
7. **Every module should expose the narrowest interface that preserves operator clarity.**

---

## 3. Top-level module map

Recommended top-level modules:

1. `gateway.telegram`
2. `routing`
3. `run_engine`
4. `context_assembly`
5. `tool_runtime`
6. `artifact_store`
7. `memory_store`
8. `skill_store`
9. `delivery`
10. `delegation`
11. `scheduler`
12. `recall`
13. `policy`

---

## 4. Module definitions

## 4.1 `gateway.telegram`

### Responsibility
Translate Telegram-native events into normalized runtime events and send outbound messages/media back through Telegram.

### Owns
- Telegram update ingestion
- parsing topic/thread metadata
- extracting reply linkage
- mention/trigger detection
- mapping media into normalized references

### Must not own
- run orchestration logic
- memory policy
- prompt construction
- execution loop decisions

### Input
- raw Telegram updates/events

### Output
- `NormalizedEvent`
- outbound delivery requests to `delivery`

### Key interfaces
- `parse_telegram_update(update) -> NormalizedEvent`
- `detect_trigger(event) -> TriggerDecision`
- `extract_delivery_context(event) -> DeliveryTarget`

---

## 4.2 `routing`

### Responsibility
Map normalized inbound events to execution decisions and execution groups/topics.

### Owns
- event-to-task routing
- execution-group association
- ambient vs active execution decision
- task/run launch policy hooks

### Must not own
- Telegram API logic
- model invocation
- artifact persistence internals

### Input
- `NormalizedEvent`

### Output
- `RunLaunchRequest`
- `NoOpDecision`
- `StatusOnlyDecision`

### Key interfaces
- `route_event(event) -> RoutingDecision`
- `resolve_execution_group(event) -> ExecutionGroupRef`
- `should_launch_run(event) -> bool`

---

## 4.3 `run_engine`

### Responsibility
Execute a bounded model/tool loop for a single run.

### Owns
- run lifecycle
- step iteration
- terminal states
- stop reasons
- main reason/act/observe loop

### Must not own
- Telegram-specific branching
- long-term memory persistence policy
- direct artifact storage implementation

### Input
- `RunLaunchRequest`
- `RunState`
- assembled context
- scoped toolset

### Output
- updated `RunState`
- `RunResult`
- artifact write requests
- delivery intents

### Key interfaces
- `start_run(request) -> RunState`
- `step_run(run_state) -> RunStepOutcome`
- `complete_run(run_state) -> RunResult`
- `resume_run(run_state_ref) -> RunState`

---

## 4.4 `context_assembly`

### Responsibility
Build deterministic model input context from ordered layers.

### Owns
- layer ordering
- inclusion policy
- artifact reference resolution
- per-run context shaping

### Must not own
- actual memory storage
- tool execution
- delivery routing

### Input
- `RunState`
- `TaskBrief`
- `TopicContext`
- memory facts
- skills
- artifact refs
- recent interaction window

### Output
- `AssembledContext`

### Key interfaces
- `assemble_context(run_state) -> AssembledContext`
- `collect_context_layers(run_state) -> ContextLayerSet`
- `render_model_input(layer_set) -> ModelInput`

---

## 4.5 `tool_runtime`

### Responsibility
Provide scoped capability execution for tools.

### Owns
- tool registration
- per-run tool scoping
- normalized tool invocation records
- tool result shaping

### Must not own
- routing policy
- task definition
- memory writes beyond explicit result recording pathways

### Input
- `ToolInvocationRequest`
- run-scoped capability set

### Output
- `ToolInvocationResult`
- normalized tool observation

### Key interfaces
- `resolve_toolset(run_state) -> Toolset`
- `invoke_tool(request) -> ToolInvocationResult`
- `normalize_tool_result(raw_result) -> ToolObservation`

---

## 4.6 `artifact_store`

### Responsibility
Persist and retrieve file-first runtime artifacts.

### Owns
- artifact path conventions
- artifact metadata
- write/read/update operations
- artifact linkage across runs

### Must not own
- task routing
- memory classification
- direct Telegram delivery concerns

### Artifact classes
- task brief
- progress snapshot
- final report
- handoff note
- child result
- execution log refs

### Key interfaces
- `write_artifact(artifact) -> ArtifactRef`
- `read_artifact(ref) -> Artifact`
- `list_artifacts(run_id|task_id) -> list[ArtifactRef]`
- `resolve_latest_artifact(kind, scope) -> ArtifactRef | None`

---

## 4.7 `memory_store`

### Responsibility
Store and retrieve durable facts and operator profile separately from transcripts and artifacts.

### Owns
- durable fact storage
- operator profile storage
- memory write criteria enforcement

### Must not own
- session transcript persistence
- procedural skill text
- current run state artifacts

### Subareas
- `durable_facts`
- `operator_profile`

### Key interfaces
- `get_relevant_facts(query) -> list[MemoryFact]`
- `write_fact(fact) -> MemoryFactRef`
- `get_operator_profile() -> OperatorProfile`
- `update_operator_profile(patch) -> OperatorProfile`

---

## 4.8 `skill_store`

### Responsibility
Store and serve procedural skills/workflow overlays.

### Owns
- skill file format
- skill discovery/loading
- skill matching rules
- skill metadata and hygiene hooks

### Must not own
- durable fact storage
- tool execution
- direct runtime control

### Key interfaces
- `match_skills(run_state) -> list[SkillRef]`
- `load_skill(ref) -> SkillDocument`
- `validate_skill(doc) -> ValidationResult`
- `list_skills() -> list[SkillMetadata]`

---

## 4.9 `delivery`

### Responsibility
Handle outbound user/operator-facing delivery independent of execution.

### Owns
- output routing
- topic/thread targeting
- media vs text delivery decisions
- status update formatting

### Must not own
- reasoning logic
- run step loop
- Telegram event ingestion

### Input
- `DeliveryIntent`
- `RunResult`
- `ArtifactRef`

### Output
- platform-specific send requests

### Key interfaces
- `resolve_delivery_target(intent) -> DeliveryTarget`
- `deliver_message(target, payload) -> DeliveryReceipt`
- `deliver_artifact_summary(target, artifact_ref) -> DeliveryReceipt`

---

## 4.10 `delegation`

### Responsibility
Launch and manage isolated child runs under strict parent-child contracts.

### Owns
- child task schema
- child launch flow
- child result schema
- verification hooks

### Must not own
- generic run stepping logic
- Telegram message parsing
- global scheduler logic

### Key interfaces
- `launch_child(task) -> ChildRunRef`
- `poll_child(ref) -> ChildStatus`
- `collect_child_result(ref) -> ChildResult`
- `verify_child_result(result) -> VerificationOutcome`

---

## 4.11 `scheduler`

### Responsibility
Manage isolated background and scheduled runs.

### Owns
- job definitions
- schedule triggers
- pause/resume state
- isolated launch of scheduled work

### Must not own
- reuse of live thread context as primary input
- execution loop internals
- Telegram routing internals

### Key interfaces
- `create_job(job_spec) -> JobRef`
- `run_due_jobs(now) -> list[RunLaunchRequest]`
- `pause_job(job_id)`
- `resume_job(job_id)`

---

## 4.12 `recall`

### Responsibility
Provide selective retrieval of historical sessions/artifacts into current runs.

### Owns
- search interfaces
- recall ranking
- retrieval shaping for runtime inclusion

### Must not own
- become ambient always-on memory injection

### Key interfaces
- `search_artifacts(query) -> list[ArtifactRef]`
- `search_sessions(query) -> list[SessionRef]`
- `prepare_recall_context(matches) -> RecallBundle`

---

## 4.13 `policy`

### Responsibility
Centralize execution rules and boundary decisions.

### Owns
- memory write policy
- trigger policy
- tool exposure policy
- skill loading policy
- background notification policy

### Must not own
- low-level storage implementation
- model/tool execution logic

### Key interfaces
- `should_write_memory(item) -> bool`
- `allowed_toolset_for(run_state) -> ToolsetPolicy`
- `should_load_skill(skill, run_state) -> bool`
- `should_notify(job_result) -> bool`

---

## 5. Cross-module data flow

Recommended primary flow:

1. `gateway.telegram` parses raw update into `NormalizedEvent`
2. `routing` decides whether to launch a run
3. `artifact_store` creates/loads task brief and prior state refs
4. `run_engine` starts or resumes run
5. `context_assembly` builds model input
6. `run_engine` asks model for next step
7. `tool_runtime` executes tool if requested
8. `artifact_store` stores outputs/snapshots
9. `delivery` sends status/final result to correct target
10. optional: `memory_store`, `skill_store`, `delegation`, `scheduler`, `recall` participate via explicit interfaces

---

## 6. Interface contracts that matter most in v1

The most important contracts to stabilize early are:

1. `NormalizedEvent`
2. `RunLaunchRequest`
3. `RunState`
4. `RunResult`
5. `TaskBrief`
6. `ArtifactRef`
7. `ToolObservation`
8. `DeliveryIntent`

If these are stable, most later features can be added without changing the runtime spine.

---

## 7. Module dependency rules

### Allowed dependency direction
- outer platform modules may depend on core interfaces
- runtime modules may depend on policy/storage interfaces
- storage modules should not depend on platform modules
- delivery may depend on platform adapters but not vice versa

### Forbidden dependency direction
- `run_engine` importing Telegram adapter details
- `memory_store` reaching into platform events directly
- `artifact_store` deciding routing or trigger policy
- `scheduler` depending on live thread state as required input

---

## 8. Suggested implementation order

### Step 1
- `run_engine`
- `artifact_store`
- `context_assembly`
- `tool_runtime`

### Step 2
- `gateway.telegram`
- `routing`
- `delivery`

### Step 3
- `memory_store`
- `skill_store`
- `policy`

### Step 4
- `delegation`
- `scheduler`
- `recall`

---

## 9. Final recommendation

For this runtime, the best boundary strategy is:
- keep the **run engine** small and strict,
- keep **Telegram** outside the reasoning core,
- make **artifacts** the main continuity layer,
- keep **memory** and **skills** explicit and separate,
- add **delegation** and **scheduler** as pluggable extensions after the runtime spine is stable.

This preserves the strongest Hermes-inspired architectural advantages without importing Hermes-scale complexity too early.