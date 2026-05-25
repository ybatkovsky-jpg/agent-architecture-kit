# OpenClaw Architecture Evolution Timeline

A short chronology of how the currently exported OpenClaw architecture contours emerged.

This is not a full task ledger.
It is a reader-oriented timeline for the four main lines that now matter most in this repository:

1. Memory
2. Task Manager / autonomy
3. OpenClaw Frame
4. Context System 2

---

## 1. Early execution-control foundation

### 2026-04-24 to 2026-04-25
Initial control-plane and watchdog contours appear.

Key themes:
- fresh task-scoped bootstrap
- watchdog routing
- background worker / writeback discipline
- early autonomy safety boundaries

Representative sources:
- `exports/task-manager-core/artifacts/fresh-task-scoped-bootstrap-contract-2026-04-24.md`
- `task-manager` source lineage around watchdog / closure loop
- `exports/task-manager-core/artifacts/task-78-watchdog-phase2-writeback-validation-2026-04-25.md`

Main architectural shift:
- execution is no longer treated as just long chat continuation;
- it starts becoming a governed runtime with explicit watchdog and state semantics.

---

## 2. Frame baseline and thin-main direction

### 2026-04-28 to 2026-05-03
OpenClaw Frame becomes a named execution/orchestration contour.

Key themes:
- thin main orchestrator
- bounded isolated execution
- handoff contracts
- routing ownership
- retry / escalation budgets
- blind-judge and closure discipline

Representative sources:
- `exports/architecture-support-pack/tm-artifacts/openclaw-architecture-implementation-plan-2026-04-28.md`
- `exports/architecture-support-pack/tm-artifacts/openclaw-execution-context-schema-implementation-facing-v1-2026-04-28.md`
- `exports/architecture-support-pack/tm-artifacts/openclaw-frame-architecture-baseline-v1-2026-05-01.md`
- `exports/architecture-support-pack/tm-artifacts/openclaw-frame-handoff-spec-v1-2026-05-01.md`
- `exports/architecture-support-pack/tm-artifacts/openclaw-frame-routing-ownership-map-v1-2026-05-01.md`
- `exports/task-manager-core/artifacts/task-273-blind-judge-spec-v1-2026-05-02.md`

Main architectural shift:
- `main` is explicitly reframed as orchestrator rather than primary execution runtime.

---

## 3. Memory Core v1 program

### 2026-05-06 to 2026-05-07
Memory moves from broad stack ideas into a concrete typed/runtime program.

Key themes:
- Memory Core v1 scope freeze
- schema conformance
- registry / typed links / decisions / session capsules / task metadata
- retrieval policy matrix
- request classification and routing policy
- authority priority, citation envelope, conflict/open-question synthesis
- evaluation and bounded hardening

Representative task clusters:
- scope/spec: `#342`, `#346`
- schema/runtime baseline: `#347`, `#348`
- write surfaces: `#349`-`#357`
- retrieval policy/routing: `#358`-`#363`
- evaluation/hardening: `#364`-`#377`

Representative exported materials:
- `docs/memory/memory-core-v1.md`
- `docs/memory/retrieval-policy-matrix.md`
- `exports/memory-core/*`
- `exports/task-manager-core/artifacts/task-409-memory-stack-improvement-spec-2026-05-12.md`

Main architectural shift:
- memory stops being discussed only as general “agent memory” and becomes a typed, policy-routed serving system with explicit write/read surfaces.

---

## 4. Evaluation and promotion discipline hardening

### 2026-05-05 to 2026-05-12
Evaluation becomes first-class architecture, not an afterthought.

Key themes:
- evaluation harness
- protected regressions
- continuation contracts
- promotion gates
- release recommendation logic

Representative sources:
- `docs/evaluation/evaluation-harness-v0-1.md`
- `docs/evaluation/protected-regression-layer-v0-1.md`
- `docs/evaluation/release-recommendation-contours.md`
- `exports/task-manager-core/artifacts/task-392-architecture-promotion-gate-script-v0-1-spec-2026-05-12.md`
- `exports/task-manager-core/artifacts/task-399-promotion-gate-destination-action-mapping-v0-1-2026-05-12.md`
- `exports/memory-core/CONTINUATION_RETRIEVAL_CONTRACT_V1.md`

Main architectural shift:
- architecture changes require bounded verification artifacts and promotion logic, not just prose confidence.

---

## 5. Memory runtime reality-map and target-architecture phase

### 2026-05-12 to 2026-05-14
The focus shifts from only Memory Core pieces to the broader deployed runtime contour.

Key themes:
- runtime audit of the live memory contour
- target architecture for cleaner serving
- freshness / ingestion policy
- observability / trace debug
- phased rollout and verification
- typed serving plane and runtime cleanup

