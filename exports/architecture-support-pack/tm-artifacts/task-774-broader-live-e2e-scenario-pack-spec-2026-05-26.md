# Task #774 — Broader live E2E scenario pack: replayable production-like proof across multiple task classes

Date: 2026-05-26
Task: #774
Parent: #768
Status: specification draft

## 1. Purpose

The current contour has meaningful bounded proof, but confidence still depends too much on narrow slices.
What is missing is a broader **replayable live E2E scenario pack** that demonstrates production-like behavior across multiple task classes.

This task defines that scenario-pack shape.

---

## 2. Core design rule

**A scenario pack is not a demo script. It is replayable proof against explicit gates.**

Each scenario must specify:
- starting conditions,
- runtime/task/memory assumptions,
- expected operator-visible behavior,
- expected internal state behavior,
- pass/fail gates,
- evidence artifacts produced by replay.

---

## 3. Required scenario classes

The minimum broader pack should cover:
1. `normal_bounded_execution`
2. `long_running_progress_surfacing`
3. `delegated_interruption_resume`
4. `degraded_delivery_or_recovery`
5. `memory_critical_recall`
6. `false_closure_prevention`

---

## 4. Canonical harness shape

Each scenario should use one common harness envelope.

### Scenario envelope fields
- `scenario_id`
- `scenario_class`
- `initial_task_shape`
- `initial_runtime_shape`
- `initial_memory_shape`
- `actions`
- `expected_internal_transitions`
- `expected_operator_surfaces`
- `expected_terminal_outcome`
- `verification_steps`
- `evidence_artifacts`

---

## 5. Pass/fail gate model

Every scenario should define at least four gate families:
- execution gate
- honesty gate
- surfacing gate
- replay gate

---

## 6. Recommended first replayable scenario

The best first replayable production-like scenario is:

**delegated interruption/resume with false-closure pressure**

Why this first:
- it exercises delegation, lifecycle recovery, operator surfacing, and closure honesty together;
- it is more production-like than a trivial bounded success case;
- it touches high-risk trust seams without requiring every future lane to exist first.

### First-scenario shape
1. create a task that delegates a bounded but long-ish run;
2. persist delegated run-state/handle;
3. interrupt local continuity or simulate reload boundary;
4. recover directly or in degraded mode;
5. continue until a meaningful outcome exists;
6. verify no false closure was allowed before terminal proof;
7. verify operator/user surfacing occurred only at significant lifecycle boundaries.

---

## 7. Relationship to current contours

This pack should reuse, not replace:
- bounded task-manager closure tests,
- autonomy gating tests,
- delegated Track A/B lifecycle slices,
- memory-critical recall verifiers.

It sits above them as replayable integrated proof.

---

## 8. Evidence expectations

A real scenario replay should produce artifacts such as:
- scenario manifest,
- transition log,
- verification transcript,
- generated operator-summary snapshot,
- pass/fail verdict with explicit reasons.

---

## 9. Minimum implementation-first seam

**Define a reusable scenario-manifest + verifier harness that can drive one integrated delegated interruption/resume scenario end-to-end.**

That seam should:
1. standardize scenario inputs and expected gates;
2. produce a replay artifact bundle;
3. exercise both runtime truth and operator-visible truth;
4. stay narrow enough to implement before a full scenario matrix exists.

---

## 10. Acceptance shape

This task counts as complete when:
- scenario classes are defined;
- proof harness shape exists;
- the first replayable scenario is identified.

---

## 11. Concise verdict

The broader E2E pack should be a replayable proof framework, not a narrative demo. The best first integrated scenario is delegated interruption/resume under false-closure pressure, implemented through a standard scenario manifest and verifier harness.
