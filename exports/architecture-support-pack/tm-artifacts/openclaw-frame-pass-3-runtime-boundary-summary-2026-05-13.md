# OpenClaw Frame — Pass 3 runtime-boundary summary

Date: 2026-05-13
Status: bounded summary artifact
Scope: capture the corrected architectural picture after pass 3 direction-finding on memory / approval / runtime-bridge behavior

---

## 1. Executive conclusion

The earlier hypothesis was too narrow.

It is **not** accurate to treat live OpenClaw Frame behavior as something explained only by workspace memory code.

The stronger model is:

**live behavior = workspace artifacts + workspace memory/retrieval layer + installed OpenClaw runtime/plugin layer**

That conclusion matters specifically for two active problem classes:
- topic / approval behavior;
- memory-runtime bridge / context-assembly behavior.

Those classes cannot be honestly debugged or specified from the workspace repo alone.

---

## 2. What pass 3 clarified

### 2.1 Workspace memory code is real, but not the whole system

Confirmed workspace-side memory core exists in and around:
- `pkm-memory/retrieve_memory.py`
- task artifacts for memory-core rollout, serving policy, authority ranking, continuation hardening, and context serving

Representative artifacts:
- `task-manager/artifacts/task-361-memory-core-v1-authority-priority-ranking-handoff-2026-05-07.md`
- `task-manager/artifacts/task-396-openclaw-frame-context-serving-policy-v1-2026-05-12.md`
- `task-manager/artifacts/task-410-context-engine-memory-retrieval-handoff-integration-2026-05-12.md`
- `task-manager/artifacts/task-406-openclaw-frame-runtime-enforcement-task-pool-2026-05-12.md`

This layer clearly owns:
- retrieval policy;
- authority-aware ranking;
- citation envelope behavior;
- continuation/context-serving specs;
- structured architecture intent.

But it does **not** by itself explain all live runtime behavior.

### 2.2 Installed runtime layer is architecturally significant

Pass 3 direction-finding also surfaced strong evidence that live behavior depends on installed runtime/plugin layers, not just workspace code.

Specifically, the observed seams point to separate installed-runtime layers for:
- approval/system-run behavior:
  - `system-run-approval-context-*`
- memory runtime bridge behavior:
  - `memory-core-engine-runtime-*`

Even where the exact code path was not fully extracted in the noisy grep tails, the architectural implication is already strong enough:

- approvals are not just a local workspace concern;
- memory serving into runtime is not just a direct call from workspace retrieval code;
- context assembly likely crosses a runtime integration seam before becoming live prompt context.

---

## 3. Boundary of responsibility

## 3.1 What is reasonably attributable to workspace-level code

Workspace-level code/artifacts are the right place to reason about:
- memory object model;
- retrieval routing and ranking policy;
- authority ordering;
- citation/serve-pack shaping;
- continuation policy;
- context-serving rules;
- structured compression / handoff contracts.

This is the **policy and canonical design layer**.

## 3.2 What is reasonably attributable to installed runtime/plugin code

Installed runtime/plugin layers are the right place to reason about:
- how approval context is actually injected/enforced at execution time;
- how memory/retrieval outputs are bridged into live runtime context;
- how context assembly is wired into the execution stack;
- what hidden/default shaping occurs between policy artifacts and observed live behavior.

This is the **live enforcement / integration layer**.

## 3.3 Practical rule

If the question is:
- “what should the policy be?” → workspace artifacts are often enough.
- “why did the live runtime actually behave this way?” → workspace-only analysis is insufficient.

---

## 4. Why this changes the debugging stance

Before pass 3, it was still plausible to investigate approval or memory-bridge issues mostly inside the workspace contour.

After pass 3, that is no longer the honest default.

For the affected issues, the correct stance is:
1. identify the workspace policy/design object;
2. identify the installed runtime bridge/enforcement seam;
3. compare intended policy vs live runtime wiring;
4. locate the mismatch at the seam, not by over-blaming the memory repo.

This avoids a repeated failure mode:
- overfitting explanations to `pkm-memory` because it is visible in the workspace,
- while the decisive behavior actually happens in the installed runtime layer.

---

## 5. Concrete implications for current contours

### 5.1 Topic / approval issue

Current conclusion:
- not safely diagnosable as “just a workspace memory or task artifact problem”;
- must include inspection of the installed approval runtime seam.

Interpretation:
- approval behavior likely has its own execution-facing context assembly/enforcement layer;
- fixes that touch only workspace artifacts may improve policy clarity but still miss live behavior.

### 5.2 Memory-runtime bridge / context-assembly issue

Current conclusion:
- not safely diagnosable as “retrieve_memory.py alone decides what the model gets”;
- must include inspection of the installed memory runtime bridge.

Interpretation:
- retrieval output, serving policy, and continuation anchors may be transformed, filtered, wrapped, or selectively injected by a runtime layer before they become active context.

### 5.3 Architecture documentation stance

Future docs/specs should stop implying:
- “workspace memory code == whole memory system”

and instead use a layered description:
- workspace policy/design layer;
- runtime bridge/integration layer;
- live execution behavior as the composition of both.

---

## 6. What is already strong enough to treat as confirmed

The following statements are strong enough to use as working architecture assumptions:

1. **Workspace memory code is necessary but not sufficient** to explain live memory/continuation behavior.
2. **Installed runtime code materially participates** in approval and memory-context behavior.
3. **Live debugging must cross the workspace/runtime seam** for topic approval and context-assembly classes.
4. **Architecture artifacts should describe a layered system**, not a single-repo closed loop.

---

## 7. What remains unclosed

Still worth proving more directly in a later bounded slice:
- exact installed code paths for approval-context injection;
- exact installed code paths for memory-runtime bridge/context assembly;
- where the final prompt-facing envelope is assembled;
- which transformations are policy-preserving vs policy-distorting.

These are proof-strengthening tasks, not reasons to revert to the older narrower hypothesis.

---

## 8. Recommended next bounded artifact

The most useful next artifact is a **runtime-boundary map** with three columns:
- workspace owner;
- runtime owner;
- observed live symptom / risk.

Suggested rows:
- approval context injection;
- memory retrieval serving;
- continuation anchor injection;
- transcript/compression rollover;
- context assembly / final prompt shaping.

That would turn this pass-3 conclusion into an execution-facing inspection map.

---

## 9. Bottom line

Pass 3 corrected the architectural picture.

The right mental model now is:

**OpenClaw Frame live behavior is produced by a layered system, where workspace memory/retrieval artifacts define important policy and structure, but installed runtime/plugin layers materially shape approval and memory-to-runtime behavior.**

So from here on, analysis of approval or context-assembly issues should explicitly track the boundary between:
- **workspace-level design truth**, and
- **installed-runtime enforcement truth**.
