# Meta Evaluation Recall Contract v1

Status: bounded companion contract for first-class meta/evaluation retrieval lane
Date: 2026-05-07
Related tasks: #368, #369, #370, #371
Primary implementation file: `pkm-memory/retrieve_memory.py`
Parent lane contract: `pkm-memory/RETRIEVAL_LANE_CONTRACTS_V1.md`

## Lane id

`meta_evaluation_recall`

## Purpose

This artifact freezes the extracted first-class lane for explicit evaluation/meta/hardening recall so the behavior no longer lives only as an implementation mapping under `architecture_design_recall`.

## Trigger intent

Queries explicitly asking for one or more of:
- evaluation artifacts
- evaluation summary
- hardening slice / hardening log
- release recommendation
- scenario pack / Stage 5 evidence
- baseline fail/pass evidence
- explicit meta audit/evaluation recall

## Contracted routing

- Request class: `meta_evaluation_recall`
- Serve class: `on_demand`
- Budget: `small`
- Primary domains: `evidence_record`
- Allowed fallback domains: `memory_note`, `wiki_page`, `retrieval_document`
- Forbidden default domains: continuation handoff substitution, transcript-only recall, memory-only answer with no cited artifact basis

## Contracted authority order

1. `evidence_record`
2. `canonical_handoff` only when explicitly requested as evidence
3. `memory_note`
4. `wiki_page`
5. `retrieval_document`

## Canonical top-shape

1. directly requested evaluation/hardening artifact
2. adjacent evidence artifacts from the same family
3. synthesis note only after artifact evidence is established

## Boundary rules

- Explicit meta/evaluation intent must not stay in `architecture_design_recall`.
- Explicit meta/evaluation intent disables continuation-meta suppression.
- Generic architecture/design recall remains in `architecture_design_recall`.
- Short ambiguous continuation phrasing without explicit meta evidence cues does not enter this lane.

## Minimal regression anchors

- `explicit-meta-evaluation-query`
- `evaluation-summary-explicit-meta`
- `hardening-slice-explicit-meta`

These anchors live in `pkm-memory/fixtures/continuation-regression-task-371/cases.json`.
