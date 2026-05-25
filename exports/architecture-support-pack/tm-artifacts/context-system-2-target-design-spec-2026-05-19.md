# Context System 2 — target design spec

Date: 2026-05-19
Status: draft-for-execution
Owner lane: OpenClaw / Context System
Intent: replace the current "storage-slimmed but surface-fat" contour with a truly thin main + pack-driven + task-scoped context system.

---

## 1. Why Context System 1 did not deliver the expected thinness

Bootstrap packs and topic-specific packs were a correct direction, but they did not solve the actual failure mode.

### Core diagnosis
The current system is not failing because packs exist.
It is failing because **surface admission and always-on loading remained too broad**.

In practice:
- startup/runtime context for `main` is still too heavy;
- project context is still injected too broadly;
- long-lived sessions/topics still accumulate tail and become working memory;
- packs improved organization, but **did not become a strict admission boundary**;
- retrieval may be policy-aware, but startup composition is still too ambient.

### One-sentence diagnosis
**Context System 1 improved structure, but did not enforce thinness at the prompt assembly boundary.**

---

## 2. CS2 design objective

Create a context system where:
- `main` is truly thin and orchestration-only;
- startup always-on payload is minimal and stable;
- deep work happens in fresh task-scoped runs by default;
- topical/role knowledge is loaded only through explicit packs or on-demand retrieval;
- long history is never ambient by default;
- every loaded context item has a declared admission reason.

---

## 3. Design principles

### P1 — Default to near-empty
The system should load almost nothing by default beyond a compact universal core.

### P2 — Packs are admission boundaries, not just file organization
A pack exists to control whether something may be loaded ambiently, conditionally, on-demand, or never.

### P3 — Main is a router, not a workbench
`main` should carry dialogue, decisions, summaries, and task routing — not deep execution memory.

### P4 — Fresh execution beats long-tail continuation
If a task is independent and bounded, start it in a fresh task-scoped run.

### P5 — Continuation is branch-local only
Only current-branch continuation may be ambient. Cross-topic residue and old tail must stay suppressed.

### P6 — Retrieval is on-demand, not ambient compensation
Retrieval should fill specific evidence gaps, not silently backfill a fat baseline prompt.

### P7 — Observability is mandatory
The system must be able to say why each context block was loaded, skipped, or suppressed.

---

## 4. Target surface model

### Layer 0 — Universal thin core
Always-on, extremely small.

Allowed contents:
- compact identity/tone;
- compact user-address preferences;
- compact safety/operating rules;
- compact thin-main rule;
- compact workspace root / execution invariants when needed.

Hard rule:
This layer must stay small enough that it never becomes the main context problem.

### Layer 1 — Surface contract
Exactly one surface contract per run/session.

Examples:
- `main`
- `strategist`
- `architect`
- `learning`
- `task_scoped_execution`

Each contract defines:
- purpose;
- startup budget;
- ambient allowlist;
- conditional allowlist;
- on-demand only classes;
- ambient forbidden classes;
- continuation policy;
- output contract.

### Layer 2 — Current-branch continuation capsule
Short, local, branch-specific only.

Contains only:
- current goal;
- current state;
- next action;
- blockers;
- essential refs.

### Layer 3 — Conditional packs
Loaded only if surface contract + request class allow them.

Examples:
- strategist current-control pack;
- architect current-state pack;
- business constraints summary;
- learning roadmap summary.

### Layer 4 — On-demand retrieval
Used for exact factual/evidence need.
Never ambient by default.

### Layer 5 — Archive/history
Searchable only.
Never ambient.

---

## 5. Surface contracts in CS2

## 5.1 `main`
Purpose:
- user interaction;
- orchestration;
- routing;
- concise summaries;
- decisions requiring Yuri.

Always-on:
- universal thin core;
- `main` surface contract;
- current local continuation only if truly active.

Forbidden ambiently:
- broad project context;
- old task tails;
- role packs;
- daily memory excerpts;
- topic history;
- archive/history.

Rule:
If work needs reading, synthesis, coding, or validation beyond a short step, `main` should spawn/hand off to a fresh run.

## 5.2 `strategist`
Purpose:
- business strategy;
- approvals;
- packaging/offer/content planning.

Always-on:
- universal thin core;
- strategist contract;
- compact strategist current-control pack.

Forbidden ambiently:
- full business history;
- old content plans;
- generic mixed memory;
- cross-role packs.

## 5.3 `architect`
Purpose:
- architecture/design reasoning;
- system shape decisions;
- implementation mapping.

Always-on:
- universal thin core;
- architect contract;
- compact current architecture state summary.

Forbidden ambiently:
- long design history;
- generic business packs;
- long transcript tails.

## 5.4 `learning`
Purpose:
- explanation;
- roadmap guidance;
- concept simplification.

Always-on:
- universal thin core;
- learning contract;
- compact learning mode rules.