Representative sources:
- `exports/architecture-support-pack/memory-docs/MEMORY_RUNTIME_AUDIT_PRELIM_2026-05-13.md`
- `exports/architecture-support-pack/memory-docs/MEMORY_RUNTIME_AUDIT_PASS2_2026-05-13.md`
- `exports/architecture-support-pack/memory-docs/MEMORY_RUNTIME_AUDIT_LIVE_2026-05-13.md`
- `exports/architecture-support-pack/memory-docs/MEMORY_TARGET_ARCHITECTURE_V1_2026-05-13.md`
- `docs/memory/runtime-improvement-overview.md`
- `docs/memory/runtime-serving-architecture.md`
- `docs/memory/freshness-and-ingestion-policy.md`
- `docs/memory/observability-and-trace-debug.md`
- `docs/memory/phased-rollout-and-verification.md`

Main architectural shift:
- the repo begins distinguishing sharply between the deployed hybrid reality and the desired cleaner target memory architecture.

---

## 6. Bootstrap and thin-main memory contour

### 2026-05-14 onward
Attention expands from retrieval alone to what gets loaded into runtime and when.

Key themes:
- isolated bootstrap contract
- bootstrap index
- first runtime capsules
- conditional load
- thin-main memory contour

Representative sources:
- `exports/task-manager-core/artifacts/task-468-isolated-bootstrap-contract-and-bootstrap-index-proposal-2026-05-14.md`
- `exports/task-manager-core/artifacts/task-468-first-runtime-bootstrap-capsules-and-wiring-proposal-2026-05-14.md`
- `docs/bootstrap-contour.md`

Main architectural shift:
- memory architecture is no longer only storage/retrieval;
- it becomes tied to runtime bootstrap and surface admission.

---

## 7. Context System 2

### 2026-05-19
Context System 2 formalizes the next step after thin-main and bootstrap work.

Key themes:
- thin main + pack-driven assembly
- strict surface admission
- context manifests
- pack admission schema
- runtime assembly binding
- role-specific surfaces

Representative sources:
- `exports/architecture-support-pack/tm-artifacts/context-system-2-target-design-spec-2026-05-19.md`
- `exports/architecture-support-pack/tm-artifacts/context-system-2-surface-manifest-schema-2026-05-19.md`
- `exports/architecture-support-pack/tm-artifacts/context-system-2-pack-admission-schema-2026-05-19.md`
- `exports/architecture-support-pack/tm-artifacts/context-system-2-runtime-assembly-binding-plan-2026-05-19.md`
- `exports/architecture-support-pack/tm-artifacts/context-system-2-first-surface-manifests-2026-05-19.md`

Main architectural shift:
- the system moves from “some slimming and packs” to an explicit prompt/context assembly architecture with strict admission boundaries.

---

## 8. Memory v1 canonical production and lifecycle loop

### 2026-05-20 to 2026-05-21
The memory line moves toward production-shape synthesis.

Key themes:
- canonical production contract
- lifecycle loop
- rollout verification
- production readiness proof

Representative sources:
- `task-manager/artifacts/task-544-memory-v1-canonical-production-contract-2026-05-20.md`
- `task-manager/artifacts/task-546-memory-v1-lifecycle-loop-contract-and-rollout-slice-2026-05-20.md`
- `task-manager/artifacts/task-549-memory-v1-rollout-verification-and-production-readiness-proof-2026-05-20.md`
- `exports/architecture-support-pack/curated-proof-pack/task-546-lifecycle-slice-verification-2026-05-21/verification-report.json`

Main architectural shift:
- memory is treated as an operational lifecycle with rollout proof, not just a design target.

---

## 9. Surfaced-recorded execution integrity and autonomy hardening

### 2026-05-24 to 2026-05-25
Task Manager evolves from generic autonomy enforcement into stronger honesty/integrity guarantees.

Key themes:
- anti-silence and forced-status surfacing
- anti-hesitation enforcement
- structured observability
- surfaced-recorded execution integrity
- closure-proof hardening awareness

Representative sources:
- `docs/architecture/surfaced-recorded-execution-integrity-contract.md`
- `exports/task-manager-core/test_autonomy_observability.py`
- `exports/task-manager-core/test_autonomy_anti_hesitation.py`
- `exports/task-manager-core/artifacts/tm-multi-pass-closure-loop-change-list-2026-05-24.md`
- `exports/task-manager-core/artifacts/autonomy-guardrail-change-list-2026-05-24.md`

Main architectural shift:
- the system starts explicitly defending against pseudo-activity and unsurfaced execution, not only against technical failure.

---

## 10. Summary arc

A short way to read the overall evolution:

1. **Control and watchdog discipline**
2. **Frame / thin-main execution architecture**
3. **Typed Memory Core v1**
4. **Evaluation and promotion hardening**
5. **Runtime memory audit and target architecture**
6. **Bootstrap and context admission**
7. **Context System 2**
8. **Production/lifecycle proof**
9. **Execution integrity and anti-pseudo-activity hardening**

That arc is the main reason this repository now has both:
- polished architecture docs, and
- source-adjacent sanitized exports.
