# Task 462 — Phased rollout and verification plan for memory runtime improvements

Date: 2026-05-13
Task: #462
Parent: #454
Depends on:
- `task-manager/artifacts/task-455-openclaw-memory-runtime-contour-improvement-spec-2026-05-13.md`
- `task-manager/artifacts/task-456-openclaw-memory-runtime-architecture-and-serving-contract-2026-05-13.md`
- `task-manager/artifacts/task-457-openclaw-memory-freshness-and-ingestion-policy-2026-05-13.md`
- `task-manager/artifacts/task-459-typed-memory-core-first-class-serving-plane-2026-05-13.md`
- `task-manager/artifacts/task-460-retrieval-orchestration-bounded-modules-refactor-plan-2026-05-13.md`
- `task-manager/artifacts/task-461-memory-runtime-observability-and-trace-debug-contour-2026-05-13.md`
Additional verified baseline:
- `docs/MEMORY_RUNTIME_AUDIT_LIVE_2026-05-13.md`
- `task-manager/artifacts/task-127-memory-rollout-operational-runbook-live-ingest-and-retrieval-2026-04-26.md`

---

## 1. Purpose

This artifact turns the approved memory-runtime direction into a **decision-grade rollout and verification sequence**.

It is specifically intended to answer:
- what order the changes should ship in;
- what must be true before each wave may proceed;
- what no-go conditions stop promotion;
- how current working retrieval is protected during the transition;
- what fallback points keep the rollout reversible;
- what bounded success metrics determine whether the rollout is helping;
- what a practical verification pack should contain for each gate.

This document distinguishes:
- **verified current-state facts** supported by predecessor artifacts and live audit evidence; and
- **normative rollout choices** adopted here to manage delivery risk.

Core stance:

> Roll out memory-runtime improvements as a **behavior-preserving, reversible, wave-based migration** that protects the current PostgreSQL lexical retrieval backbone while progressively introducing bounded modules, typed-serving authority, freshness enforcement, and decision traces.

---

## 2. Decision summary

### 2.1 Verified current-state facts

The following are treated as verified from the predecessor artifacts and live audit basis.

1. The live contour is **DB-first, lexical-first, and lane-aware** today.
2. PostgreSQL lexical retrieval over `documents` / `chunks` is the main working retrieval backbone.
3. Typed `mc_*` storage exists, but typed serving is currently sparse relative to the lexical corpus.
4. Approved enabled roots remain narrow and known:
   - `memory/`
   - `task-manager/artifacts/`
   - `task-manager/handoffs/`
5. Freshness is a real risk; no always-proven memory-specific refresh loop was established live.
6. Local fallback exists and is part of the current resilience contour.
7. Retrieval logic is currently concentrated enough that refactors carry real regression risk.
8. Observability exists only partially; a first-class decision-trace contract is not yet fully present.
9. The installed runtime/workspace seam is real enough that rollout must tolerate adapter boundaries rather than assuming one-file ownership.

### 2.2 Normative rollout choices

This plan locks the following rollout choices.

1. **Protection of the current lexical path is the primary rollout safety rail.**
2. **Behavior-preserving module extraction ships before major serving-authority changes.**
3. **Observability and freshness visibility must be available before broad typed-serving promotion.**
4. **Typed-serving promotion is lane-scoped and object-family-scoped, not global.**
5. **Every wave has a hard rollback point and explicit no-go criteria.**
6. **Promotion depends on verification packs with bounded fixtures, traces, and pass/fail criteria, not informal judgment.**
7. **The transition remains reversible until typed-serving proves stable across target lanes under mixed and stale-state conditions.**

### 2.3 Recommended implementation order

Ship in this order:
1. **Wave 0 — safety baseline and freeze rules**
2. **Wave 1 — observability and verification harness first**
3. **Wave 2 — bounded-module refactor with compatibility shim**
4. **Wave 3 — freshness enforcement and operator-visible stale-state control**
5. **Wave 4 — typed-serving advisory mode**
6. **Wave 5 — typed-serving primary for selected lanes**
7. **Wave 6 — broaden typed-serving coverage and retire transitional shims selectively**

This order is deliberate: it makes the system easier to inspect before making it more complex or authoritative.

---

## 3. Rollout principles

This section is normative.

