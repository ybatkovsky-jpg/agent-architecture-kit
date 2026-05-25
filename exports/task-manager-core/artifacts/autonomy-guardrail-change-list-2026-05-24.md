# Task #753 — autonomy guardrail change-list

Date: 2026-05-24
Owner: yuriy / OpenClaw
Purpose: prevent the failure mode where autonomous continuation is promised, but no real execution contour is armed before the assistant stops with a normal chat reply.

## 1. Problem statement

Current gap:
- `autonomy_mode` can express that a task should continue without the user,
- but there is no first-class distinction between:
  - autonomy requested,
  - autonomy armed,
  - autonomy execution anchor actually created.

This allows a false-positive autonomous claim:
1. operator/user says “continue autonomously”,
2. notes/plan are updated,
3. no spawned child / cron job / background anchor is created,
4. assistant still exits with a normal user-facing reply.

That is an execution-state defect, not just a wording defect.

---

## 2. Bounded implementation target

Land the smallest enforceable contour that makes “autonomous requested but not armed” visible and non-silent.

This slice should:
- separate requested-vs-armed autonomy in durable TM state,
- expose the armed execution mode and anchor,
- let watchdog/reporting detect promised-but-not-armed tasks,
- give router/policy a machine-readable state to refuse ack-only pseudo-autonomy,
- document the user-facing status contract.

This slice does **not** need to implement every upstream chat/runtime hook immediately.
It should first make the state and enforcement seam explicit and testable inside task-manager.

---

## 3. File-level changes

### A. `task-manager/autonomy_state.py`

#### Add durable execution-arm fields
Extend `default_autonomy_state()` with a new block:

```json
"execution": {
  "autonomy_requested": false,
  "autonomy_armed": false,
  "execution_mode": "none",
  "anchor_kind": "",
  "anchor_id": "",
  "requested_at": "",
  "armed_at": "",
  "last_armed_by": "",
  "non_armed_reason": ""
}
```

#### Normalize allowed execution modes
Add allowlist such as:
- `none`
- `current_run`
- `spawned_session`
- `openclaw_cron_agent_turn`
- `background_exec`
- `manual_hold`

#### Normalization rules
In `normalize_autonomy_state(...)`:
- if `autonomy_mode=true`, `execution.autonomy_requested=true`, and `execution.autonomy_armed=false`, preserve that explicitly instead of silently treating it as healthy autonomous progress;
- if an `active_child.kind` exists and maps to a known execution mode/anchor, infer `autonomy_armed=true` when safe;
- if `autonomy_mode=false`, clear armed/requested state unless explicitly preserved for audit;
- keep `non_armed_reason` when autonomy is requested but no anchor exists.

#### Add helper predicates
Add helpers like:
- `autonomy_arm_detected(state)`
- `autonomy_requested_but_not_armed(state)`
- `derive_execution_anchor(state)`

These will be reused by CLI/reporting/watchdog.

---

### B. `task-manager/task_manager.py`

#### `autonomy-init`
Current behavior should be tightened so it means:
- autonomy requested is true,
- autonomy armed is **false by default** unless a real anchor is passed or inferred,
- execution mode is `current_run` only if this command is explicitly used as the active continuation arm in the same execution contour.

Add optional flags:
- `--execution-mode`
- `--anchor-kind`
- `--anchor-id`
- `--arm yes|no`
- `--non-armed-reason`

Result:
- `autonomy-init` can record “requested but not yet armed” honestly.

#### `autonomy-enable`
Mirror the same execution block and optional arm flags.
Do not equate `autonomy_mode=true` with `autonomy_armed=true` automatically.

#### `autonomy-resume`
When resume actually schedules the next bounded pass:
- set `execution.autonomy_requested=true`
- set `execution.autonomy_armed=true`
- set `execution.execution_mode` to the real launcher mode
- write `anchor_kind` and `anchor_id`
- stamp `armed_at`

#### `watchdog(...)`
Add a new report bucket:
- `promised_not_armed_autonomy`

Inclusion rule:
- task is `in_progress`
- `autonomy_mode=true` or `execution.autonomy_requested=true`
- `execution.autonomy_armed=false`
- no valid active child/anchor exists

