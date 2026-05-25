# Retrieval Policy Matrix v1

Status: implementation-facing baseline for Memory Core v1 Stage 4.1
Related tasks: #345, #346, #358

## Purpose

This file turns the retrieval/serving rules from the broader Memory Core spec into a direct implementation baseline for request classification, policy routing, and bounded serve-pack assembly.

It defines:
- request classes;
- primary and fallback retrieval domains;
- forbidden default domains;
- serving mode / serve class;
- authority priority;
- expected citation shape;
- size budget.

## Authority priority

Higher authority wins when multiple domains disagree or overlap.

1. **evidence_record** — direct file/task/artifact-backed source evidence
2. **memory_note** — distilled durable notes backed by evidence and/or explicit source-of-truth refs
3. **wiki_page** — curated synthesis backed by notes/evidence
4. **retrieval_document** — searchable projection/index layer, never stronger than its backing evidence
5. **session_capsule** — active-run continuity aid only, never durable truth
6. **transcript/raw chat history** — never primary memory by default

## Serving classes / serve modes

### `always_on_candidate`
Small, stable, repeatedly useful canonical material that can improve startup or bounded resume.

### `on_demand`
Retrieve only for a specific question, task, or lookup.

### `never_ambient`
Derived, noisy, speculative, stale, or high-volume material that must never silently ride in startup context.

## Request-class policy matrix

| Request class | Primary domains | Allowed fallback domains | Forbidden default domains | Serve class | Authority priority focus | Expected citation | Budget |
|---|---|---|---|---|---|---|---|
| current_task_execution | task-manager state; canonical handoff; task-scoped memory notes | wiki_page; evidence_record; retrieval_document | unrelated project history; transcript tails; stale session capsules from other runs | always_on_candidate + on_demand | task state/handoff > memory_note > wiki/evidence > retrieval_document | task id, handoff artifact path, note refs | small |
| resume_reopen_continuation | canonical handoff; fresh task state; state summaries for same run | evidence_record; wiki_page | stale capsules from other runs; long chat replay; transcript-first reconstruction | always_on_candidate + on_demand | handoff/task state > evidence_record > wiki_page > retrieval_document > owning active capsule only if needed | handoff/task refs | small |
| architecture_design_recall | memory_note (decision/pattern); wiki_page | evidence_record; retrieval_document | raw transcripts by default; session capsules | on_demand | memory_note > wiki_page > evidence_record > retrieval_document | note refs, wiki refs, backing artifact refs | small |
| meta_evaluation_recall | evidence_record | memory_note; wiki_page; retrieval_document | continuation handoff substitution; transcript-only recall; memory-only answer with no cited artifact basis | on_demand | evidence_record > canonical_handoff > memory_note > wiki_page > retrieval_document | explicit artifact paths, evidence-bearing file refs, fail/pass summary sources | small |
| factual_lookup | evidence_record | retrieval_document; wiki_page for orientation only | session_capsule; unsupported summaries; transcript recollection | on_demand | evidence_record > retrieval_document > wiki_page | direct source path/section refs | medium |
| policy_decision_lookup | memory_note (decision/preference/policy) | wiki_page; evidence_record | generic chunk dumps; transcript-tail summaries | on_demand | memory_note > evidence_record > wiki_page > retrieval_document | note refs + supporting evidence refs | small |
| preference_operating_style_recall | verified preference notes | evidence_record | speculative notes; old transcript recollections | always_on_candidate + on_demand | memory_note > evidence_record | note refs + supporting ref | tiny |
| artifact_source_trace_request | evidence_record | retrieval_document | memory-only answer with no source | on_demand | evidence_record > retrieval_document | direct artifact/file refs | medium |

## Operational routing rules

1. **Transcripts are not primary memory by default.**
   Raw transcript or chat replay may only be used in a special explicit mode, not as default authoritative recall.

2. **Retrieval-document authority is derived.**
   `retrieval_document` helps search and retrieval, but it cannot override backing evidence or stable memory notes.

3. **Session capsule usage is narrow.**
   `session_capsule` is continuity support for the owning active run only. It is not a durable authority class and must not answer generic factual or policy recall.

4. **Serve-pack assembly must follow request purpose.**
   The router should select only the domains and budget needed for the request class rather than dumping broad context.

5. **Citation-bearing output is mandatory.**
   Any factual or policy-serving result must carry citations appropriate to the selected authority layer.

## Budget classes

- **tiny** — 0-2 short note items, no body dumps, direct refs only
- **small** — compact answer nucleus + a few notes/refs + maybe one narrow synthesis summary
- **medium** — targeted evidence snippets allowed when exact grounding is needed

Unbounded dumps are invalid for all classes.

## Verification basis

This baseline is implementation-facing but anchored in already agreed spec material:
- `task-manager/artifacts/task-346-memory-core-spec-v1-draft-2026-05-06.md`
  - sections 7.1-7.6 define request classes, retrieval domains, serve-pack contract, budgets, and forbidden patterns
- This file extracts those rules into a router-friendly matrix so Stage 4.2 and 4.3 can implement classifier/router behavior without re-parsing the full spec

## Stage 4.1 acceptance mapping

- **There is a retrieval policy matrix v1**
  - satisfied by the request-class policy matrix above
- **Each request class has primary/fallback domains**
  - satisfied by the `Primary domains` and `Allowed fallback domains` columns
- **Serve mode and authority priority are clear**
  - satisfied by `Serve class`, `Authority priority focus`, and the global `Authority priority` section
