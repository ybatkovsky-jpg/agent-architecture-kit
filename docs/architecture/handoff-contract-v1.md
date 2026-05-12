# Handoff Contract v1

A bounded work unit should terminate in one of three states:
- `ACK` — execution ownership accepted;
- `DONE` — bounded responsibility completed with a durable result anchor;
- `BLOCKED` — local continuation is no longer justified and decision ownership must move.

## Required fields

Every handoff should carry:
- `status`
- `work_unit_id`
- `owner`
- `scope`
- `summary`
- `next_action`

Conditionally required:
- `result_anchor` for `DONE`
- `blocked_reason` for `BLOCKED`
- `owner_for_decision` for `BLOCKED`

## Intent

The contract exists to answer, without ambiguity:
- who took the work;
- what bounded scope was attempted;
- where the result lives;
- who owns the next move;
- why work stopped when it stopped.
