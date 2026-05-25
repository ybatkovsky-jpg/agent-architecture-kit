# Task #468 — First runtime/bootstrap capsules and wiring proposal for new isolated agents — 2026-05-14

## Purpose

Using the prior audit artifact and bootstrap-contract proposal as inputs, this artifact defines the **first practical capsule set** and **bootstrap wiring flow** for newly spawned isolated agents.

This is intentionally:
- **generic where possible**;
- **isolated-agent-first in rollout order**;
- explicit about **what is generated vs manually maintained**;
- explicit about **trace and metadata surfaces** needed to make startup explainable and debuggable.

This is a proposal/spec artifact, not a claim that the runtime already implements the structures below.

---

## Inputs

Primary source artifacts:
- `task-manager/artifacts/task-468-isolated-startup-bootstrap-audit-2026-05-14.md`
- `task-manager/artifacts/task-468-isolated-bootstrap-contract-and-bootstrap-index-proposal-2026-05-14.md`

Observed baseline from those inputs:
- current isolated startup already carries strong execution/task framing;
- startup-file boundaries are ambiguous;
- fixed bootstrap cost is too large;
- retrieval domains are not yet surfaced as a first-class manifest/trace contract.

---

## 1) First capsule set

The first capsule set should be small, composable, and independently testable. A capsule is a **bounded structured payload** with a clear owner, schema, and loading rule.

## Capsule 1 — `runtime_contract`

### Role
Minimum safe-execution contract for the spawned run.

### Load rule
Always loaded in startup.

### Schema / fields
```yaml
runtime_contract:
  schema_version: 1
  run_kind: isolated_agent | subagent | task_scoped_run
  scope_classification: shared_safe | main_private | operator_private
  safety_profile: default_runtime
  workdir: string
  runtime:
    agent: string
    host: string
    repo: string
    os: string
    node_version: string
    shell: string
    model: string
    channel: string
    capabilities: string[]
    thinking_mode: string
  clock:
    now_utc: string
    timezone: string
  tool_surface:
    source: runtime
    available_tools: string[]
    tool_policy_summary: string
```

### Notes
This capsule carries only execution facts and minimal policy summary, not long prose copies of every tool rule if a shorter canonical surface exists.

---

## Capsule 2 — `task_envelope`

### Role
Exact bounded assignment for the isolated run.

### Load rule
Always loaded in startup.

### Schema / fields
```yaml
task_envelope:
  schema_version: 1
  task:
    id: integer | null
    title: string | null
    label: string | null
    brief: string
    success_requirements: string[]
    output_contract:
      expected_artifacts: string[]
      expected_note_updates: string[]
      completion_style: string
  delegation:
    requester_session: string
    requester_channel: string
    parent_session_id: string | null
    depth: integer
    source_message_excerpt: string
  session:
    id: string
    label: string
```

### Notes
This should be the most important startup capsule and should remain human-legible.

---

## Capsule 3 — `startup_context_manifest`

### Role
Make startup loading explicit and remove ambiguity about what was injected vs withheld.

### Load rule
Always loaded in startup.

### Schema / fields
```yaml
startup_context_manifest:
  schema_version: 1
  startup_files_loaded:
    - path: string
      capsule_id: string
      mode: full | summary | synthetic
      reason: string
  startup_files_excluded:
    - path: string
      reason: string
      exclusion_policy: privacy | size | scope | not_needed_by_default
  startup_files_available_on_demand:
    - path: string
      domain: string
      scope: string
  startup_sections_loaded:
    - string
  startup_sections_suppressed:
    - string
```

### Notes
This is the clearest direct answer to the ambiguity found in the audit.

---

## Capsule 4 — `bootstrap_index_ref`

### Role
Pointer to the richer routing/index contract without inlining its full contents.

### Load rule
Always loaded in startup, but only as a compact reference plus summary.

### Schema / fields
```yaml
bootstrap_index_ref:
  schema_version: 1
  index_version: 1
  index_path: string
  profile: string
  available_domains:
    - name: string
      default_load: never | conditional | always
      scope: string
      triggers: string[]
  fetch_policy_summary:
    memory_md_default: excluded
    daily_memory_default: excluded
    deep_artifacts_default: excluded
    full_skill_catalog_default: excluded
```

