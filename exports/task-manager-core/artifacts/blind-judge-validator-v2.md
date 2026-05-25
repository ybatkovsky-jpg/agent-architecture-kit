# Blind Judge Validator V2

## Distinction

- **Blind judge** = judgment posture. It interprets task state conservatively, asks "what can actually be concluded from the evidence?", and produces coaching / attention guidance.
- **Validator** = mechanical enforcement. It blocks certain status transitions unless minimum closure-contract signals are present.

These layers should stay adjacent but distinct:
- blind judge may be nuanced, skeptical, and advisory;
- validator should stay bounded, explicit, and debuggable.

## V2 enforcement rules

### `review`
Requires:
- claimed outcome in fresh note,
- durable anchor (prefer `context_json.links`, else inline artifact/path/url anchor),
- verification basis,
- explicit `next_action`.

Meaning:
- work produced something inspectable,
- but it is **not** yet equivalent to final closure.

### `done`
Requires:
- claimed outcome,
- anchor,
- verification,
- review gate (`current_status == review` or prior `status:review` event).

Meaning:
- closure should usually pass through review semantics before final done.

### `waiting_user`
Requires:
- explicit `blocked_reason`,
- explicit `next_action` for resumption,
- reason should look externally dependent, not just internally blocked.

Meaning:
- the task is paused on outside input, not merely stuck.

## Debug shape goals

Validator verdicts should explain:
- what status was targeted,
- what was missing,
- which anchors/signals were detected,
- whether review-gate history exists,
- the exact inputs used for the decision.

This keeps false positives / false negatives easier to inspect without turning the layer into a giant policy engine.
