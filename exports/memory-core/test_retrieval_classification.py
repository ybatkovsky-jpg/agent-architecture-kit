from retrieval_classification import classify_request
from retrieve_memory import (
    apply_typed_serving_precedence,
    build_answer_envelope,
    route_sources,
    source_domain_tags,
    typed_candidate_eligibility,
)


def test_resume_classification_preserved():
    result = classify_request("Resume Memory Core v1 after task-363 handoff")
    assert result["request_class"] == "resume_reopen_continuation"
    assert result["budget"] == "small"


def test_meta_classification_preserved():
    result = classify_request("Show Memory Core evaluation summary and hardening log for continuation retrieval")
    assert result["request_class"] == "meta_evaluation_recall"
    assert result["meta_subfamily"] == "hardening_slice"


def test_artifact_trace_classification_preserved():
    result = classify_request("which file cites the routing policy artifact path")
    assert result["request_class"] == "artifact_source_trace_request"


def test_route_sources_excludes_handoffs_for_meta_lane():
    classification = classify_request("Show evaluation summary and release recommendation for Memory Core Stage 5.")
    selected_sources = [
        {"key": "task_manager_handoffs", "root_path": "task-manager/handoffs"},
        {"key": "task_manager_artifacts", "root_path": "task-manager/artifacts"},
        {"key": "openclaw_shared_memory", "root_path": "memory"},
    ]

    routed, routing = route_sources(selected_sources, classification, query="Show evaluation summary and release recommendation for Memory Core Stage 5.")

    assert [source["key"] for source in routed] == ["task_manager_artifacts", "openclaw_shared_memory"]
    assert "task_manager_handoffs" in routing["lane_excluded_source_keys"]
    assert routing["selected_phase"] == "primary"



def test_route_sources_excludes_handoffs_for_architecture_lane():
    classification = classify_request("what architecture baseline did we define for memory runtime")
    selected_sources = [
        {"key": "task_manager_handoffs", "root_path": "task-manager/handoffs"},
        {"key": "task_manager_artifacts", "root_path": "task-manager/artifacts"},
        {"key": "openclaw_shared_memory", "root_path": "memory"},
    ]

    routed, routing = route_sources(selected_sources, classification, query="what architecture baseline did we define for memory runtime")

    assert [source["key"] for source in routed] == ["task_manager_artifacts", "openclaw_shared_memory"]
    assert "task_manager_handoffs" in routing["lane_excluded_source_keys"]
    assert routing["selected_phase"] == "primary"



def test_typed_candidate_rejects_scope_mismatch_for_current_task_lane():
    classification = classify_request("current status for task 442")
    item = {
        "document": {
            "workspace_path": "memory/task-411-runtime-note.md",
            "title": "Task 411 runtime note",
        },
        "chunk": {
            "section_path": "status/task-411",
            "chunk_ordinal": 1,
        },
        "excerpt": "Canonical note for task-411 only.",
        "provenance": {
            "source_locator": "memory/task-411-runtime-note.md",
            "chunk_locator": "memory/task-411-runtime-note.md::status/task-411#chunk-1",
        },
    }

    result = typed_candidate_eligibility(item, "memory_note", classification, query="current status for task 442")

    assert result["is_typed_candidate"] is True
    assert result["eligible"] is False
    assert "typed_scope_mismatch" in result["reasons"]


