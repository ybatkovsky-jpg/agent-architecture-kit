# Context System 2 — first runtime proof: strategist assembly

Date: 2026-05-19
Status: bounded proof design / proof-of-assembly stub
Parent task: #531
Task: CS2-C1
Follows:
- `task-manager/artifacts/context-system-2-runtime-assembly-binding-plan-2026-05-19.md`
- `task-manager/artifacts/context-system-2-current-control-pack-map-2026-05-19.md`
- `task-manager/artifacts/context-system-2-first-surface-manifests-2026-05-19.md`

Purpose: turn the CS2 runtime assembly binding plan into one concrete, operationally testable first proof for a single surface with the best current verified anchors.

---

## 1. Selected surface

Selected surface: `strategist`

Why this surface was chosen first:
- it has the strongest verified direct-pack anchors in the current pack map;
- all three required strategist always-on packs already exist as compact source files;
- the manifest shape is clear and narrow;
- it gives an honest optional-missing case via `strategist.local_current_branch` without blocking startup;
- it avoids the higher ambiguity of architect/learning wrap rules and the more synthetic nature of `main` generated continuation packs.

This makes `strategist` the cleanest first proof that the runtime seam can:
1. load direct packs,
2. emit explicit trace for a missing optional pack,
3. return a non-theoretical assembled result.

---

## 2. Exact source anchors used in this proof

### Manifest anchor
- `task-manager/artifacts/context-system-2-first-surface-manifests-2026-05-19.md`
  - selected manifest: `strategist`

### Pack-map anchor
- `task-manager/artifacts/context-system-2-current-control-pack-map-2026-05-19.md`

### Verified direct source files
- `agents/business-strategist-seed/capsules/runtime/strategist-core-operating-contract.md`
- `agents/business-strategist-seed/capsules/bootstrap/strategist-current-contour.md`
- `agents/business-strategist-seed/capsules/runtime/strategist-current-control-pack.md`

---

## 3. Strategist manifest entries covered by this proof

From the current first manifest, the relevant startup entries are:

### Always-on allowlist
1. `strategist.core_operating_contract`
2. `strategist.current_contour`
3. `strategist.current_control`
4. `strategist.local_current_branch`

### Conditional allowlist deliberately left out of this first proof
- `strategist.approved_content_plan_summary`
- `strategist.offer_constraints_summary`
- `strategist.business_bottleneck_summary`

Reason for exclusion in this first proof:
this slice is intentionally limited to proving the direct-load seam plus explicit missing-pack trace. Conditional request-class admission and wrapper generation can be proven next without muddying the first runtime result.

---

## 4. Resolution decisions for this proof

## 4.1 Direct loads

### `strategist.core_operating_contract`
- manifest kind: `pack`
- required: `true`
- pack-map state: `exists_usable`
- load path: `direct`
- materialization mode: `existing_pack`
- source ref:
  - `agents/business-strategist-seed/capsules/runtime/strategist-core-operating-contract.md`
- expected resolution state: `loaded_direct`
- expected trace reason: `source_exists_verified`

### `strategist.current_contour`
- manifest kind: `pack`
- required: `true`
- pack-map state: `exists_usable`
- load path: `direct`
- materialization mode: `existing_pack`
- source ref:
  - `agents/business-strategist-seed/capsules/bootstrap/strategist-current-contour.md`
- expected resolution state: `loaded_direct`
- expected trace reason: `source_exists_verified`

### `strategist.current_control`
- manifest kind: `pack`
- required: `true`
- pack-map state: `exists_usable`
- load path: `direct`
- materialization mode: `existing_pack`
- source ref:
  - `agents/business-strategist-seed/capsules/runtime/strategist-current-control-pack.md`
- expected resolution state: `loaded_direct`
- expected trace reason: `source_exists_verified`

## 4.2 Explicit missing optional pack

### `strategist.local_current_branch`
- manifest kind: `continuation_capsule`
- required: `false`
- pack-map state: `missing_create_first`
- load path in this proof: `missing`
- materialization mode: `none`
- expected resolution state: `missing_pack`
- expected trace reason: `referenced_in_manifest_but_no_verified_pack_or_wrap_rule`

