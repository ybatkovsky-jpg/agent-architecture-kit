# Task #371 continuation retrieval regression pack

Bounded regression pack for continuation retrieval stabilization after the continuation freshness / meta-alignment slices.

## What it covers

- explicit task-id resume
- predecessor-chain reopen
- natural-language continue-after-X
- ambiguous continuation phrasing without task-id
- explicit meta/evaluation query
- latest-handoff ambiguous resume
- factual/trace query with explicit task-id artifact target
- architecture/design natural-language recall
- explicit evaluation-summary meta recall
- explicit hardening-slice meta recall

## What it checks

Checks stay intentionally narrow:
- request-class lane (`resume_reopen_continuation`, `architecture_design_recall`, `meta_evaluation_recall`, `artifact_source_trace_request`, `factual_lookup` where expected)
- top-result basis for anchored continuation cases
- top authority layer
- continuation vs factual / trace boundary
- meta vs architecture boundary
- evaluation-summary vs hardening-slice boundary
- bounded candidate-pool guardrail for the intentionally ambiguous case

This is not a full retrieval-quality benchmark.
It is a stability pack for the continuation-vs-meta contract, including the extracted first-class `meta_evaluation_recall` lane.

## Run

```bash
python3 pkm-memory/scripts/verify_continuation_regression_task_371.py
```

## Outputs

- `pkm-memory/outputs/task-371-continuation-regression-2026-05-07/verification-report.json`
- per-case raw command logs
- per-case retrieval result JSONs

## Related files

- `pkm-memory/RETRIEVAL_LANE_CONTRACTS_V1.md`
- `pkm-memory/CONTINUATION_RETRIEVAL_CONTRACT_V1.md`
- `pkm-memory/RETRIEVAL_POLICY_MATRIX_V1.md`
- `task-manager/artifacts/task-370-memory-core-v1-continuation-meta-alignment-hardening-slice-2026-05-07.md`
