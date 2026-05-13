# Structured Compression Contract v1

## 1. Scope

This contract defines the minimum structured payload that continuation-aware compression should preserve when a run or prompt window must be compacted.

It is intentionally narrow:
- it defines the shape of compression output needed for safe continuation;
- it does not replace task state, durable memory, or handoff truth;
- it does not require a specific plugin architecture by itself.

The payload is a continuity aid, not the source of truth.

---

## 2. Intent

A valid structured compression payload should preserve enough machine-usable and operator-usable state for a later continuation step to:
- identify the active bounded task;
- know the next safe executable step;
- preserve blockers, unresolved questions, and active truth;
- reload canonical artifacts, task anchors, and memory or handoff references.

---

## 3. Required fields

All fields in this section are mandatory.

| Field | Type | Rules |
|---|---|---|
| `task_id` | string or integer | Canonical active task id when one exists. |
| `goal` | string | One bounded objective active at compression time. |
| `status` | string | Must be one of `launching`, `executing`, `waiting`, `handoff`, `finishing`. |
| `next_action` | string | One immediately executable next step. |
| `blockers` | array of strings | Use `[]` when none. Each blocker should be concrete. |
| `facts_to_preserve` | array of strings | Active facts or decisions that would make continuation unsafe if lost. |
| `relevant_refs` | array | Canonical references needed to resume. Entries may be strings or structured reference objects. |
| `open_questions` | array of strings | Use `[]` when none. Preserve unresolved questions that can change the next step or verification. |
| `drop_safe_summary` | string | Short non-canonical summary residue that is useful but safe to drop after re-materialization from canonical anchors. |

---

## 4. Optional fields

Optional fields may be emitted when reliably known.

| Field | Type | Include when |
|---|---|---|
| `owner` | string | ownership or routing matters for resume |
| `task_status` | string | task state should be restated explicitly |
| `handoff_anchor` | string or object | a canonical handoff, session-capsule, or continuation id exists |
| `memory_refs` | array | durable memory anchors should be reloaded separately |
| `artifact_refs` | array | created or updated files are continuation-critical |
| `verification_state` | string | the result is partially verified, pending review, or awaiting readback |
| `risks` | array of strings | known failure modes or ambiguity should survive compression |
| `resume_hint` | string | a short operator or runner hint materially improves restart quality |
| `updated_at` | string | ISO-8601 timestamp is available |

Optional fields should be omitted rather than invented.

---

## 5. Structured reference shape

Reference-bearing fields may contain either:
- a canonical reference string; or
- a structured reference object.

Recommended object form:

```json
{
  "kind": "task|artifact|memory|handoff|url|file",
  "value": "task:427",
  "label": "optional human-readable label"
}
```

Minimum rules:
- `kind` describes the reference class;
- `value` contains the canonical resolvable pointer;
- `label`, when present, should not replace `value`.

---

## 6. Fill rules

### Rule A — Prefer canonical anchors

If a canonical anchor exists, record it directly.

Prefer exact refs such as:
- `task:427`
- `task-manager/artifacts/task-427-structured-compression-contract-v1-2026-05-13.md`
- explicit handoff or session anchor ids

Do not rely on vague prose such as “the file created earlier” when a concrete path or task ref exists.

### Rule B — Keep `goal` bounded

`goal` should describe the currently active bounded objective, not a broad program vision.

### Rule C — `next_action` must be executable now

`next_action` should be a single concrete next move that can be started without reinterpretation.

### Rule D — `blockers` are factual, not speculative

Use `[]` when unblocked.
If blocked, each blocker should describe the real dependency or missing condition.

### Rule E — `facts_to_preserve` is for active truth only

Include only information that would break safe continuation if lost.
Do not use it as a dump of general discussion residue.

### Rule F — `relevant_refs` is the canonical reload set

At minimum, `relevant_refs` should include the task anchor and any artifact or handoff anchors directly needed for continuation.

### Rule G — `drop_safe_summary` is explicitly non-canonical

This field may summarize transcript residue, but canonical refs, task state, and preserved facts remain authoritative.

### Rule H — Empty beats fabrication

Prefer:
- `[]` over guessed list content;
- omitted optional fields over speculative values;
- a smaller truthful payload over a fuller but unreliable one.

### Rule I — Preserve unresolved tension explicitly

If the run ends with ambiguity, verification debt, or a pending decision, record that explicitly in `open_questions`, `verification_state`, or `risks`.

---

## 7. Canonical reference policy

### 7.1 Authority order

When downstream logic reconstructs context, a sensible priority order is:
1. task state and canonical task id;
2. checked-in artifact paths referenced in `relevant_refs` or `artifact_refs`;
3. canonical handoff or session anchors;
4. canonical memory references;
5. `facts_to_preserve`;
6. `drop_safe_summary`.

`drop_safe_summary` should always remain lowest-authority.

### 7.2 Reference normalization

When possible, references should use stable, resolvable forms such as:
- `task:<id>`
- repo-relative file paths
- stable handoff or session ids
- memory ids, paths, or slugs already used by the surrounding system

### 7.3 Duplicate reference handling

If the same anchor appears in both string and object form, downstream normalization should deduplicate by canonical `value`.

### 7.4 No prose-only hidden anchors

A valid payload should not hide critical continuation anchors only inside prose fields. If a later step needs an anchor, it belongs in a reference-bearing field.

---

## 8. Validation expectations

A payload is minimally valid only if:
- all required fields exist;
- `status` is one of the allowed values;
- `blockers`, `facts_to_preserve`, `relevant_refs`, and `open_questions` are arrays;
- `next_action` is non-empty and concrete;
- `drop_safe_summary` is present even if short.

A payload is stronger when:
- references are canonical and resolvable;
- open questions and verification debt are explicit;
- artifact and handoff anchors are separated cleanly.

---

## 9. Design principle

Compression should preserve enough structured state to support safe continuation, but it should not become the hidden owner of truth.

Task state, artifacts, memory, and handoff anchors remain the authoritative layers. Structured compression exists to bridge context loss without collapsing those layers back into transcript-only continuity.
