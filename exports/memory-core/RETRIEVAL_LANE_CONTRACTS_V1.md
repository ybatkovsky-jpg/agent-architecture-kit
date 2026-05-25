# Retrieval Lane Contracts v1

Status: implementation-facing lane contract artifact for Memory Core retrieval behavior
Date: 2026-05-07
Related tasks: #358, #359, #360, #361, #362, #363, #368, #369, #370, #371
Related baselines:
- `pkm-memory/RETRIEVAL_POLICY_MATRIX_V1.md`
- `pkm-memory/CONTINUATION_RETRIEVAL_CONTRACT_V1.md`

## Purpose

This file productizes the retrieval behavior into explicit **lane contracts** so classifier/routing/ranking changes can be checked against bounded expectations.

It freezes, for the main lanes currently exercised in Stage 5 hardening:
- expected winner family;
- allowed authority layers;
- allowed and forbidden source types;
- canonical top-shape;
- boundary rules against adjacent lanes.

This is a contract artifact, not a promise of global ranking perfection.

---

## Global lane principles

1. **Lane decides what kind of truth should win.**
   Classification is not cosmetic; it changes which authority family should become the answer nucleus.

2. **Top-shape matters more than broad candidate noise.**
   For this stage, the stabilized surface is the top answer basis and first few supporting items, not full-list purity.

3. **Derived search projections are never ultimate authority.**
   `retrieval_document` can help discovery but cannot outrank its backing authority family when the backing family is present.

4. **Transcripts are forbidden as default top truth.**
   Raw chat/transcript material is never the canonical winner for the lanes covered here.

5. **Explicit meta intent overrides suppression heuristics.**
   When the user explicitly asks for evaluation/hardening/meta artifacts, the system must surface the artifact/evidence family rather than hide it behind continuation or note-preference heuristics.

---

## 1) Continuation lane

**Lane id**: `resume_reopen_continuation`

### Primary user question
- Where do I resume actual work?
- What is the freshest operational handoff anchor?

### Expected winner family
- `canonical_handoff` first
- then `task_state` when no canonical handoff is available
- then directly relevant `evidence_record`

### Allowed authorities
- `canonical_handoff`
- `task_state`
- `evidence_record`
- `wiki_page`
- `retrieval_document`
- `memory_note`
- `session_capsule` only as narrow owning-run continuity aid

### Forbidden / non-winning defaults
- transcript/raw chat as top answer
- stale session capsules from unrelated runs
- evaluation/hardening artifacts as top answer for non-explicit continuation queries
- verification/self-hit artifacts replacing the operational handoff when a handoff exists

### Allowed source types
- task-manager handoff artifacts
- fresh task-state / next-step artifacts in the same task chain
- directly backing implementation artifacts tied to the resume target

### Forbidden source types by default
- transcript tails / chat replay
- stale generic handoffs from other efforts
- evaluation summaries used as substitute for operational resume state

### Canonical top-shape
1. freshest canonical handoff for the named or inferred task chain
2. nearby predecessor/same-chain handoff or evidence items
3. only then descriptive memory/meta context

Expected citation shape:
- task id
- handoff path
- optionally one or two same-chain supporting artifact refs

### Boundary rules
- **vs factual**: natural-language resume cues (`resume`, `reopen`, `continue from handoff`, `продолжи`, `с места после`) pull the query into continuation even if the query references facts.
- **vs meta/evaluation**: explicit meta wording (`evaluation summary`, `hardening slice`, `stage 5`, `baseline fail/pass`) overrides continuation suppression and moves the winner family away from handoff truth.
- **explicit task-id rule**: named task-id handoff should strongly dominate.
- **predecessor-chain rule**: when adjacent tasks are named, freshest relevant handoff wins over predecessor-only context.
- **natural-language continuation rule**: a continue-after-X query with clear resume framing should still land on the operational anchor.

---

## 2) Factual lane

**Lane id**: `factual_lookup`

### Primary user question
- What artifact/file/path contains the fact?
- What is the direct grounded answer?

### Expected winner family
- `evidence_record`
- then `retrieval_document` for discovery/orientation only
- `wiki_page` may orient, but should not replace direct evidence when available

### Allowed authorities
- `evidence_record`
- `retrieval_document`
- `wiki_page`

### Forbidden / non-winning defaults
- `session_capsule`
- unsupported summary-only answers
- transcript recollection
- policy/memory-note synthesis pretending to be direct evidence when direct evidence exists

### Allowed source types
- direct artifacts/files
- evidence-bearing task artifacts
- path-bearing retrieval documents
- wiki only as orientation/supporting synthesis

### Forbidden source types by default
- chat replay
- speculative memory summaries
- active-run continuity capsules

### Canonical top-shape
1. direct artifact/evidence item with exact or near-exact lexical grounding
2. adjacent evidence items from the same artifact family
3. retrieval projection or wiki orientation only after direct evidence

Expected citation shape:
- direct file path and/or section ref

### Boundary rules
- **vs continuation**: if the query lacks resume framing and behaves like a short artifact hunt, factual may win even if words like `continue after` appear weakly.
- **vs architecture**: asking for “what file/path proves X” stays factual even when the topic is architectural.
- **explicit task-id alone is not enough**: task-id plus artifact/path-oriented wording can remain factual.

---

## 3) Architecture / design recall lane

**Lane id**: `architecture_design_recall`

### Primary user question
- What architecture, design, contract, or baseline did we define?
- What is the intended system structure or policy shape?

