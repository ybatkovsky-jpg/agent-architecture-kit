# Memory Freshness and Ingestion Policy

## Purpose

This document defines a reusable freshness and ingestion policy for a memory runtime that depends on indexed durable sources.

The core design goal is simple:
- freshness must be explicit;
- freshness must affect serving behavior;
- ingest behavior must be bounded, observable, and lane-safe.

A lexical corpus may remain the evidence backbone, but it should not be treated as trustworthy unless each approved source root has a declared freshness expectation, trigger model, retry policy, and visible stale-state behavior.

---

## Core decisions

1. Freshness is a serving input, not just an ingestion concern.
2. Each approved source root should have its own SLO tier.
3. Change-triggered ingest is preferred, but scheduled backstop ingest is mandatory.
4. Retries must be bounded and source-run scoped.
5. Staleness must be visible to both operators and retrieval logic.
6. Typed-memory freshness remains downstream of source and lexical freshness.

---

## Freshness object model

Freshness should be evaluated at four levels:
1. source-root freshness — whether a root has been scanned and reconciled recently enough;
2. document-index freshness — whether changed files are represented in the indexed corpus;
3. typed-object freshness — whether typed objects derived from evidence remain valid;
4. serving freshness — whether the runtime may serve results for a lane without warning, demotion, or escalation.

A newer source with older index state means the root is stale, even if retrieval still returns plausible content.

---

## Freshness states

Each root should be classifiable as one of:
- `fresh`
- `aging`
- `stale`
- `failed_refresh`
- `unknown`

Useful per-root timestamps include:
- `last_successful_ingest_at`
- `last_attempted_ingest_at`
- `last_detected_source_change_at`
- `oldest_uningested_change_at` when known

State semantics:
- **fresh** — within target SLO and no excessive pending change lag
- **aging** — beyond preferred target but still within hard max lag
- **stale** — beyond hard max lag or pending change exceeds grace
- **failed_refresh** — recent attempts exhausted retry budget
- **unknown** — no trustworthy freshness state is available

---

## Source-root policy tiers

Different source roots should carry different freshness expectations because their failure modes differ.

Example pattern:

| Root class | Typical role | Target freshness SLO | Hard max lag | Trigger grace | Serving sensitivity |
|---|---|---:|---:|---:|---|
| durable memory notes | preferences, reusable memory, stable constraints | 30 min | 6 h | 10 min | medium-high |
| task/artifact store | design, audit, decisions, architecture artifacts | 15 min | 4 h | 5 min | high |
| handoff / continuation store | active resume and continuity state | 5 min | 1 h | 2 min | very high |

The exact numbers may vary by system, but the policy pattern should remain root-specific rather than globally uniform.

---

## Two-layer refresh model

Use two refresh mechanisms together:

### 1. Change-triggered refresh
Preferred path for fast convergence after detected source changes.

### 2. Scheduled backstop refresh
Mandatory correctness layer for missed events, watcher failure, or degraded runtime conditions.

This combination gives both responsiveness and resilience.

---

## Retry policy

Retry must be bounded.

Rules:
- retries are scoped to a root-run or ingest-run;
- no unbounded retry loops;
- exhaustion of retry budget must produce a visible failing or stale state;
- the next scheduled attempt or explicit manual intervention becomes the recovery path.

A system should never drift into a silent forever-fail ingest contour.

---

## Lane-aware serving consequences

Staleness must change serving behavior by lane.

Typical pattern:

| Lane | Stale sensitivity | Required behavior |
|---|---|---|
| continuation / resume | highest | do not silently present stale continuation as current |
| current task execution | high | surface that task state may lag |
| architecture / policy recall | high | demote confidence and show stale trace state |
| preference recall | medium | may serve with warning if no fresher contradiction exists |
| general lookup / meta evaluation | medium | trace and confidence shaping should reflect stale state |

Authority implications:
1. fresh or aging evidence may serve normally within lane policy;
2. stale evidence may still support fallback, but should not silently appear current when recency matters;
3. failed-refresh evidence should be explicitly tagged;
4. typed objects derived from stale evidence should inherit stale-state unless revalidated.

---

## Minimum trace visibility

Every memory-serving trace should eventually expose at least:
- source roots consulted;
- freshness state per consulted root;
- latest successful ingest time per consulted root;
- whether newer source changes are known but not yet ingested;
- whether stale state altered ranking, authority, or answer wording.

---

## Trigger model

A robust ingest policy should combine multiple trigger classes:
- change-detected trigger;
- scheduled backstop trigger;
- operator/manual trigger;
- recovery trigger after bounded failure.

No single trigger class is enough for a reliable memory runtime.

---

## Operator visibility requirements

Operators should be able to answer quickly:
- when each approved root last ingested successfully;
- what changed since the last ingest;
- which roots are within SLO and which are stale;
- which runs failed and how many times;
- whether a stale root affected a served answer.

Freshness policy that is invisible to operators is operationally weak even if the ingest loop technically exists.

---

## Design summary

The durable pattern is:
- source-specific freshness tiers;
- explicit freshness states;
- change-triggered ingest plus scheduled backstop;
- bounded retries;
- lane-aware stale-state serving consequences;
- operator-visible freshness traces.

That is what makes memory freshness a runtime discipline rather than a vague background maintenance task.
