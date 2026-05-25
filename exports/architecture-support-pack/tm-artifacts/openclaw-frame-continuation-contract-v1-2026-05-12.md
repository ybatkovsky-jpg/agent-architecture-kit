# OpenClaw Frame Continuation Contract v1

Date: 2026-05-12
Task: #394
Status: bounded completion artifact
Scope: contract/spec layer for restartable continuation across `main`, isolated bounded runs, and return-to-parent handling in OpenClaw Frame

---

## 1. Scope and purpose

This artifact defines the minimum continuation contract for the Frame pattern:

`handoff -> resume-trigger -> isolated continuation -> return`

Its purpose is to make bounded continuation:
- restartable without transcript archaeology;
- explicit about ownership and next decision;
- anchored in durable artifacts rather than chat residue;
- compatible with thin-`main` orchestration and task-first control.

This is **not** a broad runtime design. It is a compact contract for later implementation, validation, and verification work.

---

## 2. Contract intent

The continuation contract must answer, at every boundary:
1. what bounded unit is being continued;
2. why the continuation is justified now;
3. who owns execution;
4. who owns the next decision;
5. what artifact or state is the authoritative resume basis;
6. what terminal condition returns control to the parent surface.

The contract exists because the handoff spec alone defines terminal states well, but chained or resumed execution still needs a stronger binding between:
- the outbound handoff package;
- the event or decision that permits resume;
- the isolated continuation unit;
- the terminal return package.

---

## 3. Core continuation objects

### 3.1 Handoff package
The parent-authored contract that delegates a bounded slice into another execution lane.

### 3.2 Resume trigger
The explicit event, decision, or artifact state that authorizes a continuation attempt to start.

### 3.3 Continuation unit
The isolated bounded run spawned from a handoff package plus a valid resume basis.

### 3.4 Return package
The terminal package emitted by the continuation unit to return control as `DONE` or `BLOCKED`.

---

## 4. States and transitions

## 4.1 Contract states

The continuation plane uses five operational states:
- `PREPARED` — handoff package exists but execution has not yet accepted it;
- `ACK` — execution ownership has been accepted by the continuation lane;
- `RUNNING` — isolated continuation is actively consuming its bounded scope;
- `DONE` — bounded continuation responsibility is complete and has a durable result anchor;
- `BLOCKED` — bounded continuation cannot proceed within authority, information, or budget.

`RUNNING` is an operational state, not necessarily a separately surfaced public artifact. The canonical externally meaningful transitions remain centered on `ACK`, `DONE`, and `BLOCKED`.

## 4.2 Allowed transitions

Canonical transition path:

`PREPARED -> ACK -> RUNNING -> DONE`

Blocked path:

`PREPARED -> ACK -> RUNNING -> BLOCKED`

Direct blocked-before-execution path is allowed only when the continuation lane can immediately prove the resume basis is invalid or missing:

`PREPARED -> BLOCKED`

### Transition rules
- A continuation unit must not emit `DONE` without first having a valid handoff package and resume basis.
- A continuation unit must not silently skip `ACK` when it has actually taken execution ownership.
- A `BLOCKED` return closes the current bounded attempt; later work must start as a new continuation attempt, not as an untracked reopening.
- A follow-up continuation should reference the previous return package as part of its resume basis.

---

## 5. Minimum schema

The contract may later be encoded as markdown-with-frontmatter, YAML, or JSON, but the minimum semantic fields should remain stable.

## 5.1 Handoff package fields

Required:
- `handoff_id` — unique id for the delegated continuation package;
- `parent_task_id` — task lifecycle anchor;
- `parent_run_id` — parent run/session if available;
- `continuation_scope` — bounded slice being delegated;
- `execution_owner_target` — intended lane or worker;
- `decision_owner` — owner of the next non-local decision;
- `resume_basis` — authoritative basis for why this unit may start or restart;
- `expected_next_step` — single bounded action expected first;
- `return_target` — where terminal return should land;
- `created_at`;
- `created_by`.

Recommended:
- `attempt_index`;
- `parent_handoff_id`;
- `artifact_inputs`;
- `constraints`;
- `budget_class`;
- `notes_for_operator`.

## 5.2 Resume trigger fields

Required:
- `resume_trigger_id`;
- `handoff_id`;
- `trigger_type` — e.g. `decision-recorded`, `artifact-ready`, `prerequisite-met`, `manual-resume`;
- `trigger_summary`;
- `basis_anchor` — the concrete artifact, note, or state proving resume is allowed;
- `authorized_by`;
- `triggered_at`.

Recommended:
- `supersedes_trigger_id`;
- `valid_until`;
- `comments`.

## 5.3 Continuation unit fields

Required:
- `continuation_id`;
- `handoff_id`;
- `resume_trigger_id`;
- `status` — `ACK`, `RUNNING`, `DONE`, or `BLOCKED`;
- `execution_owner`;
- `decision_owner`;
- `scope`;
- `resume_basis_snapshot` — concise restatement of the actual basis consumed;
- `started_at`.

Recommended:
- `attempt_index`;
- `input_anchors`;
- `working_notes_anchor`;
- `budget_consumed`.

