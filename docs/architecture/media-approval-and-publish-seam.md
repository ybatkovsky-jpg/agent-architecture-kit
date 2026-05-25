# Media Approval and Publish Seam

## Purpose

Define a clean architecture seam between:
- **content generation**,
- **approval-ready review surfaces**, and
- **final publish delivery**.

This contour emerged from a real failure mode where a post could be structurally approval-ready, but the human review surface still degraded into a text-only experience or a placeholder preview image.

The goal of this seam is to ensure that a review-gated publishing workflow can carry a **real media asset plus caption** all the way from content generation to approval and then to final publish, without collapsing into disconnected local hacks.

---

## Problem this contour solves

A common failure pattern in agent-driven content systems is:

1. the generator produces text and an image prompt;
2. the workflow marks the post as review-ready;
3. the queue contains a nominal `photo_file` field;
4. the human approval surface still shows only text, or references a placeholder preview;
5. publish and approval behave like different systems with different payload contracts.

This creates three architecture defects:

- **asset truth drift** — the queue points to an image field that is not a verified generated asset;
- **approval/publish contract split** — the approval surface can approve text while the publish surface later sends a different or degraded media payload;
- **fallback opacity** — placeholder assets are treated like normal assets unless explicitly distinguished.

---

## Architecture decision

The content system should expose **two adjacent but distinct delivery contracts**:

1. **Approval card contract**
   - human-readable review summary;
   - suitable for inbox/list surfaces;
   - may be text-first.

2. **Approval media contract**
   - machine-usable payload for sending the real approval preview;
   - includes resolved media path plus resolved caption;
   - must point to the same asset that publish will use unless a later explicit replacement happens.

The publish system remains a third contract:

3. **Publish delivery contract**
   - resolved transport payload for the destination channel;
   - must consume the already-materialized approved asset and caption.

These contracts should be separate representations of one shared underlying publish object, not parallel sources of truth.

---

## Core seam

### 1. Materialization happens before approval rendering

The system should normalize and materialize the queue item before any approval surface renders it.

That materialization step is responsible for:
- validating or generating the caption artifact;
- resolving the effective image asset;
- writing the effective asset reference back into the queue item and canonical content metadata when needed.

This means approval does not inspect partially prepared state.

### 2. Placeholder preview is not equivalent to a generated asset

A synthetic preview file such as `telegram.preview.png` must not automatically be treated as a trustworthy media artifact.

If the system supports real generative image creation, then placeholder previews must be explicitly detectable as fallback artifacts.

Recommended rule:
- if the preview file has no provenance marker from the real image generator,
- or matches placeholder heuristics,
- it remains a fallback and is eligible for regeneration.

### 3. Real image generation can occur at materialization time

If a post is approval-ready in text/content terms but still lacks a real media asset, the materialization layer may call a configured image generator using the final image prompt.

This is appropriate when:
- the workflow already has a finalized image prompt;
- approval requires a real visual;
- the asset can be generated deterministically enough for review.

This avoids a broken state where the workflow says “ready for approval” but the human sees only a stub.

---

## RouterAI-specific implementation pattern

One concrete implementation pattern validated in production-like use:

- keep an image generator wrapper script outside the approval transport code;
- load generator credentials from a dedicated local env file;
- write the generated asset to the task-local publish preview path;
- write a sidecar provenance artifact (for example, a response JSON file);
- update canonical `selected_asset` metadata once the real asset exists.

This pattern gives a useful split:
- generation remains an infrastructure concern;
- queue materialization decides whether generation is required;
- approval/publish only consume the resolved asset.

---

## Approval media payload contract

A useful approval media payload should contain at least:

- `kind`
- `queue_item`
- `target`
- `status`
- `approval_ready`
- `blockers`
- `photo_file`
- `photo_path`
- `caption_file`
- `caption`
- `caption_preview`
- `metadata`

Why this matters:
- approval transport can send real media without reverse-engineering queue internals;
- orchestration can inspect readiness and blockers without rendering a human card;
- approval and publish operate from the same resolved asset/caption basis.

---

## Scheduling and approval interaction

A review-approved item may still remain non-publishable because of a future scheduled time.

This is not a failure.
It is a separate gating layer.

The seam should therefore preserve three distinct states:

- **approval-ready** — sufficient content/media completeness for human review;
- **approved/ready** — approved for publish, but not necessarily due yet;
- **publishable now** — approved and not blocked by schedule or retry timing.

This separation prevents a class of operator confusion where “approved” is incorrectly assumed to mean “should publish immediately.”

---

## Anti-patterns

Avoid these:

### 1. Text-only approval on media-dependent posts
If the post is intended to ship with an image, a text-only approval surface is incomplete unless the system explicitly says the visual is deferred.

### 2. Approval reading one asset while publish sends another
Approval and publish must not silently diverge.
If publish will send a different image, that change needs a new approval-relevant event.

### 3. Treating fallback previews as ordinary assets
Fallback previews should be visible as fallback state, not silently promoted into canonical output.

### 4. Collapsing approval and publish transport into one path
Approval preview delivery and final publish delivery have different semantics and should remain separate operations even if they share payload structure.

---

## Minimal reference flow

1. final content contains text plus image prompt;
2. queue item is normalized;
3. materialization ensures caption artifact exists;
4. materialization resolves or generates the real image asset;
5. canonical output records the selected asset;
6. approval card renders a human-readable summary;
7. approval media payload exposes the resolved `photo_path + caption`;
8. human approves;
9. publish transport sends the same resolved asset and caption.

---

## Why this belongs in the architecture kit

This seam is reusable outside the original codebase because it expresses a general pattern:

- **generation is not delivery**;
- **approval is not publish**;
- **fallback artifacts need provenance-aware handling**;
- **resolved media payloads deserve a first-class contract**.

Any agent system that creates rich media for human review before channel delivery will hit the same class of problems.

This note turns that operational pain into a reusable architecture contour.
