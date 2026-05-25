# Task 415 — R1 continuation state machine fixture spec

Date: 2026-05-12
Task: #415
Status: bounded completion artifact
Scope: define one concrete fixture-spec artifact for the continuation state machine so later verification work can validate agreed transitions against explicit examples rather than implicit prose

---

## 1. Purpose

This artifact closes the narrow gap in task #415:

- create a **concrete fixture-spec artifact** for continuation state handling;
- cover the minimum agreed transitions:
  - `PREPARED -> ACK -> RUNNING -> DONE`
  - `PREPARED -> ACK -> RUNNING -> BLOCKED`
  - `PREPARED -> BLOCKED`
- provide a fresh verification basis for task #416.

This is intentionally **not** a runtime implementation or broad redesign.
It is a bounded, checkable fixture-spec layer.

---

## 2. Basis and constraint

The state vocabulary and allowed transition shape come from the existing contract artifact:

- `task-manager/artifacts/openclaw-frame-continuation-contract-v1-2026-05-12.md`

That contract already names the states and allowed paths, but it does not provide a compact machine-readable fixture pack that a verifier can consume directly.

Task #415 therefore lands the missing **R1 fixture-spec layer**, not new semantics.

---

## 3. Short verdict

## 3.1 Main result

A minimal R1 fixture pack is sufficient if each case makes four things explicit:

1. the transition sequence;
2. the event/object emitted at each step;
3. the minimum required fields for that step;
4. the terminal validity rule for the path.

## 3.2 Reframing note

Current evidence does **not** justify expanding #415 into implementation logic.
The bounded gap was the absence of an explicit fixture-spec artifact.
So #415 should be treated as **spec/fixture completion**, while task #416 can consume this artifact for executable verification.

---

## 4. Fixture pack delivered

Primary supporting fixture:

- `pkm-memory/fixtures/continuation-state-machine-task-415/fixture.json`

This fixture is designed as a verifier input, not a production schema.
It encodes:

- allowed states;
- allowed transitions;
- three canonical cases;
- minimum object/field expectations by step;
- invalid transition examples that future verification should reject.

---

## 5. Canonical state machine model

## 5.1 States

- `PREPARED`
- `ACK`
- `RUNNING`
- `DONE`
- `BLOCKED`

## 5.2 Allowed transitions in R1

Only the following transitions are in scope for this fixture spec:

- `PREPARED -> ACK`
- `ACK -> RUNNING`
- `RUNNING -> DONE`
- `RUNNING -> BLOCKED`
- `PREPARED -> BLOCKED`

## 5.3 Explicitly out of scope in R1

The fixture spec does **not** define or bless:

- `DONE -> *`
- `BLOCKED -> *`
- direct `PREPARED -> RUNNING`
- direct `ACK -> DONE`
- reopening a blocked attempt in-place

Per the continuation contract, later work after `BLOCKED` must be modeled as a **new continuation attempt**, not a silent continuation of the old one.

---

## 6. Required object expectations by state step

## 6.1 `PREPARED`

Expected object class:
- handoff package

Minimum fields:
- `handoff_id`
- `parent_task_id`
- `continuation_scope`
- `execution_owner_target`
- `decision_owner`
- `resume_basis`
- `expected_next_step`
- `return_target`
- `created_at`
- `created_by`

## 6.2 `ACK`

Expected object class:
- continuation unit

Minimum fields:
- `continuation_id`
- `handoff_id`
- `resume_trigger_id`
- `status = ACK`
- `execution_owner`
- `decision_owner`
- `scope`
- `resume_basis_snapshot`
- `started_at`

## 6.3 `RUNNING`

Expected object class:
- continuation unit

Minimum fields:
- same identity tuple as `ACK`
- `status = RUNNING`

R1 does not require a separate external file for `RUNNING`; it requires that verification treat `RUNNING` as a valid explicit operational state on the continuation unit.

## 6.4 `DONE`

Expected object class:
- return package