def test_typed_serving_promotes_eligible_memory_note_before_plain_evidence():
    classification = classify_request("current status for task 442")
    memory_note = {
        "score": 10.0,
        "match_reason": "token_overlap",
        "document": {
            "workspace_path": "memory/task-442-runtime-note.md",
            "title": "Task 442 runtime note",
        },
        "chunk": {
            "section_path": "status/task-442",
            "chunk_ordinal": 1,
        },
        "excerpt": "Canonical task-442 status note.",
        "provenance": {
            "source_locator": "memory/task-442-runtime-note.md",
            "chunk_locator": "memory/task-442-runtime-note.md::status/task-442#chunk-1",
        },
        "authority": {
            "layer": "memory_note",
            "priority_index": 3,
            "current_execution_shape_priority": 2,
            "continuation_shape_priority": 2,
        },
        "source": {"key": "openclaw_shared_memory"},
    }
    evidence = {
        "score": 50.0,
        "match_reason": "exact_title",
        "document": {
            "workspace_path": "task-manager/artifacts/task-442-runtime-audit.md",
            "title": "Task 442 runtime audit",
        },
        "chunk": {
            "section_path": "summary",
            "chunk_ordinal": 1,
        },
        "excerpt": "Artifact evidence for task-442.",
        "provenance": {
            "source_locator": "task-manager/artifacts/task-442-runtime-audit.md",
            "chunk_locator": "task-manager/artifacts/task-442-runtime-audit.md::summary#chunk-1",
        },
        "authority": {
            "layer": "evidence_record",
            "priority_index": 5,
            "current_execution_shape_priority": 5,
            "continuation_shape_priority": 5,
        },
        "source": {"key": "task_manager_artifacts"},
    }

    reordered, trace = apply_typed_serving_precedence([evidence, memory_note], classification, query="current status for task 442")

    assert reordered[0]["document"]["workspace_path"] == "memory/task-442-runtime-note.md"
    assert trace["typed_serving"]["eligible_typed_count"] == 1
    assert trace["typed_serving"]["ineligible_typed_count"] == 0


def test_resume_history_assisted_anchor_detected_for_explicit_task_handoff():
    classification = classify_request("Resume Memory Core v1 after task-363 handoff")
    items = [
        {
            "score": 120.0,
            "match_reason": "continuation_task_id_exact_match",
            "document": {
                "workspace_path": "task-manager/artifacts/task-363-memory-core-v1-conflict-open-question-synthesis-handoff-2026-05-07.md",
                "title": "Task 363 Memory Core handoff",
            },
            "chunk": {
                "section_path": "Next bounded step",
                "chunk_ordinal": 1,
            },
            "excerpt": "Resume from task-363 handoff with next bounded step.",
            "provenance": {
                "source_locator": "task-manager/artifacts/task-363-memory-core-v1-conflict-open-question-synthesis-handoff-2026-05-07.md",
                "chunk_locator": "task-manager/artifacts/task-363-memory-core-v1-conflict-open-question-synthesis-handoff-2026-05-07.md::Next bounded step#chunk-1",
                "document_locator": "Task 363 Memory Core handoff (task-manager/artifacts/task-363-memory-core-v1-conflict-open-question-synthesis-handoff-2026-05-07.md)",
            },
            "authority": {
                "layer": "canonical_handoff",
                "matched_from": ["canonical handoff"],
                "priority_index": 0,
            },
            "source": {"key": "task_manager_handoffs"},
        }
    ]
    serve_pack = {
        "history_assisted_continuation_anchor": "task-363 handoff",
        "typed_serving": {"applied": True, "eligible_typed_count": 0, "ineligible_typed_count": 0, "trace": []},
        "canonical_winner_lock": {"applied": True, "reason": "continuation_handoff_task_state_prebounded_lock"},
        "document_diversity": {"applied": False, "reason": "already_diverse"},
    }

    envelope = build_answer_envelope("Resume Memory Core v1 after task-363 handoff", items, classification, serve_pack)

    assert envelope["trace_summary"]["history_assisted_continuation_anchor"] == "task-363 handoff"
    assert envelope["trace_summary"]["top_authority_layers"] == ["canonical_handoff"]
    assert envelope["trace_summary"]["selected_source_keys"] == ["task_manager_handoffs"]


