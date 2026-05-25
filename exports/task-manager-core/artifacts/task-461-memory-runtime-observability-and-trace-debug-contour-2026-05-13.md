# Task 461 — Memory runtime observability and trace/debug contour for answer decisions

Date: 2026-05-13
Task: #461
Parent: #454
Depends on:
- `task-manager/artifacts/task-455-openclaw-memory-runtime-contour-improvement-spec-2026-05-13.md`
- `task-manager/artifacts/task-456-openclaw-memory-runtime-architecture-and-serving-contract-2026-05-13.md`
- `task-manager/artifacts/task-457-openclaw-memory-freshness-and-ingestion-policy-2026-05-13.md`
- `task-manager/artifacts/task-459-typed-memory-core-first-class-serving-plane-2026-05-13.md`
- `task-manager/artifacts/task-460-retrieval-orchestration-bounded-modules-refactor-plan-2026-05-13.md`
Primary evidence basis:
- `docs/MEMORY_RUNTIME_AUDIT_LIVE_2026-05-13.md`
- `pkm-memory/retrieve_memory.py`

---

## 1. Purpose

This artifact defines a **decision-grade runtime observability contour** for OpenClaw memory answers.

It covers:
- the trace model for memory decision-making;
- operator debug surfaces for routine diagnosis and bounded incident review;
- redaction and safety rules so traceability does not become a data leak;
- retention and verbosity policy so the system remains inspectable without turning into an unbounded logging plane;
- rollout sequencing and bounded acceptance checks.

Core stance:

> Every memory answer should be explainable through a bounded trace that shows how the runtime classified the request, chose sources, ranked candidates, assembled the serving pack, handled fallback and freshness, and shaped the final answer — without requiring operators to reverse-engineer the whole runtime from raw code or unsafe full payload logs.

---

## 2. Decision summary

### 2.1 Verified current-state facts

The following are treated as verified from the live audit and predecessor artifacts:

1. The live memory contour is **DB-first, lexical-first, and lane-aware**.
2. The main operational retrieval path runs through `pkm-memory/retrieve_memory.py` and mixes classification, routing, ranking, authority shaping, trace synthesis, and fallback logic.
3. The runtime already emits some decision-related metadata such as routing, provenance, authority-layer notes, conflicts, and open questions, but observability is **partial and uneven**, not a bounded first-class trace model.
4. Typed Memory Core tables exist, but typed serving is currently sparse relative to the lexical corpus.
5. Freshness is a real runtime risk because latest proven ingest was stale relative to audit time.
6. Local fallback exists and can materially change which evidence is seen.
7. The live contour crosses a workspace/runtime seam, so some behavior is not safely inspectable by reading one file alone.

### 2.2 Normative design choices locked by this artifact

1. **A memory decision trace becomes a first-class runtime object.**
2. **The trace must separate facts observed during execution from policy verdicts and answer-shaping decisions.**
3. **Trace detail must be tiered** so normal serving stays cheap while deep debug remains available on demand.
4. **Redaction is mandatory by default** for raw content, prompt fragments, personal data, secrets, and unsafe file payloads.
5. **Fallback and stale-state behavior must be visible**, not implicit.
6. **Observability must align to the target modular architecture** from task #460 rather than reinforce the current monolith.

### 2.3 Outcome sought

After rollout, an operator should be able to answer, for any inspected memory response:
- what lane/classification the runtime chose and why;
- which source families and retrieval paths were eligible, preferred, excluded, or used;
- which typed and lexical candidates were considered and why winners outranked losers;
- whether freshness or fallback changed the decision;
- what final answer-shaping constraints were applied;
- what data is intentionally hidden/redacted from the trace.

---

## 3. Scope and exclusions

### In scope
- runtime decision trace schema;
- event model for classification, source selection, ranking, serving-pack assembly, fallback, freshness, and final shaping;
- operator-facing debug surfaces;
- redaction, retention, and verbosity rules;
- rollout guidance and acceptance checks.

