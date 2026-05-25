# Task 455 — Decision-grade specification for improving the live OpenClaw memory runtime contour

Date: 2026-05-13
Task: #455
Parent: #454
Primary evidence basis: `docs/MEMORY_RUNTIME_AUDIT_LIVE_2026-05-13.md`
Related prior artifacts:
- `task-manager/artifacts/task-409-memory-stack-improvement-spec-2026-05-12.md`
- `task-manager/artifacts/task-334-memory-core-v1-schema-and-serving-policy-2026-05-06.md`
- `task-manager/artifacts/task-440-authoritative-sources-inventory-2026-05-13.md`

---

## 1. Purpose

This document is a **decision-grade execution specification** for improving the **live deployed OpenClaw memory runtime contour** without losing the parts that already work.

It is intentionally grounded in the 2026-05-13 live audit rather than in older planned architecture alone.

Primary goals:
- state the current live contour precisely;
- separate **verified facts** from hypotheses and desired end state;
- define the **target runtime architecture** for a hybrid lexical + typed memory system;
- specify the **serving and authority contract** between the lexical backbone and the typed Memory Core;
- define **freshness, ingestion, retrieval-boundary, and observability** requirements;
- provide a bounded rollout basis that can be decomposed into implementation tasks.

Core stance:

> The system should evolve from a **lexical-first retrieval runtime with a partially active typed overlay** into a **typed-memory-first serving runtime backed by a lexical evidence substrate**, while preserving the current PostgreSQL lexical retrieval backbone as a working safety rail.

---

## 2. Decision summary

### 2.1 What remains unchanged

The following are retained as first-class implementation constraints:
- PostgreSQL remains the main structured backing store.
- `documents` / `chunks` lexical retrieval remains operational and supported.
- file-backed sources remain durable human-readable roots.
- the enabled source-registry model remains the gate for what enters indexed memory.
- request-lane-aware retrieval remains necessary.
- local-file fallback remains allowed initially as a resilience path.

### 2.2 What changes

The following are the required architectural moves:
- typed Memory Core becomes the **preferred serving plane** when typed objects exist;
- lexical retrieval becomes the **evidence and discovery substrate**, not the dominant final serving plane;
- retrieval orchestration is split into narrower components with explicit interfaces;
- freshness becomes visible, enforced, and monitorable;
- memory-serving traces become inspectable per response/run;
- object authority, supersession, and staleness become explicit runtime behaviors rather than mostly schema intent.

### 2.3 Decision statement

**Adopt a transitional hybrid target:**
1. preserve the proven lexical PostgreSQL system;
2. refactor serving so typed objects are authoritative for reusable conclusions;
3. require every memory-serving path to expose lane, source, freshness, and authority trace data;
4. only consider vector/embedding layers after the lexical + typed operating model is stable and measured gaps remain.

---

## 3. Current-state summary from verified live evidence

Per the live audit, the deployed contour is:

> a **hybrid PostgreSQL-backed lexical retrieval system with a partially active typed Memory Core overlay**, plus file-backed markdown/task artifacts as the main durable knowledge roots.

### 3.1 Verified live properties

1. **PostgreSQL is live and central.**
   - Live DB: `pkm_memory`
   - Live structured surfaces include `sources`, `documents`, `chunks`, `ingestion_runs`, and multiple `mc_*` tables.

2. **The main active retrieval path is lexical, not vector-based.**
   - Verified use of `tsvector`, `plainto_tsquery`, `ts_rank_cd`, and trigram similarity.
   - No verified pgvector/embedding runtime use.

3. **Enabled ingestion scope is narrow and source-registry controlled.**
   - Verified enabled roots:
     - `memory/`
     - `task-manager/artifacts/`
     - `task-manager/handoffs/`

4. **The lexical corpus is materially populated.**
   - Observed live counts in the audit: `documents=700`, `chunks=21240`.

5. **The typed Memory Core layer is real but sparse.**
   - Live `mc_*` tables exist and contain some real records.
   - Population is far smaller than the lexical corpus.

6. **Retrieval behavior is lane-aware and policy-routed.**
   - Request classes drive source routing and authority behavior.

7. **The runtime is DB-first with local fallback.**
   - Primary path: PostgreSQL retrieval.
   - Fallback path: local file walking.

8. **Authority shaping exists but is concentrated in application logic.**
   - Conflict handling, citation policy, focus ordering, and bounded evidence shaping happen mainly in retrieval code.

