# Promotion Gate Verdict Schema v1

## 1. Purpose and scope

This document defines the **verdict output contract** for the promotion gate used to evaluate whether internal architecture artifacts are ready for promotion into a product-facing repository.

Its job is to standardize what the gate must say after evaluating a candidate artifact for possible promotion from internal workspace storage into a reusable product-facing repository such as `product-repos/agent-architecture-kit`.

This schema is intended to be directly usable by downstream tasks such as:
- heuristic implementation;
- destination suggestion logic;
- verification fixtures and regression tests;
- future queue/reporting or task-close trigger hooks.

### In scope
- verdict object model;
- required and optional fields;
- verdict semantics;
- score model;
- reasons / warnings / blockers structure;
- destination and action suggestion fields;
- confidence / ambiguity signaling;
- example JSON payloads;
- acceptance criteria and open questions.

### Out of scope
- the scoring algorithm itself beyond contract expectations;
- repo write automation;
- full sanitization workflow;
- generalized schemas for every file class;
- UI/reporting design.

---

## 2. Design goals

The verdict schema should be:
- **machine-readable** enough for scripts, tests, and hooks;
- **human-explainable** enough for operator review;
- **strict on core fields** but flexible on future metadata;
- **safe-by-default**, making ambiguity and blocking conditions explicit;
- **compact**, so it can remain stable in v0.1/v1 implementation work.

### Contract posture

- A verdict is a **decision object**, not a narrative report.
- Every verdict must include enough information to explain **what was decided**, **why**, and **what should happen next**.
- Hard-blocking conditions must be surfaced explicitly rather than hidden in freeform prose.
- Ambiguity must be represented directly, not inferred from vague reason text.

---

## 3. Top-level verdict object model

A promotion gate verdict is a JSON object with this conceptual shape:

```json
{
  "schema_version": "promotion_gate_verdict/v1",
  "candidate": { ... },
  "verdict": "promote",
  "score": { ... },
  "reasons": [ ... ],
  "warnings": [ ... ],
  "blockers": [ ... ],
  "suggested_destination": { ... },
  "next_action": { ... },
  "confidence": { ... },
  "review": { ... },
  "provenance": { ... }
}
```

### Object sections

| Section | Purpose |
|---|---|
| `schema_version` | identifies the verdict contract version |
| `candidate` | identifies what artifact was evaluated |
| `verdict` | final decision class |
| `score` | dimension scores and aggregate score |
| `reasons` | positive or decisive rationale |
| `warnings` | non-fatal concerns |
| `blockers` | fatal or promotion-preventing issues |
| `suggested_destination` | recommended repo/bucket/path target |
| `next_action` | bounded operational follow-up |
| `confidence` | certainty and ambiguity signaling |
| `review` | review need and review context |
| `provenance` | metadata about the evaluation run |

---

## 4. Required fields

The following fields are required in every verdict object:

- `schema_version`
- `candidate`
- `verdict`
- `score`
- `reasons`
- `warnings`
- `blockers`
- `suggested_destination`
- `next_action`
- `confidence`

### Required nested fields

#### `candidate`
- `path`
- `artifact_type`

#### `score`
- `aggregate`
- `dimensions`

#### `score.dimensions`
- `reusable`
- `public_safe`
- `generic_enough`
- `stable_enough`
- `repo_fit`

#### `suggested_destination`
- `repo`
- `bucket`
- `path`
- `rationale`

#### `next_action`
- `code`
- `summary`

#### `confidence`
- `level`
- `value`
- `ambiguity_flags`

### Required-array behavior

The arrays `reasons`, `warnings`, `blockers`, and `confidence.ambiguity_flags` must always be present.
They may be empty, but must not be omitted.

This keeps consumer logic simple and avoids null-vs-missing drift.

---

## 5. Optional fields

The following fields are optional but recommended when available:

### Optional top-level fields
- `review`
- `provenance`
- `source_signals`
- `detected_topics`
- `normalization_notes`
- `sanitization_hints`
- `internal_only_notes`

### Optional `candidate` fields
- `title`
- `content_hash`
- `size_bytes`
- `created_at`
- `modified_at`

### Optional `score` fields
- `weights`
- `threshold_profile`
- `hard_block_present`

### Optional `review` fields
- `needed`
- `reason_codes`
- `questions`

### Optional `provenance` fields
- `evaluated_at`
- `tool_name`
- `tool_version`
- `policy_version`

