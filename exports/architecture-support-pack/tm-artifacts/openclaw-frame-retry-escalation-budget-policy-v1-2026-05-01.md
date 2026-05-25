# OpenClaw Frame Retry / Escalation Budget Policy v1

Date: 2026-05-01
Status: draft
Depends on:
- `task-manager/artifacts/openclaw-frame-architecture-baseline-v1-2026-05-01.md`
- `task-manager/artifacts/openclaw-frame-handoff-spec-v1-2026-05-01.md`
- `task-manager/artifacts/openclaw-frame-routing-ownership-map-v1-2026-05-01.md`
Scope: минимальная policy для bounded retries, stop conditions и escalation budgets в OpenClaw Frame

## Purpose

Запретить silent infinite loops и неявные зависания в Frame.

Любой bounded execution unit, background observation или orchestration slice должен иметь заранее понятную границу:
- сколько раз он пытается продолжать работу;
- когда он обязан остановиться;
- когда он поднимает `BLOCKED`;
- кому он передаёт decision ownership.

Policy v1 задаёт operating rules, а не низкоуровневую реализацию retry engine.

---

## Core principle

### Rule 1: No unbounded persistence by default
В Frame нельзя считать нормой бесконечное «ещё раз попробуем».

Если unit не имеет явно заданного retry budget, он должен считаться bounded single-attempt work unit.

### Rule 2: Retries are a budget, not a vibe
Retry — это не эмоциональное решение исполнителя, а заранее определённый operational budget.

### Rule 3: Escalation is a first-class outcome
Если budget исчерпан или блокер не локален, правильный следующий шаг — escalation, а не замаскированное продолжение.

---

## Budget vocabulary

### `attempt`
Одна завершённая bounded попытка выполнить work unit или его clearly-scoped sub-step.

### `retry budget`
Максимальное число повторных попыток в рамках одного ownership cycle без внешнего decision/reset.

### `escalation trigger`
Условие, при котором unit обязан прекратить локальные попытки и передать decision ownership наружу.

### `stop condition`
Явное условие завершения попытки как `DONE`, `BLOCKED` или abandoned/restarted under new unit.

---

## Default policy

### Default budget
Если иное не указано, для bounded unit действует:
- `initial attempt = 1`
- `automatic retries = 0`

То есть default mode — **single-attempt bounded execution**.

### Why
Это предотвращает скрытое раздувание работы и принуждает систему явно решать, где retries действительно нужны.

---

## Budget classes v1

Frame v1 вводит 4 базовых budget classes.

## Class A — `single-shot`
### Intent
Для большинства bounded analysis / drafting / inspection slices.

### Policy
- `attempts_total_max = 1`
- auto-retry: no
- on failure/blocker: immediate `BLOCKED` or explicit reroute

### Use for
- narrow code inspection
- one-pass document drafting
- single bounded synthesis
- explicit review slice

### Why
Повтор обычно не даёт качественно нового результата без смены input, route или owner.

---

## Class B — `light-retry`
### Intent
Для операций, где локальный transient failure reasonably possible.

### Policy
- `attempts_total_max = 2 or 3`
- retries allowed only for clearly local/transient issues
- must stop after budget exhaustion with `BLOCKED`

### Use for
- flaky file operation
- short command retry
- transient parsing/load hiccup
- short observation sample that may miss first signal

### Constraints
- retries should be fast
- no indefinite waiting between tries
- no semantic drift between retries

---

## Class C — `timed-observation`
### Intent
Для observation lanes, где важен не count-only budget, а bounded watch window.

### Policy
- define `max_observation_window`
- define `sample cadence`
- define `stop condition`
- if no signal by deadline -> `DONE(no signal)` or `BLOCKED`, depending on task contract

### Use for
- telemetry capture
- runtime observation
- waiting for exact evidence
- background monitoring slice

### Constraints
- observation must have explicit end
- silence cannot count as perpetual progress

---

## Class D — `human-gated`
### Intent
Для контуров, где дальше нельзя двигаться без approval, authority, access или explicit preference.

### Policy
- local execution may prepare decision package
- once human gate is reached, further retries are not allowed without new human input
- outcome must become `BLOCKED` or explicit wait state owned by human-decision lane

### Use for
- approval needed
- secret/access missing
- external action needed
- unresolved architectural choice requiring preference

### Constraints
- do not keep reattempting locally after authority boundary is known

---

## What counts as a valid retry

Retry допустим только если проблема:
- локальна;
- потенциально transient;
- не требует новой архитектурной интерпретации;
- не требует нового человеческого решения;
- не требует существенного расширения scope.

### Valid retry examples
- transient file write collision
- temporary process start hiccup
- short-lived lock contention
- one more telemetry sample within predefined observation window

### Invalid retry examples
- снова думать ту же архитектурную мысль без нового input
- снова пробовать без нужного permission
- снова запускать path, который already proved semantically blocked
- бесконечно ждать “может сейчас появится сигнал” без observation budget

