# Memory Runtime Improvement Overview

## Purpose

This document provides the high-level rationale and transition map for evolving a live memory runtime from a lexical-first retrieval system with a sparse typed overlay into a stronger hybrid architecture.

It is an overview layer.
It does not replace the more specific documents on:
- runtime serving architecture;
- typed memory as a first-class serving plane;
- freshness and ingestion policy;
- retrieval orchestration modules;
- observability and trace debug;
- phased rollout and verification.

Its job is to explain why those layers exist, how they fit together, and which constraints shape the transition.

---

## Core transition

The target transition is:
- from a lexical-first retrieval runtime with a partially active typed overlay;
- to a typed-memory-first serving runtime backed by a lexical evidence substrate.

The key nuance is that this is not a rejection of lexical retrieval.
It is a change in runtime roles:
- lexical retrieval remains the evidence and discovery backbone;
- typed memory becomes the preferred serving plane for reusable meaning.

---

## What stays the same

A safe transition preserves these implementation constraints:
- a structured backing store remains central;
- lexical document/chunk retrieval remains operational during transition;
- durable file-backed sources remain important human-readable authority roots;
- source-registry or source-gating rules remain the ingestion boundary;
- lane-aware retrieval remains necessary;
- fallback behavior remains available until stronger hybrid behavior is proven.

This is a transition plan, not a “throw away the old system and hope” plan.

---

## What changes

The architecture should shift in several deliberate ways:
1. typed Memory Core becomes the preferred serving plane when eligible typed objects exist;
2. lexical retrieval becomes the evidence and discovery substrate rather than the dominant final serving plane;
3. retrieval orchestration is split into narrower modules with explicit interfaces;
4. freshness becomes visible, enforced, and monitorable;
5. memory-answer traces become inspectable;
6. authority, supersession, and staleness become explicit runtime behaviors rather than implicit side effects.

---

## Current-state diagnosis

A useful live memory system may still need architectural improvement.
Typical symptoms of the transitional state are:
- lexical retrieval does too much of the practical serving work;
- typed memory exists, but behaves as a sparse overlay rather than a dominant serving layer;
- freshness is weak or invisible;
- authority shaping lives mostly inside orchestration heuristics;
- observability is partial;
- too much policy and runtime behavior is concentrated in one orchestration-heavy execution surface.

The system may be useful already, but still structurally underpowered.

---

## Non-negotiable constraints

A serious improvement plan should respect these constraints:

### 1. Keep the working retrieval backbone alive
Do not require typed-memory completeness before useful recall continues to work.

### 2. Preserve ingestion boundaries
Do not quietly widen what enters indexed or typed memory just to improve apparent recall.

### 3. Keep durable human-readable roots inspectable
A memory architecture should not become opaque or impossible to audit.

### 4. Preserve lane sensitivity
Continuation, architecture recall, preference recall, policy lookup, and related lanes should not collapse into one flat ranking policy.

### 5. Treat staleness as a runtime risk
Freshness problems are not only ingest-maintenance problems; they affect serving truth.

### 6. Improve observability before aggressive authority promotion
If a new serving path cannot explain itself, it is not ready to outrank the old one.

---

## Target runtime shape

A stronger memory runtime should look roughly like this:

```text
memory request
  -> lane classifier
  -> serving planner
  -> typed-serving plane (preferred when eligible)
  -> lexical evidence retrieval plane (discovery + support + fallback)
  -> authority resolver
  -> freshness evaluator
  -> bounded serving-pack assembler
  -> trace + answer/context output
```

This shape matters because it makes the runtime easier to reason about, test, and evolve.

---

## Runtime layers

### Layer 1 — Durable source roots
Human-readable source material such as memory files, task artifacts, and handoff surfaces.

### Layer 2 — Lexical evidence backbone
Searchable indexed evidence with provenance and discovery value.

### Layer 3 — Typed Memory Core
Compact reusable objects such as notes, evidence anchors, retrieval documents, continuity objects, and typed links.

### Layer 4 — Serving orchestration runtime
Lane choice, source/object selection, authority resolution, freshness handling, and serving-pack assembly.

### Layer 5 — Observability and governance
Traceability, stale-state visibility, verification support, and rollout control.

---

## Lexical backbone vs typed Memory Core

The two planes should not compete blindly.
They have different roles.

### Lexical backbone
Best for:
- evidence indexing;
- search-time matching;
- provenance anchors;
- citations and supporting quotes;
- discovery for future distillation.

Not ideal as the long-term dominant final serving authority for:
- reusable decisions;
- canonical preferences;
- stable patterns and anti-patterns;
- session continuity summaries.

### Typed Memory Core
Best for:
- reusable conclusions;
- compact memory notes;
- continuity/session capsules;
- typed relations and supersession behavior;
- explicit serving decisions about what should be surfaced.

Not a replacement for raw evidence storage.
Typed memory should stay grounded in evidence.

---

## Transitional serving principle

During transition, the right operating model is:
- typed-first when typed objects exist and are eligible;
- lexical-backed when typed coverage is missing or insufficient;
- never provenance-free;
- never stale-by-default without explicit trace state.

This gives the system a stronger serving layer without severing its grounding.

---

## Why the improvement stack splits into multiple docs

A single giant architecture spec is not the best reusable product layer.
The improvement stack naturally separates into distinct concerns:

1. **Runtime serving architecture**
   - the major layers and serving contract.

2. **Typed serving plane**
   - what typed entities exist and when they may lead serving.

3. **Freshness and ingestion policy**
   - how stale state is detected and how it changes serving behavior.

4. **Retrieval orchestration modules**
   - how to decompose monolithic runtime logic into explicit seams.

5. **Observability and trace debug**
   - how to explain answer decisions safely and usefully.

6. **Phased rollout and verification**
   - how to ship the transition without breaking the working system.

This overview exists to connect those layers into one readable architecture story.

---

## Recommended migration stance

A durable migration stance is:
- preserve the proven lexical system;
- introduce explicit modular seams;
- make freshness and traces visible early;
- promote typed serving lane by lane;
- keep rollback paths available;
- gate progress with bounded verification packs.

This is stronger than either naive conservatism (“never change anything”) or architecture theatre (“rewrite everything cleanly”).

---

## Anti-patterns to avoid

1. **Typed memory as decorative overlay forever**
   - the typed layer exists but never becomes operationally authoritative.

2. **Lexical-only serving despite stronger typed candidates**
   - reusable meaning keeps getting rediscovered from raw evidence every time.

3. **Authority hidden inside ranking heuristics**
   - the system behaves differently without making the reason inspectable.

4. **Freshness ignored until failures become visible to users**
   - stale state remains invisible until it has already harmed answer quality.

5. **Monolithic orchestration with broad regression blast radius**
   - every change touches everything.

6. **Promotion without traceability**
   - new authority paths are trusted before they can explain themselves.

---

## Practical end state

The desired end state is not a magical memory engine.
It is a system where:
- reusable conclusions are served from typed memory when justified;
- evidence remains easy to inspect and cite;
- stale state is explicit;
- fallback is honest;
- answer decisions are traceable;
- rollout remains reversible until the new authority path proves itself.

---

## Design summary

The architecture direction is:
- keep lexical retrieval as evidence and discovery backbone;
- promote typed memory into the serving plane for reusable meaning;
- add explicit freshness, authority, and observability layers;
- modularize orchestration;
- migrate in reversible, verified waves.

That is the real improvement story behind the detailed memory-runtime docs.
