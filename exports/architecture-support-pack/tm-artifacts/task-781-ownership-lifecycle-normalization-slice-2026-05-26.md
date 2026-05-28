# Task #781 — ownership lifecycle normalization slice

Date: 2026-05-26
Task: #781
Status: bounded slice landed

## What landed

Extended the canonical async run record seam so ownership lifecycle semantics are now explicitly persisted for degraded recovery and terminal replay cases.

### Ownership lifecycle additions

`kinetic/runtime_models.py` / `kinetic/runtime_bridge.py` now persist an `ownership` block inside `async-run-record.v1.json` with explicit fields:
- `owner = runtime_bridge`
- `authority = canonical_async_record`
- `recovery_status` (`direct`, `degraded_recovered`, `terminal_replay`)
- `recovery_reason` (`fresh_submission`, `persisted_run_handle`, `async_run_record`, `already_terminal`, etc.)
- `terminal_replay` boolean
- `reload_source`
- `handle_version`

### Runner lifecycle normalization

`kinetic/runner.py` now distinguishes reloads against already-terminal persisted runs and marks them as:
- `lifecycle_reload.reason = already_terminal`
- `operator_action = replay_terminal_result`

This lets the canonical async record preserve the difference between:
- direct active continuity,
- degraded-but-successful recovery,
- terminal replay of an already-complete delegated run.

## Verification additions

Extended `kinetic/test_hermes_async_lifecycle_smoke.py` to prove:
1. direct terminal completion writes `ownership.recovery_status = direct`;
2. async-record-based degraded recovery writes `ownership.recovery_status = degraded_recovered` and `recovery_reason = async_run_record`;
3. runner poll against an already-terminal delegated run writes `ownership.recovery_status = terminal_replay` and `terminal_replay = true`.

## Verification

### Targeted
- `python3 kinetic/test_hermes_async_lifecycle_smoke.py`

Result: green

### Broader low-risk regression
- `python3 kinetic/test_runner_resume_admission_policy.py`

Result: green

## Closure decision

Task #781 is not yet safely terminal.

What is now complete:
- canonical async run record persistence;
- runner reload/recovery consumption of the canonical async record;
- explicit ownership lifecycle normalization for direct continuity, degraded recovery, and terminal replay.

What remains open:
- no explicit stale / `stuck_or_ambiguous` policy is machine-enforced yet;
- no lease/heartbeat-based transition to `unrecoverable` exists yet;
- lifecycle idempotence is improved for terminal replay semantics, but broader mature async transport policy from Track C remains larger than this bounded implementation seam.

## Recommended closure path

Split or continue with a narrower follow-up focused specifically on stale/unrecoverable delegated lifecycle policy if full Track C maturity is still desired. As implemented, the current Task #781 implementation seam looks closure-ready if its intended scope is limited to canonical async run record + ownership lifecycle normalization around degraded recovery and terminal replay.