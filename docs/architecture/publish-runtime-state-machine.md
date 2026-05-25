# Publish Runtime State Machine

## Purpose

Define the runtime control model for review-gated channel publishing.

This contour describes how a publish worker should behave once a queue item already exists and is moving through approval, schedule gating, retry handling, locking, and final delivery.

It is not a content-generation note.
It is a delivery-runtime note.

---

## Problem this contour solves

A publish queue often starts simple and then quietly accumulates hidden states:
- waiting for approval;
- approved but not yet due;
- temporarily blocked by retry timing;
- actively publishing;
- published;
- failed terminally;
- rejected or canceled by humans.

If these states are not modeled explicitly, operators get misleading answers such as:
- “ready” when the item is actually schedule-blocked;
- “failed” when it should retry;
- “approved” when it is not yet publishable;
- duplicate publishes caused by concurrent workers.

---

## Core architecture decision

A publish queue item should carry an explicit **runtime state block** and be processed by a worker that behaves like a small deterministic state machine.

At minimum, the runtime layer should model:
- approval gate state;
- schedule gate state;
- retry gate state;
- publish attempt bookkeeping;
- terminal outcome state;
- concurrency lock state.

---

## Recommended runtime fields

A useful runtime block includes:

- `status`
- `approval.required`
- `approval.status`
- `schedule.proposed_for`
- `schedule.scheduled_for`
- `schedule.approved`
- `publish.attempt_count`
- `publish.max_attempts`
- `publish.last_attempt_at`
- `publish.next_attempt_after`
- `publish.last_error`
- `publish.last_error_kind`
- `publish.last_http_status`
- `publish.last_retryable`
- `published_at`

These fields let the runtime answer three different questions cleanly:
1. should this item publish now?
2. if not, what gate is holding it?
3. if something failed, is the next move retry, review, or terminal stop?

---

## State classes

### 1. Human-gated states

- `waiting_approval`
- `rework_requested`
- `rejected`
- `canceled`

These states are controlled primarily by human review or explicit workflow policy.

### 2. Runtime-ready states

- `ready`
- `locked`
- `retry_scheduled`
- `scheduled`

These states are operational and time-sensitive.
They do not necessarily require new human input.

### 3. Terminal delivery states

- `published`
- `failed`

A terminal state should be stable and interpretable without replaying runtime logs.

---

## Gate order

A strong processing order is:

1. terminal-state check;
2. approval gate;
3. retry gate;
4. status readiness check;
5. lock acquisition;
6. payload completeness check;
7. transport attempt;
8. success or failure registration;
9. task-state sync.

Why this order matters:
- approval should short-circuit delivery;
- retry delay should short-circuit transport;
- lock acquisition should happen only when a real attempt is plausible;
- state sync should happen after durable item updates.

---

## Schedule is a gate, not just metadata

A scheduled timestamp must not be treated as decorative context.
It is an execution gate.

Architecture rule:
- `approved` is not the same as `publishable now`.

A correct model distinguishes:
- approval has happened;
- the item is due or not due;
- retry timing may still delay transport even after due time.

---

## Retry model

Retries should be explicit and bounded.

Recommended behavior:
- classify errors into retryable vs non-retryable;
- keep `attempt_count` and `max_attempts` on the item;
- compute `next_attempt_after` deterministically;
- move to terminal `failed` only when retry is not justified or budget is exhausted.

Good examples of retryable classes:
- rate limit;
- timeout;
- transport/network failure;
- upstream 5xx.

Good examples of non-retryable classes:
- invalid request payload;
- missing target;
- missing media/caption file;
- unauthorized or misconfigured destination when known to be persistent.

---

## Failure registration contract

A failure should not just set `status=failed` and stop.

A proper failure registration unit should answer:
- what attempt failed;
- what the error kind was;
- whether retry remains allowed;
- when the next retry is due if any;
- whether the task-level state should now read as failed, approved, or review-blocked.

This is the difference between a queue that can recover and a queue that only accumulates scars.

---

## Locking and concurrency

A publish worker should use per-item locking.

Why:
- queue polling and manual publish commands can overlap;
- retries and ad-hoc force runs can race;
- chat-driven operator systems often issue duplicate publish triggers under uncertainty.

Minimal rule:
- if a lock for the queue item already exists, the worker should report `locked` rather than attempt transport.

This is a runtime architecture concern, not merely an implementation nicety.

---

## Task-level aggregation

A task with one or more queue items should expose an aggregated publish view rather than forcing operators to inspect raw queue files.

Useful task-level summary fields:
- `total`
- `waiting_approval`
- `ready`
- `scheduled`
- `retry_scheduled`
- `rework_requested`
- `published`
- `failed`
- `rejected`
- `canceled`

From this summary, derive task-facing flags such as:
- `approval_pending`
- `ready_for_publish`
- `needs_human_review`
- `publish_failed`
- `published`

This aggregation turns queue runtime into operator-usable truth.

---

## Why this contour is separate from the media seam

The media seam explains how approval and publish consume the same resolved media object.

This runtime state machine explains how an already-resolved queue item progresses through delivery control.

Both matter, but they solve different classes of failures:
- media seam → payload truth and preview correctness;
- runtime state machine → gating, retries, concurrency, and terminal outcomes.

---

## Minimal reference flow

1. queue item exists with resolved channel payload;
2. runtime checks human approval state;
3. runtime checks retry timing;
4. runtime checks due schedule;
5. runtime acquires item lock;
6. runtime validates payload completeness;
7. runtime attempts delivery;
8. on success, marks `published` and records result;
9. on failure, records classified error and either schedules retry or moves to terminal failure;
10. task-level publish summary is refreshed from queue truth.

---

## Anti-patterns

Avoid these:

### 1. Conflating `ready` with `publishable now`
This hides schedule and retry gates.

### 2. Recording only free-text errors
Without structured error kind and retryability, operations become guesswork.

### 3. Retrying blindly
Retries without budget or classification create noise and duplicate risk.

### 4. Treating publish state as channel-only state
The queue item and task-level state must stay synchronized.

### 5. Ignoring concurrency
Duplicate sends are architecture failures, not harmless runtime accidents.
