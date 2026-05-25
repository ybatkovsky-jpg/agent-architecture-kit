# Context System 2 — surface manifest schema

Date: 2026-05-19
Status: draft-for-execution
Parent task: #531
Task: CS2-A2

Purpose: define the machine-facing schema for CS2 surface contracts/manifests so runtime context assembly can make explicit admission decisions per surface.

---

## 1. Schema purpose

A surface manifest declares the runtime contract for one context surface.

Examples:
- `main`
- `strategist`
- `architect`
- `learning`
- `task_scoped_execution`

The manifest is the canonical source for:
- startup budget rules;
- ambient admission rules;
- conditional admission rules;
- forbidden ambient classes;
- continuation behavior;
- stay-vs-spawn bias;
- output contract.

Without a valid manifest, a surface must not load non-core context ambiently.

---

## 2. Required top-level fields

Each surface manifest must define:

- `surface_id`
- `version`
- `status`
- `purpose`
- `owner_runtime`
- `startup_budget`
- `live_budget_guardrails`
- `always_on_allowlist`
- `conditional_allowlist`
- `on_demand_only`
- `ambient_forbidden`
- `continuation_policy`
- `routing_policy`
- `output_contract`
- `reason_codes`

Optional:
- `notes`
- `open_questions`
- `trace_defaults`

---

## 3. Field definitions

## 3.1 Identity and lifecycle

### `surface_id`
String, required.
Stable identifier.

Allowed initial values:
- `main`
- `strategist`
- `architect`
- `learning`
- `task_scoped_execution`

### `version`
String, required.
Example: `cs2-v1`.

### `status`
Enum, required.
Allowed:
- `draft`
- `active`
- `deprecated`

### `purpose`
String, required.
One compact paragraph explaining what the surface is for.

### `owner_runtime`
String, required.
Must name the OpenClaw-owned runtime seam responsible for applying this manifest.

Examples:
- `openclaw.runtime.main`
- `openclaw.runtime.topic`
- `openclaw.runtime.task_scoped`

---

## 3.2 Budget fields

### `startup_budget`
Object, required.
Defines target startup envelope before conversation tail and tool outputs.

Required fields:
- `target_tokens` — integer
- `hard_cap_tokens` — integer
- `budget_policy` — enum:
  - `strict`
  - `soft_warn`
  - `trim_to_fit`

Rules:
- `hard_cap_tokens >= target_tokens`
- startup assembly must not silently exceed `hard_cap_tokens`

### `live_budget_guardrails`
Object, required.
Defines budget rules after startup.

Required fields:
- `preferred_context_window_tokens` — integer
- `warning_threshold_tokens` — integer
- `spawn_bias_threshold_tokens` — integer
- `history_trim_mode` — enum:
  - `aggressive`
  - `balanced`
  - `minimal`

Meaning:
When the live context approaches the spawn bias threshold, the surface should prefer fresh task-scoped execution over continuing in-place.

---

## 3.3 Admission fields

### `always_on_allowlist`
Array of admission entries, required.
Declares what may always load ambiently for this surface.

Each entry must include:
- `kind` — enum:
  - `core_item`
  - `pack`
  - `continuation_capsule`
  - `task_bootstrap`
- `id` — string
- `max_tokens` — integer
- `required` — boolean
- `admission_reason` — string

Rule:
Anything not listed here cannot be ambient always-on.

### `conditional_allowlist`
Array of conditional admission entries, required.
Declares what may load only when request class / state matches.

Each entry must include:
- `kind`
- `id`
- `when` — object
- `max_tokens`
- `admission_reason`
- `fallback_behavior` — enum:
  - `skip`
  - `spawn_fresh`
  - `retrieve_on_demand`

`when` may include:
- `request_classes`
- `surface_modes`
- `task_presence`
- `branch_state`
- `freshness_required`

### `on_demand_only`
Array, required.
Declares context classes that may never load ambiently, but may be used through explicit retrieval or explicit operator action.

Each entry must include:
- `kind`
- `id_or_class`
- `reason`

### `ambient_forbidden`
Array, required.
Declares what must be suppressed by default.

Each entry must include:
- `kind`
- `id_or_class`
- `reason`
- `suppression_strength` — enum:
  - `hard_forbid`
  - `prefer_suppress`

---

## 3.4 Continuation policy

### `continuation_policy`
Object, required.
Defines what continuation may come along ambiently.

Required fields:
- `ambient_scope` — enum:
  - `none`
  - `current_branch_only`
  - `current_task_only`
  - `surface_local_only`
- `max_continuation_tokens` — integer
- `allow_closed_branch_tail` — boolean
- `allow_cross_topic_tail` — boolean
- `allow_cross_surface_tail` — boolean
- `continuation_capsule_required` — boolean

CS2 default expectation:
- closed branch tail = false
- cross-topic tail = false
- cross-surface tail = false

---

## 3.5 Routing policy

### `routing_policy`
Object, required.
Defines when to stay vs spawn fresh.

