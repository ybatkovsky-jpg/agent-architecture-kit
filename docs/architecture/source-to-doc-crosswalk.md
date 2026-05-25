# Source-to-Doc Crosswalk

A practical mapping from live source files / artifact origins to the exported architectural documents and packages in this repository.

This file is intentionally selective.
It focuses on the most important crosswalks for Memory, Task Manager, Frame, and Context System 2.

---

## 1. How to read this table

- **Live source / origin** = where the idea or implementation lived in the operational workspace
- **Exported doc / package** = where the sanitized architectural representation now lives in this repository
- **Type** = code, artifact, architecture doc, support doc, or proof
- **Notes** = how literal vs synthesized the export is

---

## 2. Memory crosswalk

| Live source / origin | Exported doc / package | Type | Notes |
|---|---|---|---|
| `pkm-memory/memory_core_registry.py` | `exports/memory-core/memory_core_registry.py` | code export | direct sanitized code export |
| `pkm-memory/memory_core_typed_links.py` | `exports/memory-core/memory_core_typed_links.py` | code export | direct sanitized code export |
| `pkm-memory/memory_core_decisions_sessions.py` | `exports/memory-core/memory_core_decisions_sessions.py` | code export | direct sanitized code export |
| `pkm-memory/memory_core_session_capsule_distiller.py` | `exports/memory-core/memory_core_session_capsule_distiller.py` | code export | direct sanitized code export |
| `pkm-memory/memory_core_task_metadata.py` | `exports/memory-core/memory_core_task_metadata.py` | code export | direct sanitized code export |
| `pkm-memory/retrieve_memory.py` | `exports/memory-core/retrieve_memory.py` | code export | main retrieval runtime export |
| `pkm-memory/retrieval_classification.py` | `exports/memory-core/retrieval_classification.py` | code export | request classification/runtime routing export |
| `pkm-memory/RETRIEVAL_POLICY_MATRIX_V1.md` | `exports/memory-core/RETRIEVAL_POLICY_MATRIX_V1.md` and `docs/memory/retrieval-policy-matrix.md` | contract + architecture doc | one direct export plus one repository-native canonicalized doc |
| `pkm-memory/META_EVALUATION_RECALL_CONTRACT_V1.md` | `exports/memory-core/META_EVALUATION_RECALL_CONTRACT_V1.md` | contract | direct exported contract |
| `pkm-memory/CONTINUATION_RETRIEVAL_CONTRACT_V1.md` | `exports/memory-core/CONTINUATION_RETRIEVAL_CONTRACT_V1.md` | contract | direct exported contract |
| `pkm-memory/RETRIEVAL_LANE_CONTRACTS_V1.md` | `exports/memory-core/RETRIEVAL_LANE_CONTRACTS_V1.md` | contract | direct exported contract |
| `pkm-memory/RETRIEVAL_PAYLOAD_CONTRACT_V1.md` | `exports/memory-core/RETRIEVAL_PAYLOAD_CONTRACT_V1.md` | contract | direct exported contract |
| `pkm-memory/sql/040_memory_core_v1_baseline.sql` | `exports/memory-core/sql/040_memory_core_v1_baseline.sql` and `docs/memory/memory-core-v1.md` | schema + architecture doc | schema exported directly; doc is synthesized architecture layer |
| `task-manager/artifacts/task-346-memory-core-spec-v1-draft-2026-05-06.md` | `docs/memory/memory-core-v1.md` | architecture doc | synthesized from task artifact line |
| `task-manager/artifacts/task-358-memory-core-v1-retrieval-policy-matrix-handoff-2026-05-06.md` | `docs/memory/retrieval-policy-matrix.md` | architecture doc | canonicalized from rollout/handoff artifact |
| `task-manager/artifacts/task-455-openclaw-memory-runtime-contour-improvement-spec-2026-05-13.md` | `docs/memory/runtime-improvement-overview.md` and `exports/task-manager-core/artifacts/task-455-openclaw-memory-runtime-contour-improvement-spec-2026-05-13.md` | architecture doc + artifact export | both polished and source-adjacent forms kept |
| `task-manager/artifacts/task-456-openclaw-memory-runtime-architecture-and-serving-contract-2026-05-13.md` | `docs/memory/runtime-serving-architecture.md` and matching exported artifact | architecture doc + artifact export | canonical doc plus artifact provenance |
| `task-manager/artifacts/task-457-openclaw-memory-freshness-and-ingestion-policy-2026-05-13.md` | `docs/memory/freshness-and-ingestion-policy.md` and matching exported artifact | architecture doc + artifact export | polished plus source-adjacent |
| `task-manager/artifacts/task-461-memory-runtime-observability-and-trace-debug-contour-2026-05-13.md` | `docs/memory/observability-and-trace-debug.md` and matching exported artifact | architecture doc + artifact export | same contour in two layers |
| `task-manager/artifacts/task-462-memory-runtime-phased-rollout-and-verification-plan-2026-05-13.md` | `docs/memory/phased-rollout-and-verification.md` and matching exported artifact | architecture doc + artifact export | rollout plan canonicalized |
| `docs/MEMORY_TARGET_ARCHITECTURE_V1_2026-05-13.md` in live workspace | `exports/architecture-support-pack/memory-docs/MEMORY_TARGET_ARCHITECTURE_V1_2026-05-13.md` | support doc export | preserved as source-adjacent architecture support |
| `docs/MEMORY_RUNTIME_AUDIT_LIVE_2026-05-13.md` in live workspace | `exports/architecture-support-pack/memory-docs/MEMORY_RUNTIME_AUDIT_LIVE_2026-05-13.md` | support doc export | preserved audit artifact |

