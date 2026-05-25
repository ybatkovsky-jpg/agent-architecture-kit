# Task #468 — Isolated bootstrap contract and `BOOTSTRAP_INDEX.yaml` proposal — 2026-05-14

## Purpose

Define a concrete **isolated-agent-first bootstrap contract** for newly spawned isolated runs, using the observed startup audit in `task-manager/artifacts/task-468-isolated-startup-bootstrap-audit-2026-05-14.md` as the evidence baseline.

This artifact distinguishes clearly between:
- **Observed current behavior** — what the audit directly or indirectly evidenced in the current isolated run;
- **Proposal** — what the new isolated bootstrap contract should become.

This is a design/spec artifact, not a claim that the runtime already implements the contract below.

---

## 1) Evidence baseline from current observed startup

### Observed current behavior
From the audit artifact, a fresh isolated run currently receives, at minimum:
- system/developer/runtime instructions;
- tool inventories and tool-use rules;
- inline available-skills catalog;
- workspace/runtime metadata;
- subagent execution envelope;
- delegated task brief;
- delegated user message.

The audit also found:
- `AGENTS.md`/`SOUL.md`/`USER.md` may be injected or consulted upstream, but their inclusion was **not fully visible in-body** in this run;
- `MEMORY.md` was **not observed** in isolated startup and is likely excluded by policy for shared/isolated contexts;
- the startup heading `Workspace Files (injected)` was visible, but the concrete injected file set was ambiguous in this run.

### Observed risk drivers
- large fixed bootstrap cost before task-specific work starts;
- ambiguous startup-file loading contract;
- no explicit separation between default startup and fetch-on-demand sources;
- risk of broad context leakage into isolated runs that only need a narrow task capsule.

---

## 2) Proposed isolated bootstrap contract

## Contract objective
A **new isolated agent** should start with only the minimum context required to:
1. understand its exact assignment;
2. know its execution constraints and available tools;
3. know which context sources are available;
4. fetch additional context selectively and traceably.

## Contract shape
The isolated bootstrap contract should be split into two layers:

1. **Startup payload (kept in prompt at launch)**
   - small, explicit, bounded, mostly static plus run-identity fields.

2. **Routing manifest (`BOOTSTRAP_INDEX.yaml`)**
   - machine-readable map of what other context exists, when it is allowed, and how it should be fetched.

Everything not required for safe first action should move out of launch payload and into manifest-addressable retrieval.

---

## 3) Explicit keep-in-startup set

Below is the proposed **keep-in-startup** set for isolated runs.

## A. Core execution contract
Keep:
- system/developer safety and tool-usage constraints;
- OpenClaw runtime/tool availability block;
- isolated/subagent role rules;
- workdir and basic runtime identity (`repo`, `os`, `shell`, `channel`);
- current date/time/timezone if already supplied by runtime.

Why keep:
- agent cannot act safely or correctly without them;
- these govern tool use, privacy, and execution shape.

Observed status:
- **already observed in startup**.

## B. Exact task envelope
Keep:
- task id/title if known;
- delegated task statement;
- success/output requirements;
- requester session/channel identifiers when needed for routing/reporting;
- session label/id for lineage.

Why keep:
- isolated runs exist to perform a bounded task;
- this is the main reason the run exists.

Observed status:
- **already observed in startup**.

## C. Minimal startup file-load declaration
Keep:
- a short machine-readable declaration of what startup files were loaded vs not loaded.

Proposed fields:
- `startup_files_loaded`
- `startup_files_excluded`
- `startup_files_available_on_demand`

Why keep:
- removes current ambiguity seen in the audit;
- prevents duplicate reads and false assumptions.

Observed status:
- **not present as explicit structured declaration today**; proposal only.

## D. Minimal identity/profile capsule
Keep only a very short capsule if required for general behavior:
- assistant identity/tone summary;
- user-preference summary only if scope-safe and needed;
- group/shared-context privacy rule.

Why keep:
- some behavior framing may be needed;
- full persona/user files are too large for every isolated run.

Observed status:
- **behavioral framing likely present indirectly**, but exact injected form is uncertain.

## E. Compact skills routing surface
Keep one of the following, not the full skill catalog:
- matched skill path only; or
- compact skill index with name + one-line trigger.

Why keep:
- preserves skill-selection ability without paying full catalog cost.

Observed status:
- current startup injects the **full** available-skills catalog.
- Proposal: replace with a thinner routing surface.

