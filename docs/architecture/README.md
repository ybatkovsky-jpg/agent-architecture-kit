# Architecture Docs

This folder contains the second-wave export of the stronger architecture layer.

Included here:
- frame baseline;
- handoff contract;
- routing and ownership map;
- retry and escalation budget policy;
- memory distillation cadence;
- control-plane spec;
- implementation mapping;
- current-state and next-steps summary;
- continuation contract and promotion-gate supporting docs under `promotion-gates/`, `policies/`, and `schemas/`.

These docs are curated exports from a larger internal architecture corpus. They are intentionally rewritten into a public-safe, repo-friendly shape rather than copied as raw internal working notes.

Notable subfolders:
- `promotion-gates/` — continuation and promotion-gate architecture notes;
- `policies/` — focused operational policies promoted into product-facing form, including anchor/storage and context-serving guidance;
- `schemas/` — prose references for machine-readable schemas that also live under the repo-level `schemas/` directory.
