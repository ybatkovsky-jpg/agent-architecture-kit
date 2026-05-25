# Surfaced-Recorded Execution Integrity Contract

## Purpose

Prevent a system from accumulating real execution traces without a task-bound, surfaced, canonical work trail.

This contract addresses the failure pattern seen when scripts, reruns, raw outputs, or partial verification files exist in the workspace, but the task control plane cannot honestly answer:
- what bounded work slice was executed;
- which task the execution belongs to;
- what result was surfaced;
- whether the raw output was promoted into durable proof;
- whether the task is actively progressing or merely appears busy.

The goal is not only better summaries.
The goal is to make unsurfaced execution mechanically visible and eventually mechanically disallowed.

---

## Problem statement

A task system can currently show `in_progress` while execution reality lives elsewhere:
- task state exists in the task manager;
- runtime continuity exists in autonomy/watchdog state;
- outputs exist on disk;
- artifacts may exist under unrelated names;
- user-visible progress may be absent;
- no single task-bound surface records the execution slice as canonical operational truth.

This produces the orphan-evidence pattern:
1. work happened;
2. evidence exists somewhere;
3. task-specific proof does not exist or is stale;
4. operators cannot distinguish “no work happened” from “work happened but escaped the task trail”.

---

## Contract summary

A significant execution step is valid only when it is both:
1. **recorded** in a task-bound canonical surface; and
2. **surfaced** as a named result, blocker, or bounded-progress update.

This yields the minimum integrity rule:

> No significant execution result may remain only in raw runtime traces or filesystem residue.

For this contract, a system must maintain six linked elements:
1. execution ledger;
2. mandatory task binding;
3. surface-or-fail discipline;
4. artifact promotion path;
5. orphan evidence detection;
6. work-state distinct from task-state.

---

## 1. Execution ledger

### Rule

Every significant execution slice must leave a task-bound ledger entry.

### Why

Task status alone is too coarse.
`in_progress` says the task is open, not what was actually executed.

### Minimum ledger fields

- `task_id`
- `slice_id` or timestamped execution entry id
- `goal`
- `owner`
- `started_at`
- `ended_at` or `last_progress_at`
- `mode` (`research`, `implementation`, `verification`, `handoff-prep`, etc.)
- `input_anchor` (what the slice resumed from)
- `raw_outputs[]`
- `promoted_artifacts[]`
- `verification_refs[]`
- `result_class` (`bounded_progress`, `done_candidate`, `blocked`, `invalidated`, `needs_followup`)
- `surface_state` (`not_surfaced`, `progress_surfaced`, `terminal_surfaced`)

### Canonical placement

For OpenClaw Frame / TM-shaped systems:
- lifecycle status remains in task state/events;
- execution ledger belongs either in task-manager task metadata or a task-scoped runtime state object linked from task events;
- chat summaries are projection only.

---

## 2. Mandatory task binding

### Rule

Any script, output, verification pack, artifact, or result used as task evidence must resolve to a task binding.

### Binding means

At minimum, the system can answer:
- which `task_id` owns this execution object;
- whether it is raw output or promoted proof;
- whether it is current, superseded, or unrelated residue.

### Acceptable binding mechanisms

At least one of:
- task-scoped path naming convention;
- embedded task metadata inside JSON/markdown frontmatter;
- task event linking the object path;
- promotion artifact that explicitly references the raw output path and parent task id.

### Non-compliant state

These are not enough:
- a filename that happens to mention a task in a different numbering family;
- “we know what it was for” from chat memory;
- a script/output pair with no task event linking them.

---

## 3. Surface-or-fail discipline

### Rule

After a significant execution step, the system must either:
1. surface a bounded progress update tied to the task;
2. surface a terminal result or blocker tied to the task; or
3. mark an integrity fault.

### Significant execution step

A step is significant when it produces one or more of:
- changed code or config;
- generated outputs intended as evidence;
- verification results;
- reruns whose result changes the task’s truth;
- artifacts later cited in review/done transitions.

### Implication

Silent accumulation of important outputs is not a normal state.
It is either temporary and short-lived, or it is an integrity defect.

### Minimum enforcement seam

For TM-like systems, this discipline should not be checked only at `done`.
It should also be checked:
- after autonomous bounded slices;
- when watchdog progress windows expire;
- when a task remains `in_progress` with new filesystem evidence but no fresh task trail.

---

## 4. Artifact promotion path

### Rule

Raw execution residue is not automatically proof.
The system must distinguish:
1. raw output;
2. verification summary;
3. promoted task artifact;
4. transition proof.

### Promotion chain

#### A. Raw output
Examples:
- rerun JSON;
- logs;
- temporary reports;
- generated files in repo-specific output folders.

#### B. Verification summary
A bounded interpretation that states:
- what was tested or observed;
- what passed/failed;
- which raw outputs were consulted.

#### C. Promoted task artifact
A task-bound durable document or structured artifact suitable for future review and resume.

#### D. Transition proof
Fresh claim/evidence/verification/anchor material used for `review` / `done` / `accept` gates.

### Implication

A task may have raw outputs without being review-ready.
A task may have a promoted artifact without being done.
A transition must still cite fresh proof.

---

## 5. Orphan evidence detection

### Rule

The system must actively detect likely evidence that exists without a corresponding task trail.

### Detection goal