9. **Freshness is not currently guaranteed.**
   - Latest proven ingestion in the audit was stale relative to audit time.

10. **No dedicated recurring memory-maintenance loop was proven live.**
   - General cron infrastructure exists, but a memory-specific always-on refresh/distillation loop was not proven.

### 3.2 Current architecture diagnosis

The live system is not broken in the narrow sense. It already provides useful memory retrieval. The issue is that:
- the lexical layer is doing too much of the practical serving work;
- typed memory exists more as a partial overlay than as the dominant runtime serving plane;
- freshness, traceability, and object-lifecycle enforcement are weaker than the storage design suggests;
- too much serving policy is bundled into one orchestration-heavy runtime file.

---

## 4. Verified constraints and non-negotiables

These constraints are treated as binding unless later disproven by higher-authority runtime evidence.

### 4.1 Operational constraints

- **C1 — PostgreSQL is the required core backing store.**
  Improvement work must not assume replacing the live DB backbone.

- **C2 — Lexical retrieval must continue to work during transition.**
  No redesign may require typed-memory completeness before recall remains useful.

- **C3 — Approved source registry remains the ingestion gate.**
  New serving behavior must still respect enabled source boundaries.

- **C4 — File-backed memory remains durable human-readable authority.**
  The system must continue to support markdown/task-artifact durability and inspectability.

- **C5 — The system is lane-sensitive.**
  Continuation, architecture recall, preference recall, policy lookup, and similar lanes cannot collapse into one flat ranking policy.

- **C6 — Dual-path resilience must be preserved initially.**
  DB-first plus local fallback is allowed during transition, though parity requirements tighten.

### 4.2 Architectural constraints

- **C7 — Typed Memory Core is not yet populated enough to replace lexical retrieval outright.**
- **C8 — Retrieval heuristics currently encode real working behavior and cannot be discarded blindly.**
- **C9 — Runtime observability is incomplete and must improve before aggressive architectural promotion.**
- **C10 — Staleness must be treated as a first-class runtime risk, not an implementation detail.**
- **C11 — The verified architecture-lane contamination seam from task #445 must be treated as an active retrieval-side constraint.**
  For `architecture_design_recall`, implementation work must assume a currently verified leak path: task-anchored handoff-like artifacts under `task-manager/artifacts/` can re-enter architecture recall, retain `canonical_handoff` authority, and survive final envelope assembly. Improvements must repair this seam deliberately rather than treating the drift as only a broad runtime mystery.

### 4.3 Explicit non-goals for this slice

- Not a vector-first redesign.
- Not a rewrite of all memory persistence.
- Not a requirement to type-promote the entire existing corpus before improvements ship.
- Not a claim that transcript or chat residue should become primary authority.

---

## 5. Target architecture

## 5.1 Target statement

Target the following runtime shape:

```text
Memory query/request
  -> lane classifier
  -> serving planner
  -> typed-serving plane (preferred when eligible)
  -> lexical evidence retrieval plane (discovery + support + fallback)
  -> authority resolver
  -> freshness/staleness evaluator
  -> bounded context/evidence pack assembler
  -> trace + answer/context output
```

### 5.2 Architectural layers

#### Layer A — Durable source roots
Includes:
- `memory/`
- `task-manager/artifacts/`
- `task-manager/handoffs/`
- any future approved roots

Role:
- durable human-readable source material;
- externalized inspectable truth surface.

#### Layer B — Lexical evidence backbone
Includes:
- `sources`
- `documents`
- `chunks`
- `ingestion_runs`
- related lexical/index metadata

Role:
- searchable evidence substrate;
- canonical index of approved source content;
- citation and provenance support;
- discovery surface for typed distillation and fallback serving.

#### Layer C — Typed Memory Core
Includes:
- `mc_source_records`
- `mc_evidence_records`
- `mc_memory_notes`
- `mc_retrieval_documents`
- `mc_session_capsules`
- `mc_typed_links`
- related join/supersession/evidence tables

Role:
- compact reusable memory objects;
- authority-bounded serving model;
- preferred runtime plane for durable conclusions, decisions, patterns, and session continuity.

#### Layer D — Serving/orchestration runtime
Role:
- choose lane;
- choose sources and object classes;
- gather typed + lexical candidates;
- resolve authority and freshness;
- assemble bounded outputs.

#### Layer E — Observability and governance
Role:
- explain why a memory response used a given lane/path/source/object;
- expose freshness and suppression reasons;
- support rollout evaluation and no-go decisions.