### P1 — Preserve current retrieval usefulness throughout
At no point should the rollout require typed-memory completeness before useful recall continues to work.

### P2 — One dominant change axis per wave
Do not combine major module extraction, freshness-policy activation, and typed-authority promotion in the same gate.

### P3 — Every wave must be reversible within one deployment boundary
Each wave must identify:
- a feature flag or mode gate;
- a compatibility path;
- the exact demotion/revert action.

### P4 — Trace before trust
If a new authority path cannot explain itself through a bounded trace, it is not ready to outrank the old path.

### P5 — Stale state is a runtime failure mode, not only an ingestion concern
Rollout must test stale, failed-refresh, and fallback cases explicitly.

### P6 — Gate on lane outcomes, not only global averages
A rollout may succeed for one lane and be blocked for another.

### P7 — Protect source-registry and authority boundaries during migration
No wave may quietly widen source scope or loosen source-family exclusions just to improve apparent recall.

---

## 4. Transition protection for current working retrieval

This section defines how the current operational contour is protected during transition.

## 4.1 What is being protected

The protected baseline is:
- PostgreSQL lexical retrieval remains operational and callable;
- source-registry gating remains intact;
- lane-sensitive routing remains in force;
- DB-first plus local fallback semantics remain available;
- current callers continue to receive a compatible answer/context payload.

## 4.2 Mandatory transition protections

### T1 — Compatibility mode remains available through Wave 5
A lexical-first compatibility mode must remain callable even when typed-serving features are implemented.

### T2 — Shadow evaluation before authority promotion
Before a lane flips to typed-primary, run typed-serving in shadow/advisory mode and compare results against the lexical baseline.

### T3 — Existing payload contract cannot break without explicit adapter layer
Any new trace or serve-pack shape must be add-on or adapter-normalized until callers are migrated.

### T4 — Local fallback semantics remain intact until typed + lexical hybrid path proves resilient
No rollout wave may remove local fallback during this transition plan.

### T5 — Lane exclusions remain strict during refactor
Known hygiene protections, especially around handoffs/artifacts in architecture-like lanes, must remain explicit and regression-tested.

### T6 — Rollback path must prefer demotion over deletion
If a wave fails, revert by:
- disabling typed-primary decisions;
- disabling new planner/module path;
- muting freshness-enforcement verdicts to advisory;
- falling back to compatibility mode.

Do not require destructive schema or content rollback to restore service.

---

## 5. Wave plan

## 5.1 Wave 0 — Safety baseline and rollout guardrails

### Purpose
Freeze the comparison baseline and define the artifacts needed to judge every later wave.

### Main outcomes
- identify the canonical lexical-first baseline behavior to preserve;
- lock the initial lane set to evaluate;
- define feature flags/mode switches for later waves;
- define the minimum verification pack layout.

### Verified current-state facts this wave depends on
- current retrieval works materially today via PostgreSQL lexical search;
- local fallback exists;
- predecessor artifacts already identify the working backbone and major risks.

### Normative implementation choices
- choose a fixed initial lane set for promotion work:
  - `continuation_resume`
  - `current_task_execution`
  - `architecture_recall`
  - `policy_lookup`
  - `preference_recall`
- choose a fixed baseline backend comparison set:
  - `auto`
  - `psql`
  - `local`
- define feature gates such as:
  - `MEMORY_TRACE_LEVEL`
  - `MEMORY_REFACTOR_PLANNER_ENABLED`
  - `MEMORY_FRESHNESS_ENFORCEMENT_MODE=off|advisory|enforcing`
  - `MEMORY_TYPED_SERVING_MODE=off|shadow|advisory|primary`

### Gate to exit Wave 0
- baseline fixture set exists and is versioned;
- initial lane matrix is agreed;
- mode gates/flags are defined;
- rollback target is documented as lexical compatibility mode.

### No-go criteria
- no agreed baseline fixtures;
- inability to run current retrieval reproducibly in at least `psql` mode;
- unclear rollback switch.

### Fallback point
- do not begin structural code movement; remain on current production path.

---

## 5.2 Wave 1 — Observability and verification harness first

### Purpose
Make decisions inspectable before changing serving authority.

### Scope
Aligned primarily with task #461 and verification portions of #456/#457.

