# Local Task Manager

Простой локальный Task Manager для рабочего потока Клава:

- задачи хранятся в `task-manager/tasks.db`
- статусы:
  - `open`
  - `in_progress`
  - `review` — задача выполнена по мнению Клава и ждёт согласования Юрия
  - `waiting_user`
  - `done`
- есть история событий
- есть `next` для следующей задачи
- есть `watchdog` для зависших задач
- simplify/refactor/consolidate/hardening задачи можно вести как named Simplification Lane внутри общего Task Manager workflow

## Быстрые команды

```bash
python3 task-manager/task_manager.py init
python3 task-manager/task_manager.py add "Довести triad pipeline до approval-ready workflow" --priority 10 --next-action "Починить bridge task/final -> publish-ready queue"
python3 task-manager/task_manager.py list
python3 task-manager/task_manager.py start 1 --note "Начал работу"
python3 task-manager/task_manager.py claim-active 1 --priority-band P2 --priority-reason "normal current focus" --priority-source policy
python3 task-manager/task_manager.py note 1 --note "Сделан свежий bridge task queue -> plan slot" --next-action "Доматериализовать publish package и visual asset"
python3 task-manager/task_manager.py preempt 2 --incoming-priority-band P1 --incoming-priority-reason "operator-declared urgent fix" --basis higher_priority --authority-source operator --resume-next-action "Вернуться к publish package после hotfix" --resume-basis "event:preemption checkpoint saved" --yield-reason "urgent hotfix outranks current P2"
python3 task-manager/task_manager.py show-active
python3 task-manager/task_manager.py review 1 --note "Задача выполнена, прошу согласовать" --next-action "Если Юрий скажет ок — закрыть; если нет — вернуть в работу"
python3 task-manager/task_manager.py wait 1 --note "Жду решения пользователя по закрытию" --blocked-reason "Нужно подтверждение закрытия" --next-action "После ответа закрыть или вернуть в работу"
python3 task-manager/task_manager.py done 1 --note "Задача закрыта"
python3 task-manager/task_manager.py next
python3 task-manager/task_manager.py watchdog --hours 2
```

### Validate vs transition contract

Для переходов в `review` и `done` Task Manager применяет **fresh inline closure-proof contract**: реальная transition-команда смотрит прежде всего на note, переданный прямо в `review` / `accept` / `done`, и ожидает там claim/evidence/anchor/verification.

Практическое следствие:
- старый паттерн `note` -> потом пустой `review`/`done` может выглядеть правдоподобно по накопленным notes,
- но реальный transition всё равно может быть отклонён, если в самой transition-команде нет свежего closure-proof note.

Команда `validate` теперь отдельно подсвечивает этот случай warning'ом `transition_requires_inline_fresh_proof` и human-readable notice в stderr, но лучший операторский паттерн остаётся таким:
- для closure-ready задач передавать полный closure-proof сразу в `review` / `accept` / `done --note "CLAIMED_OUTCOME ... EVIDENCE ... ANCHOR ... VERIFICATION ..."`.

## Simplification Lane

Task Manager может использоваться не только для feature / implementation задач, но и для отдельного named lane на упрощение системы.

Когда задача в первую очередь нужна чтобы:
- убрать дублирование;
- схлопнуть лишнюю поверхность;
- прояснить boundary;
- сократить workflow friction;
- укрепить operating rule против повторяющегося drift;

её стоит классифицировать как simplify / refactor / consolidate / hardening task.

Практические правила:
- задача должна быть bounded и обычно закрываться одним основным artifact;
- task card хранит статус, краткие notes, next action и ссылки на proving artifact;
- подробный результат живёт в файле, а не внутри task card;
- wiki обновляется только если результат меняет или проясняет долговечную человеко-читаемую конвенцию;
- decision page обновляется только если change становится governing policy или меняет structural boundary.

Подробные правила см. в `../wiki/resources/SIMPLIFICATION_LANE_CONVENTIONS.md`.

## Structured / MCP adapter note

Для machine-facing интеграций допускается **тонкий structured/MCP adapter** поверх существующего `task_manager.py`, но только как bounded wrapper.

Правило пилота:
- `task-manager` остаётся source of truth для task state;
- adapter переиспользует существующее CLI/API-поведение, а не заводит вторую task-логику;
- нельзя добавлять второй task store, shadow orchestration layer или широкий framework/API слой;
- phase-1 surface должен оставаться минимальным и experimental.

Текущий phase-1 contract зафиксирован в `task-manager/STRUCTURED_ADAPTER_CONTRACT.md`.
Разрешённый минимальный operation set сейчас ограничен только:
- `task_list`
- `task_show`
- `task_add`
- `task_start`

Если меняется governing boundary, это фиксируется decision page, а не только кодом.

## Autonomous task mode contract

Task Manager supports an explicit per-task autonomous execution mode named `autonomous_until_done`.

Canonical runtime rules:
- mode persists per task in `task-manager/runtime/autonomy/task-<id>.json`;
- tasks not enrolled in autonomy remain `manual` and keep normal lifecycle behavior;
- autonomous mode keeps the delivery gate internal until a terminal surface decision exists;
- normal task inspection surfaces the autonomy projection via `task_manager.py show`, `list --format json`, and `watchdog`.