---

## 6. Roles of lexical backbone vs typed Memory Core

This section is normative.

### 6.1 Lexical backbone role

The lexical PostgreSQL layer is the **evidence backbone**.

It is authoritative for:
- what approved content was indexed;
- which chunks/documents match a retrieval query lexically;
- search-time provenance anchors;
- supporting citations, quotes, and evidence-pack assembly;
- discovery candidates for later typed distillation.

It is **not** the preferred final authority for:
- reusable decisions;
- canonical preferences;
- stable patterns/anti-patterns;
- session continuation summaries;
- compact operator-facing memory serving.

### 6.2 Typed Memory Core role

The typed Memory Core is the **serving authority plane** for reusable meaning.

It is authoritative for:
- compact durable memory notes;
- session capsules and continuation anchors;
- typed relationships between decisions, evidence, tasks, and patterns;
- supersession/expiry state for promoted knowledge;
- “what should be served” rather than merely “what matched”.

It is **not** a replacement for raw evidence storage. It remains backed by lexical/file evidence and must preserve provenance links.

### 6.3 Transitional principle

Until typed coverage is broad enough, the serving model is:
- **typed-first when typed objects exist and are eligible**;
- **lexical-backed when typed coverage is missing or insufficient**;
- **never provenance-free**.

### 6.4 Practical object expectations

At minimum, the typed serving plane must become reliable for:
- `memory_note` for durable decisions, preferences, patterns, blockers;
- `session_capsule` for active/recent continuation state;
- `retrieval_document` for normalized recall bundles when direct memory notes are not appropriate.

---

## 7. Serving and authority model

This section defines the runtime contract for what may be served and why.

### 7.1 Serving precedence

For any request lane, serving should prefer in this order:

1. **Active typed objects with valid freshness/authority**
   - active `memory_note`
   - active `session_capsule`
   - active `wiki_page` or equivalent typed synthesis if present

2. **Typed objects plus lexical supporting evidence**
   - when typed object exists but needs evidence grounding/citations

3. **Lexical retrieval-only serving**
   - when no adequate typed object exists
   - or when the lane is inherently evidence-heavy

4. **Local fallback retrieval**
   - only when DB retrieval fails or is unavailable

### 7.2 Authority classes

Every served item should be assigned one of these practical authority classes:
- `source_of_truth` — raw evidence/file/task artifact authority
- `typed_canonical` — promoted reusable memory object
- `operational_index` — retrieval/index representation
- `derived_runtime_summary` — bounded assembled serving pack for a specific request

### 7.3 Lane-specific authority guidance

#### Continuation / resume lane
Prefer:
- recent `session_capsule`
- task/handoff-specific `memory_note`
- handoff lexical evidence

Disallow:
- broad architecture artifacts outranking fresh task continuity unless explicitly requested.

#### Architecture / design recall lane
Prefer:
- durable `memory_note` decisions/patterns
- stable architecture artifacts
- synthesis pages if present

De-emphasize:
- ephemeral handoffs unless they contain the only current truth.

#### Preference / operating-style lane
Prefer:
- verified preference `memory_note`
- high-confidence operator notes

Disallow:
- speculative inference from one-off artifacts unless explicitly marked tentative.

#### Policy / decision lookup lane
Prefer:
- typed decisions with backing evidence
- authoritative artifacts directly if no typed decision exists

### 7.4 Freshness gate inside serving

A typed object may outrank lexical evidence only if:
- it is not expired/superseded;
- its source references are valid;
- it is not older than relevant newer contradictory source evidence without acknowledgment.

### 7.5 Bounded output requirement

Every runtime serving result must remain bounded and should return:
- small set of served memory objects;
- small supporting evidence set;
- conflicts/open questions if unresolved;
- trace metadata.

The goal is not exhaustive replay but decision-useful recall.

---

## 8. Freshness and ingestion policy

This section is normative.

### 8.1 Freshness problem statement

The audit proved that the corpus can become stale relative to live files. Therefore freshness cannot remain an implicit operational assumption.

### 8.2 Required ingestion policy

The system should implement a visible freshness policy with three levels:

#### F0 — Source freshness
For each enabled root, track:
- last indexed timestamp;
- newest source file timestamp seen during last scan;
- count of changed/new/deleted documents since prior ingest.

#### F1 — Lexical index freshness
For each document and chunk set, track whether indexed content matches current source content hash.

