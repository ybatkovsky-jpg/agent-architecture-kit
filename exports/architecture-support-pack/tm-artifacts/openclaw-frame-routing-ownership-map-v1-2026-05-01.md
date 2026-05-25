# OpenClaw Frame Routing / Ownership Map v1

Date: 2026-05-01
Status: draft
Depends on:
- `task-manager/artifacts/openclaw-frame-architecture-baseline-v1-2026-05-01.md`
- `task-manager/artifacts/openclaw-frame-handoff-spec-v1-2026-05-01.md`
Scope: минимальная routing/ownership карта для OpenClaw Frame v1

## Purpose

Зафиксировать, как Frame v1 маршрутизирует типы работы по execution lanes, кто является owner в каждом контуре, где живёт durable state, куда приземляется completion, и как выглядит escalation path.

Цель v1 — убрать ambiguous routing. Это не полная runtime architecture, а operating map, достаточная для последовательной работы.

---

## Routing principles

### 1. Conversational surface != execution lane
Чат / main-сессия — это точка входа, orchestration и decision surface, но не default место для длинного выполнения.

### 2. Routing should happen early
Как только понятно, что работа bounded и самостоятельная, её надо маршрутизировать в соответствующий lane, а не держать в `main`.

### 3. Ownership must be explicit
Для каждого lane должно быть понятно:
- кто execution owner;
- кто decision owner;
- кто принимает `BLOCKED`;
- кто получает `DONE`.

### 4. Durable state must be known in advance
Маршрут неполон, если непонятно, где живёт рабочее состояние и где искать anchor результата.

---

## Lane catalog v1

Frame v1 использует 5 основных lane-категорий:
1. `main-orchestrator`
2. `bounded-execution`
3. `artifact-production`
4. `human-decision`
5. `background-observation`

Ниже — не runtime types в узком кодовом смысле, а operating lanes.

---

## Lane 1: `main-orchestrator`

### Role
Тонкий слой orchestration, routing, user interaction, decision-taking и closure.

### Typical inputs
- новые пользовательские задачи;
- запросы на решение / выбор / приоритизацию;
- review of results;
- escalation from other lanes.

### Default owner
- `main`

### Durable state
- task artifacts
- handoff files
- memory surfaces
- structured task state

### Completion surface
- short user-facing summary
- routing decision
- next bounded unit creation

### Escalation path
- to `human-decision` if explicit human choice is needed
- to `bounded-execution` if implementation/analysis is needed

### Handoff rules
- `ACK` when work is delegated to execution lane
- `DONE` when orchestration slice itself is complete
- `BLOCKED` only when main genuinely lacks authority/context to route safely

---

## Lane 2: `bounded-execution`

### Role
Изолированное выполнение bounded work unit: анализ, patching, bounded coding, inspection, narrow synthesis, technical validation.

### Typical inputs
- code inspection
- focused implementation slice
- technical debugging
- bounded research with clear output contract

### Default owner
- `subagent:<label>`
- or `runtime:<execution-lane>`

### Durable state
- produced artifact files
- task notes / handoffs
- code diffs / generated outputs
- bounded run state in task manager or equivalent

### Completion surface
- `DONE` with artifact/result anchor
- `BLOCKED` with explicit blocker and decision owner

### Escalation path
- back to `main-orchestrator`
- or to `human-decision` if authority/input is missing

### Handoff rules
- should emit `ACK` quickly after taking work
- should not keep conversational ownership
- should terminate with `DONE` or `BLOCKED`, not drift silently

---

## Lane 3: `artifact-production`

### Role
Производство durable outputs, которые сами являются целевым результатом или несущим промежуточным объектом.

### Typical inputs
- architecture baselines
- specs
- maps
- reports
- publish packages
- generated content packages

### Default owner
- usually `bounded-execution`
- but result ownership after completion often returns to `main`

### Durable state
- files under workspace/task-manager/content-system/etc.

### Completion surface
- artifact path(s)
- short summary of what was produced

### Escalation path
- back to `main-orchestrator` for review/next-step decision
- to `human-decision` if artifact needs approval

### Handoff rules
- `DONE` must include concrete artifact anchor
- artifact-only work should not end as vague “prepared something” summary

---

## Lane 4: `human-decision`

### Role
Контур, куда возвращается работа, когда нужен явный человеческий выбор, разрешение, approval, prioritization или authority grant.

### Typical inputs
- approval needed
- competing architectural options
- external action required
- missing secret/access/permission
- decision after bounded analysis

### Default owner
- `human:<name>`
- operationally surfaced by `main`

### Durable state
- decision notes
- approved artifact reference
- explicit user message / accepted choice

### Completion surface
- human answer
- approval / rejection
- chosen option

### Escalation path
- back to `main-orchestrator`
- then usually to `bounded-execution`

### Handoff rules
- other lanes must use `BLOCKED` or `DONE->needs decision`, not silently wait forever
- if a lane requires explicit human authority, ownership must be transferred here clearly

---

## Lane 5: `background-observation`

### Role
Наблюдение, мониторинг, timed instrumentation, passive waiting, lightweight recurring checks.

### Typical inputs
- runtime observation
- telemetry collection
- waiting for event/signal
- cron-like bounded observation tasks

### Default owner
- `runtime:background`
- or detached execution lane under orchestration

