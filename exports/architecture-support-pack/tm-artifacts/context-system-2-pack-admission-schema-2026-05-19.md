# Context System 2 — pack admission schema

Date: 2026-05-19
Status: draft-for-execution
Parent task: #531
Task: CS2-A3

Purpose: define the machine-facing schema for CS2 packs so packs become explicit admission objects with bounded runtime meaning, instead of loose files that may or may not leak into startup.

---

## 1. Schema purpose

A pack is a bounded context object that may be admitted into runtime context only according to explicit policy.

A pack is not just a file group.
A pack must declare:
- what it is for;
- which surface may use it;
- how it may be admitted;
- how fresh it must be;
- whether it is continuation-local or durable;
- what budget it may consume;
- why it may load or must be suppressed.

Without explicit admission metadata, a pack must not be loaded ambiently.

---

## 2. Admission classes

Every pack must declare exactly one primary `admission_class`.

Allowed values:
- `always_on`
- `conditional`
- `on_demand`
- `archive_only`
- `ambient_forbidden`

### Meaning

#### `always_on`
May load ambiently for the owning surface if referenced by that surface manifest.

#### `conditional`
May load only when the surface manifest and request/state conditions match.

#### `on_demand`
May never load ambiently by default. May load only through explicit retrieval/admission.

#### `archive_only`
Kept only as deep history / source material. Not eligible for ambient or normal conditional load.

#### `ambient_forbidden`
Must be actively suppressed from ambient loading for the relevant surface(s).

### Non-overlap rule
A single pack cannot simultaneously be `always_on` and `on_demand`, or any other combination. If the system needs two behaviors, it must define two different packs.

---

## 3. Required top-level fields

Each pack must define:
- `pack_id`
- `version`
- `status`
- `owner_surface`
- `purpose`
- `admission_class`
- `request_classes`
- `freshness_class`
- `continuation_scope`
- `durability_class`
- `source_kind`
- `source_refs`
- `budget`
- `admission_policy`
- `trace_policy`

Optional:
- `notes`
- `open_questions`
- `synthesis_rule`
- `refresh_rule`

---

## 4. Field definitions

## 4.1 Identity and lifecycle

### `pack_id`
String, required.
Stable pack identifier.

Examples:
- `strategist.current_control`
- `architect.current_state`
- `learning.mode_rules`
- `task.bootstrap_packet`
- `main.local_continuation`

### `version`
String, required.
Example: `cs2-v1`.

### `status`
Enum, required.
Allowed:
- `draft`
- `active`
- `deprecated`

### `owner_surface`
String, required.
Primary owning surface.

Allowed initial values:
- `main`
- `strategist`
- `architect`
- `learning`
- `task_scoped_execution`
- `shared`

### `purpose`
String, required.
One compact explanation of what this pack contributes.

---

## 4.2 Admission and request fit

### `admission_class`
Enum, required.
One of the five admission classes defined above.

### `request_classes`
Array of strings, required.
Declares which request classes may legitimately use this pack.

Examples:
- `business_strategy`
- `offer_design`
- `content_planning`
- `architecture_design_recall`
- `current_task_execution`
- `factual_lookup`

Rules:
- empty array is allowed only for `archive_only` or `ambient_forbidden`
- if request classes are broad, the pack should usually not be `always_on`

### `admission_policy`
Object, required.
Declares how admission is decided.

Required fields:
- `requires_surface_manifest_reference` — boolean
- `requires_request_class_match` — boolean
- `requires_freshness_check` — boolean
- `requires_task_link` — boolean
- `requires_current_branch` — boolean
- `fallback_behavior` — enum:
  - `skip`
  - `retrieve_on_demand`
  - `spawn_fresh`

Meaning:
This is the pack-level side of admission. The surface manifest decides whether the class is admissible; the pack decides what conditions it itself requires.

---

## 4.3 Freshness and durability

### `freshness_class`
Enum, required.
Allowed:
- `static`
- `slow_moving`
- `current_required`
- `ephemeral`

Meaning:
- `static` — almost never needs regeneration
- `slow_moving` — can be reused for a while
- `current_required` — should reflect current state
- `ephemeral` — short-lived branch/task state only

### `continuation_scope`
Enum, required.
Allowed:
- `none`
- `current_branch_only`
- `current_task_only`
- `surface_local_only`
- `shared_safe`

Meaning:
Defines how far this pack may travel ambiently across sessions or branches.

### `durability_class`
Enum, required.
Allowed:
- `generated_summary`
- `curated_capsule`
- `task_bootstrap`
- `retrieval_backed`
- `archive_record`

---

## 4.4 Source description

### `source_kind`
Enum, required.
Allowed:
- `single_file`
- `file_group`
- `generated_capsule`
- `task_manager_state`
- `retrieval_query`
- `mixed`

