# OpenClaw Frame Canonical Anchor and Storage Policy v1

## 1. Scope and purpose

This document defines the minimum canonical anchor and storage policy for OpenClaw Frame v1.

Its purpose is to ensure that important runtime objects do not live only in transcript residue or operator memory.
It gives later implementation and verification tasks a stable policy for:
- what classes of objects need canonical anchoring;
- which default surfaces should hold them;
- how canonical truth differs from readable projection;
- how recovery should work when summaries or chat tails are incomplete;
- how newer anchors supersede older ones without ambiguity.

This is a policy/spec artifact, not a broad storage-engine design.

---

## 2. Core policy stance

### 2.1 Truth-before-legibility rule
Readable summaries are useful, but operational truth must live in a canonical anchor.
If a statement changes execution, ownership, lifecycle, evidence, or reusable memory, it must map to a canonical surface.

### 2.2 One object class, one default anchor rule
Each operational object class should have one default canonical location/surface.
Exceptions are allowed, but only as explicit policy exceptions rather than ad hoc convenience.

### 2.3 File-first and state-first recovery
If recovery would require transcript archaeology, anchoring is insufficient.
Default recovery should start from task state, continuation artifacts, durable evidence, and memory notes.

### 2.4 Projection-is-not-authority rule
Chat replies, dashboard summaries, and operator-facing digests are projections unless explicitly declared as the canonical anchor.
They may quote or summarize truth, but should not silently replace it.

### 2.5 Separation rule
The policy distinguishes at least four truth classes:
- task truth;
- continuation truth;
- evidence truth;
- memory truth.

These may link to each other, but should not collapse into one mixed surface.

---

## 3. Object classes that require canonical anchoring

The following object classes require canonical anchors in Frame v1:
- task lifecycle state;
- routing decision / routing card;
- handoff package;
- resume trigger or continuation basis;
- continuation return package;
- blocked package;
- result anchor / evidence artifact;
- distillation entry;
- durable memory note;
- human decision once it affects work;
- operator-visible summary only when separately promoted into a canonical note.

Not every conversational utterance needs anchoring.
Only objects that affect recovery, next action, authority, or future reuse must be canonically anchored.

---

## 4. Default canonical locations and surfaces

| Object class | Default canonical location / surface | Canonical truth class | Notes |
|---|---|---|---|
| Task lifecycle state | `task-manager` task state and task notes | Task truth | Authoritative for open/active/blocked/closed, dependencies, next owner |
| Routing card | `task-manager/artifacts/` or task note if very small | Task truth / routing truth | Use artifact when routing is non-trivial or reusable |
| Handoff package | `task-manager/artifacts/` | Continuation truth | Parent-created continuation basis |
| Resume trigger / continuation basis | `task-manager/artifacts/` or explicit task note linking basis anchor | Continuation truth | Must point to concrete reason resume is valid |
| Return package (`DONE`/`BLOCKED`) | `task-manager/artifacts/` with link from task note/state reflection | Continuation truth | Terminal contract for bounded attempt |
| Blocked package | `task-manager/artifacts/` or structured task note if small and local | Continuation truth / task truth | Must name blocker and decision owner |
| Result anchor / evidence artifact | Producing repo/workspace path, linked from task note or return package | Evidence truth | Canonical proof that bounded work produced something |
| Distillation entry | memory surface or task-linked distillation note | Memory truth | Event-driven compact reusable lesson |
| Durable memory note | memory surface | Memory truth | Decision, pattern, anti-pattern, blocker, durable ref, etc. |
| Human decision reflection | task note, decision note, or linked artifact | Human decision truth reflected into task/continuation truth | Raw chat alone is insufficient |
| Operator-visible summary | chat/topic reply, dashboard, status digest | Legibility truth only | Should cite canonical anchors |

---

## 5. Canonical truth vs readable projections

### 5.1 Canonical truth
A canonical anchor is the surface the system should trust first during recovery, verification, or dispute.
Canonical truth should be durable, referenceable, and narrow enough to re-read without replaying a whole conversation.

### 5.2 Readable projection
A readable projection is optimized for operator comprehension, not authority.
Examples:
- Telegram reply summarizing progress;
- short completion summary from a bounded unit;
- dashboard digest;
- review comment.

### 5.3 Projection requirements
A projection should, when relevant:
- cite task id;
- cite artifact path or anchor id;
- state whether it is `DONE`, `BLOCKED`, decision-needed, or summary-only;
- avoid introducing new authoritative state that is not reflected elsewhere.

