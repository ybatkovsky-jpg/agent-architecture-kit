# Task #121 retrieval regression fixture pack

## Purpose

Bounded durable fixture pack for known retrieval queries in the memory rollout work.

This pack covers exactly four query shapes:
- exact artifact query
- slug-heavy artifact query
- milestone-intent query
- generic milestone phrasing query

It is built around the existing verifier:
- `pkm-memory/scripts/verify_retrieval_fixtures.py`

## Files

- `known-good-queries.json` — fixture definition with current validated expectations
- `corpus-manifest.json` — bounded corpus/anchor set referenced by this pack
- `sample-output-manifest.json` — pointers to verification outputs produced from the fixture
- `report.md` — short human report for Task #121

## Verification command

From workspace root:

```bash
python3 pkm-memory/scripts/verify_retrieval_fixtures.py
```

Outputs are written to:

- `pkm-memory/outputs/task-121-retrieval-regression-fixture-pack-2026-04-26/`

## Contract notes

- Expectations are intentionally narrow and tied to what is currently validated.
- Where ranking remains stable and precise, the pack asserts `top1_path`.
- Where the corpus now contains newer follow-up artifacts that legitimately compete, the pack asserts bounded `top3_contains` checks instead of stale stricter ranking claims.
- Paths are matched exactly as emitted by `retrieve_memory.py`.
