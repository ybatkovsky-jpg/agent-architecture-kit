# Task 401 — OpenClaw Frame scenario pack for continuation, anchor, context, and gate flows

Date: 2026-05-12
Task: #401
Parent contour: OpenClaw Frame next-stage continuation / anchor / context / gate verification
Status: bounded completion artifact
Scope: compact bounded acceptance scenario pack directly usable by downstream verification and implementation work

---

## 1. Purpose

This scenario pack defines bounded acceptance scenarios for the new OpenClaw Frame contour across four policy/contract families:
- continuation contract behavior;
- canonical anchor and storage behavior;
- context serving behavior;
- promotion gate behavior.

The scenarios are intentionally compact and spec-oriented.
They are designed to verify whether a future implementation preserves the intended authority rules, bounded recovery rules, and output shapes described in tasks #393–#400.

---

## 2. Scenario family map

| Family | Coverage intent |
|---|---|
| Continuation | verify `PREPARED/ACK/RUNNING/DONE/BLOCKED`, resume-basis discipline, and terminal return requirements |
| Anchor/storage | verify canonical-vs-projection boundaries, default storage placement, and recovery/supersession behavior |
| Context serving | verify always-on vs on-demand vs forbidden ambient context, authority ordering, and uncertainty behavior |
| Promotion gate | verify verdict/output shape, lane semantics, ambiguity signaling, and bounded next-action behavior |

---

## 3. Bounded acceptance scenarios

## A. Continuation contract scenarios

### SCN-CONT-01 — Normal bounded continuation completion
- **Prompt / operator request**: “The mapping matrix and prerequisite artifacts exist. Continue by drafting the compact contract artifact and return the result anchor.”
- **Request / verification class**: `resume_reopen_continuation` / normal completion
- **Expected output / behavior shape**:
  - handoff package exists or is referenced;
  - continuation emits `ACK` after accepting execution ownership;
  - bounded work completes with terminal `DONE` return;
  - return package includes summary, next action, durable result anchor, and result kind.
- **Expected authority / anchor / projection behavior**:
  - authority comes from handoff package plus explicit resume basis, not transcript residue;
  - result truth is the produced artifact path;
  - any chat summary is projection-only and cites the artifact.
- **Pass criteria**:
  - `ACK` precedes `DONE`;
  - resume basis is explicit and anchorable;
  - `DONE` includes durable result anchor outside chat;
  - next action is stated.
- **Fail criteria**:
  - direct completion with no accepted basis;
  - summary-only completion with no artifact/result anchor;
  - transcript tail treated as sole resume authority.

### SCN-CONT-02 — Immediate blocked-before-ACK due to invalid resume basis
- **Prompt / operator request**: “Continue this bounded run from the earlier stop point,” where the cited prerequisite artifact is missing or invalid.
- **Request / verification class**: `resume_reopen_continuation` / invalid basis rejection
- **Expected output / behavior shape**:
  - continuation attempt returns `BLOCKED` directly from `PREPARED`;
  - blocked package names missing/invalid basis, owner for decision, and recovery suggestion.
- **Expected authority / anchor / projection behavior**:
  - authority check happens against explicit basis anchor;
  - no fake `ACK` is emitted when execution ownership should not be accepted.
- **Pass criteria**:
  - blocked return is explicit and terminal for the attempt;
  - blocker identifies concrete missing prerequisite or invalid anchor;
  - decision owner is named.
- **Fail criteria**:
  - emits `ACK` despite lacking valid basis;
  - ambiguous “can’t continue” prose with no blocked package;
  - silent retry or dangling limbo state.

### SCN-CONT-03 — Blocked after ACK due to authority gap
- **Prompt / operator request**: “Continue and finish the next bounded step if possible,” but completion requires a human or `main` decision not delegated locally.
- **Request / verification class**: `resume_reopen_continuation` / authority-bound blockage
- **Expected output / behavior shape**:
  - `ACK` is emitted because execution ownership was validly accepted;
  - later terminal return is `BLOCKED`;
  - blocked package captures attempted scope, blocked reason, owner for decision, and recovery suggestion.
- **Expected authority / anchor / projection behavior**:
  - execution authority is local only up to the point of decision gap;
  - blocked package becomes current continuation truth for that attempt;
  - parent/task truth should be reflectable from it.
- **Pass criteria**:
  - local work stops at authority boundary;
  - `owner_for_decision` is explicit;
  - recovery suggestion names concrete next prerequisite or decision.
- **Fail criteria**:
  - model guesses or fabricates decision authority;
  - blocked state exists only in narrative chat;
  - same attempt is implicitly reopened without fresh trigger.

