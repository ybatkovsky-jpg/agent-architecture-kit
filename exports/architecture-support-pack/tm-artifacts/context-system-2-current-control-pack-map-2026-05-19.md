# Context System 2 — current-control pack map

Date: 2026-05-19
Status: draft-for-execution
Parent task: #531
Task: CS2-B2

Purpose: map the first CS2 manifests to real compact packs/capsules where they already exist, and explicitly identify the missing packs that must be created before runtime binding can be complete.

---

## 1. Mapping rule

This artifact does not pretend every referenced pack already exists.

It separates packs into three states:
- `exists_usable` — already present and close enough to serve as an initial runtime target
- `exists_but_needs_cs2_wrap` — source material exists, but needs explicit CS2 pack metadata or tighter extraction
- `missing_create_first` — no adequate compact pack exists yet and one must be created

The point is to stop runtime binding from depending on vague names.

---

## 2. Surface-by-surface pack map

## 2.1 `main`

### `main.local_current_branch`
- state: `missing_create_first`
- target pack id: `main.local_current_branch`
- intended role: compact branch-local continuation capsule for current main branch only
- likely source refs:
  - current branch-local conversation summary
  - active task-manager next-action state when relevant
- CS2 classification:
  - admission_class: `conditional`
  - freshness_class: `ephemeral`
  - continuation_scope: `current_branch_only`
  - durability_class: `generated_summary`
- note: this is one of the most important missing packs because thin main depends on branch-local continuation instead of chat tail

### `main.local_decision_context`
- state: `missing_create_first`
- target pack id: `main.local_decision_context`
- intended role: compact decision lookup pack for factual/policy decision continuity in main
- likely source refs:
  - active decision summaries
  - task-manager artifacts explicitly linked to current branch
- CS2 classification:
  - admission_class: `conditional`
  - freshness_class: `current_required`
  - continuation_scope: `current_branch_only`
  - durability_class: `generated_summary`

---

## 2.2 `strategist`

### `strategist.core_operating_contract`
- state: `exists_usable`
- source ref:
  - `agents/business-strategist-seed/capsules/runtime/strategist-core-operating-contract.md`
- target pack id: `strategist.core_operating_contract`
- CS2 classification:
  - admission_class: `always_on`
  - freshness_class: `slow_moving`
  - continuation_scope: `surface_local_only`
  - durability_class: `curated_capsule`

### `strategist.current_contour`
- state: `exists_usable`
- source ref:
  - `agents/business-strategist-seed/capsules/bootstrap/strategist-current-contour.md`
- target pack id: `strategist.current_contour`
- CS2 classification:
  - admission_class: `always_on`
  - freshness_class: `slow_moving`
  - continuation_scope: `surface_local_only`
  - durability_class: `curated_capsule`

### `strategist.current_control`
- state: `exists_usable`
- source ref:
  - `agents/business-strategist-seed/capsules/runtime/strategist-current-control-pack.md`
- target pack id: `strategist.current_control`
- CS2 classification:
  - admission_class: `always_on`
  - freshness_class: `current_required`
  - continuation_scope: `surface_local_only`
  - durability_class: `curated_capsule`
- note: this is the strongest currently verified real pack anchor in the CS2 set

### `strategist.local_current_branch`
- state: `missing_create_first`
- target pack id: `strategist.local_current_branch`
- intended role: branch-local strategist continuation capsule
- likely source refs:
  - active strategist topic branch summary
  - current approved state for the active strategist thread
- CS2 classification:
  - admission_class: `conditional`
  - freshness_class: `ephemeral`
  - continuation_scope: `current_branch_only`
  - durability_class: `generated_summary`

### `strategist.approved_content_plan_summary`
- state: `exists_but_needs_cs2_wrap`
- target pack id: `strategist.approved_content_plan_summary`
- likely source refs:
  - approved content-plan artifacts in task-manager and strategist lane outputs
- note: evidence for related planning artifacts exists in the broader workspace, but a clean CS2 compact pack with explicit metadata still needs to be carved out
- CS2 classification:
  - admission_class: `conditional`
  - freshness_class: `current_required`
  - continuation_scope: `surface_local_only`
  - durability_class: `generated_summary`

