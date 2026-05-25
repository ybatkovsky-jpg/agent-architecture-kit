# Agent Architecture Kit

A GitHub-ready product repository for reusable agent-system architecture patterns.

This repository packages a set of architectural contours that emerged from real operator use and iterative refinement:

- memory as selective continuity rather than transcript storage;
- task state as operational source of truth;
- truth resolution across memory, tasks, and artifacts;
- thin-main / bounded isolated execution;
- approval-ready media and publish seam design for review-gated content workflows;
- publish runtime state-machine design for schedule/retry/lock-aware delivery;
- plan / task / queue sync design for linked publishing workflows;
- regression and promotion-gate discipline for architecture changes.

The goal is not to ship one monolithic framework, but a clear architecture kit that others can read, adapt, and implement in their own agent systems.

This repository now includes both architecture docs and a minimal Python reference implementation.

## Start here

If you want the fastest way to navigate the current exported corpus, read:

- [`EXPORT_INDEX.md`](./EXPORT_INDEX.md) — canonical map of the repository
- [`docs/architecture/README.md`](./docs/architecture/README.md)
- [`docs/memory/README.md`](./docs/memory/README.md)
- [`docs/evaluation/README.md`](./docs/evaluation/README.md)

If you specifically want the sanitized live-system exports, go to:

- [`exports/memory-core/`](./exports/memory-core/)
- [`exports/task-manager-core/`](./exports/task-manager-core/)
- [`exports/architecture-support-pack/`](./exports/architecture-support-pack/)

---

## What is inside

### Core architecture contours

A deeper export now also lives under `docs/architecture/`, `docs/memory/`, and `docs/evaluation/`.

1. **Memory Contour**
   - retrieval
   - distillation
   - protected memory
   - truth hierarchy
   - memory write discipline

2. **Task State Contour**
   - task manager as operational source of truth
   - task / artifact / memory separation
   - lifecycle discipline
   - status and dependency semantics

3. **Execution Contour**
   - thin main orchestrator
   - bounded isolated execution
   - explicit ownership
   - ACK / DONE / BLOCKED handoff contract
   - retry and escalation budgets

4. **Evaluation Contour**
   - regression harnesses
   - protected cases
   - comparable coverage
   - dataset delta checks
   - promotion gate realism

5. **Truth Resolution Contour**
   - domain-specific source of truth
   - canonical-over-raw resolution
   - freshness and supersession handling
   - conflict-aware retrieval/application

6. **Approval/Publish Seam Contour**
   - approval-card vs approval-media contract split
   - placeholder-vs-real-asset handling
   - pre-approval media materialization
   - publish consuming the same resolved media payload

7. **Publish Runtime Contour**
   - approval/schedule/retry/lock gating
   - classified failures and retry budgets
   - task-level publish aggregation
   - terminal delivery state semantics

8. **Plan / Task / Queue Sync Contour**
   - linked identities across planning, execution, and delivery
   - directional synchronization instead of whole-object overwrite
   - queue generation via plan or task bridge
   - rework/schedule propagation across layers

---

## Repository structure