### 5.4 Precedence rule when surfaces disagree
When the same operational fact appears in several places, prefer:
1. task lifecycle truth for lifecycle status and next owner;
2. continuation truth for handoff/resume/return state;
3. evidence truth for what was actually produced or observed;
4. memory truth for reusable lessons and decisions already distilled;
5. readable projections and transcript residue.

---

## 6. Anchor rules by truth class

### 6.1 Task truth
Task truth answers:
- what is active now;
- what is blocked now;
- what depends on what;
- who owns the next decision;
- what bounded step should happen next.

Rules:
- canonical surface is task-manager task state plus task notes;
- lifecycle state must not depend on a chat reply alone;
- if a child run ends `DONE` or `BLOCKED`, parent task truth must be updated or linked accordingly;
- task truth may point to continuation and evidence anchors, but should not duplicate them in full.

### 6.2 Continuation truth
Continuation truth answers:
- what bounded unit was delegated;
- why resume is allowed;
- who owns execution;
- who owns the next decision;
- what terminal condition closed the attempt.

Rules:
- canonical surface is handoff package, resume trigger/basis, and return package;
- continuation truth should live under `task-manager/artifacts/` by default;
- every continuation package should link back to parent task truth;
- each bounded attempt should end in an explicit terminal anchor, not an implied stopping point in chat.

### 6.3 Evidence truth
Evidence truth answers:
- what was produced;
- what was observed;
- what demonstrates bounded completion.

Rules:
- canonical surface is the produced artifact or evidence file itself;
- return packages and task notes should link to evidence rather than trying to replace it;
- if a summary claims a result exists, the summary should point to the result anchor;
- evidence truth is not automatically memory truth.

### 6.4 Memory truth
Memory truth answers:
- what should be reused later;
- what decision/pattern/anti-pattern/blocker should survive this run;
- which durable references matter beyond the immediate task.

Rules:
- canonical surface is durable memory note or other memory-layer object;
- memory notes should be selective and event-driven;
- memory truth should be derived from evidence and decisions, not from vague recollection;
- not every result artifact deserves memory distillation.

---

## 7. Default storage rules for specific Frame objects

### 7.1 Routing cards
Default storage:
- `task-manager/artifacts/` when routing is complex, reusable, or cross-cutting;
- task note only when routing is a small one-off reflection.

Policy:
- routing card is canonical only if it records the current route and owner clearly;
- operator message announcing routing is projection only unless linked to the card or note.

### 7.2 Handoff packages
Default storage:
- `task-manager/artifacts/`.

Policy:
- handoff package is the canonical outbound continuation anchor;
- it should include parent task linkage and intended return target;
- if multiple attempts occur, each attempt should remain linkable rather than overwritten in place.

### 7.3 Blocked packages
Default storage:
- `task-manager/artifacts/` for durable blocked packages;
- task note allowed for very small local blocker reflections, provided blocker fields are explicit.

Policy:
- blocked package must name blocked reason, owner for next decision, and recovery suggestion;
- `BLOCKED` in chat without a canonical note/package is insufficient.

### 7.4 Continuation basis
Default storage:
- same continuation artifact family under `task-manager/artifacts/`, or an explicit task note that points to the authoritative basis anchor.

Policy:
- continuation basis is canonical only if it answers why this unit may start now;
- basis may reference decision note, prerequisite artifact, prior return package, or manual resume authorization.

### 7.5 Result anchors
Default storage:
- the produced workspace or repo file itself, linked from return package and task note.

Policy:
- result anchors are evidence truth;
- a completion summary should not be treated as enough if the produced artifact is missing or unclear;
- when the result is a code change, canonical evidence may be diff plus modified file set.

### 7.6 Distillation entries
Default storage:
- memory-layer durable note surface, optionally mirrored by task note reference.

Policy:
- distillation entries are for reuse value, not for every outcome;
- trigger categories from memory-distillation cadence apply;
- distillation should cite its upstream evidence or decision anchors.

### 7.7 Memory notes
Default storage:
- memory surface intended for reusable compact objects.

Policy:
- memory notes should be typed conceptually as decision, pattern, anti-pattern, blocker, durable ref, preference, or state summary;
- a memory note must not become the only place where immediate task lifecycle state is stored.

---

## 8. Operator-visible projection policy

Operators need concise, human-readable visibility, but that surface should remain a projection by default.

### 8.1 What operator-visible projections should include
- task id when available;
- current status (`active`, `DONE`, `BLOCKED`, awaiting decision, etc.);
- short summary of what changed;
- canonical artifact path or note reference for anything important;
- next owner or next action.

### 8.2 What projections should avoid
- being the only record of a blocker or decision;
- implying completion without result anchor;
- describing a resume basis that is not captured canonically elsewhere;
- mixing evidence, memory, and lifecycle truth into one untyped narrative blob.

