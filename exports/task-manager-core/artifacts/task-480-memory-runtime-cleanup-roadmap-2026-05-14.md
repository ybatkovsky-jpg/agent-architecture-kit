# Memory/runtime cleanup roadmap — 2026-05-14

## Summary
- Goal: collapse branch sprawl into one execution spine: dedupe branches -> one execution spine -> production-serving contour -> bootstrap/context optimization only after serving.
- Mode note: intended ZIRiBT program run was blocked by gateway timeout; safe local main-session execution used for roadmap/triage/task-manager hygiene.
- 2026-05-14 verification pass for task #480 re-checked task-manager contour and nearby artifacts; baseline spine still holds, with no new branch promoted above runtime-serving work.

## KEEP — active execution spine
- #409 [in_progress] Memory stack improvement spec: current state, target model, and task-cut basis
- #411 [open] Memory stack reality map and operational health check
- #412 [open] Implement first honest evidence-to-memory-note promotion loop
- #413 [open] Operationalize session capsules as real continuity objects
- #414 [open] Design unified runtime serving bridge for memory recall
- #442 [in_progress] Runtime audit and refactor plan for deployed memory contour
- #454 [open] OpenClaw memory runtime improvement program
- #456 [closed] Define target runtime architecture and serving contract
- #457 [closed] Specify and implement memory freshness / ingestion policy
- #459 [done] Promote typed Memory Core to first-class serving plane
- #460 [done] Refactor retrieval orchestration into bounded modules
- #461 [open] Add runtime observability and trace/debug contour for memory answers
- #462 [open] Create phased rollout and verification plan for memory runtime improvements
- #463 [open] Implement wave-1 typed-serving-plane eligibility and precedence wiring
- #464 [open] Memory runtime implementation wave 1 program
- #465 [open] Implement Wave 1 extraction for retrieval classification and adapter seams
- #466 [open] Implement Wave 1 trace summary instrumentation in retrieval runtime
- #342 [in_progress] Memory Core v1 / Stage 1.1: freeze v1 scope and non-scope
- #347 [in_progress] Memory Core v1 / Stage 2.1: draft Postgres schema v1
- #355 [in_progress] Memory Core v1 / Stage 3.3: create decision ingest/update path
- #358 [in_progress] Memory Core v1 / Stage 4.1: define retrieval policy matrix
- #359 [in_progress] Memory Core v1 / Stage 4.2: implement request classifier
- #360 [open] Memory Core v1 / Stage 4.3: implement policy router by domain and authority
- #361 [open] Memory Core v1 / Stage 4.4: define serve-pack schema and output contract
- #362 [open] Memory Core v1 / Stage 4.5: implement serve-pack assembler
- #363 [open] Memory Core v1 / Stage 4.6: add citations, conflict markers and output checks
- #366 [open] Memory Core v1 / Stage 5.3: log failure modes and hardening fixes
- #367 [open] Memory Core v1 / Stage 5.4: assemble evaluation summary and release recommendation
- #472 [open] R2: Define and wire BOOTSTRAP_INDEX for isolated runs
- #473 [open] R3: Implement first runtime/bootstrap capsules
- #475 [open] R5: Optimize main agent bootstrap and memory contour
- #478 [open] Усилить память OpenClaw: canonical user-profile block и retrieval-hardening
- #479 [open] Расширить memory hardening: canonical fact blocks для project/operational/tech domains

## FREEZE — not on active spine now