### Out of scope
- full metrics platform design;
- unrelated application-wide logging policy;
- full typed-writer implementation;
- vector-search observability;
- end-user UI redesign beyond debug needs.

---

## 4. Fact/design split

## 4.1 Verified current-state facts

### F1 — There is already some trace-like output, but not an explicit decision-trace contract
Evidence from the live audit and current retrieval code shows routing, provenance, conflicts, and open-question synthesis, but not a stable end-to-end trace schema with consistent event identities and verbosity tiers.

### F2 — Classification, routing, ranking, fallback, and envelope assembly are currently co-located
Task #460 verified that these responsibilities currently sit largely in `retrieve_memory.py`, making diagnosis possible but expensive and regression-prone.

### F3 — Freshness and fallback can change answer quality materially
Task #457 and the live audit verify stale ingest risk and DB-first/local-fallback behavior.

### F4 — Typed objects are not yet dense enough to dominate all traces
The observability design must work for lexical-only, typed-first, and mixed answers.

### F5 — Some runtime behavior crosses an installed-runtime boundary
Observability must tolerate the bridge seam rather than assume every transformation occurs in one directly owned workspace file.

## 4.2 Normative design choices

### D1 — Use one canonical trace envelope with stage events
Rather than bespoke ad hoc logs per function, define one top-level trace envelope plus bounded stage events.

### D2 — Trace should explain decisions, not mirror every internal detail
The goal is operator understanding and bounded replay reasoning, not byte-for-byte execution capture.

### D3 — Observability should be useful at three levels
- **response-inline**: very small explanation hints safe to include in normal output metadata;
- **operator-summary**: bounded debug summary for routine diagnosis;
- **deep-trace**: fuller event stream for targeted incident analysis.

### D4 — Redaction-first by default
Only hashes, IDs, locators, snippets under policy, and bounded rationale summaries should appear unless a stronger operator/debug mode explicitly allows more.

---

## 5. Trace model

## 5.1 Top-level trace envelope

Each memory-serving run should be able to produce a `memory_decision_trace` object with this conceptual shape:

```json
{
  "trace_id": "memtrace_...",
  "request_id": "...",
  "timestamp": "2026-05-13T...Z",
  "runtime_version": "...",
  "policy_version": "...",
  "trace_level": "inline|summary|deep",
  "mode": "auto|psql|local|typed_hybrid",
  "status": "success|partial|fallback|failed",
  "request": { ... },
  "classification": { ... },
  "plan": { ... },
  "stages": [ ... ],
  "final_decision": { ... },
  "redaction": { ... },
  "retention": { ... }
}
```

## 5.2 Required top-level fields

### Request block
Must include:
- `query_hash` or bounded normalized query form;
- raw query only when policy allows and trace mode explicitly requests it;
- actor/session/task scope if available;
- requested lane if caller supplied one;
- backend mode requested (`auto`, `psql`, `local`, future typed hybrid);
- debug flag source if deep trace was explicitly requested.

### Classification block
Must include:
- chosen lane/request class;
- classifier confidence bucket or score;
- top alternative classes within a bounded list;
- rationale signals as tags, not chain-of-thought prose;
- citation expectation;
- authority-priority intent;
- retrieval budget class.

### Plan block
Must include:
- eligible retrieval planes: `typed`, `lexical_psql`, `local_fallback`;
- selected primary path;
- excluded paths with reasons;
- source-family allow/exclude list;
- planned fetch budget and rerank budget;
- freshness policy hook chosen for the lane.

### Final decision block
Must include:
- winning serve path;
- whether typed objects were used, advisory, or bypassed;
- whether lexical evidence was primary, supporting, or replacement;
- whether fallback happened;
- whether stale-state warnings affected rank or envelope;
- final answer-shaping mode;
- top cited/supporting refs;
- final safety/redaction actions.

---

## 6. Stage event schema