---

## 3. Task Manager / autonomy crosswalk

| Live source / origin | Exported doc / package | Type | Notes |
|---|---|---|---|
| `task-manager/autonomy_state.py` | `exports/task-manager-core/autonomy_state.py` | code export | direct sanitized code export |
| `task-manager/test_autonomy_router.py` | `exports/task-manager-core/test_autonomy_router.py` | proof/test export | regression anchor |
| `task-manager/test_autonomy_watchdog.py` | `exports/task-manager-core/test_autonomy_watchdog.py` | proof/test export | watchdog enforcement proof |
| `task-manager/test_autonomy_resume.py` | `exports/task-manager-core/test_autonomy_resume.py` | proof/test export | resume semantics proof |
| `task-manager/test_autonomy_observability.py` | `exports/task-manager-core/test_autonomy_observability.py` | proof/test export | observability proof |
| `task-manager/test_autonomy_anti_hesitation.py` | `exports/task-manager-core/test_autonomy_anti_hesitation.py` | proof/test export | anti-hesitation proof |
| `task-manager/STRUCTURED_ADAPTER_CONTRACT.md` | `exports/task-manager-core/STRUCTURED_ADAPTER_CONTRACT.md` | contract export | direct sanitized export |
| `task-manager/artifacts/task-240-multi-run-arbitration-policy-closure-cut-2026-04-29.md` | `exports/task-manager-core/artifacts/task-240-multi-run-arbitration-policy-closure-cut-2026-04-29.md` | artifact export | source-adjacent autonomy lineage |
| `task-manager/artifacts/task-307-control-plane-priority-and-preemption-model-2026-05-06.md` | `exports/task-manager-core/artifacts/task-307-control-plane-priority-and-preemption-model-2026-05-06.md` and `docs/architecture/control-plane-spec-v0-1.md` | artifact + architecture doc | both provenance and polished contour retained |
| `task-manager/artifacts/tm-multi-pass-closure-loop-change-list-2026-05-24.md` | `exports/task-manager-core/artifacts/tm-multi-pass-closure-loop-change-list-2026-05-24.md` | artifact export | late autonomy hardening delta |
| `task-manager/artifacts/autonomy-guardrail-change-list-2026-05-24.md` | `exports/task-manager-core/artifacts/autonomy-guardrail-change-list-2026-05-24.md` | artifact export | surfaced guardrail lineage |
| `product-repos/agent-architecture-kit/docs/architecture/surfaced-recorded-execution-integrity-contract.md` (live authored canonical doc) | `docs/architecture/surfaced-recorded-execution-integrity-contract.md` | native architecture doc | canonical architecture doc authored directly in repo |

---

## 4. OpenClaw Frame crosswalk

| Live source / origin | Exported doc / package | Type | Notes |
|---|---|---|---|
| `task-manager/artifacts/openclaw-frame-architecture-baseline-v1-2026-05-01.md` | `exports/architecture-support-pack/tm-artifacts/openclaw-frame-architecture-baseline-v1-2026-05-01.md` and `docs/architecture/frame-baseline-v1.md` | artifact + architecture doc | same contour kept in both layers |
| `task-manager/artifacts/openclaw-frame-handoff-spec-v1-2026-05-01.md` | `exports/architecture-support-pack/tm-artifacts/openclaw-frame-handoff-spec-v1-2026-05-01.md` and `docs/architecture/handoff-contract-v1.md` | artifact + architecture doc | direct provenance plus polished version |
| `task-manager/artifacts/openclaw-frame-routing-ownership-map-v1-2026-05-01.md` | `exports/architecture-support-pack/tm-artifacts/openclaw-frame-routing-ownership-map-v1-2026-05-01.md` and `docs/architecture/routing-ownership-map-v1.md` | artifact + architecture doc | same contour across layers |
| `task-manager/artifacts/openclaw-frame-retry-escalation-budget-policy-v1-2026-05-01.md` | `exports/architecture-support-pack/tm-artifacts/openclaw-frame-retry-escalation-budget-policy-v1-2026-05-01.md` and `docs/architecture/retry-escalation-budget-policy-v1.md` | artifact + architecture doc | direct/polished pair |
| `task-manager/artifacts/openclaw-frame-memory-distillation-cadence-v1-2026-05-01.md` | `exports/architecture-support-pack/tm-artifacts/openclaw-frame-memory-distillation-cadence-v1-2026-05-01.md` and `docs/architecture/memory-distillation-cadence-v1.md` | artifact + architecture doc | direct/polished pair |
| `task-manager/artifacts/openclaw-frame-continuation-contract-v1-2026-05-12.md` | `exports/architecture-support-pack/tm-artifacts/openclaw-frame-continuation-contract-v1-2026-05-12.md` and `docs/architecture/promotion-gates/openclaw-frame-continuation-contract-v1.md` | artifact + architecture doc | promotion-gate contour canonicalized |
| `task-manager/artifacts/task-395-openclaw-frame-canonical-anchor-and-storage-policy-v1-2026-05-12.md` | `docs/architecture/policies/openclaw-frame-canonical-anchor-and-storage-policy-v1.md` | architecture doc | canonicalized from task artifact |
| `task-manager/artifacts/task-396-openclaw-frame-context-serving-policy-v1-2026-05-12.md` | `docs/architecture/policies/openclaw-frame-context-serving-policy-v1.md` | architecture doc | canonicalized from task artifact |
| `task-manager/artifacts/task-420-openclaw-frame-serving-class-matrix-v1-2026-05-12.md` | `docs/architecture/policies/openclaw-frame-serving-class-matrix-v1.md` and `examples/serving-policy/openclaw-frame-serving-class-matrix-v1.json` | architecture doc + example | matrix exported as doc and example data |