### SCN-CONT-04 — Reopen after blocker cleared using new trigger lineage
- **Prompt / operator request**: “The prior blocker is cleared by decision note X / artifact Y. Resume from the blocked return and finish the next bounded slice.”
- **Request / verification class**: `resume_reopen_continuation` / chained continuation lineage
- **Expected output / behavior shape**:
  - a new resume trigger references the prior blocked package and new basis anchor;
  - a new continuation attempt is started rather than mutating the old one;
  - terminal state is `DONE` or `BLOCKED` for the new attempt.
- **Expected authority / anchor / projection behavior**:
  - new basis explains what changed and why continuation is justified now;
  - prior blocked attempt remains historical truth, not overwritten.
- **Pass criteria**:
  - explicit prior-attempt linkage exists;
  - new attempt has distinct continuation identity;
  - consumed basis snapshot restates the now-valid reason.
- **Fail criteria**:
  - old blocked attempt is silently reused as if still open;
  - no new trigger/basis is recorded;
  - recovery depends on transcript reconstruction.

## B. Canonical anchor and storage scenarios

### SCN-ANCH-01 — Completion summary must not replace result anchor
- **Prompt / operator request**: “Summarize the finished bounded task for the operator.”
- **Request / verification class**: projection-versus-canonical verification
- **Expected output / behavior shape**:
  - operator-visible summary may be concise;
  - summary cites task id and artifact/result path;
  - canonical truth remains the return package plus result artifact.
- **Expected authority / anchor / projection behavior**:
  - summary is projection only unless explicitly promoted to task note/artifact;
  - result anchor remains evidence truth.
- **Pass criteria**:
  - summary points back to canonical anchors;
  - recovery can succeed even if chat summary is absent.
- **Fail criteria**:
  - “done” message is the only completion record;
  - summary introduces authoritative state not reflected elsewhere.

### SCN-ANCH-02 — Human decision in chat requires durable reflection
- **Prompt / operator request**: Human replies in chat, “Use option B and continue.”
- **Request / verification class**: human-decision reflection
- **Expected output / behavior shape**:
  - the decision is recorded in a task note, decision note, or explicit continuation-basis artifact;
  - subsequent continuation references the reflected decision anchor.
- **Expected authority / anchor / projection behavior**:
  - raw chat alone is not sufficient authority for restartable execution;
  - reflected decision becomes canonical human-decision truth.
- **Pass criteria**:
  - durable reflection exists before or alongside resumed execution;
  - later recovery can find the decision without transcript archaeology.
- **Fail criteria**:
  - continuation proceeds using raw chat as sole basis;
  - no durable note or artifact records the decision.

### SCN-ANCH-03 — Recovery prefers canonical layers over projections
- **Prompt / operator request**: “We lost the chat tail. Recover current status and next action.”
- **Request / verification class**: recovery-order verification
- **Expected output / behavior shape**:
  - recovery starts from task truth, latest continuation anchor, and linked evidence;
  - response states current status and next owner using canonical objects.
- **Expected authority / anchor / projection behavior**:
  - precedence: task truth > continuation truth > evidence truth > memory truth > projections.
- **Pass criteria**:
  - answer is derivable from task/continuation/evidence anchors;
  - no dependency on transcript tail for primary recovery.
- **Fail criteria**:
  - operator must reconstruct status from vague old summaries;
  - projection outranks current canonical state when they disagree.

### SCN-ANCH-04 — New attempt supersedes current continuation without erasing lineage
- **Prompt / operator request**: “Create a fresh continuation attempt after the prior blocked run.”
- **Request / verification class**: supersession and lineage verification
- **Expected output / behavior shape**:
  - new handoff/trigger/continuation objects are created or referenced;
  - prior attempt remains preserved as historical truth;
  - latest valid attempt becomes current continuation truth.
- **Expected authority / anchor / projection behavior**:
  - supersession occurs within the same truth class and lineage only;
  - newer summary alone does not supersede an older canonical artifact.
- **Pass criteria**:
  - lineage between attempts is explicit;
  - current-vs-historical attempt can be distinguished.
- **Fail criteria**:
  - newer prose summary implicitly overwrites artifact history;
  - previous blocked package disappears from recoverable record.

## C. Context serving scenarios

### SCN-CTX-01 — Status request serves only thin always-on orientation pack
- **Prompt / operator request**: “Where are we now and what is next?”
- **Request / verification class**: `current_task_execution` / status serving
- **Expected output / behavior shape**:
  - response is built from current task state, current-branch continuation anchor, and at most a compact current summary note;
  - no broad historical retrieval bundle is loaded by default.
- **Expected authority / anchor / projection behavior**:
  - current task truth and current continuation truth dominate;
  - old transcripts and generic wiki material stay out of ambient context.
- **Pass criteria**:
  - answer is fresh, concise, and anchored to current state;
  - always-on pack remains small and authority-bearing.
