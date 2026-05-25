# OpenClaw Frame — current architecture and improvement plan

Date: 2026-05-02
Status: working note
Scope: краткая опорная записка о текущей действующей архитектуре Frame и ближайшем плане улучшений

## 1. Current architecture

Сейчас у нас уже собран не просто набор идей, а оформленный **OpenClaw Frame v1 baseline stack**.

### 1.1 Main = thin orchestrator
`main` у нас задуман и зафиксирован как:
- точка входа;
- orchestration layer;
- decision surface;
- короткая поверхность возврата результата.

`main` **не** должен быть default execution sink для длинной, stateful или многослойной работы.

### 1.2 Real work routes into explicit lanes
Самостоятельная bounded-работа должна как можно раньше маршрутизироваться в явные execution lanes:
- `main-orchestrator`
- `bounded-execution`
- `artifact-production`
- `human-decision`
- `background-observation`

Это убирает ambiguity вокруг того:
- где работа реально выполняется;
- кто ей владеет;
- где живёт состояние;
- куда возвращается результат.

### 1.3 Unified handoff contract
Для переходов между контурами у нас зафиксирован единый минимальный handoff contract:
- `ACK`
- `DONE`
- `BLOCKED`

Смысл:
- `ACK` — execution ownership принято;
- `DONE` — bounded responsibility завершена и есть durable result anchor;
- `BLOCKED` — локальное продолжение больше не оправдано, нужен явный decision owner.

### 1.4 Explicit ownership and escalation
В текущей архитектуре ownership и escalation должны быть явными:
- кто execution owner;
- кто decision owner;
- куда уходит `BLOCKED`;
- куда возвращается `DONE`.

Это защищает систему от полуживых состояний, где работа как будто идёт, но никто не понимает, кто теперь отвечает.

### 1.5 Retry is budgeted
Retry больше не трактуется как эмоциональное "ну давай ещё попробуем".

Зафиксирован принцип:
- **no unbounded persistence by default**

Default mode:
- `initial attempt = 1`
- `automatic retries = 0`

Budget classes:
- `single-shot`
- `light-retry`
- `timed-observation`
- `human-gated`

Это защищает архитектуру от:
- бесконечных retry-loop;
- скрытых зависаний;
- фонового бесконечного ожидания без stop condition.

### 1.6 Memory is distilled, not archival
Memory layer у нас понимается как selective continuity layer.

В durable memory должны попадать:
- decisions;
- patterns;
- anti-patterns;
- blockers with reuse value;
- durable references.

То есть память служит не складом chat history, а слоем, который улучшает future execution quality.

### 1.7 Operational bridge already exists
Архитектура уже существует не только как набор принципов, но и как operator stack:
- baseline docs;
- unified index;
- templates pack;
- worked examples pack.

То есть Frame v1 уже выражен:
- как архитектурный слой;
- как operating rules;
- как reusable forms;
- как pressure-tested example scenarios.

### 1.8 ХеРТИК as operating pattern
Отдельно зафиксирован рабочий термин:
- `ХеРТИК = handoff + resume-trigger / isolated continuation`

Смысл паттерна:
- если `main` перегрет;
- если execution-heavy ветку нельзя разумно тащить через текущий чат;
- нужно делать handoff;
- затем поднимать isolated continuation как следующий bounded unit.

Это уже не просто словесная идея, а один из ключевых operating moves в Frame.

---

## 2. What is already assembled

На текущий момент собран следующий пакет артефактов:

1. `task-manager/artifacts/openclaw-frame-architecture-baseline-v1-2026-05-01.md`
2. `task-manager/artifacts/openclaw-frame-handoff-spec-v1-2026-05-01.md`
3. `task-manager/artifacts/openclaw-frame-routing-ownership-map-v1-2026-05-01.md`
4. `task-manager/artifacts/openclaw-frame-retry-escalation-budget-policy-v1-2026-05-01.md`
5. `task-manager/artifacts/openclaw-frame-memory-distillation-cadence-v1-2026-05-01.md`
6. `task-manager/artifacts/openclaw-frame-v1-index-map-2026-05-01.md`
7. `task-manager/artifacts/openclaw-frame-v1-templates-pack-2026-05-01.md`
8. `task-manager/artifacts/openclaw-frame-v1-worked-examples-pack-2026-05-01.md`

Этот пакет уже можно считать **coherent Frame v1 architecture package**.

---

