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

## Retry discipline

Retries should be budgeted, not emotional.

Good default:
- one initial attempt
- zero automatic retries unless explicitly justified

## Goal

Keep the human-facing surface clean while preserving execution power and recoverability.
