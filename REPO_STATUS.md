# Repository Status

Short status snapshot for the current exported state of `agent-architecture-kit`.

---

## 1. What this repository is now

This repository is now the **canonical public-safe architecture assembly** for the current OpenClaw contour.

It is no longer only a clean architecture façade.
It now combines:

1. **native AIK architecture materials**
2. **sanitized live-system core exports**
3. **selected support and proof exports**

Primary navigation:
- `README.md`
- `EXPORT_INDEX.md`

---

## 2. Already exported

### A. Native AIK layer
Already present as the original architecture-kit repository:
- architecture docs
- memory docs
- evaluation docs
- examples
- schemas
- reference implementation
- evaluation tooling

### B. Memory core export
Exported under:
- `exports/memory-core/`

Includes:
- retrieval/runtime core
- Memory Core v1 implementation slices
- contracts
- SQL schema
- fixtures
- verification scripts

### C. Task-manager core export
Exported under:
- `exports/task-manager-core/`

Includes:
- autonomy state core
- watchdog / closure-loop / autonomy tests
- structured adapter contract
- selected reviewed TM artifacts

### D. Architecture support pack
Exported under:
- `exports/architecture-support-pack/`

Includes:
- selected frame/context-system/execution-context artifacts
- memory runtime audit docs
- target architecture docs
- curated proof pack

---

## 3. What is intentionally not in this repository

The repo is sanitized by design.

Excluded intentionally:
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
- broad raw execution exhaust
- unreviewed bulk artifacts

---

## 4. What still exists outside the repo

There are still live-workspace materials that are not yet exported.

Main remaining zones:

### Memory-side remainder
Still outside the repo:
- large parts of `pkm-memory/outputs/`
- `memory/*` daily/operator memory notes
- private memory packs
- some supporting artifacts that need manual review

### Task-manager-side remainder
Still outside the repo:
- many TM artifacts not yet curated into export waves
- operational residue
- runtime/task state files
- infra/business-specific artifacts

### Workspace docs remainder
Still outside the repo:
- some workspace-level docs that are either too operational, too private, or not yet reviewed for export fitness

---

## 5. Current export quality assessment

### Strongly exported already
These contours are now represented well enough for architecture reading and reuse:
- memory core
- retrieval policy / memory architecture
- task-manager autonomy core
- watchdog / closure-loop contours
- frame / execution-context architecture
- context-system-2 direction
- audit / target-memory architecture layer

### Partially exported
These contours are present, but not yet fully canonicalized:
- broader proof history
- evolution timeline
- task lineage / rollout sequencing
- source-to-doc crosswalk from live implementation to exported architecture docs

### Not intended for full export
These should likely remain excluded or heavily filtered:
- private operator memory
- personal strategy memory
- raw operational traces
- environment-specific deployment residue
- business-specific project matter that is not architecture-general

---

## 6. Recommended next waves

If more export work is desired later, the best next additions would be:

### Wave N+1 — human summary layer
Possible additions:
- architecture evolution timeline
- memory/runtime program map
- task lineage map for major architecture programs
- source-to-doc crosswalk

### Wave N+2 — tighter proof layer
Possible additions:
- curated human-readable proof summaries
- smaller annotated verification index
- release-history / regression-history summaries

### Wave N+3 — selective artifact expansion
Possible additions only after review:
- more TM architecture artifacts
- more memory proof materials
- additional architecture diagrams

---

## 7. Current practical reading path

For a new reader:
1. `README.md`
2. `EXPORT_INDEX.md`
3. `docs/architecture/README.md`
4. `docs/memory/README.md`
5. `docs/evaluation/README.md`
6. `exports/memory-core/README.md`
7. `exports/task-manager-core/README.md`
8. `exports/architecture-support-pack/README.md`

---

## 8. Bottom line

The repository has already crossed the important threshold:

- it is not just a polished architectural shell;
- it now contains meaningful sanitized source-adjacent architecture exports from the live OpenClaw contour;
- it is usable as the single canonical architecture repository for Memory, AIK, and Task Manager.