## 5.4 Return package fields

Required for all terminal returns:
- `return_id`;
- `continuation_id`;
- `handoff_id`;
- `status` — `DONE` or `BLOCKED`;
- `execution_owner`;
- `decision_owner`;
- `summary`;
- `next_action`;
- `returned_at`.

Required for `DONE`:
- `durable_result_anchor`;
- `result_kind`.

Required for `BLOCKED`:
- `blocked_reason`;
- `owner_for_decision`;
- `recovery_suggestion`.

Recommended:
- `evidence_anchors`;
- `followup_handoff_needed`;
- `task_state_reflection_hint`.

---

## 6. Owner semantics

## 6.1 Owner roles

The contract distinguishes four owner semantics:

- `execution owner` — the lane currently performing the bounded work;
- `decision owner` — the lane or human who must decide when local authority is insufficient;
- `persistence owner` — the surface responsible for ensuring canonical state is durably reflected;
- `task owner` — the task lifecycle controller that decides what becomes active next.

In many cases these collapse, but the contract should not assume they are always the same.

## 6.2 Default semantics by phase

### During handoff preparation
- execution owner: still parent / none yet accepted;
- decision owner: usually `main` or human;
- persistence owner: parent lane creating the package;
- task owner: task control plane.

### After `ACK`
- execution owner: continuation lane;
- decision owner: as named in handoff, unless later escalated;
- persistence owner: continuation lane for its own terminal package;
- task owner: unchanged until return is reflected.

### After `DONE`
- execution owner: closed for this bounded unit;
- decision owner: returns to parent unless explicitly forwarded;
- persistence owner: parent must reflect terminal state into task truth;
- task owner: parent/task control plane.

### After `BLOCKED`
- execution owner: closed for this bounded attempt;
- decision owner: transfers to `owner_for_decision`;
- persistence owner: blocked package plus task note/state reflection;
- task owner: parent/task control plane after escalation.

---

## 7. ACK / DONE / BLOCKED handling

## 7.1 ACK

`ACK` means:
- the continuation lane has accepted execution ownership;
- the handoff package and resume basis were sufficiently understood to begin;
- the work is no longer in ambiguous limbo.

Rules:
- emit early after acceptance;
- include the consumed `handoff_id`;
- if the resume basis is obviously invalid, do not fake `ACK`; return `BLOCKED` immediately.

## 7.2 DONE

`DONE` means:
- the continuation finished its bounded slice;
- the completion is evidenced outside chat;
- the next action is known.

Rules:
- requires a `durable_result_anchor`;
- may complete only the bounded slice, not the whole parent task;
- should identify whether the parent now needs review, follow-up execution, or task closure.

## 7.3 BLOCKED

`BLOCKED` means:
- further local continuation is no longer justified under current budget, authority, or information;
- the current bounded attempt is closed correctly;
- the next decision owner is explicit.

Rules:
- must name an operational blocker, not a vague failure feeling;
- must identify `owner_for_decision`;
- should give a concrete recovery suggestion;
- does not permit silent background retry under the same attempt.

---

## 8. Resume basis rules

The resume basis is the most important continuation-specific field.

## 8.1 Definition

`resume_basis` is the smallest authoritative set of facts and anchors that justifies starting the continuation now.

It should be based on durable state such as:
- a parent handoff package;
- a task note recording a human decision;
- a produced artifact;
- a verification result;
- a prior blocked package that has now been resolved.

## 8.2 Rules

1. **No transcript-only basis by default**
   - Raw prior chat may help explain context but should not be the sole canonical resume basis.

2. **Basis must be anchorable**
   - Every resume basis should point to at least one durable artifact, note, or state reference.

3. **Basis must be bounded**
   - It should identify the specific prerequisite that became true, not re-describe the entire history.

4. **Basis must explain why now**
   - A good basis states what changed between the prior stop and the new continuation attempt.

5. **Basis must be snapshotable**
   - The continuation unit should restate the basis it actually consumed so later recovery does not depend on mutable interpretation.

## 8.3 Acceptable basis examples

- “Human approved option B in task note X; continue by drafting v1 spec artifact.”
- “Artifact Y now exists and passes validation; proceed to promotion-gate evaluation.”
- “Previous attempt blocked on missing mapping matrix; matrix artifact now anchored at path Z.”

---

## 9. Durable result anchor rules

## 9.1 General rule

A continuation return is complete only when its result is anchored outside pure conversational residue.

## 9.2 Allowed anchors

Typical valid anchors include:
- artifact file paths under the workspace;
- code diffs or changed files under versioned repos;
- structured task notes;
- verification output files;
- explicit durable result packages.

## 9.3 Anchor quality rules

A good result anchor is:
- stable enough to be re-read later;
- narrow enough to identify the bounded result;
- linked back to the `handoff_id` or task id;
- sufficient for parent review without re-running the entire flow.

## 9.4 Projection rule

A chat summary may accompany the anchor but never replace it.

---

## 10. Blocked and recovery path

## 10.1 Blocked package requirements

A blocked return should capture:
- what was attempted;
- where execution stopped;
- why local continuation is no longer justified;
- who must decide or provide the missing prerequisite;
- what concrete recovery action would reopen work.

