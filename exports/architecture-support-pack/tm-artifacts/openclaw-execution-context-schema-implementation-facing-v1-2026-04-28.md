# OpenClaw execution-context schema — implementation-facing v1

**Date:** 2026-04-28  
**Base draft:** `/home/openclaw/.openclaw/workspace/task-manager/artifacts/openclaw-execution-context-schema-draft-2026-04-28.md`  
**Refinement prompt:** `/home/openclaw/.openclaw/workspace/task-manager/artifacts/openclaw-execution-context-schema-refinement-prompt-2026-04-28.md`

---

## Layer 1 — Key refinements

This version tightens the base draft in five ways:

1. **Typed artifact classes** are now explicit instead of generic `*_artifact_refs` blobs.
2. **Waiting semantics** are separated from `blocked` so runtime can distinguish pause vs dead-end.
3. **Verification / acceptance** is now a first-class contract instead of implied completion.
4. **Lifecycle transitions** are defined more normatively, especially for `RunState`.
5. **Storage mapping** is explicit so entities are tied to file-first operational reality.

---

## Global design assumptions

This schema is optimized for:
- isolated runs
- bounded tasks
- file-first artifacts
- resumability from written state
- Telegram topic-based execution
- explicit parent/child delegation

This is **not** a giant platform schema. It is a strict v1 operational schema.

---

## Artifact classes (global)

All entities that reference artifacts must use typed artifact references from this set:

- `input` — upstream input material required to begin work
- `working` — intermediate state/output created during execution
- `final` — deliverable end-state output of a run/task
- `evidence` — supporting proof used to justify a claim/result
- `handoff` — written state intended for resume, transfer, or review
- `verification` — artifacts created specifically for validation/review/acceptance

### Design rule
A generic untyped `artifact_refs` field is not sufficient for implementation-facing v1.

### Artifact reference shape
Minimal normalized artifact ref:
```yaml
ArtifactRef:
  artifact_id: string
  kind: input|working|final|evidence|handoff|verification
  path: string
  created_at: datetime
  created_by: string
  description: string|null
```

---

## Layer 2 — Refined schema by entity

# 1. `RunState`

## Purpose
`RunState` is the authoritative live execution-state object for one isolated run.

It answers:
- what is executing,
- what state it is in,
- what step it has reached,
- what written evidence/artifacts exist,
- whether it is active, waiting, terminal, or resumable.

## Refined required fields
- `run_id` — immutable unique run identifier
- `task_id` — stable task identity this run is executing
- `status` — authoritative runtime status enum
- `step_count` — authoritative count of completed loop steps
- `max_steps` — hard execution bound
- `stop_reason` — required when terminal, otherwise null
- `task_brief_ref` — immutable ref to originating task brief
- `topic_context_ref` — immutable ref to topic execution surface
- `delivery_target` — explicit return target for outputs/status
- `input_artifact_refs` — typed refs required as run inputs
- `working_artifact_refs` — typed refs for in-progress state
- `final_artifact_refs` — typed refs for final outputs
- `evidence_artifact_refs` — typed refs supporting decisions/results
- `handoff_artifact_refs` — typed refs for resume/transfer
- `verification_status` — run-level verification state
- `needs_review` — explicit review gate flag
- `created_at`
- `updated_at`

## Refined optional fields
- `parent_run_id`
- `child_run_ids`
- `current_phase`
- `current_goal`
- `last_model_action`
- `last_tool_observation_ref`
- `memory_refs`
- `skill_refs`
- `resume_from_run_id`
- `resume_checkpoint_ref`
- `error_summary`
- `accepted_by`
- `accepted_at`
- `verification_notes_ref`
- `execution_group_id`
- `waiting_reason`
- `external_dependency_ref`

## Artifact ownership / ref types
`RunState` may reference all artifact classes:
- `input` for run inputs
- `working` for stepwise outputs/state snapshots
- `final` for final deliverables
- `evidence` for proof and supporting material
- `handoff` for explicit resumption or transfer notes
- `verification` for review/check artifacts

## Lifecycle role
`RunState` is the live control object used by runtime orchestration.
It is mutable during execution and must be persistable after every state-changing step.

## Status enum
Required v1 enum:
- `pending`
- `running`
- `waiting_user`
- `waiting_external`
- `blocked`
- `completed`
- `failed`
- `cancelled`

