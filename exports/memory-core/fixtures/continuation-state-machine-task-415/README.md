# Task #415 continuation state machine fixture spec

Minimal bounded fixture pack for continuation state machine verification.

## Purpose

Provides one explicit verifier input for the continuation contract transition rules.

Covered canonical paths:
- `PREPARED -> ACK -> RUNNING -> DONE`
- `PREPARED -> ACK -> RUNNING -> BLOCKED`
- `PREPARED -> BLOCKED`

## Basis

- `task-manager/artifacts/openclaw-frame-continuation-contract-v1-2026-05-12.md`
- `task-manager/artifacts/task-415-r1-continuation-state-machine-fixture-spec-2026-05-12.md`

## Notes

This pack is intentionally narrow.
It is not a runtime schema and not an implementation.
It exists so follow-up verification work can validate allowed and forbidden transitions against explicit examples.

## Expected follow-up

A bounded verifier should:
1. load `fixture.json`;
2. validate allowed transitions for all valid cases;
3. validate required fields per state;
4. reject the listed invalid transition examples.