## 3. Current strengths

### 3.1 We now have a clean conceptual center
Понятно, чем является `main`, а чем — не является.

### 3.2 We have a shared language for execution transitions
`ACK / DONE / BLOCKED` уже дают достаточно сильный минимальный state-transition vocabulary.

### 3.3 Routing is no longer implicit
У работы теперь есть явные lanes и owner-model.

### 3.4 Loop-control discipline exists
Retry и observation больше не остаются бесформенными.

### 3.5 Learning/continuity is built in
Memory distillation уже признана частью архитектуры, а не побочным занятием.

### 3.6 High-context continuation has a named pattern
`ХеРТИК` даёт важный practical move для сохранения тонкого `main`.

---

## 4. Current limitations

Несмотря на хорошую архитектурную плотность, есть несколько ещё не закрытых слоёв.

### 4.1 Implementation mapping is not yet formalized
Пока мы хорошо описали **что** хотим, но ещё не до конца формализовали:
- где именно каждый слой живёт в реальном OpenClaw runtime;
- как это маппится на `sessions`, `subagents`, `handoffs`, `task-manager`, `artifacts`, background jobs и tool surfaces.

### 4.2 ХеРТИК is conceptually strong but not yet fully runtime-bound
Паттерн очень удачный, но ещё требует чёткого runtime-mapping:
- как exactly создаётся handoff;
- что именно считается `resume-trigger`;
- как поднимается isolated continuation;
- как результат возвращается в `main`.

### 4.3 Canonical operator surfaces still need stricter mapping
Нужно точнее закрепить, где по умолчанию живут:
- handoff files;
- blocked packages;
- routing cards;
- memory entries;
- continuation artifacts.

### 4.4 Chained continuation recovery is still underexplored
Одиночные bounded flows уже проверены, но ещё не до конца проверены:
- цепочки continuation;
- повторные handoff after partial progress;
- возврат из `BLOCKED` в новый bounded attempt;
- многошаговые escalation/retry/resume paths.

---

## 5. Improvement plan

### Priority 1 — Implementation mapping
Следующий главный шаг:
- сделать **implementation mapping**

Нужно связать baseline stack с реальными механизмами OpenClaw:
- `main session`
- `sessions`
- `subagents`
- `handoffs`
- `task-manager`
- `artifacts`
- `background observation`
- relevant tool surfaces

Это будет переход от architecture/spec layer к practical system embedding.

### Priority 2 — Runtime binding for ХеРТИК
Нужно превратить `ХеРТИК` из сильного operating concept в repeatable runtime path.

Надо описать:
- creation path for handoff;
- shape of resume-trigger;
- isolated continuation spawn path;
- return path into `main`.

### Priority 3 — Canonical surface mapping
Нужно жёстче определить default storage and anchor policy:
- где лежит handoff;
- где лежит blocked package;
- где лежит routing card;
- где фиксируется distillation entry;
- какие surfaces считаются canonical по умолчанию.

### Priority 4 — Semi-automation opportunities
После mapping можно переходить к полуавтоматизации:
- auto-suggest routing card;
- auto-generate handoff skeleton;
- auto-detect high-context branch and suggest `ХеРТИК`;
- auto-distill key lesson after bounded completion;
- auto-escalate on budget exhaustion.

### Priority 5 — Pressure-test on real live flows
После implementation mapping архитектуру нужно прогонять на реальных рабочих сценариях:
- technical investigations;
- approval-gated mutations;
- background observation tasks;
- artifact-production tasks;
- high-context continuations.

Это покажет, где архитектура уже operationally solid, а где остаётся слишком paper-native.

---

## 6. Short summary

Текущая действующая архитектура OpenClaw Frame такая:
- `main` = thin orchestrator;
- bounded work уходит в explicit lanes;
- transitions выражаются через `ACK / DONE / BLOCKED`;
- retry и observation bounded через budget policy;
- memory selective and distilled;
- high-context continuation оформляется через `ХеРТИК`.

Главный следующий этап улучшений:
- implementation mapping;
- runtime-binding of `ХеРТИК`;
- canonical surface policy;
- semi-automation;
- real-world pressure-testing.

---

## 7. Recommended next document

Следующий самый логичный артефакт:
- `OpenClaw Frame v1 implementation mapping`

Потому что baseline stack уже достаточно зрелый, и следующий вопрос теперь не про принципы, а про точную посадку на реальный execution contour.
