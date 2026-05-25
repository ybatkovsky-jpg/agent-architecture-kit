# Context System 2 — first surface manifests

Date: 2026-05-19
Status: draft-for-execution
Parent task: #531
Task: CS2-B1

Purpose: define the first concrete CS2 manifests for `main`, `strategist`, `architect`, `learning`, and `task_scoped_execution` using the target design and the two CS2 schemas.

---

## 1. Manifest set overview

These are the first runtime-facing surface contracts for CS2:
- `main`
- `strategist`
- `architect`
- `learning`
- `task_scoped_execution`

Each manifest below is written in implementation-facing JSON-like shape, but remains an artifact until runtime binding lands.

---

## 2. `main` manifest

```json
{
  "surface_id": "main",
  "version": "cs2-v1",
  "status": "draft",
  "purpose": "Primary user dialogue, orchestration, routing, concise summaries, and decisions requiring Yuri.",
  "owner_runtime": "openclaw.runtime.main",
  "startup_budget": {
    "target_tokens": 2500,
    "hard_cap_tokens": 4000,
    "budget_policy": "trim_to_fit"
  },
  "live_budget_guardrails": {
    "preferred_context_window_tokens": 10000,
    "warning_threshold_tokens": 14000,
    "spawn_bias_threshold_tokens": 16000,
    "history_trim_mode": "aggressive"
  },
  "always_on_allowlist": [
    {"kind": "core_item", "id": "identity_tone_compact", "max_tokens": 250, "required": true, "admission_reason": "surface_always_on"},
    {"kind": "core_item", "id": "user_address_prefs_compact", "max_tokens": 180, "required": true, "admission_reason": "surface_always_on"},
    {"kind": "core_item", "id": "operating_rules_compact", "max_tokens": 500, "required": true, "admission_reason": "surface_always_on"},
    {"kind": "core_item", "id": "thin_main_rule_compact", "max_tokens": 180, "required": true, "admission_reason": "surface_always_on"},
    {"kind": "continuation_capsule", "id": "main.local_current_branch", "max_tokens": 900, "required": false, "admission_reason": "current_branch_required"}
  ],
  "conditional_allowlist": [
    {"kind": "pack", "id": "main.local_decision_context", "when": {"request_classes": ["factual_lookup", "policy_decision_lookup"], "branch_state": "active"}, "max_tokens": 800, "admission_reason": "request_class_match", "fallback_behavior": "retrieve_on_demand"}
  ],
  "on_demand_only": [
    {"kind": "class", "id_or_class": "daily_memory", "reason": "not ambient in main"},
    {"kind": "class", "id_or_class": "task_artifacts_longform", "reason": "search/retrieve only"},
    {"kind": "class", "id_or_class": "architecture_history", "reason": "search/retrieve only"},
    {"kind": "class", "id_or_class": "business_history", "reason": "search/retrieve only"}
  ],
  "ambient_forbidden": [
    {"kind": "class", "id_or_class": "broad_project_context", "reason": "main must stay thin", "suppression_strength": "hard_forbid"},
    {"kind": "class", "id_or_class": "topic_history", "reason": "history is not startup", "suppression_strength": "hard_forbid"},
    {"kind": "class", "id_or_class": "cross_surface_tail", "reason": "avoid shared residue", "suppression_strength": "hard_forbid"},
    {"kind": "class", "id_or_class": "transcript_tail_as_memory", "reason": "tail is not memory", "suppression_strength": "hard_forbid"}
  ],
  "continuation_policy": {
    "ambient_scope": "current_branch_only",
    "max_continuation_tokens": 900,
    "allow_closed_branch_tail": false,
    "allow_cross_topic_tail": false,
    "allow_cross_surface_tail": false,
    "continuation_capsule_required": true
  },
  "routing_policy": {
    "default_action": "stay",
    "independent_work_bias": "high",
    "multi_step_bias": "high",
    "large_read_bias": "high",
    "implementation_bias": "high",
    "validation_bias": "high",
    "spawn_target_surface": "task_scoped_execution"
  },
  "output_contract": {
    "shape": "concise_summary",
    "max_default_paragraphs": 4,
    "artifact_expected": false,
    "requires_user_decision_only_when_needed": true,
    "return_to_main_style": "short_result"
  }
}
```

---

## 3. `strategist` manifest

