# Task #772 — Memory cognitive substrate: significance, freshness, conflict, and working-context promotion

Date: 2026-05-26
Task: #772
Parent: #768
Status: specification draft

## 1. Purpose

Current memory is no longer trivial retrieval, but its strongest future form is not just "better search".
It should become a **cognitive substrate** that decides what matters, what stays hot, what is stale, what conflicts, and what deserves promotion into active working context.

This task defines that substrate at specification scope.

---

## 2. Core design rule

**Memory should optimize operator/useful continuity, not raw retention volume.**

The system must distinguish:
- durable truth from temporary residue;
- hot working context from cold archive;
- fresh evidence from stale but historically relevant evidence;
- conflict that must remain visible from conflict that has been resolved.

---

## 3. Canonical significance hierarchy

The first explicit significance tier model should be:

1. `critical_policy`
2. `durable_operating_truth`
3. `active_working_context`
4. `supporting_evidence`
5. `cold_archive`
6. `ballast_or_suppressible`

### `critical_policy`
High-impact rules, safety constraints, identity/policy boundaries, or operator-critical standing instructions.

### `durable_operating_truth`
Stable preferences, durable facts, reusable lessons, validated decisions, business context, or long-lived architectural truths.

### `active_working_context`
Short- to medium-horizon material needed to continue current or nearby work efficiently.

### `supporting_evidence`
Useful source material that should remain discoverable but should not usually dominate top-level recall by itself.

### `cold_archive`
Material retained for provenance/recovery but intentionally demoted from hot serving paths.

### `ballast_or_suppressible`
Low-value residue such as duplicated paraphrases, stale boilerplate, unimportant trace noise, or superseded repetition.

---

## 4. Freshness model

Each memory object should be understood through at least:
- `recorded_at`
- `last_confirmed_at`
- `freshness_class`
- `revalidation_basis`
- `superseded_by`

### Freshness classes
- `fresh_confirmed`
- `fresh_unconfirmed`
- `aging_but_usable`
- `stale_requires_caution`
- `superseded`
- `historical_only`

---

## 5. Conflict model

Contradiction should be a first-class state, not an accidental retrieval side effect.

### Conflict classes
1. `no_known_conflict`
2. `soft_tension`
3. `hard_conflict_open`
4. `resolved_conflict`
5. `authority_conflict`

When conflict is open, the system should prefer surfacing the conflict posture instead of flattening it into fake certainty.

---

## 6. Working-context promotion model

Promotion into working context should be based on:
- significance;
- recency/freshness;
- relation to the current task/session/request lane;
- unresolved dependency relevance;
- operator actionability.

Promote into `active_working_context` when the item directly changes the next safe action, is recent enough or revalidated, and is not superseded.
Do not promote stale, conflict-heavy, or merely evidentiary ballast unless explicitly needed for provenance.

---

## 7. Lifecycle policy

### Distill
Distill residue/evidence into candidate objects with explicit significance + freshness + conflict posture.

### Promote
Promote into durable memory if long-lived and reusable, active working context if immediately operational, or both when both conditions hold.

### Archive
Archive objects still useful for provenance but not hot serving.

### Suppress
Suppress ballast or duplicated residue from hot serving paths without pretending it never existed.

---

## 8. Retrieval implications

Retrieval should not answer solely by lexical similarity.
It should prefer items that are:
- higher significance,
- fresher,
- conflict-aware,
- lane-relevant,
- and context-promoted when appropriate.

For active execution questions, precedence should usually favor:
1. relevant `active_working_context`
2. durable operating truth with fresh confirmation
3. supporting evidence
4. cold archive
5. suppressed/ballast only if nothing better exists and provenance is necessary

---

## 9. Operator implications

The operator should be able to inspect:
- why an item was hot or cold;
- whether it was durable vs transient;
- freshness posture;
- conflict posture;
- whether it was promoted into working context;
- what evidence/resolution basis justified that promotion.

---

## 10. Minimum implementation-first seam

**Introduce explicit metadata classification for significance/freshness/conflict on promoted memory objects plus a lightweight working-context candidate projection.**

That seam should:
1. add canonical fields/normalization for significance tier, freshness class, and conflict class;
2. allow lifecycle/distill outputs to tag objects with those classes;
3. project a bounded working-context candidate set for current task/session retrieval;
4. stay metadata-first rather than requiring a full new storage engine.

---

## 11. Acceptance shape

This task counts as complete when:
- significance tiers are defined;
- lifecycle/promotion policy is explicit;
- freshness/conflict model is defined;
- a first narrow implementation seam is identified.

---

## 12. Concise verdict

Memory should evolve from retrieval correctness into a cognitive substrate that ranks significance, tracks freshness, exposes conflict, and selectively promotes active working context. The safest first implementation step is metadata-level classification plus a bounded working-context projection layer, not a full storage redesign.