Minimum fields:
- `return_id`
- `continuation_id`
- `handoff_id`
- `status = DONE`
- `execution_owner`
- `decision_owner`
- `summary`
- `next_action`
- `returned_at`
- `durable_result_anchor`
- `result_kind`

## 6.5 `BLOCKED`

Expected object class:
- return package for terminal block

Minimum fields:
- `return_id`
- `continuation_id` when execution ownership was accepted first
- `handoff_id`
- `status = BLOCKED`
- `execution_owner`
- `decision_owner`
- `summary`
- `next_action`
- `returned_at`
- `blocked_reason`
- `owner_for_decision`
- `recovery_suggestion`

Special case for direct `PREPARED -> BLOCKED`:
- `continuation_id` may be absent;
- the blocked return must still cite the `handoff_id` and explain why execution could not validly start.

---

## 7. Required canonical cases

## 7.1 Case A — happy path completion

Transition chain:

`PREPARED -> ACK -> RUNNING -> DONE`

Meaning:
- handoff exists;
- continuation lane accepts ownership;
- bounded work runs;
- terminal result is produced with durable anchor.

Verifier expectations:
- exact state order matches the allowed chain;
- one stable `handoff_id` across all steps;
- one stable `continuation_id` from `ACK` through terminal return;
- terminal `DONE` includes `durable_result_anchor` and `result_kind`.

## 7.2 Case B — blocked after work started

Transition chain:

`PREPARED -> ACK -> RUNNING -> BLOCKED`

Meaning:
- ownership was accepted;
- work genuinely started;
- the bounded attempt closes blocked.

Verifier expectations:
- `ACK` must exist before terminal `BLOCKED` in this path;
- stable `handoff_id` and `continuation_id` across non-prepared steps;
- terminal `BLOCKED` includes `blocked_reason`, `owner_for_decision`, `recovery_suggestion`.

## 7.3 Case C — blocked before ownership acceptance

Transition chain:

`PREPARED -> BLOCKED`

Meaning:
- handoff package exists;
- the lane can immediately prove the resume basis is invalid, missing, or unauthorized;
- execution ownership is never accepted.

Verifier expectations:
- no `ACK` or `RUNNING` step is present;
- terminal `BLOCKED` still references the same `handoff_id`;
- the case explains the pre-execution invalidity basis.

---

## 8. Minimum invalid examples for future verification

The fixture spec also defines invalid examples so task #416 can verify rejection behavior.

Invalid transitions in the supporting fixture include:

- `PREPARED -> RUNNING`
- `ACK -> DONE`
- `RUNNING -> ACK`
- `DONE -> RUNNING`
- `BLOCKED -> RUNNING`

R1 intent:
- terminal states are terminal for the current attempt;
- ownership cannot be treated as accepted implicitly if the system skipped `ACK`;
- reopened work after `BLOCKED` must be represented as a new attempt, outside this R1 fixture pack.

---

## 9. Verification basis for task #416

Task #416 can now use the fixture pack as an explicit basis for a bounded verifier.

Minimum verification loop expected for #416:

1. load `pkm-memory/fixtures/continuation-state-machine-task-415/fixture.json`;
2. assert that every listed valid case uses only allowed transitions;
3. assert that required fields exist for each step type/state;
4. assert that invalid transition examples are rejected;
5. emit a bounded verification report with per-case pass/fail.

This gives #416 a concrete target and avoids inventing semantics during verification.

---

## 10. Delivered files

Created:
- `task-manager/artifacts/task-415-r1-continuation-state-machine-fixture-spec-2026-05-12.md`
- `pkm-memory/fixtures/continuation-state-machine-task-415/fixture.json`
- `pkm-memory/fixtures/continuation-state-machine-task-415/README.md`

---

## 11. Final bounded status

Task #415 is satisfied as a bounded R1 spec artifact:

- the weak tail was the missing explicit fixture-spec;
- the minimum transition set is now concretely encoded;
- the artifact intentionally stops at verification input level;
- implementation/executable validation belongs to follow-up work such as task #416.