#### F2 — Typed object freshness
For each typed object, track whether backing evidence changed after object generation or last validation.

### 8.3 Minimum automation target

At minimum, the runtime should support:
- manual on-demand ingest;
- scheduled periodic ingest for enabled roots;
- a typed-object revalidation sweep for objects whose source evidence changed;
- surfaced stale flags in retrieval/serving output.

### 8.4 Freshness status vocabulary

Use practical states such as:
- `fresh`
- `index_stale`
- `source_changed`
- `typed_needs_revalidation`
- `superseded`
- `expired`

### 8.5 Runtime freshness behavior

When stale conditions exist:
- results remain retrievable if necessary;
- but outputs must expose freshness warnings;
- typed objects with unresolved stale backing evidence must not silently present as fully canonical.

### 8.6 Distillation/ingestion policy separation

Keep these flows separate:
- **ingest** = index source content into lexical backbone;
- **distill/promote** = create/update typed objects from evidence;
- **serve** = answer request using current typed + lexical state.

This separation is important so freshness bugs do not hide behind one monolithic script.

---

## 9. Retrieval refactor boundaries

The live audit identified retrieval-logic concentration as a major maintainability risk. This section defines bounded refactor seams.

### 9.1 Required runtime modules

The current orchestration should be split conceptually into:

1. **Lane classifier**
   - infer request class;
   - expose confidence and rationale summary.

2. **Source and object router**
   - choose allowed roots and object families by lane.

3. **Lexical candidate fetcher**
   - SQL/full-text/trigram retrieval only;
   - no final authority decisions.

4. **Typed candidate fetcher**
   - fetch eligible `mc_*` objects by lane, scope, freshness, and authority.

5. **Authority resolver**
   - compare typed vs lexical candidates;
   - apply freshness/supersession constraints;
   - identify conflicts.

6. **Serving pack assembler**
   - build bounded context pack / evidence pack;
   - attach citations and references.

7. **Trace emitter**
   - persist or return structured explanation of chosen path.

### 9.2 Boundary rules

- SQL retrieval logic should not also decide final serving authority.
- lane classification should not be hidden inside ranking heuristics only.
- fallback handling should reuse the same authority and trace layers where possible.
- typed-object retrieval should be independently testable from lexical retrieval.
- synthesis of conflicts/open questions should consume normalized candidate structures, not raw ad hoc branch outputs.

### 9.3 Compatibility constraint

Refactor work must preserve current external behavior enough to:
- keep existing retrieval smoke tests meaningful;
- avoid requiring a full tool-bridge rewrite first;
- support gradual promotion of typed objects lane by lane.

---

## 10. Observability and trace contour

The live contour lacks enough explainability for confident operational debugging. This must change.

### 10.1 Required per-response trace envelope

Every memory-serving response should be able to surface a compact machine-readable trace containing at least:
- request ID / run ID;
- request lane;
- selected sources;
- selected object families;
- DB vs local path used;
- freshness summary;
- typed objects considered/served;
- lexical candidates considered/served;
- authority winner reasons;
- suppressed candidates and suppression reasons;
- conflicts/open questions;
- elapsed timing by stage.

### 10.2 Required persistent observability surfaces

Maintain inspectable records for:
- ingest runs;
- typed distillation/promotion runs;
- serving traces for bounded recent history;
- stale-object counts by source and object family;
- lane-level serving composition (typed-first vs lexical-only vs fallback).

### 10.3 Primary operational dashboards/reports

At minimum, produce inspectable summaries for:
- index freshness by source root;
- typed coverage by lane/object family;
- fallback rate;
- stale typed object count;
- lexical-only answer rate;
- top suppression/failure reasons.

### 10.4 Debugging outcome requirement

For any surprising memory answer, an operator should be able to determine:
- what lane was selected;
- what candidates were available;
- why one item outranked another;
- whether freshness or source policy affected the answer.

---

## 11. Rollout phases

This rollout is intentionally staged.

### Phase 0 — Baseline hardening and evidence lock

Goal:
- freeze the decision basis around the live audit and current retrieval behavior.

Deliverables:
- this spec approved;
- authoritative runtime/source inventory for memory path confirmed;
- bounded regression fixtures capturing current lane behavior;
- explicit freshness report for enabled roots.

Exit gate:
- current lexical behavior is reproducible enough to compare future changes.

### Phase 1 — Freshness and trace foundation

Goal:
- make the current hybrid system observable before major serving changes.

