# Task 392 — Architecture promotion gate script v0.1 spec

Date: 2026-05-12
Task: #392
Status: bounded completion artifact
Scope: define a compact but implementation-ready specification for a markdown-first promotion gate that decides whether an internal architecture artifact should remain internal, be sanitized, or be promoted into `product-repos/agent-architecture-kit`

---

## 1. Purpose

This spec turns the current repo-promotion guidance from prose into a bounded decision contract that later implementation tasks can execute consistently.

The v0.1 gate should answer three linked questions for a candidate artifact:
1. is this artifact reusable outside the local workspace?
2. is it public-safe enough for the product repo now?
3. if it is promotable, where should it go and what should happen next?

The goal is not full automation of publication. The goal is a reliable machine-readable architecture decision point.

---

## 2. Scope and non-goals

### 2.1 In scope for v0.1

- markdown artifacts as the first supported input class;
- one or more candidate paths per invocation;
- machine-readable JSON verdict output;
- explicit reasons, destination suggestion, and next-action mapping;
- rule-based checks for:
  - reusable;
  - public-safe;
  - generic enough;
  - stable enough;
  - repo-fit;
- bounded trigger path for manual or task-close execution;
- support for `agent-architecture-kit` destination buckets.

### 2.2 Out of scope for v0.1

- auto-committing or auto-pushing to the product repo by default;
- broad support for code, tests, schemas, or mixed binary assets;
- LLM-dependent classification as a hard requirement;
- fully autonomous sanitization or rewriting;
- deep semantic deduplication against all existing product-repo docs;
- replacing human review for ambiguous architecture decisions.

### 2.3 Design constraints

- prefer deterministic rule logic over fuzzy keyword-only guessing;
- treat false promotion as worse than missed promotion;
- make every verdict explainable from surfaced evidence;
- keep the first version thin enough to implement in a single small script and bounded tests.

---

## 3. Decision model

The gate should evaluate a candidate across five dimensions and then produce a verdict class.

### 3.1 Dimensions

1. **Reusable**
   - asks whether the artifact captures a pattern, contract, spec, worked example, policy, or mapping that could help outside one local run.
2. **Public-safe**
   - asks whether the artifact is safe to move into a public or product-facing repo without leaking secrets, identifiers, private notes, or environment-bound operational detail.
3. **Generic enough**
   - asks whether the framing is architecture/reference oriented rather than transcript residue, local operator chatter, or narrow one-off operational debris.
4. **Stable enough**
   - asks whether the artifact appears complete enough to serve as a reusable reference rather than a scratchpad.
5. **Repo-fit**
   - asks whether the artifact maps clearly into a destination area of `agent-architecture-kit`.

### 3.2 Decision posture

- `public_safe` is the primary blocking dimension.
- `repo_fit` and `reusable` are primary promotion enablers.
- `generic_enough` and `stable_enough` are quality gates that distinguish `promote` from `needs_review` or `hold_internal`.
- Any hard block should override aggregate score.

### 3.3 Hard blocks

The gate should return at least `hold_internal` or `sanitize_then_promote` when it detects:
- secrets, tokens, credentials, or private keys;
- raw user/private memory content or obviously sensitive personal data;
- environment-specific operational values that should not be published as-is;
- artifact classes that are clearly backups, raw logs, raw transcript dumps, or internal-only state packages;
- missing readable content or unsupported file class in v0.1.

---

## 4. Verdict classes and semantics

The gate must emit one of four verdicts.

### 4.1 `promote`

Use when:
- no hard block is present;
- reusable, public-safe, and repo-fit are all strong;
- artifact is generic and stable enough for direct reuse.

Meaning:
- candidate likely belongs in the product repo after at most light editorial cleanup.

### 4.2 `sanitize_then_promote`

Use when:
- artifact is reusable and repo-fit is strong;
- but publication is blocked by removable sensitive or environment-bound details.

Meaning:
- create a sanitized derivative or generalized rewrite, then re-run gate on that derivative.