Not to prove semantic ownership perfectly, but to catch high-risk ambiguity mechanically.

### Detection heuristics

For live tasks, flag when any of the following are true:
- task is `in_progress`, but recent outputs/scripts reference work matching the task scope and there is no recent note/event/artifact link;
- raw outputs were created after the last task proof event and no promotion/surfacing event followed;
- a verification artifact exists, but no task event references it;
- task manager `next_action` implies execution, but the ledger has no fresh slice record;
- result files are newer than the last surfaced task update by a suspicious margin.

### Output of detector

The detector should not silently mutate truth.
It should emit one of:
- `integrity_ok`
- `needs_surface`
- `orphan_evidence_suspected`
- `task_binding_missing`

These should be attachable to watchdogs, dashboards, and review gates.

---

## 6. Work-state distinct from task-state

### Rule

`task_state` and `work_state` must not be collapsed.

### Task-state answers
- Is the task open, in progress, waiting, review, done?
- What is the official next action?
- Who owns the next transition?

### Work-state answers
- What slice is currently running or last ran?
- Was real execution observed recently?
- Was the latest slice surfaced?
- Are there unsurfaced outputs?
- Is closure pending, verification pending, or follow-up split pending?

### Why this split matters

Without it, `in_progress` becomes a vague umbrella that can hide:
- active implementation;
- stalled execution;
- unsurfaced evidence;
- pending closure decision;
- silent failure to report results.

### Recommended work-state fields

- `execution_stage`
- `slice_goal`
- `slice_started_at`
- `last_progress_at`
- `slice_done`
- `closure_required`
- `surface_required`
- `unsurfaced_output_count`
- `orphan_evidence_status`
- `verification_pending`
- `followup_split_needed`

---

## Mapping to existing OpenClaw/TM surfaces

### Already present in task-manager

The current TM/autonomy runtime already contains useful seams:
- `task_events` as lifecycle/event trail;
- autonomy `watchdog` fields such as `last_progress_at`, `anti_silence_due_at`, `forced_reroute_reason`, `final_surface_required`;
- `closure_loop` fields such as `execution_stage`, `slice_goal`, `slice_done`, `closure_required`, `followup_split_needed`, `next_slice_required`;
- status transition validation and fresh-proof gates for `review` / `done`.

### What is still missing or under-bound

1. **explicit execution ledger entries**
   - current runtime state has slice-like fields but not a normalized task-bound ledger of significant executions.

2. **mandatory task binding for artifacts/outputs**
   - existing docs distinguish task truth from artifact truth, but the runtime does not yet require evidence objects to be linked back to the owning task.

3. **surface-or-fail for non-terminal execution**
   - strong terminal surfacing exists, but bounded non-terminal execution can still leave weak or missing task-bound notes.

4. **promotion chain semantics**
   - raw output vs verification summary vs promoted artifact vs transition proof is not consistently modeled as a first-class contract.

5. **orphan evidence detector**
   - no first-class integrity status appears to mark “filesystem evidence exists, but task trail is missing or stale”.

6. **first-class work-state exposure**
   - pieces exist inside autonomy state, but they are not yet framed as the canonical answer to “is work really happening and is it surfaced?”.

---

## Recommended bounded TM enforcement slice

A minimal first enforcement slice should do the following without redesigning the whole system:

### Slice A — explicit integrity state
Add a task-scoped integrity/work-state block that can answer:
- `surface_required`
- `orphan_evidence_status`
- `last_surface_at`
- `last_ledger_entry_at`
- `unsurfaced_output_count`

### Slice B — progress-note binding rule
When significant execution finishes, require one of:
- task note with raw output links and result classification;
- promoted artifact link;
- terminal status transition with fresh proof.

Otherwise mark the task as integrity-degraded rather than merely `in_progress`.

### Slice C — watchdog integrity check
Extend watchdog logic so that it can route not only on silence, but also on:
- `final_result_not_surfaced`
- `significant_progress_not_surfaced`
- `orphan_evidence_suspected`

### Slice D — artifact/link convention
Require task-bound references for promoted proof objects, at least by path or event link, so later audits do not depend on transcript archaeology.

---

## Review/done implications

This contract does not weaken the existing closure-proof rule.
It strengthens the path leading up to it.

Current strong rule:
- `review` / `done` require fresh inline proof.

Additional rule introduced here:
- meaningful execution cannot remain unsurfaced until the very end.

That means the system gains two gates:
1. **progress integrity gate** — catches invisible execution while work is still underway;
2. **closure proof gate** — catches unsupported terminal claims.

---

## Acceptance criteria for this contract

A system satisfies surfaced-recorded execution integrity when:
1. every significant execution slice leaves a task-bound ledger or equivalent durable runtime entry;
2. evidence objects resolve to a task binding;
3. important execution results are surfaced quickly or flagged as integrity faults;
4. raw outputs are distinguishable from promoted proof;
5. likely orphan evidence is detectable mechanically;
6. operators can distinguish task-state from work-state without reading chat residue.

---

## Non-goals

This contract does not require:
- full semantic attribution of every file in the workspace;
- replacing artifacts with chat summaries;
- making raw outputs user-facing by default;
- collapsing task manager, memory, and evidence into one object.

---

## One-line rule

> If execution happened, the task control plane must be able to show where it was recorded, how it was surfaced, and whether its raw outputs were promoted into task-bound proof.