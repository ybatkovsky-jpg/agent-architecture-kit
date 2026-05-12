# Frame Baseline v1

This document captures the first stable baseline of the agent execution architecture.

## Core decisions

### 1. Main is a thin orchestrator
The main conversational surface should remain a place for:
- intent intake;
- orchestration;
- routing;
- decision-taking;
- short user-facing summaries.

It should not be the default sink for long, stateful, or execution-heavy work.

### 2. Handoff must use a small shared contract
Bounded work should use a unified handoff vocabulary:
- `ACK`
- `DONE`
- `BLOCKED`

This avoids ambiguous transitions and makes ownership legible.

### 3. Memory is a distillation layer
Memory should preserve:
- decisions;
- patterns;
- anti-patterns;
- blockers with reuse value;
- durable references.

Memory is not a full chat archive.

### 4. Routing must be explicit
The system should know, for each work type:
- target lane;
- execution owner;
- decision owner;
- durable state location;
- completion surface;
- escalation path.

### 5. Long contours need bounded retry budgets
Retries must be budgeted.
No unbounded persistence by default.

## Consequences

This baseline pushes the architecture toward:
- isolated bounded execution units;
- file-first durable state;
- explicit ownership;
- deterministic routing;
- memory distillation instead of transcript dependence.
