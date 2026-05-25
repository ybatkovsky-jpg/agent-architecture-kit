# Retrieval Payload Contract v1

Status: implementation-facing contract for the canonical `retrieve_memory.py` output payload
Date: 2026-05-16
Task: #493
Scope: freeze the current retrieval JSON surface needed for implementation/verifier alignment only

## Purpose

This artifact freezes the **bounded canonical payload shape** currently emitted by `pkm-memory/retrieve_memory.py`.

It is intentionally narrow:
- no triad changes;
- no Hermes changes;
- no architecture expansion;
- only the retrieval output surface already exercised by current `pkm-memory` verifiers.

Reference implementation source: `pkm-memory/retrieve_memory.py`
Primary verifier dependencies observed in workspace:
- `scripts/verify_request_classifier_contract.py`
- `scripts/verify_routing_policy_task_360.py`
- `scripts/verify_authority_priority_task_361.py`
- `scripts/verify_citation_policy_task_362.py`
- `scripts/verify_conflict_open_questions_task_363.py`
- `scripts/verify_trace_summary_observability.py`

---

## Canonical output envelope

Top-level payload shape:

```json
{
  "query": "...",
  "mode": "local|postgres|...",
  "contract_version": "2026-04-26.phase1",
  "item_count": 3,
  "summary": "...",
  "items": [
    {
      "score": 0,
      "match_reason": "...",
      "source": {"key": "..."},
      "document": {"workspace_path": "...", "title": "..."},
      "chunk": {"section_path": "..."},
      "excerpt": "...",
      "provenance": {...},
      "authority": {
        "layer": "..."
      },
      "rank": 1
    }
  ],
  "provenance": {...},
  "routing": {...},
  "serve_pack": {...},
  "request_classification": {...}
}
```

This contract only freezes fields required by current implementation and verifiers. Other additive fields may exist.

---

## Required fields

### 1) `request_classification`

Required as a top-level object.

Minimum required members:
- `request_class`
- `serve_class`
- `budget`
- `primary_domains`
- `fallback_domains`
- `forbidden_default_domains`
- `authority_priority_focus`
- `expected_citation`

Meaning for alignment:
- this is the canonical classifier output consumed by routing and serve-pack packaging;
- verifiers treat `request_class` as the primary lane selector;
- `expected_citation` must propagate into `serve_pack.citation_policy.expected_citation`.

### 2) `routing.selected_source_keys`

Required path:
- `routing.selected_source_keys: string[]`

Meaning for alignment:
- the ordered set of source keys actually selected for retrieval after classification/routing;
- verifiers use it to confirm that the chosen lane pulled from the right source families.

Notes:
- this is a routing result, not a complete inventory of all registered sources;
- sibling routing fields may exist, but `selected_source_keys` is the required contract field.

### 3) `items[].authority.layer`

Required path on every returned item:
- `items[i].authority.layer: string`

Meaning for alignment:
- the canonical authority label for ranking/serving checks;
- current verifiers use it to validate top-authority behavior and authority-priority outcomes.

Current observed layer vocabulary includes at least:
- `canonical_handoff`
- `task_state`
- `evidence_record`
- `memory_note`
- `wiki_page`
- `retrieval_document`
- `session_capsule`

This artifact freezes presence and semantic role, not a closed enum.

### 4) `serve_pack.citation_policy`

Required path:
- `serve_pack.citation_policy: object`

Required members:
- `request_class`
- `expected_citation`
- `citation_mode`
- `answer_shape`
- `purpose`
- `min_cited_facts`
- `fact_ref_style`
- `supporting_ref_style`

Meaning for alignment:
- this is the implementation-facing answer-packaging contract derived from request class;
- task #362 verifier checks these fields directly;
- it defines how the answer should be cited, not the natural-language wording of the answer.

### 5) `serve_pack.cited_facts`

Required path:
- `serve_pack.cited_facts: object[]`

Required members per fact:
- `claim`
- `refs`
- `authority`
- `document_title`

Meaning for alignment:
- bounded evidence facts selected for the answer envelope;
- this is the canonical evidence pack checked by citation-policy and bounded-sufficiency verifiers.

Implementation note:
- `refs` format varies by `citation_policy.fact_ref_style`.

### 6) `serve_pack.conflicts`

Required path:
- `serve_pack.conflicts: object[]`

Meaning for alignment:
- structured declaration that the bounded result set contains authority ambiguity, dated-source ambiguity, or similar synthesis-level tension;
- may be empty;
- task #363 verifier checks presence/absence and conflict type behavior, not prose style.

Observed required subfield for verifier use:
- `type`

### 7) `serve_pack.open_questions`

Required path:
- `serve_pack.open_questions: string[]`

Meaning for alignment:
- bounded unresolved questions emitted when evidence is thin, mixed, or freshness is ambiguous;
- may be empty;
- task #363 verifier checks semantic presence, count alignment, and some message fragments, not exact global phrasing.

### 8) `serve_pack.trace`

Required path:
- `serve_pack.trace: object`

Required members:
- `authority_priority_focus`
- `serve_pack_changed_order`
- `top_item_lock`
- `top_authority_layers`
- `selected_item_paths`
- `synthesis`

Required nested members under `serve_pack.trace.synthesis`:
- `conflict_count`
- `open_question_count`
- `authority_trace_changed_order`

Meaning for alignment:
- canonical machine-facing trace for why the envelope looks the way it does;
- this is the detailed trace object, distinct from `serve_pack.trace_summary`;
- current conflict/open-question verification depends on `trace.synthesis` count alignment.

---

## Invariants

1. **Top-level classifier presence invariant**
   - final payload must include top-level `request_classification`.

2. **Classifier-to-policy carry-through invariant**
   - `serve_pack.citation_policy.request_class == request_classification.request_class`.
   - `serve_pack.citation_policy.expected_citation == request_classification.expected_citation`.

3. **Routing visibility invariant**
   - final payload must include `routing.selected_source_keys`, even if other routing detail changes.

4. **Authority labeling invariant**
   - every returned item must carry `authority.layer`.
   - top-rank authority checks are performed against this field, not inferred from path names.

5. **Bounded evidence-pack invariant**
   - `serve_pack.cited_facts` is the canonical bounded answer evidence set.
   - minimum expected size is governed by `serve_pack.citation_policy.min_cited_facts`.

6. **Conflict/open-question accounting invariant**
   - `serve_pack.trace.synthesis.conflict_count == len(serve_pack.conflicts)`.
   - `serve_pack.trace.synthesis.open_question_count == len(serve_pack.open_questions)`.

7. **Serve-pack namespace invariant**
   - canonical answer-packaging fields live under `serve_pack`, not duplicated into a second top-level answer envelope.

8. **Additive-safe invariant**
   - additive fields are allowed, but required fields above must remain stable in name, nesting, and meaning.

---

## Non-goals

This artifact does **not** freeze:
- ranking internals or scoring formulas;
- the full item schema beyond required alignment fields;
- the full set of possible `authority.layer` values as a permanently closed taxonomy;
- Hermes payloads or Hermes interface changes;
- triad behavior;
- any new architecture or cross-system abstraction;
- exact prose wording of summaries, conflicts, or open questions outside verifier-relevant semantics.

---

## Practical verifier reading

If a future change keeps this contract true, it should continue to satisfy the current retrieval verifier family even if ranking heuristics evolve.

If a future change renames, relocates, or collapses any of the required fields above, it should be treated as a contract break and updated intentionally with verifier changes, not incidentally.