Verification note: contour re-check did not surface a justified promotion from these branches into the active spine. They remain frozen to avoid parallel execution drift while runtime-serving and core-serving tasks are still incomplete.
- #90 [waiting_user] PKM/RAG implementation: set up local storage stack (PostgreSQL + pgvector + schema)
- #92 [open] PKM/RAG implementation: hybrid retrieval and compact evidence packing
- #93 [open] PKM/RAG implementation: OpenClaw integration and memory-agent prompt policy
- #105 [open] Memory core rollout: реализовать базовый ingestion/update контур
- #106 [open] Memory core rollout: реализовать FTS + pg_trgm retrieval и evidence packing
- #107 [open] Memory core rollout: спланировать local-vs-server workload placement
- #108 [open] Memory core rollout: аккуратно добавить vector layer после стабилизации базы
- #109 [open] MemPalace pilot: bounded evaluation поверх стабилизированного backbone
- #111 [open] Architecture uplift: оформить явное разделение prompt-memory и searchable recall
- #114 [open] Architecture uplift: усилить durable lineage между task-manager, handoff, recovery и memory
- #116 [open] Memory preflight: read-only SSH аудит текущего memory-контура на сервере
- #131 [open] Obsidian wiki system: human-facing knowledge layer and vault skeleton
- #132 [open] Internet-facing wiki: public/shared publish contour and deployment skeleton
- #133 [waiting_user] Internet-facing wiki: choose publish engine and build first public deploy scaffold
- #134 [open] Wiki: public/shared layering expansion and first curated public pages
- #135 [open] Wiki: selected page indexing policy into memory retrieval
- #136 [open] Wiki: domain coverage expansion for TRIAD / ProClimate / operations
- #137 [open] Obsidian cloud vault for wiki: sync architecture and workspace mapping
- #182 [open] Obsidian/PKM-контур: структура vault, заметок и смысловой перелинковки
- #183 [open] PKM/Obsidian: skeleton vault и стартовая структура
- #184 [open] PKM/Obsidian: первые опорные заметки и паттерны
- #185 [open] Adaptive learning: карта интересов, пробелов и непрерывной диагностики
- #186 [open] PKM/Obsidian: первая содержательная пачка заметок
- #187 [open] PKM/Obsidian: стартовые карты baseline по ключевым направлениям
- #371 [open] Refactor agent architecture: separate main orchestrator memory from domain-agent memory
- #372 [open] Create strategist MEMORY.md and perform first main-vs-strategist memory split
- #441 [open] OpenClaw↔Hermes integration spec v0.1 (bounded delegated runtime, not embedded core)
- #443 [open] Hermes integration v0.3 implementation plan
- #444 [open] Hermes integration first bounded coding slice
- #452 [open] Hermes bounded re-poll and timeout escalation pilot policy
- #89 [open] MCP server someday: expose triad as a reusable content engine

## REFERENCE / ARCHIVE — useful background, not active execution

Verification note: recent artifacts around #360/#361/#363 confirm these items remain useful evidence/history, but not the operator-facing execution lane for task #480.
- #333 [open] Memory Stack v2: layered memory architecture for context optimization
- #334 [open] Memory Core v1: schema and serving policy for context optimization
- #335 [open] Memory Core v1 rollout: unified memory platform implementation
- #336 [open] Memory Core v1 rollout / Stage 1: spec lock and architecture freeze
- #337 [open] Memory Core v1 rollout / Stage 2: storage layer v1
- #338 [open] Memory Core v1 rollout / Stage 3: ingestion and distillation pipeline
- #339 [open] Memory Core v1 rollout / Stage 4: retrieval and serve-pack layer
- #340 [open] Memory Core v1 rollout / Stage 5: real-scenario evaluation and hardening
- #341 [open] Memory Core v1 rollout / Stage 6: post-v1 augmentation gate
- #343 [open] Memory Core v1 / Stage 1.2: define canonical object model
- #344 [open] Memory Core v1 / Stage 1.3: define authority map and domain boundaries
- #345 [open] Memory Core v1 / Stage 1.4: define retrieval request classes and serving principles
- #346 [open] Memory Core v1 / Stage 1.5: assemble spec baseline v1
- #348 [open] Memory Core v1 / Stage 2.2: create migrations for storage layer
- #349 [open] Memory Core v1 / Stage 2.3: implement shared registry model
- #350 [open] Memory Core v1 / Stage 2.4: implement typed links layer
- #351 [open] Memory Core v1 / Stage 2.5: implement decision and capsule storage
- #352 [open] Memory Core v1 / Stage 2.6: storage smoke checks
- #353 [open] Memory Core v1 / Stage 3.1: ingest task metadata into memory core
- #356 [open] Memory Core v1 / Stage 3.4: define and build session capsule distiller
- #357 [open] Memory Core v1 / Stage 3.5: provenance and link integrity in ingest pipeline
- #368 [open] Memory Core v1 / Stage 6.1: build post-v1 enhancement backlog
- #369 [open] Memory Core v1 / Stage 6.2: define augmentation decision criteria
- #370 [open] Memory Core v1 / Stage 6.3: review augmentation go/no-go after v1 eval
- #86 [done] PKM/RAG Architect: design private personal memory system for OpenClaw
- #94 [done] PKM/RAG Architect: internet-backed comparative scan for private memory stack options
- #97 [done] Разобрать внешние prompt/RAG/LLM-материалы и извлечь, что реально встраивать в систему
- #98 [done] MemPalace: анализ на наших данных и подготовка practical pilot / внедрения
- #101 [done] Углублённый анализ MemPalace и локальной реализации memory-стека под нашу инфраструктуру
- #121 [done] Memory rollout: retrieval regression fixture pack for known queries
- #125 [done] Memory rollout: live retrieval smoke runner unification
- #127 [done] Memory rollout: operational runbook for live ingest and retrieval

