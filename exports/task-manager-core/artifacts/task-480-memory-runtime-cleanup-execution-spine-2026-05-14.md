# Task 480 — master execution spine (2026-05-14)

Task: #480  
Program: Memory/runtime cleanup program  
Source directive: `task-480-memory-runtime-cleanup-program-2026-05-14.md`  
Baseline roadmap: `task-480-memory-runtime-cleanup-roadmap-2026-05-14.md`

## Purpose
Turn the roadmap into one operator-usable execution lane with explicit ordering, bounded active slices, and a stop-doing list that prevents branch sprawl from reopening.

## Verified contour
Roadmap baseline was re-checked against visible task-manager notes/artifacts for:
- runtime contour: `#411/#442/#462/#463/#465/#466/#461`
- core serving slice: `#342/#347/#355/#358/#359/#360/#361/#362/#363/#366/#367`
- bootstrap-only-after-serving: `#472/#473/#475`

Result: no stronger competing execution lane was found. Existing roadmap remains directionally correct.

## Single execution spine

### Spine A — runtime-serving hardening first
1. `#411` reality map / operational health check  
   Output needed: honest deployed contour, current failure modes, live path inventory.
2. `#442` runtime audit / refactor plan  
   Output needed: exact gaps between deployed path and target serving contour.
3. `#462` phased rollout + verification plan  
   Output needed: execution gates, evidence loop, rollout checkpoints.
4. `#463` typed-serving-plane eligibility + precedence wiring  
   Output needed: runtime path selects serving plane by rules, not ad hoc fallback.
5. `#465` retrieval classification extraction + adapter seams  
   Output needed: request class enters runtime path in structured form.
6. `#466` trace summary instrumentation  
   Output needed: recall path explains what it served and why.
7. `#461` observability / trace-debug contour  
   Output needed: operator can inspect live answers and runtime path selection.

### Spine B — minimal Memory Core serving contract behind runtime
8. `#342/#347/#355` keep the minimum core substrate honest  
   Output needed: scoped core, schema baseline, decision ingest/update path.
9. `#358/#359/#360` retrieval policy matrix + classifier + router  
   Output needed: classification and routing become explicit runtime contract.
10. `#361/#362/#363` serve-pack schema + assembler + output checks  
    Output needed: bounded answer/execution pack with citations/conflict checks.
11. `#366/#367` hardening/evaluation summary  
    Output needed: known failure modes and release verdict.

### Spine C — bootstrap/context only after runtime-serving progress
12. `#472/#473/#475` BOOTSTRAP_INDEX + capsules + startup optimization  
    Entry condition: runtime-serving path materially stronger than markdown-only fallback.

## Current bounded active slice executed in this run
Chosen slice: promote structured runtime-serving metadata from provider prefetch into the main agent runtime path instead of treating prefetch as plain text only.

Why this slice:
- directly advances `#463/#465/#466/#461`
- keeps one execution spine
- improves canonical recall path without jumping prematurely into bootstrap work

## What not to do in parallel
- Do not advance old PKM/RAG rollout tasks `#90/#92/#93/#105-#109` in parallel.
- Do not reopen wiki/Obsidian/Hermes side branches as if they were primary memory-runtime work.
- Do not treat markdown hardening tasks `#478/#479` as substitute completion for serving runtime.
- Do not pull `#472/#473/#475` forward unless serving/runtime evidence is already stronger.

## Task-manager-facing launch order suggestion
If work must be split after this run, spawn/sequence only in this order:
1. verify or close gap on `#463`
2. verify or close gap on `#465`
3. verify or close gap on `#466`
4. extend operator observability under `#461`
5. only then resume `#360 -> #361 -> #362 -> #363 -> #366 -> #367`
6. only after that open bounded bootstrap slice `#472/#473/#475`

## Acceptance gate for moving to bootstrap
Bootstrap/context work may start only when all are true:
- runtime prefetch path exposes structured metadata, not text only
- request classification is visible in runtime trace
- serving-class / source / trace summary are inspectable
- tests verify the runtime contract

## Evidence produced in this run
- code/test changes in Hermes memory runtime path
- green targeted test run covering manager + startup metadata surfaces
- serving-progress artifact documenting implementation, verification, blockers, and next mandatory slice
