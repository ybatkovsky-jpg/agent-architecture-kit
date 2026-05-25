# Task 456 — OpenClaw memory contour target runtime architecture and serving contract

Date: 2026-05-13
Task: #456
Parent: #454
Depends on approved specification: `task-manager/artifacts/task-455-openclaw-memory-runtime-contour-improvement-spec-2026-05-13.md`
Primary evidence basis:
- `docs/MEMORY_RUNTIME_AUDIT_LIVE_2026-05-13.md`
- `task-manager/artifacts/task-334-memory-core-v1-schema-and-serving-policy-2026-05-06.md`
- `task-manager/artifacts/openclaw-frame-pass-3-runtime-boundary-summary-2026-05-13.md`

---

## 1. Purpose

This artifact defines the **target runtime architecture** and **serving contract** for the OpenClaw memory contour.

It is narrower than the decision-grade spec in task #455. That spec establishes why the hybrid lexical + typed direction is required. This document locks the **runtime shape**, the **module boundaries**, and the **serving semantics** that downstream implementation work should preserve.

This artifact is intended to be safe for code-splitting and incremental rollout. It makes explicit:
- the lexical backbone boundary;
- the typed Memory Core boundary;
- the retrieval orchestration boundary;
- authority and serving precedence;
- answer-shaping/output contract;
- fallback behavior;
- assumptions vs design choices;
- bounded acceptance checks for this architecture layer.

Core stance:

> The target OpenClaw memory runtime should serve from a **typed, authority-aware Memory Core when eligible**, while keeping the PostgreSQL lexical system as the **evidence backbone, discovery substrate, and resilience fallback**, all bridged through a traceable orchestration layer that can also tolerate the installed-runtime integration seam.

---

## 2. Scope and exclusions

### In scope
- runtime serving architecture for memory retrieval and answer assembly;
- serving precedence across typed objects, lexical evidence, and fallback paths;
- interfaces between retrieval, authority resolution, and answer shaping;
- runtime boundary between workspace-side policy and installed-runtime integration;
- bounded operational checks for this architecture layer.

### Out of scope
- full schema redesign;
- vector/embedding adoption;
- implementation details of every typed object writer;
- UI/tooling specifics outside what the serving contract needs;
- final proof of every installed-runtime code path.

---

## 3. Design inputs: verified assumptions vs deliberate design choices

## 3.1 Verified assumptions from live evidence

The following are treated as verified because they are supported by the live audit and adjacent artifacts.

### A1 — PostgreSQL lexical retrieval is the live operational backbone
Verified by live use of `pkm_memory`, `documents`, `chunks`, `sources`, `ingestion_runs`, `tsvector`, full-text ranking, and trigram similarity.

### A2 — Typed Memory Core exists but is not yet dense enough to replace lexical recall
Verified by the presence and partial population of `mc_*` tables, with far lower density than the lexical corpus.

### A3 — Source-registry gating is a real authority boundary
Verified enabled roots are `memory/`, `task-manager/artifacts/`, and `task-manager/handoffs/`.

### A4 — Retrieval is lane-sensitive
Verified by request-class-specific routing in the current retrieval runtime.

### A5 — DB-first with local fallback is part of the live resilience contour
Verified by the runtime path that prefers PostgreSQL retrieval and falls back to local file walking on failure.

### A6 — Freshness is not guaranteed today
Verified by stale ingestion timestamps relative to audit time.

### A7 — Workspace policy/design is not the whole live system
Supported strongly enough by the pass-3 runtime-boundary summary: workspace retrieval/policy logic is necessary but not sufficient to explain live behavior; an installed runtime/integration seam also materially participates.

## 3.2 Design choices locked by this artifact

The following are not merely observations; they are normative architecture choices.

### D1 — Typed Memory Core is the preferred serving plane, not the only storage plane
Typed objects should become the first candidate for reusable meaning, but never sever themselves from evidence provenance.

### D2 — Lexical retrieval is the evidence backbone and discovery substrate
Lexical search remains first-class and operationally required even after typed-serving promotion.

### D3 — Authority resolution is its own layer
Final serving authority must not remain implicit in SQL ranking or mixed orchestration heuristics.