---

## 4) Explicit fetch-on-demand set

The following should be excluded from default isolated startup and fetched only when relevant.

## A. Large workspace files and policy prose
Fetch on demand:
- full `AGENTS.md` when startup summary is insufficient;
- full `SOUL.md`, `USER.md`, `IDENTITY.md`, `TOOLS.md`;
- `HEARTBEAT.md` unless heartbeat-specific task.

Reason:
- these are useful references but not required for most bounded isolated tasks.

## B. Long-term and daily memory
Fetch on demand:
- `MEMORY.md`;
- `memory/YYYY-MM-DD.md`;
- any daily memory excerpts.

Reason:
- privacy and scope concerns;
- not needed for most mechanical isolated runs;
- matches existing `AGENTS.md` caution.

Observed status:
- `MEMORY.md` not observed in isolated startup; this proposal formalizes that default.

## C. Operational/project context
Fetch on demand:
- active task lists beyond the assigned task;
- active project summaries;
- topic maps;
- architecture summaries;
- current bottleneck summaries;
- decision registers.

Reason:
- often task-dependent;
- should load via domain triggers, not by default.

## D. Deep archive/history
Fetch on demand:
- `task-manager/artifacts/` long-form artifacts;
- `task-manager/handoffs/` chains;
- `docs/` audits and historical notes;
- old conversation excerpts unless not externalized elsewhere.

Reason:
- high token cost;
- best treated as retrieval sources, not bootstrap.

## E. Full skill catalog
Fetch on demand:
- the full `<available_skills>` block or any detailed skill prose beyond the matched skill.

Reason:
- the audit identified this as prompt bloat.

---

## 5) Dynamic runtime fields

These fields are inherently per-run and should remain in startup, but as structured metadata rather than prose when possible.

## Required dynamic fields
- `session.id`
- `session.label`
- `session.depth`
- `session.parent_session_id` when present
- `requester.channel`
- `requester.session`
- `task.id` when known
- `task.title` when known
- `task.source_message_excerpt` or equivalent delegated instruction
- `runtime.agent`
- `runtime.host`
- `runtime.repo`
- `runtime.os`
- `runtime.node_version`
- `runtime.model`
- `runtime.shell`
- `runtime.channel`
- `runtime.capabilities`
- `runtime.thinking_mode`
- `clock.timezone`
- `clock.now_utc`

## Dynamic-but-optional fields
- `runtime.gateway/node binding` if relevant to browser/canvas actions;
- `scope.classification` such as `main_session`, `shared_group`, `isolated_subagent`;
- `privacy_profile` such as `shared-safe`, `operator-private`, `task-only`.

## Proposal rule
Dynamic fields should be:
- included in startup;
- concise;
- structured;
- not mixed with large prose unless explanation is required.

Observed status:
- most of these are currently present, but embedded in human-readable startup blocks rather than an explicit contract object.

---

## 6) Proposed `BOOTSTRAP_INDEX.yaml` schema

This is a proposed machine-readable schema direction, not an existing validated runtime schema.