---

## 5. Context System 2 crosswalk

| Live source / origin | Exported doc / package | Type | Notes |
|---|---|---|---|
| `task-manager/artifacts/context-system-2-target-design-spec-2026-05-19.md` | `exports/architecture-support-pack/tm-artifacts/context-system-2-target-design-spec-2026-05-19.md` | support artifact export | source-adjacent export |
| `task-manager/artifacts/context-system-2-surface-manifest-schema-2026-05-19.md` | `exports/architecture-support-pack/tm-artifacts/context-system-2-surface-manifest-schema-2026-05-19.md` | support artifact export | source-adjacent export |
| `task-manager/artifacts/context-system-2-pack-admission-schema-2026-05-19.md` | `exports/architecture-support-pack/tm-artifacts/context-system-2-pack-admission-schema-2026-05-19.md` | support artifact export | source-adjacent export |
| `task-manager/artifacts/context-system-2-runtime-assembly-binding-plan-2026-05-19.md` | `exports/architecture-support-pack/tm-artifacts/context-system-2-runtime-assembly-binding-plan-2026-05-19.md` | support artifact export | source-adjacent export |
| `task-manager/artifacts/context-system-2-first-surface-manifests-2026-05-19.md` | `exports/architecture-support-pack/tm-artifacts/context-system-2-first-surface-manifests-2026-05-19.md` | support artifact export | concrete manifest examples |
| `task-manager/artifacts/context-system-2-current-control-pack-map-2026-05-19.md` | `exports/architecture-support-pack/tm-artifacts/context-system-2-current-control-pack-map-2026-05-19.md` | support artifact export | control-pack mapping |

Note:
At this stage Context System 2 is preserved mostly as source-adjacent exported artifacts rather than fully rewritten polished docs. That is intentional: the contour is important, but still closer to active architecture design than finished canonical handbook form.

---

## 6. Proof crosswalk

| Live source / origin | Exported doc / package | Type | Notes |
|---|---|---|---|
| `pkm-memory/outputs/memory-core-schema-conformance/verification-report.json` | `exports/architecture-support-pack/curated-proof-pack/memory-core-schema-conformance/verification-report.json` | proof export | schema/runtime conformance summary |
| `pkm-memory/outputs/memory-core-storage-smoke/summary.json` | `exports/architecture-support-pack/curated-proof-pack/memory-core-storage-smoke/summary.json` | proof export | storage smoke summary |
| `pkm-memory/outputs/meta-evaluation-routing-regression-2026-05-12/verification-report.json` | matching file under `exports/architecture-support-pack/curated-proof-pack/` | proof export | meta routing verification |
| `pkm-memory/outputs/meta-lane-regression-mini-pack-2026-05-07/verification-report.json` | matching file under `exports/architecture-support-pack/curated-proof-pack/` | proof export | meta lane classification/routing proof |
| `pkm-memory/outputs/architecture-design-recall-regression-2026-05-12/verification-report.json` | matching file under `exports/architecture-support-pack/curated-proof-pack/` | proof export | architecture design recall proof |
| `pkm-memory/outputs/artifact-source-trace-regression-2026-05-12/verification-report.json` | matching file under `exports/architecture-support-pack/curated-proof-pack/` | proof export | artifact source trace proof |
| `pkm-memory/outputs/task-357-provenance-link-integrity/verification-report.json` | matching file under `exports/architecture-support-pack/curated-proof-pack/` | proof export | provenance integrity proof |
| `pkm-memory/outputs/task-546-lifecycle-slice-verification-2026-05-21/verification-report.json` | matching file under `exports/architecture-support-pack/curated-proof-pack/` | proof export | lifecycle loop verification |

---

## 7. Short interpretation

This repository now keeps three different but linked representations:

1. **direct code/contract exports**
2. **source-adjacent architecture/support artifacts**
3. **canonicalized polished docs**

That means the reader can move in either direction:
- from polished architecture doc toward origin/provenance,
- or from exported source artifact toward the canonicalized architectural explanation.
