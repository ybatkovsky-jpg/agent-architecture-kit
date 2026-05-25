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

## Non-triggers that must not be mislabeled as escalation

The following do **not** by themselves justify escalation:
- discovering that the current plan was wrong;
- discovering a deeper root cause;
- replacing a fake problem with the real one;
- finding a missing implementation seam;
- realizing that prior green checks were only local, not global.

These events should usually cause **rerouting inside the same frontier**, not escalation.

Default correction:
- shrink to the next honest bounded leaf;
- keep the same owner when authority still holds;
- continue until a real external dependency, approval need, or material risk appears.

## False-blocker test before escalation

Before emitting `BLOCKED` / escalating, the unit should ask:

1. Is the next strong move already known?
2. Can I execute that move with the tools/authority I already have?
3. Is the move still part of the same task frontier rather than a new program?
4. Would stopping now merely convert diagnosis into chat noise?

If answers are `yes, yes, yes, yes`, escalation is premature and the unit should continue.

## Canonical phrasing rule

Use escalation only for conditions equivalent to:
- "I cannot proceed without outside approval, authority, missing access, or unacceptable risk."

Do **not** use escalation for conditions equivalent to:
- "I now understand what I should do next."