```yaml
version: 1
profile: isolated_agent_bootstrap
applies_to:
  run_kinds: [isolated_agent, subagent, task_scoped_run]

startup_contract:
  keep_in_startup:
    rules:
      - id: runtime_safety_rules
        required: true
      - id: tool_availability
        required: true
      - id: isolated_role_rules
        required: true
      - id: task_envelope
        required: true
      - id: runtime_metadata_min
        required: true
      - id: startup_file_load_declaration
        required: true
      - id: compact_identity_capsule
        required: false
      - id: compact_skill_index
        required: false

  fetch_on_demand_defaults:
    exclude_from_startup:
      - AGENTS.md
      - SOUL.md
      - USER.md
      - IDENTITY.md
      - TOOLS.md
      - HEARTBEAT.md
      - MEMORY.md
      - memory/*
      - task-manager/artifacts/**
      - task-manager/handoffs/**
      - docs/**
      - full_available_skills_catalog

startup_files:
  loaded: []
  excluded:
    - MEMORY.md
  available_on_demand:
    - AGENTS.md
    - SOUL.md
    - USER.md
    - IDENTITY.md
    - TOOLS.md

runtime_fields:
  required:
    - session.id
    - session.label
    - requester.channel
    - requester.session
    - runtime.repo
    - runtime.os
    - runtime.model
    - runtime.shell
    - runtime.channel
    - clock.now_utc
    - clock.timezone
    - task.brief
  optional:
    - task.id
    - task.title
    - session.parent_session_id
    - runtime.capabilities
    - runtime.thinking_mode
    - scope.classification
    - privacy_profile

context_domains:
  identity:
    source:
      kind: file
      path: AGENTS.md
    default_load: never
    triggers: [identity, behavior, startup_rules]
    scope: safe_shared

  user_profile:
    source:
      kind: file_group
      paths: [USER.md, SOUL.md, IDENTITY.md]
    default_load: conditional
    triggers: [user_preference, tone, personalization]
    scope: scope_filtered

  task_state:
    source:
      kind: task_manager
      path: task-manager/tasks.db
    default_load: conditional
    triggers: [task, next_action, status, dependency]
    scope: safe_shared

  project_runtime:
    source:
      kind: generated_summary
      path: runtime/bootstrap/current-architecture-state.yaml
    default_load: conditional
    triggers: [architecture, project_state, rollout]
    scope: safe_shared

  memory_daily:
    source:
      kind: file_glob
      path: memory/*.md
    default_load: never
    triggers: [recent_history, diary, timeline]
    scope: main_only_or_explicit

  long_term_memory:
    source:
      kind: file
      path: MEMORY.md
    default_load: never
    triggers: [user_history, stable_preferences, prior_decisions]
    scope: main_only_or_explicit

  deep_artifacts:
    source:
      kind: file_glob
      path: task-manager/artifacts/**/*.md
    default_load: never
    triggers: [artifact_lookup, evidence, audit, source_trace]
    scope: safe_shared

acceptance:
  startup_requirements:
    max_startup_sections: 10
    must_include_task_envelope: true
    must_include_loaded_vs_excluded_file_list: true
    must_exclude_memory_md_in_isolated_shared_runs: true
    must_not_inline_deep_artifacts_by_default: true
    must_provide_fetchable_context_domains: true

  traceability_requirements:
    context_fetch_must_record:
      - domain
      - source
      - reason
      - scope_check
      - loaded_at
```

---

## 7) Proposed `BOOTSTRAP_INDEX.yaml` example

Example for a newly spawned isolated task run:

```yaml
version: 1
profile: isolated_agent_bootstrap
applies_to:
  run_kinds: [isolated_agent]

startup_contract:
  keep_in_startup:
    rules:
      - id: runtime_safety_rules
        required: true
      - id: tool_availability
        required: true
      - id: isolated_role_rules
        required: true
      - id: task_envelope
        required: true
      - id: runtime_metadata_min
        required: true
      - id: startup_file_load_declaration
        required: true
      - id: compact_skill_index
        required: true

  fetch_on_demand_defaults:
    exclude_from_startup:
      - MEMORY.md
      - memory/*
      - task-manager/artifacts/**
      - task-manager/handoffs/**
      - docs/**
      - full_available_skills_catalog

startup_files:
  loaded:
    - AGENTS_MIN_CAPSULE
  excluded:
    - MEMORY.md
    - memory/2026-05-14.md
    - task-manager/artifacts/**
  available_on_demand:
    - AGENTS.md
    - USER.md
    - SOUL.md
    - IDENTITY.md
    - TOOLS.md

runtime_fields:
  required:
    session.id: agent:main:subagent:ddbb3a2b-9530-4fc2-a676-d7ceabefcb8f
    session.label: ziribt-2-isolated-bootstrap-contract
    requester.channel: telegram
    requester.session: agent:main:telegram:group:-1003880835934:topic:341
    runtime.repo: /home/openclaw/.openclaw/workspace
    runtime.os: Linux 5.15.0-174-generic (x64)
    runtime.model: openai/cx/gpt-5.4
    runtime.shell: bash
    runtime.channel: telegram
    clock.timezone: UTC
    task.brief: >-
      Define the isolated bootstrap contract and a concrete BOOTSTRAP_INDEX.yaml
      schema/proposal for new isolated agents using the audit artifact.
  optional:
    task.id: 468
    task.title: Apply bootstrap context architecture to new isolated agents
    runtime.capabilities: [inlinebuttons]
    runtime.thinking_mode: low
    scope.classification: isolated_subagent
    privacy_profile: shared-safe

context_domains:
  task_state:
    source:
      kind: task_manager
      path: task-manager/tasks.db
    default_load: conditional
    triggers: [task, next_action, status]
    scope: safe_shared

  deep_artifacts:
    source:
      kind: file_glob
      path: task-manager/artifacts/**/*.md
    default_load: never
    triggers: [artifact_lookup, audit, evidence]
    scope: safe_shared

  long_term_memory:
    source:
      kind: file
      path: MEMORY.md
    default_load: never
    triggers: [user_history, stable_preferences]
    scope: main_only_or_explicit

acceptance:
  startup_requirements:
    must_include_task_envelope: true
    must_include_loaded_vs_excluded_file_list: true
    must_exclude_memory_md_in_isolated_shared_runs: true
    must_not_inline_deep_artifacts_by_default: true
```

