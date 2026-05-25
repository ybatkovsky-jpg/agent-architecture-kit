# Task 420 — Closure review for C1 serving-class matrix

Date: 2026-05-12
Task: #420
Review type: bounded closure-readiness check
Decision: **closure-ready**

---

## Scope of this review

This review checks whether the existing C1 artifact for task #420 is sufficient for bounded closure without introducing a new product/runtime layer.

Reviewed primary artifacts:
- `task-manager/artifacts/task-420-openclaw-frame-serving-class-matrix-v1-2026-05-12.json`
- `task-manager/artifacts/task-420-openclaw-frame-serving-class-matrix-v1-2026-05-12.md`

Referenced conservatively as downstream evidence:
- `task-manager/artifacts/task-421-context-serving-evaluator-v0-report-2026-05-12.json`
- `task-manager/artifacts/task-421-context-serving-evaluator-fixtures-2026-05-12.json`
- `task-manager/artifacts/task-422-x1-cross-lane-rerun-pack-2026-05-12.md`

Policy basis checked:
- `task-manager/artifacts/task-396-openclaw-frame-context-serving-policy-v1-2026-05-12.md`

---

## What was verified

### 1. C1 artifact exists in executable form

The core requirement for C1 was to turn serving policy into a machine-checkable request-class × object-class matrix.

That requirement is satisfied by the JSON artifact because it contains:
- normalized request classes;
- normalized object classes;
- full per-cell serving decisions;
- constrained outputs (`always_on`, `on_demand`, `forbidden`);
- authority-order metadata;
- compact consistency rules.

### 2. The matrix stays bounded to policy translation

The artifact does **not** introduce a new product or architecture layer.
It is a conservative executable normalization of the policy in #396.
This matches the stated task boundary for C1.

### 3. Core policy claims are represented explicitly

The reviewed matrix encodes the main closure-relevant policy constraints from #396:
- always-on remains narrow and current-contour-only;
- transcript-first context is explicitly forbidden ambiently;
- historical canonical objects are retrievable but not ambiently always-on;
- `retrieval_document` remains lowest-authority among allowed retrieval classes;
- audit/source-trace defaults to proof-bearing artifact classes.

### 4. Downstream executability evidence exists

Task #421 provides bounded downstream evidence that #420 is already executable enough to drive a thin evaluator without adding new serving policy.

Observed support from #421:
- evaluator explicitly depends on the #420 matrix;
- six fixtures cover all normalized request classes from #420;
- fixture summary reports `all_passed: true`;
- report notes the evaluator is intentionally thin and only executes the #420 matrix.

This is sufficient evidence that #420 is not just descriptive prose; it is consumable in executable form.

### 5. No closure blocker introduced by #422

Task #422 is broader cross-lane rerun evidence and still shows mixed-pack issues at the system level.
However, those issues are not a precise closure blocker for #420 itself because:
- #420 is a C1 matrix-definition artifact, not full runtime retrieval integration;
- #421 already demonstrates bounded execution of the matrix contract;
- #422 mainly signals broader boundary hardening still needed elsewhere, not incompleteness of the matrix artifact itself.

---

## Closure rationale

Task #420 should be considered **closure-ready** because:
1. the requested executable-form artifact exists;
2. it remains within the bounded C1 scope;
3. the policy-to-matrix translation is explicit and machine-checkable;
4. downstream task #421 provides conservative execution evidence directly against the matrix;
5. no missing minimal supporting artifact is required to justify closure.

---

## Non-blocking notes

These are not closure blockers for #420:
- #421 evaluator is thin and bounded rather than runtime-integrated;
- #422 still shows broader mixed-pack cross-lane issues;
- future tightening may expand fixtures or verifier depth.

Those belong to downstream enforcement / integration / hardening work, not to the bounded C1 completion test for #420.

---

## Final decision

**Task #420 status: closure-ready**

Recommended close reason:
- C1 serving-class matrix is present in executable form, policy-bounded, and conservatively validated by downstream evaluator evidence in #421.