---

## Escalation triggers

Unit обязан поднимать escalation, если происходит хотя бы одно из следующих:

### 1. Retry budget exhausted
Все допустимые попытки исчерпаны, а unit не достиг `DONE`.

### 2. Authority boundary hit
Нужен approval, доступ, секрет, решение или внешний action.

### 3. Information boundary hit
Ключевая информация отсутствует, и локально её достоверно получить нельзя.

### 4. Scope expansion detected
Чтобы продолжать, unit должен фактически превратиться в другую, более крупную задачу.

### 5. Risk boundary hit
Дальнейшее продолжение без нового решения unsafe, destructive или operationally unjustified.

### 6. Observation deadline reached
Фоновое наблюдение исчерпало допустимое окно и не может считать отсутствие сигнала бесконечным justification для продолжения.

---

## Required fields when a budget exists

Если unit работает не как pure single-shot, а с явным budget, handoff/relevant state должен знать минимум:
- `budget_class`
- `attempt`
- `attempts_total_max` or `max_observation_window`
- `escalation_trigger`
- `owner_for_decision` on exhaustion/block

### Recommended
- `retry_reason`
- `last_failure_class`
- `resume_condition`
- `next_allowed_action`

---

## Status rules tied to budget

### `ACK`
Может содержать implicit budget context, но сам по себе не означает право на бесконечные продолжения.

### `DONE`
Допустим, если unit достиг stop condition в рамках бюджета.

### `BLOCKED`
Обязателен, если:
- budget exhausted;
- authority boundary crossed;
- stop condition says no further local progress is justified.

---

## Lane-specific policy overlay

## `main-orchestrator`
Default budget class:
- `single-shot`

Why:
`main` не должен застревать в повторяющемся execution behavior.

Escalate when:
- route unclear after one serious pass;
- explicit human decision needed;
- bounded unit should be spawned instead of continuing in main.

---

## `bounded-execution`
Default budget class:
- `single-shot` or `light-retry`

Why:
bounded execution должен быть focused и не превращаться в скрытый endless workshop.

Escalate when:
- code path proves wider than scoped;
- local fixes exhausted;
- missing approval/access/data;
- expected artifact cannot be produced within class budget.

---

## `artifact-production`
Default budget class:
- `single-shot`

Why:
если durable artifact не удаётся собрать с первой bounded попытки, обычно нужен либо reroute, либо new slice, а не скрытый endless drafting.

Escalate when:
- artifact contract unclear;
- required inputs missing;
- production path turns into broader design problem.

---

## `human-decision`
Default budget class:
- `human-gated`

Why:
retry без нового human input здесь семантически бессмысленен.

Escalate when:
- human does not respond within outer process rules;
- decision must be deferred/reframed;
- another owner should take priority/risk decision.

---

## `background-observation`
Default budget class:
- `timed-observation`

Why:
фоновые контуры особенно склонны деградировать в бесконечное молчаливое ожидание.

Escalate when:
- observation window expired;
- no reliable signal source exists;
- signal requires action beyond observation scope.

---

## Canonical budget shapes

### Single-shot
```yaml
budget_class: single-shot
attempt: 1
attempts_total_max: 1
escalation_trigger: no-local-progress
```

### Light-retry
```yaml
budget_class: light-retry
attempt: 2
attempts_total_max: 3
escalation_trigger: retry-budget-exhausted
```

### Timed-observation
```yaml
budget_class: timed-observation
attempt: 1
max_observation_window: 30m
sample_cadence: 5m
escalation_trigger: observation-deadline-reached
```

### Human-gated
```yaml
budget_class: human-gated
attempt: 1
attempts_total_max: 1
escalation_trigger: waiting-for-human-decision
owner_for_decision: human:<name>
```

---

## Anti-patterns

### 1. Hidden continuation after failure
Попытка формально закончилась, но исполнитель продолжает её как будто budget не существовал.

### 2. Retry without classification
Никто не знает, почему retry вообще допустим.

### 3. Human gate treated as transient error
Отсутствие approval/permission ошибочно трактуется как что-то, что можно локально дорешать ещё одной попыткой.

### 4. Observation without deadline
Фоновый контур не имеет window и живёт бесконечно.

### 5. Scope creep disguised as retry
На самом деле unit уже делает новую работу, но всё ещё считается «той же попыткой».

---

## Minimal acceptance criteria for Policy v1

Policy считается достаточной для v1, если:
- default mode в системе — bounded single-attempt, а не hidden persistence;
- retries разрешены только в явных class-based contours;
- исчерпание budget ведёт к `BLOCKED` или явной эскалации;
- background observation не может жить бесконечно без stop window;
- human-gated contours не retry'ятся локально без нового решения.

---

## Next likely step

После этой policy логично собрать `Memory Distillation Cadence`, чтобы закрыть четвёртый несущий слой baseline и перестать хранить lessons/patterns только в execution/chat traces.