### Status semantics
- `pending` — created, not yet executing
- `running` — actively making progress
- `waiting_user` — progress paused until explicit operator/user input
- `waiting_external` — progress paused until external system/event/input arrives
- `blocked` — no valid next step exists under current constraints
- `completed` — execution finished its contract
- `failed` — execution terminated due to unrecoverable internal/external failure
- `cancelled` — intentionally stopped by operator/system

## Lifecycle transitions
Allowed transitions:
- `pending -> running`
- `running -> waiting_user`
- `running -> waiting_external`
- `running -> blocked`
- `running -> completed`
- `running -> failed`
- `running -> cancelled`
- `waiting_user -> running`
- `waiting_user -> cancelled`
- `waiting_external -> running`
- `waiting_external -> blocked`
- `waiting_external -> cancelled`
- `blocked -> running` only if new input/artifact/constraint change is recorded
- `blocked -> cancelled`

Illegal transitions:
- `completed -> running`
- `failed -> running`
- `cancelled -> running`
- any terminal state change without creating a new resumed run or explicit resume record

Terminal states:
- `completed`
- `failed`
- `cancelled`

Non-terminal but non-progress states:
- `waiting_user`
- `waiting_external`
- `blocked`

## Verification / acceptance role
A run may be `completed` but still not fully accepted.

Required run-level verification enum:
- `not_required`
- `pending_verification`
- `verified`
- `verification_failed`
- `accepted`
- `rejected`

### Rule
`status=completed` means execution finished.  
`verification_status=accepted` means result is actually accepted as sufficient.

## Storage location in file-first runtime
Should live as a **runtime state file** or equivalent task-manager execution-state artifact.

Recommended storage form:
- one current canonical state file per run
- append-only event/history log optional but secondary
- artifact refs point outward instead of embedding large payloads

## Minimal v1 version
```yaml
RunState:
  run_id: string
  task_id: string
  status: pending|running|waiting_user|waiting_external|blocked|completed|failed|cancelled
  step_count: integer
  max_steps: integer
  stop_reason: string|null
  task_brief_ref: string
  topic_context_ref: string
  delivery_target: string
  input_artifact_refs: [ArtifactRef]
  working_artifact_refs: [ArtifactRef]
  final_artifact_refs: [ArtifactRef]
  evidence_artifact_refs: [ArtifactRef]
  handoff_artifact_refs: [ArtifactRef]
  verification_status: not_required|pending_verification|verified|verification_failed|accepted|rejected
  needs_review: boolean
  created_at: datetime
  updated_at: datetime
```

## Common failure modes
- using `blocked` for everything that is really waiting
- treating completion as automatic acceptance
- storing large mutable payloads directly inside run state
- losing resumability because handoff refs are optional in practice but never written
- mutating terminal runs instead of creating explicit resume lineage

---

# 2. `TaskBrief`

## Purpose
`TaskBrief` is the durable execution contract for a bounded unit of work.

It should be sufficient to launch or relaunch a non-trivial run without relying on chat history as the source of truth.

## Refined required fields
- `task_id` — immutable task identifier
- `title` — short human-readable task name
- `objective` — authoritative target outcome
- `scope` — in-bounds work definition
- `constraints` — hard constraints / rules
- `done_criteria` — explicit completion criteria
- `acceptance_criteria_ref` — artifact or structured ref defining how result is accepted
- `delivery_target` — intended result destination
- `allowed_tools` — explicit tool/capability scope
- `topic_context_ref` — operational surface where task belongs
- `input_artifact_refs`
- `expected_final_artifact_types` — what kinds of outputs are expected
- `created_at`
- `created_by`

## Refined optional fields
- `out_of_scope`
- `priority`
- `deadline`
- `working_artifact_refs`
- `skill_refs`
- `memory_refs`
- `preferred_output_format`
- `max_steps`
- `timeout`
- `resume_from_run_id`
- `parent_run_id`
- `execution_group_id`
- `notes`
- `review_required`
- `verification_notes_ref`

## Artifact ownership / ref types
`TaskBrief` should primarily reference:
- `input`
- `verification`
- optionally `handoff` if the brief is produced as part of resume/transfer

It should not be the primary owner of `working` artifacts.

## Lifecycle role
`TaskBrief` is a durable contract artifact. It is authoritative for task intent, scope, and acceptance criteria.

### Mutability rule
The original brief should remain inspectable. Revisions should be versioned or appended, not silently overwritten.