### D4 — Answer shaping is a contract, not a side effect
Memory-serving outputs must be assembled through a bounded, inspectable output shape.

### D5 — Runtime bridge behavior must be isolated behind a narrow interface
Because live behavior crosses a workspace/runtime seam, downstream code must not smear serving logic directly into prompt-injection or plugin-integration code.

### D6 — Fallback behavior must preserve semantics as much as possible
Fallback may degrade retrieval quality, but should not invent a different authority model.

---

## 4. Target architecture overview

## 4.1 Top-level shape

```text
memory tool / agent request
  -> lane classifier
  -> serving planner
  -> typed candidate fetcher
  -> lexical candidate fetcher
  -> authority resolver
  -> freshness evaluator
  -> serving pack assembler
  -> runtime bridge adapter
  -> consumer-facing answer/context payload
```

The planner may decide to skip or de-emphasize some stages for certain lanes, but the architecture is organized around these explicit seams.

## 4.2 Layer map

```text
Layer 0: Durable source roots
  - MEMORY.md / memory/
  - task-manager/artifacts/
  - task-manager/handoffs/
  - future approved roots

Layer 1: Lexical backbone
  - sources / documents / chunks / ingestion_runs
  - source hashes, section paths, chunk provenance

Layer 2: Typed Memory Core
  - mc_* object families
  - memory notes, session capsules, retrieval documents, typed links

Layer 3: Retrieval orchestration runtime
  - lane classification
  - source/object routing
  - lexical fetch
  - typed fetch
  - authority/freshness resolution
  - serving-pack assembly

Layer 4: Runtime bridge / integration seam
  - adapter from serving pack to tool/runtime consumer
  - prompt/context injection seam
  - policy-preserving transformation only

Layer 5: Consumer surfaces
  - agent memory tool responses
  - continuation packs
  - bounded context payloads for answer assembly
  - trace/debug surfaces
```

## 4.3 Boundary principle

Each layer owns a distinct question:
- **Layer 0**: what durable human-readable material exists?
- **Layer 1**: what approved evidence is indexed and retrievable?
- **Layer 2**: what reusable memory objects have been promoted?
- **Layer 3**: what should be served for this request and why?
- **Layer 4**: how does the runtime consume that result safely?
- **Layer 5**: what does the caller actually receive?

---

## 5. Component responsibilities

## 5.1 Lexical backbone

### Role
The lexical backbone is the **canonical evidence index**.

### Responsibilities
- index approved source content;
- preserve provenance from source root -> document -> chunk/locator;
- support lexical search, ranking, and evidence discovery;
- provide grounding/citation anchors for typed or lexical-serving paths;
- expose freshness metadata for indexed content.

### Non-responsibilities
The lexical backbone must not alone decide:
- final serving authority;
- whether a durable memory conclusion is canonical;
- whether an older typed object should be suppressed by newer evidence;
- prompt/context packaging rules.

### Required interface shape
Input:
- query text;
- lane;
- allowed source roots/families;
- retrieval budget;
- optional task/session scope.

Output:
- ranked lexical candidates with provenance, evidence snippets, freshness state, and retrieval score;
- no final authority claim beyond `operational_index` or `source_of_truth` evidence anchors.

## 5.2 Typed Memory Core

### Role
The typed Memory Core is the **preferred serving authority plane** for reusable meaning.

### Responsibilities
- store compact reusable objects such as memory notes, session capsules, retrieval documents, and typed links;
- encode supersession/expiry/lifecycle state;
- preserve evidence references back to lexical or source-of-truth anchors;
- support lane-aware typed retrieval by scope, object kind, confidence, freshness, and authority.

### Non-responsibilities
The typed Memory Core must not pretend to be:
- the raw source-of-truth store;
- the only retrieval path;
- exempt from evidence freshness or provenance checks.

### Required interface shape
Input:
- lane;
- query text or semantic intent label;
- allowed scopes and object families;
- freshness constraints;
- optional task/session identifiers.

Output:
- eligible typed candidates with object class, confidence, scope, freshness state, supersession state, and evidence refs;
- explicit reason when no eligible typed candidate exists.

## 5.3 Retrieval orchestration runtime

### Role
The orchestration layer is the **decision-making runtime** that converts a request into a bounded serving result.