Deliverables:
- ingest freshness metadata surfaced;
- scheduled/triggered ingest policy implemented or documented as active mechanism;
- structured serving trace envelope added;
- stale flags available in runtime outputs.

Exit gate:
- operator can explain a memory response and detect stale-index conditions.

### Phase 2 — Retrieval boundary refactor

Goal:
- split orchestration responsibilities without changing serving philosophy yet.

Deliverables:
- modular lane classifier/router/fetcher/authority/assembler structure;
- lexical and typed fetchers independently testable;
- fallback path normalized under shared authority/trace logic.

Exit gate:
- retrieval runtime is maintainable enough for typed-first promotion.

### Phase 3 — Typed-serving promotion

Goal:
- make typed Memory Core the preferred serving plane for selected lanes.

Initial promotion candidates:
- continuation/resume;
- policy/decision lookup;
- preference recall;
- architecture/design recall where durable decisions exist.

Deliverables:
- typed eligibility rules;
- lane-by-lane precedence policy;
- stale/superseded guardrails;
- typed coverage reports.

Exit gate:
- measurable share of responses in target lanes serve through typed objects first without regression in usefulness.

### Phase 4 — Typed coverage expansion and lifecycle enforcement

Goal:
- improve typed object density and hygiene.

Deliverables:
- stronger distillation/promotion flows;
- revalidation/supersession workflows;
- better task/handoff/session capsule population discipline.

Exit gate:
- typed layer is not merely present but operationally significant.

### Phase 5 — Optional semantic augmentation decision

Goal:
- decide whether vectors/embeddings are justified.

Condition:
- only after lexical + typed-first architecture is stable and measured.

Possible outputs:
- no vector layer needed;
- narrow vector augmentation for paraphrase/concept recall;
- deferred pending stronger typed coverage.

---

## 12. Risks and no-go conditions

### 12.1 Major risks

#### R1 — Premature typed-first promotion
If typed coverage remains too sparse, forcing typed-first globally may reduce recall quality.

Mitigation:
- lane-by-lane rollout;
- lexical fallback preserved;
- typed coverage metrics required.

#### R2 — Freshness blindness
A stronger serving plane is dangerous if stale objects silently outrank newer evidence.

Mitigation:
- stale gating;
- typed-object revalidation policy;
- surfaced warnings.

#### R3 — Refactor regression in working lexical retrieval
The current retrieval logic is ugly but operationally useful. A clean refactor can still break behavior.

Mitigation:
- fixture pack based on current live lanes;
- stage-by-stage parity checks;
- no big-bang rewrite.

#### R4 — Trace overhead or operator overload
Observability can become too verbose or costly.

Mitigation:
- compact default trace envelope;
- deeper traces only when requested or sampled.

#### R5 — Authority confusion between source, lexical index, and typed note
If serving semantics are not explicit, the system will continue to blur “matched text” and “approved reusable memory.”

Mitigation:
- explicit authority classes;
- typed object eligibility rules;
- provenance requirements.

#### R6 — Verified architecture-lane contamination remains unrepaired
Task #445 proved a concrete retrieval-side seam: architecture recall can still be contaminated by task-anchored handoff artifacts re-entering from `task-manager/artifacts/`, keeping `canonical_handoff` authority, and then being preserved by final envelope assembly.

Mitigation:
- treat architecture-lane purity as an explicit regression target;
- separate source routing, authority inference, and final assembly checks;
- require trace output to expose when `canonical_handoff` survives in architecture/design lanes;
- prioritize this seam early in retrieval-boundary work before broader runtime speculation.

### 12.2 No-go conditions

Do **not** advance typed-first serving broadly if any of these remain true:
- NG1 — freshness status cannot be surfaced reliably;
- NG2 — typed objects cannot be checked for supersession/expiry/backing-evidence validity;
- NG3 — lane routing behavior is not reproducible enough for regression testing;
- NG4 — fallback and DB paths produce materially unexplained divergence;
- NG5 — operator cannot inspect why a specific memory answer was served.

### 12.3 Rollback principle

At every rollout phase, it must remain possible to:
- fall back to lexical-serving-first behavior for affected lanes;
- disable typed precedence selectively by lane;
- continue ingest and evidence retrieval even if typed promotion logic is temporarily disabled.

---

## 13. Bounded acceptance checks

These checks are written so downstream implementation can prove this spec was met.

