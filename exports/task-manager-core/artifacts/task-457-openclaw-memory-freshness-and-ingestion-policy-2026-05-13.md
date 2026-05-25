# Task 457 — OpenClaw memory freshness and ingestion policy

Date: 2026-05-13
Task: #457
Parent: #454
Depends on:
- `task-manager/artifacts/task-455-openclaw-memory-runtime-contour-improvement-spec-2026-05-13.md`
- `task-manager/artifacts/task-456-openclaw-memory-runtime-architecture-and-serving-contract-2026-05-13.md`
Primary evidence basis:
- `docs/MEMORY_RUNTIME_AUDIT_LIVE_2026-05-13.md`
- `task-manager/artifacts/task-440-authoritative-sources-inventory-2026-05-13.md`
- `task-manager/artifacts/task-127-memory-rollout-operational-runbook-live-ingest-and-retrieval-2026-04-26.md`

---

## 1. Purpose

This artifact defines the **freshness, ingestion, retry, and operator-visibility policy** for the live OpenClaw memory contour.

It is intended to be **decision-grade** rather than merely aspirational. It therefore distinguishes:
- what is **verified in the live contour today**;
- what this document **chooses normatively** for rollout;
- what can be adopted immediately versus in later hardening waves.

Core stance:

> OpenClaw memory should remain a DB-first hybrid system, but freshness must become explicit, bounded, observable, and lane-safe. The lexical corpus may remain the evidence backbone, yet it cannot be treated as trustworthy unless each approved source root has a declared freshness expectation, refresh trigger set, bounded retry policy, and visible stale-state behavior.

---

## 2. Decision summary

### 2.1 Verified live baseline

The following are treated as verified facts from the live audit and predecessor artifacts:

1. PostgreSQL `pkm_memory` is the live structured backing store.
2. The active retrieval path is primarily lexical over `documents` and `chunks`.
3. Enabled source roots are currently:
   - `memory/`
   - `task-manager/artifacts/`
   - `task-manager/handoffs/`
4. Ingestion is run through `pkm-memory/ingest_sources.py` using the source registry.
5. Local-file fallback exists when DB retrieval fails.
6. Freshness is **not guaranteed today**.
7. No memory-specific always-on refresh loop was proven live.
8. Latest proven ingestion in the audit lagged audit time by multiple days.

### 2.2 Normative policy decisions

This document locks the following decisions:

1. **Freshness is a serving input, not just an ingest concern.** Retrieval/runtime should reason about stale vs fresh indexed evidence.
2. **Each approved source root gets its own SLO tier.** One global cadence is not sufficient.
3. **Change-triggered ingest is preferred; scheduled backstop ingest is mandatory.**
4. **Retries must be bounded and source-run scoped.** No unbounded loops, no silent forever-fail mode.
5. **Cron/background behavior is allowed, but must remain conservative and inspectable.**
6. **Staleness must be operator-visible and retriever-visible.**
7. **Typed Memory Core refresh remains downstream of lexical/source freshness.** Typed objects cannot out-authorize stale or missing evidence without explicit trace state.

### 2.3 Operational outcome sought

After rollout, operators should be able to answer all of the following quickly:
- When was each approved source root last successfully ingested?
- What changed since the last ingest?
- Which roots are within freshness SLO and which are stale?
- Which runs failed, how many times, and what happens next?
- Did the scheduler miss a run, or did the ingest fail after starting?
- Is a memory answer relying on data that is stale by policy for its lane?

---

## 3. Scope

### In scope
- freshness expectations per approved root;
- trigger model for ingest;
- scheduled cadence options;
- bounded retry and failure handling;
- stale-data detection and serving consequences;
- cron/background expectations;
- operator visibility and rollout guidance;
- ownership boundaries.

### Out of scope
- full typed-object writer implementation;
- new source families beyond the currently approved enabled roots;
- vector/embedding refresh policy;
- unrelated OpenClaw infrastructure maintenance.

---

## 4. Authority and evidence model for freshness policy

This section is normative.

### 4.1 Truth-source order for freshness decisions

When there is disagreement, freshness decisions should resolve in this order:

1. **runtime-observed source state**
   - actual file mtimes / hashes / source availability
   - live DB `ingestion_runs` state
2. **checked-in source registry and ingest code**
   - enabled roots
   - root ownership metadata
   - ingestion tooling behavior
