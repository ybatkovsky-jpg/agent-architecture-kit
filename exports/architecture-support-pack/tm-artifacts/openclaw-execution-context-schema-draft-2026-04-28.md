# OpenClaw execution-context schema draft

**Date:** 2026-04-28  
**Scope:** Practical schema draft for isolated runs, bounded task contracts, file-first artifacts, handoff/resume, topic-based execution, and parent/child result return.

---

## 1. Design intent

This document defines a practical v1 schema draft for the core execution-context entities:
- `RunState`
- `TaskBrief`
- `ChildTask`
- `ChildResult`
- `TopicContext`

The goal is not to produce final storage types or API bindings. The goal is to define the **operational data contracts** that make the runtime coherent.

These schemas are designed around:
- isolated runs instead of one giant ambient session,
- bounded task execution,
- file-first continuity,
- resumability from artifacts,
- topic-aware routing,
- narrow parent/child delegation.

---

# 2. Entity: `RunState`

## Purpose
`RunState` is the canonical runtime state object for a single isolated execution run.

It exists to answer:
- what this run is trying to do,
- what step it is on,
- what evidence/artifacts it has produced,
- why it is still active or why it stopped,
- how it can be resumed or handed off.

## Required fields
- `run_id` — unique identifier for this run
- `task_id` — stable task identifier associated with the run
- `status` — current status (`pending`, `running`, `completed`, `blocked`, `failed`, `cancelled`)
- `step_count` — number of completed steps
- `max_steps` — hard upper bound for loop iterations
- `stop_reason` — explicit terminal reason when no longer active
- `task_brief_ref` — artifact/path/reference for the originating `TaskBrief`
- `topic_context_ref` — reference to the associated `TopicContext`
- `artifact_refs` — list of artifacts produced or consumed by the run
- `delivery_target` — where results/status should be returned
- `created_at`
- `updated_at`

## Optional fields
- `parent_run_id` — if this run was launched by another run
- `child_run_ids` — child runs launched from this run
- `current_phase` — human-readable phase label
- `current_goal` — narrowed current objective within the task
- `last_model_action` — last decision/action type taken by the model
- `last_tool_observation_ref` — reference to the last normalized tool result
- `memory_refs` — durable memory items loaded into this run
- `skill_refs` — procedural skills loaded into this run
- `resume_token` — resumability marker/checkpoint ID
- `error_summary` — compact error state if failed/blocked
- `handoff_note_ref` — written handoff artifact for another run/operator
- `input_artifact_refs` — artifact refs used as run inputs
- `output_artifact_refs` — artifact refs considered final outputs
- `execution_group_id` — optional grouping ID for related runs

## Lifecycle role
`RunState` is the **live control object** of execution.

Typical lifecycle:
1. created from `TaskBrief` + `TopicContext`
2. updated at every loop step
3. accumulates artifact refs and observations
4. reaches terminal state
5. becomes resumable evidence for handoff, audit, or restart

## Relationships with other entities
- **belongs to** one `TaskBrief`
- **belongs to** one `TopicContext`
- **may have** one parent `RunState`
- **may launch** many child runs via `ChildTask`
- **may consume** many `ChildResult`s
- **references** artifacts for progress and outputs

## Minimal v1 version
```yaml
RunState:
  run_id: string
  task_id: string
  status: pending|running|completed|blocked|failed|cancelled
  step_count: integer
  max_steps: integer
  stop_reason: string|null
  task_brief_ref: string
  topic_context_ref: string
  artifact_refs: [string]
  delivery_target: string
  created_at: datetime
  updated_at: datetime
```

## Common failure modes
- `RunState` grows into a junk drawer for every possible runtime concern
- stop reasons are missing or inconsistent
- artifact references exist but no clear distinction between inputs, progress, and outputs
- resumability depends on hidden chat history instead of explicit refs
- parent/child linkage exists informally but not structurally

---

# 3. Entity: `TaskBrief`

## Purpose
`TaskBrief` is the written, file-first task contract that defines what a run is supposed to accomplish.

It is the main bridge between:
- operator intent,
- isolated execution,
- handoff/resume,
- reproducibility.

A `TaskBrief` should be sufficient to launch or relaunch a serious run without requiring the entire chat transcript.

## Required fields
- `task_id` — stable task identifier
- `title` — short human-readable task name
- `objective` — what must be accomplished
- `scope` — what is in-bounds
- `constraints` — non-negotiable boundaries/rules
- `done_criteria` — what counts as complete
- `delivery_target` — where result should go
- `allowed_tools` — allowed toolset/capabilities
- `topic_context_ref` — associated topic/execution context
- `created_at`
- `created_by`

## Optional fields
- `out_of_scope` — explicit exclusions
- `priority`
- `deadline`
- `input_artifact_refs`
- `expected_output_artifacts`
- `operator_notes`
- `skill_refs`
- `memory_refs`
- `preferred_output_format`
- `max_steps`
- `timeout`
- `resume_from_run_id`
- `parent_run_id`
- `execution_group_id`

