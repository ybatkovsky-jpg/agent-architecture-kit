# Task #419 recovery resolver prototype fixture

Minimal bounded candidate-set fixture for selecting a winning recovery anchor.

## Dependency

Conservatively reuses the precedence contract from task #418 when its report is present:
- `pkm-memory/outputs/task-418-canonical-recovery-precedence-2026-05-12/verification-report.json`

## Cases

- 4 pass cases with explicit expected winner anchor/layer
- 1 fail case for unsupported layer

## Run

```bash
python3 pkm-memory/scripts/verify_recovery_resolver_task_419.py
```

## Outputs

- `pkm-memory/outputs/task-419-recovery-resolver-prototype-2026-05-12/verification-report.json`
