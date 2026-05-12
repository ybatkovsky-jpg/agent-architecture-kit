# OpenClaw Frame Context Serving Policy v1

## 1. Scope and purpose

This document defines the minimum context serving policy for OpenClaw Frame v1.

Its purpose is to reduce context bloat without weakening continuity, authority discipline, or recovery quality.
It gives later implementation and verification work a stable policy for:
- what context classes may be present by default;
- what context classes must be retrieved only when the request actually needs them;
- what context classes must not be ambiently injected into runtime context;
- how authority boundaries and request classes change serving behavior;
- how to avoid transcript-first continuity mistakes;
- how to respond when evidence is weak, stale, or conflicting.

This is a serving-policy artifact, not a broad retrieval-engine design.

---

## 2. Why context bloat is a real failure mode

Context bloat is not just a cost problem. It is a correctness problem.

When too much mixed context is injected by default, the system becomes more likely to:
- answer from stale but verbose material instead of fresh canonical state;
- blur task truth, continuation truth, evidence truth, and memory truth;
- overfit to transcript phrasing rather than operational reality;
- let weakly related retrieval documents outrank stronger authority objects;
- hallucinate continuity by replaying old chat tails;
- hide uncertainty because the large bundle creates false confidence.

In the Frame contour, context bloat is especially dangerous because thin `main` and bounded execution depend on explicit recovery anchors rather than conversation residue.

### Core failure pattern

Bad path:
1. inject transcript tail, old summaries, generic memory, and retrieval chunks together;
2. model sees high lexical overlap and plausible narrative continuity;
3. canonical current state is diluted or displaced;
4. response sounds coherent but is operationally wrong.

### Policy stance

Default context should be as small as possible while preserving safe orientation.
If a context item is not needed to answer the current request or continue the current bounded step, it should not be ambiently served.

---

## 3. Serving classes

Frame v1 uses exactly three serving classes.

### 3.1 Always-on

Definition:
Small, high-authority context that is safe and usually necessary to orient the current step.

Properties:
- low volume;
- high freshness or direct current relevance;
- clear canonical owner;
- strong recovery value;
- should not require transcript archaeology.

### 3.2 On-demand retrieval

Definition:
Context that may be useful or necessary for a specific request class, but should be loaded only when the request calls for it.

Properties:
- variable size;
- request-shaped relevance;
- may require ranking, citation, and conflict handling;
- should be cited or linked when materially used.

### 3.3 Forbidden ambient injection

Definition:
Context that must not be injected into default runtime context merely because it exists or is nearby.

Properties:
- high noise or stale-continuity risk;
- weak authority without explicit promotion;
- likely to distort routing or confidence if always present;
- may still be accessible for audit or explicit lookup, but not as ambient context.

---

## 4. Default serving rule

Use the smallest sufficient authority-bearing context.

Default order:
1. always-on orientation pack;
2. classify the operator request;
3. retrieve only the domains allowed for that request class;
4. reorder candidates by authority priority;
5. surface uncertainty if evidence is weak or conflicting;
6. never silently widen into transcript-first mixed context.

---

## 5. Mapping of core memory object types into serving classes

