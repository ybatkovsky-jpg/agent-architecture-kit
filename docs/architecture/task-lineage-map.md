# Task Lineage Map

A reader-oriented lineage map for the major task groups that produced the exported OpenClaw architecture contours.

This file is not a full task-manager dump.
It is a structural guide showing which task families generated which durable architecture lines.

Primary emphasis:
- memory/runtime program
- frame / execution program
- autonomy / integrity program
- context/bootstrap program

---

## 1. How to read this map

Each section shows:
- **task family**
- **architectural outcome**
- **main exported traces**

Where possible, tasks are grouped by program rather than listed individually without structure.

---

## 2. Memory Core v1 lineage

## 2.1 Scope and baseline family

### Main task family
- `#342` — freeze v1 scope and non-scope
- `#346` — Memory Core v1 spec draft/skeleton
- `#347` — schema/runtime conformance
- `#348` — baseline bootstrap / migration

### Architectural outcome
This family established that Memory Core v1 was a bounded typed-memory program rather than a vague “future memory” idea.

### Main exported traces
- `docs/memory/memory-core-v1.md`
- `exports/memory-core/sql/040_memory_core_v1_baseline.sql`
- `exports/memory-core/memory_core_registry.py`
- `exports/task-manager-core/artifacts/task-409-memory-stack-improvement-spec-2026-05-12.md`

---

## 2.2 Write-surface family

### Main task family
- `#349` registry write surface
- `#350` typed links write path
- `#351` decisions/session capsules write path
- `#352` storage smoke checks
- `#353` task metadata ingest
- `#354` batch reingest/task metadata
- `#355` decision ingest update path
- `#356` session capsule distiller
- `#357` provenance link integrity

### Architectural outcome
This family turned Memory Core into a real write/read surface with typed object families instead of just a schema shell.

### Main exported traces
- `exports/memory-core/memory_core_registry.py`
- `exports/memory-core/memory_core_typed_links.py`
- `exports/memory-core/memory_core_decisions_sessions.py`
- `exports/memory-core/memory_core_session_capsule_distiller.py`
- `exports/memory-core/memory_core_task_metadata.py`
- `exports/architecture-support-pack/curated-proof-pack/task-357-provenance-link-integrity/verification-report.json`

---

## 2.3 Retrieval policy and serving family

### Main task family
- `#358` retrieval policy matrix
- `#359` request classifier
- `#360` routing policy enforcement
- `#361` authority priority ranking
- `#362` citation envelope
- `#363` conflict/open-question synthesis

### Architectural outcome
This family defines the serving contract: how requests are classified, routed, ranked, cited, and synthesized.

### Main exported traces
- `docs/memory/retrieval-policy-matrix.md`
- `docs/memory/authority-priority.md`
- `exports/memory-core/retrieval_classification.py`
- `exports/memory-core/retrieve_memory.py`
- `exports/memory-core/RETRIEVAL_POLICY_MATRIX_V1.md`
- `exports/memory-core/META_EVALUATION_RECALL_CONTRACT_V1.md`

---

## 2.4 Evaluation and hardening family

### Main task family
- `#364` acceptance scenarios
- `#365` end-to-end scenario evaluation
- `#366` failure modes and hardening log
- `#367` evaluation summary and release recommendation
- `#368` meta-artifact suppression hardening
- `#369` continuation freshness hardening
- `#370` continuation/meta alignment hardening
- `#371` continuation retrieval contract and regression pack
- `#376` bounded reeval summary
- `#377` status handoff hardening

### Architectural outcome
This family gives the memory line its evaluation discipline and retrieval-hardening credibility.

### Main exported traces
- `docs/evaluation/acceptance-scenarios.md`
- `docs/evaluation/failure-modes-and-hardening.md`
- `docs/evaluation/release-recommendation-contours.md`
- `exports/memory-core/CONTINUATION_RETRIEVAL_CONTRACT_V1.md`
- `exports/architecture-support-pack/curated-proof-pack/meta-evaluation-routing-regression-2026-05-12/verification-report.json`
- `exports/architecture-support-pack/curated-proof-pack/meta-lane-regression-mini-pack-2026-05-07/verification-report.json`

