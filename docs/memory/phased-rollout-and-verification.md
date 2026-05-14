# Memory Runtime Phased Rollout and Verification

## Purpose

This document defines a reusable rollout pattern for introducing major memory-runtime improvements without breaking the currently working retrieval backbone.

The central rule is simple:
- ship improvements in reversible waves;
- keep the current useful path protected;
- require explicit verification packs rather than vague optimism.

---

## Core decisions

1. Protection of the current lexical retrieval path is the primary safety rail.
2. Behavior-preserving module extraction should ship before major serving-authority changes.
3. Observability and freshness visibility should exist before broad typed-serving promotion.
4. Typed-serving promotion should be lane-scoped and object-family-scoped.
5. Every wave should have a rollback point and explicit no-go criteria.
6. Promotion should depend on bounded verification packs, not informal judgment.

---

## Rollout principles

### Preserve usefulness throughout
At no point should rollout require typed-memory completeness before useful recall continues to work.

### One dominant change axis per wave
Do not combine major module extraction, freshness enforcement, and typed-authority promotion in the same gate.

### Reversibility per deployment boundary
Each wave should identify:
- a feature flag or mode gate;
- a compatibility path;
- the exact rollback or demotion action.

### Trace before trust
If a new authority path cannot explain itself through a bounded trace, it is not ready to outrank the old path.

### Test stale and fallback states explicitly
Stale data and fallback behavior are runtime failure modes, not edge trivia.

### Gate by lane outcomes, not only global averages
A rollout may be safe for one lane and blocked for another.

---

## Protected baseline during transition

The baseline to protect is typically:
- lexical retrieval remains operational;
- source-registry gating remains intact;
- lane-sensitive routing remains intact;
- fallback semantics remain available;
- callers still receive a compatible payload contract.

Transition protections should include:
1. compatibility mode remains callable through most of the rollout;
2. typed-primary paths run in shadow or advisory mode before promotion;
3. payload changes remain adapter-normalized until callers are migrated;
4. fallback is removed only after hybrid paths prove resilient;
5. known lane-exclusion and hygiene rules stay regression-tested.

---

## Recommended wave order

### Wave 0 — Safety baseline and rollout guardrails

Purpose:
- freeze the comparison baseline;
- define feature flags and rollback targets;
- lock the initial lane set and verification pack layout.

Exit gate:
- baseline fixtures exist;
- lane matrix is agreed;
- rollback target is documented.

### Wave 1 — Observability and verification harness first

Purpose:
- make decisions inspectable before changing authority.

Exit gate:
- operators can inspect chosen lane, source families, fallback state, top refs, and stale-state visibility;
- a verification harness can compare baseline and future-wave runs.

### Wave 2 — Bounded-module refactor with compatibility shim

Purpose:
- extract orchestration seams while preserving behavior.

Exit gate:
- refactored path remains materially compatible with protected baseline lanes;
- compatibility mode remains callable.

### Wave 3 — Freshness enforcement and stale-state visibility

Purpose:
- activate root-specific freshness reasoning and operator-visible stale-state control.

Exit gate:
- stale vs fresh state changes runtime traces and serving behavior in bounded, reviewable ways.

### Wave 4 — Typed serving advisory mode

Purpose:
- run typed-serving logic without letting it dominate answers yet.

Exit gate:
- shadow/advisory comparisons show typed candidates are useful, bounded, and evidence-backed.

### Wave 5 — Typed serving primary for selected lanes

Purpose:
- promote typed serving for narrow lanes where readiness is proven.

Exit gate:
- selected lanes pass verification under fresh, stale, mixed, and fallback conditions.

### Wave 6 — Broaden typed-serving coverage and retire transitional shims selectively

Purpose:
- expand from proven narrow lanes to wider serving coverage.

Exit gate:
- broader lane set remains stable enough that transitional compatibility shims can be reduced selectively.

---

## No-go criteria pattern

A wave should stop if any of these appear:
- no reproducible baseline comparison;
- broken rollback path;
- missing trace visibility for the changed authority path;
- lane-specific regressions hidden by global averages;
- new behavior that depends on stale data but does not surface it;
- semantic drift disguised as “refactor only.”

---

## Verification pack expectations

A serious verification pack should include:
- fixed fixture set by lane;
- backend mode used;
- chosen lane and source-family trace;
- top cited/supporting refs;
- freshness state;
- fallback state;
- pass/fail verdicts;
- comparison between baseline and candidate behavior.

For typed-serving promotion, add:
- shadow/advisory comparison output;
- evidence/provenance checks;
- stale-state and contradiction cases;
- rollback-demotion confirmation.

---

## Rollback posture

Rollback should prefer demotion over deletion.

Examples:
- disable typed-primary decisions;
- disable new planner or module path;
- mute freshness enforcement from enforcing to advisory;
- route back to compatibility mode.

Do not make service recovery depend on destructive schema or content rollback unless absolutely unavoidable.

---

## Design summary

The durable rollout pattern is:
- protect lexical baseline first;
- instrument before trusting new authority paths;
- extract modules before widening semantics;
- enforce freshness before promoting typed dominance;
- promote typed serving lane by lane;
- keep every wave reversible and verified.

That is how a memory runtime evolves without gambling the working system on one big switch.