Optional fields should enrich explainability, not replace the required contract.

---

## 6. Verdict enum and semantics

The field `verdict` must be exactly one of:
- `promote`
- `hold_internal`
- `sanitize_then_promote`
- `needs_review`

### 6.1 `promote`

Use when:
- no hard blocker prevents publication;
- the artifact is strongly reusable;
- it is public-safe as evaluated;
- it maps cleanly to a target bucket/path;
- ambiguity is low enough that review is not required.

Meaning:
- the artifact, or a lightly edited derivative, is suitable for product-repo promotion.

Expected field shape:
- `blockers` should be empty;
- `next_action.code` should usually be `copy_or_rewrite_for_product_repo`;
- `suggested_destination.path` should normally be populated.

### 6.2 `hold_internal`

Use when:
- the artifact is not sufficiently reusable;
- it is primarily internal operational evidence or local planning residue;
- repo fit is weak;
- or publication is not justified even if the content is technically public-safe.

Meaning:
- retain internally; do not prepare for promotion in the current contour.

Expected field shape:
- `suggested_destination.path` may be `null`;
- `next_action.code` should usually be `retain_internal_reference`.

### 6.3 `sanitize_then_promote`

Use when:
- the artifact appears reusable and repo-fit is adequate;
- but public-safe status is blocked by removable details such as sensitive identifiers, local paths, environment-bound details, or internal-only references.

Meaning:
- create a public-safe derivative or generalized rewrite, then rerun the gate.

Expected field shape:
- `blockers` should explain what blocks direct promotion;
- `sanitization_hints` is recommended;
- `next_action.code` should usually be `sanitize_then_rerun_gate`.

### 6.4 `needs_review`

Use when:
- competing signals exist;
- score and rule output do not justify a confident automated decision;
- destination is unclear;
- or ambiguity is real enough that a human architecture/operator decision should own the next step.

Meaning:
- do not silently choose promotion or hold; escalate with a bounded review package.

Expected field shape:
- `review.needed` should typically be `true`;
- `review.questions` should name what needs adjudication;
- `next_action.code` should usually be `request_architecture_review`.

---

## 7. Candidate object

The `candidate` object identifies the evaluated artifact.

```json
{
  "path": "task-manager/artifacts/example.md",
  "artifact_type": "markdown",
  "title": "Example artifact",
  "content_hash": "sha256:..."
}
```

### Required fields

#### `path`
Workspace-relative or repo-relative path to the evaluated artifact.

#### `artifact_type`
For the current contour, expected values are narrowly scoped, with `markdown` the primary supported type.

### Optional fields

#### `title`
Human-readable title when available from the document.

#### `content_hash`
Useful for deduplication, fixture stability, and auditability.

#### `size_bytes`, `created_at`, `modified_at`
Helpful but not required for v1 contract consumers.

---

## 8. Score object structure

The `score` object carries both aggregate and dimension-level scoring.

```json
{
  "aggregate": 0.84,
  "dimensions": {
    "reusable": 0.92,
    "public_safe": 0.88,
    "generic_enough": 0.79,
    "stable_enough": 0.81,
    "repo_fit": 0.83
  },
  "weights": {
    "reusable": 0.30,
    "public_safe": 0.30,
    "generic_enough": 0.15,
    "stable_enough": 0.10,
    "repo_fit": 0.15
  },
  "hard_block_present": false,
  "threshold_profile": "default_v0_1"
}
```

### Field semantics

#### `aggregate`
Normalized overall score in `[0.0, 1.0]`.
It is informative, but not sufficient by itself because blockers and ambiguity can override it.

#### `dimensions`
Normalized dimension scores in `[0.0, 1.0]` for:
- `reusable`
- `public_safe`
- `generic_enough`
- `stable_enough`
- `repo_fit`

#### `weights` optional
If surfaced, documents the profile used to calculate `aggregate`.
Useful for test reproducibility.

#### `hard_block_present` optional but recommended
Explicit boolean so consumers do not have to infer blocking solely from `blockers.length > 0`.

#### `threshold_profile` optional
Names the rule set used for decisioning.

### Score interpretation rule

Consumers must not treat a high aggregate score as promotion authority if:
- `blockers` is non-empty;
- `confidence.level` is low;
- or `verdict` is not `promote`.

---

## 9. Reasons, warnings, and blockers model

These fields separate positive rationale, non-fatal concerns, and decision-preventing conditions.

