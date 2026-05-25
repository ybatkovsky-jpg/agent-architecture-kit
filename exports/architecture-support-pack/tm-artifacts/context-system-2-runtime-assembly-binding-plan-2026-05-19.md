# Context System 2 — runtime assembly binding plan

Date: 2026-05-19
Status: draft-for-execution
Parent task: #531
Task: CS2-C1

Purpose: define the first concrete runtime binding seam for CS2 so surface manifests can resolve pack references into real startup context objects without pretending every referenced pack already exists.

---

## 1. Binding objective

CS2 runtime assembly must make one thing true:

> a manifest entry like `strategist.current_control` resolves through a single OpenClaw-owned binding seam into either a materialized pack, a generated/wrapped pack, or an explicit `missing_pack` trace result.

This slice does **not** require perfect pack coverage.
It requires honest, inspectable assembly behavior.

---

## 2. Runtime seam owner

Binding should happen in the OpenClaw runtime assembly seam, not inside lane-specific prompt files.

Current owner shape:
- manifest discovery/loading already bound at runtime seam level;
- CS2-C1 extends that seam with pack resolution and assembly decisions.

Working responsibility split:
1. **manifest loader** — loads the selected surface manifest;
2. **pack resolver** — maps manifest ids to concrete sources or generation rules;
3. **assembly planner** — applies admission conditions, requiredness, and budget trimming;
4. **trace emitter** — records loaded/skipped/generated/missing outcomes.

---

## 3. Required inputs

CS2-C1 binds these artifacts together:
- surface manifests:
  - `task-manager/artifacts/context-system-2-first-surface-manifests-2026-05-19.md`
- pack metadata model:
  - `task-manager/artifacts/context-system-2-pack-admission-schema-2026-05-19.md`
- current pack/source map:
  - `task-manager/artifacts/context-system-2-current-control-pack-map-2026-05-19.md`

The pack map is the initial truth source for whether a referenced pack is:
- `exists_usable`
- `exists_but_needs_cs2_wrap`
- `missing_create_first`

---

## 4. Resolver contract

Each manifest entry with `kind = pack | continuation_capsule | task_bootstrap` must resolve through a normalized resolver result:

```json
{
  "pack_id": "strategist.current_control",
  "resolution_state": "loaded_direct",
  "materialization_mode": "existing_pack",
  "source_ref": "agents/business-strategist-seed/capsules/runtime/strategist-current-control-pack.md",
  "trace_reason": "source_exists_verified",
  "tokens_estimate": 900
}
```

Allowed `resolution_state` values:
- `loaded_direct`
- `loaded_wrapped`
- `loaded_generated`
- `skipped_condition_unmet`
- `skipped_budget_trim`
- `missing_pack`
- `error_invalid_source`

Allowed `materialization_mode` values:
- `existing_pack`
- `wrapped_source`
- `generated_from_refs`
- `none`

---

## 5. Three binding paths

## 5.1 Path A — load existing packs directly

Use when pack-map state is `exists_usable` and the source is already compact enough.

Examples:
- `strategist.core_operating_contract`
- `strategist.current_contour`
- `strategist.current_control`
- `task.bootstrap_packet`

Binding rule:
- read source artifact directly;
- stamp runtime metadata:
  - `pack_id`
  - `surface_id`
  - `materialization_mode = existing_pack`
  - `source_ref`
  - `freshness_class`
  - `admission_class`
- include in assembly if manifest admission allows it and budget fits.

No extra wrapping is required beyond metadata normalization.

## 5.2 Path B — load wrapped packs from known source refs

Use when pack-map state is `exists_but_needs_cs2_wrap`.

Examples:
- `strategist.approved_content_plan_summary`
- `architect.current_state_summary`
- `architect.implementation_mapping`
- `learning.current_roadmap_summary`

Binding rule:
- take the mapped source refs from the pack map;
- construct a small CS2 wrapper object around the extracted content;
- preserve provenance to the original source artifact(s);
- emit `resolution_state = loaded_wrapped`.

