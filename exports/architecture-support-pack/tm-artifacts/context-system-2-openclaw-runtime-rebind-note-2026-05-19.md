# Context System 2 — OpenClaw runtime rebind note

Date: 2026-05-19
Status: corrective rebind
Parent task: #531
Task: CS2-C1

## 1. Correction

The previously landed CS2 runtime stub under:
- `agents/hermes-workspace/hermes-agent/agent/cs2_strategist_runtime.py`
- `agents/hermes-workspace/hermes-agent/run_agent.py`

was the **wrong implementation contour** for CS2 runtime work.

Reason:
- it targets the Hermes isolated-run runtime path;
- CS2 is supposed to bind into the **OpenClaw-native startup/bootstrap and prompt assembly seam**;
- Hermes may remain useful only as precedent for proof shape (`manifest -> resolve -> trace -> degraded/missing`), not as the runtime owner.

Therefore:
- treat the Hermes artifact as a **discarded runtime landing zone**;
- preserve only the abstract proof decisions listed below;
- do **not** continue CS2 runtime implementation inside `agents/hermes-workspace/...`.

## 2. Reusable abstract decisions preserved from the prior proof

These decisions remain valid and should transfer to OpenClaw:

1. **Manifest-driven assembly**
   - selected surface manifest declares the ambient candidate set.
2. **Normalized resolution states**
   - `loaded_direct`
   - `loaded_wrapped`
   - `loaded_generated`
   - `skipped_condition_unmet`
   - `skipped_budget_trim`
   - `missing_pack`
   - `error_invalid_source`
3. **Honest degraded startup**
   - required-missing packs must not be silently faked.
4. **Trace-first observability**
   - startup/context assembly must emit an inspectable resolution trace.
5. **Branch-local continuation only**
   - continuation capsules must stay local and current.

These are retained as CS2 logic, but **not** the Hermes file placement.

## 3. Actual OpenClaw-native seam identified

After inspecting the workspace and installed OpenClaw runtime, the strongest native seams are:

### Seam A — startup context prelude assembly
Owner file:
- `/home/openclaw/.npm-global/lib/node_modules/openclaw/dist/startup-context-DVdfqRzB.js`

Relevant function:
- `buildSessionStartupContextPrelude(params)`

Why it matters:
- this is a real OpenClaw startup-time context assembly function;
- it already decides what runtime-loaded startup context gets prepended;
- it is the cleanest native location for **surface-selected CS2 startup envelope material**.

Current role:
- loads bounded startup memory blocks;
- formats runtime-owned startup prelude text.

CS2 fit:
- attach `surface_id` selection,
- append compact CS2 assembly summary,
- expose loaded/skipped/missing pack trace in a startup-owned section.

### Seam B — bootstrap file resolution for a run
Owner file:
- `/home/openclaw/.npm-global/lib/node_modules/openclaw/dist/bootstrap-files-ZYTN7n8L.js`

Relevant functions:
- `resolveBootstrapFilesForRun(params)`
- `resolveBootstrapContextForRun(params)`
- `applyBootstrapHookOverrides(params)`

Why it matters:
- this is the real OpenClaw boundary where startup bootstrap files are filtered, loaded, and converted into context files;
- it already has a hookable override path;
- this is the strongest seam for mapping CS2 surface manifests into **actual startup inputs**.

CS2 fit:
- surface manifest selection can be resolved before/within bootstrap file assembly;
- pack resolution can return concrete context-file equivalents;
- startup context can stay explicit and inspectable.

### Seam C — prompt injection plugin hook
Owner type declaration:
- `/home/openclaw/.npm-global/lib/node_modules/openclaw/dist/plugin-sdk/src/plugins/hook-types.d.ts`

Relevant hook names:
- `before_prompt_build`
- `before_agent_start`
- `session_start`

Why it matters:
- OpenClaw already exposes first-class runtime hooks for prompt/startup mutation;
- this provides an OpenClaw-native extension seam without routing through Hermes runtime code.

CS2 fit:
- a CS2 plugin can compute surface + manifest + pack trace,
- then inject a bounded startup block or attach metadata before prompt build.

## 4. Best current OpenClaw implementation contour

The recommended order is:

1. **Surface selection input**
   - source from OpenClaw surface/profile artifacts already present in workspace:
     - `openclaw-frame/surfaces/main.surface.json`
     - `openclaw-frame/surfaces/strategist.surface.json`
     - related surface/profile files
2. **CS2 manifest + pack-map resolution layer**
   - source from workspace artifacts:
     - `task-manager/artifacts/context-system-2-first-surface-manifests-2026-05-19.md`
     - `task-manager/artifacts/context-system-2-pack-admission-schema-2026-05-19.md`
     - `task-manager/artifacts/context-system-2-current-control-pack-map-2026-05-19.md`
3. **Runtime attachment at OpenClaw seam**
   - preferred landing seam: `resolveBootstrapContextForRun(...)`
   - secondary/startup-display seam: `buildSessionStartupContextPrelude(...)`
4. **Trace exposure through startup-owned metadata text or hook-owned metadata**
   - do not hide missing packs.

## 5. Exact rebind mapping

### Wrong contour
- `agents/hermes-workspace/hermes-agent/agent/cs2_strategist_runtime.py`
- `agents/hermes-workspace/hermes-agent/run_agent.py`

### Correct contour
- OpenClaw runtime/bootstrap owner:
  - `/home/openclaw/.npm-global/lib/node_modules/openclaw/dist/bootstrap-files-ZYTN7n8L.js`
  - `/home/openclaw/.npm-global/lib/node_modules/openclaw/dist/startup-context-DVdfqRzB.js`
- OpenClaw hook surface:
  - `/home/openclaw/.npm-global/lib/node_modules/openclaw/dist/plugin-sdk/src/plugins/hook-types.d.ts`
- OpenClaw surface/profile inputs in workspace:
  - `openclaw-frame/surfaces/main.surface.json`
  - `openclaw-frame/surfaces/strategist.surface.json`
  - sibling surface files under `openclaw-frame/surfaces/`

## 6. Next bounded deliverable from the corrected footing

A safe direct code patch is **not** the strongest next move yet because the inspected OpenClaw runtime here is compiled under global `dist/`, and the correct extension shape should be pinned before editing runtime-owned compiled output.

So the next bounded deliverable should be:

## OpenClaw-native seam mapping spec

Create a tiny implementation-facing spec that defines:
- the CS2 resolver input object,
- the normalized resolution trace object,
- where `surface_id` comes from,
- how `resolveBootstrapContextForRun(...)` should call the resolver,
- how `buildSessionStartupContextPrelude(...)` should expose the trace,
- how `before_prompt_build` can be used as a non-invasive first integration path.

## 7. Immediate implementation recommendation

First implementation slice should be **plugin-first, not Hermes-first**:

1. create a workspace-local OpenClaw plugin/stub spec for `before_prompt_build`;
2. have it read one selected surface (`main` or `strategist`);
3. resolve only direct existing packs from the current pack map;
4. emit a compact `cs2_runtime_trace` block;
5. leave wrapped/generated packs and budget trimming for the next slice.

That gives an OpenClaw-native proof without patching Hermes and without prematurely editing compiled runtime core.
