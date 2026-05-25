# Memory Runtime Audit — pass 2 (registry/config evidence) — 2026-05-13

## What this pass added

This pass moved beyond the initial `retrieve_memory.py` read and confirmed that the deployed contour already contains a **typed Memory Core storage layer**, a **seeded source registry**, and **retrieval result artifacts** proving lane-aware behavior.

---

## Newly verified findings

### 1) There is an explicit source registry, not only implicit path heuristics
Verified from:
- `pkm-memory/config/source_registry.seed.yaml`

Confirmed enabled sources:
- `openclaw_shared_memory` → `memory`
- `task_manager_artifacts` → `task-manager/artifacts`
- `task_manager_handoffs` → `task-manager/handoffs`

Confirmed disabled-but-modeled sources:
- `content_system_memory`
- `agent_local_memories`
- `mempalace_data_protected`
- `mempalace_adapter_protected`
- `unclassified_workspaces`

Important consequence:
- the live contour is already operating with a declared ingestion/retrieval source model;
- path heuristics still exist in retrieval logic, but they are sitting on top of a real source-registry layer.

### 2) There is a typed relational Memory Core model behind the contour
Verified from:
- `pkm-memory/memory_core_registry.py`
- `task-manager/artifacts/task-349-memory-core-v1-registry-write-surface-handoff-2026-05-06.md`

Confirmed object families:
- `source_record`
- `evidence_record`
- `memory_note`
- `wiki_page`
- `retrieval_document`
- `session_capsule`
- `typed_link`

Confirmed relational backing tables (`mc_*`):
- `mc_source_records`
- `mc_evidence_records`
- `mc_memory_notes`
- `mc_wiki_pages`
- `mc_retrieval_documents`
- `mc_session_capsules`
- `mc_typed_links`
- relation tables such as `mc_object_sources`, `mc_object_evidence`, `mc_wiki_backing_memory`, `mc_retrieval_document_chunks`, etc.

Important consequence:
- the memory contour is not just lexical retrieval over markdown;
- there is an explicit target shape for canonical typed memory objects.

### 3) Retrieval policy behavior is backed by saved result artifacts, not only code claims
Verified from:
- `pkm-memory/outputs/task-360-routing-policy-2026-05-10-rerun2/architecture-keeps-memory-in-selected-sources.result.json`
- `pkm-memory/outputs/task-360-routing-policy-2026-05-10-rerun2/resume-prefers-handoffs-over-memory.result.json`

Observed behavior:
- architecture-style query returns top evidence from `task_manager_artifacts`, with authority layer `evidence_record`;
- continuation-style query returns top evidence from `task_manager_handoffs`, with authority layer `canonical_handoff`;
- result payloads contain explicit authority metadata, provenance, focus order, match reasons, and ranked outputs.

Important consequence:
- the policy-aware routing is not hypothetical; it has artifact-level evidence of working behavior.

### 4) Deterministic context assembly exists as an architectural target in the workspace
Verified from retrieval output citing:
- `task-manager/artifacts/openclaw-architecture-implementation-plan-2026-04-28.md`

Relevant cited layer order in that artifact:
1. runtime policy
2. task brief
3. topic context
4. linked artifacts
5. durable memory facts
6. relevant skill(s)
7. recent local interaction
8. toolset metadata

Important consequence:
- memory retrieval is being developed within a larger context-assembly architecture, not as an isolated search subsystem.

### 5) Telegram topic/approval routing was not proven from config yet
Verified negative finding:
- `content-system/config/channels.yaml` is only a placeholder and does not explain live Telegram topic approval routing.

Implication:
- the reason approvals surface in the group-level chat rather than the topic is still unverified in this pass;
- likely explanation remains runtime/plugin routing outside the currently inspected workspace config.

---

## Updated architecture maturity assessment

Previous pass estimate: custom heuristic retrieval orchestrator.

Updated estimate after this pass:
- **more mature than first thought** in storage and source modeling;
- **less mature than desired** in end-to-end observability and runtime explainability.

Refined summary:
> The live contour is a hybrid of (a) seeded source-registry retrieval, (b) typed relational Memory Core foundation, and (c) still-heavy retrieval heuristics on the read side.

So the system is not merely heuristic. It is a **partially formalized memory architecture with an uneven maturity profile**:
- stronger on model/storage direction,
- weaker on runtime visibility and read-path cleanliness.

---

## Updated keep / simplify / rewrite verdict

### Keep
- source registry model;
- typed Memory Core object families;
- policy-aware routing by request class;
- authority metadata in retrieval outputs;
- provenance-bearing result format.

### Simplify
- path/title special-case routing where source registry + typed family metadata should dominate;
- read-side compensating logic that exists only because canonical source/family wiring is not yet fully trusted.

### Rewrite / strengthen
- retrieval observability/tracing in actual runtime calls;
- explicit bridge from source registry / typed families into final read-path ranking;
- topic/approval routing observability in Telegram runtime layer;
- live status/health surface that currently times out or disappears.

---

## Confidence update

### Verified
- source registry exists and is seeded;
- typed Memory Core relational schema/write surface exists;
- routing-policy result artifacts demonstrate differentiated authority behavior;
- context assembly is part of the broader architecture plan.

### Still unverified
- live DB connectivity state during current runtime;
- whether relational `mc_*` storage is actively populated in current production path vs foundation-only contour;
- exact runtime bridge from retrieval outputs into final prompt injection;
- exact cause of Telegram approval events landing at group-level rather than topic-level;
- exact cause of `openclaw status` timeout and silent subagent death.

---

## Final pass-2 verdict

The deployed memory contour is stronger than a simple heuristic markdown retriever and weaker than a fully observable typed memory platform.

The most accurate label now is:

> **policy-routed hybrid memory architecture with typed-core foundations and incomplete runtime observability**.
