# Authority Priority

## Core rule

Final served memory items should not be ranked by raw lexical score alone.
They should be reordered by authority priority once request class is known.

## Example authority layers

- `canonical_handoff`
- `task_state`
- `memory_note`
- `wiki_page`
- `evidence_record`
- `retrieval_document`

## Why this matters

A lower-score item can still be more correct if it belongs to a stronger authority layer for the current request type.

## Explainability requirement

The serve pack should make authority ordering visible, not hidden.
At minimum it should expose:
- inferred authority layer;
- priority index;
- matched focus order;
- whether authority priority changed the final order.
