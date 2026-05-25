# Export Index

Canonical navigation index for the current `agent-architecture-kit` export state.

This repository now contains three layers:

1. **Native AIK architecture kit**
   - cleaned architectural docs, examples, schemas, and minimal reference code
2. **Sanitized core exports from live OpenClaw systems**
   - `exports/memory-core/`
   - `exports/task-manager-core/`
3. **Second-wave support exports**
   - `exports/architecture-support-pack/`
   - selected architecture support docs and curated proof artifacts

The goal of this index is to answer four questions quickly:
- what is in this repo;
- what is core vs support vs proof;
- what order to read it in;
- what is intentionally excluded.

---

## 1. Recommended reading order

If you want the shortest path to understanding the whole contour, read in this order:

### Pass 1 — orientation
1. `README.md`
2. `docs/architecture/README.md`
3. `docs/memory/README.md`
4. `docs/evaluation/README.md`

### Pass 2 — top-level architecture
5. `docs/architecture-overview.md`
6. `docs/memory-contour.md`
7. `docs/task-manager-integration.md`
8. `docs/isolated-execution.md`
9. `docs/eval-regression.md`

### Pass 3 — canonical exported cores
10. `exports/memory-core/README.md`
11. `exports/task-manager-core/README.md`
12. `exports/architecture-support-pack/README.md`

### Pass 4 — deep architecture details
13. `docs/architecture/frame-baseline-v1.md`
14. `docs/architecture/handoff-contract-v1.md`
15. `docs/architecture/routing-ownership-map-v1.md`
16. `docs/memory/memory-core-v1.md`
17. `docs/memory/retrieval-policy-matrix.md`
18. `docs/evaluation/evaluation-harness-v0-1.md`

### Pass 5 — source-adjacent exported materials
19. `exports/architecture-support-pack/memory-docs/MEMORY_TARGET_ARCHITECTURE_V1_2026-05-13.md`
20. `exports/architecture-support-pack/memory-docs/MEMORY_RUNTIME_AUDIT_LIVE_2026-05-13.md`
21. `exports/architecture-support-pack/tm-artifacts/openclaw-frame-architecture-baseline-v1-2026-05-01.md`
22. `exports/architecture-support-pack/tm-artifacts/context-system-2-target-design-spec-2026-05-19.md`

### Pass 6 — proof and verification
23. `exports/architecture-support-pack/curated-proof-pack/README.md`
24. selected `verification-report.json` and `summary.json` files in `exports/architecture-support-pack/curated-proof-pack/`

---

## 2. Repository map

## 2.1 Native AIK layer

These are the repo-native architecture-kit materials.

### `docs/`
Primary architectural writing.

- `docs/architecture/`
  - execution/orchestration/frame contours
  - handoff contracts
  - routing and ownership maps
  - control-plane and serving policies
  - promotion-gate schemas and policies
- `docs/memory/`
  - memory stack model
  - Memory Core v1
  - retrieval policy
  - authority priority
- `docs/evaluation/`
  - regression harness
  - protected cases
  - acceptance scenarios
  - hardening / release recommendation contours
- top-level docs in `docs/`
  - overview explainers
  - integration notes
  - isolated execution contour
  - primer materials

### `src/agent_architecture_kit/`
Minimal Python reference implementation for selected architecture concepts.

### `schemas/`
JSON schemas for memory/task/trace/promotion-gate structures.

### `examples/`
Readable examples of truth hierarchy, memory distillation, task-memory-artifact splits, and serving-policy examples.

### `scripts/` and `evals/`
Reference evaluation / scoring / regression-support tooling and sample fixtures.

---

## 2.2 Exported core layer

These are sanitized exports from the live OpenClaw contour.

### `exports/memory-core/`
Purpose:
- preserve the strongest reusable memory runtime core
- show actual retrieval / classification / registry / typed-link contours

Contains:
- memory core implementation files
- retrieval implementation
- contracts
- SQL schema
- fixtures
- verification scripts
- env example

Use this when you want:
- the most implementation-adjacent memory export
- real retrieval policy/routing material
- Memory Core v1 runtime contours

Start with:
- `exports/memory-core/README.md`
- `exports/memory-core/EXPORT_NOTES.md`
- `exports/memory-core/RETRIEVAL_POLICY_MATRIX_V1.md`
- `exports/memory-core/META_EVALUATION_RECALL_CONTRACT_V1.md`

### `exports/task-manager-core/`
Purpose:
- preserve the reusable autonomy / watchdog / closure-loop / TM execution core

Contains:
- `autonomy_state.py`
- autonomy/watchdog regression tests
- core TM contracts
- selected reviewed architecture artifacts

Use this when you want:
- the practical autonomy state machine contour
- closure-loop and watchdog semantics
- regression anchors for autonomy hardening

Start with:
- `exports/task-manager-core/README.md`
- `exports/task-manager-core/EXPORT_NOTES.md`
- `exports/task-manager-core/STRUCTURED_ADAPTER_CONTRACT.md`
- `exports/task-manager-core/autonomy_state.py`

---

## 2.3 Architecture support layer

### `exports/architecture-support-pack/`
Purpose:
- bridge the gap between the polished AIK layer and the deeper live-system core exports
- preserve second-wave architecture materials that are valuable but not part of the minimal core slices

Contains three parts:

#### A. `tm-artifacts/`
Selected architecture-rich artifacts from Task Manager / frame work.

