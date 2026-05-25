# OpenClaw Frame v1 Index / Map

Date: 2026-05-01
Status: draft
Scope: единая входная карта для baseline stack OpenClaw Frame v1

## Purpose

Собрать стартовый baseline stack Frame v1 в один entrypoint, чтобы:
- читать его как одну систему, а не как россыпь документов;
- быстро понимать, какой документ за что отвечает;
- видеть dependency order;
- понимать, откуда начинать чтение и куда идти дальше.

Этот index не заменяет исходные документы. Он даёт рабочую карту по ним.

---

## Baseline stack status

На 2026-05-01 стартовый baseline stack Frame v1 собран и состоит из 5 несущих документов:

1. `task-manager/artifacts/openclaw-frame-architecture-baseline-v1-2026-05-01.md`
2. `task-manager/artifacts/openclaw-frame-handoff-spec-v1-2026-05-01.md`
3. `task-manager/artifacts/openclaw-frame-routing-ownership-map-v1-2026-05-01.md`
4. `task-manager/artifacts/openclaw-frame-retry-escalation-budget-policy-v1-2026-05-01.md`
5. `task-manager/artifacts/openclaw-frame-memory-distillation-cadence-v1-2026-05-01.md`

Together they define the minimum operating layer of Frame v1.

---

## Reading order

### 1. Architecture baseline
Read first when you need the high-level model.

Document:
- `task-manager/artifacts/openclaw-frame-architecture-baseline-v1-2026-05-01.md`

Answers:
- what Frame is trying to be;
- what core architectural decisions already exist;
- what is in-scope for the first operating layer;
- what is intentionally a non-goal for now.

Core contribution:
- задаёт базовый shape системы.

---

### 2. Handoff spec
Read second when you need the minimum execution contract.

Document:
- `task-manager/artifacts/openclaw-frame-handoff-spec-v1-2026-05-01.md`

Answers:
- как bounded unit сообщает, что он взял работу, завершил её или упёрся;
- какие статусы разрешены;
- какие поля обязательны;
- что считается корректным `DONE` и корректным `BLOCKED`.

Core contribution:
- задаёт единый contract `ACK / DONE / BLOCKED`.

---

### 3. Routing / ownership map
Read third when you need to know where work should go.

Document:
- `task-manager/artifacts/openclaw-frame-routing-ownership-map-v1-2026-05-01.md`

Answers:
- какие execution lanes есть в системе;
- кто owner в каждом lane;
- где живёт durable state;
- куда возвращается `DONE` / `BLOCKED`.

Core contribution:
- превращает architecture + handoff в operating routing model.

---

### 4. Retry / escalation budget policy
Read fourth when you need stop conditions and loop control.

Document:
- `task-manager/artifacts/openclaw-frame-retry-escalation-budget-policy-v1-2026-05-01.md`

Answers:
- сколько попыток допустимо;
- когда retry valid;
- когда надо поднимать escalation;
- как не допускать silent infinite loops.

Core contribution:
- добавляет boundedness discipline к routing/execution.

---

### 5. Memory distillation cadence
Read fifth when you need continuity and learning surfaces.

Document:
- `task-manager/artifacts/openclaw-frame-memory-distillation-cadence-v1-2026-05-01.md`

Answers:
- что должно попадать в durable memory;
- когда это должно происходить;
- какие surfaces использовать;
- кто отвечает за distillation.

Core contribution:
- связывает execution outcomes с persistent learning layer.

---

## Dependency map

### Layer 1 — shape
- `architecture baseline`

### Layer 2 — execution contract
- `handoff spec`

### Layer 3 — routing and ownership
- `routing / ownership map`

### Layer 4 — boundedness and escalation
- `retry / escalation budget policy`

### Layer 5 — continuity and learning
- `memory distillation cadence`

In short:
- baseline says **what kind of system this is**;
- handoff spec says **how units report state transitions**;
- routing map says **where work goes and who owns it**;
- budget policy says **when work must stop or escalate**;
- memory cadence says **what must survive beyond the run**.