Each `stages[]` item should be a bounded event with:
- `stage`: stable enum;
- `started_at` / `ended_at`;
- `status`: `success|partial|skipped|failed`;
- `inputs_summary`;
- `decision_summary`;
- `artifacts`: IDs, counts, hashes, candidate refs, warnings;
- `policy_refs`: stable rule names / policy keys;
- `redaction_class`: what content suppression policy applied.

The trace must not require preserving full raw payloads from every stage.

## 6.1 Classification event

`stage = classification`

Required fields:
- normalized request hash;
- selected lane;
- alternatives considered;
- cue tags used (examples: `resume_phrase`, `task_id_present`, `architecture_term`, `preference_request`);
- confidence;
- ambiguity flags;
- operator warning when lane confidence falls below threshold.

Acceptance intent:
An operator can see whether the wrong answer began with a bad lane classification.

## 6.2 Source-selection / planning event

`stage = source_selection`

Required fields:
- allowed source roots / families;
- excluded roots / families;
- exclusion reasons, especially for handoffs in architecture/meta lanes;
- backend eligibility (`typed`, `psql`, `local`);
- budget settings;
- task/session scoping decisions;
- explicit note when installed-runtime bridge policy altered the planned set.

Acceptance intent:
An operator can see why a source was never considered, not only why a candidate lost later.

## 6.3 Candidate fetch events

Separate stage types are preferred:
- `typed_fetch`
- `lexical_fetch`
- `local_fallback_fetch`

Required fields for each:
- requested budget;
- returned candidate count;
- latency bucket;
- failure or degradation cause if partial;
- candidate families present;
- top candidate refs with scores in bounded form;
- freshness metadata attached/not attached;
- provenance completeness summary.

Normative rule:
When one plane is skipped, the trace must say whether it was **ineligible**, **empty**, **failed**, or **policy-disabled**.

## 6.4 Ranking and authority-resolution event

`stage = ranking_authority`

Required fields:
- pre-rank candidate counts by plane;
- main scoring components used;
- authority ordering applied;
- freshness demotions/promotions;
- supersession suppression;
- contradiction/conflict flags;
- diversity shaping actions;
- canonical winner locks, if any;
- top winner/runner-up explanation in bounded structured form.

This stage is where the trace must answer:
- why the winner won;
- why a seemingly obvious candidate did not win;
- whether policy or raw retrieval score dominated.

## 6.5 Serving-pack assembly event

`stage = serving_pack_assembly`

Required fields:
- final top-N selected items;
- answer envelope type;
- cited facts count;
- supporting refs count;
- omitted-but-near-miss candidate count;
- trace of pack compaction decisions;
- note if local fallback evidence was downgraded for weaker provenance.

## 6.6 Fallback event

`stage = fallback`

This event should appear only when relevant, but when present must state:
- fallback trigger (`db_exception`, `typed_empty`, `typed_stale_block`, `policy_bypass`, `ingest_stale_guard`, etc.);
- from-path and to-path;
- whether semantic parity is expected or degraded;
- operator severity (`info`, `warning`, `high`);
- whether user-visible caution should be added.

## 6.7 Freshness evaluation event

`stage = freshness`

Required fields:
- source-root freshness states for involved roots;
- typed-object freshness / evidence freshness relation;
- stale thresholds used for the lane;
- known pending-change or stale-ingest indicators if available;
- final freshness verdict per winning item;
- serving consequence (`none`, `warn`, `demote`, `fallback`, `block`).

## 6.8 Final answer-shaping event

`stage = answer_shaping`

Required fields:
- final surface type (continuation pack, concise lookup summary, architecture evidence pack, etc.);
- inclusion/exclusion rationale for refs exposed to the caller;
- user-visible caveats inserted or suppressed;
- citation mode actually used;
- final redaction decisions;
- any bridge-adapter transformations applied after serving-pack assembly.

This event answers the common operator question: “The right evidence existed — why did the final answer still look the way it did?”

---

## 7. Trace-specific handling for typed + lexical hybrid serving

## 7.1 Required hybrid distinctions