### Expected winner family
- `memory_note` or `wiki_page` for canonical design synthesis
- `evidence_record` allowed when explicit artifact-first architecture recall is requested

### Allowed authorities
- `memory_note`
- `wiki_page`
- `evidence_record`
- `retrieval_document`

### Forbidden / non-winning defaults
- raw transcripts
- `session_capsule`
- continuation handoff as substitute for design recall

### Allowed source types
- memory notes distilling architecture/design decisions
- wiki pages / curated synthesis
- backing artifacts/spec docs

### Forbidden source types by default
- handoff-only operational notes when the question asks for design/system recall
- transcript-first reconstruction

### Canonical top-shape
1. distilled architecture note or curated wiki synthesis
2. one or more backing spec/artifact refs
3. retrieval-document discovery support only if needed

Current accepted v1 implementation shape:
- design/architecture queries may still top-rank a strongly lexical spec artifact (`evidence_record`) instead of a memory note when no stronger curated note match is surfaced.
- This is acceptable in v1 as long as the winner remains architecture-spec evidence rather than continuation or transcript material.

Expected citation shape:
- note/wiki ref plus backing artifact refs where applicable

### Boundary rules
- **vs meta/evaluation**: generic architecture/design recall should prefer synthesis (`memory_note`/`wiki_page`), but explicit evaluation/hardening artifact asks can intentionally switch top authority to evidence-bearing artifacts.
- **vs continuation**: words like `next step` or `continue` do not override architecture intent if the core ask is for design/contract recall.
- **vs factual**: “show architecture spec baseline” is architecture recall; “which file/path contains the architecture baseline” is artifact trace or factual.

---

## 4) Meta / evaluation recall lane

**Lane id**: `meta_evaluation_recall`

### Primary user question
- What did the evaluation, scenario pack, hardening slice, or release recommendation say?
- Which artifacts show fail/pass evidence or meta findings?

### Expected winner family
- artifact/evidence family first
- typically `evidence_record`
- continuation hardening slices and evaluation summaries are valid primary winners when explicitly asked for

### Allowed authorities
- `evidence_record`
- `canonical_handoff` only if the query explicitly asks for a handoff artifact as evidence
- `memory_note`
- `wiki_page`
- `retrieval_document`

### Forbidden / non-winning defaults
- continuation suppression of explicitly requested meta artifacts
- handoff continuity material replacing requested evaluation evidence
- memory-only answer with no cited artifact basis

### Allowed source types
- evaluation summary artifacts
- scenario pack artifacts
- hardening log / hardening slice artifacts
- release recommendation artifacts
- explicit verification/evidence files when they are the requested proof surface

### Forbidden source types by default
- transcript-only recall
- generic continuation handoffs unless explicitly requested as evidence

### Canonical top-shape
1. directly requested evaluation/hardening artifact
2. adjacent evidence artifacts from the same evaluation family
3. synthesis note only after artifact evidence is established

Expected citation shape:
- explicit artifact path(s)
- evidence-bearing file refs
- fail/pass summary sources where applicable

### Boundary rules
- **vs architecture**: explicit asks for `evaluation artifacts`, `hardening slice`, `release recommendation`, `stage 5`, or fail/pass evidence should classify into `meta_evaluation_recall` and yield artifact/evidence winners, not memory-note synthesis.
- **vs continuation**: explicit meta intent disables continuation-meta suppression.
- **evaluation-summary vs hardening-slice**: either family may win if it is the more exact lexical fit to the explicit request; both remain valid meta/evidence winners.
- **hardening-slice family overlap**: for broad `hardening slice` wording, adjacent hardening slices (`368–370`) are all acceptable evidence-family winners until narrower family-disambiguation is implemented.

---

## Cross-lane boundary matrix

| Boundary | Contracted winner rule |
|---|---|
| continuation vs factual | Resume framing wins continuation; weak artifact-hunt phrasing with no resume anchor may remain factual |
| meta vs architecture | Explicit evaluation/hardening artifact ask wins artifact/evidence family; generic design/spec ask wins memory/wiki synthesis |
| evaluation-summary vs hardening-slice | Both are valid meta winners; more exact requested artifact family should top-rank |
| explicit task-id vs natural-language recall | Explicit task-id continuation should strongly dominate when resume framing is present; natural-language recall follows lane cues and may be less stable if cues are weak |

---

## Locked boundary rules for this stage

1. **Explicit task-id continuation must be handoff-first.**
2. **Anchored natural-language continuation must beat continuation-meta writeups.**
3. **Short ambiguous phrasing without strong resume cues may still fall back to factual.**
4. **Explicit meta/evaluation recall must route through `meta_evaluation_recall` and remain artifact/evidence-first.**
5. **Generic architecture/design recall remains synthesis-first by contract, but architecture-spec evidence winners are acceptable in v1 when lexical artifact grounding is stronger than available curated-note matches.**
6. **Direct factual lookup remains evidence-first.**
7. **Transcript-first answers are invalid across all five lanes by default.**

---

## Known current limitation

Very short ambiguous continuation-style phrasing without task-id or strong resume cues can still classify as `factual_lookup` and self-hit verification artifacts in the top-N pool.

This limitation is accepted in v1 only as a documented boundary, not as desired end-state behavior.

---

## Next logical stage after this contract

The next bounded hardening stage should target:
- family-level disambiguation inside `meta_evaluation_recall` so evaluation-summary vs hardening-slice vs release-recommendation requests separate more crisply when lexical evidence is close;
- remaining candidate-pool hygiene / self-hit suppression for short ambiguous recall prompts that still fall back to factual lookup.