### 4.3 `hold_internal`

Use when:
- artifact is not meaningfully reusable;
- or is inherently internal/operational;
- or is too tied to local execution state to justify product-repo placement.

Meaning:
- keep in workspace and optionally label as internal-only reference/evidence.

### 4.4 `needs_review`

Use when:
- the artifact looks potentially promotable but ambiguity remains;
- destination is unclear;
- or signals conflict in a way deterministic rules should not resolve alone.

Meaning:
- escalate to architecture/operator review with surfaced reasons and competing cues.

---

## 5. Rule logic and scoring model

v0.1 should use a hybrid of deterministic hard rules plus simple weighted scores.

### 5.1 Dimension scoring

Each dimension should produce a normalized score in `[0.0, 1.0]`.

Suggested dimensions:
- `reusable`
- `public_safe`
- `generic_enough`
- `stable_enough`
- `repo_fit`

### 5.2 Suggested weights

```text
reusable        0.30
public_safe     0.30
generic_enough  0.15
stable_enough   0.10
repo_fit        0.15
```

Aggregate score:

```text
aggregate =
  reusable * 0.30 +
  public_safe * 0.30 +
  generic_enough * 0.15 +
  stable_enough * 0.10 +
  repo_fit * 0.15
```

### 5.3 Suggested threshold logic

Use hard blocks first, then thresholds.

1. If `hard_block == true` and artifact still appears reusable after sanitization:
   - verdict = `sanitize_then_promote`
2. If `hard_block == true` and artifact is inherently internal:
   - verdict = `hold_internal`
3. Else if:
   - `reusable >= 0.70`
   - `public_safe >= 0.85`
   - `repo_fit >= 0.60`
   - `generic_enough >= 0.60`
   - `stable_enough >= 0.55`
   - `aggregate >= 0.72`
   then verdict = `promote`
4. Else if:
   - `reusable >= 0.70`
   - `repo_fit >= 0.60`
   - `public_safe` is impaired mostly by sanitizable details
   then verdict = `sanitize_then_promote`
5. Else if:
   - `reusable < 0.45` or `repo_fit < 0.35`
   then verdict = `hold_internal`
6. Else:
   - verdict = `needs_review`

### 5.4 Example signals by dimension

#### Reusable positive signals
- title and purpose are explicit;
- sections define contract, policy, schema, mapping, examples, or acceptance criteria;
- language is framed as general guidance or reusable architecture;
- artifact references durable concepts rather than one transient chat event.

#### Reusable negative signals
- mostly a run log or one-off execution diary;
- content depends on unexplained local context;
- no reusable abstraction beyond local completion proof.

#### Public-safe positive signals
- no secrets or tokens;
- no raw private memory excerpts;
- host/path references are genericized or absent;
- identifiers appear illustrative rather than operational.

#### Public-safe negative/blocking signals
- credentials, tokens, access secrets;
- exact internal-only endpoints, private chat ids, personal identifiers, raw internal traces;
- unredacted absolute host/user paths that reveal sensitive environment detail when not necessary.

#### Generic-enough positive signals
- architecture tone;
- references to patterns, components, objects, contracts, workflows;
- minimal local operator residue.

#### Generic-enough negative signals
- “for this one run only” framing;
- narrow local housekeeping with no generalization;
- transcript-like back-and-forth fragments.

#### Stable-enough positive signals
- structured sections;
- conclusion or bounded completion summary;
- no obvious TODO-only scratch state.

#### Stable-enough negative signals
- outline-only fragments with unresolved placeholders dominating content;
- incomplete sentence fragments or pure brainstorm notes;
- contradictory or abandoned structure.

#### Repo-fit positive signals
- clear mapping to architecture, memory, evaluation, examples, schemas, or implementation docs;
- title and sections align with product-repo information architecture.

#### Repo-fit negative signals
- no clear destination bucket;
- primarily evidence/logs/backups rather than reference content.

---

## 6. Verdict schema

The gate should emit JSON to stdout in v0.1.