### 8.3 Promotion exception
If an operator-visible note is intentionally promoted to canonical status, that promotion must be explicit and should normally happen by saving it as a task note or artifact.

---

## 9. Recovery rules

### 9.1 Default recovery order
When recovery is needed, prefer this order:
1. task truth for current lifecycle and next owner;
2. latest continuation package / return package for bounded-run state;
3. evidence anchor for what was produced;
4. memory note for reusable prior lessons;
5. projections and transcript residue only as fallback.

### 9.2 Recovery by failure class

| Failure class | Default recovery action | Canonical basis |
|---|---|---|
| Lost chat context | Re-read task state and latest linked anchors | Task truth + continuation truth |
| Missing or vague completion summary | Read return package and evidence artifact | Continuation truth + evidence truth |
| Need to resume after blocker cleared | Create new continuation attempt referencing prior blocked package and new basis anchor | Prior blocked package + new continuation basis |
| Reusable lesson needs preservation | Distill from evidence and decision anchors into memory note | Evidence truth + memory truth |
| Conflicting summaries | Prefer the highest-precedence canonical truth class and repair projections if needed | Truth precedence rule |

### 9.3 Repair rule
If projection and canonical state diverge, repair the projection or add corrective note.
Do not silently treat the projection as authoritative.

---

## 10. Supersession rules

### 10.1 General supersession rule
Newer anchors supersede older anchors only within the same truth class and object lineage.
A newer readable summary does not supersede an older canonical anchor by itself.

### 10.2 Task truth supersession
For lifecycle state, the latest valid task state/note reflection supersedes older lifecycle reflections.
Older notes remain history, but should not be treated as current state.

### 10.3 Continuation supersession
A new continuation attempt does not erase the previous one.
Instead:
- previous handoff/blocked/return package remains historical truth for that attempt;
- new attempt references the prior package as part of lineage;
- the latest valid terminal or active continuation anchor becomes current continuation truth.

### 10.4 Evidence supersession
A revised artifact supersedes an earlier version only if versioning or replacement is explicit.
Where possible, preserve stable paths or explicit version markers to avoid ambiguous replacement.

### 10.5 Memory supersession
A memory note may be superseded by a later refined memory note or wiki-like consolidation page, but only if the newer note explicitly carries forward or replaces the prior lesson.

---

## 11. Bounded examples

### Example 1 — Simple bounded document task
- `main` delegates a spec drafting task.
- Canonical handoff package is saved under `task-manager/artifacts/`.
- Child run produces `DONE` return package plus a markdown artifact path.
- Parent adds a task note linking the artifact.
- Telegram summary says “done” and cites the task note/artifact.

Canonical anchors:
- handoff package;
- produced markdown artifact;
- return package;
- task note.

Projection only:
- chat completion summary.

### Example 2 — Blocked for human decision
- Child run cannot proceed without approval.
- It emits `BLOCKED` package naming decision owner and recovery suggestion.
- Parent reflects blocker into task note/state.
- Human replies in chat.
- Parent records the decision in a task note and creates a new continuation basis.

Canonical anchors:
- blocked package;
- decision reflection note;
- new continuation basis.

Projection only:
- approval chat reply before reflection.

### Example 3 — Distilled reusable lesson
- A bounded investigation finds that transcript-only recovery repeatedly fails.
- Evidence artifact documents the failure mode.
- A memory note is created capturing the anti-pattern and the preferred anchor rule.

Canonical anchors:
- investigation artifact as evidence truth;
- memory note as memory truth.

Projection only:
- short operator summary describing the lesson.

---

## 12. Open questions

1. Should continuation artifacts use markdown-with-frontmatter, pure JSON/YAML, or a dual-surface format?
2. Which exact task-manager fields should be reserved as authoritative linkage for parent/child continuations and latest result anchors?
3. Should blocked packages always be separate artifacts, or can a structured task note be the default for small blockers?
4. How much automatic projection generation is desirable before it starts obscuring truth-boundary discipline?
5. Which memory surface should be treated as the first-class home for distillation entries in the current runtime?

---

## 13. Why this is a good bounded completion

This artifact gives the #391 next-stage contour a direct storage-policy contract without expanding into broad infrastructure design.
It is compact, implementation-facing, and verification-friendly.
It cleanly separates:
- canonical truth from projection;
- task vs continuation vs evidence vs memory truth;
- current state from historical lineage and supersession.

It also appears reusable and public-safe enough that it likely qualifies for later cleanup and promotion into `product-repos/agent-architecture-kit`,