Each item should use a compact structured object, not bare strings.

### 9.1 Shared item shape

```json
{
  "code": "reusable_contract_spec",
  "message": "Defines a reusable contract for downstream implementation and tests.",
  "evidence": [
    "sections: purpose, object model, examples, acceptance criteria"
  ]
}
```

### Required fields for each item
- `code`
- `message`

### Optional fields for each item
- `evidence`
- `field`
- `severity`
- `suggested_fix`

### 9.2 `reasons`

Purpose:
- capture why the verdict is justified;
- especially useful for `promote`, `sanitize_then_promote`, and `needs_review`.

Guidance:
- include at least 1 reason;
- include 2–5 reasons when available;
- keep messages concise and decision-relevant.

### 9.3 `warnings`

Purpose:
- capture concerns that do not block the chosen verdict.

Examples:
- title still too workspace-specific;
- wording may need generalization;
- destination bucket plausible but not ideal.

### 9.4 `blockers`

Purpose:
- capture issues that prevent direct promotion.

Examples:
- sensitive environment-specific details;
- internal-only operational identifiers;
- unsupported/raw artifact class;
- strong ambiguity requiring review.

### Blocker rule

If `verdict = promote`, `blockers` must be empty.

If `verdict = sanitize_then_promote`, `blockers` should normally be non-empty and sanitizable.

If `verdict = hold_internal`, blockers may be empty or populated depending on whether the hold is due to low reuse versus a hard safety block.

---

## 10. Suggested destination object

The `suggested_destination` object gives the best current promotion target.

```json
{
  "repo": "product-repos/agent-architecture-kit",
  "bucket": "docs/architecture",
  "path": "docs/architecture/promotion-gate-verdict-schema-v1.md",
  "rationale": "Architecture contract artifact with direct downstream implementation value."
}
```

### Required fields

#### `repo`
Target repository name/path, or `null` when no promotion target is recommended.

#### `bucket`
Logical destination class such as:
- `docs/architecture`
- `docs/memory`
- `docs/evaluation`
- `examples`
- `schemas`
- `tests`

#### `path`
Suggested destination path within the target repo.
May be `null` for `hold_internal` or uncertain review cases.

#### `rationale`
Short explanation of why the target makes sense.

### Contract rule

A destination suggestion is a recommendation, not an execution order.
It should remain specific enough for the earlier implementation work/#400 style follow-on work.

---

## 11. Next action object

The `next_action` object translates the verdict into a bounded operational step.

```json
{
  "code": "copy_or_rewrite_for_product_repo",
  "summary": "Prepare a cleaned product-repo version and retain schema compatibility.",
  "owner_hint": "operator_or_architecture_lane"
}
```

### Required fields
- `code`
- `summary`

### Optional fields
- `owner_hint`
- `prerequisites`
- `suggested_artifacts`

### Recommended `code` enum
- `copy_or_rewrite_for_product_repo`
- `sanitize_then_rerun_gate`
- `retain_internal_reference`
- `request_architecture_review`
- `collect_stronger_evidence`

### Mapping guidance

| Verdict | Typical next action code |
|---|---|
| `promote` | `copy_or_rewrite_for_product_repo` |
| `sanitize_then_promote` | `sanitize_then_rerun_gate` |
| `hold_internal` | `retain_internal_reference` |
| `needs_review` | `request_architecture_review` |

`collect_stronger_evidence` may be used as an override when the real blocker is weak basis rather than content class.

---

## 12. Confidence and ambiguity handling

The gate must expose confidence explicitly because score alone does not communicate decision certainty.

### `confidence` object

```json
{
  "level": "high",
  "value": 0.86,
  "ambiguity_flags": []
}
```

### Required fields

#### `level`
Enum:
- `low`
- `medium`
- `high`

#### `value`
Normalized confidence value in `[0.0, 1.0]`.

#### `ambiguity_flags`
Array of machine-readable codes describing unresolved uncertainty.
Examples:
- `destination_unclear`
- `mixed_public_safety_signals`
- `borderline_reuse`
- `needs_human_judgment`
- `insufficient_basis`

### Optional fields
- `notes`
- `conflicting_signals`

### Confidence rules

1. A high score does not require high confidence.
2. `needs_review` should usually carry at least one ambiguity flag.
3. `promote` should usually have `confidence.level` of `medium` or `high`.
4. `sanitize_then_promote` may have high confidence if the removable blockers are clear.
5. `hold_internal` may also have high confidence when non-reusability is obvious.

