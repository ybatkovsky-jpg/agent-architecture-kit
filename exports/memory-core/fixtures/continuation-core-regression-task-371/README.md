# Task #371 continuation-core regression pack

Focused regression pack for continuation retrieval invariants after splitting the old mixed `task-371` contour.

## What it covers

- explicit task-id resume
- predecessor-chain reopen
- natural-language continue-after-X
- latest-handoff ambiguous resume
- ambiguous continuation phrasing without task-id as an explicit boundary case

## What it checks

- continuation request-class lane
- anchored handoff winner selection
- top authority layer for continuation answers
- bounded duplicate/path hygiene in top-N
- one explicitly documented boundary/known-limitation case

This pack is intentionally narrow.
It does **not** cover meta/evaluation routing, architecture/design recall, or artifact/source-trace behavior.

## Run

```bash
python3 pkm-memory/scripts/verify_continuation_core_regression_task_371.py
```

## Outputs

- `pkm-memory/outputs/task-371-continuation-core-regression-2026-05-12/verification-report.json`
- per-case raw command logs
- per-case retrieval result JSONs

## Related files

- `pkm-memory/CONTINUATION_RETRIEVAL_CONTRACT_V1.md`
- `pkm-memory/RETRIEVAL_LANE_CONTRACTS_V1.md`
- `pkm-memory/RETRIEVAL_POLICY_MATRIX_V1.md`
