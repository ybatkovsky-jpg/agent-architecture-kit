# Context System 2 — OpenClaw plugin stub validation note

Date: 2026-05-19
Status: ready-for-manual-validation
Parent task: #531
Task: CS2-C1

## What was implemented

A workspace-local OpenClaw plugin stub was created at:
- `openclaw-plugins/cs2-strategist-stub/openclaw.plugin.json`
- `openclaw-plugins/cs2-strategist-stub/index.js`

Hook used:
- `before_prompt_build`

Behavior:
- targets strategist-identifiable runs (`agentId`, `sessionKey`, or prompt cues)
- normalizes selected `surface_id` to `strategist`
- resolves only first-slice strategist packs marked `exists_usable`
- emits only:
  - `surface_id`
  - `assembly_status`
  - `resolved_items`
  - `missing_items`
- does not patch runtime core
- does not materialize wrapped/generated packs

## Why no automated runtime test was added

A safe local unit-test seam is not exposed in the current workspace without introducing extra harness assumptions about plugin discovery and host boot wiring. Since the goal of this slice is the narrowest operational proof, validation is specified as a bounded manual runtime check.

## Manual validation steps

1. Ensure the plugin is discoverable/enabled in OpenClaw config.
   - Add a plugin entry pointing at or enabling `cs2-strategist-stub` according to local plugin discovery policy.
   - If explicit path-based discovery is used in your environment, point it at:
     - `/home/openclaw/.openclaw/workspace/openclaw-plugins/cs2-strategist-stub`

2. Enable prompt injection for the plugin if your policy gates it.
   - `before_prompt_build` must not be blocked by `hooks.allowPromptInjection=false`.

3. Run a strategist-bound interaction.
   - Best proof path: send a Telegram message through the `strateg` account binding, or run a local strategist session if available.

4. Inspect the built prompt or runtime trace logs.
   - Expected injected block shape:

```text
[CS2_RUNTIME_TRACE]
{
  "surface_id": "strategist",
  "assembly_status": "ok_with_missing_optional",
  "resolved_items": [
    {
      "pack_id": "strategist.core_operating_contract",
      "resolution_state": "loaded_direct",
      "materialization_mode": "existing_pack",
      "source_ref": "agents/business-strategist-seed/capsules/runtime/strategist-core-operating-contract.md",
      "required": true,
      "trace_reason": "source_exists_verified"
    },
    {
      "pack_id": "strategist.current_contour",
      "resolution_state": "loaded_direct",
      "materialization_mode": "existing_pack",
      "source_ref": "agents/business-strategist-seed/capsules/bootstrap/strategist-current-contour.md",
      "required": true,
      "trace_reason": "source_exists_verified"
    },
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
[/CS2_RUNTIME_TRACE]
```

## Expected first-proof result

- `surface_id = strategist`
- `assembly_status = ok_with_missing_optional`
- direct existing strategist packs show `loaded_direct`
- `strategist.local_current_branch` shows `missing_pack`
- no Hermes runtime file changes are involved

## Next strongest step

Promote this stub into a real runtime-owned resolver module shared by:
- `before_prompt_build` for non-invasive proofing
- later `resolveBootstrapContextForRun(...)` integration for startup-owned assembly

That next step should replace the local pack map literal with artifact-backed manifest parsing and then append actual resolved pack content through a bounded bootstrap adapter.