### Notes
This prevents the startup prompt from carrying the full domain map while still making the retrieval contract explicit.

---

## Capsule 5 — `identity_capsule_min`

### Role
Optional minimal assistant/user framing needed for behavior continuity.

### Load rule
Conditional. Load only when the runtime/profile says isolated runs still need a shared-safe identity summary.

### Schema / fields
```yaml
identity_capsule_min:
  schema_version: 1
  assistant_identity_summary: string
  user_style_summary: string | null
  privacy_rule_summary: string
  source_files:
    - path: string
      mode: summary
```

### Notes
This capsule exists to replace loading full `SOUL.md`/`USER.md`/`IDENTITY.md` into every isolated run.

---

## Capsule 6 — `skill_routing_capsule_min`

### Role
Allow skill selection without paying the full prompt cost of the entire skill catalog.

### Load rule
Conditional. Prefer matched-skill-only; otherwise compact skill trigger index.

### Schema / fields
```yaml
skill_routing_capsule_min:
  schema_version: 1
  routing_mode: matched_skill_only | compact_index
  matched_skill:
    name: string | null
    path: string | null
    why_matched: string | null
  compact_index:
    - name: string
      trigger_summary: string
      path: string
```

### Notes
For the first rollout, a compact index is acceptable; later optimization can move to matched-skill-only injection.

---

## Capsule 7 — `bootstrap_trace_seed`

### Role
Initialize traceability for everything loaded after startup.

### Load rule
Always loaded in startup, but starts nearly empty.

### Schema / fields
```yaml
bootstrap_trace_seed:
  schema_version: 1
  trace_id: string
  startup_trace:
    startup_bytes_estimate: integer | null
    startup_token_estimate: integer | null
    startup_capsules:
      - string
  fetch_trace:
    domain_fetches: []
    suppressed_fetches: []
    warnings: []
```

### Notes
This gives the runtime a stable place to append context-loading decisions.

---

## First capsule set summary

### Required in first isolated rollout
1. `runtime_contract`
2. `task_envelope`
3. `startup_context_manifest`
4. `bootstrap_index_ref`
5. `bootstrap_trace_seed`

### Optional in first isolated rollout
6. `identity_capsule_min`
7. `skill_routing_capsule_min`

This order keeps the first slice practical without waiting for full identity/skill routing redesign.

---

## 2) What is generated vs maintained manually

## Generated at spawn/build time
These should be generated because they are dynamic, environment-derived, or task-specific:
- `runtime_contract.runtime.*`
- `runtime_contract.clock.*`
- `task_envelope.delegation.*`
- `task_envelope.session.*`
- `task_envelope.task.brief`
- `task_envelope.task.success_requirements` when sourced from delegation
- `startup_context_manifest.startup_files_loaded`
- `startup_context_manifest.startup_files_excluded`
- `startup_context_manifest.startup_sections_loaded`
- `bootstrap_index_ref.index_version`
- `bootstrap_index_ref.index_path`
- `bootstrap_trace_seed.trace_id`
- `bootstrap_trace_seed.startup_trace.*`
- fetch trace records such as `domain_fetches`

## Generated from source files via summarization/synthesis
These should be generated as compact capsules from larger sources:
- `identity_capsule_min.assistant_identity_summary`
- `identity_capsule_min.user_style_summary`
- `identity_capsule_min.privacy_rule_summary`
- `skill_routing_capsule_min.compact_index`
- `skill_routing_capsule_min.matched_skill`
- any `AGENTS_MIN_CAPSULE`-style summary content

## Maintained manually in repo/workspace
These are policy/config artifacts humans should maintain deliberately:
- root source files like `AGENTS.md`, `SOUL.md`, `USER.md`, `IDENTITY.md`, `TOOLS.md`
- task artifacts and handoffs
- any static bootstrap policy fragments
- the logical domain definitions and trigger vocabulary for `BOOTSTRAP_INDEX.yaml`
- rollout acceptance thresholds once chosen

## Generated or partially generated manifests with manual source of truth
These are best treated as hybrid:
- `BOOTSTRAP_INDEX.yaml`
  - manually maintained for domain definitions, scope rules, trigger families, and exclusions;
  - generated or normalized for compiled summaries, version stamping, and path resolution.

