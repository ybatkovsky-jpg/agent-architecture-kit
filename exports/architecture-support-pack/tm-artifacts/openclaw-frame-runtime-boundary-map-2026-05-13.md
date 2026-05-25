# OpenClaw Frame — runtime boundary map

Date: 2026-05-13
Status: execution-facing boundary artifact
Purpose: map where ownership appears to sit between workspace policy/design layers and runtime/integration layers, using current repo evidence and pass-3 findings

---

## 1. Why this artifact exists

After the pass-3 summary, the next useful step is not more abstract architecture prose.
It is an execution-facing boundary map:
- what the workspace clearly defines;
- what the runtime bridge appears to materialize/enforce;
- where the live symptoms show a seam or mismatch.

This artifact is intentionally practical.
It is meant to guide inspection and future bounded tasks.

---

## 2. Core model

Current best-fit layered model:

1. **Workspace policy/design layer**
   - retrieval policy
   - authority order
   - continuation rules
   - context-serving rules
   - structured compression / handoff contracts

2. **Runtime bridge / integration layer**
   - materialization of execution context objects
   - injection/enforcement of live run context
   - assembly of prompt-facing context envelope
   - approval/runtime guards

3. **Observed live behavior**
   - what actually wins in retrieval
   - what context appears to reach the model
   - where policy and live outputs diverge

---

## 3. Boundary map

| Concern | Workspace owner / evidence | Runtime owner / seam | Observed live symptom / risk | Current judgment |
|---|---|---|---|---|
| **Approval context injection** | Approval rules and gate logic clearly exist in workspace/domain artifacts, e.g. `task-222-approval-gate-before-autopublish-2026-04-28.md` | pass-3 findings indicate separate approval execution layer (`system-run-approval-context-*`) likely shapes runtime approval behavior | workspace policy may be correct while live approval behavior still differs due to execution-layer injection/enforcement | **cross-boundary** |
| **Memory retrieval policy** | `pkm-memory/retrieve_memory.py`, task 358/359/360/361/362/363 family, context-serving policy in task 396 | runtime bridge likely consumes retrieval output and shapes what becomes live context | policy can say one thing while live top items or served context show another | **workspace-defined, runtime-shaped** |
| **Continuation anchor selection** | task 396, task 410, task 422, continuation hardening artifacts, authority priority rules | runtime bridge materializes `TopicContext`, `TaskBrief`, `RunState-lite` per task 217 | bounded packs show continuation anchor logic can be green, but live mixed packs still show contamination | **mostly defined in workspace, realized through runtime seam** |
| **Transcript / compression rollover** | task 410 defines structured compression contract and anchor-preservation stance | actual compression and rollover behavior likely occurs in runtime/context-engine path | generic summary pressure can erase canonical anchors unless runtime bridge preserves them structurally | **runtime-heavy seam with workspace contract** |
| **Context-serving class rules** | task 396 explicitly defines always-on / on-demand / forbidden ambient injection | live serving envelope still depends on what runtime actually injects by default | forbidden-by-policy material can still effectively influence live behavior if runtime assembly is too broad | **workspace policy, runtime enforcement risk** |
| **Final prompt/context assembly** | policy inputs exist across task 396 and task 410; retrieval serve-pack is visible in workspace artifacts | final prompt-facing envelope appears to be assembled after retrieval, inside runtime integration seam | strongest current mismatch zone: declared request class / authority focus vs actual selected top layers | **primary seam to inspect** |

---

## 4. Strong workspace-side evidence

## 4.1 Retrieval and authority policy clearly exist in workspace

Confirmed in current artifacts/code:
- `pkm-memory/retrieve_memory.py`
- `task-manager/artifacts/task-361-memory-core-v1-authority-priority-ranking-handoff-2026-05-07.md`
- `task-manager/artifacts/task-396-openclaw-frame-context-serving-policy-v1-2026-05-12.md`
- `task-manager/artifacts/task-410-context-engine-memory-retrieval-handoff-integration-2026-05-12.md`

What these already define:
- request classification;
- authority-priority ordering;
- serve-pack shaping;
- continuation-vs-transcript policy;
- context-serving classes;
- structured compression / anchor-preservation rules.

So there is no serious doubt that the workspace owns a large part of the intended behavior contract.

## 4.2 Runtime bridge is explicitly present in architecture artifacts

Task `217` states directly that the standard bounded execution path includes:
- task-manager providing task identity/state;
- Kinetic routing the work;
- **runtime bridge materializing `TopicContext`, `TaskBrief`, and `RunState-lite`**.

Source:
- `task-manager/artifacts/task-217-openclaw-frame-current-architecture-2026-04-30.md`