### Durable state
- logs
- observation artifacts
- sampled metrics
- trace outputs

### Completion surface
- observation note
- metric sample
- evidence artifact
- escalation if threshold crossed

### Escalation path
- back to `main-orchestrator`
- or to `human-decision` if action/approval is needed

### Handoff rules
- must define stop condition up front
- must not become infinite silent watch loops without budget
- should emit `DONE` when evidence is collected, `BLOCKED` when observation cannot proceed meaningfully

---

## Work type -> lane routing map

## 1. Conversational clarification / framing
- Target lane: `main-orchestrator`
- Owner: `main`
- State: chat + supporting artifacts if needed
- Completion: clarified goal / next routed unit
- Escalation: none unless ambiguity remains high

## 2. Focused technical inspection
- Target lane: `bounded-execution`
- Owner: execution unit / subagent
- State: task notes, code references, artifacts
- Completion: technical verdict with anchors
- Escalation: `main`, then optional `human-decision`

## 3. Document / spec / baseline creation
- Target lane: `artifact-production` via `bounded-execution`
- Owner: execution unit during production, then `main`
- State: workspace artifact file
- Completion: `DONE` with artifact path
- Escalation: review by `main` or human

## 4. Runtime instrumentation / telemetry capture
- Target lane: `bounded-execution` + `background-observation`
- Owner: execution lane while patching, background lane while observing
- State: patched code, logs, sampled outputs
- Completion: evidence-backed verdict
- Escalation: `main` / `human-decision` if live mutation approval needed

## 5. External approval / permission / authority gating
- Target lane: `human-decision`
- Owner: human
- State: request + supporting artifact
- Completion: approve / reject / choose
- Escalation: back to `main`

## 6. Long-running or exact-time checks
- Target lane: `background-observation`
- Owner: background runtime
- State: cron/job/observation artifact
- Completion: evidence or timeout/budget exhaustion
- Escalation: `main`

---

## Ownership transitions by lane

### Main -> Bounded execution
Use when:
- work is самостоятельная;
- нужен execution focus;
- нужен bounded technical slice.

Expected handoff:
- `ACK` from execution lane
- then `DONE` or `BLOCKED`

### Bounded execution -> Artifact production
Use when:
- output должен жить как durable file/spec/package.

Expected handoff:
- usually internal to same bounded unit,
- but final `DONE` must point to produced artifact.

### Bounded execution -> Main
Use when:
- technical slice completed;
- нужен routing/closure/review/summary.

Expected handoff:
- `DONE` with anchor
- or `BLOCKED` with decision owner

### Any lane -> Human decision
Use when:
- explicit human authority or choice is required.

Expected handoff:
- `BLOCKED` with `owner_for_decision=human:<name>`
- or explicit decision package for review

### Background observation -> Main
Use when:
- evidence collected;
- threshold crossed;
- stop condition met.

Expected handoff:
- `DONE` with observation anchor
- or `BLOCKED` if observation path cannot proceed

---

## Durable state map

### `main-orchestrator`
State should live in:
- task artifacts
- memory surfaces
- structured notes

### `bounded-execution`
State should live in:
- produced files
- diffs
- handoff artifacts
- bounded-run state

### `artifact-production`
State should live in:
- target artifact file(s)
- package directories
- explicit output locations

### `human-decision`
State should live in:
- explicit decision messages
- approved/rejected artifacts
- follow-up tasks or notes

### `background-observation`
State should live in:
- logs
- observation files
- sampled outputs
- trace captures

---

## Escalation map

### Escalate to `main-orchestrator` when
- execution completed and needs routing/closure;
- a technical slice produced a result;
- a background check found a signal that needs interpretation.

### Escalate to `human-decision` when
- approval is needed;
- permission or access is missing;
- multiple valid options require explicit preference;
- risk boundary forbids autonomous continuation.

### Escalate as `BLOCKED` rather than retry when
- retry budget exhausted;
- blocker is not local to the lane;
- missing prerequisite is external;
- ambiguity is decision-grade, not implementation-grade.

---

## Routing anti-patterns

### 1. Keeping execution in `main`
Длинная реальная работа идёт прямо в chat surface без выделенного execution owner.

### 2. Artifact without lane closure
Артефакт создан, но неясно, кто теперь owner и что next step.

### 3. Human approval hidden inside execution
Исполнитель ждёт неявного одобрения вместо явного перехода в `human-decision`.

### 4. Observation with no stop condition
Background lane запущен, но не имеет explicit budget / stop rule / escalation rule.

### 5. Routing by vibe
Непонятно, почему работа пошла именно в этот lane и по каким правилам.

---

## Minimal acceptance criteria for Routing / Ownership Map v1

Карта считается достаточной для v1, если:
- для каждого основного типа работы есть понятный target lane;
- у каждого lane есть owner, durable state, completion surface и escalation path;
- handoff spec можно приземлить на routing map без выдумок;
- `main` не остаётся implicit default execution sink;
- `BLOCKED` и `DONE` имеют понятные адресаты.

---

## Next likely step

После этой карты логично собирать один из двух следующих слоёв:
1. `Memory Distillation Cadence`
2. `Retry / Escalation Budget Policy v1`

Если идти по structural dependency, сначала разумнее сделать `Retry / Escalation Budget Policy v1`, потому что routing без budget rules всё ещё может деградировать в бесконечные loops.
