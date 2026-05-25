# Task 479 — Memory hardening: general fact domains expansion

## Context
Первый проход memory hardening усилил personal/profile retrieval, но показал, что general fact retrieval всё ещё не доведён:
- project facts остаются частично размазанными по narrative memory и historical notes;
- operational agreements смешаны с preference/style blocks;
- tech facts часто живут в daily memory и session trails, а не в canonical blocks;
- retrieval по не-персональным вопросам всё ещё может шуметь.

Пользователь подтвердил следующий шаг: расширить hardening не только на профиль, а на другие fact domains.

## Goal
Расширить retrieval-friendly memory structure с user-profile layer на более общий слой fact domains: проекты, договорённости, tech facts, рабочие контуры.

## Desired outcome
После выполнения:
1. В `MEMORY.md` появляются явные canonical blocks для non-personal fact domains.
2. Ключевые project / operational / tech facts представлены в короткой retrieval-friendly форме.
3. Появляется mixed probe-set, который проверяет не только личные, но и project / operational / tech / workflow facts.
4. Общая memory shape становится лучше приспособлена для factual retrieval across domains.

## In scope
- Добавить или усилить в `MEMORY.md` блоки для:
  - `Project facts`
  - `Operational agreements`
  - `Tech facts`
  - `Working contours`
- Добавить normalized fact lines для устойчивых и проверенных фактов в этих доменах.
- Создать mixed-domain probe artifact.
- Сохранить human readability и не ломать existing memory structure.

## Out of scope
- Полный рефактор historical memory files.
- Изменение search/embedding engine.
- Большая чистка всех session trails.
- Любые gateway/config изменения.

## Plan
### Step 1 — Audit stable non-personal facts
- Выделить из `MEMORY.md` и связанных устойчивых записей факты, которые уже достаточно стабильны для canonicalization.
- Отделить устойчивые факты от шумных или time-sensitive деталей.

### Step 2 — Introduce canonical non-personal fact blocks
- Добавить retrieval-friendly блоки по project / operational / tech / working contour domains.
- Размещать только те факты, которые реально помогают повторному retrieval.

### Step 3 — Add normalized fact lines
- Для ключевых non-personal facts добавить короткие canonical fact lines.
- Не перегружать блок и не превращать его в свалку всего подряд.

### Step 4 — Add mixed-domain probe artifact
- Создать probe set минимум с 6 вопросами:
  - personal
  - project
  - operational
  - tech
  - workflow
  - execution contour
- Для каждого указать expected answer и expected source section.

### Step 5 — Quick validation
- Структурно проверить, что новые блоки читаемы человеком и полезны для retrieval.
- По возможности сделать быстрый retrieval sanity check на нескольких доменах.

## Acceptance criteria
- [ ] Создан artifact-spec для task #479.
- [ ] В `MEMORY.md` добавлены или усилены canonical blocks для non-personal fact domains.
- [ ] Добавлены normalized fact lines для project / operational / tech / working contour facts.
- [ ] Создан mixed-domain probe artifact минимум с 6 вопросами.
- [ ] Структура памяти осталась human-readable.
- [ ] Улучшение направлено именно на general fact retrieval, а не только на user profile.

## Risks
- Перегрузить `MEMORY.md` и потерять читаемость.
- Канонизировать слишком шумные или быстро устаревающие факты.
- Дублировать факты так, что появится риск рассинхронизации.

## Execution mode
ЗИРиБТ / isolated bounded run.
