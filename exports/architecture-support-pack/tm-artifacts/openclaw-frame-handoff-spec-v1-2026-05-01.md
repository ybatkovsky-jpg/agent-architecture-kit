# OpenClaw Frame Handoff Spec v1

Date: 2026-05-01
Status: draft
Depends on: `task-manager/artifacts/openclaw-frame-architecture-baseline-v1-2026-05-01.md`
Scope: минимальный handoff contract для bounded execution units и cross-lane coordination в OpenClaw Frame

## Purpose

Определить короткий и единый handoff contract, чтобы любой bounded execution unit оставлял после себя не просто «что-то произошло», а понятный transition of responsibility:
- кто взял работу,
- что именно сделал,
- где результат,
- где теперь owner,
- что делать дальше,
- почему работа застряла, если она не завершена.

Spec v1 специально узкий. Его задача — не покрыть все возможные workflow, а дать рабочий минимум для Frame.

---

## Core statuses

Frame v1 использует три базовых handoff-статуса:
- `ACK`
- `DONE`
- `BLOCKED`

### 1. `ACK`
Meaning:
- bounded unit принял работу в исполнение;
- ownership выполнения временно перешёл в execution lane / runtime / subagent;
- работа ещё не завершена, но больше не находится в неясном состоянии.

Use when:
- работа взята в isolated run;
- создан bounded child unit;
- orchestration передал execution в другой lane;
- нужно явно показать, что задача не потерялась.

`ACK` не означает, что есть результат. Он означает, что теперь есть owner execution.

### 2. `DONE`
Meaning:
- bounded unit завершил свою ответственность;
- есть конкретный result anchor;
- понятно, кто следующий owner и что является завершением именно этого unit.

Use when:
- создан артефакт;
- получен завершённый output;
- сделан decision package;
- выполнен bounded slice с явной границей done.

`DONE` не обязательно означает «весь большой проект завершён». Он означает, что завершён именно данный work unit.

### 3. `BLOCKED`
Meaning:
- bounded unit не может продолжать работу в рамках допустимого budget / authority / information set;
- причина остановки сформулирована явно;
- указан owner следующего decision.

Use when:
- не хватает доступа / данных / разрешения;
- достигнут retry budget;
- обнаружен ambiguity, который нельзя безопасно разрешить локально;
- дальнейшее продолжение без decision извне будет wasteful или unsafe.

`BLOCKED` не означает failure in general. Это корректное завершение bounded attempt с передачей decision наверх или в сторону.

---

## Required fields

Каждый handoff v1 должен содержать минимальный набор полей.

### Required
- `status`
- `work_unit_id`
- `owner`
- `scope`
- `summary`
- `next_action`

### Conditionally required
- `result_anchor` — обязательно для `DONE`
- `blocked_reason` — обязательно для `BLOCKED`
- `owner_for_decision` — обязательно для `BLOCKED`

### Recommended
- `parent_id`
- `lane`
- `created_by`
- `attempt`
- `artifact_paths`
- `decision_needed`
- `resume_condition`

---

## Field semantics

### `status`
Одно из:
- `ACK`
- `DONE`
- `BLOCKED`

### `work_unit_id`
Идентификатор bounded unit, по которому можно однозначно соотнести handoff с execution slice.

Examples:
- task id
- child run id
- compound work unit id

### `owner`
Кто сейчас владеет текущим состоянием work unit.

Examples:
- `main`
- `subagent:<label>`
- `runtime:<lane>`
- `human:<name>`

### `scope`
Короткое описание того, какой bounded кусок работы покрывает handoff.

Examples:
- `inspect session-store lock critical section`
- `produce handoff spec v1 draft`
- `run weekly analyst slice`

### `summary`
Короткий factual summary handoff-состояния.
Должен быть достаточно коротким, чтобы быстро прочитать, и достаточно конкретным, чтобы не терять смысл.

### `next_action`
Что должно происходить следующим шагом для этого work unit или его parent flow.

### `result_anchor`
Ссылка на артефакт, output surface или иной durable anchor результата.

Examples:
- path to artifact
- task handoff file
- generated package
- specific surfaced output

### `blocked_reason`
Явная причина, почему bounded unit остановился.
Не общая фраза вроде "не получилось", а operationally useful blocker.

### `owner_for_decision`
Кто должен принять следующее решение, если unit завершился как `BLOCKED`.

Examples:
- `human:Юрий`
- `main`
- `operator`
- `routing-layer`

---

## Canonical handoff shapes

### `ACK` shape
```yaml
status: ACK
work_unit_id: <id>
owner: <execution-owner>
scope: <bounded-scope>
summary: <accepted into execution>
next_action: <what this unit will now do>
```

### `DONE` shape
```yaml
status: DONE
work_unit_id: <id>
owner: <current-owner-after-completion>
scope: <bounded-scope>
summary: <what was completed>
result_anchor: <artifact/output anchor>
next_action: <what the parent flow or next owner should do>
```