- **Fail criteria**:
  - large mixed context bundle is injected for a simple status request;
  - stale historical material displaces current task state.

### SCN-CTX-02 — Continuation request must not reconstruct from transcript
- **Prompt / operator request**: “Continue after the last bounded step.”
- **Request / verification class**: `resume_reopen_continuation` / continuity serving
- **Expected output / behavior shape**:
  - serving retrieves current task state, immediate predecessor continuation basis, and latest terminal package;
  - if basis is missing, the answer surfaces the gap instead of faking continuity.
- **Expected authority / anchor / projection behavior**:
  - transcript tails are forbidden ambient input;
  - canonical-first continuity is enforced.
- **Pass criteria**:
  - resume point is traced to explicit current anchors;
  - uncertainty is surfaced when basis is incomplete.
- **Fail criteria**:
  - model narratively guesses where to continue from chat residue;
  - unrelated older continuations are silently blended in.

### SCN-CTX-03 — Rationale question retrieves decision/spec layers on demand
- **Prompt / operator request**: “Why is `retrieval_document` treated as a derived layer rather than source of truth?”
- **Request / verification class**: `policy_decision_lookup` / rationale serving
- **Expected output / behavior shape**:
  - decision note/spec sections are retrieved on demand;
  - answer cites governing policy/rationale, optionally supported by evidence.
- **Expected authority / anchor / projection behavior**:
  - decision memory/spec anchors outrank generic retrieval documents;
  - retrieval documents may assist discovery but not act as truth source.
- **Pass criteria**:
  - rationale is grounded in decision/spec artifacts;
  - answer distinguishes rationale from evidence/proof.
- **Fail criteria**:
  - answer is built only from retrieval snippets;
  - derived documents silently outrank governing spec text.

### SCN-CTX-04 — Audit request prioritizes proving artifacts over meta-artifacts
- **Prompt / operator request**: “Show the exact files that prove this bounded verification claim.”
- **Request / verification class**: `artifact_source_trace_request` / audit serving
- **Expected output / behavior shape**:
  - direct evidence files and exact paths are retrieved first;
  - framing task/spec artifacts may be included secondarily.
- **Expected authority / anchor / projection behavior**:
  - evidence truth dominates for proof-trace requests;
  - scenario packs or summaries that merely mention the proof do not replace it.
- **Pass criteria**:
  - answer cites direct proving artifacts;
  - scope framing remains bounded.
- **Fail criteria**:
  - audit answer cites only evaluation packs or summaries;
  - no distinction between proof object and descriptive meta-artifact.

### SCN-CTX-05 — Weak evidence must reduce confidence, not inflate it
- **Prompt / operator request**: “What’s the preferred operating style here?” when no durable preference note exists.
- **Request / verification class**: `preference_operating_style_recall` / weak-evidence handling
- **Expected output / behavior shape**:
  - answer states that evidence is weak or absent;
  - falls back to safe default behavior;
  - may suggest creating a durable preference note.
- **Expected authority / anchor / projection behavior**:
  - weak transcript hints do not become durable preference truth;
  - confidence is driven by authority/freshness, not volume.
- **Pass criteria**:
  - uncertainty is explicit;
  - no fabricated preference memory is claimed.
- **Fail criteria**:
  - assistant invents stable preference from chat tone or old summaries;
  - large context volume is used to imply confidence.

## D. Promotion gate scenarios

### SCN-GATE-01 — Strong reusable/public-safe artifact yields `promote`
- **Prompt / operator request**: “Evaluate this reusable contract/spec artifact for product-repo promotion.”
- **Request / verification class**: promotion-gate decision / direct promote lane
- **Expected output / behavior shape**:
  - verdict object conforms to `promotion_gate_verdict/v1`;
  - `verdict = promote`;
  - blockers are empty;
  - destination repo/bucket/path and next action are populated.
- **Expected authority / anchor / projection behavior**:
  - candidate artifact path is the evaluated anchor;
  - verdict is a decision object, not a prose-only recommendation.
- **Pass criteria**:
  - required fields are present;
  - verdict semantics align with reusable/public-safe/low-ambiguity case;
  - suggested destination is specific.
- **Fail criteria**:
  - missing required sections/arrays;
  - prose recommendation with no structured verdict object;
  - `promote` returned with blockers present.

### SCN-GATE-02 — Internal-only or low-reuse artifact yields `hold_internal`
- **Prompt / operator request**: “Evaluate this local operational residue artifact for promotion.”
- **Request / verification class**: promotion-gate decision / hold-internal lane
- **Expected output / behavior shape**:
  - `verdict = hold_internal`;
  - destination path may be `null`;
  - next action usually retains internal reference.