Why this is the right missing case:
- it is referenced by the manifest;
- it is not required;
- no verified concrete generator or compact source file was established in the inspected artifacts;
- the runtime can therefore remain honest and still assemble the strategist surface successfully.

---

## 5. Proof boundary

This proof intentionally covers only this startup set:
- required direct strategist packs;
- one optional missing continuation capsule.

It does **not** yet prove:
- conditional request-class admission;
- wrapped strategist content-plan pack materialization;
- branch-local continuation generation;
- budget trimming under over-cap conditions.

That restraint is deliberate. The goal is to make the first proof small enough that failure is legible.

---

## 6. Expected assembly result

Expected runtime status:
- `assembly_status = ok_with_missing_optional`

Reason:
- all required always-on strategist packs resolve successfully;
- only the non-required continuation capsule is missing.

Expected assembled items:
1. `strategist.core_operating_contract`
2. `strategist.current_contour`
3. `strategist.current_control`

Expected non-assembled traced item:
1. `strategist.local_current_branch`

---

## 7. Proof registry stub

Minimal starter registry sufficient for this one proof:

```json
{
  "strategist.core_operating_contract": {
    "pack_state": "exists_usable",
    "load_mode": "existing_pack",
    "source_ref": "agents/business-strategist-seed/capsules/runtime/strategist-core-operating-contract.md"
  },
  "strategist.current_contour": {
    "pack_state": "exists_usable",
    "load_mode": "existing_pack",
    "source_ref": "agents/business-strategist-seed/capsules/bootstrap/strategist-current-contour.md"
  },
  "strategist.current_control": {
    "pack_state": "exists_usable",
    "load_mode": "existing_pack",
    "source_ref": "agents/business-strategist-seed/capsules/runtime/strategist-current-control-pack.md"
  },
  "strategist.local_current_branch": {
    "pack_state": "missing_create_first",
    "load_mode": "none"
  }
}
```

This is enough to verify the direct path and the missing-pack path without introducing broader generalization too early.

---

## 8. Minimal implementation seam / stub shape

A minimal implementation-facing seam for this proof can be as small as two functions and one result shape.

## 8.1 Suggested seam

```python
from dataclasses import dataclass
from typing import Optional

@dataclass
class ResolverResult:
    pack_id: str
    resolution_state: str
    materialization_mode: str
    source_ref: Optional[str]
    trace_reason: str
    required: bool
    estimated_tokens: int
    content: Optional[str]


def resolve_manifest_entry(surface_id: str, entry: dict, registry: dict, cwd: str) -> ResolverResult:
    ...


def assemble_surface(surface_manifest: dict, registry: dict, cwd: str) -> dict:
    ...
```

## 8.2 Direct-load behavior for this proof

For each admitted strategist startup entry:
1. look up `entry["id"]` in the starter registry;
2. if `load_mode == existing_pack`, read the `source_ref` file;
3. return:
   - `resolution_state = loaded_direct`
   - `materialization_mode = existing_pack`
   - compact token estimate
   - raw file content as the proof payload;
4. if registry state is missing and there is no sanctioned wrap/generate rule, return:
   - `resolution_state = missing_pack`
   - `materialization_mode = none`.

## 8.3 Assembly status rule for this proof

```python
def derive_assembly_status(trace_items: list[ResolverResult]) -> str:
    required_missing = any(
        item.required and item.resolution_state == "missing_pack"
        for item in trace_items
    )
    if required_missing:
        return "degraded_missing_required"

    optional_missing = any(
        (not item.required) and item.resolution_state == "missing_pack"
        for item in trace_items
    )
    if optional_missing:
        return "ok_with_missing_optional"

    return "ok"
```

This is sufficient for the strategist proof without needing the full future budget/trimming machinery.

---

## 9. Expected proof output

## 9.1 Expected normalized assembly object

