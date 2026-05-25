# ZIRIBT 3 — Fresh-run policy enforcement spec

Date: 2026-05-17
Status: bounded implementation-facing policy artifact
Scope: define when work must leave `main` or long-lived lane surfaces and move into fresh bounded execution; define branch-local continuation and return contract.

---

## 1. Purpose

The goal of this slice is operational, not philosophical:

> make thin-context architecture real by enforcing **when** work must move into a fresh bounded run instead of staying inside `main` or a long-lived lane surface.

This artifact builds on:
- session hygiene policy;
- fresh task-scoped bootstrap contract;
- routing map;
- lane manifests;
- runtime envelope inspection.

---

## 2. Executive decision

## Default rule
If work is **bounded, multi-step, artifact-producing, domain-specific, or likely to create context tail**, it should move into a **fresh bounded run**.

### Corollary
Long-lived surfaces should be treated as:
- dialogue surface;
- approval surface;
- summary surface;
- escalation surface;

and **not** as primary machine working memory for deep execution.

---

## 3. Surface roles

### 3.1 `main`
Allowed role:
- user dialogue;
- quick clarification;
- routing;
- short decisions;
- concise synthesis;
- escalation/approval requests.

Not allowed as default:
- long implementation trail;
- deep research branch;
- repeated validation loops;
- broad file-inspection chain;
- long-lived execution memory.

### 3.2 Long-lived role topics/threads
Allowed role:
- operator-visible continuity;
- decision history;
- summary and approval flow;
- narrow human conversation around a contour.

Not allowed as default:
- primary execution substrate for deep bounded work;
- ambient memory reservoir for future runs;
- implicit replacement for branch-local continuation capsule.

### 3.3 Fresh bounded run
Default role for:
- deep work;
- one-off research;
- artifact production;
- validation;
- bounded implementation;
- work likely to survive current turn.

---

## 4. Mandatory spawn triggers

Spawn a fresh bounded run when **any** of these is true.

### Trigger A — Multi-step bounded work
The request clearly requires more than one meaningful execution step.

Examples:
- inspect -> compare -> propose;
- research -> synthesize -> spec;
- implement -> verify -> summarize.

### Trigger B — Artifact-producing work
The expected output is:
- spec;
- report;
- plan;
- code change;
- audit artifact;
- structured note.

### Trigger C — File/system inspection or validation
The work requires:
- reading several files;
- tracing architecture/runtime seams;
- validating outputs;
- running checks;
- comparing artifacts.

### Trigger D — Domain-specific deep lane work
The work belongs mainly to:
- strategist;
- architect;
- learning;
- ops;

and is not just a short answer.

### Trigger E — Tail-growth risk
The branch is likely to generate:
- long reasoning trail;
- repeated retries;
- broad context accumulation;
- long-lived local state not needed in the user-facing surface.

### Trigger F — Work should survive restart/compaction
If the work needs resumability after:
- context cut;
- restart;
- handoff;
- pause/resume.

### Trigger G — Current surface budget is already under pressure
If the lane already risks crossing target budget or has accumulated stale residue, do not continue there by inertia.

---

## 5. Allowed stay-in-surface exceptions

Work may remain in the current surface only when **all** relevant conditions fit.

### Exception 1 — Short answer
The answer is direct, short, and does not create a meaningful execution tail.

### Exception 2 — Live dialogue is the work
The user is actively discussing, deciding, refining, or brainstorming in a way where the interactive back-and-forth is itself the main task.

### Exception 3 — Routing is the main work
The only real step is deciding lane/scope/next action.

### Exception 4 — Tiny bounded clarification
A micro-inspection or one-step check is enough and will not generate significant residue.

### Exception 5 — User explicitly wants interactive co-working in current surface
Even then, if the branch starts growing, policy should re-evaluate and move the next bounded chunk into a fresh run.

---

## 6. Decision matrix by request class

| Request class | Default execution surface | Exception to stay in current surface | Return shape |
|---|---|---|---|
| short factual / quick answer | current surface | default | direct answer |
| routing / what lane? | current surface | default | lane decision + next step |
| architecture research / contour design | fresh bounded architect run | only if truly one-shot and short | decision-grade summary + artifact ref |
| business strategy / content planning | fresh bounded strategist run | only if user is doing live interactive shaping and no artifact trail yet | approval-ready summary/artifact |
| learning roadmap / explanation design | fresh bounded learning run | only if short explanation is enough | clear explanation/plan |
| ops diagnosis / config analysis | fresh bounded ops run | only for tiny status checks | observed state + next safe action |
| file-heavy investigation | fresh bounded run | none by default | claim/evidence/verification |
| validation / reruns / regression checks | fresh bounded run | none by default | verdict + evidence |
| implementation slice | fresh bounded run | none by default | result + delta + blocker if any |
| long-form research/spec | fresh bounded run | none by default | artifact + concise synthesis |

---

## 7. Fresh-run bootstrap contract