The trace must distinguish at least these cases:

1. **typed-primary, lexical-supporting**
2. **typed-candidate rejected, lexical-primary**
3. **typed-empty, lexical-primary**
4. **typed-primary but stale-warning attached**
5. **lexical-primary with no typed eligibility**
6. **fallback-local after DB or typed path failure**

## 7.2 Rejection reasons for typed candidates

When typed candidates do not serve, trace reasons should use stable enums such as:
- `no_candidate`
- `insufficient_evidence`
- `stale_evidence`
- `superseded`
- `lane_ineligible`
- `scope_mismatch`
- `lower_authority_than_source`
- `debug_disabled_due_to_redaction_policy`

## 7.3 Rejection reasons for lexical candidates

Similarly, lexical losers should be explainable by bounded reasons such as:
- `lower_rank`
- `freshness_demoted`
- `handoff_excluded_for_lane`
- `wrapper_meta_suppressed`
- `duplicate_document_diversity_limit`
- `weaker_provenance`
- `contradicted_by_higher_authority`

---

## 8. Operator debug surfaces

This section is normative.

## 8.1 Surface A — Inline response metadata

Purpose:
- safe default visibility for consumers and light debugging.

Should expose only:
- `trace_id`
- chosen lane
- winning path (`typed`, `psql`, `local_fallback`, `hybrid`)
- freshness summary (`fresh`, `aging`, `stale_warning`)
- fallback flag
- citation count / support count

Must not expose raw content, full candidate lists, or hidden policy internals.

## 8.2 Surface B — Operator summary view

Purpose:
- default human/operator inspection surface.

Should show:
- request summary;
- lane/classification confidence;
- source-plan summary;
- winners and near-misses;
- fallback and freshness warnings;
- final shaping decision;
- links/IDs to deeper trace artifacts if retained.

Format may be JSON or rendered markdown, but it must preserve stable fields.

## 8.3 Surface C — Deep trace event view

Purpose:
- incident analysis and regression debugging.

Should show:
- ordered stage events;
- candidate IDs and score components in bounded form;
- policy refs;
- suppression reasons;
- bridge-adapter transformations;
- explicit redaction markers where content is hidden.

Deep trace should be gated by operator intent, sampling policy, or debug mode — not emitted by default on every call.

## 8.4 Surface D — Aggregate operational counters

Purpose:
- detect systematic drift without inspecting single traces one by one.

Recommended counters:
- lane distribution;
- typed-primary rate;
- typed-rejected-by-reason distribution;
- fallback rate by trigger;
- stale-warning rate by lane;
- source-root exclusion frequency;
- no-result / weak-result rate;
- average candidate counts and latency buckets by stage.

This artifact does not require a full metrics stack immediately, but these counters define the minimum direction.

## 8.5 Surface E — Bounded replay fixture export

Purpose:
- support regression tests and targeted review.

A fixture export should include:
- normalized request;
- selected trace summary;
- stable candidate refs / hashes;
- final decision verdict;
- redacted supporting snippets when allowed.

It should exclude secrets, large raw files, and unrestricted personal content.

---

## 9. Redaction and safety rules

This section is mandatory.

## 9.1 Default trace principle

Traceability is subordinate to safety. If a field is not needed to explain the decision, do not log it.

## 9.2 Always-redact or hash-by-default fields

The following should be redacted, hashed, or replaced by stable IDs by default:
- raw user query text when it contains secrets, credentials, personal identifiers, or long pasted content;
- raw file bodies;
- prompt/context payloads sent to downstream models;
- access tokens, URLs with secrets, cookies, auth headers;
- personal data not needed for debugging the retrieval decision;
- content from excluded/private roots if those roots later exist;
- full local fallback file dumps.

## 9.3 Bounded snippet policy

Allowed in summary/deep traces only when safe:
- short evidence snippets around cited spans;
- max length should be capped by policy;
- snippets should prefer source-backed artifacts over transient prompt text;
- secrets and structured identifiers inside snippets must be masked.