```json
{
  "surface_id": "strategist",
  "manifest_version": "cs2-v1",
  "assembly_status": "ok_with_missing_optional",
  "assembled_items": [
    {
      "pack_id": "strategist.core_operating_contract",
      "resolution_state": "loaded_direct",
      "materialization_mode": "existing_pack",
      "source_ref": "agents/business-strategist-seed/capsules/runtime/strategist-core-operating-contract.md",
      "trace_reason": "source_exists_verified"
    },
    {
      "pack_id": "strategist.current_contour",
      "resolution_state": "loaded_direct",
      "materialization_mode": "existing_pack",
      "source_ref": "agents/business-strategist-seed/capsules/bootstrap/strategist-current-contour.md",
      "trace_reason": "source_exists_verified"
    },
    {
      "pack_id": "strategist.current_control",
      "resolution_state": "loaded_direct",
      "materialization_mode": "existing_pack",
      "source_ref": "agents/business-strategist-seed/capsules/runtime/strategist-current-control-pack.md",
      "trace_reason": "source_exists_verified"
    }
  ],
  "assembly_trace": [
    {
      "pack_id": "strategist.core_operating_contract",
      "resolution_state": "loaded_direct",
      "required": true
    },
    {
      "pack_id": "strategist.current_contour",
      "resolution_state": "loaded_direct",
      "required": true
    },
    {
      "pack_id": "strategist.current_control",
      "resolution_state": "loaded_direct",
      "required": true
    },
    {
      "pack_id": "strategist.local_current_branch",
      "resolution_state": "missing_pack",
      "materialization_mode": "none",
      "trace_reason": "referenced_in_manifest_but_no_verified_pack_or_wrap_rule",
      "referenced_by_surface": "strategist",
      "required": false
    }
  ]
}
```

## 9.2 Expected compact debug log

```text
[cs2] assemble surface=strategist manifest=cs2-v1
[cs2] admit always_on id=strategist.core_operating_contract required=true
[cs2] resolve id=strategist.core_operating_contract mode=existing_pack state=loaded_direct
[cs2] admit always_on id=strategist.current_contour required=true
[cs2] resolve id=strategist.current_contour mode=existing_pack state=loaded_direct
[cs2] admit always_on id=strategist.current_control required=true
[cs2] resolve id=strategist.current_control mode=existing_pack state=loaded_direct
[cs2] admit always_on id=strategist.local_current_branch required=false
[cs2] resolve id=strategist.local_current_branch state=missing_pack reason=referenced_in_manifest_but_no_verified_pack_or_wrap_rule
[cs2] assembly_status=ok_with_missing_optional assembled=3 missing_optional=1 missing_required=0
```

This is the minimum useful operator/debug view because it answers:
- what surface assembled;
- what actually loaded;
- what was missing;
- whether startup degraded.

---

## 10. Why this proof is stronger than alternative first proofs

### Better than `architect` as first proof
`architect` currently mixes:
- one required pack that appears truly missing;
- one required pack that needs wrapping;
- one conditional pack that also needs wrapping.

That is valuable later, but it is noisier for the first runtime proof because it combines several unproven mechanisms at once.

### Better than `main` as first proof
`main` depends immediately on generated branch-local continuation concepts that are important but still more synthetic and runtime-policy-heavy.

### Better than `task_scoped_execution` as first proof
`task_scoped_execution` has one strong direct anchor (`task.bootstrap_packet` at contract level), but its companion `task_scoped.execution_contract` still needs CS2 wrapping, so the clean all-direct proof is weaker there than in strategist.

So the strategist proof is the best first assembly proof because it is mostly real files, not future promises.

---

## 11. Immediate next implementation step after this proof

Implement this exact strategist starter assembly in the OpenClaw runtime seam:
1. hard-bind the strategist manifest selection;
2. add the four-entry starter registry from this artifact;
3. read the three verified strategist source files directly;
4. emit explicit `missing_pack` trace for `strategist.local_current_branch`;
5. return `assembly_status = ok_with_missing_optional`.

After that lands, the next best proof is:
- one wrapped-pack proof, preferably `architect.current_state_summary` or `task_scoped.execution_contract`.

That sequencing proves the seam in ascending difficulty:
- direct,
- then wrapped,
- then generated.