```json
{
  "candidate": "task-manager/artifacts/task-392-architecture-promotion-gate-script-v0-1-spec-2026-05-12.md",
  "artifact_type": "markdown",
  "verdict": "promote",
  "aggregate_score": 0.86,
  "score": {
    "reusable": 0.94,
    "public_safe": 0.93,
    "generic_enough": 0.88,
    "stable_enough": 0.82,
    "repo_fit": 0.84
  },
  "hard_blocks": [],
  "warnings": [],
  "reasons": [
    "defines a reusable architecture decision contract",
    "maps clearly into architecture documentation",
    "contains no detected sensitive operational material"
  ],
  "suggested_destination": {
    "repo": "product-repos/agent-architecture-kit",
    "path": "docs/architecture/promotion-gate-script-v0-1.md",
    "bucket": "docs/architecture"
  },
  "next_action": "copy_or_rewrite_for_product_repo",
  "review_notes": [],
  "version": "promotion-gate-spec-v0.1"
}
```

### 6.1 Required fields

- `candidate`
- `artifact_type`
- `verdict`
- `aggregate_score`
- `score`
- `reasons`
- `suggested_destination`
- `next_action`
- `version`

### 6.2 Optional fields

- `hard_blocks`
- `warnings`
- `review_notes`
- `source_signals`
- `detected_topics`

### 6.3 Schema behavior notes

- `suggested_destination.path` may be `null` when verdict is `hold_internal`.
- `next_action` should remain bounded and class-like, not a giant procedural plan.
- `reasons` should be human-readable and concise.

---

## 7. Destination mapping

The gate should suggest a destination bucket only when reusable and repo-fit are sufficiently strong.

### 7.1 Primary destination buckets for v0.1

- `docs/architecture/`
- `docs/memory/`
- `docs/evaluation/`
- `examples/`
- `schemas/`
- `tests/`
- `src/agent_architecture_kit/` only as a future-facing placeholder in v0.1, not default for markdown

### 7.2 Mapping heuristics

| Artifact signals | Suggested destination |
|---|---|
| architecture layers, contracts, runtime mapping, orchestration rules | `docs/architecture/` |
| memory object model, serving policy, retrieval boundaries, note taxonomy | `docs/memory/` |
| verification scenarios, judges, regression packs, acceptance checks | `docs/evaluation/` or `tests/` |
| worked scenarios, templates, example walkthroughs | `examples/` |
| machine-readable contracts or JSON/YAML schemas | `schemas/` |

### 7.3 Hold mapping

Artifacts should default to internal hold when they are primarily:
- run evidence;
- deployment-specific notes;
- raw backups;
- transient local planning with no reusable abstraction;
- sensitive operator records.

---

## 8. Action mapping

The verdict should map to a next-action class.

| Verdict | Next action | Meaning |
|---|---|---|
| `promote` | `copy_or_rewrite_for_product_repo` | perform bounded product-repo adaptation and re-check if needed |
| `sanitize_then_promote` | `sanitize_then_rerun_gate` | create public-safe derivative, then re-evaluate |
| `hold_internal` | `retain_internal_reference` | keep in workspace; optionally add internal-only label/note |
| `needs_review` | `request_architecture_review` | operator/architect decides destination or classification |

### 8.1 Important v0.1 limit

The gate should recommend actions, not execute repo writes by default. This preserves low-risk adoption and makes the gate usable before automation hooks are trusted.

---

## 9. Trigger integration path

### 9.1 Recommended first trigger

**Manual task-close or artifact-close trigger**

Run the gate when:
- a bounded architecture artifact is declared complete;
- a task note says the artifact may be reusable/public-safe;
- or an operator explicitly requests promotion evaluation.

Why this first:
- lowest noise;
- easiest to reason about;
- matches the current bounded-completion workflow from tasks #391/#393.

### 9.2 Follow-on trigger options

1. **Task-close hook**
   - when a task in a selected architecture/memory/evaluation lane is closed, run gate against linked artifacts.