def test_answer_envelope_exposes_trace_summary_for_operator_debug():
    classification = classify_request("which file cites the routing policy artifact path")
    classification["selected_phase"] = "primary"
    items = [
        {
            "rank": 1,
            "score": 40.0,
            "excerpt": "Routing policy artifact located in task-manager/artifacts/task-462-memory-runtime-phased-rollout-and-verification-plan-2026-05-13.md",
            "document": {
                "workspace_path": "task-manager/artifacts/task-462-memory-runtime-phased-rollout-and-verification-plan-2026-05-13.md",
                "title": "Task 462 rollout plan",
            },
            "chunk": {
                "section_path": "5.2/Wave 1",
                "chunk_ordinal": 2,
            },
            "provenance": {
                "source_locator": "task-manager/artifacts/task-462-memory-runtime-phased-rollout-and-verification-plan-2026-05-13.md",
                "chunk_locator": "task-manager/artifacts/task-462-memory-runtime-phased-rollout-and-verification-plan-2026-05-13.md::5.2/Wave 1#chunk-2",
                "document_locator": "Task 462 rollout plan (task-manager/artifacts/task-462-memory-runtime-phased-rollout-and-verification-plan-2026-05-13.md)",
            },
            "authority": {
                "layer": "evidence_record",
                "matched_from": ["authority_priority_focus"],
                "priority_index": 0,
            },
            "source": {"key": "task_manager_artifacts"},
            "match_reason": "artifact_slug_exact",
        }
    ]
    serve_pack = {
        "typed_serving": {"applied": True, "eligible_typed_count": 0, "ineligible_typed_count": 0, "trace": []},
        "canonical_winner_lock": {"applied": False, "reason": "no_canonical_candidates_found"},
        "document_diversity": {"applied": False, "reason": "single_document_only"},
        "fallback_used": True,
        "fallback_reason": "psql unavailable",
    }

    envelope = build_answer_envelope("which file cites the routing policy artifact path", items, classification, serve_pack)

    assert envelope["trace"]["selected_item_paths"] == [
        "task-manager/artifacts/task-462-memory-runtime-phased-rollout-and-verification-plan-2026-05-13.md"
    ]
    assert envelope["trace_summary"]["request_class"] == "artifact_source_trace_request"
    assert envelope["trace_summary"]["authority_priority_focus"] == "evidence_record > retrieval_document"
    assert envelope["trace_summary"]["selected_phase"] == "primary"
    assert envelope["trace_summary"]["top_authority_layers"] == ["evidence_record"]
    assert envelope["trace_summary"]["selected_source_keys"] == ["task_manager_artifacts"]
    assert envelope["trace_summary"]["selected_source_refs"] == [
        "task-manager/artifacts/task-462-memory-runtime-phased-rollout-and-verification-plan-2026-05-13.md"
    ]
    assert envelope["trace_summary"]["fallback_used"] is True
    assert envelope["trace_summary"]["fallback_reason"] == "psql unavailable"


def test_infer_item_authority_keeps_artifact_trace_artifacts_as_evidence_records():
    from retrieve_memory import infer_item_authority

    classification = classify_request("which file cites the routing policy artifact path")
    item = {
        "document": {
            "workspace_path": "task-manager/artifacts/task-461-memory-runtime-observability-progress-delta-2026-05-14.md",
            "title": "task 461 memory runtime observability progress delta 2026 05 14",
        },
        "source": {"key": "task_manager_artifacts"},
    }
    source_tags = source_domain_tags({"key": "task_manager_artifacts", "root_path": "task-manager/artifacts"})

    authority = infer_item_authority(item, source_tags, classification, query="which file cites the routing policy artifact path")

    assert authority == "evidence_record"