3. **runbooks / implementation docs / specs**
4. **planning notes or assumptions**

### 4.2 Freshness object of concern

Freshness is not only “how old the DB row is.” The policy evaluates freshness at four levels:

1. **source-root freshness** — whether a root has been scanned and reconciled recently enough;
2. **document-index freshness** — whether changed files from that root are represented in `documents/chunks`;
3. **typed-object freshness** — whether typed Memory Core objects derived from evidence are still valid relative to their evidence refs;
4. **serving freshness** — whether the runtime is permitted to serve results for a lane without stale warning/escalation.

### 4.3 Policy principle

A newer file with older DB state means the root is stale, even if retrieval still returns something plausible.

---

## 5. Verified facts vs design choices

## 5.1 Verified facts

### F1 — Enabled roots are narrow and known
Verified enabled roots are:
- `memory/`
- `task-manager/artifacts/`
- `task-manager/handoffs/`

### F2 — The ingest entrypoint already exists
`pkm-memory/ingest_sources.py` is the verified operational path.

### F3 — State and run tracking already exist in some form
The contour includes:
- PostgreSQL `ingestion_runs`
- local state file `pkm-memory/state/ingestion_state.json`

### F4 — A general cron substrate exists
Cron is running in the live environment, but a dedicated memory-refresh loop was not proven.

### F5 — Retrieval can degrade into local fallback
This helps resilience, but local fallback does not substitute for freshness accounting.

## 5.2 Deliberate design choices

### D1 — Root-specific SLOs
Different roots carry different change rates and lane consequences.

### D2 — Two-layer refresh model
Use:
- **event/change-triggered refresh** for fast convergence;
- **scheduled backstop refresh** for correctness and missed-event recovery.

### D3 — Freshness states are explicit
Every root and typed derivative should be classifiable as one of:
- `fresh`
- `aging`
- `stale`
- `failed_refresh`
- `unknown`

### D4 — Stale state changes serving behavior
Staleness is not only a dashboard concern. It can demote authority, add warnings, or trigger fallback behavior depending on lane.

### D5 — Retry is bounded by policy tier
No infinite retries. After the retry budget is exhausted, the root becomes operator-visible stale/failing until the next scheduled attempt or manual intervention.

---

## 6. Source-root freshness tiers and SLOs

This section defines the normative freshness targets for the currently approved enabled roots.

## 6.1 Freshness-state definitions

For each root, compute these timestamps:
- `last_successful_ingest_at`
- `last_attempted_ingest_at`
- `last_detected_source_change_at`
- `oldest_uningested_change_at` if known

A root is:
- **fresh**: within target SLO and no known pending source change older than trigger grace;
- **aging**: beyond preferred target but within hard maximum lag;
- **stale**: beyond hard maximum lag or known pending change exceeds grace;
- **failed_refresh**: most recent refresh attempts exhausted retry budget;
- **unknown**: no trustworthy state available.

## 6.2 Source-root policy table

| Root | Primary runtime role | Expected change pattern | Target freshness SLO | Hard max lag | Trigger grace after detected change | Serving sensitivity | Owner |
|---|---|---:|---:|---:|---:|---|---|
| `memory/` | durable shared memory / preference / notes | moderate, bursty | 30 min | 6 h | 10 min | medium-high | memory/runtime owner |
| `task-manager/artifacts/` | design, architecture, audit, decision artifacts | high during active work | 15 min | 4 h | 5 min | high | task-manager + memory/runtime owner |
| `task-manager/handoffs/` | continuation / resume / session transfer | very high consequence for continuation | 5 min | 1 h | 2 min | very high | task-manager/handoff owner + memory/runtime owner |

## 6.3 Why these tiers differ

### `task-manager/handoffs/`
This root most directly affects continuation and resume quality. Missing the most recent handoff can create immediate user-facing errors. It gets the tightest target.

### `task-manager/artifacts/`
Artifacts matter heavily for architecture, policy, and decision recall. They are slightly less time-critical than active handoffs but still require relatively fast convergence.

### `memory/`
This root is authoritative and durable, but its typical failure mode is slower drift rather than acute continuation breakage. It still requires a reasonable freshness envelope because preferences and operating constraints may change.

---

## 7. Lane-aware serving consequences of stale data

This section binds freshness policy to the runtime architecture from task #456.

