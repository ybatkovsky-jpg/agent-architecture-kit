# Memory Target Architecture v1 — 2026-05-13

## Purpose

Design a cleaner target architecture for the deployed OpenClaw memory contour based on the current observed state:
- custom policy-aware retrieval already exists;
- source authority semantics already matter;
- current contour is still too heuristic-heavy and weakly observable.

This document proposes a next-step architecture that preserves the strong parts and removes avoidable brittleness.

---

## 1. Core diagnosis

Current contour strengths:
- request-class-aware retrieval;
- authority-first serving logic;
- bounded context budgets;
- explicit separation between continuation, evidence, and shared memory lanes.

Current contour weaknesses:
- too much dependence on path/title heuristics;
- candidate admission and final ranking are not cleanly separated;
- weak retrieval observability;
- corrective anti-noise logic is compensating for an under-modeled source system.

Therefore the target architecture should:
1. preserve policy-aware retrieval;
2. formalize source types and authority classes;
3. split candidate admission from ranking;
4. emit traceable retrieval decisions;
5. reduce filename/path heuristics to a fallback role only.

---

## 2. Target runtime flow

```text
user query
  -> query normalizer
  -> request classifier
  -> source gate
  -> candidate admission
  -> authority/rule filter
  -> final ranker
  -> context packer
  -> prompt injection
  -> retrieval trace log
```

### Stage meanings

#### A. Query normalizer
Responsibility:
- normalize query text;
- detect language/mixed-language form;
- extract explicit artifact/path/task identifiers;
- detect trace/citation intent.

Output:
- normalized query payload.

#### B. Request classifier
Responsibility:
- assign request class, for example:
  - `current_task_execution`
  - `resume_reopen_continuation`
  - `architecture_design_recall`
  - `meta_evaluation_recall`
  - `policy_decision_lookup`
  - `preference_operating_style_recall`
  - `artifact_source_trace_request`
  - `factual_lookup`

Output:
- request class;
- confidence;
- requested serve class;
- retrieval budget profile.

#### C. Source gate
Responsibility:
- choose which source families are admissible for this request class;
- exclude forbidden default lanes before expensive ranking begins.

Input:
- request class;
- source registry metadata.

Output:
- admissible source family set;
- excluded families with reason codes.

#### D. Candidate admission
Responsibility:
- fetch candidate documents/chunks only from admissible sources;
- use source-declared metadata, not filename guesses, as the primary routing basis;
- return a broad but lane-safe candidate pool.

Output:
- candidate pool with provenance metadata.

#### E. Authority/rule filter
Responsibility:
- enforce authority ordering;
- demote lower-authority substitutes;
- apply request-class-specific rule constraints.

Examples:
- meta-evaluation should not silently substitute continuation handoff as first-class evidence;
- preference recall should prefer verified memory notes over generic artifacts;
- factual source trace should only pass source-citable items.

Output:
- filtered/scored candidate set.

#### F. Final ranker
Responsibility:
- combine semantic similarity, authority score, freshness, request-class fit, and explicit source-match signals;
- choose final top-k items under budget.

Output:
- final evidence/context items.

#### G. Context packer
Responsibility:
- assemble prompt-safe context blocks;
- deduplicate overlapping artifacts;
- emit citations and short rationale per item;
- respect token budget.

Output:
- final injected context package.

#### H. Retrieval trace log
Responsibility:
- log why the system answered the way it did.

Trace fields should include:
- request id;
- request class;
- classifier confidence;
- admissible source families;
- excluded source families + reasons;
- candidate count by family;
- final selected items;
- dropped high-score items + reason;
- budget profile;
- total estimated tokens.

---

## 3. Canonical source model

The current contour should move to declared source families.

### Required source families

- `task_state`
  - live or recent task-manager state
  - active task metadata
  - next actions

- `canonical_handoff`
  - continuation handoffs
  - bounded-session resumability artifacts

- `evidence_record`
  - architecture artifacts
  - verification notes
  - evaluation outputs
  - source-of-truth docs for factual recall