This is the key explicit seam.
It means the workspace does not hand raw truth directly to the model without an integration layer.

---

## 5. Strong live-symptom evidence of the seam

## 5.1 Declared architecture recall policy still drifts in live/broader packs

Current live-ish evidence shows a very specific mismatch pattern.

In the broader continuation/mixed pack, request classification can say:
- `request_class = architecture_design_recall`
- `authority_priority_focus = memory_note > wiki_page > evidence_record > retrieval_document`

But the top selected layers still show:
- `canonical_handoff`
- `canonical_handoff`
- `canonical_handoff`

And selected paths can still be:
- `task-360-memory-core-v1-routing-policy-enforcement-handoff-2026-05-07.md`
- `task-362-memory-core-v1-citation-envelope-handoff-2026-05-07.md`
- `task-410-context-engine-memory-retrieval-handoff-integration-2026-05-12.md`

Interpretation:
- policy trace is being produced,
- but final winner behavior is still contaminated by continuation/handoff dominance in some mixed packs.

This is exactly the kind of signal that says:
- workspace policy exists,
- but live selection/assembly behavior still crosses an unresolved seam.

## 5.2 Cross-lane rerun artifact confirms mixed-pack contamination remains

From `task-422-x1-cross-lane-rerun-pack-2026-05-12.md`:
- explicit anchored continuation requests got materially better;
- bounded anchor precedence is green;
- compact explicit meta lane is green;
- **but** broader mixed continuation pack is still not all-pass;
- explicit meta asks can still drift to `canonical_handoff`;
- architecture/design recall boundary remains noisy.

Interpretation:
- the problem is not simply “policy missing.”
- the problem is closer to “policy exists, but cross-lane live behavior is not yet cleanly enforced.”

---

## 6. Operational reading by concern

### 6.1 Approval context injection

Best current reading:
- workspace can define approval rules and guarded paths;
- runtime still owns whether approval context is correctly materialized at execution time.

Implication:
- any approval anomaly should be inspected across both:
  - workspace gate definitions,
  - runtime injection/enforcement seam.

### 6.2 Memory serving bridge

Best current reading:
- retrieval and serve-pack policy are workspace-defined;
- what actually becomes active model context is likely mediated by runtime bridge logic.

Implication:
- debugging must distinguish:
  - retrieval ranking result,
  - served envelope,
  - final prompt-context assembly.

### 6.3 Continuation anchor injection

Best current reading:
- canonical continuation behavior is well-specified and increasingly well-verified in bounded packs;
- however, continuation objects can still over-dominate neighboring request classes in broader mixed packs.

Implication:
- the seam is not only “which anchors exist,” but also “where their dominance should stop.”

### 6.4 Compression / rollover

Best current reading:
- workspace now has a clear stance: compression must preserve anchors structurally, not only as prose summary;
- runtime path still likely determines whether that contract is actually respected during live compaction.

Implication:
- this is a likely future enforcement hotspot, not a closed lane.

### 6.5 Final context assembly

Best current reading:
- this is probably the highest-leverage unresolved seam.

Why:
- policy traces can look correct;
- bounded packs can be green in isolation;
- but mixed-pack final winners still drift.

That pattern strongly suggests the issue is near or inside final context assembly / cross-lane envelope composition.

---

## 7. Inspection priorities

If opening the next bounded verification slice, inspect in this order:

1. **Final context assembly path**
   - where selected retrieval items become prompt-facing context
   - where continuation anchors may be over-promoted beyond allowed request classes

2. **Runtime bridge shaping of retrieval output**
   - whether serve-pack fields are consumed faithfully
   - whether request class and authority focus are advisory only instead of enforced

3. **Approval runtime seam**
   - how execution-facing approval context is injected
   - whether runtime guard state can diverge from workspace policy objects

4. **Compression/rollover bridge**
   - whether structured anchors survive real runtime compaction

---

## 8. Recommended next artifact/task shape

The clean next bounded slice is:

**Runtime seam inspection pack** with one row per concern:
- input policy object;
- runtime bridge object/function/path;
- expected live effect;
- actual observed effect;
- mismatch classification.

Suggested first rows:
- architecture-design recall case drifting to `canonical_handoff`;
- explicit meta case green in mini-pack but drifting in mixed pack;
- approval-context injection path;
- context-assembly path after retrieval classification.

---

## 9. Bottom line

This boundary map sharpens the main architectural conclusion:

- **workspace owns much of the intended contract**;
- **runtime owns material parts of live context/approval assembly**;
- **the current failures are best understood as seam failures, not as a single-layer bug**.

So the next serious work should inspect and verify the seam itself, especially around final context assembly and continuation over-dominance in mixed request packs.