```text
agent-architecture-kit/
├── README.md
├── docs/
│   ├── learning/
│   │   └── architecture-config.v0_1.example.yaml
│   ├── architecture/
│   │   ├── README.md
│   │   ├── frame-baseline-v1.md
│   │   ├── handoff-contract-v1.md
│   │   ├── routing-ownership-map-v1.md
│   │   ├── retry-escalation-budget-policy-v1.md
│   │   ├── memory-distillation-cadence-v1.md
│   │   ├── control-plane-spec-v0-1.md
│   │   ├── truth-boundary-contract.md
│   │   ├── implementation-mapping.md
│   │   ├── current-state-and-next-steps.md
│   │   ├── structured-compression-contract-v1.md
│   │   ├── session-lifecycle-prevention-spec.md
│   │   ├── media-approval-and-publish-seam.md
│   │   ├── publish-runtime-state-machine.md
│   │   ├── plan-task-queue-sync-contour.md
│   │   ├── promotion-gates/
│   │   │   ├── openclaw-frame-continuation-contract-v1.md
│   │   │   └── markdown-promotion-gate-spec-v0-1.md
│   │   ├── policies/
│   │   │   ├── openclaw-frame-canonical-anchor-and-storage-policy-v1.md
│   │   │   ├── openclaw-frame-context-serving-policy-v1.md
│   │   │   └── openclaw-frame-serving-class-matrix-v1.md
│   │   └── schemas/
│   │       └── promotion-gate-verdict-schema-v1.md
│   ├── memory/
│   │   ├── README.md
│   │   ├── memory-stack-v2.md
│   │   ├── memory-core-v1.md
│   │   ├── retrieval-policy-matrix.md
│   │   └── authority-priority.md
│   ├── evaluation/
│   │   ├── README.md
│   │   ├── evaluation-harness-v0-1.md
│   │   ├── protected-regression-layer-v0-1.md
│   │   ├── acceptance-scenarios.md
│   │   ├── failure-modes-and-hardening.md
│   │   └── release-recommendation-contours.md
│   ├── architecture-overview.md
│   ├── memory-contour.md
│   ├── task-manager-integration.md
│   ├── isolated-execution.md
│   ├── eval-regression.md
│   └── github-primer-ru.md
├── schemas/
│   ├── memory-item.schema.json
│   ├── task-summary.schema.json
│   ├── trace-summary.schema.json
│   └── promotion-gate-verdict-v1.schema.json
├── examples/
│   ├── truth-hierarchy-example.md
│   ├── memory-distillation-example.md
│   ├── task-memory-artifact-example.md
│   ├── serving-policy/
│   │   └── openclaw-frame-serving-class-matrix-v1.json
│   └── promotion-gate/
│       └── fixtures/
│           ├── known-pass-schema.md
│           ├── known-hold-internal.md
│           ├── known-sanitize-architecture.md
│           └── known-review-competing-buckets.md
├── src/
│   └── agent_architecture_kit/
│       ├── __init__.py
│       ├── memory.py
│       ├── models.py
│       ├── tasks.py
│       ├── trace.py
│       ├── truth.py
│       └── evaluation.py
├── tests/
│   ├── test_core.py
│   └── test_evaluation.py
├── scripts/
│   ├── promotion_gate.py
│   ├── verify_promotion_gate_cases.py
│   └── architecture/
│       ├── load_arch_config.py
│       ├── emit_trace.py
│       ├── score_trace.py
│       ├── eval_policy.py
│       ├── run_protected_cases.py
│       ├── regression_report.py
│       ├── run_regression_suite.py
│       ├── controlled_baseline_refresh.py
│       ├── verify_continuation_cases.py
│       ├── context_serving_evaluator.py
│       ├── run_stage2_demo.py
│       └── fixtures/
│           └── continuation_verifier/
│               ├── known-pass-done.json
│               ├── known-pass-blocked-direct.json
│               └── known-fail-done-without-ack.json
├── evals/
│   └── architecture/
│       ├── sampled_cases/
│       │   └── trace-demo-001.json
│       ├── score_reports/
│       │   └── demo_score_report.json
│       └── fixtures/
│           └── context-serving-fixtures.json
└── notes/
    └── export-boundary.md
```

---

## Who this is for

This repo is useful if you are building:

- an assistant that works across many sessions;
- a tool-using agent that needs durable state;
- a task-driven operator assistant;
- an architecture/eval loop for agent improvement;
- a system where chat history alone is not a sufficient memory model.

---

## Core ideas in one page

### 1. Memory is not full transcript retention
Useful memory is selective.
It should preserve decisions, patterns, anti-patterns, blockers with reuse value, and canonical references.

### 2. Tasks are not the same as memory
A task registry remembers work state.
Memory remembers meaning.
Artifacts remember detail.

### 3. Truth is domain-specific
For task status, the task registry should win.
For long-term user preferences, curated memory should win.
For deep implementation context, linked artifacts often win.

### 4. Main should stay thin
The conversational surface should remain an orchestration and decision surface, not the default sink for heavy execution.

### 5. Every architecture claim should be testable
If a contour matters, it should be evaluable, regression-protected, and measurable.

### 6. Execution state needs lifecycle discipline
Bounded execution sessions should not linger indefinitely after delivery. Session pressure, checkpoint growth, and stale hot state are architecture problems, not just operational annoyances.

### 7. Compression should preserve anchors, not replace them
A compressed context window can carry structured continuity aids, but canonical task, artifact, memory, and handoff references must remain authoritative.

---

## Suggested public/private split

### Public-safe by default
- architecture principles
- neutral schemas
- examples with redacted specifics
- evaluation methodology
- generic handoff contracts
- generic memory/task patterns

### Keep private or sanitize first
- real chat ids
- user-specific memory
- private artifacts and operational logs
- secrets, tokens, infrastructure details
- environment-specific paths unless intentionally documented

---

## How to use this repo

### Option A — Read-only architecture reference
Use the docs as a design guide while implementing in your own stack.

### Option B — Starter kit
Adopt the schemas, examples, policy ideas, and minimal Python modules as a scaffold for your own architecture.

### Option C — Evolving architecture repository
Treat this repo as a living product surface:
- document contours;
- add examples;
- add evaluation cases;
- version changes explicitly.

---

## Initial roadmap

- [ ] refine architecture overview into v1 public form
- [ ] convert internal patterns into sanitized public docs
- [ ] add machine-readable policy/eval examples
- [x] add regression case examples
- [x] add minimal Python reference implementation
- [x] add reference implementation notes for evaluation/release gates

---

## License

TBD by repository owner.

A practical choice is usually one of:
- MIT — most permissive;
- Apache-2.0 — permissive with patent language;
- AGPL-3.0 — forces networked derivatives to stay open.

---

## Short glossary

- **Repository / repo** — a project folder tracked by Git.
- **Git** — version-control system.
- **GitHub** — hosting platform for Git repositories.
- **Commit** — saved change snapshot.
- **Branch** — parallel line of work.
- **Pull Request (PR)** — proposed changes to merge into a branch.
- **Issue** — tracked problem, task, or idea.
- **Release** — named published version of the repo.

For a fuller Russian explanation, see `docs/github-primer-ru.md`.
