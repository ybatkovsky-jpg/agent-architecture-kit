# Thin Main and Isolated Execution

## Principle

The main conversational surface should stay thin.

Its job is to:
- receive requests;
- frame decisions;
- orchestrate execution;
- return concise outcomes.

It should not be the default sink for heavy, stateful, or multi-step bounded work.

## Why

Long execution inside the main thread causes:
- context bloat;
- ownership ambiguity;
- weak recovery paths;
- poor continuation hygiene.

## Better model

Route real work into explicit execution lanes.

Typical lanes:
- orchestrator
- bounded execution
- artifact production
- human decision
- background observation

## Minimal handoff vocabulary

A simple but strong transition model is:
- `ACK` — ownership accepted
- `DONE` — bounded responsibility completed with durable result anchor
- `BLOCKED` — local continuation no longer justified; decision/escalation required

### `BLOCKED` is a hard condition, not a convenient checkpoint

`BLOCKED` should be emitted only when continuation is no longer justified **inside the current authority and capability envelope**.

It is **not** enough that the run has:
- found the real problem;
- reduced ambiguity;
- identified the next implementation leaf;
- produced a sharper diagnosis than before.

Those are signs of successful progress, not blockage.

A run must **not** surface `BLOCKED` if the next bounded move is still:
- technically available now;
- inside the same task frontier;
- inside the same authority boundary;
- low-risk enough to execute without human approval.

In that case the correct action is:
- open or enter the next bounded leaf;
- continue execution;
- return only after `DONE`, a real blocker, or a material risk alert.

### False-blocker anti-pattern

A common failure mode is:
1. the run finds that the original assumption was wrong or incomplete;
2. the run discovers the true critical path;
3. the run reports a "blocker" immediately;
4. but the discovered blocker is actually internal and actionable by the same run.

This is a **false blocker**.

Canonical rule:

> "Now I know what the real next step is" is **not** a blocker.

If the obstacle is removable by the same agent through another bounded implementation, verification, or cleanup slice, the run should continue rather than escalate.

## Retry discipline

Retries should be budgeted, not emotional.

Good default:
- one initial attempt
- zero automatic retries unless explicitly justified

## Goal

Keep the human-facing surface clean while preserving execution power and recoverability.
