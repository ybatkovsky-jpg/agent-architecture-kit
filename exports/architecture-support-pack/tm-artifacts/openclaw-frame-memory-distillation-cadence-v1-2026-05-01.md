# OpenClaw Frame Memory Distillation Cadence v1

Date: 2026-05-01
Status: draft
Depends on:
- `task-manager/artifacts/openclaw-frame-architecture-baseline-v1-2026-05-01.md`
- `task-manager/artifacts/openclaw-frame-handoff-spec-v1-2026-05-01.md`
- `task-manager/artifacts/openclaw-frame-routing-ownership-map-v1-2026-05-01.md`
- `task-manager/artifacts/openclaw-frame-retry-escalation-budget-policy-v1-2026-05-01.md`
Scope: минимальный operating cadence для перевода решений, паттернов и blockers из chat/execution traces в durable memory surfaces

## Purpose

Закрыть типичный разрыв между "мы уже поняли что-то важное" и "это осталось жить только в хвосте чата / execution trace".

Memory distillation cadence нужен, чтобы Frame сохранял не весь разговор подряд, а именно то, что улучшает последующие решения:
- decisions
- patterns
- anti-patterns
- blockers
- operating conventions
- stable references to important artifacts

Cadence v1 задаёт что, когда, куда и кем должно быть дистиллировано.

---

## Core principle

### Rule 1: Memory is selective, not exhaustive
В durable memory попадает не «всё подряд», а только то, что меняет future execution quality.

### Rule 2: Distillation must be event-driven
Нельзя полагаться только на "потом когда-нибудь подведём итоги". У memory должны быть явные триггеры.

### Rule 3: Durable memory must outlive chat reconstruction
Если следующий bounded unit не сможет надёжно восстановить lesson/decision без перечитывания длинной переписки, значит дистилляция не сделана.

---

## What counts as distill-worthy

Ниже — базовые категории, которые должны переходить в durable surfaces.

## 1. Decisions
Что система или человек уже решил и не хочет каждый раз переоткрывать заново.

Examples:
- архитектурный выбор
- routing convention
- approval rule
- naming or ownership rule
- accepted baseline / spec direction

## 2. Patterns
Что доказало свою полезность и должно повторяться дальше.

Examples:
- successful workflow slice
- good artifact structure
- working execution pattern
- proven bounded operating move

## 3. Anti-patterns / failure lessons
Что уже сломалось или дало плохой outcome и не должно теряться.

Examples:
- broad/noisy search instead of focused path
- fake done without durable anchor
- endless retries without budget
- storing critical meaning only in chat

## 4. Blockers with reuse value
Не любой blocker, а такой, который вероятно повторится или важен для future routing.

Examples:
- approval boundary
- known missing capability
- runtime constraint
- permission gap

## 5. Durable references
Ссылки на артефакты, которые стали важными опорными объектами.

Examples:
- architecture baseline doc
- handoff spec
- routing map
- instrumentation artifact

---

## What should NOT be distilled by default

### 1. Raw execution chatter
Промежуточные мысли, которые не дают reusable signal.

### 2. Full conversation transcripts
История чата сама по себе не является distilled memory.

### 3. Every minor step
Если событие не изменяет operating model или future decisions, его не надо тянуть в durable memory.

### 4. Temporary noise
Случайные transient errors без reuse value не должны засорять memory layer.

---

## Distillation triggers

Frame v1 использует 5 основных trigger categories.

## Trigger A — `decision accepted`
Когда:
- принят архитектурный выбор;
- зафиксирован новый operating rule;
- принято решение по маршрутизации / ownership / approval.

Action:
- записать decision в durable artifact / memory surface.

---

## Trigger B — `bounded slice completed with reusable lesson`
Когда:
- bounded unit завершился и дал lesson/pattern worth reusing.

Action:
- зафиксировать pattern или anti-pattern.

---

## Trigger C — `blocked with systemic meaning`
Когда:
- `BLOCKED` отражает не разовую мелочь, а границу, которая вероятно повторится.

Action:
- записать blocker class / boundary rule / escalation lesson.

---

## Trigger D — `new canonical artifact created`
Когда:
- создан baseline/spec/map/policy/doc, который становится reference point.

Action:
- записать durable reference и его роль.

---

## Trigger E — `session / workstream closure`
Когда:
- завершён заметный кусок работы;
- есть риск потерять контекст при переходе к новой ветке.

Action:
- сделать короткую distillation summary вместо надежды на chat reconstruction.

---

## Cadence layers

Frame v1 использует 3 уровня cadence.

## Layer 1 — immediate distillation
### When
Сразу после значимого trigger event.

### Goal
Не потерять свежее решение/lesson.

### Typical outputs
- короткая task note
- artifact reference entry
- memory note
- handoff summary with reusable lesson

### Use for
- accepted decisions
- systemic blockers
- important patterns
- canonical artifacts

