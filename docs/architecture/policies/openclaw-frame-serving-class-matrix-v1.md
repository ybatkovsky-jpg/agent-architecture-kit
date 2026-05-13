# OpenClaw Frame Serving-Class Matrix v1

## 1. Purpose

This document turns the context-serving policy into an executable request-class × object-class matrix.

Its role is to make serving decisions machine-checkable without expanding the underlying policy surface. It defines:
- normalized request classes;
- normalized object classes;
- the allowed serving outcomes for each combination;
- authority-order notes and consistency constraints.

This document is intentionally narrow. It is a policy-to-executable bridge, not a new retrieval architecture.

---

## 2. Policy intent

The matrix exists to enforce three core rules consistently:

1. **Always-on context must stay narrow.**
2. **Historical and derived material must not silently become ambient truth.**
3. **Transcript-first continuity must remain forbidden by default.**

The matrix expresses those rules in a form suitable for evaluators, fixtures, and runtime enforcement.

---

## 3. Serving outcomes

Each request-class × object-class cell must resolve to exactly one of:

- `always_on` — safe and expected in the default orientation pack for that request class;
- `on_demand` — retrievable when the request calls for it, but not ambient;
- `forbidden` — must not be injected into runtime context for that request class.

These outcomes are intentionally minimal. Ranking and explanation can be layered on top, but the base serving class must remain explicit.

---

## 4. Normalized request classes

The matrix uses six normalized request classes:

- `current_task_execution`
- `resume_reopen_continuation`
- `policy_decision_lookup`
- `artifact_source_trace_request`
- `preference_operating_style_recall`
- `general_topic_lookup`

These classes are intentionally broad enough for stable policy enforcement while still being specific enough to change serving behavior materially.

---

## 5. Normalized object classes

The matrix distinguishes the following object classes:

- `task_state_current`
- `canonical_handoff_current_branch`
- `state_summary_current_contour`
- `decision_memory_note`
- `pattern_blocker_durable_ref_memory_note`
- `preference_memory_note`
- `wiki_page`
- `evidence_record`
- `source_record`
- `retrieval_document`
- `raw_transcript_tail`
- `operator_summary_unanchored`
- `historical_retrieval_bundle_unscoped`
- `task_state_historical`
- `canonical_handoff_historical_branch`
- `meta_artifact_projection`

The split between current and historical task or handoff objects is deliberate. Current active-branch truth may be ambient in some request classes; historical truth may be canonical but should still stay on-demand unless the request requires it.

---

## 6. High-level rules encoded by the matrix

### 6.1 Hard forbidden ambient objects

The following object classes should remain `forbidden` across all request classes:

- `raw_transcript_tail`
- `operator_summary_unanchored`
- `historical_retrieval_bundle_unscoped`

This enforces the anti-pattern rule that transcript residue and unanchored summaries must not become default continuity substrates.

### 6.2 Always-on must remain narrow and request-shaped

Examples:
- status and continuation requests may keep `task_state_current` and `canonical_handoff_current_branch` as `always_on`;
- preference recall may keep `preference_memory_note` as `always_on`;
- audit-style requests may treat `evidence_record` and `source_record` as `always_on` within that request frame.

Always-on should never expand merely because material is available.

### 6.3 Historical canonical objects are retrievable, not ambient

Historical task states and older handoff branches may remain important and canonical, but they should usually be `on_demand`, not `always_on`.

Canonical does not mean ambient.

### 6.4 Derived retrieval stays low-authority

`retrieval_document` may help discover stronger anchors, but it must remain the lowest-authority allowed class among truth-bearing objects in the matrix.

---

## 7. Authority notes

Serving class and authority are related but distinct.

Typical authority order remains:
1. current task state;
2. current-branch continuation truth;
3. durable memory notes;
4. wiki pages;
5. evidence records;
6. retrieval documents.

The matrix should preserve this relationship explicitly so that an allowed low-authority object does not silently outrank a stronger anchor.

---

## 8. Consistency constraints

A valid executable matrix should satisfy at least these checks:

1. every normalized request class has a full row covering every normalized object class;
2. every cell uses only `always_on`, `on_demand`, or `forbidden`;
3. hard-forbidden ambient classes stay forbidden everywhere;
4. active-contour-only objects are never marked `always_on` outside the request classes that justify them;
5. `retrieval_document` remains the lowest-authority allowed derived class.

These checks are intentionally small but machine-verifiable.

---

## 9. Suggested executable representation

A practical machine-readable form should include:
- `request_classes`
- `object_classes`
- `matrix`
- per-cell `serving` value
- optional authority rank and note fields
- global consistency checks

A JSON artifact is a natural fit for this layer because it is easy to validate and consume from evaluators or runtime guards.

---

## 10. Why this layer matters

Without an explicit matrix, serving policy stays vulnerable to drift:
- transcript or summary residue may leak back into default context;
- historical canonical material may become ambient by convenience;
- retrieval surfaces may outrank stronger anchors due to lexical match alone.

The matrix constrains those failure modes by making the policy executable.

---

## 11. Recommended use

Use this document and its machine-readable counterpart when you need to:
- build a context-serving evaluator;
- verify that serving behavior matches policy;
- enforce request-shaped serving at runtime;
- prevent transcript-first or bundle-first regressions.

It should be treated as a thin enforcement layer over the serving policy, not as a substitute for the policy itself.