---

## 3. Memory runtime v2 / production-shape lineage

## 3.1 Runtime reality and target-design family

### Main task family
- `#409` memory stack improvement spec
- `#411` reality map and health-check delta
- `#455` runtime contour improvement spec
- `#456` runtime architecture and serving contract
- `#457` freshness and ingestion policy
- `#461` observability and trace debug
- `#462` phased rollout and verification plan

### Architectural outcome
This family moved the project from Memory Core internals to whole-runtime understanding: what is actually deployed, what target architecture is desired, and what rollout path bridges them.

### Main exported traces
- `docs/memory/runtime-improvement-overview.md`
- `docs/memory/runtime-serving-architecture.md`
- `docs/memory/freshness-and-ingestion-policy.md`
- `docs/memory/observability-and-trace-debug.md`
- `docs/memory/phased-rollout-and-verification.md`
- `exports/architecture-support-pack/memory-docs/MEMORY_RUNTIME_AUDIT_LIVE_2026-05-13.md`
- `exports/architecture-support-pack/memory-docs/MEMORY_TARGET_ARCHITECTURE_V1_2026-05-13.md`

---

## 3.2 Bootstrap / startup / thin-main memory family

### Main task family
- `#468` isolated bootstrap contract and bootstrap index
- `#471` startup metadata closure
- `#472` bootstrap index wiring
- `#473` first runtime bootstrap capsules
- `#474` conditional bootstrap load isolated run
- `#475` thin-main bootstrap memory contour
- `#476` strategist bootstrap memory contour

### Architectural outcome
This family ties memory architecture to runtime loading and thin-main context discipline.

### Main exported traces
- `docs/bootstrap-contour.md`
- `exports/task-manager-core/artifacts/task-468-isolated-bootstrap-contract-and-bootstrap-index-proposal-2026-05-14.md`
- `exports/task-manager-core/artifacts/task-468-first-runtime-bootstrap-capsules-and-wiring-proposal-2026-05-14.md`

---

## 3.3 Cleanup / hardening / production family

### Main task family
- `#479` mixed-domain/general-fact hardening
- `#480` runtime cleanup roadmap / program / execution spine
- `#544` memory v1 canonical production contract
- `#546` memory v1 lifecycle loop contract and rollout slice
- `#549` rollout verification and production readiness proof

### Architectural outcome
This family turns the memory line into a production-readiness and lifecycle-governed program.

### Main exported traces
- `docs/memory/typed-memory-serving-plane.md`
- `exports/task-manager-core/artifacts/task-479-memory-hardening-general-fact-domains-spec-2026-05-14.md`
- `exports/task-manager-core/artifacts/task-480-memory-runtime-cleanup-roadmap-2026-05-14.md`
- `exports/architecture-support-pack/curated-proof-pack/task-546-lifecycle-slice-verification-2026-05-21/verification-report.json`

---

## 4. Frame / execution program lineage

## 4.1 Frame baseline family

### Main task family
- early rollout/planning around `#217`, `#227`, `#228`, `#229`
- later baseline crystallization around `#271`, `#273`, `#278`, `#280`

### Architectural outcome
This family defines OpenClaw Frame as a distinct execution/orchestration architecture with thin main, handoff, routing, and bounded retry semantics.

### Main exported traces
- `docs/architecture/frame-baseline-v1.md`
- `docs/architecture/handoff-contract-v1.md`
- `docs/architecture/routing-ownership-map-v1.md`
- `docs/architecture/retry-escalation-budget-policy-v1.md`
- `exports/architecture-support-pack/tm-artifacts/openclaw-frame-architecture-baseline-v1-2026-05-01.md`

---

## 4.2 Policy and promotion family

