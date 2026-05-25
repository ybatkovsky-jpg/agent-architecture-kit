# Context System 2 — OpenClaw seam mapping spec

Date: 2026-05-19
Status: bounded next deliverable
Parent task: #531
Task: CS2-C1

Purpose: define the exact OpenClaw-native landing seam for the first CS2 runtime proof after correcting the earlier Hermes-targeted contour.

---

## 1. Target seam choice

Primary runtime seam:
- `/home/openclaw/.npm-global/lib/node_modules/openclaw/dist/bootstrap-files-ZYTN7n8L.js`
- function: `resolveBootstrapContextForRun(params)`

Secondary display/metadata seam:
- `/home/openclaw/.npm-global/lib/node_modules/openclaw/dist/startup-context-DVdfqRzB.js`
- function: `buildSessionStartupContextPrelude(params)`

Non-invasive first integration option:
- OpenClaw plugin hook `before_prompt_build`
- declared in `/home/openclaw/.npm-global/lib/node_modules/openclaw/dist/plugin-sdk/src/plugins/hook-types.d.ts`

Decision:
- first proof should attach by **plugin/hook or bootstrap-adjacent layer**, not by further Hermes runtime edits.

---

## 2. First-slice scope

The first OpenClaw-native CS2 proof should do only this:

1. select one surface id (`main` or `strategist`);
2. load the corresponding CS2 manifest definition;
3. resolve only `exists_usable` packs from the pack map;
4. emit a normalized runtime trace;
5. expose the trace through prompt/startup metadata text.

Explicitly out of scope for this slice:
- wrapped pack materialization;
- generated continuation capsules;
- token-budget trimming;
- automatic stay-vs-spawn enforcement;
- multi-surface dynamic routing.

---

## 3. Resolver input contract

Minimum input object:

```json
{
  "surface_id": "strategist",
  "request_class": "business_strategy",
  "workspace_dir": "/home/openclaw/.openclaw/workspace",
  "mode": "startup",
  "allow_wrapped": false,
  "allow_generated": false
}
```

Field notes:
- `surface_id`: chosen surface contract to bind.
- `request_class`: optional first-pass selector for conditionals; may be absent in first proof.
- `workspace_dir`: needed to resolve concrete source refs.
- `mode`: startup-only for first slice.
- `allow_wrapped`: false in first slice.
- `allow_generated`: false in first slice.

---

## 4. Resolver output contract

```json
{
  "surface_id": "strategist",
  "assembly_status": "ok_with_missing_optional",
  "selected_manifest_ref": "task-manager/artifacts/context-system-2-first-surface-manifests-2026-05-19.md",
  "resolved_items": [
    {
      "pack_id": "strategist.current_control",
      "resolution_state": "loaded_direct",
      "materialization_mode": "existing_pack",
      "source_ref": "agents/business-strategist-seed/capsules/runtime/strategist-current-control-pack.md",
      "required": true,
      "trace_reason": "source_exists_verified"
    }
  ],
  "missing_items": [
    {
      "pack_id": "strategist.local_current_branch",
      "resolution_state": "missing_pack",
      "materialization_mode": "none",
      "required": false,
      "trace_reason": "referenced_but_not_materialized"
    }
  ]
}
```

Required top-level fields:
- `surface_id`
- `assembly_status`
- `resolved_items`
- `missing_items`

Allowed `assembly_status` values for first slice:
- `ok`
- `ok_with_missing_optional`
- `degraded_required_missing`
- `error`

---

## 5. Exact file/function responsibilities

### A. Surface selector
Input sources:
- `openclaw-frame/surfaces/main.surface.json`
- `openclaw-frame/surfaces/strategist.surface.json`

Responsibility:
- provide the OpenClaw-native surface identity used to choose the CS2 manifest.

### B. Manifest resolver
Artifact source:
- `task-manager/artifacts/context-system-2-first-surface-manifests-2026-05-19.md`

Responsibility:
- translate selected surface into candidate pack ids for startup.

### C. Pack map resolver
Artifact source:
- `task-manager/artifacts/context-system-2-current-control-pack-map-2026-05-19.md`

Responsibility:
- map candidate pack ids to one of:
  - `loaded_direct`
  - `missing_pack`

First slice rule:
- accept only entries already marked `exists_usable`.

### D. Bootstrap seam adapter
Target function:
- `resolveBootstrapContextForRun(params)`

Responsibility:
- append resolved direct-pack context blocks into the startup context file set,
  or prepare a compact synthetic CS2 block carried alongside existing bootstrap context.

### E. Startup trace renderer
Target function:
- `buildSessionStartupContextPrelude(params)`

Responsibility:
- render a short human/agent-readable trace block such as:
  - selected surface,
  - loaded packs,
  - missing optional packs,
  - degraded required status if any.

---

## 6. First practical integration shape

Preferred first integration shape:

### Option 1 — plugin-first proof
Use `before_prompt_build` hook to:
1. determine target surface;
2. run direct-pack-only CS2 resolver;
3. append a compact `CS2 Runtime Trace` block to prompt context.

Pros:
- OpenClaw-native;
- reversible;
- no need to patch Hermes;
- no need to directly edit runtime core first.

### Option 2 — bootstrap-adjacent runtime patch
Patch `resolveBootstrapContextForRun(params)` to call the resolver directly.

Pros:
- closer to long-term runtime ownership.

Cons:
- higher risk because current local OpenClaw runtime is installed compiled under global `dist/`.

Recommendation:
- do Option 1 first unless a local plugin loading seam proves blocked.

---

## 7. Minimal first-proof target set

Use `strategist` for the first OpenClaw-native proof because current verified direct refs already exist:
- `agents/business-strategist-seed/capsules/runtime/strategist-core-operating-contract.md`
- `agents/business-strategist-seed/capsules/bootstrap/strategist-current-contour.md`
- `agents/business-strategist-seed/capsules/runtime/strategist-current-control-pack.md`

Expected first-proof missing item:
- `strategist.local_current_branch`

Why strategist first:
- strongest already-verified `exists_usable` anchor set;
- smallest honest proof with real loaded + missing behavior.

---

## 8. Acceptance criteria for the next implementation step

- Given `surface_id = strategist`, startup assembly chooses strategist CS2 candidates.
- Given direct existing strategist packs, runtime trace marks them `loaded_direct`.
- Given `strategist.local_current_branch` is still absent, runtime trace marks it `missing_pack`.
- No Hermes runtime file is edited.
- The emitted output is visible at an OpenClaw-native startup/prompt seam.

---

## 9. Strongest next step after this spec

Author a tiny workspace-local OpenClaw plugin stub that targets `before_prompt_build` and emits only:
- `surface_id`
- `assembly_status`
- `resolved_items`
- `missing_items`

for the `strategist` first slice.
