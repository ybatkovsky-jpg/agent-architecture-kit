# Task 778 — Memory substrate promotion seam checkpoint

Date: 2026-05-27
Task: #778

## Completed bounded slice
- Added explicit `significance`, `freshness`, and `conflict_posture` schema validation in `pkm-memory/memory_core_session_capsule_distiller.py` for `promoted_memory_notes`.
- Implemented one narrow promotion path from durable `mem_*` notes into inspectable working context via `metadata.promoted_memory_context` and `metadata.capsule_text`.
- Added explicit reversibility/inspectability controls under `metadata.promotion_controls`.
- Kept promotion bounded to the session capsule distiller seam without replacing durable writers or general retrieval orchestration.

## Acceptance mapping
- Metadata shape exists: `promoted_memory_notes[*]` validates `significance`, `freshness`, `conflict_posture`.
- Narrow classifier/promotion path exists: durable `mem_*` note inputs are promoted into capsule metadata and summarized text.
- Working-context promotion is inspectable and reversible/controllable: exposed in `metadata.promoted_memory_context`, `metadata.capsule_text`, and `metadata.promotion_controls`.
- Verification uses explicit metadata rather than hidden heuristics: verifier asserts exact promoted metadata fields and summary presence.

## Verification
- `python3 pkm-memory/scripts/verify_memory_core_session_capsule_distiller.py`
- `python3 pkm-memory/scripts/verify_memory_core_decisions_sessions.py`

## Residual follow-up scope
- No runtime consumer reads `metadata.promoted_memory_context` yet outside the distiller verification path; later work can wire this inspectable working-context pack into retrieval/serving traces if desired.
- No broader DB persistence schema change was needed for this bounded slice because the promotion remains in inspectable capsule metadata.