## 7.1 Lane sensitivity

The serving planner and freshness evaluator should treat stale roots differently by lane.

| Lane | Stale root sensitivity | Required behavior |
|---|---|---|
| `continuation_resume` | highest | prefer freshest `task-manager/handoffs/`; if stale, emit stale warning/trace and widen evidence carefully; do not silently present stale continuation as current |
| `current_task_execution` | high | prefer fresh artifacts/handoffs; if stale, surface that current task state may lag |
| `architecture_recall` | high | stale artifacts should demote confidence and force trace visibility |
| `policy_lookup` | medium-high | stale memory/artifact roots require authority caution |
| `preference_recall` | medium | stale `memory/` results can serve with warning if no fresher contradiction exists |
| `meta_evaluation` / `general_lookup` | medium | stale state should appear in trace and confidence shaping |

## 7.2 Authority effects

Stale state should change authority semantics as follows:

1. `fresh` or `aging` lexical evidence may serve normally within lane policy.
2. `stale` evidence may still be used as fallback evidence, but must not be silently presented as up-to-date canonical state when the lane expects recency.
3. `failed_refresh` evidence should be explicitly tagged in trace output.
4. Typed objects derived from stale evidence should be marked `freshness_inherited=stale` unless revalidated.

## 7.3 Minimum serving trace additions

Every memory-serving trace should eventually expose at least:
- source roots consulted;
- freshness state per consulted root;
- latest successful ingest time per consulted root;
- whether a newer source change is known but not yet ingested;
- whether stale state altered ranking/authority/answer wording.

---

## 8. Refresh triggers

This section specifies when ingestion should run.

## 8.1 Trigger classes

Use four trigger classes:

### T1 — source-change trigger
Triggered when a file under an enabled root is created, modified, renamed, or deleted.

Policy:
- preferred trigger for convergence;
- should enqueue a scoped refresh for the affected root;
- may be debounced briefly to avoid one-run-per-file burst.

### T2 — periodic backstop trigger
Runs on a schedule even if no file watcher/event path fired.

Policy:
- mandatory;
- protects against missed events, watcher drift, process restarts, and state corruption.

### T3 — operator/manual trigger
Triggered explicitly by operator or maintenance command.

Policy:
- should bypass normal debounce;
- should still obey single-run concurrency rules;
- may request one root or all enabled roots.

### T4 — demand-side safety trigger
Triggered by retrieval/runtime when a request hits a root that is beyond hard max lag or marked `failed_refresh`, subject to rate limits.

Policy:
- should not block the user turn waiting for full ingest unless explicitly designed to do so later;
- should enqueue or request a background refresh;
- must be rate-limited to prevent thrash.

## 8.2 Trigger precedence

When multiple triggers coincide:
1. active source-change trigger
2. operator/manual trigger
3. demand-side safety trigger
4. periodic backstop trigger

This is a scheduling priority, not an authority ranking.

## 8.3 Debounce rules

Because active work can create many artifacts quickly, apply root-level debounce windows:
- `task-manager/handoffs/`: 30–60 seconds
- `task-manager/artifacts/`: 2–5 minutes
- `memory/`: 5–10 minutes

Debounce collapses bursts into a single root refresh attempt.

---

## 9. Ingest cadence options and chosen default

## 9.1 Supported cadence models

### Option A — scheduled-only
- cron runs full ingest every N minutes/hours
- simplest
- weakest convergence

### Option B — event-driven only
- file changes trigger refresh
- best convergence when healthy
- weakest resilience to watcher gaps / restart drift

### Option C — hybrid event-driven + scheduled backstop
- change-triggered for responsiveness
- scheduled backstop for correctness
- best fit for the verified live contour

## 9.2 Chosen default

**Adopt Option C.**

Reasoning:
- it fits the existing cron-capable contour;
- it does not require trusting watchers alone;
- it limits stale windows during active work;
- it remains consistent with DB-first and bounded-operability goals.

## 9.3 Default schedule recommendations

These are rollout defaults, not immutable constants.

### Backstop full-root sweep
- every 30 minutes: sweep all enabled roots for drift and missed changes

### Root-specific minimum schedule if watcher path is absent
- `task-manager/handoffs/`: every 5 minutes
- `task-manager/artifacts/`: every 15 minutes
- `memory/`: every 30 minutes

