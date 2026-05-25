# Continuation Retrieval Contract v1

Status: implementation-facing stabilization contract for Memory Core continuation retrieval
Date: 2026-05-07
Related tasks: #368, #369, #370
Related baseline policy: `pkm-memory/RETRIEVAL_POLICY_MATRIX_V1.md`
Companion lane-contract artifact: `pkm-memory/RETRIEVAL_LANE_CONTRACTS_V1.md`

## Purpose

This file freezes the bounded retrieval contract for continuation-style requests so future ranking/router changes can be checked against explicit behavior instead of hand-tuning by feel.

It is the continuation-specialized companion to the broader lane artifact in `pkm-memory/RETRIEVAL_LANE_CONTRACTS_V1.md`.

It defines:
- what counts as continuation intent;
- which authority/source types must win;
- when meta/evaluation artifacts are allowed;
- how continuation lane differs from meta lane;
- which invariants must not regress.

## 1) What counts as continuation intent

A query is in the **continuation lane** when its primary user intent is to resume, reopen, or keep working from an operational prior state rather than inspect evaluation material about that state.

Typical continuation cues include:
- `resume`, `reopen`, `continue`, `continue from handoff`, `pick back up`
- Russian equivalents like `продолжи`, `продолжить`, `с места после`
- explicit task-id resume prompts
- predecessor-chain prompts that name adjacent tasks and ask for the freshest handoff
- natural-language continue-after-X phrasing where `X` is a prior implementation milestone/handoff step

A query is **not** continuation-lane by default if its main goal is to inspect:
- evaluation outcomes;
- scenario packs;
- fail/pass summaries;
- hardening logs;
- meta artifacts about retrieval behavior itself.

## 2) Continuation authority priority

For continuation-lane queries, the preferred authority order is:

1. `canonical_handoff`
2. `task_state`
3. `evidence_record`
4. `wiki_page`
5. `retrieval_document`
6. `memory_note`
7. `session_capsule`

Interpretation:
- **canonical handoff wins** when present and relevant;
- fresh task/handoff state beats descriptive writeups about that state;
- retrieval projections can help discovery but cannot outrank the operational handoff anchor;
- memory notes are useful context, not the primary resume anchor;
- session capsules remain continuity aids, not durable operational truth.

## 3) Source/artifact families that should win

For continuation-lane queries, top-ranked answer basis should prefer:
- task handoff artifacts in `task-manager/artifacts/*handoff*.md`
- fresh task-state / close-ready / next-step artifacts tied to the same task chain
- direct artifact-backed evidence for the relevant implementation step

If the query names a task-id, exact task-id handoff matches should strongly dominate.

If the query names a predecessor chain (for example `task-362` / `task-363`), the freshest handoff in that chain should win, with nearby predecessor artifacts allowed in supporting positions.

If the query is natural-language and unnumbered, the system may use recency/project cues, but it should still prefer the actual operational handoff anchor over fresh meta writeups that merely discuss the continuation case.

## 4) When meta/evaluation artifacts are allowed

Meta/evaluation artifacts are allowed when the query is explicitly asking for them.

Examples of explicit meta lane intent:
- `evaluation summary`
- `stage 5`
- `acceptance scenarios`
- `release recommendation`
- `hardening log`
- source-trace requests specifically asking which files show fail/pass or evaluation evidence

In explicit meta lane:
- evaluation artifacts like tasks `364–367` are valid primary evidence;
- continuation-meta hardening artifacts like `368–370` may surface if directly relevant to the query;
- no continuation suppression/demotion should hide the explicitly requested evaluation basis.

In continuation lane:
- evaluation/meta artifacts may remain in the candidate pool;
- but they must not outrank the real handoff anchor unless the query explicitly asks for meta/evaluation material.

## 5) Continuation lane vs meta lane

### Continuation lane
Primary question:
- “Where do I resume actual work from?”

Expected winner shape:
- canonical handoff or freshest operational task anchor

Expected citation shape:
- task id, handoff artifact path, directly relevant task artifact refs

Failure if:
- top result is a fresh evaluation/hardening writeup describing the situation instead of the operational handoff itself

### Meta lane
Primary question:
- “What did evaluation/hardening say about the system?”

Expected winner shape:
- evaluation summary, scenario pack, release recommendation, hardening slice

Expected citation shape:
- explicit artifact/file refs for evaluation artifacts and fail/pass evidence

Failure if:
- evaluation artifacts are suppressed just because they are meta
- the router answers a meta/evaluation question with only handoff continuity material

## 6) Regression invariants

The following invariants must not break:

1. **Explicit task-id resume invariant**
   - A continuation query naming a concrete task-id should top-rank that task’s handoff artifact when available.

2. **Predecessor-chain freshness invariant**
   - When adjacent tasks are named, the freshest relevant handoff in the chain should outrank predecessor context.

3. **Natural-language continue-after-X invariant**
   - Unnumbered continuation phrasing that refers to a prior implementation milestone should prefer the operational handoff anchor over continuation meta writeups.

4. **Meta suppression boundary invariant**
   - Non-explicit continuation queries may demote continuation-meta artifacts.
   - Explicit meta/evaluation queries must not be suppressed by continuation heuristics.

5. **Authority-over-projection invariant**
   - `retrieval_document` and descriptive summaries cannot override backing operational handoff evidence for continuation answers.

6. **No transcript-first reconstruction invariant**
   - Raw chat/transcript style material must not become primary continuation memory by default.

7. **Boundedness invariant**
   - The fix point is winner selection and top-answer basis, not unbounded context dumping.

## 7) Known acceptable limitation in current stage

At the current stage, ambiguous continuation phrasing without task-id may still surface verification or hardening-summary artifacts in the top-N candidate pool, especially when those artifacts quote the continuation phrase directly.

That is acceptable **only if**:
- the query is still classified as `resume_reopen_continuation`; and
- explicit task-id / predecessor-chain / continue-after-X cases still route to the correct handoff winner; and
- explicit meta/evaluation queries still route to evaluation artifacts.

This limitation is a next-stage cleanup target, not grounds to blur the continuation-vs-meta contract.