### Main outcomes
- introduce the bounded decision-trace envelope;
- expose plan/source-path/fallback/freshness/authority hints at at least summary level;
- create a repeatable verification harness that captures outputs and traces per fixture.

### Required deliverables
- trace envelope schema or stable shape;
- summary-level trace available for lexical-only runs;
- deep-trace mode for operator-targeted diagnosis;
- verification runner or pack process that records:
  - query/fixture metadata;
  - lane chosen;
  - backend used;
  - top refs;
  - freshness state;
  - fallback state;
  - pass/fail verdicts.

### Gate to exit Wave 1
- for baseline lexical runs, operators can see:
  - chosen lane;
  - source families included/excluded;
  - primary/fallback path;
  - whether fallback occurred;
  - top cited/supporting refs;
  - whether stale-state was known.
- the verification pack can compare current output to future-wave output.

### No-go criteria
- trace only exists for some backends but not the protected lexical path;
- trace materially changes normal answer payloads in a breaking way;
- verification harness cannot reproduce baseline answers/traces consistently enough to compare waves.

### Fallback point
- keep trace behind a flag and continue using baseline retrieval path without consuming trace operationally.

---

## 5.3 Wave 2 — Bounded-module refactor with compatibility shim

### Purpose
Extract the monolithic retrieval orchestration into bounded modules while preserving behavior.

### Scope
Aligned primarily with task #460, but must preserve the serving contract from #456.

### Main outcomes
- classification, policy, planning, fetch, ranking, assembly, and trace are split into bounded modules;
- a compatibility shim keeps old callers and old payload shape working;
- lexical retrieval semantics remain baseline-preserving.

### Required implementation sequence
1. extract declarative policy/constants;
2. extract classification;
3. extract planner/source routing;
4. extract fetch adapters;
5. extract ranking/authority pipeline;
6. extract serving-pack assembly;
7. keep the current top-level entrypoint as compatibility wrapper until later wave.

### Gate to exit Wave 2
- baseline fixture matrix shows no material regression on protected lanes;
- fallback-to-local still works when DB path fails;
- known lane hygiene filters still fire;
- trace stage breakdown matches the new module seams;
- compatibility wrapper preserves current consumer contract.

### No-go criteria
- regression on protected lanes that changes top result class/source family without an intentional, reviewed policy reason;
- inability to reproduce old behavior through compatibility path;
- routing exclusions or fallback rules become less explicit after refactor;
- module split only “moves code around” but loses traceability or adapter isolation.

### Fallback point
- disable new planner/module path and route calls through the preserved compatibility entrypoint.

---

## 5.4 Wave 3 — Freshness enforcement and operator-visible stale-state control

### Purpose
Turn freshness from hidden risk into a bounded serving input.

### Scope
Aligned primarily with task #457 and trace expectations from #461.

### Main outcomes
- root freshness states become explicit (`fresh`, `aging`, `stale`, `failed_refresh`, `unknown`);
- ingest cadence/trigger expectations become visible;
- runtime can demote or warn on stale evidence by lane;
- typed objects inherit stale-state correctly from evidence when required.

### Required deliverables
- root freshness calculator or equivalent policy surface;
- serving-plan hook that imports lane-specific freshness policy;
- trace fields for consulted roots and their freshness state;
- operator summary for stale/failing roots;
- verification fixtures for stale, aging, and failed-refresh conditions.

### Gate to exit Wave 3
- stale-state is visible in trace and operator summaries;
- architecture/current-task/continuation lanes change behavior in stale scenarios according to policy rather than silently;
- lexical compatibility mode still serves when roots are stale, but with bounded demotion/warning behavior;
- no source root is treated as silently fresh when evidence shows known un-ingested change beyond grace.

### No-go criteria
- freshness logic blocks normal retrieval too aggressively without advisory soak period;
- stale-state exists in ingest reporting but not in serve-time traces;
- continuation or current-task lanes still present stale data as if current with no trace evidence;
- stale heuristics create cross-lane regressions without clear policy basis.

### Fallback point
- demote `MEMORY_FRESHNESS_ENFORCEMENT_MODE` from `enforcing` to `advisory`.

---

## 5.5 Wave 4 — Typed-serving advisory mode

### Purpose
Introduce typed-serving evaluation without letting it outrank the lexical baseline yet.

### Scope
Aligned primarily with task #459, using the architecture contract from #456 and the refactor seams from #460.