### Daily reconciliation sweep
- once every 24 hours: full consistency sweep that ignores incremental assumptions and rechecks all enabled roots

The daily sweep is a correctness backstop and can run during lower-traffic periods.

---

## 10. Concurrency and run model

## 10.1 Single-writer expectation

Per root, only one ingest run should be active at a time.

## 10.2 Overlap handling

If a trigger fires while the same root is already being ingested:
- record the trigger;
- mark the root as `pending_followup`;
- run one additional follow-up pass after the current run if changes may have arrived mid-run.

## 10.3 Full-sweep vs root-scoped runs

Prefer **root-scoped runs** for trigger-driven refreshes and **full-sweep runs** for scheduled backstop/reconciliation.

Reason:
- root-scoped runs reduce work during bursts;
- full sweeps provide broad correctness guarantees.

---

## 11. Bounded retry and failure handling

This section is normative.

## 11.1 Failure classes

Classify failures into:

1. **transient infrastructure**
   - DB temporarily unavailable
   - file lock / temporary IO error
   - short-lived environment issue
2. **source-content failures**
   - malformed input that the ingester cannot process
   - encoding/path issues on one file or subtree
3. **configuration/policy failures**
   - invalid registry entry
   - missing env/config required for ingest
4. **internal ingest bug**
   - unhandled exception / invariant breach

## 11.2 Retry budgets

### For transient infrastructure failures
- immediate retries: up to 2
- backoff: 1 min, then 5 min
- if still failing: mark `failed_refresh`
- next scheduled trigger may retry again

### For source-content failures scoped to one file
- continue ingest for other eligible files when safe
- mark the file and root with partial-failure metadata
- no more than 1 immediate retry for the same file in the same run
- escalate for operator visibility if unchanged failure repeats across 3 runs

### For configuration/policy failures
- do not loop immediate retries
- mark `failed_refresh`
- require operator intervention or config change

### For internal ingest bugs
- at most 1 immediate retry for non-deterministic suspicion
- otherwise fail fast and surface operator-visible alert/state

## 11.3 Partial success policy

If a root run ingests most files but a bounded subset fails:
- record the run as `partial_success` rather than clean success;
- freshness may remain `aging` rather than `fresh` if the failed subset is recent or high-authority;
- serving trace should know that the root is not fully reconciled.

## 11.4 Failure saturation rule

If the same root enters `failed_refresh` for more than 24 hours or misses 3 consecutive hard max windows, operator attention becomes mandatory. The system should not quietly normalize chronic staleness.

---

## 12. Stale-data detection

## 12.1 Detection signals

A root should be considered stale if any of the following hold:

1. `now - last_successful_ingest_at > hard_max_lag`
2. a known changed file is older than `trigger_grace` and not yet represented in ingest state
3. latest run status is `failed_refresh` and no newer successful run exists
4. local state and DB run state materially disagree and reconciliation is not complete
5. no trustworthy freshness metadata exists

## 12.2 Derivative typed-object stale detection

A typed object becomes freshness-suspect when:
- any evidence ref points to a root in `stale` or `failed_refresh` state;
- the source document version/hash differs from what the typed object last referenced;
- the root was reingested after the typed object’s last validation time.

## 12.3 Unknown-state policy

If the system cannot establish freshness state, treat it as `unknown`, not implicitly fresh.

Serving implication:
- `unknown` should behave at least as cautiously as `stale` for high-sensitivity lanes.

---

## 13. Operator visibility and observability

This section defines the minimum visibility surface required by the policy.

## 13.1 Minimum operator questions the system must answer

Operators should be able to inspect:
- enabled roots;
- last attempted and last successful ingest per root;
- current freshness state per root;
- current retry/failure state per root;
- partial-failure file list or count;
- whether a periodic sweep is overdue;
- whether retrieval has recently served from stale roots.

## 13.2 Recommended visibility surfaces

At minimum, expose one or more of:
- a CLI/status command or script;
- a machine-readable status file/JSON surface;
- DB query/report over `ingestion_runs` and root freshness summary;
- optional operator-facing summary artifact/log.

## 13.3 Recommended root summary schema

A root summary surface should include fields equivalent to:

