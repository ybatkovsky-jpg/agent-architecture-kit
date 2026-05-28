# Task #771 — Adaptive autonomy modes: explicit execution-mode model and transition policy

Date: 2026-05-26
Task: #771
Parent: #768
Status: specification draft

## 1. Purpose

The current autonomy contour is honest and fail-closed, but it is still mostly a guardrail system.
It decides what is forbidden, what may surface, and when closure cannot be claimed.
That is necessary, but not yet sufficient for a mode-aware operator-grade autonomy model.

This task defines an explicit **execution-mode model** so that autonomy is not treated as one flat state.
The goal is to make runtime posture, transition triggers, and operator implications explicit.

---

## 2. Core design rule

**Autonomy mode is a runtime posture contract, not a cosmetic label.**

A mode must change at least one of:
- what the system is trying to optimize;
- what evidence threshold is required;
- what surfacing policy applies;
- what watchdog / resume behavior applies;
- what closure claims are allowed.

If a so-called mode does not affect execution semantics, it is not a real mode.

---

## 3. Canonical mode set

The minimum explicit mode model should include:

1. `normal_execution`
2. `research_uncertain`
3. `blocked_external`
4. `approval_needed`
5. `degraded_manual`
6. `delegated_long_run`
7. `closure_validation`

These modes do not replace task status.
They refine how an in-progress or autonomy-enabled task should be interpreted and governed.

---

## 4. Mode definitions

### A. `normal_execution`
Default mode for bounded executable work.

### B. `research_uncertain`
Use when the system is gathering information, validating ambiguity, or reducing uncertainty before execution can be trusted.

### C. `blocked_external`
Use when forward progress depends on an external dependency rather than missing internal initiative.

### D. `approval_needed`
Use when the next safe action requires explicit human approval or policy authorization.

### E. `degraded_manual`
Use when autonomy or delegation contour is degraded enough that honest autonomous continuation is no longer supported.

### F. `delegated_long_run`
Use when bounded local execution has intentionally handed off to a longer-lived delegated run.

### G. `closure_validation`
Use when implementation appears complete but final proof, replay, or closure checks are still pending.

---

## 5. Transition trigger policy

Mode transitions should be driven by explicit triggers rather than intuition.

### Into `normal_execution`
Allowed when frontier is known, no dominating blocker exists, and the execution lane is honest and armed if autonomy is claimed.

### Into `research_uncertain`
Trigger when the next action depends on missing knowledge, multiple viable explanations remain open, or evidence is insufficient for a safe implementation choice.

### Into `blocked_external`
Trigger when progress depends on an external actor/system and internal execution cannot resolve it alone.

### Into `approval_needed`
Trigger when the next safe step crosses a permission, deployment, policy, spend, or irreversible-change boundary.

### Into `degraded_manual`
Trigger when autonomy launch was requested but never honestly armed, delegated recovery becomes unrecoverable, risk posture forbids continuation, or execution provenance is too ambiguous to continue safely.

### Into `delegated_long_run`
Trigger when delegated execution is intentionally submitted and authoritative continuity lives in delegated run-state.

### Into `closure_validation`
Trigger when implementation frontier appears exhausted and remaining work is proof, replay, review, or acceptance.

---

## 6. Transition constraints

1. **No silent downgrade** — the system must not silently move from autonomy-claimed posture into effectively manual behavior without an explicit degraded/manual reason.
2. **Mode does not override delivery-gate honesty** — terminal surfacing still requires the existing delivery-gate contract.
3. **Status and mode are orthogonal** — examples: `in_progress + normal_execution`, `waiting_user + approval_needed`, `review + closure_validation`.
4. **Stronger blockers dominate weaker active modes** — `approval_needed` dominates research; `degraded_manual` dominates normal execution.

---

## 7. Operator surfacing implications per mode

- `normal_execution`: keep internal unless terminal route exists.
- `research_uncertain`: keep internal while bounded/productive; surface only if uncertainty becomes terminally relevant.
- `blocked_external`: eligible for explicit blocked surfacing with actionable reason.
- `approval_needed`: eligible for surface when the approval boundary is proven.
- `degraded_manual`: must surface when autonomy/delegation honesty would otherwise be misrepresented.
- `delegated_long_run`: surface only significant lifecycle events.
- `closure_validation`: do not emit `done` early; surface only on final terminal decision.

---

## 8. Closure implications per mode

- `normal_execution`: closure forbidden while frontier remains.
- `research_uncertain`: closure forbidden unless task acceptance is research-bounded and evidence is complete.
- `blocked_external`: may route terminally as blocked-external, but not as done.
- `approval_needed`: may route terminally as approval-needed, but not as done.
- `degraded_manual`: may route terminally as degraded/risk/launch-failed class, but not as successful closure.
- `delegated_long_run`: closure depends on delegated lifecycle outcome plus proof reconciliation.
- `closure_validation`: should bias toward final proof checks rather than more implementation churn.

---

## 9. Minimum implementation-first seam

**Add an explicit normalized `execution_mode` field plus transition helper/policy layer in autonomy state projection and routing logic.**

That seam should:
1. persist a canonical execution mode separate from boolean autonomy;
2. derive/normalize mode from continuation + watchdog + launch-gate signals;
3. expose mode on `autonomy-show` / `autonomy-status`;
4. enforce dominance rules for `approval_needed`, `blocked_external`, `degraded_manual`, and `delegated_long_run`;
5. stay projection-first before deeper behavioral rewrites.

---

## 10. Acceptance shape

This task counts as complete when:
- a canonical mode model exists;
- triggers and transitions are defined;
- surfacing and closure implications per mode are explicit;
- a first low-risk implementation seam is identified.

---

## 11. Concise verdict

Adaptive autonomy should evolve from one flat guarded posture into an explicit mode system where execution semantics, transition triggers, operator surfacing, and closure implications differ by runtime posture. The lowest-risk first step is to project and normalize a canonical execution-mode field before deeper behavioral automation changes.