### `BLOCKED` shape
```yaml
status: BLOCKED
work_unit_id: <id>
owner: <owner at stop point>
scope: <bounded-scope>
summary: <what was attempted and where it stopped>
blocked_reason: <explicit blocker>
owner_for_decision: <who must decide>
next_action: <what should happen after decision>
```

---

## Owner transition rules

### Rule 1: `ACK` transfers execution ownership
Когда unit выдаёт `ACK`, должно быть понятно, что execution ownership уже не висит в воздухе.

Expected effect:
- раньше owner был orchestrator / caller;
- после `ACK` owner execution — bounded worker / lane.

### Rule 2: `DONE` closes bounded responsibility
После `DONE` этот unit не должен оставаться в полу-живом ambiguous state.

Expected effect:
- либо owner возвращается parent orchestrator;
- либо ownership переходит в next lane;
- либо result handed to human-facing layer.

### Rule 3: `BLOCKED` transfers decision ownership
Если unit blocked, он не должен продолжать silently retry.

Expected effect:
- execution stops;
- handoff указывает, кто принимает следующее решение;
- parent flow получает явный escalation point.

---

## Result anchor rules

### Rule A
Если статус `DONE`, результат должен быть anchored outside pure chat memory.

Allowed anchors:
- file artifact
- durable task note / handoff file
- generated package path
- explicit output surface with stable reference

### Rule B
Если результата как durable object нет, `DONE` использовать нельзя.
В таком случае нужен либо:
- `ACK` (если работа ещё идёт),
- либо `BLOCKED` (если работа не может быть завершена корректно).

### Rule C
Chat summary может сопровождать handoff, но не заменяет durable anchor.

---

## Blocked-handling rules

### Rule 1
`BLOCKED` поднимается не когда «устали», а когда есть явная operational boundary:
- authority boundary
- missing prerequisite
- retry budget exhausted
- unresolved ambiguity requiring decision
- unsafe continuation

### Rule 2
Каждый `BLOCKED` обязан иметь:
- конкретную причину;
- конкретного decision owner;
- конкретный next action.

### Rule 3
`BLOCKED` должен останавливать silent loops.
После `BLOCKED` повторная попытка допустима только как новый bounded attempt или после нового decision/input.

---

## Anti-patterns

### 1. Fake `DONE`
Писать `DONE`, когда есть только разговорное summary без durable result anchor.

### 2. Ambiguous `ACK`
Писать `ACK`, но не обозначать, кто теперь owner execution.

### 3. Soft `BLOCKED`
Писать vague blocker вроде:
- `нужно подумать`
- `что-то пошло не так`
- `пока не получилось`

Такие формулировки не годятся для orchestration.

### 4. Hidden retries after `BLOCKED`
Нельзя поднимать `BLOCKED`, а потом продолжать тот же цикл молча, будто блокировки не было.

### 5. Chat-only closure
Нельзя считать короткое сообщение в чате полноценным handoff, если от него нельзя перейти к следующему шагу без восстановления контекста из истории.

---

## Minimal examples

### Example: `ACK`
```yaml
status: ACK
work_unit_id: task-275-instrumentation-slice
owner: subagent:code-trace
scope: add minimal session-store lock timing instrumentation
summary: bounded execution slice accepted into isolated code path inspection and patching
next_action: patch installed dist file and verify syntax
```

### Example: `DONE`
```yaml
status: DONE
work_unit_id: task-275-instrumentation-slice
owner: main
scope: add minimal session-store lock timing instrumentation
summary: gated timing instrumentation added to session-store lock/write path and syntax-checked
result_anchor: /home/openclaw/.npm-global/lib/node_modules/openclaw/dist/store-DFXcceZJ.js
next_action: enable trace via gateway env and capture runtime lines
```

### Example: `BLOCKED`
```yaml
status: BLOCKED
work_unit_id: task-275-runtime-proof-slice
owner: main
scope: capture session-store lock hold telemetry from live gateway
summary: code instrumentation exists, but live observation is paused pending service env mutation approval
blocked_reason: enabling trace requires live gateway env change and restart
owner_for_decision: human:Юрий
next_action: approve env change or defer runtime proof branch
```

---

## Acceptance criteria for Handoff Spec v1

Этот spec считается достаточным для v1, если:
- любой bounded unit может завершиться через `ACK`, `DONE` или `BLOCKED` без дополнительных локальных выдумок;
- по handoff видно current owner и next owner / decision owner;
- `DONE` всегда имеет durable anchor;
- `BLOCKED` не оставляет ambiguity о том, почему работа остановилась;
- spec достаточно короткий, чтобы реально использоваться, а не только «быть правильным на бумаге».

---

## Non-goals

Spec v1 пока не фиксирует:
- wire format для всех внутренних API;
- transport-specific envelope details;
- полную state machine всех execution lanes;
- UI rendering details для handoff surfaces.

Это intentional: сначала нужен operating contract, потом его детальная техническая упаковка.