2. **Folder batch scan**
   - periodically scan `task-manager/artifacts/` for new candidate docs and produce a promotion queue.
3. **Promotion queue report**
   - emit a short report of `promote` and `sanitize_then_promote` candidates for review.

### 9.3 Trigger contract recommendation

v0.1 should support CLI usage like:

```bash
python3 scripts/architecture/promotion_gate.py \
  --candidate task-manager/artifacts/foo.md \
  --target-repo product-repos/agent-architecture-kit \
  --format json
```

Recommended options:
- `--candidate <path>` repeatable
- `--target-repo <path>`
- `--format json|text`
- `--check-only`
- `--suggest-destination`
- `--emit-action-plan`

---

## 10. Bounded v0.1 implementation plan

This section is intentionally implementation-facing but still spec-level.

### 10.1 Deliverable shape

Suggested script path:
- `scripts/architecture/promotion_gate.py`

Suggested bounded support files later:
- `tests/architecture/test_promotion_gate.py`
- `task-manager/artifacts/verification-task-392-promotion-gate-fixtures/` or equivalent fixtures folder

### 10.2 Implementation slices

#### Slice A — input and parsing
- accept repeatable candidate paths;
- reject unsupported file types cleanly;
- read markdown content and basic metadata.

#### Slice B — hard-block detection
- detect obvious secrets/tokens/private-key material;
- detect obvious backup/raw-log/internal-only classes;
- detect likely environment leakage patterns.

#### Slice C — dimension scoring
- compute simple rule-based scores for reusable/public-safe/generic/stable/repo-fit;
- emit reasons and warnings from matched signals.

#### Slice D — verdict and destination selection
- apply threshold logic;
- map likely destination bucket;
- emit action class.

#### Slice E — bounded verification
- add known-pass, known-sanitize, known-hold, and known-review fixtures;
- verify JSON shape and verdict class consistency.

### 10.3 Explicit non-requirements for v0.1 implementation

- no Git integration required;
- no commit generation required;
- no rewriting engine required;
- no public repo write path required.

---

## 11. Acceptance criteria

### 11.1 Spec acceptance

- [x] Scope and non-goals are explicit.
- [x] Decision dimensions and hard blocks are defined.
- [x] Verdict semantics are unambiguous.
- [x] JSON verdict schema is defined.
- [x] Destination mapping exists for `agent-architecture-kit` buckets.
- [x] Action mapping is bounded.
- [x] Trigger integration path is defined.
- [x] Implementation plan is sliced for later tasks.

### 11.2 Implementation-ready acceptance for follow-up tasks #397/#398/#399/#400

A later implementation should be considered successful when:
- it runs on markdown candidates from the workspace;
- it emits valid JSON matching the schema above;
- it distinguishes at least one fixture for each verdict class;
- it produces explainable reasons, not score-only output;
- it suggests a non-null destination for promotable cases;
- it avoids auto-promoting artifacts with hard public-safety blocks.

---

## 12. Open questions

1. Should absolute paths always be treated as public-safety warnings, or only when they appear environment-sensitive and non-essential?
2. Should task ids and artifact ids be allowed in product docs when they function as provenance references, or should they be generalized during promotion?
3. For v0.1, should `needs_review` be preferred over `hold_internal` when repo-fit is unclear but reusability is high?
4. Should destination mapping later consult existing product-repo file names to avoid duplicate concept pages?
5. Should a future v0.2 support a `sanitization hints` field with concrete rewrite suggestions?

---

## 13. Why this is a good bounded completion

This artifact is strong enough to serve as the direct contract input for later implementation tasks because it defines:
- the decision model;
- the verdict schema;
- the rule and threshold logic;
- the destination and next-action mappings;
- the bounded trigger and implementation path.

It stays compact by limiting v0.1 to markdown-first deterministic checks, while still being extensible to code/tests/schemas later.

This spec itself also appears likely reusable and public-safe enough for later promotion into `agent-architecture-kit` after light editorial cleanup, but that promotion is intentionally out of scope for this run.
