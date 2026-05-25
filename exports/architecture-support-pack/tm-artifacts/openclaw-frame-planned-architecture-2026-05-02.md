# OpenClaw Frame — planned architecture

Date: 2026-05-02
Status: planning note
Scope: целевая планируемая архитектура OpenClaw Frame с учётом уже собранного baseline stack, evidence/review practice и следующего слоя architecture improvement

## 1. Core architectural shape

Планируемая архитектура строится вокруг нескольких жёстких принципов:
- `main` = thin orchestrator;
- самостоятельная bounded-работа рано уходит в явные execution lanes;
- каждый meaningful unit должен завершаться через `ACK`, `DONE` или `BLOCKED`;
- `DONE` требует durable anchor;
- review опирается на evidence, а не на narrative summary;
- retry и observation bounded policy-driven budget'ом;
- memory selective and distilled;
- improvement делается через evidence-backed modernization loop, а не через стихийное разрастание архитектуры.

---

## 2. Main layer

`main` остаётся:
- точкой входа;
- orchestration surface;
- decision surface;
- местом короткого возврата результата;
- местом human-gated архитектурных решений.

`main` не должен быть:
- default execution sink;
- длинным stateful execution-tail;
- местом хранения всей continuity;
- единственным носителем контекста.

---

## 3. Execution lane model

Планируемая архитектура закрепляет следующие основные lanes:
- `main-orchestrator`
- `bounded-execution`
- `artifact-production`
- `human-decision`
- `background-observation`

Дополнительно как next-layer может быть явно оформлен:
- `review / blind-judge lane`

Смысл:
- execution отделён от orchestration;
- production отделён от judgment;
- background work bounded по окну/дедлайну;
- decision authority не размывается.

---

## 4. Transition contract

Базовый переходный контракт остаётся минимальным и жёстким:
- `ACK` = execution ownership принято;
- `DONE` = bounded responsibility завершена и есть durable result anchor;
- `BLOCKED` = локальное продолжение больше не оправдано, есть явная причина и `owner_for_decision`.

Это должно быть общим языком переходов между слоями, сессиями и артефактами.

---

## 5. Handoff and continuation architecture

Планируемая архитектура усиливает handoff/continuation как отдельный несущий слой.

Ключевые правила:
- continuation не должен держаться только на chat tail;
- handoff должен иметь durable artifact form;
- resume должен опираться на explicit resume basis;
- review-gated continuation не должен auto-resume'иться;
- high-context branches по умолчанию уходят через `ХеРТИК`.

`ХеРТИК` здесь понимается как:
- handoff;
- resume-trigger;
- isolated continuation;
- bounded return path into `main`.

---

## 6. Evidence and blind-judge layer

Планируемая архитектура признаёт, что evidence-backed judging practice уже существовала, и делает её явным слоем.

Минимальный смысл этого слоя:
- closure и review опираются на artifact/evidence/verification trail;
- результат не принимается только по уверенности исполнителя;
- слабый evidence pack не даёт права на молчаливое закрытие;
- review-gated состояние означает реальную остановку для judgment.

В зрелой форме этот слой должен включать:
- input package;
- evidence expectations;
- judgment questions;
- verdict schema;
- close / rework / blocked outcomes;
- linkage to manual reopen policy.

---

## 7. Retry / escalation model

Retry и continuation остаются строго ограниченными.

Default posture:
- `initial attempt = 1`
- `automatic retries = 0`

Разрешённые budget classes:
- `single-shot`
- `light-retry`
- `timed-observation`
- `human-gated`

Архитектурная цель:
- не допускать бесконечного persistence by mood;
- не путать effort с progress;
- не маскировать архитектурную проблему повторными попытками.

---

## 8. Memory architecture

Memory в планируемой архитектуре — это не архив чата, а continuity layer.

Туда должны попадать:
- decisions;
- reusable patterns;
- anti-patterns;
- blockers with reuse value;
- durable references;
- lessons from evidence/review.

Memory должна помогать будущему execution quality, а не копить неструктурированный хвост.

---

## 9. Canonical surfaces

Планируемая архитектура требует жёстче закрепить canonical surfaces:
- где живут handoff files;
- где живут blocked packages;
- где живут routing cards;
- где живут evidence packs;
- где живут memory distillation entries;
- где живут continuation artifacts.

Цель:
- убрать ambiguity;
- упростить retrieval;
- сократить зависимость от памяти чата;
- сделать review и resume inspectable.

---

## 10. Architecture improvement layer

Следующий эволюционный слой — `Architecture Improvement Layer`.

Его задача не в том, чтобы архитектура самовольно себя переписывала.
Его задача в том, чтобы архитектура училась на собственной практике.

Этот слой должен делать 4 вещи:

### 10.1 Observe
Собирать сигналы трения:
- frequent `BLOCKED` clusters;
- repeated reopen after review;
- weak evidence packs;
- overloaded `main`;
- repeated handoff gaps;
- routing ambiguity;
- needless transitions;
- continuation chains that became too long.

### 10.2 Distill
Превращать сигналы в:
- pattern notes;
- anti-pattern notes;
- simplification candidates;
- architecture debt notes.

### 10.3 Suggest
Готовить bounded proposals:
- объединить шаги;
- убрать лишний transition;
- стандартизировать template;
- выделить canonical artifact;
- уточнить policy gap;
- предложить новый review/mapping rule.

### 10.4 Promote
Только через human-gated decision:
- создавать improvement task;
- писать spec/update note;
- обновлять template/policy/mapping;
- закреплять новое правило в baseline.

---

## 11. Allowed vs forbidden automation

### Allowed automation
Можно автоматизировать:
- signal detection;
- evidence summarization;
- routing suggestions;
- handoff scaffolding;
- resume-basis scaffolding;
- blocked-package scaffolding;
- lesson distillation;
- debt flagging;
- improvement proposal drafting.

### Forbidden silent automation
Нельзя молча автоматизировать:
- смену ownership model;
- смену authority boundaries;
- ослабление review-gates;
- изменение retry defaults;
- изменение close/reopen semantics;
- изменение memory policy;
- удаление core architectural layers.

Иными словами:
- **auto-observation and auto-suggestion = yes**;
- **silent architecture mutation = no**.

---

## 12. Planned modernization path

Планируемая последовательность модернизации выглядит так:

### Priority 1
Implementation mapping:
- посадить baseline stack на реальные runtime surfaces.

### Priority 2
Runtime-binding for `ХеРТИК`:
- creation path for handoff;
- resume-trigger shape;
- isolated continuation path;
- return path into `main`.

### Priority 3
Canonical surface policy:
- зафиксировать default artifact/storage anchors.

### Priority 4
Blind Judge Spec + worked example:
- явно оформить evidence-backed review layer.

### Priority 5
Architecture Improvement Layer v1:
- наблюдать трение;
- собирать improvement proposals;
- запускать bounded modernization tasks.

### Priority 6
Pressure-test on live flows:
- прогонять архитектуру на реальных bounded задачах.

---

## 13. Bottom line

Планируемая архитектура OpenClaw Frame — это не просто stack документов.

Это operating architecture, где:
- `main` тонкий;
- execution early-routed;
- review evidence-backed;
- continuation inspectable;
- retry budgeted;
- memory distilled;
- improvement loop встроен в саму систему.

То есть цель не просто "делать задачи", а делать так, чтобы сама архитектура со временем становилась:
- проще;
- чище;
- проверяемее;
- менее chat-dependent;
- более устойчивой к перегреву и размазыванию ответственности.
