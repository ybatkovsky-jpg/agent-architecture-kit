# Task #781 — Canonical async run record bounded slice

Date: 2026-05-26
Task: #781
Status: bounded slice landed

## What landed

Implemented the first bounded Track C persistence seam for a **canonical async run record** on Hermes delegated execution paths.

### Schema
A new runtime model `AsyncRunRecord` now persists at:

- `runtime/tasks/<task_id>/runs/<run_id>/working/async-run-record.v1.json`

Current fields include:
- `record_version`
- `task_id`
- `run_id`
- `executor_id`
- `delegation_id`
- `hermes_run_id`
- `transport_id`
- `transport_mode`
- `active_handle_ref`
- `handle_version`
- `lifecycle_phase`
- `lifecycle_status`
- `submitted_at`
- `last_observed_at`
- `cancel_requested`
- `cancelled_at`
- `poll_count`
- `provenance`
- `transport`
- `lifecycle_reload`
- `integrity`
- `created_at`
- `updated_at`

### Wiring
`RuntimeBridge.finalize_from_result(...)` now:
1. persists normal `run-state-lite.json` updates;
2. derives the canonical async run record from delegated adapter metadata;
3. writes `async-run-record.v1.json` for delegated runs with async lifecycle metadata;
4. stores `delegation.async_run_record_ref` back into `run-state-lite.json`.

### Covered lifecycle states in this bounded slice
The first wired path covers Hermes delegated results for:
- `submitted_async` -> `submitted`
- `polling` -> `running`
- `cancel_requested` -> `cancel_requested`
- `cancelled` -> `cancelled`
- `completed_slice` -> `completed_success`
- `failed_terminal` -> `completed_failed`

### Provenance behavior
The record preserves bounded provenance signals already present in Track B:
- direct handle vs transport-handle fallback presence;
- lifecycle reload outcome/reason when available;
- handle version continuity across rewrites.

## Verification

### Targeted
- `python3 kinetic/test_hermes_async_lifecycle_smoke.py`

Result: green

### Broader low-risk regression
- `python3 kinetic/test_runner_resume_admission_policy.py`

Result: green

## Closure decision

This bounded slice is **complete**, but Task #781 as a whole is **not yet terminally complete**.

Reason:
- the canonical async run record schema now exists and is persisted/updated for the first delegated-execution seam;
- but the broader Task #781 title also includes **ownership lifecycle**, and the current code does not yet fully normalize ownership/state-authority rules beyond this first persistence seam.

## Recommended next bounded slice

1. make runner lifecycle reload/recovery explicitly consume and validate `async-run-record.v1.json` as the canonical continuity artifact, not just `delegation.run_handle` + transport refs;
2. normalize ownership fields/reasons for degraded recovery, terminal replay, and unrecoverable states;
3. extend verification for direct-vs-recovered provenance and handle replacement/version bumps.