Minimum wrapper fields:

```json
{
  "pack_id": "architect.current_state_summary",
  "materialization_mode": "wrapped_source",
  "basis_refs": [
    "task-manager/artifacts/task-217-current-state-architecture-overview-for-yuriy-2026-04-29.md"
  ],
  "generated_at": "runtime",
  "summary_kind": "cs2_wrap"
}
```

Rule:
wrapped loading is valid only when source refs are explicit and bounded.
Do not silently wrap broad history classes or generic transcript tails.

## 5.3 Path C — load generated packs from known refs

Use when the target pack is runtime-oriented and expected to be synthesized from current structured inputs rather than loaded as one static file.

Examples:
- `main.local_current_branch`
- `main.local_decision_context`
- `strategist.local_current_branch`
- `task_scoped.linked_artifact_summary`
- `task_scoped.narrow_recent_excerpt`

Binding rule:
- generation is allowed only when the pack map or manifest names concrete source refs/classes;
- generator input must be narrow and current;
- output must be compact and tagged as derived runtime material;
- emit `resolution_state = loaded_generated`.

Required metadata:
- `basis_refs`
- `generator_kind`
- `freshness_basis`
- `generated_at`
- `source_window_description`

Example:

```json
{
  "pack_id": "main.local_current_branch",
  "resolution_state": "loaded_generated",
  "materialization_mode": "generated_from_refs",
  "basis_refs": [
    "current_branch_summary",
    "active_task_manager_next_action"
  ],
  "generator_kind": "branch_continuation_compactor",
  "freshness_basis": "active_branch_only"
}
```

---

## 6. Missing-pack behavior

If a manifest references a pack that is not materialized and has no approved wrapping/generation path, runtime must not fake success.

It must emit:
- `resolution_state = missing_pack`
- `materialization_mode = none`
- `trace_reason` describing why it is missing
- `referenced_by_surface`
- `required = true|false`

Example trace item:

```json
{
  "pack_id": "architect.core_operating_contract",
  "resolution_state": "missing_pack",
  "materialization_mode": "none",
  "trace_reason": "referenced_in_manifest_but_no_verified_pack_or_wrap_rule",
  "referenced_by_surface": "architect",
  "required": true
}
```

Operational rule:
- if a **required always-on** pack resolves to `missing_pack`, assembly should mark startup as degraded;
- if a **conditional** pack resolves to `missing_pack`, startup may continue but trace/debug must show the miss.

This is the minimum honest behavior needed before full pack completeness exists.

---

## 7. Assembly algorithm

## 7.1 Candidate collection

For the selected surface:
1. load manifest;
2. collect `always_on_allowlist` entries;
3. evaluate `conditional_allowlist` against current request/task/branch state;
4. exclude `on_demand_only` and `ambient_forbidden` classes from ambient assembly.

## 7.2 Resolution pass

For each admitted candidate:
1. look up `pack_id` in the pack map/registry;
2. choose path A, B, or C;
3. build normalized resolver result;
4. attach estimated token cost.

## 7.3 Budget pass

Apply startup budget in this order:
1. required always-on entries;
2. non-required always-on entries;
3. conditional entries by request match strength.

If trimming is needed:
- keep required entries unless invalid/missing;
- drop non-required conditional entries first with `skipped_budget_trim`;
- never replace a missing required pack with broad history fallback.

## 7.4 Final assembly output

Runtime assembly should produce:
- `assembled_items[]` — materialized packs/items actually injected;
- `assembly_trace[]` — per-candidate resolution outcomes;
- `assembly_status`:
  - `ok`
  - `ok_with_missing_optional`
  - `degraded_missing_required`
  - `degraded_invalid_source`

---

## 8. First trace/debug envelope

CS2-C1 should expose a minimal debug shape:

