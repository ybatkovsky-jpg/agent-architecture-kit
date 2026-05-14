# Memory Runtime Serving Architecture

## Purpose

This document defines a reusable target runtime architecture for a memory system that combines:
- a typed memory layer for reusable conclusions;
- a lexical evidence backbone for discovery and grounding;
- an orchestration layer that resolves authority, freshness, and serving eligibility.

The goal is not to replace lexical retrieval with typed memory, but to make typed memory the preferred serving plane when it is eligible, while preserving lexical retrieval as the evidence backbone and resilience fallback.

---

## Core stance

A robust memory runtime should:
1. serve from a typed, authority-aware Memory Core when eligible;
2. keep lexical retrieval as the evidence backbone and discovery substrate;
3. route both through an explicit orchestration layer;
4. preserve semantics across fallback paths instead of silently changing the authority model.

---

## Scope

In scope:
- runtime serving architecture for memory retrieval and answer assembly;
- serving precedence across typed objects, lexical evidence, and fallback paths;
- module boundaries between retrieval, authority resolution, and answer shaping;
- fallback behavior and recovery expectations.

Out of scope:
- full schema redesign;
- embedding/vector adoption decisions;
- UI-specific rendering;
- storage-engine implementation details for every object family.

---

## Architecture overview

### Top-level shape

```text
memory request
  -> lane classifier
  -> serving planner
  -> typed candidate fetcher
  -> lexical candidate fetcher
  -> authority resolver
  -> freshness evaluator
  -> serving pack assembler
  -> runtime adapter
  -> consumer-facing answer or context payload
```

### Layer map

```text
Layer 0: Durable source roots
  - curated memory files
  - task/artifact stores
  - handoff/continuation stores
  - other approved durable roots

Layer 1: Lexical backbone
  - document/chunk indexes
  - provenance metadata
  - freshness / ingestion state

Layer 2: Typed Memory Core
  - memory notes
  - evidence records
  - retrieval documents
  - continuity/session objects
  - typed links

Layer 3: Retrieval orchestration runtime
  - lane classification
  - source/object routing
  - typed fetch
  - lexical fetch
  - authority resolution
  - freshness resolution
  - serving-pack assembly

Layer 4: Runtime adapter
  - transforms serving packs into tool/runtime-facing payloads
  - preserves policy semantics across integration seams

Layer 5: Consumer surfaces
  - memory-tool responses
  - bounded context payloads
  - continuation-oriented serving packs
  - debug / trace surfaces
```

### Boundary principle

Each layer should own a distinct question:
- Layer 0: what durable material exists?
- Layer 1: what approved evidence is indexed and retrievable?
- Layer 2: what reusable objects have been promoted?
- Layer 3: what should be served for this request and why?
- Layer 4: how is that result adapted safely for runtime consumption?
- Layer 5: what does the caller actually receive?

---

## Component responsibilities

### Lexical backbone

Role:
- canonical evidence index.

Responsibilities:
- index approved source content;
- preserve provenance from source to document to chunk or locator;
- support lexical discovery and grounding;
- expose freshness metadata for indexed content.

Non-responsibilities:
- final serving authority;
- canonical conclusion selection by itself;
- prompt packaging policy.

Expected output:
- ranked lexical candidates with provenance, evidence snippets, freshness state, and retrieval score.

### Typed Memory Core

Role:
- preferred serving authority plane for reusable meaning.

Responsibilities:
- store reusable typed objects such as notes, evidence anchors, retrieval documents, continuity objects, and links;
- encode lifecycle, freshness, confidence, and supersession state;
- preserve references back to evidence.

Non-responsibilities:
- raw source-of-truth storage;
- sole retrieval path;
- immunity from freshness/provenance checks.

Expected output:
- eligible typed candidates with class, scope, freshness, confidence, supersession state, and evidence refs.

### Retrieval orchestration runtime

Role:
- bounded decision-making layer that turns a request into a serving result.

Responsibilities:
- classify the request lane;
- choose source and object families;
- invoke typed and lexical fetchers;
- resolve authority and freshness;
- identify contradictions or uncertainty;
- assemble the serving pack;
- emit a trace envelope.

Non-responsibilities:
- durable source storage;
- hidden mutation of prompt/context inside retrieval branches;
- burying authority logic inside opaque ranking heuristics.

### Runtime adapter

Role:
- isolate serving policy from tool/runtime integration details.

Responsibilities:
- convert serving packs into consumer-facing payloads;
- preserve authority and uncertainty semantics during adaptation;
- avoid widening context beyond what the serving contract allowed.

---

## Serving contract

### Default precedence

When candidate objects compete, the default precedence should be:
1. eligible typed canonical objects for the lane;
2. direct evidence-backed lexical candidates;
3. supporting retrieval documents or synthesized orientation objects;
4. degraded fallback results with explicit caveats.

### Eligibility rules

Typed serving should be preferred only when the object is:
- in-scope for the current lane;
- fresh enough for its purpose;
- not superseded;
- evidence-backed;
- policy-allowed for serving.

If any of those conditions fail, lexical evidence should support, widen, or replace the typed result.

### Output contract

A serving pack should make explicit:
- request lane;
- winning object(s) or evidence path;
- authority basis;
- freshness state;
- contradictions or uncertainty;
- fallback status when applicable;
- evidence refs or source anchors.

Answer shaping should be treated as a contract, not an accidental side effect of retrieval order.

---

## Fallback policy

Fallback is allowed to degrade recall quality, but not to silently change the authority model.

Fallback behavior should preserve these rules:
- evidence still outranks unsupported summaries;
- lane boundaries still apply;
- uncertainty must become more visible, not less;
- degraded results should remain traceable.

The system should prefer a weaker but honest answer over a confident answer assembled from mixed stale context.

---

## Freshness and supersession

The runtime should treat freshness and supersession as first-class serving inputs.

A typed object should not win by default if it is:
- stale relative to the request lane;
- explicitly superseded;
- contradicted by fresher evidence;
- outside its bounded scope.

Lexical evidence should remain available as the grounding and dispute-resolution layer even when typed serving is dominant.

---

## Acceptance checks for this architecture layer

A memory runtime shaped by this architecture should satisfy at least these checks:
1. typed serving can win when an eligible typed object exists;
2. lexical evidence replaces typed output when typed coverage is absent, stale, or ineligible;
3. fallback does not collapse into transcript-first continuity;
4. authority resolution is explicit and traceable;
5. output packs expose enough structure to audit why a result was served.

---

## Design summary

The stable design pattern is:
- typed memory for reusable meaning;
- lexical retrieval for evidence and discovery;
- orchestration for authority and freshness;
- adapter isolation for runtime integration;
- traceable serving packs for consumer surfaces.

That combination is stronger than either a purely lexical memory system or an ungrounded typed-memory-only system.