```yaml
root_id: task-manager/handoffs
enabled: true
freshness_state: fresh | aging | stale | failed_refresh | unknown
last_attempted_ingest_at: <timestamp>
last_successful_ingest_at: <timestamp>
last_detected_source_change_at: <timestamp|null>
oldest_uningested_change_at: <timestamp|null>
run_mode: trigger | scheduled_backstop | manual | demand_side
retry_state:
  consecutive_failures: <int>
  last_failure_class: <optional string>
pending_followup: <bool>
partial_failure_count: <int>
slo:
  target: 5m
  hard_max_lag: 1h
owner:
  primary: <owner label>
```

## 13.4 Retrieval trace visibility

Serving traces should include enough freshness state to explain degraded authority or warnings without requiring operators to reverse-engineer ingest logs.

---

## 14. Ownership model

This section assigns responsibility without overclaiming unknown team structure.

## 14.1 Ownership layers

### O1 — source owner
The subsystem or operator closest to the root’s content semantics.

### O2 — memory runtime owner
The owner of ingest scheduling, DB persistence, freshness evaluation, and serving visibility.

### O3 — operator/on-call owner
The person or process expected to react when chronic stale/failure states appear.

## 14.2 Root-specific ownership expectation

| Root | Source owner | Memory runtime owner | Notes |
|---|---|---|---|
| `memory/` | shared-memory / operator-maintained surface | memory runtime owner | durable preference/knowledge root |
| `task-manager/artifacts/` | task-manager / architecture workstream | memory runtime owner | high-value decision and design artifacts |
| `task-manager/handoffs/` | task-manager / handoff-producing runtime | memory runtime owner | continuity-critical |

## 14.3 Ownership rule

Source owners are responsible for content correctness; memory runtime owners are responsible for ingest freshness, stale detection, and visibility. These responsibilities must not be conflated.

---

## 15. Cron/background behavior policy

## 15.1 Acceptable runtime posture

The verified contour supports cron/background jobs. The policy allows that mechanism but constrains it:

1. jobs must be bounded, not daemonized without observability;
2. each run must produce inspectable state/log outcome;
3. repeated failures must not self-loop rapidly;
4. scheduled jobs must coexist with manual/operator triggers safely.

## 15.2 Minimum scheduled behavior

A compliant rollout should provide at least:
- periodic backstop refresh of enabled roots;
- daily reconciliation sweep;
- bounded retry behavior on transient failures;
- visible missed-run detection.

## 15.3 Missed-run detection

If the scheduler itself fails to fire within 2x the configured interval for a root backstop, the root should move to `aging` or `stale` based on the hard max lag, and the operator surface should show `scheduler_gap=true` or equivalent.

## 15.4 Background demand-trigger guardrail

Demand-side refresh requests caused by retrieval must be coalesced and rate-limited. User traffic must not be able to create an ingest storm.

Recommended guardrail:
- no more than one demand-side enqueue per root per 10 minutes while already stale.

---

## 16. Rollout guidance

This rollout is phased so the policy can be adopted without pretending the entire future system already exists.

## 16.1 Phase 0 — policy adoption and visibility baseline

Required outcomes:
- this policy is accepted as the operating contract;
- current enabled roots are mapped to SLO tiers;
- operators can inspect last successful ingest timestamps and recent failures.

## 16.2 Phase 1 — backstop scheduling hardening

Required outcomes:
- install/verify periodic scheduled ingest for enabled roots;
- record run results in a consistent status surface;
- enforce bounded retry budgets.

## 16.3 Phase 2 — stale-aware serving trace

Required outcomes:
- retrieval trace exposes root freshness states;
- stale roots alter confidence/authority output for sensitive lanes.

## 16.4 Phase 3 — trigger-driven convergence

Required outcomes:
- root-scoped change-triggered ingest or equivalent enqueue path;
- debounce and overlap controls;
- demand-side safety trigger guarded by rate limiting.

## 16.5 Phase 4 — typed freshness inheritance

Required outcomes:
- typed Memory Core objects inherit or recompute freshness state from evidence refs;
- stale evidence can suppress or demote stale typed objects for sensitive lanes.

---

## 17. Acceptance checks

These checks are bounded and intended for rollout gating, not exhaustive proof.

## 17.1 Policy completeness checks

1. **Root SLO coverage**
   - Given the current enabled roots,
   - when this policy is reviewed,
   - then each root has target freshness, hard max lag, trigger grace, serving sensitivity, and ownership.

