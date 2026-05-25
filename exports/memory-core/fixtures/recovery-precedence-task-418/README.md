# Task #418 canonical recovery precedence test pack

Bounded executable/checkable pack for recovery-order precedence.

## Covered precedence rules

- task truth over projection
- continuation truth over transcript residue
- evidence truth over summary claims
- memory truth as reusable layer, not execution proof

## Shape

This pack is intentionally narrow.
It does **not** benchmark full retrieval quality.
It encodes explicit precedence scenarios with expected winner layers and reasons.

## Run

```bash
python3 pkm-memory/scripts/verify_recovery_precedence_task_418.py
```

## Output

- `pkm-memory/outputs/task-418-canonical-recovery-precedence-2026-05-12/verification-report.json`