## Verification / acceptance role
`TaskBrief` owns the definition of acceptance, not the result of acceptance.

Meaning:
- `done_criteria` = execution completeness
- `acceptance_criteria_ref` = acceptance standard

## Storage location in file-first runtime
Should live as a **task-manager artifact** or durable task contract file.

Recommended storage form:
- one file per task brief
- revisions as separate versioned artifacts or appended addenda

## Minimal v1 version
```yaml
TaskBrief:
  task_id: string
  title: string
  objective: string
  scope: string
  constraints: [string]
  done_criteria: [string]
  acceptance_criteria_ref: string
  delivery_target: string
  allowed_tools: [string]
  topic_context_ref: string
  input_artifact_refs: [ArtifactRef]
  expected_final_artifact_types: [string]
  created_at: datetime
  created_by: string
```

## Common failure modes
- vague objective with no bounded scope
- done criteria exist but acceptance criteria do not
- hidden reliance on chat context for crucial constraints
- task brief drifting into run log / mutable state
- permissions/tool scope inferred instead of written

---

# 3. `ChildTask`

## Purpose
`ChildTask` is the bounded delegation contract from a parent run to a child run.

It defines what is delegated, with what inputs, under what limits, and with what expected return shape.

## Refined required fields
- `child_task_id`
- `parent_run_id`
- `parent_task_id`
- `objective`
- `scope`
- `constraints`
- `inputs` — explicit refs/inputs passed to child
- `allowed_tools`
- `output_contract`
- `done_when`
- `acceptance_criteria_ref`
- `max_steps`
- `timeout`
- `delivery_mode` — how result returns
- `topic_context_ref`
- `created_at`

## Refined optional fields
- `out_of_scope`
- `skill_refs`
- `memory_refs`
- `priority`
- `expected_final_artifact_types`
- `verification_requirements`
- `child_model_profile`
- `notes_for_child`
- `resume_context_ref`

## Artifact ownership / ref types
`ChildTask` should primarily reference:
- `input`
- `verification`
- optionally `handoff`

It may specify expected `final` and `evidence` artifact classes in its output contract.

## Lifecycle role
`ChildTask` is a launch contract artifact for child execution. It is immutable after launch except for explicit cancellation metadata.

## Verification / acceptance role
`ChildTask` should define what kind of result is acceptable from the child, but not record the final acceptance outcome itself.

## Storage location in file-first runtime
Should live as a **child-task artifact** under the parent task/run lineage.

## Minimal v1 version
```yaml
ChildTask:
  child_task_id: string
  parent_run_id: string
  parent_task_id: string
  objective: string
  scope: string
  constraints: [string]
  inputs: [ArtifactRef]
  allowed_tools: [string]
  output_contract: [string]
  done_when: [string]
  acceptance_criteria_ref: string
  max_steps: integer
  timeout: string
  delivery_mode: return_to_parent|artifact_only|routed_summary
  topic_context_ref: string
  created_at: datetime
```

## Common failure modes
- child scope broad enough to become a second main agent
- no acceptance criteria beyond “try your best”
- parent passes ambient chat context instead of typed inputs
- expected output form is not checkable
- no hard execution limits

---

# 4. `ChildResult`

## Purpose
`ChildResult` is the structured return contract from child execution back to parent control flow.

It exists to keep delegated work inspectable, verifiable, and compact.

## Refined required fields
- `child_task_id`
- `child_run_id`
- `status`
- `stop_reason`
- `summary`
- `final_artifact_refs`
- `evidence_artifact_refs`
- `handoff_artifact_refs`
- `verification_status`
- `needs_review`
- `unresolved_issues`
- `recommendation`
- `completed_at`

## Refined optional fields
- `working_artifact_refs`
- `verification_notes_ref`
- `accepted_by`
- `accepted_at`
- `warnings`
- `resource_usage`
- `step_count`
- `delivery_receipt`
- `structured_outputs`

## Artifact ownership / ref types
`ChildResult` should primarily own/reference:
- `final`
- `evidence`
- `handoff`
- `verification`
- optionally `working` if the parent needs to inspect intermediate traces

## Lifecycle role
`ChildResult` is the terminal return artifact of child execution. It should be written once per child run completion and then consumed by the parent.

## Status enum
Required v1 child-result status enum:
- `completed`
- `blocked`
- `failed`
- `cancelled`

## Verification / acceptance role
`ChildResult` needs an explicit acceptance layer because a child can claim completion without satisfying the parent’s actual standards.

