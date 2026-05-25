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
- structured compression contract;
- session lifecycle prevention guidance;
- media approval and publish seam guidance;
- publish runtime state machine guidance;
- plan / task / queue sync contour guidance;
- continuation contract and promotion-gate supporting docs under `promotion-gates/`, `policies/`, and `schemas/`.

These docs are curated exports from a larger internal architecture corpus. They are intentionally rewritten into a public-safe, repo-friendly shape rather than copied as raw internal working notes.

Notable docs and subfolders:
- `media-approval-and-publish-seam.md` — approval-ready media contract, placeholder detection, and publish seam guidance for review-gated content systems;
- `publish-runtime-state-machine.md` — approval/schedule/retry/lock/runtime-state model for deterministic delivery workers;
- `plan-task-queue-sync-contour.md` — linked-identity and directional-sync pattern across planning, execution, and delivery layers;
- `promotion-gates/` — continuation and promotion-gate architecture notes;
- `policies/` — focused operational policies promoted into product-facing