### Main outcomes
- typed fetch path is callable through the new planner;
- `mc_memory_notes`, `mc_session_capsules`, and supporting evidence records participate in shadow or advisory evaluation;
- traces show when typed candidates were eligible, empty, stale, superseded, or advisory-only.

### Required deliverables
- typed candidate fetch interface;
- eligibility checks for scope, supersession, freshness, provenance completeness, and lane fit;
- side-by-side lexical vs typed decision capture in verification runs;
- advisory verdicts that never silently replace lexical winners in this wave.

### Gate to exit Wave 4
- for target lanes, shadow runs show typed candidates that are often relevant enough to justify promotion work;
- typed traces explain non-use cases clearly (`empty`, `ineligible`, `stale`, `policy-disabled`, `superseded`);
- advisory mode does not degrade lexical answer quality or payload compatibility.

### No-go criteria
- typed-serving cannot explain why it won or lost against lexical baseline;
- provenance or freshness fields are missing for many typed candidates;
- advisory mode reveals that typed coverage is too sparse or too noisy for target lanes;
- shadow results show frequent contradiction with fresher lexical evidence.

### Fallback point
- set `MEMORY_TYPED_SERVING_MODE=off` or keep it at `shadow` only.

---

## 5.6 Wave 5 — Typed-serving primary for selected lanes

### Purpose
Promote typed-serving from advisory to primary for a bounded lane subset.

### Eligible first-promotion lanes
Recommended order:
1. `continuation_resume` via `mc_session_capsules`
2. `current_task_execution` via `mc_session_capsules` + `mc_memory_notes`
3. `preference_recall` via `mc_memory_notes`

Defer `architecture_recall` until typed evidence and hygiene protections are proven stronger.

### Promotion rule
Typed-serving may be primary only when candidates are:
- lane-eligible;
- not superseded;
- freshness-eligible for the lane;
- supported by evidence refs;
- traceable through the decision envelope.

Lexical retrieval remains mandatory as support, verification, or replacement path.

### Gate to exit Wave 5
- promoted lanes show stable or improved outcome quality in verification pack review;
- stale/superseded typed objects are correctly demoted;
- lexical replacement path activates when typed path is empty or ineligible;
- operators can explain lane decisions using trace without reverse-engineering hidden heuristics.

### No-go criteria
- typed-primary produces untraceable authoritative answers;
- promoted lanes regress in recency, contradiction handling, or fallback behavior;
- lexical support path becomes optional in practice rather than mandatory;
- installed-runtime bridge cannot safely consume the new serve-pack path.

### Fallback point
- demote `MEMORY_TYPED_SERVING_MODE` from `primary` to `advisory` per lane or globally.

---

## 5.7 Wave 6 — Broaden typed-serving coverage and selectively retire shims

### Purpose
Expand typed-primary usage where proven, while removing transitional complexity only after evidence supports it.

### Candidate scope
- broader `mc_memory_notes` usage for policy/architecture lanes;
- `mc_retrieval_documents` and relation-driven expansion where helpful;
- selective retirement of compatibility wrapper internals once equivalent traces and outputs are proven.

### Gate to exit Wave 6
- lane-by-lane evidence shows typed-primary is stable beyond initial promotion lanes;
- verification packs cover mixed typed/lexical, stale, contradiction, and fallback scenarios;
- compatibility shims removed only where consumers are confirmed migrated;
- operational dashboards/summaries show acceptable freshness and failure behavior over time.

### No-go criteria
- pressure to remove lexical path before typed coverage/provenance/freshness is sufficient;
- pressure to retire shims without consumer migration proof;
- architecture lane still shows contamination or authority leakage from known seams.

### Fallback point
- keep selective hybrid mode permanently longer; retire shims only lane-by-lane.

---

## 6. Gates, no-go criteria, and rollback matrix