Required child-result verification enum:
- `pending_verification`
- `verified`
- `verification_failed`
- `accepted`
- `rejected`

### Rule
A parent must not treat `status=completed` as equivalent to `accepted`.

## Storage location in file-first runtime
Should live as a **child-result artifact** written by the child and read by the parent.

## Minimal v1 version
```yaml
ChildResult:
  child_task_id: string
  child_run_id: string
  status: completed|blocked|failed|cancelled
  stop_reason: string
  summary: string
  final_artifact_refs: [ArtifactRef]
  evidence_artifact_refs: [ArtifactRef]
  handoff_artifact_refs: [ArtifactRef]
  verification_status: pending_verification|verified|verification_failed|accepted|rejected
  needs_review: boolean
  unresolved_issues: [string]
  recommendation: string
  completed_at: datetime
```

## Common failure modes
- result is prose-heavy but structurally weak
- no evidence artifacts to support claims
- optimistic summary masks blocked/failed state
- parent accepts result without recorded verification
- final artifact path omitted even though “done” is claimed

---

# 5. `TopicContext`

## Purpose
`TopicContext` defines the operational execution surface for a Telegram-first topic/thread/execution group.

It captures routing and default delivery behavior, not live task state.

## Refined required fields
- `topic_context_id`
- `platform`
- `chat_id`
- `topic_id`
- `execution_group_id`
- `routing_mode`
- `default_delivery_target`
- `mention_policy`
- `visibility_policy`
- `created_at`
- `updated_at`

## Refined optional fields
- `topic_title`
- `owner_refs`
- `allowed_run_types`
- `default_tool_policy`
- `participation_rules`
- `active_run_ids`
- `summary_artifact_refs`
- `operator_notes`
- `archival_refs`

## Artifact ownership / ref types
`TopicContext` may reference:
- `handoff` for topic-level continuity notes
- `verification` for operational policy docs
- `final` for periodic summaries if needed

It should not be the owner of per-run `working` artifacts.

## Lifecycle role
`TopicContext` is a durable routing/control context for work happening in a topic. It persists across many tasks and runs.

## Routing enum
Required v1 enum:
- `trigger_only`
- `ambient_observe`
- `mixed`

### Routing semantics
- `trigger_only` — work launches only from explicit triggers/commands/mentions
- `ambient_observe` — system may monitor but not actively execute unless configured
- `mixed` — both ambient and explicit trigger behavior are allowed by policy

## Verification / acceptance role
`TopicContext` does not own task acceptance. It owns topic-level participation and routing policy only.

## Storage location in file-first runtime
Should live as a **topic context file** or operational-surface config artifact.

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
  mention_policy: string
  visibility_policy: string
  created_at: datetime
  updated_at: datetime