## Lifecycle role
`TaskBrief` is the **execution contract artifact**.

Typical lifecycle:
1. authored by operator/system/parent run
2. passed into run creation
3. may be updated by a revised brief or appended note, but original brief should remain inspectable
4. reused for resume, retry, or child task generation

## Relationships with other entities
- **spawns** one or more `RunState`s over time
- **belongs to** one `TopicContext`
- **may produce** one or more `ChildTask`s as decompositions
- **references** artifacts and skills as execution inputs

## Minimal v1 version
```yaml
TaskBrief:
  task_id: string
  title: string
  objective: string
  scope: string
  constraints: [string]
  done_criteria: [string]
  delivery_target: string
  allowed_tools: [string]
  topic_context_ref: string
  created_at: datetime
  created_by: string
```

## Common failure modes
- brief is too vague to support isolated execution
- brief mixes high-level goal with transient runtime state
- done criteria are subjective or absent
- tool permissions are implicit rather than explicit
- resume depends on oral/chat memory instead of brief + artifacts

---

# 4. Entity: `ChildTask`

## Purpose
`ChildTask` is the bounded delegation contract sent from a parent run to a child run.

It exists to ensure that delegation is:
- explicit,
- narrow,
- verifiable,
- resumable,
- not just “go think about this.”

## Required fields
- `child_task_id` — unique child-task identifier
- `parent_run_id` — run that launched the child
- `objective` — specific delegated objective
- `scope` — what the child is allowed to do
- `inputs` — artifacts/context passed to child
- `allowed_tools` — allowed toolset for child
- `output_contract` — what the child must return
- `done_when` — completion criteria
- `max_steps` — bounded execution limit
- `timeout` — wall-clock bound
- `delivery_mode` — return-to-parent / artifact-only / routed-summary
- `created_at`

## Optional fields
- `topic_context_ref`
- `constraints`
- `out_of_scope`
- `skill_refs`
- `memory_refs`
- `priority`
- `expected_artifact_paths`
- `verification_requirements`
- `child_model_profile`
- `notes_for_child`

## Lifecycle role
`ChildTask` is a **delegation launch artifact/contract**.

Typical lifecycle:
1. parent run detects bounded offload opportunity
2. parent writes `ChildTask`
3. child run starts from that contract
4. child returns `ChildResult`
5. parent verifies/consumes result

## Relationships with other entities
- **created by** one parent `RunState`
- **may inherit context from** one `TaskBrief`
- **may be scoped by** one `TopicContext`
- **must produce** one `ChildResult`

## Minimal v1 version
```yaml
ChildTask:
  child_task_id: string
  parent_run_id: string
  objective: string
  scope: string
  inputs: [string]
  allowed_tools: [string]
  output_contract: [string]
  done_when: [string]
  max_steps: integer
  timeout: string
  delivery_mode: return_to_parent|artifact_only|routed_summary
  created_at: datetime
```

## Common failure modes
- child objective is too broad and becomes a second full agent
- output contract is prose-only and not checkable
- parent passes huge ambient context instead of curated inputs
- no timeout/max_steps, leading to unbounded offload
- child is asked to do work that actually needs operator interaction

---

# 5. Entity: `ChildResult`

## Purpose
`ChildResult` is the structured return object from a child run back to a parent run.

It exists to prevent delegated work from returning as an unstructured blob that pollutes the parent context.

## Required fields
- `child_task_id` — link back to originating child task
- `child_run_id` — run that executed the child task
- `status` — (`completed`, `blocked`, `failed`, `cancelled`)
- `summary` — compact human-readable result summary
- `artifact_refs` — artifacts produced by child
- `evidence_refs` — references supporting the result
- `unresolved_issues` — anything still open/blocking
- `recommendation` — what parent should do next
- `completed_at`

## Optional fields
- `structured_outputs` — machine-readable payload/results
- `verification_notes`
- `warnings`
- `resource_usage`
- `step_count`
- `stop_reason`
- `delivery_receipt`
- `handoff_note_ref`

## Lifecycle role
`ChildResult` is the **delegation return contract**.

Typical lifecycle:
1. child run reaches terminal state
2. child writes result artifact/object
3. parent retrieves and verifies it
4. parent either accepts, retries, escalates, or continues planning based on it

## Relationships with other entities
- **answers** one `ChildTask`
- **originates from** one child `RunState`
- **consumed by** one parent `RunState`
- **references** artifacts and evidence

## Minimal v1 version
```yaml
ChildResult:
  child_task_id: string
  child_run_id: string
  status: completed|blocked|failed|cancelled
  summary: string
  artifact_refs: [string]
  evidence_refs: [string]
  unresolved_issues: [string]
  recommendation: string
  completed_at: datetime
```