## 9.4 Redaction markers

The trace should indicate **that** content was hidden and **why**, using markers like:
- `redacted_secret`
- `redacted_personal_data`
- `redacted_prompt_payload`
- `redacted_large_content`
- `redacted_policy_restricted`

This prevents the false impression that evidence was absent when it was merely suppressed.

## 9.5 Safety rules for local fallback

Because local fallback can touch raw files directly, traces from this path require stricter rules:
- log paths/locators and file hashes before snippets;
- snippets only when explicitly safe;
- no full-file inclusion;
- flag lower provenance confidence if fallback bypassed indexed metadata.

## 9.6 Operator access principle

Deep traces are for bounded operational use. They should not become a general browsing surface for all memory content.

---

## 10. Retention and verbosity guidance

## 10.1 Verbosity tiers

### Tier 0 — none / failure-only
Use for hot paths if cost pressure requires it temporarily.
Only critical failures and severe fallback events retained.

### Tier 1 — summary default
Recommended steady-state baseline.
Retain top-level trace envelope, stage summaries, winner/loser reasons, and redaction markers.

### Tier 2 — sampled deep trace
Retain fuller stage events for sampled requests, canary lanes, explicit debug sessions, or failures.

### Tier 3 — incident deep trace
Temporary short-lived escalation for bounded investigations.
Must be explicitly enabled and automatically expire.

## 10.2 Retention windows

Normative starting guidance:
- inline response metadata: tied to response artifact lifecycle;
- operator summaries: retain longer than deep traces because they are safer and cheaper;
- sampled deep traces: short retention by default;
- incident traces: shortest retention, with explicit reason and expiry.

This artifact does not lock exact day counts because environment/storage policy may differ, but it locks the relative rule:

> summary traces persist longer than deep traces, and incident verbosity expires fastest.

## 10.3 Retention tags per trace

Each trace should carry:
- `retention_tier`
- `expires_at` or retention class
- `debug_reason` if verbosity exceeded default
- `contains_snippets` boolean

## 10.4 Cost control principles

- do not store full candidate payloads by default;
- store IDs, scores, and reasons first;
- promote to deeper capture only on debug, sampling, or failure;
- cap candidate lists and snippet lengths;
- cap trace emission for repetitive fallback storms via aggregation once the incident is known.

---

## 11. Rollout sequencing

This section aligns with task #460 module boundaries.

## 11.1 Wave 0 — establish trace vocabulary

Deliver:
- stable stage enums;
- top-level trace envelope schema;
- stable reason codes for selection, rejection, fallback, and freshness.

Goal:
Make future instrumentation consistent before broad code changes.

## 11.2 Wave 1 — instrument summary traces in the current runtime

Deliver summary traces for:
- classification;
- source selection;
- lexical fetch;
- ranking/authority;
- serving-pack assembly;
- fallback;
- answer shaping.

Goal:
Get useful observability without waiting for the full refactor.

## 11.3 Wave 2 — align traces to bounded modules

As modules from task #460 split out, move ownership of trace fields to the module that owns the decision:
- classifier owns classification event;
- planner owns source-selection event;
- fetchers own fetch events;
- authority resolver owns ranking/authority event;
- assembler owns serving-pack and answer-shaping events;
- runtime adapter owns bridge-transform event.

Goal:
Prevent observability from remaining monolith-coupled.

## 11.4 Wave 3 — typed-serving-specific traces

Add:
- typed eligibility verdicts;
- typed rejection reasons;
- typed-vs-lexical arbitration visibility;
- typed freshness/evidence lineage summaries.

Goal:
Support task #459 rollout safely.

## 11.5 Wave 4 — aggregate counters and regression fixtures

Add:
- aggregate dashboards/counters;
- replay/export fixture path;
- failure cluster views by lane and reason code.

Goal:
Turn single-trace inspection into sustained operating feedback.

---

## 12. Key risks and mitigations