### Responsibilities
- classify the lane;
- choose source and object families;
- invoke typed and lexical fetchers;
- resolve authority and freshness;
- identify contradictions/open questions;
- assemble the serving pack;
- emit a trace envelope.

### Non-responsibilities
The orchestration layer should not:
- own storage of durable source material;
- mutate prompt/context directly inside retrieval logic;
- collapse into one giant file that hides authority logic inside ranking branches.

## 5.4 Runtime bridge adapter

### Role
The runtime bridge adapter isolates the **workspace policy layer** from the **installed-runtime enforcement/injection layer**.

### Responsibilities
- accept a normalized serving pack;
- preserve authority/freshness/trace metadata across the seam;
- adapt serving output to the specific tool/runtime consumer surface;
- ensure bounded payload size and stable field names;
- avoid policy distortion while crossing into live prompt/context assembly.

### Non-responsibilities
The adapter should not:
- re-rank candidates;
- invent new authority ordering;
- silently drop freshness or conflict metadata without an explicit reason;
- bury the distinction between typed canonical objects and lexical evidence.

---

## 6. Retrieval orchestration modules and code-splitting seams

The architecture should split implementation into narrow modules with explicit contracts.

## 6.1 Lane classifier

Determines request class such as:
- continuation/resume;
- architecture/design recall;
- preference recall;
- policy/decision lookup;
- meta-evaluation recall;
- general evidence-heavy lookup.

Output contract:
```yaml
lane: continuation_resume | architecture_recall | preference_recall | policy_lookup | meta_evaluation | general_lookup
confidence: high | medium | low
rationale: <short explanation>
requested_scope:
  task_id: <optional>
  session_id: <optional>
  project: <optional>
```

## 6.2 Source and object router

Maps lane and scope into allowed source roots and object families.

Output contract:
```yaml
allowed_sources: [memory, task-manager/artifacts, task-manager/handoffs]
allowed_object_families: [session_capsule, memory_note, retrieval_document]
source_biases:
  memory: neutral
  task-manager/artifacts: prefer
  task-manager/handoffs: avoid
reasoning: <short policy explanation>
```

## 6.3 Typed candidate fetcher

Pure retrieval of typed objects. No final ranking beyond typed-local eligibility.

Output contract:
```yaml
typed_candidates:
  - object_id: mem_x
    object_kind: memory_note
    subtype: decision
    authority_class: typed_canonical
    scope: task
    freshness: fresh
    supersession: active
    evidence_refs: [doc_1, ev_2]
    typed_score: 0.91
suppressed_typed_candidates:
  - object_id: mem_old
    reason: superseded
```

## 6.4 Lexical candidate fetcher

Pure retrieval of indexed evidence candidates.

Output contract:
```yaml
lexical_candidates:
  - doc_id: doc_123
    chunk_refs: [c1, c2]
    authority_class: source_of_truth
    freshness: fresh
    lexical_score: 0.88
    source: task-manager/artifacts
    locator: path#line-range
```

## 6.5 Authority resolver

Compares typed and lexical candidates under lane policy.

Responsibilities:
- determine what outranks what;
- enforce supersession and freshness gates;
- decide whether lexical evidence is support-only or primary;
- identify contradictions and unresolved ambiguity.

Output contract:
```yaml
served_items:
  - ref: mem_x
    winner_class: typed_canonical
    why_selected:
      - eligible_for_lane
      - fresher_than_alternatives
      - backed_by_valid_evidence
supporting_evidence: [doc_123]
suppressed_items:
  - ref: mem_old
    reason: superseded_by_mem_x
conflicts: []
open_questions: []
```

## 6.6 Freshness evaluator

This may be integrated with the authority resolver internally, but it must remain separable conceptually and in tests.

Responsibilities:
- check source/index/object freshness states;
- downgrade or warn on stale objects;
- prevent stale typed objects from silently presenting as canonical when contradicted.

Output contract:
```yaml
freshness_summary:
  source_state: fresh | source_changed
  index_state: fresh | index_stale
  typed_state: fresh | typed_needs_revalidation | superseded | expired
warnings: []
```

## 6.7 Serving pack assembler

Produces the bounded response object consumed by the runtime bridge and caller.