Minimal persisted state contract for continuation control:
- `mode`: `manual` or `autonomous_until_done`
- `autonomy_mode`: boolean compatibility flag
- `delivery_gate`: current delivery rule, currently `internal_only_until_terminal`
- `parent_status_at_entry`: status when autonomy was entered
- `continuation.router_decision`: `none|continue_now|resume_later|escalate_internal|surface_to_user`
- `continuation.surface_reason`: `done|blocked_external|approval_needed|risk_alert|""`
- `continuation.next_action`: current bounded continuation step
- `continuation.frontier_next_action`: explicit next frontier when a leaf/local slice finished but the parent goal remains open
- `continuation.awaiting_user|approval_needed|risk_alert|done_criteria_met|parent_goal_open|frontier_known`: terminal/continuation booleans
- `watchdog.eligible_for_resume|resume_after|retry_count|cooldown_until|last_failure_class`: minimal auto-resume control state

Main commands:
- `python3 task-manager/task_manager.py autonomy-init <task_id> --next-action "..."`
- `python3 task-manager/task_manager.py autonomy-show <task_id>`
- `python3 task-manager/task_manager.py show <task_id>`
- `python3 task-manager/task_manager.py list --format json`
- `python3 task-manager/task_manager.py watchdog --hours 2`
- `python3 task-manager/task_manager.py watchdog --hours 2 --run-resumes --cooldown-minutes 30`
- `python3 task-manager/task_manager.py watchdog-schedule --every 10m --hours 2 --cooldown-minutes 30`

Child completion input contract for `autonomy-route`:
- accepts either a JSON object or a thin AIK/OpenClaw-Frame envelope text block starting with `HANDOFF`, `ACK`, `DONE`, or `BLOCKED`;
- envelope parsing maps those message-facing statuses back into internal continuation routing (`DONE` is not parent-`done` by itself; `BLOCKED` with `owner_for_decision: human:*` / `resume_mode: await_unblock` is treated as external blocking);
- child payload may also carry `parent_goal_open`, `frontier_known`, and `frontier_next_action`/`parent_next_action` so leaf completion cannot surface while a known parent frontier still exists;
- when a child reports a missing but locally buildable implementation path, the router treats that as an implementation frontier (`continue_now`) rather than a user-facing blocker, unless the payload also shows a true external blocker such as approval, access, business decision, or irreversible/expensive risk;
- this keeps `HANDOFF/ACK/DONE/BLOCKED` as transport/view language while preserving task-manager autonomy state as the canonical control plane.

Recurring autonomous watchdog contract:
- `watchdog --run-resumes` is the executor mode; without it the command remains inspection/reporting only.
- `watchdog-schedule` installs a recurring isolated `openclaw cron add` job with `--no-deliver` so bounded continuation passes stay internal by default.
- the scheduled message contract explicitly runs `python3 task-manager/task_manager.py watchdog --hours <n> --run-resumes --cooldown-minutes <m>` as the canonical loop entrypoint.
- terminal or exception-routed autonomous tasks stop further continuation attempts because watchdog only resumes tasks that still pass the persisted autonomy gate and resume eligibility checks.
- safe finishing work is default, not opt-in: after a bounded autonomous pass modifies code or task-manager state, the executor should also complete the safe tail before stopping when low-risk — targeted verification on the changed path, a broader relevant regression sweep when practical, a durable checkpoint/memory update, and an explicit residual-risk summary. Only skip these finishing steps when they would be risky, destructive, or meaningfully scope-expanding, and name the skipped step plus reason.

## Minimal preemption contour

Для первого machine-enforced контура preemption добавлены два canonical файла:
- `task-manager/active_front_state.json` — текущий primary active front;
- `task-manager/preemption_events.jsonl` — append-only event log по claim/preempt событиям.

Правила минимального контура:
- нельзя молча переключить active front на другую задачу: `claim-active` отвергает switch, если уже записан другой active front;
- для переключения нужен явный `preempt`;
- `preempt` проверяет priority basis / authority source / preemptibility / resume-basis поля;
- interrupted front получает canonical writeback (`waiting_user` + `paused_for_preemption:*` blocked reason + next action + event);
- incoming front становится active только после этого writeback;
- все claim/preempt действия пишутся и в task events, и в `preemption_events.jsonl`.

## Идея workflow

1. Юрий ставит задачи.
2. Клав заводит их в Task Manager.
3. Клав работает по одной/нескольким задачам, но всегда знает следующую.
4. Когда задача выполнена по мнению Клава, он переводит её в `review` и спрашивает: `закрываем или возвращаем в работу?`
5. Если Юрий говорит `окей`, задача закрывается (`done`).
6. Если Юрий говорит, что переделать, задача возвращается в `in_progress`.
7. Закрытые задачи не трогаются повторно; если появляется новое дело — заводится новая задача.
8. `watchdog` показывает зависшие задачи, чтобы Клав не бросал их между сообщениями.
