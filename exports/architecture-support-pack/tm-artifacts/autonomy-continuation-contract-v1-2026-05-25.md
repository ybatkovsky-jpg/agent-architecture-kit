# Autonomy Continuation Contract v1

Date: 2026-05-25
Status: first-pass enforceable contour
Purpose: prevent autonomous execution from stopping on explanation/status reasoning when a safe local bounded next step is available.

---

## 1. Core rule

If all of the following are true:
- the task is `in_progress`;
- a bounded next step is known;
- the next step is executable in the current workspace/runtime;
- no user decision is required;
- no new external access/resource is required;
- no irreversible-harm risk is present;

then the agent must **execute the next bounded step**.

It must not stop at explanation, analysis, or blocker-language alone.

---

## 2. Allowed blocker classes

A task may pause instead of executing only if at least one of these is true:

1. **blocked_user_decision**
   - a real product/scope choice is required from the user.

2. **blocked_external_access**
   - required credentials, host access, device access, or external service capability is missing.

3. **blocked_missing_runtime**
   - required tool/runtime/resource is unavailable in the current environment.

4. **blocked_irreversible_harm_risk**
   - the next step could cause irreversible or unsafe damage without explicit confirmation.

5. **blocked_requirement_conflict**
   - two active requirements conflict and the agent is not authorized to choose locally.

Everything else is treated as executable work, not a blocker.

---

## 3. Explicit non-blockers

The following are **not** valid blockers if a bounded local first pass is possible:
- choosing a first-pass threshold;
- narrowing scope to a high-risk subset;
- deciding an enforcement seam;
- planning a regression;
- refining wording of a gate/policy;
- preferring an ideal general solution over a narrower enforceable one;
- restating the same next steps without executing them.

---

## 4. First-pass obligation

If a universal or perfect solution is not yet clear, the agent must prefer a narrower solution that is:
- honest;
- bounded;
- enforceable;
- reversible or safely extensible.

Priority order:
1. narrow high-risk scope;
2. implement mechanical enforcement for that scope;
3. add targeted regression proof;
4. surface the result honestly;
5. widen later only if needed.

---

## 5. Execution-delta requirement

An autonomous progress update is weak unless at least one of the following occurred since the previous meaningful step:
- file edit/write;
- executable command/test run;
- durable artifact creation;
- task transition or task note with new evidence;
- explicit blocker capture with a valid blocker class.

Explanation without execution delta is not considered satisfactory autonomous progress.

---

## 6. Anti-freeze rule

If the agent can already enumerate concrete local next steps, stopping is invalid.

Example invalid pattern:
1. define scope;
2. define threshold;
3. implement enforcement;
4. add regression;

If these steps are locally executable, the correct behavior is to start step 1 immediately, not to stop and describe the plan.

---

## 7. Escalation rule

If the same next step or same blocker framing is repeated across multiple cycles without execution delta, the system should treat it as a failure mode such as:
- `explanation_without_execution_delta`
- `local_step_deferred_without_blocker`
- `repeated_next_step_without_execution`

This should trigger forced continuation or explicit blocked-state surfacing.

---

## 8. Honest surfacing rule

When work is still ongoing, the agent should surface:
- what changed;
- what remains;
- why the task is not yet closed;
- what next bounded step is being executed now.

It should not surface a pseudo-update that only repeats analysis already known.

---

## 9. Minimal machine-enforcement shape

A future implementation contour should enforce at least:
- local executable next-step known + no valid blocker => continuation required;
- repeated explanation without execution delta => explicit failure class;
- first-pass narrow enforcement preferred over indefinite design delay;
- blocker claims restricted to the allowed blocker classes.

---

## 10. Relationship to current production-readiness stream

This contract is directly relevant to:
- `#759` fresh executable verification gate hardening;
- `#764` production-readiness closure program;
- `#765` production E2E acceptance proof;
- `#766` operating contour / degraded-mode honesty;
- the broader silent-stop / pseudo-progress defect family seen in autonomy hardening work.

It is intentionally small and should be treated as a first-pass enforcement target, not a complete autonomy philosophy.