### `strategist.offer_constraints_summary`
- state: `missing_create_first`
- target pack id: `strategist.offer_constraints_summary`
- intended role: compact current offer/value constraints summary
- CS2 classification:
  - admission_class: `conditional`
  - freshness_class: `current_required`
  - continuation_scope: `surface_local_only`
  - durability_class: `generated_summary`

### `strategist.business_bottleneck_summary`
- state: `missing_create_first`
- target pack id: `strategist.business_bottleneck_summary`
- intended role: compact current business bottleneck summary for strategic asks
- CS2 classification:
  - admission_class: `conditional`
  - freshness_class: `current_required`
  - continuation_scope: `surface_local_only`
  - durability_class: `generated_summary`

---

## 2.3 `architect`

### `architect.core_operating_contract`
- state: `missing_create_first`
- target pack id: `architect.core_operating_contract`
- intended role: compact always-on architect discipline pack
- note: architecture-oriented artifacts exist, but no verified compact architect operating-contract capsule was found in the quick source scan
- CS2 classification:
  - admission_class: `always_on`
  - freshness_class: `slow_moving`
  - continuation_scope: `surface_local_only`
  - durability_class: `curated_capsule`

### `architect.current_state_summary`
- state: `exists_but_needs_cs2_wrap`
- target pack id: `architect.current_state_summary`
- likely source refs:
  - `task-manager/artifacts/task-217-current-state-architecture-overview-for-yuriy-2026-04-29.md`
  - current architecture state/spec artifacts around context/runtime work
- note: useful architecture state material exists, but not yet as one compact CS2 pack with explicit freshness and admission metadata
- CS2 classification:
  - admission_class: `always_on`
  - freshness_class: `current_required`
  - continuation_scope: `surface_local_only`
  - durability_class: `generated_summary`

### `architect.local_current_branch`
- state: `missing_create_first`
- target pack id: `architect.local_current_branch`
- intended role: branch-local architect continuation capsule
- CS2 classification:
  - admission_class: `conditional`
  - freshness_class: `ephemeral`
  - continuation_scope: `current_branch_only`
  - durability_class: `generated_summary`

### `architect.implementation_mapping`
- state: `exists_but_needs_cs2_wrap`
- target pack id: `architect.implementation_mapping`
- likely source refs:
  - current implementation-facing spec artifacts in task-manager
  - validated mapping notes tied to active architecture tasks
- CS2 classification:
  - admission_class: `conditional`
  - freshness_class: `current_required`
  - continuation_scope: `surface_local_only`
  - durability_class: `generated_summary`

### `architect.current_decision_register_summary`
- state: `missing_create_first`
- target pack id: `architect.current_decision_register_summary`
- intended role: compact current design decision register
- CS2 classification:
  - admission_class: `conditional`
  - freshness_class: `current_required`
  - continuation_scope: `surface_local_only`
  - durability_class: `generated_summary`

---

## 2.4 `learning`

### `learning.mode_rules`
- state: `missing_create_first`
- target pack id: `learning.mode_rules`
- intended role: stable learning-surface operating rules
- CS2 classification:
  - admission_class: `always_on`
  - freshness_class: `slow_moving`
  - continuation_scope: `surface_local_only`
  - durability_class: `curated_capsule`

### `learning.current_roadmap_summary`
- state: `exists_but_needs_cs2_wrap`
- target pack id: `learning.current_roadmap_summary`
- likely source refs:
  - roadmap/spec artifacts such as `task-manager/artifacts/hermes-next-slice-spec-plan-roadmap-2026-05-13.md`
  - future learning-specific curated roadmap summary
- note: available roadmap material is not yet the same thing as a dedicated learning current-roadmap pack
- CS2 classification:
  - admission_class: `always_on`
  - freshness_class: `slow_moving`
  - continuation_scope: `surface_local_only`
  - durability_class: `generated_summary`