## Recommended ownership split
- **Manual**: policy, domain catalog, source-file content, scope rules.
- **Generated**: per-run payloads, summaries, lineages, traces, loaded/excluded lists.

---

## 3) Bootstrap builder flow

The builder flow should be explicit, deterministic, and observable.

## Phase 0 — classify run
Inputs:
- run kind;
- parent/main/session context;
- task delegation payload;
- privacy/scope classification.

Outputs:
- `run_kind`
- `scope_classification`
- bootstrap profile selection, initially `isolated_agent_bootstrap`

## Phase 1 — assemble mandatory runtime/task capsules
Build:
1. `runtime_contract`
2. `task_envelope`

Rule:
- these are assembled before any optional file-derived context.

## Phase 2 — apply startup inclusion policy
Consult bootstrap profile and exclusions.

Decide:
- which startup files, if any, are loaded as summaries;
- which are excluded by default;
- whether identity and skill capsules are needed.

Build:
3. `startup_context_manifest`
4. optional `identity_capsule_min`
5. optional `skill_routing_capsule_min`

## Phase 3 — attach retrieval/index reference
Resolve the active bootstrap index contract.

Build:
6. `bootstrap_index_ref`

Rule:
- include summary only, not full deep index content.

## Phase 4 — seed trace metadata
Build:
7. `bootstrap_trace_seed`

Rule:
- startup trace exists even if no later fetches occur.

## Phase 5 — emit normalized startup package
Produce a normalized startup package whose sections map directly to capsule ids.

Example ordering:
1. runtime/tool/safety contract
2. task envelope
3. startup context manifest
4. bootstrap index reference
5. optional identity capsule
6. optional skill routing capsule
7. trace seed

## Phase 6 — on-demand fetch loop during execution
When the run later needs more context:
1. identify domain trigger;
2. check `BOOTSTRAP_INDEX.yaml` for domain and scope rule;
3. load the smallest sufficient source;
4. append trace entry;
5. surface fetched context to the run.

## Phase 7 — completion/debug artifacting
At completion or failure, retain enough metadata to reconstruct:
- what was present at startup;
- what was fetched later;
- what was blocked or excluded.

This can be emitted as runtime metadata, sidecar logs, or optional audit artifact.

---

## 4) Trace / metadata fields

The following fields should become first-class metadata, not buried in prose.

## Startup trace fields
```yaml
startup_trace:
  startup_profile: string
  startup_capsules:
    - string
  startup_files_loaded:
    - path: string
      capsule_id: string
      mode: full | summary | synthetic
      bytes: integer | null
      reason: string
  startup_files_excluded:
    - path: string
      exclusion_policy: privacy | size | scope | default_exclusion
      reason: string
  startup_files_available_on_demand:
    - path: string
      domain: string
      scope: string
  startup_sections_loaded:
    - string
  startup_sections_suppressed:
    - string
  startup_bytes_estimate: integer | null
  startup_token_estimate: integer | null
```

## Fetch trace fields
```yaml
fetch_trace:
  domain_fetches:
    - domain: string
      source_kind: file | file_glob | generated_summary | task_manager | memory
      source_path: string
      trigger: string
      reason: string
      scope_check: allowed | denied | escalated
      loaded_at: string
      bytes: integer | null
      token_estimate: integer | null
      result_mode: full | excerpt | summary | synthetic
  suppressed_fetches:
    - domain: string
      source_path: string
      trigger: string
      denied_by: string
      reason: string
      observed_at: string
  warnings:
    - code: string
      message: string
```

## Completion trace fields
```yaml
completion_trace:
  completion_status: success | blocked | failed
  artifact_paths:
    - string
  note_paths:
    - string
  strongest_next_step: string | null
```

## Minimum required first-slice fields
If the first implementation must stay narrow, require at least:
- `startup_files_loaded`
- `startup_files_excluded`
- `startup_files_available_on_demand`
- `domain_fetches`
- `scope_classification`
- `startup_profile`

Those fields alone would already solve most of the observed explainability gap.

---

## 5) Rollout order

