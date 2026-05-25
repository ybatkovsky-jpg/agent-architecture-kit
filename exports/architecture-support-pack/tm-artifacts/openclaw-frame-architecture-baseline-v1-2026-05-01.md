# OpenClaw Frame Architecture Baseline v1

Date: 2026-05-01
Status: draft baseline
Scope: стартовая рамка для дальнейшего развития OpenClaw Frame как execution/orchestration architecture

## Purpose

Зафиксировать минимальный набор уже созревших архитектурных решений, чтобы дальше обсуждать и строить не «вообще систему», а конкретный baseline с понятными operating rules.

---

## 1. Main = thin orchestrator, not execution runtime

### Decision
`main` должен оставаться тонким слоем диалога, orchestration, routing, decision-taking и коротких user-facing summaries.

### Why
Если длинное bounded work, stateful execution и многослойная обработка живут прямо в `main`, контекст быстро раздувается, теряется читаемость, ухудшается handoff, а execution-state становится смешанным с conversational state.

### Operating rule
- Всё достаточно самостоятельное и bounded по умолчанию выносится в fresh execution unit.
- `main` возвращает только решение, summary, request for input или closure.
- Длинные execution trails не считаются нормальной формой работы в `main`.

### Implications
- Нужны удобные isolated/task-scoped runs.
- Нужен хороший handoff contract.
- Нужен file-first state, чтобы execution не зависел от длинного chat tail.

---

## 2. Unified handoff contract is required

### Decision
Для bounded work и cross-lane coordination нужен единый handoff contract с минимумом статусов:
- `ACK`
- `DONE`
- `BLOCKED`

### Why
Без единого handoff contract система быстро превращается в набор несогласованных completion styles, где непонятно:
- кто взял работу,
- где сейчас owner,
- что реально завершено,
- что blocked,
- что нужно для продолжения.

### Contract intent
- `ACK` = работа принята в execution.
- `DONE` = есть завершённый результат с anchor на артефакт / summary / output.
- `BLOCKED` = есть явная причина блокировки и owner следующего decision.

### Required fields for v1
Минимум:
- `status`
- `task / work unit id`
- `owner`
- `scope`
- `result anchor`
- `next action`
- `blocked reason` (если `BLOCKED`)

---

## 3. Memory = distillation layer, not chat archive

### Decision
Memory в Frame — это не попытка «помнить весь чат», а отдельный слой дистилляции решений, паттернов, blockers и lessons learned.

### Why
Если значимые выводы остаются только в conversational history, система становится хрупкой:
- важные решения теряются,
- повторяются одни и те же ошибки,
- новые execution units не имеют короткого reliable context.

### Operating rule
Нужно перегонять в file-first artifacts:
- решения,
- рабочие паттерны,
- анти-паттерны,
- blockers,
- доказанные operating conventions.

### Implications
- Нужен cadence memory distillation.
- Нужны отдельные durable surfaces под decisions/patterns/lessons.
- Нельзя считать длинный chat history достаточным source of truth.

---

## 4. Routing must be deterministic and topic-aware

### Decision
Frame должен иметь явную routing/ownership map: какой тип работы в какую lane идёт, кто owner, где хранится state, где escalation point.

### Why
Без deterministic routing даже сильные bounded runs начинают конфликтовать:
- задачи попадают не в те execution surfaces,
- ownership размывается,
- state расползается,
- escalation происходит слишком поздно или не туда.

### Operating rule
Для каждой категории работы должна быть явная карта:
- input type
- target lane
- owner type
- durable state location
- completion surface
- escalation path

### Minimal routing dimensions
- conversational vs execution work
- synchronous vs detached work
- bounded vs long-running work
- topic-bound vs general work
- user-visible vs internal-only completion

---

## 5. Long contours need bounded retries and escalation budgets

### Decision
Любой длинный контур в Frame должен иметь заранее заданные retry / escalation rules, а не «чиниться до победы» без границ.

### Why
Иначе система начинает тратить время на бесконечное восстановление без ясной точки остановки и без явного ownership transfer.

### Required controls
Минимум:
- `max_attempts`
- `blocked_reason`
- `owner_for_decision`
- `escalation trigger`
- `retry budget`

### Operating rule
Если bounded unit не укладывается в budget, он обязан:
- либо поднять `BLOCKED`,
- либо вернуть decision back to owner,
- либо перейти в заранее определённый escalation path.

---

## Baseline Summary

На текущем этапе Frame стоит строить вокруг пяти опорных решений:
1. `main` — thin orchestrator.
2. Handoff — единый контракт `ACK / DONE / BLOCKED`.
3. Memory — слой дистилляции, а не архив чата.
4. Routing — детерминированный и topic-aware.
5. Длинные контуры — только с bounded retry/escalation budgets.

Это не полный architecture spec, а стартовый baseline, который задаёт operating shape системы.

---

## Next steps

### A. Handoff Spec v1
Собрать короткий spec для:
- status semantics (`ACK / DONE / BLOCKED`)
- required fields
- artifact anchors
- owner transitions
- blocked-handling rules

### B. Routing / Ownership Map v1
Собрать карту:
- work type -> lane
- lane -> owner
- lane -> durable state
- lane -> completion surface
- lane -> escalation path

### C. Memory Distillation Cadence
Определить:
- когда distill делать,
- какие события обязательны для записи,
- какие surfaces считаются durable memory,
- кто отвечает за перенос lessons/patterns/decisions

### D. Retry / Escalation Budget Policy v1
Определить:
- какие контуры имеют bounded retry,
- стандартные budget classes,
- когда unit обязан поднять `BLOCKED`,
- когда решение возвращается человеку или верхнему orchestrator layer

---

## Non-goals for this baseline

Этот документ пока **не** пытается:
- описать полный internal API Frame;
- зафиксировать конкретную реализацию subagent runtime;
- задавать окончательную storage architecture;
- решать все вопросы scheduling, memory schemas и UI surfaces.

Его цель уже: зафиксировать shape of operation, чтобы следующие документы собирались поверх одного каркаса.