```json
{
  "surface_id": "strategist",
  "version": "cs2-v1",
  "status": "draft",
  "purpose": "Business strategy, offer/content/publish logic, approvals, and commercial framing.",
  "owner_runtime": "openclaw.runtime.topic",
  "startup_budget": {
    "target_tokens": 4500,
    "hard_cap_tokens": 7000,
    "budget_policy": "trim_to_fit"
  },
  "live_budget_guardrails": {
    "preferred_context_window_tokens": 12000,
    "warning_threshold_tokens": 16000,
    "spawn_bias_threshold_tokens": 18000,
    "history_trim_mode": "aggressive"
  },
  "always_on_allowlist": [
    {"kind": "core_item", "id": "identity_tone_compact", "max_tokens": 250, "required": true, "admission_reason": "surface_always_on"},
    {"kind": "core_item", "id": "business_communication_prefs_compact", "max_tokens": 220, "required": true, "admission_reason": "surface_always_on"},
    {"kind": "pack", "id": "strategist.core_operating_contract", "max_tokens": 500, "required": true, "admission_reason": "surface_always_on"},
    {"kind": "pack", "id": "strategist.current_contour", "max_tokens": 450, "required": true, "admission_reason": "surface_always_on"},
    {"kind": "pack", "id": "strategist.current_control", "max_tokens": 900, "required": true, "admission_reason": "surface_always_on"},
    {"kind": "continuation_capsule", "id": "strategist.local_current_branch", "max_tokens": 1100, "required": false, "admission_reason": "current_branch_required"}
  ],
  "conditional_allowlist": [
    {"kind": "pack", "id": "strategist.approved_content_plan_summary", "when": {"request_classes": ["content_planning", "publish_logic"]}, "max_tokens": 900, "admission_reason": "request_class_match", "fallback_behavior": "retrieve_on_demand"},
    {"kind": "pack", "id": "strategist.offer_constraints_summary", "when": {"request_classes": ["offer_design"]}, "max_tokens": 800, "admission_reason": "request_class_match", "fallback_behavior": "retrieve_on_demand"},
    {"kind": "pack", "id": "strategist.business_bottleneck_summary", "when": {"request_classes": ["business_strategy"]}, "max_tokens": 800, "admission_reason": "request_class_match", "fallback_behavior": "retrieve_on_demand"}
  ],
  "on_demand_only": [
    {"kind": "class", "id_or_class": "historical_strategy_artifacts", "reason": "history is summary-first"},
    {"kind": "class", "id_or_class": "old_content_plans", "reason": "not ambient"},
    {"kind": "class", "id_or_class": "market_research_archives", "reason": "retrieve on need"},
    {"kind": "class", "id_or_class": "experiment_logs", "reason": "evidence-only path"}
  ],
  "ambient_forbidden": [
    {"kind": "class", "id_or_class": "full_strategy_topic_history", "reason": "topic is not memory reservoir", "suppression_strength": "hard_forbid"},
    {"kind": "class", "id_or_class": "mixed_global_memory", "reason": "business-only contour", "suppression_strength": "hard_forbid"},
    {"kind": "class", "id_or_class": "non_business_role_packs", "reason": "surface purity", "suppression_strength": "hard_forbid"},
    {"kind": "class", "id_or_class": "raw_transcript_tails", "reason": "summary-first continuity", "suppression_strength": "prefer_suppress"}
  ],
  "continuation_policy": {
    "ambient_scope": "current_branch_only",
    "max_continuation_tokens": 1100,
    "allow_closed_branch_tail": false,
    "allow_cross_topic_tail": false,
    "allow_cross_surface_tail": false,
    "continuation_capsule_required": true
  },
  "routing_policy": {
    "default_action": "stay",
    "independent_work_bias": "medium",
    "multi_step_bias": "high",
    "large_read_bias": "high",
    "implementation_bias": "medium",
    "validation_bias": "high",
    "spawn_target_surface": "task_scoped_execution"
  },
  "output_contract": {
    "shape": "approval_ready",
    "max_default_paragraphs": 6,
    "artifact_expected": true,
    "requires_user_decision_only_when_needed": true,
    "return_to_main_style": "approval_request"
  }
}
```

---

## 4. `architect` manifest