### Required properties
- stable shape;
- bounded size;
- machine-readable + operator-readable;
- contains answer-shaping metadata, not just raw hits.

---

## 7. Authority model and serving precedence

## 7.1 Authority classes

The runtime must treat the following authority classes as explicit:

### `source_of_truth`
Raw human-readable source material or canonical artifact/task/handoff evidence.

### `operational_index`
The lexical retrieval/index representation of source content.

### `typed_canonical`
Promoted reusable memory objects intended to represent the best current compact conclusion.

### `derived_runtime_summary`
A request-specific serving pack assembled for one runtime call.

## 7.2 General precedence order

Unless lane-specific rules say otherwise, serve in this order:

1. active, fresh, eligible `typed_canonical` object;
2. active typed object plus lexical supporting evidence;
3. lexical evidence-only serving;
4. local fallback evidence serving if DB path is unavailable.

## 7.3 Lane-specific precedence

### Continuation / resume
Prefer:
1. fresh `session_capsule`;
2. task-scoped `memory_note` or continuation note;
3. task/handoff lexical evidence;
4. broader architecture artifacts only if explicitly requested.

### Architecture / design recall
Prefer:
1. durable architecture `memory_note` decisions/patterns;
2. architecture retrieval documents or normalized recall bundles;
3. stable architecture artifacts as evidence;
4. handoffs only when they hold unique current truth.

### Preference / operating-style recall
Prefer:
1. verified preference `memory_note`;
2. source-backed operator note with high confidence;
3. lexical evidence only when no promoted preference object exists.

### Policy / decision lookup
Prefer:
1. typed decision note;
2. typed decision + authoritative artifact support;
3. authoritative artifact directly when typed note does not exist.

### Evidence-heavy general lookup
Prefer:
1. lexical evidence directly when the request is about finding source material rather than serving a reusable conclusion;
2. typed object only as a summary aid when it helps rather than obscures.

## 7.4 Freshness gate

A typed object may outrank lexical evidence only if all are true:
- not superseded or expired;
- evidence refs still resolve;
- no known newer contradictory source evidence exists without acknowledgment;
- its freshness state is compatible with lane policy.

## 7.5 Conflict rule

When typed and lexical surfaces disagree:
- do not silently collapse them into one answer;
- surface the typed claim, contradictory evidence, and conflict/open-question metadata;
- downgrade typed confidence or serving priority when contradiction is unresolved.

## 7.6 Source authority vs serve authority

The target runtime must distinguish two different questions that are currently too easy to blur together:

### Source authority
Answers: **which durable artifact or record is allowed to count as evidence?**

Examples:
- approved files under `memory/`;
- approved files under `task-manager/artifacts/`;
- approved files under `task-manager/handoffs/`;
- typed objects whose evidence refs resolve back to approved sources.

### Serve authority
Answers: **which candidate is allowed to become the top served answer for this lane?**

Examples:
- `typed_canonical` decision note as top statement for architecture recall;
- lexical artifact evidence as support;
- handoff evidence only when lane policy explicitly permits it or no better current object exists.

### Normative rule
Being admitted as a **source-authoritative evidence input** does **not** automatically grant permission to win **serve authority**.

That distinction is mandatory in the target design and is the main protection against policy drift where an eligible artifact re-enters retrieval and then dominates final serving just because it ranked well lexically or carried a legacy authority label.

## 7.7 Seam-prevention rule derived from task #445

Task #445 verified a concrete leak path in the current runtime:
- `architecture_design_recall` is classified correctly;
- task-anchored handoff-like artifacts under `task-manager/artifacts/` still re-enter;
- they can retain `canonical_handoff` authority;
- final assembly preserves that leaked winner rather than correcting it.

The target architecture must prevent or contain that seam with the following contract.

### Rule P1 — Lane policy must be evaluated before final authority labeling
Authority labels that decide serving precedence must be computed from:
- lane;
- source family;
- object family;
- explicit artifact subtype;
- task/session scope;
- freshness/supersession state.

They must **not** be inherited unchanged from a path-shape heuristic once the lane has changed.

