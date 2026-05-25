# Plan / Task / Queue Sync Contour

## Purpose

Define how a system keeps publishing intent synchronized across three different but related objects:

- **plan items** — human scheduling and editorial intent;
- **tasks** — execution and production work units;
- **queue items** — delivery-ready channel payloads.

This contour exists because these are not the same object, but they often need to refer to the same publishing outcome.

---

## Problem this contour solves

Without an explicit sync contour, systems drift into one of two failures:

1. **collapsed identity**
   - plan, task, and queue are treated as if they were the same thing;
   - local edits in one layer silently corrupt another.

2. **broken continuity**
   - plan item says one slot is queued;
   - task state points somewhere else;
   - queue metadata has stale `post_id`, `package`, or schedule values;
   - humans lose confidence because no surface agrees.

A content workflow with approval and publishing needs these layers to remain distinct **and** linked.

---

## Architecture decision

Use **linked identities with directional synchronization**, not shared mutable identity.

The recommended model:
- plan item owns editorial/scheduling intent;
- task owns execution progress and artifact production;
- queue item owns delivery payload and runtime publish state.

Synchronization should be explicit, eventful, and field-scoped.

---

## Core identity anchors

A durable sync contour should maintain identifiers such as:

- `plan_id`
- `plan_item_id`
- `task_id`
- `queue_item`
- `package`
- `post_id`

These anchors should travel in queue/task metadata rather than being re-inferred from filenames every time.

---

## Directional ownership

### 1. Plan item owns editorial intent

The plan item should own fields such as:
- scheduled slot intent;
- editorial notes;
- per-slot approval state at the planning layer;
- package/post mapping when already known.

### 2. Task owns execution lineage

The task should own:
- generation work;
- content production state;
- artifact creation history;
- task-level publish summary rollups.

### 3. Queue item owns delivery runtime

The queue item should own:
- channel payload fields;
- approval gate state for delivery;
- retry and scheduling runtime state;
- published result metadata.

---

## Sync principles

### Principle 1 — sync fields, not whole objects

Do not overwrite an entire queue item from a task or plan blob.
Instead, synchronize specific blocks:
- metadata anchors;
- platform payload fields;
- approval state;
- schedule state;
- publish runtime state;
- rework/comment state.

### Principle 2 — preserve source-specific truth

If a field belongs to plan intent, queue sync should not overwrite it casually.
If a field belongs to publish runtime, plan editing should not pretend to own it.

### Principle 3 — sync should be eventful

A sync operation should leave a durable event trail.
This allows later reconstruction of why a plan slot, task, and queue item currently align the way they do.

---

## Bridging pattern

A useful bridging pattern is:

1. approved plan item creates or references a task;
2. task produces content artifacts;
3. queue item is generated either:
   - directly from plan/package metadata, or
   - by bridging from task output when package/post mapping already exists there;
4. queue item writes back its current delivery state to the plan slot and task summary;
5. plan slot remains human-readable while queue item remains transport-accurate.

This bridge avoids forcing one object to impersonate all three roles.

---

## Fallback identity generation

In real systems, `package` or `post_id` may be absent at first.

A robust contour may use deterministic fallback generation from:
- plan item identity;
- task identity;
- content-derived topic slug.

But architecture rule:
- fallback identity is a bridge aid, not a license for permanent ambiguity.

Once canonical mapping is known, it should be written back into the linked objects.

---

## Queue generation from plan items

A plan-driven queue generator should:
- refuse impossible states cleanly;
- generate queue items when package/post mapping is available;
- remain able to bridge from task-originated queue objects when task reality is ahead of plan bookkeeping;
- persist the chosen queue item back into the plan item generation block.

This allows human planning and execution reality to converge instead of fork.

---

## Schedule synchronization rule

A plan slot’s scheduled time and a queue item’s effective publish schedule are related but not identical.

Recommended split:
- plan slot keeps editorial target schedule;
- queue item keeps runtime `proposed_for` and `scheduled_for` fields;
- sync writes queue schedule back into plan visibility, but does not erase the conceptual distinction.

This matters when approval or runtime timing changes the effective delivery time.

---

## Rework and human review propagation

If a queue item becomes `rework_requested` or otherwise fails an approval gate:
- queue runtime should keep the concrete blocking reason;
- task state should reflect that human review is now required;
- plan slot should move into a revision-needed state visible at the planning surface.

This is one of the most important sync moments because it converts local delivery failure into system-visible editorial work.

---

## Task-level publish aggregation

A task may have more than one queue item over time.

Therefore task state should not simply point to “the queue item.”
It should maintain an aggregate publish block built from current queue truth.

This protects against:
- stale references;
- superseded queue items;
- ambiguous old task-generated artifacts;
- mismatch between operator view and delivery runtime.

---

## Why this contour matters

Many operator systems fail because they solve generation, planning, and delivery separately but never define the sync contract between them.

The result is familiar:
- the plan view looks plausible;
- the task view looks busy;
- the queue view is the only real runtime truth;
- humans must manually reconcile all three.

A good sync contour removes that reconciliation burden.

---

## Anti-patterns

Avoid these:

### 1. Filename-only identity
Inferring durable mapping only from filenames is brittle.

### 2. Whole-object overwrite sync
Replacing entire queue or plan documents from another layer destroys source-specific truth.

### 3. Silent fallback permanence
Temporary fallback IDs should not remain forever once canonical mapping is known.

### 4. Queue state hidden from task/plan surfaces
If the queue knows that review or retry is blocking delivery, task and plan surfaces should expose that meaning.

### 5. Treating plan schedule as transport truth
Editorial intent and runtime due state are adjacent, not identical.