```json
{
  "surface_id": "architect",
  "version": "cs2-v1",
  "status": "draft",
  "purpose": "Architecture/design reasoning, system shape decisions, implementation mapping, and technical contour analysis.",
  "owner_runtime": "openclaw.runtime.topic",
  "startup_budget": {
    "target_tokens": 4200,
    "hard_cap_tokens": 6500,
    "budget_policy": "trim_to_fit"
  },
  "live_budget_guardrails": {
    "preferred_context_window_tokens": 12000,
    "warning_threshold_tokens": 16000,
    "spawn_bias_threshold_tokens": 18000,
    "history_trim_mode": "aggressive"
  },
  "always_on_allowlist": [
    {"kind": "core_item", "id": "identity_tone_compact", "max_tokens": 250, "required": true, "admission_reason": "surface_always_on"},
    {"kind": "pack", "id": "architect.core_operating_contract", "max_tokens": 500, "required": true, "admission_reason": "surface_always_on"},
    {"kind": "pack", "id": "architect.current_state_summary", "max_tokens": 1000, "required": true, "admission_reason": "surface_always_on"},
    {"kind": "continuation_capsule", "id": "architect.local_current_branch", "max_tokens": 1100, "required": false, "admission_reason": "current_branch_required"}
  ],
  "conditional_allowlist": [
    {"kind": "pack", "id": "architect.implementation_mapping", "when": {"request_classes": ["architecture_design_recall", "current_task_execution"]}, "max_tokens": 900, "admission_reason": "request_class_match", "fallback_behavior": "retrieve_on_demand"},
    {"kind": "pack", "id": "architect.current_decision_register_summary", "when": {"request_classes": ["policy_decision_lookup"]}, "max_tokens": 700, "admission_reason": "request_class_match", "fallback_behavior": "retrieve_on_demand"}
  ],
  "on_demand_only": [
    {"kind": "class", "id_or_class": "long_design_history", "reason": "retrieve only when needed"},
    {"kind": "class", "id_or_class": "old_evaluation_artifacts", "reason": "evidence path only"},
    {"kind": "class", "id_or_class": "full_regression_packs", "reason": "not startup material"}
  ],
  "ambient_forbidden": [
    {"kind": "class", "id_or_class": "business_history", "reason": "wrong surface", "suppression_strength": "hard_forbid"},
    {"kind": "class", "id_or_class": "topic_tail_memory", "reason": "tail is not architecture state", "suppression_strength": "hard_forbid"},
    {"kind": "class", "id_or_class": "cross_surface_residue", "reason": "surface purity", "suppression_strength": "hard_forbid"}
  ],
  "continuation_policy": {
    "ambient_scope": "current_branch_only",
    "max_continuation_tokens": 1100,
    "allow_closed_branch_tail": false,
    "allow_cross_topic_tail": false,
    "allow_cross_surface_tail": false,
    "continuation_capsule_required": true
  },
  "routing_policy": {
    "default_action": "stay",
    "independent_work_bias": "medium",
    "multi_step_bias": "high",
    "large_read_bias": "high",
    "implementation_bias": "high",
    "validation_bias": "high",
    "spawn_target_surface": "task_scoped_execution"
  },
  "output_contract": {
    "shape": "artifact_handoff",
    "max_default_paragraphs": 6,
    "artifact_expected": true,
    "requires_user_decision_only_when_needed": true,
    "return_to_main_style": "short_result"
  }
}
```

---

## 5. `learning` manifest

```json
{
  "surface_id": "learning",
  "version": "cs2-v1",
  "status": "draft",
  "purpose": "Explanation, roadmap guidance, concept simplification, and teaching-oriented support.",
  "owner_runtime": "openclaw.runtime.topic",
  "startup_budget": {
    "target_tokens": 3500,
    "hard_cap_tokens": 5500,
    "budget_policy": "trim_to_fit"
  },
  "live_budget_guardrails": {
    "preferred_context_window_tokens": 10000,
    "warning_threshold_tokens": 14000,
    "spawn_bias_threshold_tokens": 16000,
    "history_trim_mode": "balanced"
  },
  "always_on_allowlist": [
    {"kind": "core_item", "id": "identity_tone_compact", "max_tokens": 250, "required": true, "admission_reason": "surface_always_on"},
    {"kind": "pack", "id": "learning.mode_rules", "max_tokens": 500, "required": true, "admission_reason": "surface_always_on"},
    {"kind": "pack", "id": "learning.current_roadmap_summary", "max_tokens": 900, "required": false, "admission_reason": "surface_always_on"},
    {"kind": "continuation_capsule", "id": "learning.local_current_branch", "max_tokens": 900, "required": false, "admission_reason": "current_branch_required"}
  ],
  "conditional_allowlist": [
    {"kind": "pack", "id": "learning.topic_specific_summary", "when": {"request_classes": ["factual_lookup", "architecture_design_recall"]}, "max_tokens": 800, "admission_reason": "request_class_match", "fallback_behavior": "retrieve_on_demand"}
  ],
  "on_demand_only": [
    {"kind": "class", "id_or_class": "deep_business_archive", "reason": "not ambient in learning"},
    {"kind": "class", "id_or_class": "deep_architecture_archive", "reason": "load only if explicitly needed"},
    {"kind": "class", "id_or_class": "long_task_artifacts", "reason": "retrieve for exact examples only"}
  ],
  "ambient_forbidden": [
    {"kind": "class", "id_or_class": "cross_role_history_mix", "reason": "keep teaching contour clean", "suppression_strength": "hard_forbid"},
    {"kind": "class", "id_or_class": "raw_transcript_tails", "reason": "prefer curated explanation context", "suppression_strength": "prefer_suppress"}
  ],
  "continuation_policy": {
    "ambient_scope": "current_branch_only",
    "max_continuation_tokens": 900,
    "allow_closed_branch_tail": false,
    "allow_cross_topic_tail": false,
    "allow_cross_surface_tail": false,
    "continuation_capsule_required": true
  },
  "routing_policy": {
    "default_action": "stay",
    "independent_work_bias": "medium",
    "multi_step_bias": "medium",
    "large_read_bias": "medium",
    "implementation_bias": "low",
    "validation_bias": "medium",
    "spawn_target_surface": "task_scoped_execution"
  },
  "output_contract": {
    "shape": "explanation",
    "max_default_paragraphs": 6,
    "artifact_expected": false,
    "requires_user_decision_only_when_needed": true,
    "return_to_main_style": "short_result"
  }
}
```