### `source_refs`
Array, required.
References the underlying sources from which the pack is built or loaded.

Each entry must include:
- `kind` — enum:
  - `path`
  - `task_id`
  - `artifact`
  - `memory_source`
  - `query`
- `value` — string
- `required` — boolean

Rule:
A pack may be generated from multiple sources, but the set must be explicit.

---

## 4.5 Budget and size

### `budget`
Object, required.
Defines the pack’s token budget contract.

Required fields:
- `target_tokens` — integer
- `hard_cap_tokens` — integer
- `trim_strategy` — enum:
  - `strict_truncate`
  - `summarize_then_trim`
  - `fail_admission`

Rules:
- `hard_cap_tokens >= target_tokens`
- if a pack cannot fit under hard cap, admission must fail or fall back according to policy

---

## 4.6 Trace policy

### `trace_policy`
Object, required.
Defines the reason-code vocabulary and trace expectations for this pack.

Required fields:
- `load_reasons` — array
- `skip_reasons` — array
- `suppress_reasons` — array
- `freshness_failure_reason` — string

Minimum baseline reasons:

`load_reasons`:
- `surface_manifest_reference`
- `request_class_match`
- `task_linked_required`
- `current_branch_required`
- `explicit_on_demand_request`

`skip_reasons`:
- `surface_not_admissible`
- `request_class_mismatch`
- `task_link_missing`
- `condition_not_met`
- `budget_trimmed_out`

`suppress_reasons`:
- `ambient_forbidden_class`
- `history_suppressed`
- `cross_surface_blocked`
- `cross_topic_blocked`

---

## 5. Optional operational fields

### `synthesis_rule`
Optional object.
Use when the pack is generated from larger sources.

Suggested fields:
- `mode` — `extract` | `summarize` | `distill`
- `max_source_tokens`
- `refresh_trigger`

### `refresh_rule`
Optional object.
Use when freshness matters.

Suggested fields:
- `refresh_mode` — `manual` | `on_access` | `periodic`
- `max_age_hours`
- `staleness_behavior` — `warn` | `block` | `regenerate`

---

## 6. Reference JSON shape

```json
{
  "pack_id": "strategist.current_control",
  "version": "cs2-v1",
  "status": "draft",
  "owner_surface": "strategist",
  "purpose": "Compact current strategist control state for active planning/approval work.",
  "admission_class": "conditional",
  "request_classes": ["business_strategy", "content_planning", "publish_logic"],
  "freshness_class": "current_required",
  "continuation_scope": "surface_local_only",
  "durability_class": "generated_summary",
  "source_kind": "mixed",
  "source_refs": [
    {"kind": "artifact", "value": "task-manager/artifacts/...", "required": true}
  ],
  "budget": {
    "target_tokens": 800,
    "hard_cap_tokens": 1200,
    "trim_strategy": "summarize_then_trim"
  },
  "admission_policy": {
    "requires_surface_manifest_reference": true,
    "requires_request_class_match": true,
    "requires_freshness_check": true,
    "requires_task_link": false,
    "requires_current_branch": false,
    "fallback_behavior": "retrieve_on_demand"
  },
  "trace_policy": {
    "load_reasons": [],
    "skip_reasons": [],
    "suppress_reasons": [],
    "freshness_failure_reason": "stale_current_control_pack"
  }
}
```

---

## 7. Initial pack patterns for CS2

### Pattern A — core runtime capsule
Typical class:
- `always_on`

Typical traits:
- small
- static or slow_moving
- shared_safe or owner-surface-local

### Pattern B — current-control pack
Typical class:
- `conditional`

Typical traits:
- current_required
- compact
- generated summary
- strong freshness rules

### Pattern C — task bootstrap packet
Typical class:
- `conditional` or `always_on` within `task_scoped_execution`

Typical traits:
- current_task_only
- task-linked required
- artifact-handoff friendly

### Pattern D — historical evidence pack
Typical class:
- `on_demand` or `archive_only`

Typical traits:
- not ambient
- retrieval-backed or archive record

### Pattern E — forbidden broad history pack
Typical class:
- `ambient_forbidden`

Typical traits:
- old transcript tail
- broad topic history
- mixed generic memory residue

---

## 8. Validation checklist

- [ ] admission classes are explicit and non-overlapping
- [ ] required metadata for admission decisions is defined
- [ ] budget/freshness/source metadata are explicit
- [ ] schema is concrete enough for runtime assembly work
- [ ] schema aligns with the CS2 surface manifest schema and target design

---

## 9. Recommended next step

Use this schema immediately to:
1. create first compact packs/current-control summaries,
2. create first surface manifests that reference those packs,
3. feed runtime binding work in CS2-C1.