---

## 8) Acceptance rules for isolated runs

A new isolated run should be considered compliant with this contract only if all rules below hold.

## A. Startup minimality rules
1. Startup must contain the exact delegated task envelope.
2. Startup must contain safe execution/tool rules.
3. Startup must not inline long-form artifacts by default.
4. Startup must not inline daily memory by default.
5. Startup must not inline `MEMORY.md` in isolated/shared runs.
6. Startup should avoid the full skills catalog unless no thinner routing surface exists.

## B. Explicitness rules
7. Startup must explicitly say which startup files were loaded.
8. Startup must explicitly say which startup files were excluded by policy.
9. Startup must explicitly identify fetch-on-demand domains or sources.

## C. Scope/privacy rules
10. Shared/isolated runs must default to a shared-safe profile.
11. Main-session-only materials must remain excluded unless explicit routing policy allows them.
12. User-history context must require a scope check before load.

## D. Retrieval rules
13. Any extra context beyond startup must be attributable to a named domain/source.
14. Each fetch should be justified by task relevance, not generic availability.
15. Deep history should be loaded only after smaller summaries or direct task sources are insufficient.

## E. Observability rules
16. The bootstrap builder should be able to emit a normalized startup manifest for audit.
17. Context fetches should be traceable by domain, source, reason, and time.
18. A bounded isolated run should be debuggable from its startup manifest plus fetch trace, without replaying the full parent chat.

---

## 9) Strongest next step for capsule design/wiring

## Proposal
The strongest next implementation step is:

**Design and wire a minimal isolated startup capsule plus a generated `BOOTSTRAP_INDEX.yaml`, then make the isolated-run bootstrap builder emit `startup_files_loaded`, `startup_files_excluded`, and domain-fetch trace fields as first-class metadata.**

Why this step is strongest:
- it directly resolves the biggest observed ambiguity from the audit;
- it creates a bridge between the current prompt-heavy startup and future selective retrieval;
- it is implementable without first rewriting main-session startup;
- it gives a measurable acceptance target for isolated runs.

---

## 10) Unresolved assumptions / open questions

These are intentionally marked unresolved.

1. **Whether `AGENTS.md`, `SOUL.md`, and `USER.md` are currently fully injected, summarized, or only consulted upstream**
   - Observed: behavior suggests some effect;
   - Not proven from this isolated run.

2. **Whether the full available-skills catalog is mandatory for current skill-selection logic**
   - Observed: full catalog is present today;
   - Proposal assumes this can be replaced by a thinner skill index or matched-skill injection.

3. **What exact builder component owns isolated startup composition**
   - This artifact defines contract shape, not code ownership.

4. **Whether `BOOTSTRAP_INDEX.yaml` should be workspace-root, runtime-generated, or partially static + partially generated**
   - Proposal favors a generated-or-maintained structured manifest, but final placement/wiring is not proven.

5. **How much compact identity/user context is truly necessary for isolated runs**
   - Proposal keeps this minimal and optional, but exact lower bound should be tested empirically.

6. **Whether acceptance should be measured by sections, bytes, tokens, or all three**
   - The audit motivates prompt thinning, but no numeric threshold is yet proven here.

7. **How context-fetch tracing should surface operationally**
   - Could be prompt metadata, event log, or runtime sidecar; unresolved in this artifact.

---

## Bottom line

Observed current behavior shows a large fixed isolated startup with strong task envelope but ambiguous startup-file boundaries. The concrete proposal here is to formalize isolated startup into:
- a small keep-in-startup contract;
- an explicit fetch-on-demand boundary;
- structured dynamic runtime fields; and
- a machine-readable `BOOTSTRAP_INDEX.yaml` that governs routing, scope, and acceptance.

This artifact is the contract proposal for new isolated agents; it is not evidence that the runtime already enforces it.