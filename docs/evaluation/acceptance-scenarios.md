# Acceptance Scenarios

## Purpose

A small realistic scenario pack should test operator-relevant request classes, not only abstract architecture prompts.

## Core scenario classes

- **status** — current task/stage status
- **decision** — why a design choice was made
- **continue** — resume from prior bounded work
- **preference** — recall verified operating style or preference
- **audit** — show exact source trail for a claim

## What each scenario should define

- scenario id and name;
- intended request class;
- expected output shape;
- expected authority behavior;
- pass criteria;
- fail criteria.

## Why this matters

Without realistic scenario packs, a retrieval or memory system can look impressive in general and still fail in the exact operator paths that matter.
