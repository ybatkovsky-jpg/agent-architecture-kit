# Typed Memory as a First-Class Serving Plane

## Purpose

This document defines how a typed Memory Core can be promoted from a sparse overlay into a first-class serving plane for reusable meaning.

The target outcome is not “typed memory everywhere.”
The target outcome is a system where:
- typed objects become the preferred serving layer for reusable conclusions;
- lexical retrieval remains the evidence backbone and discovery substrate;
- promotion is gated by provenance, freshness, and lifecycle discipline;
- rollout remains reversible.

---

## Core decision

A memory system should promote typed memory into the default authority-aware serving layer for reusable meaning, while preserving the lexical corpus as:
- the evidence backbone;
- the discovery substrate;
- the fallback path when typed coverage is absent, stale, weak, or ineligible.

---

## First-class typed entity families

### 1. Source records

Role:
- typed registry mirror for approved source families and policy metadata.

Serving posture:
- usually not served directly;
- used to validate whether other typed objects are allowed and properly scoped.

### 2. Evidence records

Role:
- typed pointer to source-backed evidence units.

Serving posture:
- rarely primary answer material;
- critical for provenance, contradiction review, and authority explanation.

### 3. Memory notes

Role:
- compact reusable units for decisions, patterns, anti-patterns, blockers, durable references, verified preferences, and bounded state summaries.

Serving posture:
- primary first-class serving object for concise reusable meaning.

### 4. Retrieval documents

Role:
- typed bridge between lexical documents and structured serving behavior.

Serving posture:
- secondary serving object;
- useful when a request benefits from document-level recall but not full distillation.

### 5. Session or continuity capsules

Role:
- bounded continuity object for active task, run, or session state.

Serving posture:
- first-class only for continuation, resume, and active bounded-context lanes.

### 6. Typed links

Role:
- relation graph for supports, supersedes, contradicts, derives-from, relevant-to, and similar authority-bearing relations.

Serving posture:
- usually indirect;
- used to support authority resolution, contradiction handling, and retrieval expansion.

---

## Initial promotion waves

### Wave 1

Promote as first-class serving entities:
- memory notes;
- continuity/session capsules;
- evidence records as authority support.

### Wave 2

Promote more aggressively:
- retrieval documents;
- typed-link-driven relation expansion.

### Non-primary layer

Source records remain policy-supporting rather than primary answer objects.

---

## Write-path policy

### Core principles

1. No typed object without provenance.
2. No typed object should outrank fresher evidence by default.
3. Typed memory promotion should be selective, not a mirror of the full lexical corpus.
4. Typed writes should prefer append/supersede semantics over destructive rewrites.
5. Lane consequences matter: continuity and preference objects need stricter discipline than generic summaries.

### Allowed write sources

Typed object creation may come from:
- approved source-root ingestion outputs;
- curated distillation from durable artifacts or memory surfaces;
- bounded distillers that produce evidence-backed typed candidates;
- controlled human/operator promotion workflows.

Typed object creation should not come solely from:
- uncited transcript residue;
- model guesswork without evidence refs;
- unstable fallback scans without durable anchors;
- speculative summaries with no bounded scope.

---

## Serving eligibility rules

Typed objects should be eligible to lead serving only when they expose at least:
- provenance or evidence refs;
- scope;
- freshness state;
- lifecycle state;
- confidence or verification posture;
- supersession state where relevant.

Typed serving must be gated.
A typed object should not silently outrank stronger evidence if it is:
- stale;
- superseded;
- weakly evidenced;
- lane-ineligible;
- outside its bounded scope.

---

## Typed vs lexical serving relationship

The right relationship is not replacement but structured precedence.

Default flow:
1. query eligible typed objects first;
2. validate them against freshness, scope, and supersession policy;
3. use lexical retrieval to support, verify, widen, or replace them as needed;
4. emit a traceable serving pack whose authority path is explicit.

This keeps typed memory strong where it is justified, while preserving lexical retrieval as the grounding layer.

---

## Backward-compatibility rule

Promotion should be lane-by-lane and object-family-by-object-family.

At every rollout checkpoint, the system should remain reversible by demoting typed serving back to advisory overlay mode.

That means callers should not depend on an all-at-once switch from lexical-first to typed-first behavior.
Instead, the runtime should preserve:
- stable external interfaces;
- explicit traceability for authority decisions;
- safe fallback to lexical evidence.

---

## Readiness criteria

A typed serving plane is ready for wider promotion when:
1. the relevant typed object family has enough density to serve real requests;
2. provenance is explicit and auditable;
3. freshness and supersession rules are enforced;
4. lexical evidence still grounds contradiction resolution and fallback;
5. lane-specific regressions are checked before broader rollout.

---

## Failure modes to avoid

Do not promote a typed layer that:
- acts like a thin overlay with weak data but still outranks stronger evidence;
- stores conclusions without provenance;
- leaks session continuity objects into global reusable memory;
- mirrors the lexical corpus without selective promotion discipline;
- hides fallback behavior behind apparently smooth but less truthful responses.

---

## Design summary

The durable pattern is:
- typed memory for reusable conclusions;
- lexical retrieval for evidence and discovery;
- eligibility gating for safety;
- reversible rollout by lane and object family;
- explicit serving traces rather than implicit ranking magic.

That is what makes typed memory a first-class serving plane instead of just a decorative overlay.