| Area | Gate to promote | No-go condition | Rollback action |
|---|---|---|---|
| Trace/observability | baseline lexical path emits bounded trace | trace missing for protected path or breaks payload contract | disable deep/summary trace consumption; keep flag off |
| Refactor modules | fixture parity on protected lanes; fallback intact | changed winners or exclusions without approved reason | route through compatibility entrypoint |
| Freshness policy | stale state visible and lane-sensitive behavior works | stale data still serves silently or enforcement is overly disruptive | switch freshness from enforcing to advisory |
| Typed advisory | typed shadow results are explainable and non-disruptive | typed candidates lack provenance/freshness or contradict fresher evidence | disable typed path or remain shadow only |
| Typed primary | promoted lanes remain stable with lexical support intact | recency/authority/fallback regressions in promoted lanes | demote typed-primary to advisory |
| Shim retirement | consumer migration and output equivalence proven | old callers still depend on old contract | retain shim; defer removal |

---

## 7. Bounded success metrics

These are normative success metrics for rollout review. They are intentionally bounded and should be evaluated per wave and per lane rather than as one global score.

## 7.1 Outcome-quality metrics

### M1 — Protected-lane winner stability
For protected lexical-baseline lanes during Waves 1-3, the top result class/source-family should remain unchanged except where an intentional reviewed policy fix is expected.

### M2 — Promotion-lane usefulness
For lanes promoted in Waves 5-6, typed-primary outcomes should be judged at least as useful as lexical baseline on the agreed fixture pack.

### M3 — Contradiction visibility
When typed and lexical paths disagree materially, the trace should expose disagreement rather than silently flatten it.

## 7.2 Safety and continuity metrics

### M4 — Fallback continuity
When DB retrieval is degraded or unavailable, local fallback or lexical replacement behavior should still produce a bounded answer and visible trace status.

### M5 — Freshness visibility coverage
For every response in the target verification pack, consulted roots should have a visible freshness state or an explicit `unknown`/not-attached reason.

### M6 — Rollback readiness
Every wave must demonstrate that its primary feature gate can be disabled without schema rollback or consumer breakage.

## 7.3 Operability metrics

### M7 — Trace explainability
For every failed or surprising fixture, an operator should be able to identify the decisive stage:
- classification
- source selection
- typed fetch
- lexical fetch
- ranking/authority
- freshness
- fallback
- final shaping

### M8 — Verification reproducibility
The same verification pack should be rerunnable with comparable structured outputs across at least current baseline and current candidate build.

### M9 — Freshness policy conformance
Roots exceeding hard max lag in verification scenarios must surface as `stale` or `failed_refresh`; they must not appear implicitly fresh.

---

## 8. Verification pack shape

This section is normative.

## 8.1 Verification pack goals

A rollout verification pack should be small enough to run often, but broad enough to catch the known failure modes.

It should validate:
- lane choice;
- source routing;
- authority choice;
- freshness behavior;
- fallback behavior;
- typed eligibility and supersession handling;
- output compatibility;
- trace completeness.

## 8.2 Pack structure

Recommended structure per verification run:

```text
verification-pack/
  manifest.json
  fixtures/
    <fixture-id>.json
  outputs/
    baseline/<fixture-id>.json
    candidate/<fixture-id>.json
  traces/
    baseline/<fixture-id>.trace.json
    candidate/<fixture-id>.trace.json
  diffs/
    <fixture-id>.diff.md
  summary.json
  verdict.md
```

## 8.3 Minimum fixture classes

### F1 — Continuation freshness fixtures
Examples:
- explicit resume with fresh handoff;
- explicit resume with stale handoff;
- ambiguous continue-after request;
- reopen predecessor chain.

### F2 — Current-task execution fixtures
Examples:
- task-specific continuation with current artifact evidence;
- current task with stale artifact root;
- current task where typed capsule is absent and lexical path must replace it.

### F3 — Architecture/policy hygiene fixtures
Examples:
- architecture recall that must exclude handoff-like contamination;
- policy lookup with artifact-backed answer;
- architecture query where typed note exists but fresher lexical evidence disagrees.

### F4 — Preference recall fixtures
Examples:
- durable preference backed by `memory/`;
- stale preference evidence requiring warning/demotion;
- superseded note vs newer note.

### F5 — Fallback fixtures
Examples:
- forced DB failure -> local fallback;
- typed path empty -> lexical replacement;
- lexical path stale -> advisory stale answer with trace.

### F6 — Trace-only fixtures
Examples:
- low-confidence classification;
- excluded source-family proof;
- shadow typed candidate visible but not promoted.

## 8.4 Minimum per-fixture assertions

