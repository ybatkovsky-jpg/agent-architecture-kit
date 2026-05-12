# Implementation Mapping

## 1. Purpose

This document turns the OpenClaw Frame architecture from a conceptual stack into a concrete implementation map.

It focuses on six questions for each layer:
1. where the layer lives in the real runtime;
2. what surface is canonical;
3. who owns execution vs decision vs persistence;
4. what default artifact form is expected;
5. how recovery and resume should work;
6. what operators or users are allowed to see as a projection rather than as hidden truth.

This document is intentionally compact and implementation-facing.

---

## 2. Mapping rules

### 2.1 Canonical truth precedence

When the same fact appears in several places, prefer this order:
1. task lifecycle truth;
2. runtime continuity truth;
3. durable evidence/result truth;
4. distilled memory truth;
5. operator-visible summaries and transcript residue.

### 2.2 Projection rule

Readable summaries, chat replies, and convenience notes are projections unless they are explicitly designated as canonical anchors.

### 2.3 File-first rule

If a state contract can live in a structured file or artifact, it should not rely on transcript-only recovery.

### 2.4 Thin-main rule

`main` is the default decision and orchestration surface, not the default long-running execution sink.

---

## 3. Implementation mapping matrix

| Layer / concern | Concrete runtime surface | Canonical truth / anchor | Primary owner | Default artifact form | Recovery / resume path | Operator-visible projection |
|---|---|---|---|---|---|---|
| Human/operator surface | Chat session, approval prompts, user messages | User decision once reflected into task state or note; raw chat alone is not enough | Human for decision, `main` for reflection | Short decision note, approval result, task update | Re-read latest task state + decision note; do not reconstruct from chat alone when avoidable | Reply in topic, approval card, concise summary |
| Main orchestrator | `main` session / parent run | Routing decision, active next step, return target, reflected into task manager state and/or handoff artifact | `main` | Routing card, bounded summary, handoff request | Resume from parent task + latest handoff/result anchor | Short user-facing summary, next-step explanation |
| Bounded isolated run | Subagent session / detached bounded execution unit | Its terminal `DONE`/`BLOCKED` package plus linked artifact/result anchor | Execution owner = subagent/runtime lane; decision owner usually `main` or human | Bounded completion note, patch/result summary, artifact links | Spawned from handoff package; resume via new bounded unit, not by reopening transcript tail as authority | ACK/DONE/BLOCKED summary surfaced to parent |
| Worker lane / specialized subagent | Subagent runtime surface, task-scoped execution context | Same as bounded run: terminal contract + produced artifacts | `subagent:<label>` or runtime lane | Artifact, code diff, validation output, narrow report | New handoff from parent with explicit resume basis | Parent-facing completion summary |
| Task lifecycle control plane | Task manager tasks, statuses, notes, dependency state | Task state is authoritative for lifecycle: open/active/blocked/closed, dependencies, next owner | Task control owner / `main` acting through task manager | Task record, task note, status transition | Recover by reading task record + latest related notes | Task dashboards, textual task summaries |
| Continuation truth / bridge layer | Handoff package + resume basis + parent/child linkage | The handoff/continuation package is canonical for restartable execution context | `main` creates; child execution lane consumes; decision owner explicit in package | Structured handoff artifact, blocked package, continuation basis | `handoff -> ACK -> isolated continuation -> DONE/BLOCKED`; chained continuation creates a new package rather than mutating transcript memory | Handoff accepted, blocked, or completed summaries |
| Routing / lane selection | Routing decision in `main`, optionally backed by routing card artifact | Latest explicit routing card or decision note | `main` | Routing card, scope statement, owner map reference | Re-run routing from task state and current blocker if route invalidates | “This is going to bounded execution / human decision / observation” |
| Durable evidence / result truth | Workspace files, produced documents, code diffs, generated outputs under repo or artifact storage | Result artifact path(s) and evidence package | Producing lane until `DONE`; then parent task owns incorporation | Markdown artifact, JSON output, diff, report, verification output | Resume from artifact anchor and linked task/handoff ids | Artifact path + short explanation |
| Memory note layer | Durable memory notes / distilled lessons surfaces | Distilled note only for reusable decisions, patterns, anti-patterns, blockers with reuse value | Memory/distillation owner, typically `main` or a designated distillation step | Memory note, distilled lesson entry, pattern note | Recover by retrieval of memory note, not by scanning old chat | Retrieved summary or cited lesson |
| Background observation | Detached observation runtime, cron/monitor/check lane | Observation artifact/log plus threshold/escalation note | `runtime:background` or detached worker | Observation note, log snapshot, metric sample | Resume by schedule/event trigger with prior observation anchor as basis | Alert, observation summary, threshold-crossing notice |
| Operator-visible summary surface | Final chat reply, review comment, status summary | Non-canonical unless explicitly linked to canonical artifact/task note | `main` | Short summary, bullet list, closure message | Reconstruct from canonical artifacts if summary lost | User-readable response |

