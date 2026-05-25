# Context System 2 — strategist runtime stub implementation note

Date: 2026-05-19
Status: landed bounded stub
Parent task: #531
Task: CS2-C1

## What was created

A minimal implementation-oriented runtime seam stub was added at:
- `agents/hermes-workspace/hermes-agent/agent/cs2_strategist_runtime.py`

A focused proof test was added at:
- `agents/hermes-workspace/hermes-agent/tests/run_agent/test_cs2_strategist_runtime.py`

## Why this location

This is the cleanest current code landing zone because:
- `agent/prompt_builder.py` already owns the nearby bootstrap/manifest assembly seam;
- strategist startup capsules already have working tests in `tests/run_agent/`;
- the CS2 proof can evolve beside the prompt/bootstrap path without prematurely coupling all future CS2 behavior into `prompt_builder.py`.

## Implemented proof scope

The stub intentionally implements only the bounded strategist starter assembly path from the prior proof:
- manifest selection for `strategist`
- 4-entry starter registry
- direct load of:
  - `strategist.core_operating_contract`
  - `strategist.current_contour`
  - `strategist.current_control`
- explicit `missing_pack` for:
  - `strategist.local_current_branch`
- assembly status derivation returning:
  - `ok_with_missing_optional`
- compact trace/debug envelope for startup metadata style inspection

## Important boundary

This stub does **not** yet implement:
- conditional strategist pack admission
- CS2 wrapped-pack materialization
- generated continuation capsule materialization
- token-budget trimming
- prompt-builder wiring into active runtime startup

That is deliberate: this artifact is a runnable seam stub, not a full CS2 runtime rollout.

## Follow-up seam now landed

The helper is now wired into isolated startup metadata at:
- `agents/hermes-workspace/hermes-agent/run_agent.py` via `AIAgent._build_startup_metadata()`

Guard:
- env flag `HERMES_EXPERIMENTAL_CS2_STRATEGIST_STARTUP_METADATA`

Behavior:
- default/off: no startup metadata change
- on + isolated strategist lane: startup metadata includes `cs2_strategist_runtime` with:
  - selected CS2 surface id
  - strategist assembly trace
  - missing optional continuation status

This keeps the proof observable at runtime without changing prompt payload behavior.

## Next strongest step

Promote the emitted strategist runtime trace into a small operator-facing inspection surface (for example session/debug views or explicit diagnostics tooling), then decide whether any subset should inform later prompt assembly once conditional admission rules are ready.