```json
{
  "surface_id": "strategist",
  "assembly_status": "ok",
  "manifest_version": "cs2-v1",
  "assembled_items": [
    {"id": "strategist.core_operating_contract", "resolution_state": "loaded_direct"},
    {"id": "strategist.current_contour", "resolution_state": "loaded_direct"},
    {"id": "strategist.current_control", "resolution_state": "loaded_direct"}
  ],
  "assembly_trace": [
    {"id": "strategist.local_current_branch", "resolution_state": "missing_pack", "trace_reason": "not_materialized_yet"}
  ]
}
```

Minimum operator questions this must answer:
- what surface was assembled?
- which packs loaded directly?
- which packs were wrapped/generated?
- which referenced packs are still missing?
- was startup degraded because of a required miss?

---

## 9. First binding registry

CS2-C1 does not need a full generalized registry yet.
A compact starter registry is enough.

Suggested shape:

```json
{
  "strategist.current_control": {
    "pack_state": "exists_usable",
    "load_mode": "existing_pack",
    "source_ref": "agents/business-strategist-seed/capsules/runtime/strategist-current-control-pack.md"
  },
  "architect.current_state_summary": {
    "pack_state": "exists_but_needs_cs2_wrap",
    "load_mode": "wrapped_source",
    "basis_refs": [
      "task-manager/artifacts/task-217-current-state-architecture-overview-for-yuriy-2026-04-29.md"
    ]
  },
  "main.local_current_branch": {
    "pack_state": "missing_create_first",
    "load_mode": "generated_from_refs",
    "basis_refs": [
      "current_branch_summary",
      "active_task_manager_next_action"
    ]
  }
}
```

Important distinction:
- `missing_create_first` in the pack-map artifact does **not** always mean permanent startup failure;
- if a sanctioned runtime generator exists with narrow refs, the resolver may still materialize the pack through path C;
- otherwise it must surface `missing_pack`.

---

## 10. First rollout order

Bind the safest verified surfaces first:

### Wave 1
- `strategist.current_control`
- `strategist.core_operating_contract`
- `strategist.current_contour`
- `task.bootstrap_packet`

Reason:
these already have the strongest verified existing-pack anchors.

### Wave 2
- wrapped sources:
  - `architect.current_state_summary`
  - `architect.implementation_mapping`
  - `learning.current_roadmap_summary`
  - `strategist.approved_content_plan_summary`

### Wave 3
- generated continuation/runtime packs:
  - `main.local_current_branch`
  - `main.local_decision_context`
  - `strategist.local_current_branch`
  - `task_scoped.linked_artifact_summary`
  - `task_scoped.narrow_recent_excerpt`

### Wave 4
- remaining truly missing required packs that need authoring first.

---

## 11. Non-goals for CS2-C1

CS2-C1 does not need to finish:
- full stay-vs-spawn enforcement;
- advanced freshness scoring;
- full token-accurate budgeting;
- retrieval planner redesign;
- broad historical search integration.

It only needs to make manifest-to-pack binding explicit and inspectable.

---

## 12. Acceptance checklist

- [ ] manifest entries resolve through one runtime pack resolver
- [ ] existing verified packs load directly
- [ ] known source refs can be wrapped into CS2 pack objects
- [ ] approved runtime-generated packs can materialize from narrow refs
- [ ] unresolved references emit `missing_pack` in trace/debug
- [ ] required missing packs degrade startup explicitly instead of silently falling back
- [ ] strategist and task-scoped anchors can be bound first without waiting for full CS2 completion

---

## 13. Recommended immediate next implementation move

Implement a bounded starter registry and resolver in the OpenClaw runtime assembly seam with these first proofs:
1. direct-load `strategist.current_control`;
2. direct-load `task.bootstrap_packet`;
3. wrap one known-source pack such as `architect.current_state_summary`;
4. emit `missing_pack` for one referenced-but-unmaterialized entry such as `architect.core_operating_contract`.

That is enough to prove the CS2 binding seam is real.