---

## One-line role of each document

### `openclaw-frame-architecture-baseline-v1-2026-05-01.md`
The system shape and first architectural commitments.

### `openclaw-frame-handoff-spec-v1-2026-05-01.md`
The minimum handoff contract for bounded work units.

### `openclaw-frame-routing-ownership-map-v1-2026-05-01.md`
The operating map of lanes, owners, state, and escalation.

### `openclaw-frame-retry-escalation-budget-policy-v1-2026-05-01.md`
The boundedness policy that prevents loops and hidden persistence.

### `openclaw-frame-memory-distillation-cadence-v1-2026-05-01.md`
The continuity layer that turns lessons into durable memory.

---

## How to use this stack in practice

## Case 1 — New architectural discussion
Read:
1. baseline
2. handoff spec
3. routing map

Because the immediate question is usually:
- what system shape are we protecting,
- what transition model already exists,
- where should the new concern live.

---

## Case 2 — New bounded execution flow
Read:
1. handoff spec
2. routing map
3. budget policy

Because the immediate question is usually:
- how the unit enters/leaves execution,
- who owns it,
- when it must stop or escalate.

---

## Case 3 — Designing continuity / learning behavior
Read:
1. memory cadence
2. handoff spec
3. routing map

Because the immediate question is usually:
- what outcomes should be distilled,
- where the anchors come from,
- who must perform the distillation.

---

## Case 4 — Debugging ambiguous behavior
Read:
1. routing map
2. budget policy
3. handoff spec

Typical ambiguity classes:
- work stayed in `main` too long;
- owner became unclear;
- retries continued without budget;
- blocked state did not escalate correctly.

---

## Current canonical claims of Frame v1

By this point, the stack establishes the following claims:

1. `main` is a thin orchestrator, not the default execution sink.
2. bounded work should route early into explicit lanes.
3. every meaningful unit needs a handoff outcome.
4. `DONE` requires a durable anchor.
5. `BLOCKED` is a legitimate and necessary outcome.
6. retries are budgeted, not ambient.
7. observation must have stop conditions.
8. human authority boundaries must be explicit.
9. memory is distilled selectively, not archived blindly.
10. canonical artifacts are part of the memory system, not just byproducts.

---

## Non-goals of this index

This index does not yet provide:
- implementation mappings to exact runtime modules;
- wire formats for every internal surface;
- template packs for every handoff or memory object;
- end-to-end worked examples across all lanes.

Those are next-layer deliverables, not missing parts of the baseline stack.

---

## Recommended next moves

Теперь после baseline stack есть три естественных направления.

## Direction A — implementation mapping
Сделать документ вида:
- `OpenClaw Frame v1 implementation mapping`

Goal:
- привязать baseline stack к реальным runtime surfaces, task-manager artifacts, handoff files, session behavior и tooling.

Best when:
- нужно переходить от architecture docs к практической сборке.

---

## Direction B — templates pack
Сделать набор шаблонов:
- handoff template
- blocked package template
- routing card template
- memory distillation entry template

Goal:
- превратить spec stack в повторяемую operator practice.

Best when:
- нужно быстро начать пользоваться baseline без дополнительного изобретения форматов.

---

## Direction C — worked examples pack
Сделать 3–5 concrete walkthroughs:
- bounded technical investigation
- artifact production flow
- approval-gated flow
- background observation flow
- distillation after completion

Goal:
- проверить baseline stack на реальных сценариях.

Best when:
- нужно увидеть, где stack still too abstract.

---

## Recommended next step

Если идти самым правильным bounded порядком, следующим шагом лучше делать:
- **Direction B — templates pack**

Почему:
- baseline stack уже собран;
- unified index уже есть;
- теперь нужен bridge от architecture/spec к repeatable usage;
- шаблоны дадут immediate operational leverage без premature implementation sprawl.