### Rule P2 — Handoff-shaped artifacts inside `task-manager/artifacts/` are not automatically serve-canonical
If an item is task-anchored or handoff-shaped but lives under `task-manager/artifacts/`, the runtime must treat that as:
- a **source classification hint**;
- not a final `serve authority` decision.

For `architecture_recall`, such items default to one of:
- `source_of_truth` evidence; or
- `retrieval_document` / architecture evidence support,

unless a dedicated rule explicitly upgrades them.

### Rule P3 — Architecture lanes must have a handoff containment gate
For `architecture_recall` and adjacent design/policy lanes:
- dedicated handoff roots are excluded by default;
- handoff-like artifacts in general artifact roots may be admitted as evidence;
- but they cannot win final serve authority over architecture decision notes or architecture evidence documents unless they are the only current durable source of the decision.

### Rule P4 — Final assembly is not allowed to preserve illegal winners silently
If upstream ranking still produces a lane-incompatible winner class, the serving-pack assembler or bridge adapter must either:
- demote it before final payload emission; or
- emit an explicit `policy_violation_detected` / `lane_authority_mismatch` trace flag.

Final assembly may preserve trace of the mismatch, but it may not silently preserve the mismatched winner as the unquestioned top result.

### Rule P5 — Authority resolver owns the correction point
The correction for the #445 seam belongs in the explicit authority-resolution contract, not in scattered post-hoc formatting logic.

That means later implementation tasks should fix the leak by centralizing lane-aware serve-authority resolution, while allowing the bridge layer only to preserve or expose the result.

---

## 8. Answer-shaping contract

The serving runtime must return a **bounded serving pack** rather than an unstructured list of hits.

## 8.1 Serving pack shape

```yaml
request:
  id: <run id>
  lane: <lane>
  query: <original or normalized query>
  scope:
    task_id: <optional>
    session_id: <optional>

summary:
  answer_mode: typed_first | lexical_only | fallback_local
  top_statement: <short best answer or recall summary>
  confidence: high | medium | low
  freshness_warning: <optional short warning>

served_memory:
  - ref: mem_x
    kind: memory_note
    subtype: decision
    authority_class: typed_canonical
    statement: <compact served claim>
    why_it_matters: <optional>

supporting_evidence:
  - ref: doc_123
    source: task-manager/artifacts
    locator: path#line-range
    snippet: <short bounded quote or paraphrase>

conflicts:
  - claim_ref: mem_old
    evidence_ref: doc_987
    issue: contradiction | stale | ambiguous_scope

open_questions:
  - <bounded unresolved question>

trace:
  route: db_primary | local_fallback
  selected_sources: []
  selected_object_families: []
  suppression_reasons: []
  timings_ms: {}
  freshness_summary: {}
```

## 8.2 Answer-shaping rules

### Rule S1 — Top statement must be compact
The pack should lead with one compact answer or recall statement, not a transcript replay.

### Rule S2 — Evidence must be bounded
Supporting evidence should be a small set of the most relevant provenance anchors.

### Rule S3 — Trace must survive the bridge
The runtime bridge may compress trace verbosity, but it must preserve enough to explain lane, path, freshness, and suppression.

### Rule S4 — No provenance-free memory serving
Every served conclusion must link either to a typed object with evidence refs or directly to source evidence.

### Rule S5 — No hidden escalation from tentative to canonical
Low-confidence or tentative objects must remain visibly tentative.

### Rule S6 — Caller-facing payload may be thinner than debug payload
The architecture allows a compact default payload and an expanded debug/inspection mode, but both must derive from the same normalized serving pack.

---

## 9. Fallback behavior contract

Fallback is allowed, but it must be disciplined.

## 9.1 Fallback triggers

Fallback should occur only when:
- DB retrieval fails;
- DB is unavailable or unhealthy;
- source-index parity is known broken and local evidence is safer for the lane.

## 9.2 Fallback semantics

Fallback retrieval must still:
- use the same lane classifier and source router;
- produce the same authority classes where possible;
- emit the same serving-pack shape;
- mark route as `local_fallback`;
- expose degraded confidence/freshness when appropriate.

## 9.3 Fallback limitations

Fallback may reasonably lose:
- lexical ranking quality;
- chunk-level scoring consistency;
- some typed/lexical joins if DB-only metadata is unavailable.