## Common failure modes
- summary is too long and replaces structured outputs
- no evidence refs, so parent cannot validate claims
- result hides blocked state under optimistic wording
- child returns “done” without artifact/output path
- parent consumes result blindly without verification rules

---

# 6. Entity: `TopicContext`

## Purpose
`TopicContext` captures the operational context of a topic/thread/execution-group in a Telegram-first environment.

It exists to answer:
- where this work belongs,
- how messages/tasks should be routed,
- what ambient rules govern participation,
- how delivery should return to the right operational surface.

## Required fields
- `topic_context_id` — unique topic-context identifier
- `platform` — e.g. `telegram`
- `chat_id` — platform chat/container ID
- `topic_id` — thread/topic identifier if applicable
- `execution_group_id` — stable grouping for work in this surface
- `routing_mode` — e.g. `trigger_only`, `ambient_observe`, `mixed`
- `default_delivery_target` — where outputs should return by default
- `created_at`
- `updated_at`

## Optional fields
- `topic_title`
- `owner_refs` — humans/agents responsible for this surface
- `allowed_run_types`
- `default_tool_policy`
- `participation_rules`
- `active_run_ids`
- `archival_refs`
- `summary_artifact_refs`
- `operator_notes`
- `mention_policy`
- `visibility_policy`

## Lifecycle role
`TopicContext` is the **operational routing envelope** for work.

Typical lifecycle:
1. created when a topic/work surface is recognized
2. attached to tasks and runs launched in that space
3. updated as routing/ownership rules evolve
4. used for delivery, grouping, and handoff clarity

## Relationships with other entities
- **contains** many `TaskBrief`s
- **contains** many `RunState`s over time
- **may scope** `ChildTask`s if child work remains attached to same topic semantics
- **anchors** default delivery behavior

## Minimal v1 version
```yaml
TopicContext:
  topic_context_id: string
  platform: string
  chat_id: string
  topic_id: string|null
  execution_group_id: string
  routing_mode: trigger_only|ambient_observe|mixed
  default_delivery_target: string
  created_at: datetime
  updated_at: datetime
```

## Common failure modes
- topic context is treated as just a message bucket, not an execution surface
- routing mode is implicit and causes accidental launches
- ownership rules are unclear
- delivery target and execution origin are conflated
- parent/child work crosses topics without explicit linkage

---

# 7. Cross-entity relationships

## Recommended relationship model
- `TopicContext` defines the operational surface
- `TaskBrief` defines a bounded unit of work within that surface
- `RunState` is the live execution instance for that work
- `ChildTask` is a delegated bounded sub-contract emitted from a parent `RunState`
- `ChildResult` is the structured return from the child back into the parent run

## Typical execution chain
1. incoming trigger resolves to `TopicContext`
2. system/operator creates `TaskBrief`
3. runtime creates `RunState`
4. run writes artifacts and may emit `ChildTask`
5. child run returns `ChildResult`
6. parent updates `RunState`
7. final output delivered using `TopicContext` default or explicit delivery target

---

# 8. Minimal v1 bundle

If v1 must stay minimal, the smallest coherent set is:

## Required v1 entities
- `TaskBrief`
- `RunState`
- `TopicContext`

## Add delegation only when ready
- `ChildTask`
- `ChildResult`

## Why
Without `TaskBrief`, runs are too ambient.  
Without `RunState`, execution is not inspectable.  
Without `TopicContext`, Telegram/topic routing stays ambiguous.  
Without `ChildTask` and `ChildResult`, delegation should not be introduced.

---

# 9. Schema design rules

1. **Every non-trivial run must be reconstructable from files and references.**
2. **Every terminal state must be explicit.**
3. **Every delegated task must have a verifiable output contract.**
4. **Every result path must be attached to a delivery target or topic context.**
5. **Do not use hidden conversational context as the only state carrier.**
6. **Do not blur task contract, live run state, and durable memory into one object.**
7. **Prefer explicit references to large payload embedding.**

---

# 10. Most likely schema mistakes to avoid

1. Making `RunState` the storage location for everything in the system
2. Treating `TaskBrief` as a mutable chat summary instead of a task contract
3. Letting `ChildTask` be too broad to be bounded
4. Letting `ChildResult` be essay-shaped instead of contract-shaped
5. Treating `TopicContext` as metadata instead of routing/control context
6. Storing artifacts implicitly instead of by explicit references
7. Omitting stop reasons and verification pathways

---

# 11. Final recommendation

For v1, stabilize these three first:
- `TaskBrief`
- `RunState`
- `TopicContext`

Then add:
- `ChildTask`
- `ChildResult`

only when the base runtime already supports:
- bounded steps,
- explicit stop reasons,
- artifact-backed continuity,
- topic-aware delivery,
- deterministic context assembly.