## 12.1 Risk: observability leaks sensitive content
Mitigation:
- redaction-first schema;
- snippet caps;
- deep-trace gating;
- explicit redaction markers.

## 12.2 Risk: trace cost materially slows hot-path retrieval
Mitigation:
- summary-by-default;
- bounded candidate counts;
- IDs/reasons instead of payload dumps;
- sampled deep traces.

## 12.3 Risk: monolith instrumentation bakes in current bad boundaries
Mitigation:
- stage schema mirrors target modular architecture, even before code split completes.

## 12.4 Risk: operators misread incomplete traces as full truth
Mitigation:
- explicit `trace_level`, `status`, and `coverage` markers;
- clear note when a stage was skipped, disabled, or outside observed boundary.

## 12.5 Risk: fallback behavior remains silent in edge cases
Mitigation:
- mandatory fallback event with trigger code and severity.

## 12.6 Risk: freshness stays theoretical instead of affecting service diagnosis
Mitigation:
- mandatory freshness event tied to serve consequence.

## 12.7 Risk: bridge seam hides final transformations
Mitigation:
- require answer-shaping / bridge-transform event after serving-pack assembly when downstream transformation occurs.

---

## 13. Bounded acceptance checks

These checks are intended to gate implementation safely.

## 13.1 Classification trace check
**Given** an ambiguous memory request
**When** the trace is inspected
**Then** it must show the chosen lane, at least one alternative, and the bounded rationale tags that drove the choice.

## 13.2 Source-selection trace check
**Given** an architecture recall request
**When** handoff-like roots are excluded
**Then** the trace must show the exclusion explicitly rather than leaving the omission unexplained.

## 13.3 Ranking/authority trace check
**Given** two high-scoring candidates from different authority layers
**When** one wins by policy rather than raw lexical score
**Then** the trace must show that policy/authority/freshness changed the order.

## 13.4 Fallback trace check
**Given** DB retrieval fails and local fallback is used
**When** the response succeeds through fallback
**Then** the trace must record the trigger, path switch, and expected semantic degradation.

## 13.5 Freshness trace check
**Given** a winning source root is stale by lane policy
**When** the answer is served
**Then** the trace must show stale verdict and serving consequence (`warn`, `demote`, `fallback`, or `block`).

## 13.6 Answer-shaping trace check
**Given** the winning evidence exists but the final envelope is compacted
**When** the trace is inspected
**Then** the operator must be able to see what compaction or citation-mode choice shaped the final answer.

## 13.7 Redaction check
**Given** a request or evidence snippet contains sensitive data
**When** summary or deep trace is stored
**Then** the sensitive material must be masked or replaced with explicit redaction markers.

## 13.8 Hybrid typed/lexical check
**Given** a typed candidate is considered but rejected in favor of lexical evidence
**When** the trace is inspected
**Then** the rejection reason must be explicit and stable.

## 13.9 Boundedness check
**Given** a high-candidate request
**When** deep trace is emitted
**Then** the trace must cap candidate and snippet volume according to policy rather than dumping unbounded payloads.

---

## 14. Recommended implementation contour

A safe initial implementation can proceed with these concrete surfaces:

1. Define `memory_decision_trace` schema and stable enums in one policy module.
2. Instrument summary traces first in current `retrieve_memory.py` path.
3. Emit `trace_id` into normal responses and save summary traces to a bounded artifact store.
4. Add deep-trace capture behind explicit debug flag or sampling.
5. Move stage ownership as modules split under task #460.
6. Add typed-serving-specific trace reasons as task #459 promotion expands.

---

## 15. Final recommendation

Adopt this trace/debug contour as the governing observability contract for memory-serving work.

The important implementation principle is not “log more.” It is:

> define one bounded, redaction-safe, operator-usable decision trace that follows the actual memory decision lifecycle and survives the transition from today’s lexical-first monolith to tomorrow’s typed-first modular serving plane.

That gives downstream work on refactor, freshness, and typed promotion a common diagnostic language and a safer rollout path.
