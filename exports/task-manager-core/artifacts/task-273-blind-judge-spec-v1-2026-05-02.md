# Task #273 — Blind Judge Spec v1 (2026-05-02)

Date: 2026-05-02
Status: Open
Owner: main
Depends on:
- `task-manager/artifacts/task-271-blind-judge-recovery-and-frame-v1-backfill-2026-05-02.md`
- `task-manager/artifacts/openclaw-frame-blind-judge-recovery-note-v1-2026-05-02.md`
- `task-manager/artifacts/openclaw-frame-handoff-spec-v1-2026-05-01.md`
- `task-manager/artifacts/task-229-manual-reopen-policy-review-gated-runs-2026-04-30.md`
- prior evidence-first / proof-bearing task-manager practice

## Goal

Собрать короткий и bounded `Blind Judge Spec v1` как явный Frame v1 architectural module, не теряя continuity с уже существовавшей evidence-first judging practice.

## Problem

Recovery note уже фиксирует, что blind-judge contour в практике существовал, но пока не упакован как компактный отдельный spec с понятными входами, judgment questions, outcome grammar и связью с handoff/reopen semantics.

Без такого spec слой остаётся понятым только имплицитно:
- review-by-evidence есть,
- но у него нет короткой reusable формы;
- `DONE` / `BLOCKED` уже есть,
- но нет компактного bridge между execution handoff и judgment verdict.

## Scope

Эта задача покрывает только bounded spec layer:
- определить минимальный input package для blind-judge review;
- перечислить acceptable evidence types;
- зафиксировать core judgment questions;
- определить verdict outcomes и их связь с `ACK / DONE / BLOCKED`;
- связать blind-judge verdict с review-gated reopen path;
- сохранить документ компактным и implementation-light.

## Non-goals

- не писать full protocol bible;
- не вводить новый control plane;
- не обещать полную automation of judgment;
- не заменять handoff spec, routing map или manual reopen policy;
- не требовать literal author-anonymization во всех кейсах.

## Acceptance criteria

- [ ] создан отдельный артефакт `openclaw-frame-blind-judge-spec-v1-2026-05-02.md`;
- [ ] spec компактно определяет blind judge как artifact-first / evidence-first review layer;
- [ ] spec явно покрывает input package, acceptable evidence types, core judgment questions и verdict outcomes;
- [ ] spec объясняет связь verdict layer с `ACK / DONE / BLOCKED`;
- [ ] spec явно связывает insufficient/failed review with review-gated reopen rather than silent continuation;
- [ ] continuity с recovery note и prior evidence-first practice сохранена явно.

## Next action

Собрать `Blind Judge Spec v1` как короткий архитектурный документ поверх recovery note и existing Frame v1 baseline docs.