Required fields:
- `default_action` — enum:
  - `stay`
  - `spawn_fresh`
- `independent_work_bias` — enum:
  - `low`
  - `medium`
  - `high`
- `multi_step_bias` — enum:
  - `low`
  - `medium`
  - `high`
- `large_read_bias` — enum:
  - `low`
  - `medium`
  - `high`
- `implementation_bias` — enum:
  - `low`
  - `medium`
  - `high`
- `validation_bias` — enum:
  - `low`
  - `medium`
  - `high`
- `spawn_target_surface` — string or null

Meaning:
This field is the surface-level contract behind stay-vs-spawn decisions.

---

## 3.6 Output contract

### `output_contract`
Object, required.
Defines what kind of answer/result this surface should produce.

Required fields:
- `shape` — enum:
  - `concise_summary`
  - `decision_summary`
  - `approval_ready`
  - `task_progress`
  - `explanation`
  - `artifact_handoff`
- `max_default_paragraphs` — integer
- `artifact_expected` — boolean
- `requires_user_decision_only_when_needed` — boolean
- `return_to_main_style` — enum:
  - `short_result`
  - `approval_request`
  - `escalation_only`

---

## 3.7 Reason codes

### `reason_codes`
Object, required.
Defines the reason-code vocabulary this surface expects in traces.

Required arrays:
- `load_reasons`
- `skip_reasons`
- `suppress_reasons`
- `spawn_reasons`

Minimum baseline values:

`load_reasons`:
- `surface_always_on`
- `request_class_match`
- `task_linked_required`
- `current_branch_required`
- `conditional_load_match`

`skip_reasons`:
- `condition_not_met`
- `freshness_mismatch`
- `budget_trimmed`
- `not_needed_for_surface`

`suppress_reasons`:
- `forbidden_ambient_class`
- `history_suppressed`
- `cross_surface_tail_blocked`
- `cross_topic_tail_blocked`

`spawn_reasons`:
- `bounded_independent_work`
- `large_read_required`
- `implementation_required`
- `validation_required`
- `live_budget_pressure`

---

## 4. Reference JSON shape

```json
{
  "surface_id": "main",
  "version": "cs2-v1",
  "status": "draft",
  "purpose": "Dialogue, orchestration, routing, concise summaries.",
  "owner_runtime": "openclaw.runtime.main",
  "startup_budget": {
    "target_tokens": 2500,
    "hard_cap_tokens": 4000,
    "budget_policy": "trim_to_fit"
  },
  "live_budget_guardrails": {
    "preferred_context_window_tokens": 12000,
    "warning_threshold_tokens": 16000,
    "spawn_bias_threshold_tokens": 18000,
    "history_trim_mode": "aggressive"
  },
  "always_on_allowlist": [],
  "conditional_allowlist": [],
  "on_demand_only": [],
  "ambient_forbidden": [],
  "continuation_policy": {
    "ambient_scope": "current_branch_only",
    "max_continuation_tokens": 1200,
    "allow_closed_branch_tail": false,
    "allow_cross_topic_tail": false,
    "allow_cross_surface_tail": false,
    "continuation_capsule_required": true
  },
  "routing_policy": {
    "default_action": "stay",
    "independent_work_bias": "high",
    "multi_step_bias": "high",
    "large_read_bias": "high",
    "implementation_bias": "high",
    "validation_bias": "high",
    "spawn_target_surface": "task_scoped_execution"
  },
  "output_contract": {
    "shape": "concise_summary",
    "max_default_paragraphs": 4,
    "artifact_expected": false,
    "requires_user_decision_only_when_needed": true,
    "return_to_main_style": "short_result"
  },
  "reason_codes": {
    "load_reasons": [],
    "skip_reasons": [],
    "suppress_reasons": [],
    "spawn_reasons": []
  }
}
```

---

## 5. Initial surface-specific expectations

### `main`
- smallest startup budget;
- most aggressive history suppression;
- strongest spawn bias for bounded work.

### `strategist`
- compact business-only always-on;
- no broad business history ambiently;
- approval-ready output bias.

### `architect`
- compact architecture current-state always-on;
- long design history on-demand only.

### `learning`
- compact explanation/teaching mode rules;
- archives loaded only on explicit need.

### `task_scoped_execution`
- task bootstrap required;
- old main tail forbidden;
- artifact-handoff output bias.

---

## 6. Validation checklist

- [ ] schema explicitly covers purpose, budgets, allowlists, forbidden classes, continuation policy, routing policy, and output contract
- [ ] reason-code fields are first-class
- [ ] budget fields are concrete enough for enforcement
- [ ] continuation boundary is explicit
- [ ] schema is concrete enough to generate first manifests and bind runtime admission later

---

## 7. Recommended next step

Use this schema immediately for:
1. `CS2-A3` pack admission schema,
2. `CS2-B1` first manifests,
3. runtime binding plan in `CS2-C1`.