## One execution spine
### Phase 1 — Reality map and consolidation
- #411 Memory stack reality map and operational health check
- #442 Runtime audit and refactor plan for deployed memory contour
- #462 Create phased rollout and verification plan for memory runtime improvements
### Phase 2 — Runtime serving path hardening
- #463 Implement wave-1 typed-serving-plane eligibility and precedence wiring
- #465 Implement Wave 1 extraction for retrieval classification and adapter seams
- #466 Implement Wave 1 trace summary instrumentation in retrieval runtime
- #461 Add runtime observability and trace/debug contour for memory answers
### Phase 3 — Minimal Memory Core execution slice
- #342 Memory Core v1 / Stage 1.1: freeze v1 scope and non-scope
- #347 Memory Core v1 / Stage 2.1: draft Postgres schema v1
- #355 Memory Core v1 / Stage 3.3: create decision ingest/update path
- #358 Memory Core v1 / Stage 4.1: define retrieval policy matrix
- #359 Memory Core v1 / Stage 4.2: implement request classifier
- #360 Memory Core v1 / Stage 4.3: implement policy router by domain and authority
- #361 Memory Core v1 / Stage 4.4: define serve-pack schema and output contract
- #362 Memory Core v1 / Stage 4.5: implement serve-pack assembler
- #363 Memory Core v1 / Stage 4.6: add citations, conflict markers and output checks
- #366 Memory Core v1 / Stage 5.3: log failure modes and hardening fixes
- #367 Memory Core v1 / Stage 5.4: assemble evaluation summary and release recommendation
### Phase 4 — Bootstrap only after serving-core
- #472 R2: Define and wire BOOTSTRAP_INDEX for isolated runs
- #473 R3: Implement first runtime/bootstrap capsules
- #475 R5: Optimize main agent bootstrap and memory contour
### Support only — markdown hardening
- #478 Усилить память OpenClaw: canonical user-profile block и retrieval-hardening
- #479 Расширить memory hardening: canonical fact blocks для project/operational/tech domains

## KILL — none newly justified in this pass
- No additional branches were hard-killed in this verification pass because the currently non-active lines are already adequately handled by FREEZE/REFERENCE and do not require destructive cleanup to make the spine operable.

## Stop-doing list
- Do not run old PKM/RAG rollout and new runtime-serving program in parallel.
- Do not advance bootstrap optimization before serving-core is practically stronger.
- Do not treat markdown canonicalization as final memory-engine completion.
- Do not reopen speculative wiki/Obsidian/Hermes branches until core recall path is stronger.

## Canonical claim
- Current canonical execution spine = tasks #411 -> #442 -> #462 -> #463/#465/#466/#461 -> #342/#347/#355/#358/#359/#360/#361/#362/#363/#366/#367 -> #472/#473/#475, with #478/#479 as support only.