| Object type | Default serving class | Why |
|---|---|---|
| `task_state` / current task lifecycle truth | Always-on | Highest operational value for current status, next owner, and next bounded step |
| `canonical_handoff` / continuation package / latest terminal return package | Always-on for the current active branch only | Needed for continuity and bounded resume; must stay narrow and current |
| `memory_note` subtype `state_summary` for the active contour | Always-on only when it is the compact canonical orientation note for the current contour | Useful if compact and current; should not duplicate large history |
| `memory_note` subtype `decision` | On-demand retrieval | Important for rationale and policy questions, not needed in every turn |
| `memory_note` subtype `pattern` / `anti_pattern` / `blocker` / `durable_ref` | On-demand retrieval | Reusable, but only when request or task shape calls for them |
| `memory_note` subtype `preference` | On-demand retrieval | Safe only when the request implicates personalization or operator style |
| `wiki_page` | On-demand retrieval | Stable synthesis layer for repeated knowledge, but too broad for default injection |
| `evidence_record` | On-demand retrieval | Often necessary for audit/proof, but usually too bulky for default context |
| `source_record` | On-demand retrieval | Provenance/control object, not routine runtime context |
| `retrieval_document` | On-demand retrieval with lowest authority among allowed domains | Derived search surface only; never canonical by itself |
| raw transcript tails / session residue | Forbidden ambient injection | High stale-continuity risk and weak authority unless explicitly requested for audit |
| old operator-visible summaries not reflected into canonical anchors | Forbidden ambient injection | Projection is not authority |
| mixed historical retrieval bundles with no current-task tie | Forbidden ambient injection | High noise and authority confusion |

### Important special case

Only the **current** task state and the **current-branch** continuation anchors qualify as always-on.
Historical task states and older continuation artifacts are not always-on merely because they are canonical.
They become on-demand retrieval objects.

---

## 6. Authority-aware serving rules

Serving must be authority-aware after request class is known.
Raw lexical match is not enough.

### 6.1 Core precedence

When several items compete, prefer this order unless the request class explicitly requires otherwise:
1. current `task_state`;
2. current-branch `canonical_handoff` / continuation truth;
3. durable `memory_note`;
4. `wiki_page`;
5. `evidence_record`;
6. `retrieval_document`.

### 6.2 Request-shaped overrides

- **Current status / continue / next-step requests:** current task state and current continuation truth dominate.
- **Decision rationale requests:** decision memory notes and governing specs dominate; evidence supports but should not replace rationale synthesis.
- **Audit / proof-trace requests:** evidence artifacts dominate, but task or handoff anchors may frame scope.
- **Preference requests:** durable preference notes dominate; if absent, do not backfill from weak transcript hints as if they were strong memory.
- **General topic recall:** wiki pages and mature memory notes may dominate over raw evidence if the question asks for understanding rather than proof.

### 6.3 Derived-layer rule

`retrieval_document` is a retrieval aid, not a truth source.
It may help find stronger objects, but it must not silently outrank a stronger canonical object for the same request.

### 6.4 Freshness rule

For continuation and active-status questions, a fresh high-authority object should beat an older but lexically richer object.

---

## 7. Transcript-first anti-pattern and prevention rules

### 7.1 Anti-pattern definition

Transcript-first serving means the system treats the conversation tail as the default continuity source, then shapes the answer around it, instead of using task state, continuation anchors, and explicit evidence.

### 7.2 Why it is harmful

It causes:
- stale or partial continuity;
- hidden authority inversion;
- wrong resume points;
- contaminated status answers;
- fabricated preferences and decisions;
- hard-to-audit outputs.

### 7.3 Prevention rules

1. **No transcript-first default behavior.**
   Raw chat/session tails must not be part of the always-on pack.

2. **Canonical-first continuity.**
   Resume and status answers must start from current task state and latest relevant continuation anchor.

3. **Projection demotion.**
   Chat summaries, topic replies, and dashboard digests are projections unless explicitly promoted into canonical state.

4. **Explicit transcript use only.**
   Transcript material may be retrieved only for explicit audit, exact quote, or unresolved-conflict inspection.

5. **No silent narrative bridging.**
   If canonical continuity is missing, the system should state the gap and ask for or retrieve the basis, not fake a smooth continuation from chat residue.

6. **Meta-artifact caution.**
   Evaluation packs, scenario descriptions, and summary artifacts that mention the desired facts must not replace the underlying proof objects for operational serving.

---

## 8. Operator request classes and serving implications

This policy assumes request classification happens before broad retrieval.

