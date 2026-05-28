# Task #781 — Canonical async run record lifecycle reload slice

Date: 2026-05-26
Task: #781
Status: bounded slice landed

## What landed

Advanced the runner-side lifecycle reload seam so Hermes delegated poll/cancel recovery now treats `async-run-record.v1.json` as the canonical continuity artifact when persisted `delegation.run_handle.handle_ref` is missing.

### Reload/recovery behavior

`kinetic/runner.py` now:
- reads `delegation.async_run_record_ref` when present, otherwise falls back to the conventional `working/async-run-record.v1.json` path;
- validates async record integrity against the current `task_id`, `run_id`, and `executor_id = hermes.delegate`;
- uses `active_handle_ref` from the async record as the first recovery source before transport/conventional fallbacks;
- returns structured recovery metadata including:
  - `source = async_run_record`
  - `async_run_record_ref`
  - `handle_version`
  - `ownership = canonical_async_record`

This preserves the intended authority split: task-manager remains lifecycle authority, while the OpenClaw/Kinetic runtime uses the canonical async record as the bounded execution continuity source of truth for delegated Hermes lifecycle reload.

### Verification additions

Extended `kinetic/test_hermes_async_lifecycle_smoke.py` to prove:
- degraded persisted run-state with blank `run_handle.handle_ref` reloads via the canonical async record;
- runner poll reports `lifecycle_reload.reason = async_run_record`;
- rotated handle continuity is honored when the async record points at a replacement handle and `handle_version = 2`.

## Verification

### Targeted
- `python3 kinetic/test_hermes_async_lifecycle_smoke.py`

Result: green

### Broader low-risk regression
- `python3 kinetic/test_runner_resume_admission_policy.py`

Result: green

## Closure decision

This bounded slice is complete, but Task #781 is still not terminally complete.

Reason:
- canonical async run record consumption/validation now exists on the runner lifecycle reload path;
- however the task scope still includes fuller ownership lifecycle normalization around degraded recovery and terminal replay semantics, and that broader normalization was not completed in this slice.

## Recommended next bounded slice

1. normalize terminal replay / degraded recovery semantics into explicit ownership-oriented fields/reasons in persisted delegated state;
2. extend lifecycle tests to cover terminal replay and unrecoverable canonical-record drift scenarios;
3. then re-evaluate whether the remaining Task #781 scope can close or should split into a narrower follow-up.
