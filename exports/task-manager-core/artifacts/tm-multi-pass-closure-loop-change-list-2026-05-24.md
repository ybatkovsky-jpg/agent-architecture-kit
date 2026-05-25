# Task #754 — TM multi-pass closure-loop change-list

Date: 2026-05-24
Lineage: follow-up split from task #753 (`Autonomy guardrail: prevent promised-but-not-armed autonomous execution`)
Purpose: define the task-manager/runtime change-list that upgrades autonomous execution from one-shot best-effort into a bounded multi-pass closure loop that keeps generating explicit next slices until the task reaches a terminal state.

## 1. Why this is a separate task

Task #753 closed the first concrete guardrail gap:
- durable distinction between `autonomy_requested` and `autonomy_armed`
- execution-anchor visibility
- promised-but-not-armed watchdog/operator visibility

What #753 did **not** fully solve is the next-layer orchestration problem:
- a bounded autonomous run may still do useful work and then stop before closure,
- while the task remains non-terminal,
- and no explicit next bounded slice is created automatically.

That is a distinct TM/orchestration change and should be tracked separately rather than keeping #753 open forever.

---

## 2. Outcome target

Make autonomous task execution behave like a multi-pass state machine:
1. run one bounded slice,
2. decide whether the task is terminal,
3. if not terminal, generate the next explicit bounded slice,
4. repeat until `review`, `done`, `waiting_user`, or `blocked_external`.

The point is not “run forever”.
The point is: **no useful autonomous progress may end without a closure decision**.

---

## 3. Required state model additions

### A. `task-manager/autonomy_state.py`

Add a `closure_loop` block:

```json
"closure_loop": {
  "execution_stage": "idle",
  "slice_goal": "",
  "slice_done": false,
  "closure_required": false,
  "followup_split_needed": false,
  "next_slice_required": false,
  "next_slice_reason": "",
  "next_slice_scope": "",
  "last_terminality_check": "",
  "last_terminality_result": "unknown"
}
```

### Allowed `execution_stage` values
- `idle`
- `scoping`
- `implementing`
- `verifying`
- `closing`
- `blocked`
- `terminal`

### Normalization requirements
- if a task is autonomous and non-terminal, `closure_required=true`
- if a bounded slice finishes with useful progress but non-terminal state, `next_slice_required=true`
- `execution_stage=terminal` only when the task is truly in terminal delivery state

Add helper predicates:
- `closure_loop_pending(state)`
- `terminality_decision_required(state)`
- `next_slice_missing(state)`

---

## 4. Router extensions

### B. `task-manager/autonomy_router.py`

Extend router outputs beyond:
- `continue_now`
- `resume_later`
- `surface_to_user`
- `escalate_internal`

Add explicit closure-loop decisions:
- `schedule_next_slice`
- `split_followup_task`
- `run_closure_pass`

### Decision intent

#### `schedule_next_slice`
Use when:
- useful bounded work completed,
- task is not terminal,
- next narrow step is known.

#### `split_followup_task`
Use when:
- the remaining work is real,
- but it is separable from the current task’s acceptance closure,
- and should not keep the parent task open.

#### `run_closure_pass`
Use when:
- implementation and verification likely already cover acceptance,
- but a final audit/status decision is still needed.

### New defect class
If the router sees evidence of useful progress with non-terminal state but no next slice or split decision, emit internal violation:
- `progressed_but_not_closure_routed`

---

## 5. Task-manager CLI / orchestration changes

### C. `task-manager/task_manager.py`

#### New slice metadata persistence
Thread `closure_loop` state through:
- `autonomy-init`
- `autonomy-enable`
- `autonomy-route`
- `autonomy-status`
- `autonomy-show`
- `show`

#### New commands or flags
Prefer minimal extension first:
- `autonomy-route` may populate `closure_loop.*`
- `autonomy-resume` may accept or derive `--execution-stage` / `--slice-goal`

Optional later command:
- `autonomy-next-slice <task_id>`