---

## 6. `task_scoped_execution` manifest

```json
{
  "surface_id": "task_scoped_execution",
  "version": "cs2-v1",
  "status": "draft",
  "purpose": "Fresh bounded execution for independent work, reading, synthesis, implementation, and validation outside long chat tail.",
  "owner_runtime": "openclaw.runtime.task_scoped",
  "startup_budget": {
    "target_tokens": 3000,
    "hard_cap_tokens": 5000,
    "budget_policy": "trim_to_fit"
  },
  "live_budget_guardrails": {
    "preferred_context_window_tokens": 9000,
    "warning_threshold_tokens": 12000,
    "spawn_bias_threshold_tokens": 14000,
    "history_trim_mode": "aggressive"
  },
  "always_on_allowlist": [
    {"kind": "core_item", "id": "identity_tone_compact", "max_tokens": 250, "required": true, "admission_reason": "surface_always_on"},
    {"kind": "core_item", "id": "safety_and_tool_rules_compact", "max_tokens": 600, "required": true, "admission_reason": "surface_always_on"},
    {"kind": "task_bootstrap", "id": "task.bootstrap_packet", "max_tokens": 1400, "required": true, "admission_reason": "task_linked_required"},
    {"kind": "pack", "id": "task_scoped.execution_contract", "max_tokens": 400, "required": true, "admission_reason": "surface_always_on"}
  ],
  "conditional_allowlist": [
    {"kind": "pack", "id": "task_scoped.linked_artifact_summary", "when": {"task_presence": true, "request_classes": ["current_task_execution", "resume_reopen_continuation"]}, "max_tokens": 900, "admission_reason": "task_linked_required", "fallback_behavior": "skip"},
    {"kind": "pack", "id": "task_scoped.narrow_recent_excerpt", "when": {"branch_state": "active", "freshness_required": true}, "max_tokens": 500, "admission_reason": "conditional_load_match", "fallback_behavior": "skip"}
  ],
  "on_demand_only": [
    {"kind": "class", "id_or_class": "old_main_transcript", "reason": "not startup material"},
    {"kind": "class", "id_or_class": "unrelated_role_packs", "reason": "load only by explicit need"},
    {"kind": "class", "id_or_class": "deep_archive", "reason": "retrieve exact evidence only"}
  ],
  "ambient_forbidden": [
    {"kind": "class", "id_or_class": "broad_chat_tail", "reason": "fresh run must stay fresh", "suppression_strength": "hard_forbid"},
    {"kind": "class", "id_or_class": "cross_task_residue", "reason": "task purity", "suppression_strength": "hard_forbid"},
    {"kind": "class", "id_or_class": "generic_workspace_context_dump", "reason": "use task bootstrap instead", "suppression_strength": "hard_forbid"}
  ],
  "continuation_policy": {
    "ambient_scope": "current_task_only",
    "max_continuation_tokens": 700,
    "allow_closed_branch_tail": false,
    "allow_cross_topic_tail": false,
    "allow_cross_surface_tail": false,
    "continuation_capsule_required": false
  },
  "routing_policy": {
    "default_action": "spawn_fresh",
    "independent_work_bias": "high",
    "multi_step_bias": "high",
    "large_read_bias": "high",
    "implementation_bias": "high",
    "validation_bias": "high",
    "spawn_target_surface": null
  },
  "output_contract": {
    "shape": "task_progress",
    "max_default_paragraphs": 4,
    "artifact_expected": true,
    "requires_user_decision_only_when_needed": true,
    "return_to_main_style": "short_result"
  }
}
```

---

## 7. Validation checklist

- [ ] manifests exist for all five first surfaces
- [ ] each manifest includes budgets, allowlists, forbidden classes, continuation policy, routing policy, and output contract
- [ ] manifests are concrete enough for runtime binding
- [ ] `main` is the thinnest and most aggressively suppressed
- [ ] `task_scoped_execution` is explicitly fresh-run biased

---

## 8. Recommended next step

Use these first manifests as the direct input for:
1. CS2-B2 compact current-control pack mapping,
2. CS2-C1 runtime assembly binding plan,
3. CS2-C2 stay-vs-spawn enforcement.