### Main task family
- `#391`, `#393`, `#395`, `#396`, `#401`, `#402`, `#403`, `#406`, `#420`, `#421`

### Architectural outcome
This family extends the frame line with:
- canonical anchors
- context serving policy
- serving class matrix
- scenario-pack and bounded-check promotion discipline

### Main exported traces
- `docs/architecture/policies/openclaw-frame-canonical-anchor-and-storage-policy-v1.md`
- `docs/architecture/policies/openclaw-frame-context-serving-policy-v1.md`
- `docs/architecture/policies/openclaw-frame-serving-class-matrix-v1.md`
- `docs/architecture/promotion-gates/openclaw-frame-continuation-contract-v1.md`
- `docs/architecture/schemas/promotion-gate-verdict-schema-v1.md`

---

## 5. Task Manager autonomy / integrity lineage

## 5.1 Early watchdog/control family

### Main task family
- fresh bootstrap / watchdog line around `#78`, `#177`, `#240`, `#307`

### Architectural outcome
This family builds the early durable control plane for autonomous execution.

### Main exported traces
- `exports/task-manager-core/artifacts/fresh-task-scoped-bootstrap-contract-2026-04-24.md`
- `exports/task-manager-core/artifacts/task-78-watchdog-phase2-writeback-validation-2026-04-25.md`
- `exports/task-manager-core/artifacts/task-240-multi-run-arbitration-policy-closure-cut-2026-04-29.md`
- `exports/task-manager-core/artifacts/task-307-control-plane-priority-and-preemption-model-2026-05-06.md`

---

## 5.2 Closure and guardrail family

### Main task family
- late autonomy hardening around `#756`, `#757`, `#758`, `#759`, `#763`

### Architectural outcome
This family hardens the system against:
- silent pseudo-progress
- unsurfaced terminal results
- anti-hesitation loops
- weak execution observability
- integrity drift between surfaced work and recorded work

### Main exported traces
- `docs/architecture/surfaced-recorded-execution-integrity-contract.md`
- `exports/task-manager-core/test_autonomy_observability.py`
- `exports/task-manager-core/test_autonomy_anti_hesitation.py`
- `exports/task-manager-core/artifacts/tm-multi-pass-closure-loop-change-list-2026-05-24.md`
- `exports/task-manager-core/artifacts/autonomy-guardrail-change-list-2026-05-24.md`

---

## 6. Context System 2 lineage

### Main task family
- Context System 2 cluster on 2026-05-19

Representative tasks/artifacts:
- `context-system-2-target-design-spec`
- `context-system-2-surface-manifest-schema`
- `context-system-2-pack-admission-schema`
- `context-system-2-runtime-assembly-binding-plan`
- `context-system-2-first-surface-manifests`
- related runtime rebind / stub / seam mapping notes

### Architectural outcome
This family is the direct descendant of the thin-main + bootstrap line, but focused specifically on context assembly and admission boundaries.

### Main exported traces
- `exports/architecture-support-pack/tm-artifacts/context-system-2-target-design-spec-2026-05-19.md`
- `exports/architecture-support-pack/tm-artifacts/context-system-2-surface-manifest-schema-2026-05-19.md`
- `exports/architecture-support-pack/tm-artifacts/context-system-2-pack-admission-schema-2026-05-19.md`
- `exports/architecture-support-pack/tm-artifacts/context-system-2-runtime-assembly-binding-plan-2026-05-19.md`

---

## 7. Short lineage summary

If compressed to the simplest map, the architecture lineage looks like this:

1. **Watchdog/control and bootstrap discipline**
2. **Frame / thin-main execution architecture**
3. **Memory Core v1 typed surfaces**
4. **Retrieval policy and evaluation hardening**
5. **Memory runtime audit and target serving architecture**
6. **Bootstrap and thin-main memory loading**
7. **Context System 2 prompt/context assembly architecture**
8. **Production/lifecycle memory program**
9. **Execution integrity and anti-pseudo-activity autonomy hardening**

That lineage is the main backbone behind the exported repository.