---

## 13. Review object

The `review` object is optional, but recommended whenever `verdict = needs_review`.

```json
{
  "needed": true,
  "reason_codes": ["destination_unclear", "mixed_public_safety_signals"],
  "questions": [
    "Should this be split into architecture guidance and internal operational note?"
  ]
}
```

### Review guidance

Use `review.questions` to surface the smallest set of issues a human needs to decide.
Avoid turning review into a long narrative dump.

---

## 14. Provenance object

The `provenance` object supports auditability and test replay.

```json
{
  "evaluated_at": "2026-05-12T05:00:00Z",
  "tool_name": "promotion_gate.py",
  "tool_version": "0.1.0",
  "policy_version": "task-392-v0.1"
}
```

This section is optional in v1 but likely useful for verification packs.

---

## 15. JSON example payloads

### 15.1 Example — `promote`

```json
{
  "schema_version": "promotion_gate_verdict/v1",
  "candidate": {
    "path": "task-manager/artifacts/task-397-promotion-gate-verdict-schema-v1-2026-05-12.md",
    "artifact_type": "markdown",
    "title": "Promotion gate verdict schema v1"
  },
  "verdict": "promote",
  "score": {
    "aggregate": 0.87,
    "dimensions": {
      "reusable": 0.93,
      "public_safe": 0.92,
      "generic_enough": 0.84,
      "stable_enough": 0.81,
      "repo_fit": 0.85
    },
    "hard_block_present": false,
    "threshold_profile": "default_v0_1"
  },
  "reasons": [
    {
      "code": "contract_reusable",
      "message": "Defines a stable machine-readable contract for later gate implementation and tests."
    },
    {
      "code": "clear_repo_fit",
      "message": "Maps naturally into architecture and schema documentation for a product-facing kit."
    }
  ],
  "warnings": [
    {
      "code": "minor_editorial_cleanup",
      "message": "A product-repo derivative may still benefit from light wording cleanup."
    }
  ],
  "blockers": [],
  "suggested_destination": {
    "repo": "product-repos/agent-architecture-kit",
    "bucket": "schemas",
    "path": "schemas/promotion-gate-verdict-v1.schema.json",
    "rationale": "The contract is directly reusable by validators, tests, and automation hooks."
  },
  "next_action": {
    "code": "copy_or_rewrite_for_product_repo",
    "summary": "Prepare a repo-ready derivative and keep the contract unchanged.",
    "owner_hint": "architecture_lane"
  },
  "confidence": {
    "level": "high",
    "value": 0.88,
    "ambiguity_flags": []
  },
  "provenance": {
    "tool_name": "promotion_gate.py",
    "tool_version": "0.1.0",
    "policy_version": "task-392-v0.1"
  }
}
```

### 15.2 Example — `sanitize_then_promote`

```json
{
  "schema_version": "promotion_gate_verdict/v1",
  "candidate": {
    "path": "task-manager/artifacts/internal-architecture-note.md",
    "artifact_type": "markdown"
  },
  "verdict": "sanitize_then_promote",
  "score": {
    "aggregate": 0.76,
    "dimensions": {
      "reusable": 0.86,
      "public_safe": 0.41,
      "generic_enough": 0.78,
      "stable_enough": 0.72,
      "repo_fit": 0.80
    },
    "hard_block_present": true,
    "threshold_profile": "default_v0_1"
  },
  "reasons": [
    {
      "code": "strong_reuse_value",
      "message": "The artifact captures a reusable architecture pattern."
    }
  ],
  "warnings": [
    {
      "code": "local_naming_residue",
      "message": "Some local naming and environment references remain."
    }
  ],
  "blockers": [
    {
      "code": "environment_specific_details",
      "message": "Contains local operational identifiers that should not be promoted as-is.",
      "suggested_fix": "Replace local paths and identifiers with generalized placeholders."
    }
  ],
  "suggested_destination": {
    "repo": "product-repos/agent-architecture-kit",
    "bucket": "docs/architecture",
    "path": "docs/architecture/generalized-pattern.md",
    "rationale": "A sanitized derivative would fit architecture docs."
  },
  "next_action": {
    "code": "sanitize_then_rerun_gate",
    "summary": "Create a public-safe derivative and rerun the verdict."
  },
  "confidence": {
    "level": "high",
    "value": 0.83,
    "ambiguity_flags": []
  },
  "sanitization_hints": [
    "Remove internal identifiers.",
    "Generalize local path references."
  ]
}
```