Rollout should preserve isolated-agent-first practicality.

## Rollout 1 — explicit startup manifest for isolated runs
Implement only:
- `runtime_contract`
- `task_envelope`
- `startup_context_manifest`
- `bootstrap_trace_seed` minimum fields

Goal:
- remove ambiguity around what was loaded/excluded.

Success test:
- every isolated run can say exactly which startup files were loaded, excluded, or available on demand.

## Rollout 2 — bootstrap index reference and domain tracing
Implement:
- `bootstrap_index_ref`
- `domain_fetches`
- scope checks for domain loads

Goal:
- separate startup from retrieval contract.

Success test:
- post-startup context loads are attributable to named domains and reasons.

## Rollout 3 — compact identity capsule
Implement:
- `identity_capsule_min`
- summary generation from source identity/user files

Goal:
- stop loading broad persona/user files into isolated runs by default.

Success test:
- behavior continuity preserved while startup size drops.

## Rollout 4 — compact skill routing capsule
Implement:
- `skill_routing_capsule_min`
- compact index or matched-skill-only injection

Goal:
- replace full skill catalog in isolated startup.

Success test:
- skill selection still works without large catalog injection.

## Rollout 5 — generalized bootstrap profiles beyond isolated agents
Extend the same capsule model to:
- main session;
- private operator sessions;
- possibly shared topic sessions.

Goal:
- unify bootstrap composition behind profile-specific policies.

---

## 6) Open risks

## Risk 1 — summary drift
Synthetic capsules such as `identity_capsule_min` may drift from their source files.

Mitigation:
- include source file references and regeneration rules;
- treat summaries as generated, not hand-edited truth.

## Risk 2 — hidden coupling to full skill catalog
Current skill-selection behavior may depend on full inline catalog presence.

Mitigation:
- ship compact index first;
- verify skill-selection parity before moving to matched-skill-only injection.

## Risk 3 — builder ownership ambiguity
It is still unclear which exact component owns isolated startup composition.

Mitigation:
- land the capsule contract first, then map each capsule to the owning builder step/component.

## Risk 4 — too much genericity, not enough immediate practicality
A fully generalized capsule system could delay the first useful isolated-run improvement.

Mitigation:
- keep Rollout 1 narrow: loaded/excluded manifest + trace seed only.

## Risk 5 — trace metadata becomes another source of prompt bloat
If traces are inlined too verbosely, they can reintroduce startup cost.

Mitigation:
- keep startup trace minimal;
- store richer trace out of band or append only after fetches.

## Risk 6 — unclear threshold for “small enough” startup
The prior artifacts identified bloat but did not fix numeric thresholds.

Mitigation:
- begin with structural acceptance first;
- add bytes/tokens thresholds after observing a few runs.

## Risk 7 — privacy/scope leaks through incorrect domain mapping
A bad domain rule could expose `MEMORY.md` or daily memory in shared-safe isolated runs.

Mitigation:
- make `MEMORY.md` and daily memory excluded by default for isolated/shared profiles;
- require explicit scope checks for exceptions.

## Risk 8 — generated loaded/excluded lists may not match real runtime composition
If generated manifests are not sourced from the actual builder decisions, the trace becomes misleading.

Mitigation:
- emit metadata from the builder’s actual inclusion/exclusion decisions, not from a post-hoc guesser.

---

## Strongest next implementation step

Implement **Rollout 1** now:

> Add first-class startup metadata emission for isolated runs with `startup_files_loaded`, `startup_files_excluded`, `startup_files_available_on_demand`, `scope_classification`, and `startup_profile`, using the capsule model above even if only four core capsules are initially materialized.

Why this is strongest:
- it directly closes the biggest ambiguity found in the audit;
- it does not require full bootstrap-index generalization first;
- it creates the foundation for later domain tracing and prompt-thinning work.

---

## Bottom line

The first practical capsule architecture for new isolated agents should start with a small mandatory set centered on:
- runtime contract,
- task envelope,
- explicit startup context manifest,
- bootstrap trace seed,
- and a thin bootstrap index reference.

That sequence preserves isolated-agent practicality, makes startup explainable, and provides a clean path from prompt-heavy startup toward selective, traceable on-demand retrieval.