- **Expected authority / anchor / projection behavior**:
  - decision is based on low reuse/repo-fit or internal-operational nature, not just safety.
- **Pass criteria**:
  - hold decision is explicit and structured;
  - rationale distinguishes internal retention from sanitization or ambiguity.
- **Fail criteria**:
  - artifact is promoted merely because it is technically safe;
  - verdict leaves next action undefined.

### SCN-GATE-03 — Sanitizable sensitivity yields `sanitize_then_promote`
- **Prompt / operator request**: “Evaluate this architecture artifact that contains reusable content plus removable internal paths/identifiers.”
- **Request / verification class**: promotion-gate decision / sanitization lane
- **Expected output / behavior shape**:
  - `verdict = sanitize_then_promote`;
  - blockers identify removable public-safety issues;
  - sanitization hints are recommended;
  - next action is rerun-gate after sanitization.
- **Expected authority / anchor / projection behavior**:
  - candidate artifact remains current evidence anchor;
  - direct promotion is blocked until rewritten derivative exists.
- **Pass criteria**:
  - blockers are concrete and sanitizable;
  - destination remains meaningful after cleanup;
  - next action requests sanitize-then-rerun.
- **Fail criteria**:
  - sensitive artifact is directly promoted;
  - hold-internal is chosen when reusable/sanitizable path is the better bounded action.

### SCN-GATE-04 — Competing destination signals yield `needs_review`
- **Prompt / operator request**: “Evaluate this artifact that scores reasonably well but fits multiple buckets and has ambiguous genericity.”
- **Request / verification class**: promotion-gate decision / ambiguity-review lane
- **Expected output / behavior shape**:
  - `verdict = needs_review`;
  - confidence shows ambiguity flags;
  - review section/questions are present when available;
  - next action requests architecture/operator review.
- **Expected authority / anchor / projection behavior**:
  - ambiguity is represented explicitly rather than hidden behind average score;
  - structured verdict remains the canonical decision object.
- **Pass criteria**:
  - ambiguity is visible in `confidence` and/or review fields;
  - automated system does not silently force promote/hold.
- **Fail criteria**:
  - aggregate score alone decides the lane despite meaningful ambiguity;
  - review-needed case is flattened into confident prose.

### SCN-GATE-05 — Schema-shape validation for all verdict lanes
- **Prompt / operator request**: “Verify that the emitted gate verdict is consumable by downstream scripts/tests.”
- **Request / verification class**: verdict-schema conformance
- **Expected output / behavior shape**:
  - every verdict includes required top-level fields and required nested fields;
  - arrays `reasons`, `warnings`, `blockers`, and `confidence.ambiguity_flags` are always present.
- **Expected authority / anchor / projection behavior**:
  - the verdict object itself is the canonical machine-readable decision anchor.
- **Pass criteria**:
  - schema version, candidate, score, destination, next action, and confidence sections are present and typed as expected;
  - empty arrays are present when applicable.
- **Fail criteria**:
  - missing arrays/sections cause consumers to infer absent values;
  - lane semantics depend on freeform prose outside the schema object.

---

## 4. Cross-family acceptance checks

The implementation contour should also satisfy these cross-cutting checks:

1. **Transcript-first recovery must fail verification** unless transcript use was explicitly requested for audit/quote/conflict inspection.
2. **Operator-visible summaries must remain projections** unless explicitly promoted into task/artifact truth.
3. **Every bounded completion or blockage must be anchorable outside chat.**
4. **Authority gaps must surface owner and recovery path** rather than be guessed through.
5. **On-demand retrieval must not outrank stronger current canonical objects** for status/continue flows.
6. **Promotion gate outputs must remain structured decision objects** even when the consumer also wants a short prose summary.

---

## 5. Direct downstream use

This pack is intended to be directly usable by #402 as a bounded verification/spec input for:
- fixture authoring;
- acceptance test matrix construction;
- implementation spot checks;
- regression scenarios for continuation/context/gate flows.

---

## 6. Unresolved questions

1. Should continuation and return packages be validated in markdown-with-frontmatter, JSON, or dual-format fixtures first?
2. Which exact task-manager fields will carry the authoritative linkage for “current branch” and latest terminal attempt in runtime verification?
3. For audit serving, should meta-artifacts be explicitly suppressed whenever direct evidence is available, or merely down-ranked?
4. Should promotion-gate scenario fixtures remain markdown-only in the first verification pass, or include non-markdown negative fixtures immediately?

---

## 7. Bounded completion summary

This artifact completes the scoped need for task #401 by defining a compact but strong scenario pack across:
- continuation contract behavior;
- canonical anchor/storage behavior;
- context serving behavior;
- promotion gate behavior.

It stays at the scenario/spec layer and is directly usable for downstream bounded verification work.