| Request class | Primary serving implication | Default domains |
|---|---|---|
| `current_task_execution` / status | Keep always-on pack thin and fresh; retrieve only current task/continuation/supporting artifacts as needed | task state, current handoff/return, small current state-summary note |
| `resume_reopen_continuation` / continue | Prefer immediate predecessor continuity objects; do not reconstruct from transcript | current task state, latest relevant continuation basis, latest terminal package |
| `policy_decision_lookup` / why | Bring in decision notes and governing spec/wiki pages | decision memory notes, specs, wiki pages, supporting evidence |
| `artifact_source_trace_request` / audit | Retrieve direct proving artifacts and exact file references | evidence records, concrete artifacts, supporting task/handoff scope anchors |
| `preference_operating_style_recall` / preference | Retrieve durable preference notes only; if weak evidence, answer with caveat | preference memory notes, stable operating-memory artifacts |
| general factual/topic lookup | Retrieve stable synthesis before broader evidence | wiki pages, mature memory notes, supporting evidence, retrieval docs |

### Budget implication

- status/continue: smallest budget class;
- rationale/preference: medium bounded retrieval;
- audit: larger retrieval budget allowed, but still scope-bounded and citation-heavy.

---

## 9. Uncertainty and weak-evidence handling

The serving system must fail visibly, not confidently, when evidence is weak.

### 9.1 Weak-evidence rules

If support is weak, stale, or conflicting:
- say so directly;
- lower claim strength;
- prefer a bounded answer over a confident synthesis;
- name what stronger anchor would resolve the ambiguity.

### 9.2 Specific cases

- **No durable preference note:** state that preference evidence is weak and fall back to safe default behavior.
- **Multiple candidate resume points:** surface ambiguity and prefer the freshest explicit continuation anchor; do not silently choose an older one.
- **Spec vs task-state disagreement:** for active execution status, task state wins; note the conflict.
- **Summary claims result exists but artifact missing:** treat the claim as unverified until evidence anchor is found.

### 9.3 Confidence hygiene

Large context bundles must not be used to justify stronger confidence.
Confidence should come from authority, freshness, and direct support, not from volume.

---

## 10. Bounded examples

### Example A — Good status serving

Request:

`Where are we now on this rollout and what is next?`

Serve:
- current task state;
- latest active handoff or latest terminal child return;
- maybe one compact current state summary note.

Do not ambiently serve:
- old transcripts;
- generic architecture wiki;
- large evidence bundles.

### Example B — Good continuation serving

Request:
`Continue after the last conflict-synthesis step and tell me the next bounded step.`

Serve:
- current task state;
- immediate predecessor continuation anchor;
- latest terminal package proving the last bounded step ended.

Do not:
- infer the resume point from transcript narrative;
- pull unrelated older handoffs into default context.

### Example C — Good rationale serving

Request:
`Why was retrieval_document kept as a derived layer rather than source of truth?`

Serve:
- decision note or memory note;
- governing spec sections;
- supporting evidence if needed.

Do not:
- answer only from retrieval chunks;
- treat audit-style file dump as enough if the question is asking for rationale.

### Example D — Good preference serving under weak evidence

Request:
`How should I answer a user on technical chain updates?`

Serve:
- preference notes if present.

If absent:
- say evidence is weak;
- use safe default style;
- optionally suggest that a durable preference note would help.

### Example E — Good audit serving

Request:
`Show which exact files prove Stage 4 routing, authority ranking, citation envelope, and conflict synthesis.`

Serve:
- exact proving artifacts first;
- optionally a framing task artifact.

Do not:
- cite only the evaluation pack that mentions those files.

---

## 11. Open questions

1. What exact minimal field set should define the always-on orientation pack at runtime?
2. How should current-branch detection work when several child continuations exist?
3. Should certain `memory_note.state_summary` objects be auto-promoted into always-on only when freshness checks pass?
4. What exact suppression policy should demote meta-artifacts and transcript residue for audit/status/continue classes?
5. How should authority-aware serving expose explainability without bloating the operator-visible answer envelope?
