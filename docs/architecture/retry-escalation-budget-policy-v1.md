# Retry and Escalation Budget Policy v1

## Core rule

Retries are a budget, not a vibe.

If no retry budget is declared, the default mode is:
- one initial attempt;
- zero automatic retries.

## Budget classes

### `single-shot`
Use for most bounded drafting, inspection, and analysis slices.

### `light-retry`
Use for clearly local or transient issues.

### `timed-observation`
Use for monitoring or evidence capture where the main budget is a watch window rather than a retry count.

### `human-gated`
Use when work cannot continue without approval, authority, or new input.

## Escalation triggers

A unit must escalate when:
- retry budget is exhausted;
- an authority boundary is hit;
- an information boundary is hit;
- continuing would expand scope into a different task;
- a risk boundary is crossed;
- an observation deadline is reached.