### 15.3 Example — `hold_internal`

```json
{
  "schema_version": "promotion_gate_verdict/v1",
  "candidate": {
    "path": "task-manager/artifacts/raw-run-log.md",
    "artifact_type": "markdown"
  },
  "verdict": "hold_internal",
  "score": {
    "aggregate": 0.28,
    "dimensions": {
      "reusable": 0.18,
      "public_safe": 0.70,
      "generic_enough": 0.14,
      "stable_enough": 0.30,
      "repo_fit": 0.12
    },
    "hard_block_present": false,
    "threshold_profile": "default_v0_1"
  },
  "reasons": [
    {
      "code": "low_reuse",
      "message": "The artifact is mainly local execution residue rather than reusable reference content."
    }
  ],
  "warnings": [],
  "blockers": [],
  "suggested_destination": {
    "repo": null,
    "bucket": null,
    "path": null,
    "rationale": "No product-repo destination is justified for this artifact class."
  },
  "next_action": {
    "code": "retain_internal_reference",
    "summary": "Keep as internal evidence only."
  },
  "confidence": {
    "level": "high",
    "value": 0.91,
    "ambiguity_flags": []
  }
}
```

### 15.4 Example — `needs_review`

```json
{
  "schema_version": "promotion_gate_verdict/v1",
  "candidate": {
    "path": "task-manager/artifacts/mixed-policy-and-ops-note.md",
    "artifact_type": "markdown"
  },
  "verdict": "needs_review",
  "score": {
    "aggregate": 0.67,
    "dimensions": {
      "reusable": 0.74,
      "public_safe": 0.66,
      "generic_enough": 0.58,
      "stable_enough": 0.71,
      "repo_fit": 0.61
    },
    "hard_block_present": false,
    "threshold_profile": "default_v0_1"
  },
  "reasons": [
    {
      "code": "possible_reuse",
      "message": "The artifact may contain promotable architecture guidance."
    }
  ],
  "warnings": [
    {
      "code": "mixed_content_class",
      "message": "Architecture guidance and internal operations content are interleaved."
    }
  ],
  "blockers": [
    {
      "code": "needs_human_judgment",
      "message": "Automated classification is insufficiently certain for direct promotion or hold."
    }
  ],
  "suggested_destination": {
    "repo": "product-repos/agent-architecture-kit",
    "bucket": "docs/architecture",
    "path": null,
    "rationale": "A promotable subset may exist, but the destination shape needs review."
  },
  "next_action": {
    "code": "request_architecture_review",
    "summary": "Review whether this should be split, sanitized, or retained internally."
  },
  "confidence": {
    "level": "medium",
    "value": 0.54,
    "ambiguity_flags": ["mixed_public_safety_signals", "destination_unclear"]
  },
  "review": {
    "needed": true,
    "reason_codes": ["mixed_public_safety_signals", "destination_unclear"],
    "questions": [
      "Should the reusable guidance be extracted into a separate promotable artifact?"
    ]
  }
}
```

---

## 16. Acceptance criteria

This schema artifact is acceptable if:
- [x] it defines a single stable top-level verdict object;
- [x] required vs optional fields are explicit;
- [x] all four verdict classes have unambiguous semantics;
- [x] score structure is defined with aggregate and dimension scores;
- [x] reasons, warnings, and blockers are separately modeled;
- [x] destination and next-action contract is explicit;
- [x] confidence and ambiguity are first-class fields;
- [x] examples exist for all four verdicts;
- [x] the contract is compact enough for #398/#399/#400 implementation use.

---

## 17. Open questions

1. Should `needs_review` always require a blocker item, or is ambiguity in `confidence` + `review` enough?
2. Should `suggested_destination.repo` be nullable for all non-`promote` verdicts, or should likely targets still be surfaced when useful?
3. Should reason/warning/blocker items eventually carry source spans or line references for richer explainability?
4. Should `confidence.value` be implementation-owned, or derived from score dispersion plus hard-rule clarity?
5. Should the machine-readable schema allow extra properties broadly, or be stricter for regression stability?
6. For future non-markdown inputs, should `candidate` gain subtype-specific detail objects?

---

## 18. Reuse note

This artifact appears reusable and public-safe enough that it likely qualifies for later promotion into `agent-architecture-kit` after light cleanup and destination adaptation, but no promotion is performed in this bounded run.