```

## Common failure modes
- treating topic context as mere metadata instead of control context
- blending topic-level rules with run-level state
- implicit routing behavior not written anywhere
- delivery target confused with execution origin
- no durable context for execution-group continuity

---

## Layer 3 — Cross-entity rules

# A. Typed artifact-class rules

## Required classes
- `input`
- `working`
- `final`
- `evidence`
- `handoff`
- `verification`

## Rules
1. Every final claim should have either `final` artifacts, `evidence` artifacts, or both.
2. `working` artifacts are resumability aids, not acceptance evidence by default.
3. `handoff` artifacts are required when a run is intentionally paused for transfer/resume.
4. `verification` artifacts should exist whenever verification is not trivial or purely human-verbal.

---

# B. Waiting vs blocked semantics

## `waiting_user`
Use when a valid next step exists but explicit operator/user input is required.

Examples:
- confirmation needed
- missing decision from Юрий
- approval gate not yet passed

## `waiting_external`
Use when a valid next step exists but an external event/system/output is pending.

Examples:
- HTTP callback awaited
- CI/build still running
- external API response pending

## `blocked`
Use when no valid next step exists under current constraints, inputs, or permissions.

Examples:
- missing critical data with no retrieval path
- impossible action under allowed tools
- contradictory constraints

## Rule
Do not collapse `waiting_*` into `blocked`.  
Waiting implies resumable forward path.  
Blocked implies no current executable path.

---

# C. Verification / acceptance model

## Core distinction
- **completed** = execution stopped with task-performer’s definition of done
- **verified** = result checked against evidence/criteria
- **accepted** = operator/parent/system accepts result as sufficient

## Required verification enum families
For runs:
- `not_required`
- `pending_verification`
- `verified`
- `verification_failed`
- `accepted`
- `rejected`

For child results:
- `pending_verification`
- `verified`
- `verification_failed`
- `accepted`
- `rejected`

## Acceptance rules
1. `TaskBrief` defines acceptance criteria.
2. `RunState` records verification/acceptance state for top-level execution.
3. `ChildResult` records verification/acceptance state for delegated outputs.
4. Completion without verification is allowed; acceptance without explicit criteria is not recommended.

---

# D. Parent/child linkage rules

1. Every `ChildTask` must point to exactly one `parent_run_id`.
2. Every `ChildResult` must point to exactly one `child_task_id` and one `child_run_id`.
3. Parent should consume child outputs by artifact refs and summary, not by replaying raw child history.
4. Parent must not mark a child output accepted without at least checking required evidence/verification fields.

---

# E. Handoff / resume rules

1. Resume should prefer a new run linked by `resume_from_run_id`, not mutation of old terminal state.
2. Handoff requires explicit `handoff` artifact(s), not implied “see previous chat.”
3. Any waiting or blocked state intended for future continuation should write at least one handoff artifact.
4. `TaskBrief + TopicContext + artifact refs` should be sufficient to restart non-trivial work.

---

## Layer 4 — Implementation-facing summary

## Implement first
1. `TaskBrief`
2. `TopicContext`
3. `RunState`
4. typed `ArtifactRef`
5. status enums + transition validation
6. verification-status enums

## Defer safely
1. richer resource usage tracking
2. advanced review metadata
3. complex child model profiling
4. non-essential topic archival metadata

## Mandatory for strict v1
- typed artifact refs
- explicit waiting states
- explicit stop reason
- delivery target persisted explicitly
- acceptance criteria ref on `TaskBrief`
- verification status on `RunState` and `ChildResult`
- explicit parent/child IDs for delegation
- topic context ref on task and run

## Safe to add later
- richer notes fields
- analytics/resource metrics
- secondary convenience indexes
- broader optional policy metadata

---

## Normative section

### Required enums

#### `RunState.status`
- `pending`
- `running`
- `waiting_user`
- `waiting_external`
- `blocked`
- `completed`
- `failed`
- `cancelled`

#### `RunState.verification_status`
- `not_required`
- `pending_verification`
- `verified`
- `verification_failed`
- `accepted`
- `rejected`

#### `ChildResult.status`
- `completed`
- `blocked`
- `failed`
- `cancelled`

#### `ChildResult.verification_status`
- `pending_verification`
- `verified`
- `verification_failed`
- `accepted`
- `rejected`

#### `TopicContext.routing_mode`
- `trigger_only`
- `ambient_observe`
- `mixed`

#### `ArtifactRef.kind`
- `input`
- `working`
- `final`
- `evidence`
- `handoff`
- `verification`

### Required state transition rules
1. A run must start as `pending` or `running`.
2. A terminal run (`completed`, `failed`, `cancelled`) must not return to `running`.
3. A resumed execution should create a new run or explicit resume lineage, not silently reactivate a terminal one.
4. `waiting_user` and `waiting_external` require a `waiting_reason` or equivalent explicit cause.
5. `blocked` requires an explicit explanation of why no next step exists.
6. `completed` should still allow `verification_status` to remain below `accepted`.
7. Child completion must not imply parent acceptance.

### Fields that must never be inferred from chat history alone
- `task_id`
- `run_id`
- `status`
- `stop_reason`
- `delivery_target`
- `allowed_tools`
- `done_criteria`
- `acceptance_criteria_ref`
- `topic_context_ref`
- `parent_run_id`
- `child_task_id`
- `verification_status`
- typed artifact refs

### Fields that must always be persisted explicitly
- `task_brief_ref`
- `topic_context_ref`
- `delivery_target`
- `max_steps`
- `step_count`
- `status`
- `stop_reason` when terminal
- typed artifact refs by class
- `acceptance_criteria_ref`
- `verification_status`
- `parent_run_id` / `child_task_id` linkage when delegation exists
- `completed_at` for terminal child results

---

## Final note

Compared to the base draft, this version is stricter in four practical ways:
- artifacts are typed,
- waiting is separated from blocked,
- acceptance is separated from completion,
- lifecycle/state persistence rules are normative instead of descriptive.