Each fixture should assert at least:
- expected lane or accepted-lane set;
- expected primary path (`lexical`, `typed`, `fallback`, `hybrid`);
- expected consulted/excluded source families;
- expected freshness state constraints;
- expected top reference class or reference family;
- whether fallback is expected;
- whether typed should be `unused`, `advisory`, or `primary`;
- whether output contract compatibility is required;
- whether contradiction/open-question trace content is required.

## 8.5 Summary verdict shape

A run summary should include at least:
- build/runtime identifier;
- policy version;
- trace version;
- fixture counts by lane;
- pass/fail counts;
- regressions by type;
- no-go triggers hit;
- release verdict:
  - `go`
  - `go_with_holdbacks`
  - `no_go`

---

## 9. Practical execution sequence

This section is the recommended implementation sequence across teams/files, not just abstract waves.

1. **Freeze baseline fixtures and capture current outputs/traces where possible.**
2. **Add trace envelope and verification runner around the existing lexical path first.**
3. **Extract policy/classification/planning/fetch/ranking/assembly into bounded modules behind compatibility wrapper.**
4. **Re-run full baseline pack and resolve behavior drift before proceeding.**
5. **Implement freshness-state computation and advisory serve-time visibility.**
6. **Promote freshness from advisory to enforcing only after stale fixtures pass.**
7. **Add typed fetch/eligibility path in shadow mode.**
8. **Run shadow comparison pack across target lanes and collect promotion evidence.**
9. **Enable typed-primary for the smallest justified lane subset.**
10. **Review results, expand lane coverage selectively, and defer risky lane promotions.**
11. **Retire compatibility internals only after consumer migration and equivalence proof.**

This sequence is intentionally conservative. It avoids a failure mode where typed-serving is promoted before the team can explain or compare it.

---

## 10. Recommended first promotion and first holdback decisions

## 10.1 Recommended early promotion candidates

### Promote earliest
- `continuation_resume`
  - because typed `mc_session_capsules` have clear bounded value;
  - because recency/freshness can be tested directly;
  - because lexical support remains available when capsule coverage is thin.

- `current_task_execution`
  - after continuation lane stabilizes;
  - because typed bounded-state serving is valuable here.

### Promote later
- `preference_recall`
  - once note freshness/supersession is proven.

## 10.2 Recommended holdbacks

### Hold back until later
- `architecture_recall`
  - due to known contamination and authority-leak risks;
  - because architecture answers are sensitive to source-family hygiene and stale artifacts.

- broad policy/decision recall from typed notes
  - until evidence coverage, contradiction handling, and supersession are clearly trustworthy.

---

## 11. Explicit no-go scenarios for the whole rollout

The rollout should be halted or rolled back if any of the following occur.

1. **Current lexical retrieval usefulness materially drops on protected lanes before typed-primary is proven.**
2. **The team cannot explain changed answers through the trace/verification pack.**
3. **Freshness enforcement causes answers to disappear or degrade broadly without controlled advisory soak.**
4. **Typed-primary answers appear with missing provenance, missing freshness, or silent contradiction against fresher evidence.**
5. **Consumer-facing payload compatibility breaks without an adapter path.**
6. **The rollout implicitly broadens source scope or weakens authority boundaries to compensate for coverage gaps.**
7. **The installed-runtime seam produces uninspectable behavior changes that cannot be bounded through the adapter and verification pack.**

---

## 12. Exit condition for task-level review

This artifact should be considered successful if reviewers agree that it provides:
- a credible wave order;
- explicit gates and no-go criteria;
- defined rollback/fallback points;
- bounded success metrics;
- a verification-pack structure;
- explicit protection of current working retrieval;
- a practical execution sequence aligned with tasks #455/#456/#457/#459/#460/#461.

On that basis, task #462 is reviewable as a planning artifact even though implementation work remains downstream.

---

## 13. Final recommendation

Adopt the rollout order in this document.

Specifically:
1. make trace and verification first-class first;
2. refactor into bounded modules second;
3. activate freshness semantics third;
4. run typed-serving in shadow/advisory mode before any lane promotion;
5. promote typed-primary only for the smallest, best-bounded lanes first;
6. keep lexical retrieval as the protected safety rail throughout the transition.

That is the lowest-risk path that remains aligned with the approved predecessor artifacts while still moving decisively toward the target memory-runtime contour.
