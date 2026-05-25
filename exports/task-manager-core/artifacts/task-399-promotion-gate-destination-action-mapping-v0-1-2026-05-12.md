# Task 399 — promotion gate destination/action mapping v0.1 bounded completion

Date: 2026-05-12
Task: #399
Parent contour: OpenClaw Frame next-stage / promotion gate automation
Status: bounded completion artifact

## What changed

Updated:
- `scripts/architecture/promotion_gate.py`

The bounded extension strengthens two previously thin areas of the markdown-first promotion gate:
1. destination suggestion quality;
2. verdict-to-next-action mapping clarity.

## Behavior improvements

### 1. Clearer repo-fit to destination mapping

The script now uses a more explicit bucket rule table with:
- bucket-specific pattern sets;
- a rationale string per bucket;
- path-prefix guidance for destination shaping.

This improves destination suggestion by:
- distinguishing schema-oriented content from generic architecture content more deliberately;
- shaping destination paths with compact subdirectories such as:
  - `docs/architecture/specs/...`
  - `docs/architecture/schemas/...`
  - `docs/architecture/heuristics/...`
  - `docs/evaluation/promotion-gates/...`
- adding conservative ambiguity handling when multiple buckets score similarly.

### 2. Stronger next_action selection logic per verdict

Next actions are now assembled through a dedicated mapping function rather than scattered inline branches.

This improves outputs by making them more explicit per verdict:
- `promote`
  - returns a direct product-repo preparation action;
  - includes `target_path` when destination mapping is clear.
- `sanitize_then_promote`
  - returns a rewrite/sanitize-first action;
  - includes `target_path_after_sanitization` when available;
  - includes rewrite scope guidance based on the destination bucket.
- `hold_internal`
  - returns a retain-internal action with a stronger internal rationale when operational/internal-only signals dominate.
- `needs_review`
  - returns review escalation with specific review questions;
  - includes `proposed_target_path` when a likely destination exists.

### 3. Better differentiation between sanitize vs review vs hold

Bounded handling is now stronger for the three most ambiguous lanes:

- `sanitize_then_promote`
  - used when blockers exist but are sanitizable and reuse/repo-fit remain strong.
- `needs_review`
  - used when reusable material has blockers that are not clearly sanitizable;
  - also used when competing destination buckets create uncertainty for otherwise promotable material;
  - also used for quality-threshold mixes where reuse/repo-fit are decent but generic/stability signals remain weak.
- `hold_internal`
  - remains the outcome for clearly internal/operational artifacts or weak reuse/repo-fit.

### 4. Compact refactor for legibility

Introduced compact helper structure rather than expanding inline branching:
- explicit destination bucket rule metadata;
- title/path-driven destination subdirectory hints;
- `choose_next_action(...)` helper for verdict action mapping.

## Bounded validation performed

Validated by:
- compiling the script with `python3 -m py_compile`;
- running it against tasks #392, #397, and #398 artifacts.

Observed bounded examples:
- #397 schema artifact now resolves to a stronger direct promotion recommendation with an explicit target path;
- #392 and #398 still land in review, but now with clearer proposed target paths and clearer review prompts.

## What remains deferred to #400 or later

Still deferred:
- fixture/regression pack for destination and action mapping outcomes;
- stronger deduplication or overlap checks against existing product-repo structure;
- richer rewrite planning beyond bounded hints;
- support for non-markdown artifacts;
- integration with any later queue/report/promotion execution flow.

## Assessment

This is a bounded but real extension of the runnable gate. It does not attempt end-to-end automation, but it materially improves the decision object by making destination suggestions and follow-up actions more explicit and more useful for downstream review or promotion steps.