Fallback must not lose:
- provenance;
- explicit route disclosure;
- the distinction between source evidence and typed memory.

---

## 10. Runtime bridge and serving boundary

This section exists because the pass-3 boundary summary showed that workspace logic is not the whole live system.

## 10.1 Boundary statement

The architecture must distinguish:

### Workspace policy/design truth
Owns:
- retrieval policy;
- authority ordering;
- lane semantics;
- serving-pack assembly rules.

### Installed runtime/integration truth
Owns:
- final transport into the tool/runtime consumer surface;
- prompt/context injection mechanics;
- runtime-specific adaptation and size enforcement.

## 10.2 Safe interface across the seam

The bridge between them should be:
- narrow;
- typed or schema-validated where practical;
- stable under code-splitting;
- forbidden from reinterpreting authority policy except for explicit, audited transformations.

## 10.3 Bridge input contract

The bridge should receive:
- normalized serving pack;
- trace envelope;
- optional consumer profile indicating compact vs debug shaping.

## 10.4 Bridge output contract

The bridge should return either:
- a compact memory result ready for tool consumption; or
- a structured payload inserted into a broader runtime context envelope.

In both cases, it must preserve:
- lane;
- path used;
- top served items;
- freshness/conflict indicators.

---

## 11. Freshness contract for this architecture layer

This artifact does not implement freshness, but the runtime architecture must make room for it as a first-class input.

## 11.1 Freshness dimensions

### Source freshness
Whether approved source files changed since last scan.

### Index freshness
Whether indexed documents/chunks match current source hashes/content.

### Typed freshness
Whether a typed object still reflects current evidence and has not been superseded.

## 11.2 Serving impact

Freshness must be able to influence:
- typed candidate eligibility;
- suppression reasons;
- warning banners in serving packs;
- fallback preference in exceptional cases.

## 11.3 Minimal freshness vocabulary

- `fresh`
- `source_changed`
- `index_stale`
- `typed_needs_revalidation`
- `superseded`
- `expired`

---

## 12. Clean interfaces for safe code splitting

The following interfaces are the intended stable cut lines.

## 12.1 `classifyLane(request) -> LaneDecision`
Pure classification. No DB access required.

## 12.2 `planServing(laneDecision, requestScope) -> ServingPlan`
Chooses sources, object families, budgets, and fallback policy.

## 12.3 `fetchTyped(plan, query) -> TypedCandidateSet`
Typed-object fetch only.

## 12.4 `fetchLexical(plan, query) -> LexicalCandidateSet`
Lexical-evidence fetch only.

## 12.5 `resolveAuthority(plan, typedSet, lexicalSet, freshness) -> AuthorityDecision`
Single place where precedence is decided.

## 12.6 `assembleServingPack(request, authorityDecision) -> ServingPack`
Single place where output shape is built.

## 12.7 `adaptForRuntime(servingPack, consumerProfile) -> RuntimePayload`
Single place where the workspace/runtime seam is crossed.

## 12.8 Code-splitting rule

A downstream refactor is acceptable if:
- each module can be tested with fixtures;
- authority logic stays centralized;
- bridge adaptation is downstream of serving-pack assembly;
- lexical and typed fetchers can evolve independently.

It is not acceptable if:
- ranking logic silently re-encodes authority in several modules;
- bridge code mutates serving semantics unpredictably;
- fallback path bypasses trace and authority contracts.

---

## 13. Example serving flows

## 13.1 Continuation request

```text
request: "continue task 351"
  -> classifyLane = continuation_resume
  -> planServing prefers session_capsule + task memory_note + handoff/artifact evidence
  -> fetchTyped finds active session capsule
  -> fetchLexical finds current handoff and artifact evidence
  -> resolveAuthority selects session capsule as primary, handoff as support
  -> assembleServingPack returns compact continuation state + blockers + evidence refs
  -> runtime bridge adapts for continuation context injection
```

## 13.2 Architecture recall request

```text
request: "what did we decide about memory authority?"
  -> classifyLane = architecture_recall
  -> planServing prefers decision/pattern memory notes + architecture artifacts
  -> fetchTyped finds architecture decision memory note
  -> fetchLexical finds supporting artifact/spec sections
  -> resolveAuthority serves memory note first, artifacts as grounding evidence
  -> assembleServingPack includes compact decision, support, and any freshness/conflict flags
```