For this bucket emit:
- task id
- title
- current next action
- requested_at
- non_armed_reason
- suggested fix command / note

Do **not** auto-resume these silently on first slice.
This bucket is a control-plane defect surface, not normal stale work.

#### `autonomy-show` / `autonomy-status` / `show`
Expose:
- requested vs armed
- execution mode
- anchor kind/id
- non_armed_reason

This makes false autonomy visible to operators.

#### Add one explicit guard helper
Create a small helper inside `task_manager.py` or adjacent module:
- `autonomy_claim_is_honest(state) -> bool`

Use it in surfaces that present autonomy status so they can say:
- autonomous: armed
- autonomous: requested_not_armed
- autonomous: manual

---

### C. `task-manager/autonomy_router.py`

This file currently routes child completion outcomes, but it does not represent the prior defect class where autonomy is claimed without any armed executor.

#### Add non-armed execution-state awareness
Allow router/result metadata to carry:
- `execution_state`: `armed` | `requested_not_armed` | `manual`
- optional `execution_violation`: `promised_not_armed`

#### New bounded behavior
If a child/local result implies non-terminal continuation but the autonomy state says requested-not-armed, route should prefer:
- `escalate_internal`

with decision reason like:
- `Autonomy was requested but no live execution contour is armed; ack-only continuation is not a valid autonomous state.`

This does **not** mean the router itself must spawn work.
It means it should stop pretending the state is healthy.

---

### D. `task-manager/README.md`

Update autonomy docs with a new state model section:
- `autonomy_mode`: broad compatibility intent
- `execution.autonomy_requested`: user/operator asked for autonomous continuation
- `execution.autonomy_armed`: a real executor/anchor exists
- `execution.execution_mode`: how continuation is armed
- `execution.anchor_kind|anchor_id`: exact durable anchor

Add user-facing status contract:
- `autonomous: armed`
- `autonomous: requested_not_armed`
- `autonomous: manual`

And explicitly document:
- a note/plan update alone is **not** autonomy arming.

---

### E. Tests

#### `task-manager/test_autonomy_controls.py`
Add assertions for:
- `autonomy-enable` without anchor sets requested=true, armed=false unless explicitly armed
- `autonomy-stop` clears requested/armed state as expected
- status surfaces expose requested-vs-armed correctly

#### `task-manager/test_autonomy_watchdog.py`
Add one task with:
- `autonomy_mode=true`
- requested=true
- armed=false
- no active child

Expected:
- appears in `promised_not_armed_autonomy`
- does **not** appear in normal resumable bucket
- no cron resume is spawned for it automatically

#### New test: `task-manager/test_autonomy_false_arm_guard.py`
Cover:
1. init requested-not-armed state,
2. verify visibility in status/show,
3. verify watchdog defect bucket,
4. verify real resume path flips it to armed with anchor.

---

## 4. Suggested implementation order

1. Extend durable state model in `autonomy_state.py`
2. Wire CLI visibility in `task_manager.py`
3. Add watchdog defect bucket
4. Add tests for requested-vs-armed behavior
5. Tighten router metadata / internal escalation semantics
6. Update README

---

## 5. Verification plan

Minimum proof for this slice:

1. `python3 task-manager/test_autonomy_controls.py`
2. `python3 task-manager/test_autonomy_watchdog.py`
3. `python3 task-manager/test_autonomy_false_arm_guard.py`
4. optionally broader regression:
   - `python3 task-manager/test_autonomy_router.py`
   - `python3 task-manager/test_autonomy_state_and_gate.py`

Expected proof statements:
- autonomy requested without arm is now durable and visible;
- watchdog reports promised-but-not-armed separately from resumable autonomous work;
- real resume/cron arm flips state to armed with anchor;
- operator/status surfaces no longer collapse intent and execution into one boolean.

---

## 6. Honest boundaries

This slice does **not** yet fully solve the upstream chat-turn guard that prevents any model from verbally claiming autonomy before arm.
That second seam likely lives above task-manager in agent/policy/runtime orchestration.

But this slice is still worth landing first because it creates:
- durable state vocabulary,
- detectable defect surface,
- executable verification basis,
- explicit anchor model for later upstream enforcement.

That turns the problem from “implicit behavior bug” into “observable control-plane state”.
