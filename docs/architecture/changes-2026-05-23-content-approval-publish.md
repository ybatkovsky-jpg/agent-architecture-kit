# Changes 2026-05-23 — Content Approval / Publish Architecture Delta

## Scope of this delta

This note captures the architecture-relevant changes consolidated before GitHub push for the content approval/publish contour.

It summarizes what changed conceptually, without copying private operational state or channel-specific secrets.

---

## Consolidated changes

### Coverage outcome after full crosswalk

After a fuller crosswalk against the implementation diff, the exported architecture now spans three distinct contours:

1. **media approval / publish seam**;
2. **publish runtime state machine**;
3. **plan / task / queue sync contour**.

The first export pass had captured mainly the media seam.
The later crosswalk showed that runtime-state and multi-object synchronization were also first-class architecture changes and needed dedicated docs.

### 1. Real media generation moved into queue materialization

The queue materialization path now has responsibility for resolving a real approval/publish asset, rather than trusting that an upstream workflow flag already produced one.

Implication:
- a post can become approval-ready with an actual generated image even if an earlier workflow configuration suppressed image generation.

Architecture meaning:
- **materialization is an enforcing layer**, not just a formatting layer.

### 2. Placeholder preview detection became provenance-aware

A local preview image is no longer treated as equivalent to a generated production-ready media asset.

Signals now include:
- expected filename patterns;
- presence or absence of generator provenance sidecar data;
- lightweight placeholder heuristics.

Architecture meaning:
- fallback assets need explicit provenance semantics.

### 3. Canonical asset references are updated at both queue and final-output layers

When a real media asset is generated, the effective asset reference is written back into:
- the queue item transport layer; and
- the canonical final output layer.

Architecture meaning:
- approval, publish, and downstream inspection should converge on one resolved asset reference.

### 4. Approval media became a first-class interface

The system now exposes a dedicated approval-media payload, separate from the approval card summary.

Architecture meaning:
- human-readable review and transport-ready preview are adjacent but distinct contracts.

### 5. Approval and publish remain separate transport operations

The architecture did **not** collapse approval preview sending into publish transport.
Instead, it defined a reusable seam where both can consume the same resolved media object.

Architecture meaning:
- preview delivery and final delivery share payload basis without becoming the same operation.

### 6. Scheduling remained an independent gate from approval state

Even after approval, a queue item can still remain non-publishable because of schedule semantics.

Architecture meaning:
- `approval_ready`, `approved`, and `publishable_now` are different states and should stay distinct.

---

## Primary exported docs

The main reusable architecture notes for this delta are:

- `docs/architecture/media-approval-and-publish-seam.md`
- `docs/architecture/publish-runtime-state-machine.md`
- `docs/architecture/plan-task-queue-sync-contour.md`

These are the product-facing documents that should survive beyond the original implementation details.

---

## What was intentionally not exported

Not included here:
- channel tokens or secret config;
- private queue item identifiers;
- operator chat specifics;
- one-off manual force-publish steps;
- raw internal debugging transcripts.

Those are operational details, not reusable architecture.

---

## Recommended push framing

If you want this grouped cleanly in Git history, frame it as:

- **architecture: add media approval / publish seam contour**
- optional companion implementation commit in the source repo separately from the architecture-kit export