### AC1 — Current-state fidelity
**Given** the 2026-05-13 live audit,  
**when** this spec is reviewed,  
**then** it accurately states that the current live system is PostgreSQL-backed, lexical-first, source-registry-gated, DB-first with local fallback, and only partially populated in typed Memory Core.

### AC2 — Unchanged vs redesigned boundary
**Given** the transitional hybrid contour,  
**when** the design basis is inspected,  
**then** it clearly distinguishes what remains unchanged (PostgreSQL lexical backbone, source registry, file roots, lane-aware retrieval) from what is redesigned (typed-serving precedence, freshness discipline, observability, modular retrieval runtime).

### AC3 — Lexical backbone preservation
**Given** the current working retrieval system,  
**when** implementation tasks are cut from this spec,  
**then** none require disabling lexical retrieval as a prerequisite for improvement.

### AC4 — Typed-serving target defined
**Given** the partial typed overlay today,  
**when** the target architecture is reviewed,  
**then** the spec defines a first-class typed-memory serving target with provenance, freshness, supersession, and lane-specific precedence rules.

### AC5 — Freshness policy explicit
**Given** proven stale-ingest risk,  
**when** the freshness section is inspected,  
**then** source freshness, index freshness, and typed-object freshness are all explicitly defined.

### AC6 — Retrieval refactor seams explicit
**Given** `retrieve_memory.py` concentration risk,  
**when** engineering planning begins,  
**then** the spec provides modular boundaries for classifier, router, lexical fetcher, typed fetcher, authority resolver, assembler, and trace emitter.

### AC7 — Traceability requirement explicit
**Given** runtime observability gaps,  
**when** the observability contour is inspected,  
**then** the spec requires per-response lane/source/path/freshness/authority trace output.

### AC8 — Rollout is bounded and gated
**Given** implementation uncertainty,  
**when** teams decompose the work,  
**then** they can slice the work into phased tasks with explicit no-go conditions and rollback principles.

### AC9 — Decision usefulness
**Given** this document is meant to be decision-grade,  
**when** a reviewer asks whether to invest in freshness + typed-serving + observability before vector search,  
**then** the spec answers yes and explains why.

---

## 14. Recommended immediate task cuts

The following bounded follow-up tasks are implied by this spec:

1. **Authoritative runtime bridge audit for memory tools**
   - prove the exact live call chain from memory tool invocation to retrieval serving path.

2. **Freshness status implementation task**
   - expose per-source and per-object freshness state.

3. **Serving trace envelope task**
   - add per-response structured trace output.

4. **Retrieval modularization task**
   - split current orchestration into bounded modules without changing top-level behavior first.

5. **Typed-serving pilot for one lane**
   - likely continuation/resume or decision lookup first.

6. **Typed coverage and revalidation policy task**
   - define how and when typed objects are created, refreshed, superseded, or expired.

7. **Fallback parity test task**
   - verify DB-first and local fallback produce explainable comparable behavior.

---

## 15. Final recommendation

Approve this specification as the basis for the next improvement wave **if the project wants a safer, inspectable, typed-memory-forward runtime without discarding the working lexical system**.

Do not jump directly to vectorization or to a full typed-memory-only serving model.

The correct next move is:
1. observability and freshness first,
2. retrieval modularization second,
3. typed-serving promotion third,
4. semantic augmentation only if measured gaps remain.

That sequence best matches the verified live contour and minimizes regression risk.

---

## 16. Review-close verification note

Review status: **review-closed on 2026-05-13**.

Claim:
- this spec is decision-grade and sufficient to drive bounded downstream work for the memory runtime improvement program.

Evidence:
- it states the unchanged vs redesigned boundary;
- it defines a typed-memory-first target without requiring lexical shutdown;
- it distinguishes verified findings, rollout phases, risks, no-go conditions, and acceptance checks;
- downstream child tasks #456/#457/#459/#460/#461/#462 map cleanly to sections of this spec;
- the verified seam from task #445 is now captured explicitly as constraint **C11** and risk **R6**.

Verification basis:
- reviewed against task #455 acceptance criteria;
- cross-checked with `task-manager/artifacts/task-445-runtime-seam-inspection-bounded-v2-2026-05-13.md`;
- cross-checked with `task-manager/artifacts/openclaw-frame-pass-3-runtime-boundary-summary-2026-05-13.md` and `task-manager/artifacts/openclaw-frame-runtime-boundary-map-2026-05-13.md` to keep the layered-model stance while making the verified retrieval seam concrete.
