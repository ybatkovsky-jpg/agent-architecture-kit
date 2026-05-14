# Memory Observability and Trace Debug

## Purpose

This document defines a reusable observability contour for memory-answer decisions.

The goal is not unbounded logging.
The goal is bounded explainability: an operator should be able to understand how the runtime classified a request, chose sources, ranked candidates, handled fallback and freshness, and shaped the final answer.

---

## Core decisions

1. A memory decision trace should be a first-class runtime object.
2. The trace should separate observed execution facts from policy verdicts and answer-shaping decisions.
3. Trace detail should be tiered so routine serving stays cheap while deep debug remains available on demand.
4. Redaction should be mandatory by default.
5. Fallback and stale-state behavior must be visible, not implicit.

---

## Trace levels

Use at least three levels:
- **inline** — very small explanation hints safe for normal output metadata;
- **summary** — bounded operator-facing diagnosis view;
- **deep** — fuller event stream for targeted incident analysis.

The system should not pay deep-trace cost on every routine request.

---

## Canonical trace envelope

Each memory-serving run should be able to produce a `memory_decision_trace` object with a shape like:

```json
{
  "trace_id": "memtrace_...",
  "request_id": "...",
  "timestamp": "...",
  "runtime_version": "...",
  "policy_version": "...",
  "trace_level": "inline|summary|deep",
  "mode": "auto|psql|local|typed_hybrid",
  "status": "success|partial|fallback|failed",
  "request": { },
  "classification": { },
  "plan": { },
  "stages": [ ],
  "final_decision": { },
  "redaction": { },
  "retention": { }
}
```

---

## Required trace blocks

### Request block

Should include:
- normalized query hash or bounded query form;
- raw query only when policy explicitly allows it;
- actor, session, or task scope when available;
- backend mode requested;
- debug-flag source if deep trace was explicitly requested.

### Classification block

Should include:
- chosen lane or request class;
- classifier confidence bucket or score;
- bounded alternative classes;
- rationale signals as tags, not hidden chain-of-thought;
- citation expectation;
- authority-priority intent;
- retrieval budget class.

### Plan block

Should include:
- eligible retrieval planes;
- selected primary path;
- excluded paths with reasons;
- source-family allow/exclude sets;
- planned fetch and rerank budgets;
- freshness-policy hook chosen for the lane.

### Final decision block

Should include:
- winning serve path;
- whether typed objects were used, advisory, or bypassed;
- whether lexical evidence was primary, supporting, or replacement;
- whether fallback happened;
- whether stale-state warnings changed rank or envelope;
- top cited or supporting refs;
- final redaction actions.

---

## Stage event model

Each stage event should expose:
- `stage` as a stable enum;
- `started_at` / `ended_at`;
- `status` as `success|partial|skipped|failed`;
- `inputs_summary`;
- `decision_summary`;
- bounded artifacts such as IDs, counts, hashes, candidate refs, warnings;
- `policy_refs`;
- `redaction_class`.

The trace should explain decisions, not mirror every internal byte of execution.

---

## Useful stage set

A practical stage model includes:
1. `classification`
2. `source_selection`
3. `typed_fetch`
4. `lexical_fetch`
5. `local_fallback_fetch`
6. `ranking`
7. `authority_resolution`
8. `serving_pack_assembly`
9. `answer_shaping`
10. `trace_finalize`

When a stage is skipped, the trace should say whether it was:
- ineligible;
- empty;
- failed;
- policy-disabled.

---

## Redaction-first rules

Observability should not become a data leak.

Default redaction should suppress or heavily bound:
- raw personal data;
- secrets and tokens;
- unsafe file payloads;
- large prompt fragments;
- full raw content when hashes, IDs, locators, or short snippets are enough.

The default safe surface is:
- hashes;
- IDs;
- locators;
- bounded rationale summaries;
- small policy-approved snippets.

---

## Retention and cost posture

Trace retention should be tiered too:
- inline traces may be ephemeral;
- summary traces may persist for routine debugging windows;
- deep traces should be retained selectively and intentionally.

The point is inspectability without turning the system into an unbounded logging plane.

---

## Operator questions the trace should answer

For any inspected answer, an operator should be able to determine:
- what lane was chosen and why;
- which source families and retrieval planes were eligible, preferred, excluded, or used;
- which typed and lexical candidates mattered;
- whether freshness or fallback changed the result;
- what answer-shaping constraints were applied;
- what information is intentionally hidden or redacted.

---

## Acceptance checks

An observability contour is good enough when:
1. operators can diagnose wrong-lane or wrong-source decisions without reverse-engineering the whole codepath;
2. fallback and stale-state changes are visible;
3. lexical-only, typed-first, and mixed runs all fit the same trace model;
4. trace output remains bounded and redaction-safe by default;
5. deeper debug can be requested without polluting normal serving.

---

## Design summary

The durable observability pattern is:
- one canonical trace envelope;
- stage-based decision events;
- three trace levels;
- redaction-first policy;
- explicit fallback and freshness visibility.

That is what makes memory-answer behavior inspectable without turning observability into chaos.