def test_architecture_lane_demotes_artifact_handoff_below_architecture_doc():
    from retrieve_memory import infer_item_authority, apply_lane_candidate_hygiene

    query = "what architecture baseline did we define for memory runtime"
    classification = classify_request(query)
    items = [
        {
            "score": 10.0,
            "match_reason": "token_overlap",
            "document": {
                "workspace_path": "task-manager/artifacts/task-147-rollout-handoff-next-session-2026-04-29.md",
                "title": "Task 147 rollout handoff next session",
            },
            "chunk": {"section_path": "next step", "chunk_ordinal": 1},
            "excerpt": "Next session handoff for rollout.",
            "source": {"key": "task_manager_artifacts"},
        },
        {
            "score": 10.0,
            "match_reason": "token_overlap",
            "document": {
                "workspace_path": "task-manager/artifacts/task-456-openclaw-memory-runtime-architecture-and-serving-contract-2026-05-13.md",
                "title": "Task 456 architecture and serving contract",
            },
            "chunk": {"section_path": "summary", "chunk_ordinal": 1},
            "excerpt": "Architecture and serving policy baseline.",
            "source": {"key": "task_manager_artifacts"},
        },
    ]

    ranked = apply_lane_candidate_hygiene(items, query, classification)
    source_tags = source_domain_tags({"key": "task_manager_artifacts", "root_path": "task-manager/artifacts"})
    authorities = [
        infer_item_authority(item, source_tags, classification, query=query)
        for item in ranked
    ]

    assert ranked[0]["document"]["workspace_path"] == "task-manager/artifacts/task-456-openclaw-memory-runtime-architecture-and-serving-contract-2026-05-13.md"
    assert "architecture_design_evidence_boost" in ranked[0]["match_reason"]
    assert "architecture_operational_handoff_demoted" in ranked[1]["match_reason"]
    assert authorities == ["task_state", "canonical_handoff"]



def test_typed_serving_does_not_override_canonical_handoff_in_continuation_lane():
    classification = classify_request("Resume Memory Core v1 after task-363 handoff")
    canonical = {
        "score": 30.0,
        "match_reason": "continuation_task_id_exact_match",
        "document": {
            "workspace_path": "task-manager/artifacts/task-363-memory-core-v1-conflict-open-question-synthesis-handoff-2026-05-07.md",
            "title": "Task 363 handoff",
        },
        "chunk": {
            "section_path": "Next bounded step",
            "chunk_ordinal": 1,
        },
        "excerpt": "Canonical task-363 handoff.",
        "provenance": {
            "source_locator": "task-manager/artifacts/task-363-memory-core-v1-conflict-open-question-synthesis-handoff-2026-05-07.md",
            "chunk_locator": "task-manager/artifacts/task-363-memory-core-v1-conflict-open-question-synthesis-handoff-2026-05-07.md::Next bounded step#chunk-1",
        },
        "authority": {
            "layer": "canonical_handoff",
            "priority_index": 0,
            "current_execution_shape_priority": 9,
            "continuation_shape_priority": 0,
        },
        "source": {"key": "task_manager_handoffs"},
    }
    memory_note = {
        "score": 90.0,
        "match_reason": "continuation_task_id_exact_match",
        "document": {
            "workspace_path": "memory/2026-05-10-memory-core.md",
            "title": "2026 05 10 memory core",
        },
        "chunk": {
            "section_path": "4) Task 363 — conflict / open-question synthesis",
            "chunk_ordinal": 20,
        },
        "excerpt": "Canonical task-363 status note.",
        "provenance": {
            "source_locator": "memory/2026-05-10-memory-core.md",
            "chunk_locator": "memory/2026-05-10-memory-core.md::4) Task 363 — conflict / open-question synthesis#chunk-20",
        },
        "authority": {
            "layer": "memory_note",
            "priority_index": 5,
            "current_execution_shape_priority": 9,
            "continuation_shape_priority": 9,
        },
        "source": {"key": "openclaw_shared_memory"},
    }

    reordered, trace = apply_typed_serving_precedence([memory_note, canonical], classification, query="Resume Memory Core v1 after task-363 handoff")

    assert reordered[0]["document"]["workspace_path"] == "task-manager/artifacts/task-363-memory-core-v1-conflict-open-question-synthesis-handoff-2026-05-07.md"
    assert trace["typed_serving"]["eligible_typed_count"] == 1


def test_source_domain_tags_keep_memory_and_artifact_roles_distinct():
    memory_tags = source_domain_tags({"key": "openclaw_shared_memory", "root_path": "memory"})
    artifact_tags = source_domain_tags({"key": "task_manager_artifacts", "root_path": "task-manager/artifacts"})

    assert "memory_note" in memory_tags
    assert "evidence_record" in artifact_tags