- `memory_note`
  - durable operating preferences
  - distilled lessons
  - curated long-term notes

- `wiki_page`
  - synthesized or reference-style stable internal docs

- `retrieval_document`
  - generic searchable documents with lower authority by default

- `session_capsule`
  - optional transient conversation-derived state
  - should be narrow and controlled, not default authority

### Important rule

Source family must be declared in registry/config metadata.

Path/title heuristics may still exist, but only as:
- migration fallback,
- anomaly detection,
- validation warning source.

They should not remain the primary routing backbone.

---

## 4. Scoring model

A cleaner ranking formula should separate components.

### Suggested score factors

- `semantic_match_score`
- `authority_score`
- `freshness_score`
- `request_class_fit_score`
- `explicit_reference_score`
- `source_quality_score`
- `noise_penalty`

### Decision rule

Do not compute one opaque score too early.

Use this sequence instead:
1. admission threshold;
2. authority gate;
3. final weighted ranking among admissible items.

This makes debugging far easier than current all-in-one heuristic mixtures.

---

## 5. Observability design

This is the highest-priority architectural gap.

### Required observability outputs

#### Retrieval trace record
One structured record per retrieval call.

#### Reason codes
Every exclusion/demotion should carry a reason code, e.g.:
- `forbidden_by_request_class`
- `authority_mismatch`
- `generic_handoff_substitution_blocked`
- `low_citation_value`
- `budget_trimmed`
- `wrapper_noise_penalty`

#### Eval harness by request class
Maintain small reproducible test packs for:
- continuation recall
- meta-evaluation recall
- architecture design recall
- preference recall
- factual source trace

#### Failure snapshots
For failed or suspicious retrievals, persist compact debug bundles containing:
- query
- classifier result
- source gate result
- top candidates
- final selected items
- dropped relevant candidates

Without this layer, future hardening will stay expensive and partially blind.

---

## 6. Context assembly rules

Context packer should build output by role, not only by score.

### Suggested pack structure

1. `primary_answer_basis`
   - highest-authority core evidence
2. `supporting_context`
   - secondary evidence or orientation notes
3. `task_or_continuation_state`
   - only when request class allows it
4. `citations`
   - direct source refs
5. `omissions_or_uncertainty`
   - what was not observable or not verified

This avoids current failure mode where useful but wrong-lane context crowds out authoritative evidence.

---

## 7. Migration plan

### Phase 1 — observability first
- add retrieval trace records;
- add source family + authority metadata to registry;
- surface excluded-source reasons.

### Phase 2 — source typing migration
- annotate existing sources with canonical family labels;
- keep path heuristics only as validation warnings;
- identify source records with ambiguous family assignment.

### Phase 3 — split admission from ranking
- isolate candidate fetch/admission code;
- isolate authority gating;
- isolate final ranker.

### Phase 4 — shrink compensating logic
- remove obsolete wrapper suppression hacks where source typing solves the issue;
- reduce hardcoded path markers;
- simplify special-case meta-eval patches.

### Phase 5 — runtime health and infra visibility
- explain `openclaw status` timeout;
- explain silent subagent death;
- verify active DB/vector/cache/worker dependencies.

---

## 8. Keep / simplify / rewrite / remove

### Keep
- request-class-based retrieval;
- authority-aware serving;
- token budgets;
- memory lane concept.

### Simplify
- path/title routing heuristics;
- special-case artifact detectors;
- anti-noise patches that duplicate authority semantics.

### Rewrite
- candidate admission;
- structured retrieval trace;
- canonical source registry model;
- final ranking boundary.

### Remove later
- generic handoff substitution in evidence-first lanes;
- noise hacks made obsolete by explicit source typing.

---

## 9. Final architectural verdict

The right direction is **not** to replace the current memory contour with a generic vector-memory stack.

The right direction is to:
- preserve the current policy-aware intelligence,
- formalize it into declared source types and explicit runtime traces,
- and stop relying on filenames and patch-layer heuristics as the hidden schema.

In one sentence:

> Move from heuristic memory orchestration to typed, observable, policy-routed retrieval.