2. **Trigger coverage**
   - Given the need for both responsiveness and correctness,
   - when the trigger model is inspected,
   - then source-change, periodic backstop, manual, and demand-side triggers are all defined.

3. **Failure coverage**
   - Given ingest can fail in multiple ways,
   - when retry policy is inspected,
   - then transient, source-content, config, and internal-bug classes each have bounded handling.

4. **Serving consequence coverage**
   - Given stale data can still retrieve,
   - when runtime behavior is specified,
   - then stale state changes serving/trace behavior for high-sensitivity lanes.

## 17.2 Operational acceptance checks

1. **Backstop proof**
   - Given an enabled root,
   - when no change trigger fires,
   - then a scheduled backstop still attempts refresh within the configured window.

2. **Retry bound proof**
   - Given a transient DB outage,
   - when refresh fails,
   - then the system retries only within the declared budget and surfaces `failed_refresh` if still unsuccessful.

3. **Stale detection proof**
   - Given a file changes under `task-manager/handoffs/`,
   - when that change is not ingested within trigger grace / hard max windows,
   - then the root becomes `aging` then `stale` and is visible as such.

4. **Trace proof**
   - Given a continuation request served while handoff data is stale,
   - when the retrieval trace is inspected,
   - then it shows stale handoff state and any authority downgrade/warning.

5. **Chronic-failure proof**
   - Given the same root repeatedly fails to refresh,
   - when failures exceed the budget for a prolonged period,
   - then operator-visible escalation occurs rather than silent degradation.

---

## 18. Implementation notes aligned to the verified contour

These are guidance notes, not claims that all code already exists.

1. Use the verified ingest entrypoint `pkm-memory/ingest_sources.py` as the canonical ingest executor rather than inventing a second ingest path.
2. Reuse or extend `ingestion_runs` and `pkm-memory/state/ingestion_state.json` for freshness computation before creating a separate state silo.
3. Keep source-root freshness computation close to the retrieval orchestration’s freshness evaluator from task #456.
4. Do not let local-file fallback bypass stale-state reporting; fallback should preserve the freshness caution model.
5. Typed-object freshness should be added only after the lexical/source freshness path is inspectable enough to support it.

---

## 19. Final decision statement

Adopt a **hybrid trigger + scheduled-backstop freshness policy** for the current three enabled roots, with root-specific SLOs, bounded retry/failure handling, stale-aware serving behavior, and explicit operator visibility.

This policy is intentionally conservative:
- it does not assume a perfect event system;
- it does not require typed-memory completeness first;
- it does require that the live lexical backbone stop operating as if freshness were implicit.

That is the minimum credible policy needed to move the current memory contour from useful-but-stale-prone to decision-grade and operable.

---

## 20. Claim / evidence / verification note

### Claim
This artifact completes task #457 by defining a bounded, execution-facing freshness and ingestion policy for the current OpenClaw memory contour.

### Evidence
The artifact makes all required policy surfaces explicit:
- refresh triggers are defined in Section 8;
- cadence/default schedule and hybrid trigger model are defined in Section 9;
- ownership boundaries are defined in Section 14;
- source-root expectations and SLOs are defined in Section 6;
- failure classes, retry budgets, and partial-success handling are defined in Section 11;
- operator visibility and retrieval-trace expectations are defined in Sections 13 and 15;
- rollout phases and bounded acceptance checks are defined in Sections 16 and 17.

It also stays aligned to predecessor constraints:
- task #455 by treating freshness as a first-class runtime risk and preserving the PostgreSQL lexical backbone;
- task #456 by binding freshness to the serving planner / freshness evaluator / trace envelope contract;
- task #445 by preserving lane-sensitive serving behavior and making stale-state visibility explicit so authority drift is inspectable rather than hidden.

### Verification basis
Task #457 acceptance criteria are satisfied because the artifact now explicitly answers:
1. which approved roots exist and what freshness target each root carries;
2. which trigger classes, debounce rules, and cadence defaults govern refresh behavior;
3. how retries, failure saturation, and partial success are handled;
4. what operators and retrieval traces must be able to see;
5. how stale or unknown freshness alters serving behavior for sensitive lanes.

### Closure recommendation
This task is ready to move through review to done/closed as a policy/specification task. Follow-on implementation should proceed in downstream execution slices rather than broadening #457 itself.
