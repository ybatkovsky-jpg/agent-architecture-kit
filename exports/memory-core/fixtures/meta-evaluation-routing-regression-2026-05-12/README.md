# Meta/evaluation routing regression pack

Focused regression pack for explicit meta/evaluation retrieval behavior.

## What it covers

- explicit meta/evaluation query
- evaluation summary / release recommendation query
- hardening-slice explicit meta query

## What it checks

- `meta_evaluation_recall` classification
- evidence-first top-result basis for explicit meta intent
- absence of continuation-specific suppression/demotion leakage into meta answers

This pack is separate from continuation-core regression on purpose.

## Run

```bash
python3 pkm-memory/scripts/verify_meta_evaluation_routing_regression.py
```