Forbidden ambiently:
- deep business/architecture archives unless explicitly requested.

## 5.5 `task_scoped_execution`
Purpose:
- bounded independent work.

Always-on:
- universal thin core;
- task-scoped execution contract;
- task bootstrap packet.

Allowed:
- only task-linked artifacts needed for the next concrete step.

Forbidden ambiently:
- old main transcript;
- unrelated packs;
- broad role history.

---

## 6. Pack taxonomy in CS2

Every pack must declare one of these admission classes:

- `always_on`
- `conditional`
- `on_demand`
- `archive_only`
- `ambient_forbidden`

And every pack must declare:
- `pack_id`
- `owner_surface`
- `purpose`
- `max_startup_budget`
- `request_classes`
- `freshness_class`
- `continuation_scope`
- `durability_class`
- `admission_reason_codes`

Important rule:
If a pack has no explicit admission metadata, it may not be ambiently loaded.

---

## 7. Request classification and routing

Before loading non-core context, CS2 must decide:
1. which surface this request belongs to;
2. whether the request should stay in the current surface or spawn fresh;
3. which pack classes are admissible;
4. whether retrieval is needed.

### Minimum route decisions
- `main_keep`
- `main_spawn_task_scoped`
- `strategist_keep`
- `strategist_spawn_fresh`
- `architect_keep`
- `architect_spawn_fresh`
- `learning_keep`
- `learning_spawn_fresh`
- `factual_recall_inline`

### Strong bias
When in doubt between “continue in long chat” and “fresh bounded run”, prefer fresh bounded run.

---

## 8. Continuation policy

### Allowed ambient continuation
Only:
- current branch;
- current task;
- compact current-state capsule.

### Forbidden ambient continuation
- old closed branches;
- unrelated topic tails;
- broad strategic/architectural history;
- stale daily memory;
- transcript residue without explicit active need.

### Stay vs spawn rule
Spawn fresh when:
- work is independent;
- work is likely multi-step;
- large files/artifacts must be read;
- implementation/validation is needed;
- old chat tail would mostly be baggage.

---

## 9. Observability and debug envelope

For each context assembly, CS2 should emit a compact trace with:
- selected surface;
- request class;
- stay vs spawn decision;
- loaded core items;
- loaded packs;
- skipped packs;
- reason codes;
- retrieval calls used;
- estimated token budget by layer.

Reason code examples:
- `surface_always_on`
- `request_class_match`
- `task_linked_required`
- `conditional_load_match`
- `forbidden_ambient_class`
- `history_suppressed`
- `spawn_fresh_preferred`
- `budget_trimmed`

---

## 10. Success metrics

CS2 is successful if all are materially true:
- `main` startup context is measurably smaller than the current contour;
- new task-scoped runs do not inherit broad chat tail;
- packs are loaded only by explicit admission rules;
- role/topic history stops acting as ambient working memory;
- operator can inspect why context was loaded;
- user-visible behavior quality does not collapse.

---

## 11. Rollout plan

### Phase A — Spec and manifest freeze
Outputs:
- CS2 target spec;
- surface-contract schema;
- pack admission schema;
- first manifests for `main`, `strategist`, `architect`, `learning`, `task_scoped_execution`.

### Phase B — Runtime admission seam
Bind manifest loading and admission checks into the OpenClaw-owned runtime seam.

### Phase C — Fresh-run enforcement
Make task-scoped execution the default for bounded independent work.

### Phase D — Surface suppression and budget guards
Add ambient suppression, history suppression, and budget guardrails.

### Phase E — Validation pack
Run canonical scenarios:
- main thinness;
- strategist topical task;
- architecture task;
- factual recall;
- heavy one-off execution.

### Phase F — Reconciliation and cutover
Compare expected vs actual context shape and cut over only after evidence.

---

## 12. Proposed task cut

### Parent
Context System 2 — thin-main, pack admission, fresh-run default, and runtime observability

### Child task set
1. CS2-A1 — Freeze target spec and contracts
2. CS2-A2 — Define surface manifest schema
3. CS2-A3 — Define pack admission schema
4. CS2-B1 — Create first surface manifests
5. CS2-B2 — Create first compact packs/current-control summaries
6. CS2-C1 — Bind manifest loading to runtime assembly seam
7. CS2-C2 — Enforce stay-vs-spawn decision point
8. CS2-D1 — Add ambient suppression + budget guards
9. CS2-D2 — Add context assembly trace/debug envelope
10. CS2-E1 — Validation scenario pack
11. CS2-F1 — Reconciliation, operator report, and cutover recommendation

---

## 13. Immediate recommendation

Do not continue trying to rescue thinness through file rearrangement alone.
The next correct move is:
1. freeze CS2 contracts;
2. make packs first-class admission objects;
3. enforce fresh task-scoped execution by default;
4. add observability before claiming success.