---

## Layer 2 — end-of-slice distillation
### When
В конце bounded execution slice или явно закрытого блока работы.

### Goal
Собрать в компактную форму то, что иначе останется размазанным по trace.

### Typical outputs
- task artifact note
- daily memory note
- pattern/lesson summary

### Use for
- technical investigations
- document-building sequences
- completed analysis branches

---

## Layer 3 — periodic consolidation
### When
Периодически, не на каждом микро-событии.

### Goal
Поднимать устойчивые решения и паттерны из daily/working notes в более стабильные reference surfaces.

### Typical outputs
- curated memory updates
- cleaned decision list
- consolidated pattern register
- updated architecture references

### Use for
- mature patterns
- repeated blockers
- stable conventions

---

## Durable memory surfaces v1

Frame v1 различает несколько уровней durable memory.

## Surface 1 — artifact-level memory
Назначение:
- сохранить смысл рядом с produced artifact.

Examples:
- architecture baseline docs
- specs
- maps
- policy docs

Use when:
- сам артефакт already is the memory anchor.

---

## Surface 2 — task / handoff memory
Назначение:
- зафиксировать bounded result, blocker, lesson, next step.

Examples:
- handoff file
- task artifact note
- bounded run summary

Use when:
- lesson относится к конкретному work unit.

---

## Surface 3 — daily / working memory
Назначение:
- хранить свежие distilled события дня без немедленного переноса в curated long-term layer.

Use when:
- событие важно, но ещё не ясно, станет ли оно устойчивым правилом.

---

## Surface 4 — curated long-term memory
Назначение:
- сохранить уже подтверждённые decisions, patterns и conventions, которые должны переживать отдельные сессии и ветки.

Use when:
- сигнал уже доказал свою стабильную ценность.

---

## Ownership for distillation

### `main-orchestrator`
Ответственен за:
- final framing distilled meaning;
- перенос решений из execution outcomes в user/system-visible form;
- фиксацию closure summary.

### `bounded-execution`
Ответственен за:
- локальные reusable lessons;
- technical blocker summaries;
- artifact anchors and factual result notes.

### `artifact-production`
Ответственен за:
- making artifact self-describing enough to serve as durable memory anchor.

### `human-decision`
Не обязан сам делать дистилляцию, но human decisions должны быть переведены в durable note/main summary.

### `background-observation`
Ответственен за:
- observation result summary;
- evidence capture;
- escalation-worthy signal notes.

---

## Minimal distillation contract

Каждая distilled memory entry v1 должна по возможности отвечать хотя бы на 4 вопроса:
- `what happened`
- `why it matters`
- `where the anchor is`
- `what should change next time`

### Minimal fields
- `type` (`decision`, `pattern`, `anti-pattern`, `blocker`, `artifact-reference`)
- `summary`
- `anchor`
- `reuse_value`

### Recommended fields
- `scope`
- `source_work_unit`
- `owner`
- `next_time_rule`
- `confidence`

---

## Distillation heuristics

### Distill immediately if
- решение likely to be reused;
- blocker reveals system boundary;
- artifact becomes canonical reference;
- repeated confusion was just resolved.

### Delay to periodic consolidation if
- lesson may be one-off;
- pattern still feels provisional;
- signal exists but is not yet stable enough for curated memory.

### Do not distill if
- signal is pure noise;
- content has no future routing/decision value;
- information is already captured adequately by a stronger canonical artifact.

---

## Anti-patterns

### 1. Archive everything
Пытаться превратить durable memory в полный архив чата.

### 2. Distill nothing until the end
Надеяться, что потом всё восстановится из истории.

### 3. Artifact without memory meaning
Создать документ, но не зафиксировать, почему он важен и что он теперь canonically anchors.

### 4. Relearn the same lesson
Несколько раз проходить через один и тот же вывод, потому что он так и не был distilled.

### 5. Promote unstable noise too early
Слишком рано записывать временный сигнал как долгосрочное правило.

---

## Minimal acceptance criteria for Cadence v1

Cadence считается достаточным для v1, если:
- значимые decisions/patterns/blockers/artifacts имеют явные triggers для distillation;
- у системы есть immediate, end-of-slice и periodic уровни дистилляции;
- понятно, какие surfaces использовать для какого типа сигнала;
- ownership for distillation не висит в воздухе;
- следующий bounded unit может опереться не только на chat tail, но и на durable distilled state.

---

## Resulting baseline stack status

С добавлением этого документа стартовый несущий набор Frame v1 закрыт:
- architecture baseline
- handoff spec
- routing / ownership map
- retry / escalation budget policy
- memory distillation cadence

Следующий шаг уже не «ещё один несущий базовый слой», а либо:
1. сведение этих документов в unified Frame v1 index / map,
2. либо переход к implementation-oriented layer,
3. либо backfill примеров/шаблонов под каждый spec.
