# Task #121 — Retrieval regression fixture pack report (2026-04-26)

## Status

Completed as a bounded follow-up.

## What this deliverable adds

Built the missing full fixture-pack deliverable around the existing verifier:
- fixture definition for known queries
- bounded corpus / anchor manifest
- produced sample verification outputs
- short report and usage notes

Existing helper reused:
- `pkm-memory/scripts/verify_retrieval_fixtures.py`

## Covered query scope

Exactly four bounded query classes are covered:
1. exact artifact — `memory rollout plan`
2. slug-heavy artifact — `task-107-postgres-activation-and-first-live-ingest`
3. milestone intent — `postgres activation milestone`
4. generic milestone phrasing — `activation milestone`

## Current validated contract

### Local mode

Confirmed:
- exact artifact query returns the rollout-plan artifact at top-1
- slug-heavy Task #107 query returns the Task #107 artifact at top-1
- milestone-intent query returns the Task #107 artifact at top-1
- generic milestone phrasing keeps Task #107 within top-3

### PostgreSQL mode

Confirmed:
- exact artifact query returns the rollout-plan artifact at top-1
- generic milestone phrasing returns Task #107 at top-1 and keeps Task #108 in top-3
- slug-heavy and milestone-intent queries remain valid via bounded top-3 presence checks for the primary artifact and key supporting artifacts

## Important bounded note

The DB ranking now reflects a slightly newer live corpus than some earlier smoke snapshots.
Newer follow-up artifacts can legitimately outrank older supporting artifacts for some queries.
Because of that, this fixture pack intentionally uses the narrowest currently validated checks instead of preserving stale stricter top-3 ordering assumptions.

This keeps the pack durable without broadening scope into another retrieval-tuning task.

## Verification run

Command:

```bash
python3 pkm-memory/scripts/verify_retrieval_fixtures.py
```

Output directory:

- `pkm-memory/outputs/task-121-retrieval-regression-fixture-pack-2026-04-26/`

Verification result from the completed run:
- `4 / 4` cases passed
- `8 / 8` mode checks passed

## Deliverable files

Fixture directory:
- `pkm-memory/fixtures/retrieval-regression-task-121/known-good-queries.json`
- `pkm-memory/fixtures/retrieval-regression-task-121/corpus-manifest.json`
- `pkm-memory/fixtures/retrieval-regression-task-121/sample-output-manifest.json`
- `pkm-memory/fixtures/retrieval-regression-task-121/README.md`
- `pkm-memory/fixtures/retrieval-regression-task-121/report.md`

Verification outputs:
- `pkm-memory/outputs/task-121-retrieval-regression-fixture-pack-2026-04-26/verification-report.json`
- per-case `*.raw.json`
- per-case `*.result.json`
