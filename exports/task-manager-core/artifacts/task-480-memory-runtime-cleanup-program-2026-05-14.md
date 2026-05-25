# Task 480 — Memory/runtime cleanup program

## User directive
Исполнять строго по порядку через ЗИРиБТ и не приходить как с финалом без результата по всей цепочке:
1. убить дублирование веток,
2. оставить один execution spine,
3. довести runtime serving до боевого состояния,
4. только потом оптимизировать bootstrap/context.

## Why this exists
В memory/context контуре накопился branch sprawl: старые PKM/RAG ветки, Memory Core v1, runtime retrieval/serving, bootstrap optimization, markdown hardening. Часть задач устарела, часть дублирует соседние ветки, часть должна быть заморожена до закрытия ядра.

## Program goal
Собрать и исполнить единый memory/runtime execution contour, где:
- дублирующие ветки схлопнуты или заморожены;
- остаётся один понятный execution spine;
- runtime serving становится главным боевым контуром recall;
- bootstrap/context optimization идёт только после serving-core.

## Mandatory order
### Phase 1 — Branch triage and dedupe
- Собрать полный task contour по memory/context/runtime/bootstrap.
- Разделить на `KEEP / FREEZE / KILL / REFERENCE`.
- Убрать дублирование execution веток и определить один spine.

### Phase 2 — One execution spine
- Из утверждённого набора задач собрать один master execution spine.
- Явно указать dependency order и stop-doing list.
- По возможности отразить это в task-manager notes/artifacts, чтобы контур стал операбельным.

### Phase 3 — Runtime serving to production-ready contour
- Довести serving/retrieval execution path до состояния, где memory runtime является основным path recall, а не только markdown fallback.
- Нужны: routing/precedence, traceability, instrumentation, serving packs, output checks, verification loop.

### Phase 4 — Bootstrap/context optimization only after serving
- Только после стабилизации serving-core перейти к bootstrap/context optimization.
- Уменьшать startup context, используя уже внятный serving contract.

## Desired deliverables
1. Master roadmap artifact with branch triage and execution order.
2. Consolidated execution spine.
3. Concrete task-manager updates or child-task launch plan reflecting the new spine.
4. Bounded implementation progress on runtime serving contour.
5. Only after that: bounded bootstrap optimization progress.
6. Final report with:
   - what was frozen/killed,
   - what remains active,
   - what runtime path is now canonical,
   - what still blocks “memory works as we want”.

## Constraints
- Не тащить параллельно старые speculative branches, если они не нужны spine.
- Не подменять execution красивым spec-only ответом.
- Не трогать gateway/config без отдельной необходимости.
- Сохранять human-readable artifacts.

## Acceptance criteria
- [ ] Создан master roadmap artifact.
- [ ] Есть branch triage: keep/freeze/kill/reference.
- [ ] Определён один execution spine.
- [ ] Есть task-manager-level consolidation plan or direct updates.
- [ ] Runtime serving contour продвинут практически, не только декларативно.
- [ ] Bootstrap/context optimization рассматривается только после serving-core.
- [ ] Финальный отчёт не врёт о степени готовности.

## Execution mode
Long-running ЗИРиБТ program contour.