## 13.3 No typed coverage request

```text
request: "find artifacts mentioning X"
  -> classifyLane = general_lookup
  -> planServing biases lexical evidence
  -> fetchTyped returns none eligible
  -> fetchLexical returns ranked documents/chunks
  -> resolveAuthority selects lexical-only path
  -> assembleServingPack marks answer_mode=lexical_only
```

## 13.4 DB failure request

```text
request enters during DB outage
  -> classifyLane and planServing still run
  -> fetchLexical primary path fails
  -> local fallback executes within same source/lane policy
  -> resolveAuthority works over fallback evidence set
  -> assembleServingPack marks route=local_fallback and downgraded confidence
```

---

## 14. Bounded acceptance checks for the architecture layer

### AC1 — Boundary clarity
**Given** this runtime architecture artifact,  
**when** a reviewer inspects it,  
**then** the lexical backbone, typed Memory Core, orchestration runtime, runtime bridge, and consumer surface are distinct layers with named responsibilities.

### AC2 — Lexical backbone role is preserved
**Given** the current live system,  
**when** implementation work is planned from this artifact,  
**then** lexical retrieval remains an evidence backbone and fallback-safe substrate rather than being removed or treated as incidental.

### AC3 — Typed serving role is explicit
**Given** the target contour,  
**when** serving precedence is reviewed,  
**then** typed objects are defined as the preferred serving plane for reusable meaning, with freshness and supersession gates.

### AC4 — Authority resolution is separated from raw retrieval
**Given** future code splitting,  
**when** modules are decomposed,  
**then** lexical fetch, typed fetch, and authority resolution can be tested independently without ambiguity about who decides precedence.

### AC5 — Answer-shaping contract is bounded
**Given** a memory-serving request,  
**when** the serving pack is produced,  
**then** the output shape includes a compact top statement, bounded supporting evidence, conflicts/open questions, and trace metadata.

### AC6 — Fallback behavior is policy-preserving
**Given** DB failure or unavailability,  
**when** local fallback is used,  
**then** the route is disclosed and the same lane/authority/trace semantics remain in force as far as practical.

### AC7 — Runtime seam is explicit
**Given** the pass-3 evidence that workspace logic is not the whole live system,  
**when** this architecture is reviewed,  
**then** a dedicated runtime bridge/interface seam exists between serving-pack assembly and final runtime consumption.

### AC8 — Freshness is first-class in the architecture
**Given** proven stale-ingest risk,  
**when** the architecture is inspected,  
**then** source, index, and typed freshness are modeled as explicit inputs to serving and suppression.

### AC9 — Safe code-splitting is enabled
**Given** the current concentration risk in retrieval logic,  
**when** engineering tasks are cut from this artifact,  
**then** the stable interfaces are narrow enough to move modules independently without rewriting the whole system at once.

---

## 15. Recommended next task cuts from this architecture

1. **Runtime bridge proof task**  
   Prove the live tool/runtime path that consumes the serving pack and identify the concrete installed-runtime seam.

2. **Serving pack schema task**  
   Turn the answer-shaping contract into an implementation-facing JSON schema or typed interface.

3. **Authority resolver extraction task**  
   Centralize precedence logic into one independently testable module.

4. **Typed candidate fetch contract task**  
   Define typed-object eligibility queries and suppression codes.

5. **Freshness envelope task**  
   Add freshness state plumbing into both typed and lexical candidate sets.

6. **Fallback parity fixture task**  
   Create fixtures showing DB-primary and local-fallback results for the same lane.

---

## 16. Final architecture statement

The target OpenClaw memory runtime is a **layered, authority-aware hybrid system**:
- **durable files** remain human-readable roots;
- **PostgreSQL lexical retrieval** remains the evidence backbone;
- **typed Memory Core** becomes the preferred serving plane for reusable conclusions;
- **retrieval orchestration** becomes modular and traceable;
- **runtime bridge adaptation** is isolated behind a narrow seam;
- **fallback** remains available but policy-preserving.

That is the architecture shape that best fits the verified live contour while keeping implementation safe, incremental, and debuggable.