Every fresh bounded run should launch from a minimal written package containing:
- lane;
- bounded objective;
- task or pseudo-task identity;
- definition of done / acceptance shape;
- current known constraints;
- linked artifacts or packs needed;
- expected return-to-surface shape.

### Rule
Fresh run bootstrap must prefer:
- task brief;
- current continuation capsule;
- linked artifacts;
- compact lane capsule;

and must avoid default reliance on:
- whole main-chat tail;
- long role-topic history;
- broad mixed residue.

---

## 8. Branch-local continuation rules

### Rule 1 — Continuation is current-branch only
Only the continuation package for the currently active branch may be ambiently carried.

### Rule 2 — Older continuation defaults to on-demand
Older handoffs/session capsules are not ambient by default.

### Rule 3 — Topic/thread continuity is not enough
Human-visible continuity in a topic does not replace branch-local machine continuation.

### Rule 4 — Fresh runs must write resumable state back out
At minimum, a fresh run must externalize:
- goal;
- current status;
- next action;
- blockers;
- relevant refs;
- facts to preserve.

---

## 9. Return contract from fresh runs

A fresh bounded run should return only decision-grade output to the parent surface:

1. **Claim** — what was done or concluded;
2. **Evidence** — what supports it;
3. **Verification status** — verified / partial / not yet verified;
4. **Delta** — what changed in task/context state;
5. **Needed input** — approval, missing info, or blocker;
6. **Recommended next step**.

### Anti-pattern
Do not dump long internal trace/log/process narrative into `main` or long-lived lane thread unless explicitly requested.

---

## 10. Surface-specific enforcement rules

### 10.1 `main`
If a request hits any mandatory spawn trigger, `main` should:
1. identify lane;
2. launch fresh bounded run;
3. keep only concise operator-facing summary.

### 10.2 strategist long-lived topic
Treat as:
- review/approval surface;
- business decision history;
- concise negotiation surface.

Do not keep there by default:
- long content-plan generation trail;
- deep market analysis branch;
- long artifact-building sequence.

### 10.3 architect long-lived surface
Treat as:
- architecture decision surface;
- review/synthesis surface.

Do not keep there by default:
- deep evidence-trace accumulation;
- long runtime inspection branches;
- multi-file architecture archaeology.

### 10.4 learning long-lived surface
Treat as:
- clarification and progress surface.

Do not keep there by default:
- large curriculum buildouts;
- long decomposition artifacts;
- iterative lesson design loops.

### 10.5 ops long-lived surface
Treat as:
- status/update/escalation surface.

Do not keep there by default:
- long diagnosis trails;
- repeated inspections;
- verification loops.

---

## 11. Escalation rules

### Escalation 1 — Surface drift detected
If a branch begins in current surface but becomes multi-step or artifact-producing, the **next chunk** should move into a fresh run.

### Escalation 2 — Budget warning detected
If context envelope inspection shows a red-flag trend, stop continuing in place and cut to fresh bounded execution.

### Escalation 3 — Branch split needed
If one surface now hosts multiple semantically different branches, split the next independent branch into a new fresh run.

### Escalation 4 — Audit/proof needed
If the user needs evidence-backed conclusion rather than discussion, move to fresh run.

---

## 12. Minimal implementation hooks

This policy can later be enforced with lightweight hooks.

### Hook A — spawn recommendation function
Input:
- lane
- request_class
- predicted artifact depth
- predicted tail-growth risk
- current surface budget status

Output:
- `stay`
- `spawn_fresh`
- `spawn_fresh_required`

### Hook B — branch-local continuation validator
Checks whether ambient continuation candidates are current-branch only.

### Hook C — return-contract formatter
Normalizes fresh-run output back into compact decision-grade surface updates.

---

## 13. Risks

1. **Over-spawning**
   Too many fresh runs for tiny work would create friction.
   Mitigation: keep explicit short-answer/live-dialogue exceptions.

2. **Under-spawning by habit**
   Humans and agents may keep working in-place out of inertia.
   Mitigation: mandatory triggers + budget warning rule.

3. **Weak continuation packages**
   Fresh runs fail if written state is too thin.
   Mitigation: enforce bootstrap + return contract.

4. **Surface confusion**
   Users may think long-lived topics are being ignored.
   Mitigation: keep them as summary/approval surfaces with concise updates.

---

## 14. Acceptance criteria for this ZIRIBT slice

- [x] Mandatory spawn triggers are explicit.
- [x] Stay-in-surface exceptions are explicit.
- [x] Request-class decision matrix exists.
- [x] Branch-local continuation rules are defined.
- [x] Fresh-run return contract is defined.
- [x] Minimal implementation hooks are named.

---

## 15. Recommended next step

Proceed to **ЗИРиБТ 4 — Strategist runtime contour enforcement**.

Reason:
Strategist is the most operator-visible place where long-lived surface and broad-context drift still feel like the old shared contour, so it is the highest-value enforcement pilot after fresh-run policy is locked.