#### Closure pass helper
Add helper function conceptually like:
- `decide_autonomous_closure(task, state, child_result, coach_summary)`

Responsibilities:
- decide terminal vs non-terminal,
- if non-terminal, require next explicit slice or split,
- if terminal, allow `review`/`done`/`waiting_user` routing.

#### Split follow-up support
When the remaining work is outside the parent acceptance slice:
- create a follow-up task,
- record lineage link in both tasks,
- allow the parent to move toward `review`/`done`.

---

## 6. Watchdog additions

### D. `task-manager/task_manager.py` watchdog path

Add a new defect/report bucket:
- `progressed_not_closure_routed`

Inclusion rule:
- autonomous task is still non-terminal,
- evidence indicates useful progress happened,
- but there is no explicit next slice and no split-follow-up decision,
- and task is not honestly blocked/waiting-user.

For each entry show:
- task id/title
- execution stage
- last useful progress anchor
- missing closure decision
- recommended next command or recovery action

This bucket is separate from:
- stale resumable work
- promised-not-armed work

---

## 7. Prompt / run contract changes

### E. Autonomous run message contract

Current bad pattern:
- “Finish task #X completely.”

Required pattern:
- “Execute the current bounded slice.”
- “If acceptance is met, move the task to review/done.”
- “If acceptance is not met, create the next explicit bounded slice.”
- “If remaining work is separable, split a follow-up task.”
- “Do not stop without a closure decision.”

This should be reflected in the message template used by autonomous resumes / cron jobs.

Target seam today:
- `DEFAULT_AUTONOMY_RESUME_MESSAGE_TEMPLATE` in `task_manager.py`

---

## 8. Tests to add

### A. New test: `test_autonomy_closure_loop.py`
Should cover:
1. implementation slice completes but task is non-terminal,
2. router produces `schedule_next_slice` or `run_closure_pass`,
3. closure-loop metadata is persisted.

### B. New test: `test_autonomy_followup_split.py`
Should cover:
1. parent acceptance is effectively closed,
2. remaining work is separable,
3. follow-up task is created and linked,
4. parent can move to `review`.

### C. Extend `test_autonomy_watchdog.py`
Add case for:
- `progressed_not_closure_routed`
- verify it is reported distinctly from resumable or promised-not-armed buckets.

### D. Extend `test_autonomy_router.py`
Add assertions for new router decisions:
- `schedule_next_slice`
- `split_followup_task`
- `run_closure_pass`

---

## 9. Suggested implementation order

1. Add `closure_loop` state block and normalization helpers
2. Extend router return contract with closure decisions
3. Persist/print closure-loop visibility in `show`/`autonomy-status`
4. Add watchdog defect bucket `progressed_not_closure_routed`
5. Update autonomy resume prompt contract
6. Add split-follow-up support
7. Add/extend tests

---

## 10. Verification plan

Minimum proof for this task after implementation:
- `python3 task-manager/test_autonomy_router.py`
- `python3 task-manager/test_autonomy_watchdog.py`
- `python3 task-manager/test_autonomy_closure_loop.py`
- `python3 task-manager/test_autonomy_followup_split.py`

Optional wider regression:
- `python3 task-manager/test_autonomy_e2e_exhaustive.py`
- `python3 task-manager/test_autonomy_state_and_gate.py`

---

## 11. Honest scope boundary

This task is about **TM/runtime closure-loop mechanics**.
It is not the same as broader product-level planning or generic agent autonomy.

It should remain bounded to:
- TM state,
- router decisions,
- watchdog/reporting,
- autonomous run contract,
- follow-up split semantics.

---

## 12. Closure relation to #753

Task #753 can close once its first-slice acceptance is met and the remaining “how do autonomous runs keep closing themselves over multiple passes?” question is explicitly carried by this new task.

That means:
- #753 = first concrete false-autonomy guardrail landed
- #754 = next orchestration layer for multi-pass closure-loop execution
