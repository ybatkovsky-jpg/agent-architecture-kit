# Retrieval Orchestration as Bounded Modules

## Purpose

This document defines a reusable refactor pattern for decomposing a monolithic memory-retrieval runtime into bounded, testable modules.

The key constraint is safety:
- behavior preservation comes first;
- modularity comes second;
- architecture cleanup must not quietly regress working retrieval semantics.

---

## Core decision

Refactor orchestration into explicit seams for at least:
1. classification;
2. candidate fetch;
3. ranking and authority resolution;
4. serving-pack assembly;
5. trace and diagnostics;
6. policy and authority definitions;
7. runtime and storage adapters.

This split should preserve current lane-sensitive retrieval behavior while reducing regression blast radius.

---

## Why the split matters

A monolithic retrieval runtime usually accumulates too many responsibilities in one place:
- request classification;
- source routing;
- SQL or index retrieval;
- local fallback fetch;
- suppression and ranking heuristics;
- authority shaping;
- trace synthesis;
- final payload assembly;
- runtime/backend selection.

That creates several problems:
1. heuristics become hard to test in isolation;
2. policy and mechanism get interleaved;
3. adapters remain implicit instead of explicit;
4. small edits cause broad regression risk;
5. typed-serving promotion becomes harder because seams do not exist.

---

## Target orchestration shape

```text
request
  -> classifier
  -> retrieval plan builder
  -> candidate fetchers (typed / lexical / local fallback)
  -> ranking pipeline
  -> authority resolver
  -> serving-pack assembler
  -> trace/diagnostics builder
  -> runtime adapter
```

---

## Required module set

### 1. Classification

Owns:
- lane or request-class detection;
- confidence;
- budget class;
- citation expectation;
- initial domain intent.

Must not own:
- storage access;
- candidate ranking;
- final payload assembly.

### 2. Policy and authority definitions

Owns:
- domain tags and lane maps;
- authority alias maps;
- source exclusion rules;
- default budgets;
- typed-vs-lexical precedence policy;
- freshness-policy hooks.

Must not own:
- SQL execution;
- file walking;
- final answer formatting.

### 3. Planner

Owns:
- source selection;
- retrieval budget expansion;
- path eligibility decisions;
- fallback declaration;
- lane-aware fetch plan creation.

### 4. Candidate fetchers

Separate fetch planes where possible:
- typed fetcher;
- lexical/index fetcher;
- local fallback fetcher.

Owns:
- storage-specific retrieval logic;
- provenance and freshness attachment;
- fetch-plane-specific error reporting.

Must not own:
- final winner selection;
- end-user answer shaping.

### 5. Ranking pipeline

Owns:
- suppression passes;
- hygiene filters;
- score shaping;
- diversity shaping;
- lane-aware reranking.

Must not hide policy decisions that deserve explicit authority handling.

### 6. Authority resolver

Owns:
- canonical precedence application;
- freshness-aware demotion;
- supersession handling;
- contradiction shaping;
- final winner justification.

This should be a first-class seam, not an implicit side effect of score math.

### 7. Serving-pack assembler

Owns:
- bounded top-item selection;
- supporting-ref selection;
- answer envelope metadata;
- serving-pack contract output.

### 8. Trace and diagnostics builder

Owns:
- stage events;
- open-question synthesis;
- fallback visibility;
- conflict reporting;
- bounded debug surfaces.

### 9. Runtime adapter

Owns:
- conversion from serving pack to caller-facing payload;
- compatibility shims;
- bridge handling for installed-runtime or integration seams.

---

## Refactor stance

The correct initial stance is behavior-preserving first.

That means the refactor should initially preserve:
- lane-sensitive retrieval semantics;
- DB-first plus local-fallback behavior;
- current runtime integration seams behind adapters;
- existing payload compatibility through shims if needed.

Do not use “modularization” as cover for unreviewed semantic changes.

---

## Rollout safety rules

1. Extract one seam at a time where possible.
2. Keep compatibility mode available during the transition.
3. Gate each module extraction with bounded regression checks.
4. Avoid coupling module extraction with large authority-policy changes.
5. Preserve fallback semantics until the new structure proves resilient.

---

## Acceptance checks

A bounded-module refactor is succeeding when:
1. the same request lanes still produce materially compatible answers;
2. fetch planes can be tested separately;
3. authority decisions become more explicit, not less;
4. fallback and stale-state behavior remain visible;
5. regression blast radius narrows because policy, fetch, ranking, and shaping are no longer tangled in one execution surface.

---

## Design summary

The durable modular pattern is:
- classification as one seam;
- policy as declarative input;
- planning as bounded orchestration;
- fetchers as storage-specific planes;
- ranking and authority as separate concerns;
- serving-pack assembly as an explicit contract;
- trace and adapters as first-class boundaries.

That is how a retrieval system becomes easier to evolve without becoming easier to break.