---

## 4. Layer-specific implementation notes

### 4.1 Main orchestrator

**What it should own**
- routing;
- lane selection;
- decision framing;
- return-path handling;
- reflecting user decisions into canonical state.

**What it should not own by default**
- long execution trails;
- hidden continuation state that exists only in chat;
- artifact truth without anchors.

**Default anchor set**
- task id or parent run;
- routing card or task note when branching matters;
- outbound handoff package for detached work.

### 4.2 Bounded execution and worker lanes

These are the primary execution surfaces for analysis, code changes, validation, artifact production, and narrow investigations.

**Contract expectation**
- emit `ACK` quickly when execution ownership is taken;
- terminate with `DONE` or `BLOCKED`;
- return a durable result anchor, not only prose.

**Recovery expectation**
- if follow-up work is needed, create a new bounded unit with explicit resume basis;
- avoid relying on “continue from where we left off in chat.”

### 4.3 Task lifecycle truth

Task state should answer:
- what is active now;
- what is blocked and why;
- what depends on what;
- what the next bounded unit is;
- who owns the next decision.

This is the top canonical layer for operational control.

### 4.4 Continuation truth runtime binding

For Frame, the continuation plane should be modeled as a restartable package, not an implicit memory of the prior conversation.

**Minimum continuation package fields**
- handoff id;
- parent task or parent run;
- execution owner;
- decision owner;
- bounded scope;
- resume basis;
- expected next bounded step;
- durable result anchor on completion;
- blocked reason if applicable.

**Canonical path**
- `main` identifies overheated or execution-heavy branch;
- create handoff package;
- bounded unit ACKs;
- isolated continuation executes;
- terminal `DONE` or `BLOCKED` returns to parent;
- parent reflects state into the task control plane.

### 4.5 Durable evidence vs memory

These must stay separate.

**Evidence/result truth**
- what was produced;
- what was observed;
- what proves the bounded slice completed.

**Memory truth**
- what should be reused later as a pattern, rule, decision, or anti-pattern.

Not every artifact becomes memory.
Not every memory note should be treated as execution evidence.

### 4.6 Operator-visible projection

Operators and users need concise visibility, but this surface should remain a projection.

Good projection behavior:
- cite artifact paths;
- cite task ids;
- summarize blocker and owner;
- make next action explicit.

Bad projection behavior:
- becoming the only place where state lives;
- replacing artifact links with vague narrative;
- relying on transcript archaeology.

---

## 5. Default canonical object placement

| Object class | Default canonical location | Notes |
|---|---|---|
| Routing card | Artifact storage or task note when lightweight | Use an artifact when routing is reusable or complex |
| Handoff package | Artifact storage linked from parent task or note | Canonical continuation basis |
| Blocked package | Artifact storage or task note with explicit blocker fields | Must name decision owner |
| Result/evidence artifact | Producing repo/workspace path, linked from task note or handoff result | Canonical proof of bounded completion |
| Distillation entry | Memory or durable note surface | Only for reusable lessons or patterns |
| User-facing summary | Chat reply or operator summary | Projection only unless explicitly anchored elsewhere |

---

## 6. Recovery model by failure class

| Failure class | Primary recovery action | Canonical basis |
|---|---|---|
| Lost conversational context | Re-read task state + latest handoff/result anchors | Task control plane + continuation package |
| Subagent completed but summary missing | Read artifact path and terminal note/package | Durable evidence truth |
| Subagent blocked awaiting decision | Escalate to named decision owner; reflect answer into task state | Blocked package + task state |
| Need follow-up execution after partial result | Spawn new bounded unit with explicit resume basis | Previous result anchor + parent task |
| Reusable lesson discovered | Distill into memory note after completion | Evidence artifact + decision summary |

---

## 7. Implementation implications

1. Continuation contracts should adopt the field set above and be reflected in concrete handoff artifacts.
2. Canonical storage policy can be derived directly from the placement and recovery sections above.
3. Context serving policy should use this matrix to separate:
   - always-on: task state, current routing, latest terminal handoff/result anchors;
   - on-demand: durable evidence artifacts, memory notes, historical specs;
   - forbidden ambient injection: raw transcript tails as default authority.
4. Operator-visible summaries should stay projection-level unless explicitly linked to canonical anchors.

---

## 8. Open questions

1. Should continuation packages live as pure markdown, structured YAML/JSON, or dual-format markdown with frontmatter?
2. Which exact task-manager fields should be treated as authoritative for parent/child bounded-run linkage?
3. Should memory distillation be performed only on task close, or also on terminal `DONE` of significant child runs?
4. How much of the operator-visible projection should be auto-generated from canonical artifacts versus manually summarized by `main`?