## 10.2 Recovery path

Canonical recovery sequence:
1. parent receives `BLOCKED`;
2. task truth is updated to reflect the blocker and decision owner;
3. missing decision/prerequisite is resolved and anchored durably;
4. a new resume trigger is created;
5. a new continuation attempt is spawned with explicit linkage to the prior blocked return.

## 10.3 Anti-patterns

Avoid:
- leaving a blocked unit silently open;
- retrying indefinitely without new basis;
- treating “try again later” as sufficient recovery detail;
- reopening the same attempt without a fresh trigger.

---

## 11. Relation to main, isolated runs, task truth, and evidence truth

## 11.1 Main

`main` is the orchestration and decision-framing surface.
It should:
- create or approve handoff packages;
- receive terminal returns;
- reflect outcomes into task truth;
- avoid becoming the hidden storage layer for continuation state.

## 11.2 Isolated runs

The continuation contract exists primarily for isolated bounded runs.
Their job is not to preserve ambient conversation, but to:
- consume a bounded basis;
- execute a bounded slice;
- return a terminal package with anchors.

## 11.3 Task truth

Task lifecycle state remains the top operational truth for:
- whether work is active, blocked, or closed;
- who owns the next step;
- what follow-up unit should exist next.

The continuation contract does not replace task truth; it binds runtime continuity into it.

## 11.4 Evidence truth

Evidence truth answers:
- what was actually produced;
- what proves completion or blockage;
- where the durable output lives.

Continuation packages should reference evidence truth rather than duplicating it in prose.

## 11.5 Memory truth

Memory is for distilled reusable lessons, not for raw continuation state.
A continuation result may later be distilled, but the continuation contract itself belongs to task/evidence continuity first.

---

## 12. Bounded examples

## 12.1 Example A — normal completion

```yaml
handoff:
  handoff_id: h-394-01
  parent_task_id: 394
  continuation_scope: define OpenClaw Frame continuation contract v1
  execution_owner_target: subagent:ziribt-394
  decision_owner: main
  resume_basis: mapping matrix exists and handoff/routing artifacts are available
  expected_next_step: draft compact contract artifact
  return_target: parent task #394 note and parent session summary

resume_trigger:
  resume_trigger_id: rt-394-01
  handoff_id: h-394-01
  trigger_type: prerequisite-met
  basis_anchor: task-manager/artifacts/task-393-openclaw-frame-implementation-mapping-matrix-2026-05-12.md
  authorized_by: main

return:
  return_id: ret-394-01
  continuation_id: c-394-01
  handoff_id: h-394-01
  status: DONE
  execution_owner: subagent:ziribt-394
  decision_owner: main
  summary: continuation contract v1 artifact created and task note added
  durable_result_anchor: task-manager/artifacts/openclaw-frame-continuation-contract-v1-2026-05-12.md
  result_kind: architecture-spec
  next_action: review for implementation and validation follow-up
```

## 12.2 Example B — blocked pending human decision

```yaml
return:
  return_id: ret-401-02
  continuation_id: c-401-02
  handoff_id: h-401-02
  status: BLOCKED
  execution_owner: subagent:policy-check
  decision_owner: main
  summary: promotion assessment completed but publication route is ambiguous
  blocked_reason: artifact appears reusable but repo-fit policy needs human confirmation
  owner_for_decision: human:operator
  recovery_suggestion: record target repo decision in task note and issue a new resume trigger
  next_action: wait for explicit repo-fit decision, then spawn new bounded promotion step
```

## 12.3 Example C — blocked before ACK-equivalent execution

A handoff references a missing artifact path as the sole resume basis. The continuation lane can immediately verify that the basis anchor does not exist. It may return `BLOCKED` without entering normal execution, because the prerequisite failed at contract intake.

---

## 13. Open questions

1. **Encoding format** — Should the canonical artifact be markdown-with-frontmatter, pure YAML/JSON, or dual-surface markdown plus machine-readable payload?
2. **Id scheme** — Should `handoff_id`, `resume_trigger_id`, and `continuation_id` be task-scoped, globally unique, or runtime-issued?
3. **Task manager linkage** — Which exact task-manager fields should canonically store parent/child continuation linkage and terminal reflection?
4. **ACK persistence** — Does `ACK` require a durable artifact every time, or may it remain a lightweight structured event if `DONE/BLOCKED` are durably anchored?
5. **Continuation chaining depth** — Should policy constrain how many continuation hops may occur before mandatory parent review?
6. **Auto-validation** — Which contract fields should later be machine-validated before allowing a continuation to start?

---

## 14. Why this is a good bounded completion

This artifact is a good bounded completion for #394 because it:
- stays at the contract/spec layer rather than drifting into runtime redesign;
- turns the Frame continuation idea into an explicit state and schema contract;
- binds handoff, resume trigger, isolated continuation, and return into one restartable path;
- cleanly separates task truth, evidence truth, and operator projection;
- is compact enough to drive later implementation and verification tasks.

This artifact also appears **public-safe and reusable enough for later promotion** into `product-repos/agent-architecture-kit` after light generalization and format cleanup.
