# Protected Regression Layer v0.1

## Goal

Protect important behaviors from silent regression while allowing bounded baseline refresh and learning-loop updates.

## What this layer enforces

- protected cases must continue to pass;
- baseline refresh must be guarded;
- learning-loop updates must be explicit;
- accept / refresh / rollback rules must be encoded, not improvised.

## Important distinction

A system can have a working protected-regression layer even when full promotion is still blocked.

That means:
- tooling can be sound;
- regression discipline can be real;
- but candidate quality can still be insufficient for full pass.

## Core refresh rule

Baseline refresh should happen only when:
- recommendation explicitly allows it;
- protected cases pass;
- sampled regressions are zero;
- blockers are empty.