Main themes:
- Context System 2
- OpenClaw frame baseline and contracts
- execution-context schema
- module interface blueprint
- runtime continuity / assembly boundary thinking

Best entry points:
- `openclaw-frame-architecture-baseline-v1-2026-05-01.md`
- `openclaw-frame-continuation-contract-v1-2026-05-12.md`
- `openclaw-execution-context-schema-implementation-facing-v1-2026-04-28.md`
- `context-system-2-target-design-spec-2026-05-19.md`
- `context-system-2-runtime-assembly-binding-plan-2026-05-19.md`

#### B. `memory-docs/`
Memory runtime audits and target-design materials.

Best entry points:
- `MEMORY_TARGET_ARCHITECTURE_V1_2026-05-13.md`
- `MEMORY_RUNTIME_AUDIT_LIVE_2026-05-13.md`
- `MEMORY_RUNTIME_AUDIT_PASS2_2026-05-13.md`

#### C. `curated-proof-pack/`
Selected verification summaries only.

Selection policy:
- include summary / verification artifacts
- exclude raw dumps
- exclude full operational exhaust

Use this when you want evidence that the exported contours were exercised and verified.

---

## 3. Core vs support vs proof

## Core
These are the highest-priority reusable materials:
- `docs/architecture/*`
- `docs/memory/*`
- `docs/evaluation/*`
- `src/agent_architecture_kit/*`
- `exports/memory-core/*`
- `exports/task-manager-core/*`

## Support
These deepen understanding but are not the minimal core:
- `exports/architecture-support-pack/tm-artifacts/*`
- `exports/architecture-support-pack/memory-docs/*`
- `examples/*`
- `notes/export-boundary.md`

## Proof
These are verification-oriented rather than design-oriented:
- `exports/architecture-support-pack/curated-proof-pack/*`
- parts of `evals/*`
- parts of `scripts/*`
- tests under `tests/`

---

## 4. If you are interested specifically in...

### Memory architecture
Read:
1. `docs/memory/README.md`
2. `docs/memory/memory-core-v1.md`
3. `docs/memory/retrieval-policy-matrix.md`
4. `exports/memory-core/README.md`
5. `exports/architecture-support-pack/memory-docs/MEMORY_TARGET_ARCHITECTURE_V1_2026-05-13.md`
6. `exports/architecture-support-pack/memory-docs/MEMORY_RUNTIME_AUDIT_LIVE_2026-05-13.md`

### Task-manager / autonomy contour
Read:
1. `docs/task-manager-integration.md`
2. `exports/task-manager-core/README.md`
3. `exports/task-manager-core/STRUCTURED_ADAPTER_CONTRACT.md`
4. `exports/task-manager-core/autonomy_state.py`
5. `exports/architecture-support-pack/tm-artifacts/openclaw-frame-architecture-baseline-v1-2026-05-01.md`
6. `exports/architecture-support-pack/tm-artifacts/openclaw-frame-continuation-contract-v1-2026-05-12.md`

### Thin-main / isolated execution / frame contour
Read:
1. `docs/isolated-execution.md`
2. `docs/architecture/frame-baseline-v1.md`
3. `docs/architecture/handoff-contract-v1.md`
4. `exports/architecture-support-pack/tm-artifacts/openclaw-frame-handoff-spec-v1-2026-05-01.md`
5. `exports/architecture-support-pack/tm-artifacts/openclaw-runtime-continuity-design-note-2026-04-28.md`

### Context assembly / context slimming
Read:
1. `exports/architecture-support-pack/tm-artifacts/context-system-2-target-design-spec-2026-05-19.md`
2. `exports/architecture-support-pack/tm-artifacts/context-system-2-surface-manifest-schema-2026-05-19.md`
3. `exports/architecture-support-pack/tm-artifacts/context-system-2-pack-admission-schema-2026-05-19.md`
4. `exports/architecture-support-pack/tm-artifacts/context-system-2-runtime-assembly-binding-plan-2026-05-19.md`

### Evidence / regression / proof
Read:
1. `docs/evaluation/README.md`
2. `docs/evaluation/evaluation-harness-v0-1.md`
3. `exports/architecture-support-pack/curated-proof-pack/README.md`
4. selected verification reports in `exports/architecture-support-pack/curated-proof-pack/`

---

## 5. Intentional exclusions

This repository is **not** a full raw dump of the live workspace.

Explicitly excluded or heavily filtered:
- secrets
- `.env` files
- tokens / credentials
- runtime state
- active/handoff state
- logs
- tmp files
- private daily memory notes
- personal/operator memory packs
- business-specific residue
- infrastructure backups
- broad raw execution outputs

This is deliberate. The repo is meant to be:
- reusable,
- readable,
- architecture-first,
- safe to share.

---

## 6. Current export status

As of the current export wave, the unified canonical repository includes:

- native AIK architecture kit materials
- `exports/memory-core/`
- `exports/task-manager-core/`
- `exports/architecture-support-pack/`

Practical meaning:
- the repo is no longer just a polished façade;
- it now also contains substantial sanitized source-adjacent architecture and proof material from the live OpenClaw contour.

---

## 7. Suggested future additions

Reasonable next additions, if further sanitization is done:
- a top-level architecture timeline / evolution map
- a task lineage map for major memory/runtime programs
- a source-to-doc crosswalk showing which exported docs correspond to which live-system seams
- a narrower curated proof index with human summaries for each verification artifact