### `learning.local_current_branch`
- state: `missing_create_first`
- target pack id: `learning.local_current_branch`
- intended role: branch-local teaching/explanation continuation capsule
- CS2 classification:
  - admission_class: `conditional`
  - freshness_class: `ephemeral`
  - continuation_scope: `current_branch_only`
  - durability_class: `generated_summary`

### `learning.topic_specific_summary`
- state: `missing_create_first`
- target pack id: `learning.topic_specific_summary`
- intended role: compact current topic summary admitted only when explanation depends on that topic
- CS2 classification:
  - admission_class: `conditional`
  - freshness_class: `current_required`
  - continuation_scope: `surface_local_only`
  - durability_class: `generated_summary`

---

## 2.5 `task_scoped_execution`

### `task.bootstrap_packet`
- state: `exists_usable`
- source ref:
  - `task-manager/artifacts/fresh-task-scoped-bootstrap-contract-2026-04-24.md`
- target pack id: `task.bootstrap_packet`
- note: the contract clearly exists; concrete per-run bootstrap packets still need generation at runtime, but the operating surface is already defined
- CS2 classification:
  - admission_class: `always_on`
  - freshness_class: `current_required`
  - continuation_scope: `current_task_only`
  - durability_class: `task_bootstrap`

### `task_scoped.execution_contract`
- state: `exists_but_needs_cs2_wrap`
- target pack id: `task_scoped.execution_contract`
- likely source refs:
  - `task-manager/artifacts/fresh-task-scoped-bootstrap-contract-2026-04-24.md`
  - active task-manager operating rules
- note: execution-contract semantics exist, but should be split cleanly from the bootstrap packet as a compact reusable pack
- CS2 classification:
  - admission_class: `always_on`
  - freshness_class: `slow_moving`
  - continuation_scope: `shared_safe`
  - durability_class: `curated_capsule`

### `task_scoped.linked_artifact_summary`
- state: `missing_create_first`
- target pack id: `task_scoped.linked_artifact_summary`
- intended role: compact summary of linked artifacts needed for the current task
- CS2 classification:
  - admission_class: `conditional`
  - freshness_class: `current_required`
  - continuation_scope: `current_task_only`
  - durability_class: `generated_summary`

### `task_scoped.narrow_recent_excerpt`
- state: `missing_create_first`
- target pack id: `task_scoped.narrow_recent_excerpt`
- intended role: only the minimum recent excerpt when something not yet externalized must follow the task
- CS2 classification:
  - admission_class: `conditional`
  - freshness_class: `ephemeral`
  - continuation_scope: `current_task_only`
  - durability_class: `generated_summary`

---

## 3. Cross-surface verdict

### Already verified strong anchors
- `strategist.core_operating_contract`
- `strategist.current_contour`
- `strategist.current_control`
- `task.bootstrap_packet` (contract-level anchor)

### Exists but still needs CS2 wrapping/extraction
- `strategist.approved_content_plan_summary`
- `architect.current_state_summary`
- `architect.implementation_mapping`
- `learning.current_roadmap_summary`
- `task_scoped.execution_contract`

### Clearly missing and should be created first
- all branch-local continuation capsules
- `main.local_decision_context`
- `strategist.offer_constraints_summary`
- `strategist.business_bottleneck_summary`
- `architect.core_operating_contract`
- `architect.current_decision_register_summary`
- `learning.mode_rules`
- `learning.topic_specific_summary`
- `task_scoped.linked_artifact_summary`
- `task_scoped.narrow_recent_excerpt`

---

## 4. Implementation implication for CS2-C1

Runtime binding should not wait for every ideal pack to exist.

It should support three early behaviors:
1. load verified existing packs directly,
2. load wrapped/generated packs where source refs exist,
3. emit explicit `missing_pack` trace reasons where a manifest references a pack not yet materialized.

That allows CS2 runtime binding to land incrementally without lying about completeness.

---

## 5. Recommended next step

Use this map as the input to the runtime assembly binding plan:
- define how manifests resolve pack ids to sources,
- define how missing packs surface in trace/debug output,
- bind verified strategist and task-scoped anchors first.
