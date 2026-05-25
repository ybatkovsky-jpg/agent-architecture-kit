#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from ingest_sources import ROOT, build_document, load_env_file, load_registry
from retrieval_classification import (
    REQUEST_CLASS_SPECS,
    classify_request,
    detect_meta_evaluation_subfamily,
    is_explicit_meta_query as base_is_explicit_meta_query,
    is_short_meta_evaluation_query,
    normalize_text,
    tokenize,
)

CONTRACT_VERSION = "2026-04-26.phase1"


def clamp_items(value: int) -> int:
    return max(4, min(8, value))


BUDGET_ITEM_LIMITS: dict[str, int] = {
    "tiny": 4,
    "small": 5,
    "medium": 6,
}

AUTHORITY_ALIASES: dict[str, str] = {
    "task state": "task_state",
    "fresh task state": "task_state",
    "task-manager state": "task_state",
    "canonical handoff": "canonical_handoff",
    "handoff": "canonical_handoff",
    "memory_note": "memory_note",
    "task-scoped memory notes": "memory_note",
    "verified preference notes": "memory_note",
    "wiki_page": "wiki_page",
    "evidence_record": "evidence_record",
    "retrieval_document": "retrieval_document",
    "session_capsule": "session_capsule",
}

COMPOSITE_AUTHORITY_PARTS: dict[str, list[str]] = {
    "task state/handoff": ["task_state", "canonical_handoff"],
    "handoff/task state": ["canonical_handoff", "task_state"],
    "wiki/evidence": ["wiki_page", "evidence_record"],
    "evidence/wiki": ["evidence_record", "wiki_page"],
}

TYPED_AUTHORITY_LAYERS = {"memory_note", "session_capsule"}

LANE_ALLOWED_TYPED_AUTHORITIES: dict[str, set[str]] = {
    "resume_reopen_continuation": {"memory_note", "session_capsule"},
    "current_task_execution": {"memory_note"},
    "architecture_design_recall": {"memory_note"},
    "policy_decision_lookup": {"memory_note"},
    "preference_operating_style_recall": {"memory_note"},
}


def budget_item_limit(budget: str, requested_max_items: int) -> int:
    return min(clamp_items(requested_max_items), BUDGET_ITEM_LIMITS.get(budget, 6))


def candidate_fetch_limit(classification: dict[str, Any], max_items: int) -> int:
    bounded = clamp_items(max_items)
    request_class = str(classification.get("request_class", ""))
    if request_class == "resume_reopen_continuation":
        return max(12, min(24, bounded * 4))
    if request_class == "current_task_execution":
        return max(14, min(28, bounded * 4))
    if request_class == "artifact_source_trace_request":
        return max(18, min(36, bounded * 5))
    if request_class == "meta_evaluation_recall":
        return max(18, min(32, bounded * 5))
    return bounded


def source_domain_tags(source: dict[str, Any]) -> set[str]:
    key = str(source.get("key", "")).strip()
    root_path = str(source.get("root_path", "")).strip()
    tags: set[str] = {"retrieval_document"}

    if key == "task_manager_handoffs":
        tags.update({"canonical handoff", "fresh task state", "task-manager state", "evidence_record"})
    elif key == "task_manager_artifacts":
        tags.update({"evidence_record", "task-manager state", "wiki_page"})
    elif key == "openclaw_shared_memory":
        tags.update({"memory_note", "task-scoped memory notes", "verified preference notes", "wiki_page"})

    root_norm = root_path.lower()
    if "handoff" in root_norm:
        tags.add("canonical handoff")
    if "artifact" in root_norm:
        tags.add("evidence_record")
    if root_norm.startswith("memory"):
        tags.update({"memory_note", "wiki_page"})
    return tags


def classify_source_phase(source: dict[str, Any], classification: dict[str, Any]) -> str:
    primary = set(classification.get("primary_domains", []))
    fallback = set(classification.get("fallback_domains", []))
    tags = source_domain_tags(source)
    if tags & primary:
        return "primary"
    if tags & fallback:
        return "fallback"
    return "forbidden"


def route_sources(selected_sources: list[dict[str, Any]], classification: dict[str, Any], query: str = "") -> tuple[list[dict[str, Any]], dict[str, Any]]:
    primary_sources: list[dict[str, Any]] = []
    fallback_sources: list[dict[str, Any]] = []
    excluded_sources: list[dict[str, Any]] = []

    request_class = str(classification.get("request_class", ""))
    explicit_meta_eval = request_class == "meta_evaluation_recall"
    architecture_recall = request_class == "architecture_design_recall"
    source_excluded_by_lane: list[str] = []

    for source in selected_sources:
        key = str(source.get("key", "")).strip()
        root_path = str(source.get("root_path", "")).strip().lower()

        if (explicit_meta_eval or architecture_recall) and (
            key == "task_manager_handoffs"
            or root_path.startswith("task-manager/handoffs")
        ):
            excluded_sources.append(source)
            source_excluded_by_lane.append(key or root_path)
            continue

        phase = classify_source_phase(source, classification)
        if phase == "primary":
            primary_sources.append(source)
        elif phase == "fallback":
            fallback_sources.append(source)
        else:
            excluded_sources.append(source)

    explicit_meta_like = explicit_meta_eval or (
        architecture_recall and is_explicit_meta_eval_query(query, classification)
    )
    if request_class == "resume_reopen_continuation":
        effective_sources = primary_sources + [source for source in fallback_sources if source not in primary_sources]
    elif explicit_meta_like and (primary_sources or fallback_sources):
        effective_sources = primary_sources + fallback_sources
    else:
        effective_sources = primary_sources or fallback_sources
    routing = {
        "serve_class": classification.get("serve_class"),
        "budget": classification.get("budget"),
        "primary_domains": classification.get("primary_domains", []),
        "fallback_domains": classification.get("fallback_domains", []),
        "forbidden_default_domains": classification.get("forbidden_default_domains", []),
        "authority_priority_focus": classification.get("authority_priority_focus"),
        "classification": classification,
        "selected_phase": "primary" if primary_sources else ("fallback" if fallback_sources else "none"),
        "selected_source_keys": [str(source.get("key", "")) for source in effective_sources],
        "primary_source_keys": [str(source.get("key", "")) for source in primary_sources],
        "fallback_source_keys": [str(source.get("key", "")) for source in fallback_sources],
        "excluded_source_keys": [str(source.get("key", "")) for source in excluded_sources],
        "lane_excluded_source_keys": source_excluded_by_lane,
        "source_domain_tags": {
            str(source.get("key", "")): sorted(source_domain_tags(source))
            for source in selected_sources
        },
    }
    return effective_sources, routing


def select_sources(registry: dict[str, Any], requested_keys: set[str] | None, include_disabled: bool) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for source in registry.get("sources", []):
        key = str(source.get("key", "")).strip()
        enabled = bool(source.get("enabled", False))
        root_path = str(source.get("root_path", "")).strip()
        if not root_path or "*" in root_path:
            continue
        if requested_keys and key not in requested_keys:
            continue
        if not include_disabled and not enabled:
            continue
        selected.append(source)
    return selected


def load_documents(workspace_root: Path, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    for source in sources:
        source_key = str(source.get("key", source.get("root_path", "unknown")))
        root_path = workspace_root / str(source.get("root_path", ""))
        if not root_path.exists() or not root_path.is_dir():
            continue
        source_id_seed = source_key
        for path in sorted(root_path.rglob("*")):
            if not path.is_file() or path.name.startswith("."):
                continue
            if path.suffix.lower() not in {".md", ".txt", ".rst", ".py", ".js", ".ts", ".tsx", ".jsx", ".sh", ".json"}:
                continue
            try:
                record = build_document(path, root_path, f"src_{source_id_seed}")
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            documents.append({
                "source": source,
                "source_key": source_key,
                "source_root": str(root_path),
                "record": record,
                "workspace_path": str(path.relative_to(workspace_root)),
            })
    return documents


def is_meta_eval_artifact_path(path_text: str, title_text: str = "") -> bool:
    combined = f"{normalize_text(path_text)} {normalize_text(title_text)}".strip()
    markers = {
        "task 364", "task-364",
        "task 365", "task-365",
        "task 366", "task-366",
        "task 367", "task-367",
        "task 368", "task-368",
        "task 369", "task-369",
        "task 370", "task-370",
        "task 371", "task-371",
        "acceptance scenarios",
        "scenario evaluation",
        "end to end scenario evaluation",
        "evaluation summary",
        "release recommendation",
        "failure modes and hardening log",
        "hardening log",
        "hardening slice",
        "verification summary",
        "regression pack",
        "compare-local",
        "compare-psql",
        "meta artifact suppression",
        "continuation freshness",
    }
    return any(marker in combined for marker in markers)


def is_handoff_like_artifact(path_text: str, title_text: str = "") -> bool:
    combined = f"{normalize_text(path_text)} {normalize_text(title_text)}".strip()
    return "handoff" in combined or "next session" in combined


def is_generic_timestamp_handoff_path(path_text: str, title_text: str = "") -> bool:
    path_norm = normalize_text(path_text)
    title_norm = normalize_text(title_text)
    combined = f"{path_norm} {title_norm}".strip()
    return (
        path_norm.startswith("task-manager/handoffs/")
        and "task-" not in combined
        and not re.search(r"task[-\s#]*\d{2,5}", combined)
    )


def is_continuation_meta_artifact_path(path_text: str, title_text: str = "") -> bool:
    combined = f"{normalize_text(path_text)} {normalize_text(title_text)}".strip()
    markers = {
        "task 366", "task-366",
        "task 367", "task-367",
        "task 368", "task-368",
        "task 369", "task-369",
        "hardening slice",
        "hardening log",
        "failure modes",
        "evaluation summary",
        "release recommendation",
        "meta artifact suppression",
        "continuation freshness",
    }
    return any(marker in combined for marker in markers)


def is_continuation_verification_artifact_path(path_text: str, title_text: str = "") -> bool:
    combined = f"{normalize_text(path_text)} {normalize_text(title_text)}".strip()
    markers = {
        "verification-task-369",
        "verification-task-371",
        "continuation-candidate-pool-cleanup",
        "continuation-regression-pack",
        "q4 ambiguous handoff without task id",
        "natural_continue",
        "explicit_resume",
        "reopen_chain",
        "compare-local",
        "compare-psql",
        "nl_continue_after",
        "q1-psql",
        "q2-psql",
        "q3-psql",
        "q4-psql",
        "q5-psql",
    }
    return any(marker in combined for marker in markers)


def is_memory_core_meta_project_doc(path_text: str, title_text: str = "", section_text: str = "", excerpt_text: str = "") -> bool:
    combined = normalize_text(" ".join([path_text, title_text, section_text, excerpt_text]))
    if "memory core" in combined:
        return True
    task_markers = {
        "task 364", "task-364",
        "task 365", "task-365",
        "task 366", "task-366",
        "task 367", "task-367",
        "task 368", "task-368",
        "task 369", "task-369",
        "task 370", "task-370",
        "task 376", "task-376",
    }
    return any(marker in combined for marker in task_markers)


def is_expected_meta_evidence_doc(path_text: str, title_text: str = "") -> bool:
    normalized_path = normalize_text(path_text)
    combined = f"{normalized_path} {normalize_text(title_text)}".strip()
    if not normalized_path.startswith("task-manager/artifacts/task-"):
        return False
    if any(marker in normalized_path for marker in {"verification-task-", "regression-pack", ".json", "contract-and-regression-pack"}):
        return False

    direct_task_ids = {
        "task 364", "task-364",
        "task 365", "task-365",
        "task 366", "task-366",
        "task 367", "task-367",
        "task 368", "task-368",
        "task 369", "task-369",
        "task 370", "task-370",
        "task 376", "task-376",
    }
    direct_family_markers = {
        "acceptance scenarios",
        "scenario evaluation",
        "end to end scenario evaluation",
        "evaluation summary",
        "release recommendation",
        "failure modes and hardening log",
        "hardening log",
        "meta artifact suppression",
        "hardening slice",
        "continuation freshness",
        "continuation meta alignment",
        "bounded reeval summary",
    }
    return is_memory_core_meta_project_doc(path_text, title_text) and any(marker in combined for marker in direct_task_ids | direct_family_markers)


def is_canonical_architecture_doc(path_text: str, title_text: str = "") -> bool:
    combined = f"{normalize_text(path_text)} {normalize_text(title_text)}".strip()
    markers = {
        "task 333", "task-333",
        "task 334", "task-334",
        "layered architecture",
        "schema and serving policy",
    }
    return any(marker in combined for marker in markers)


def explicit_continuation_primary_task_ref(query: str, classification: dict[str, Any] | None = None) -> int | None:
    request_class = str((classification or {}).get("request_class", ""))
    if request_class != "resume_reopen_continuation":
        return None

    query_norm = normalize_text(query)
    task_refs = unique_preserve(re.findall(r"task[-\s#]*(\d{1,5})", query_norm))
    if not task_refs:
        return None
    if any(marker in query_norm for marker in {"handoff", "resume", "reopen", "continue", "after"}):
        try:
            return int(task_refs[0])
        except ValueError:
            return None
    return None


def detect_targeted_history_assisted_continuation_anchor(query: str, classification: dict[str, Any] | None = None) -> str:
    request_class = str((classification or {}).get("request_class", ""))
    if is_explicit_meta_query(query, classification):
        return ""

    query_norm = normalize_text(query)
    task_refs = unique_preserve(re.findall(r"task[-\s#]*(\d{1,5})", query_norm))

    if request_class == "resume_reopen_continuation":
        primary_task_ref = explicit_continuation_primary_task_ref(query, classification)
        if primary_task_ref is not None:
            return f"task-{primary_task_ref} handoff"
        if any(marker in query_norm for marker in {
            "conflict/open-question synthesis",
            "conflict open question synthesis",
        }):
            return "conflict/open-question synthesis"
        return ""

    if request_class != "factual_lookup":
        return ""

    terse_like = len(tokenize(query)) <= 8
    continuation_adjacent = any(marker in query_norm for marker in {
        "continue after",
        "after ",
        "с места после",
        "после ",
    })
    if not terse_like or not continuation_adjacent:
        return ""

    anchor_markers = {
        "conflict/open-question synthesis": {
            "conflict/open-question synthesis",
            "conflict open question synthesis",
        },
        "citation envelope": {"citation envelope"},
        "authority priority": {"authority priority"},
        "routing policy": {"routing policy"},
    }
    for anchor_key, markers in anchor_markers.items():
        if any(marker in query_norm for marker in markers):
            return anchor_key
    return ""


def is_history_assisted_continuation_contamination_path(path_text: str, title_text: str = "") -> bool:
    combined = normalize_text(f"{path_text} {title_text}")
    contamination_markers = {
        "verification",
        "regression-pack",
        "hardening note",
        "hardening slice",
        "tie break spec",
        "history assisted",
        "frame context serving policy",
    }
    return any(marker in combined for marker in contamination_markers)


def apply_history_assisted_continuation_tiebreak(items: list[dict[str, Any]], query: str, classification: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    activation_anchor = detect_targeted_history_assisted_continuation_anchor(query, classification)
    primary_task_ref = explicit_continuation_primary_task_ref(query, classification)
    trace = {
        "applied": False,
        "target_family_matched": bool(activation_anchor),
        "activation_reason": "",
        "anchor": activation_anchor,
        "accepted_candidate_paths": [],
        "rejected_candidate_paths": [],
    }
    if not items or not activation_anchor:
        trace["activation_reason"] = "target_family_not_matched"
        return items, trace

    adjusted: list[dict[str, Any]] = []
    accepted: list[str] = []
    rejected: list[str] = []
    for item in items:
        workspace_path = str(item.get("document", {}).get("workspace_path", ""))
        title = str(item.get("document", {}).get("title", ""))
        section_path = str(item.get("chunk", {}).get("section_path", ""))
        excerpt = str(item.get("excerpt", ""))
        combined_norm = normalize_text(" ".join([workspace_path, title, section_path, excerpt]))
        item_task_numbers = extract_task_numbers(combined_norm)
        item_is_task_anchored_handoff = is_handoff_like_artifact(workspace_path, title) and bool(item_task_numbers)
        item_is_memory_core = "memory core" in combined_norm
        item_is_generic_timestamp_handoff = is_generic_timestamp_handoff_path(workspace_path, title)

        delta = 0.0
        extra_reasons: list[str] = []
        anchor_hit = activation_anchor and all(token in combined_norm for token in activation_anchor.split())
        if item_is_task_anchored_handoff and item_is_memory_core and anchor_hit and workspace_path.startswith("task-manager/artifacts/"):
            delta += 260.0
            extra_reasons.append("history_assisted_continuation_anchor_replay_boost")
            if primary_task_ref is not None and primary_task_ref in item_task_numbers:
                delta += 70.0
                extra_reasons.append("history_assisted_continuation_primary_task_ref_boost")
            accepted.append(workspace_path)
        elif is_history_assisted_continuation_contamination_path(workspace_path, title) and not item_is_task_anchored_handoff:
            delta -= 220.0
            extra_reasons.append("history_assisted_continuation_contamination_demoted")
            rejected.append(workspace_path)
        elif item_is_generic_timestamp_handoff and not item_is_memory_core:
            delta -= 140.0
            extra_reasons.append("history_assisted_continuation_generic_handoff_demoted")
            rejected.append(workspace_path)
        elif item_is_task_anchored_handoff and not item_is_memory_core and activation_anchor not in combined_norm:
            delta -= 80.0
            extra_reasons.append("history_assisted_continuation_off_project_handoff_demoted")
            rejected.append(workspace_path)

        if delta:
            item["score"] = round(float(item.get("score", 0.0)) + delta, 3)
            item["match_reason"] = ", ".join(unique_preserve([*(item.get("match_reason", "").split(", ") if item.get("match_reason") else []), *extra_reasons]))
        adjusted.append(item)

    if not accepted and not rejected:
        trace["activation_reason"] = "target_family_matched_but_no_replay_candidates"
        return items, trace

    adjusted.sort(key=lambda item: (-float(item.get("score", 0.0)), str(item.get("document", {}).get("workspace_path", "")), int(item.get("chunk", {}).get("chunk_ordinal", 0))))
    trace.update({
        "applied": True,
        "activation_reason": "target_family_matched_and_replay_candidates_adjusted",
        "accepted_candidate_paths": unique_preserve(accepted),
        "rejected_candidate_paths": unique_preserve(rejected),
    })
    return adjusted, trace


def continuation_query_prefers_predecessor(query: str) -> bool:
    query_norm = normalize_text(query)
    markers = {
        "after task",
        "after provenance handoff",
        "predecessor",
        "predecessor chain",
        "previous handoff",
        "next bounded step",
        "с места после",
        "после task",
        "после handoff",
        "предшествен",
        "предыдущ",
        "следующим bounded шагом",
    }
    return any(marker in query_norm for marker in markers)


def is_explicit_meta_query(query: str, classification: dict[str, Any] | None = None) -> bool:
    if _is_explicit_meta_query_base(query):
        return True

    query_norm = normalize_text(query)
    request_class = str((classification or {}).get("request_class", ""))
    if request_class == "artifact_source_trace_request" and any(token in query_norm for token in {"evaluation", "scenario", "оценк", "meta", "мета"}):
        return True
    return False


def is_explicit_meta_eval_query(query: str, classification: dict[str, Any] | None = None) -> bool:
    query_norm = normalize_text(query)
    if not is_explicit_meta_query(query, classification):
        return False
    eval_markers = {
        "evaluation", "artifacts", "artifact", "baseline", "fail/pass", "fail pass",
        "summary", "hardening", "hardening slice", "release", "scenario", "stage 5", "slice", "alignment",
        "оцен", "артеф", "файл", "файлов", "baseline fail", "baseline pass", "слайс",
    }
    return any(marker in query_norm for marker in eval_markers)


def _is_explicit_meta_query_base(query: str) -> bool:
    return base_is_explicit_meta_query(query)


def meta_eval_subfamily_priority(item: dict[str, Any], query: str, classification: dict[str, Any]) -> int:
    request_class = str(classification.get("request_class", ""))
    if request_class != "meta_evaluation_recall":
        return 9
    target = str(classification.get("meta_subfamily") or detect_meta_evaluation_subfamily(query))
    workspace_path = str(item.get("document", {}).get("workspace_path", ""))
    title = str(item.get("document", {}).get("title", ""))
    section_value = str(item.get("chunk", {}).get("section_path", ""))
    excerpt_value = str(item.get("excerpt", ""))
    if not is_memory_core_meta_project_doc(workspace_path, title, section_value, excerpt_value):
        return 8
    doc_text = normalize_text(" ".join([
        workspace_path,
        title,
    ]))
    section_text = normalize_text(section_value)
    excerpt_text = normalize_text(excerpt_value)
    combined = " ".join([doc_text, section_text, excerpt_text]).strip()
    if target == "release_recommendation":
        if "evaluation summary and release recommendation" in doc_text:
            return 0
        if "release recommendation" in doc_text and "bounded reeval summary" not in doc_text:
            return 1
        if any(marker in section_text for marker in {"executive verdict", "must do before broader release"}):
            return 2
        if "verdict" in combined:
            return 3
        if "bounded reeval summary" in combined:
            return 4
        if "evaluation summary" in combined:
            return 5
        if "hardening slice" in combined:
            return 6
    if target == "hardening_slice":
        if any(marker in doc_text for marker in {"hardening slice", "hardening log"}):
            return 0
        if any(marker in section_text for marker in {"must do before broader release", "best sequencing for the next hardening steps"}) or "next hardening" in combined:
            return 1
        if "evaluation summary" in combined:
            return 2
    if target == "evaluation_summary":
        if "evaluation summary" in doc_text or any(marker in section_text for marker in {"baseline result before bounded fixes", "acceptance scenarios under test"}):
            return 0
        if any(marker in combined for marker in {"acceptance scenarios", "baseline result", "fail pass", "fail/pass"}):
            return 1
        if "release recommendation" in combined:
            return 2
        if "hardening slice" in combined:
            return 3
    return 4


def continuation_shape_priority(item: dict[str, Any], query: str, classification: dict[str, Any]) -> int:
    if str(classification.get("request_class", "")) != "resume_reopen_continuation":
        return 9
    workspace_path = str(item.get("document", {}).get("workspace_path", ""))
    title = str(item.get("document", {}).get("title", ""))
    combined = normalize_text(f"{workspace_path} {title}")
    authority = str(item.get("authority", {}).get("layer", ""))
    if authority != "canonical_handoff":
        return 9
    if workspace_path.startswith("task-manager/artifacts/") and "task-" in combined and "handoff" in combined:
        return 0
    if workspace_path.startswith("task-manager/handoffs/") and "task-" in combined:
        return 1
    if workspace_path.startswith("task-manager/handoffs/"):
        return 2
    if "handoff" in combined:
        return 3
    return 4


def meta_evaluation_authority_bucket(item: dict[str, Any], query: str, classification: dict[str, Any]) -> int:
    request_class = str(classification.get("request_class", ""))
    if request_class != "meta_evaluation_recall":
        return 9

    workspace_path = str(item.get("document", {}).get("workspace_path", ""))
    title = str(item.get("document", {}).get("title", ""))
    section_text = normalize_text(str(item.get("chunk", {}).get("section_path", "")))
    excerpt_text = normalize_text(str(item.get("excerpt", "")))
    combined = normalize_text(" ".join([workspace_path, title, section_text, excerpt_text]))
    authority = str(item.get("authority", {}).get("layer", ""))

    is_verification_wrapper = "verification-task-" in workspace_path or "regression-pack" in workspace_path
    is_handoff_like = "handoff" in combined or authority == "canonical_handoff"
    is_direct_meta_artifact = authority == "evidence_record" and is_meta_eval_artifact_path(workspace_path, title) and not is_verification_wrapper and not is_handoff_like
    is_handoff_derived_evidence = authority == "evidence_record" and is_handoff_like

    if is_direct_meta_artifact:
        return 0
    if is_handoff_derived_evidence:
        return 1
    if is_verification_wrapper:
        return 2
    return 3


def lane_basis_priority(item: dict[str, Any], query: str, classification: dict[str, Any]) -> int:
    request_class = str(classification.get("request_class", ""))
    workspace_path = str(item.get("document", {}).get("workspace_path", ""))
    title = str(item.get("document", {}).get("title", ""))
    section_text = normalize_text(str(item.get("chunk", {}).get("section_path", "")))
    excerpt_text = normalize_text(str(item.get("excerpt", "")))
    combined = normalize_text(" ".join([workspace_path, title, section_text, excerpt_text]))
    authority = str(item.get("authority", {}).get("layer", ""))
    is_task_artifact = workspace_path.startswith("task-manager/artifacts/task-")
    is_handoff_like = "handoff" in combined or authority == "canonical_handoff"

    if request_class == "meta_evaluation_recall":
        meta_bucket = meta_evaluation_authority_bucket(item, query, classification)
        if meta_bucket == 0:
            return 0
        if meta_bucket == 1:
            return 2
        if meta_bucket == 2:
            return 3
        if authority == "evidence_record" and any(marker in combined for marker in {
            "evaluation", "evaluation summary", "acceptance", "acceptance scenarios", "release recommendation",
            "hardening slice", "hardening log", "fail/pass", "fail pass", "baseline result", "stage-5", "stage 5",
        }):
            return 1
        if authority == "evidence_record":
            return 4
        if is_handoff_like and is_task_artifact:
            return 8
        if authority == "canonical_handoff":
            return 7
        return 5

    if request_class == "architecture_design_recall":
        if authority == "evidence_record" and is_canonical_architecture_doc(workspace_path, title):
            return 0
        if authority == "evidence_record" and any(marker in combined for marker in {
            "architecture", "design", "policy", "schema", "serving policy", "retrieval policy", "baseline behavior",
        }):
            return 1
        if authority == "evidence_record":
            return 2
        if is_handoff_like and is_task_artifact:
            return 8
        if authority == "canonical_handoff":
            return 7
        if authority in {"memory_note", "wiki_page"}:
            return 4
        return 5

    return 9


def is_stage4_audit_trace_query(query: str, classification: dict[str, Any]) -> bool:
    if str(classification.get("request_class", "")) != "artifact_source_trace_request":
        return False
    query_norm = normalize_text(query)
    return "stage 4" in query_norm or "stage4" in query_norm


STAGE4_PROVING_TASK_COMPONENT_MARKERS: dict[int, set[str]] = {
    360: {"routing", "route", "routing policy"},
    361: {"authority", "ranking", "priority"},
    362: {"citation", "envelope", "cite", "cited"},
    363: {"conflict", "synthesis", "open question", "open questions"},
}


STAGE4_AUDIT_QUERY_COMPONENT_MARKERS: dict[int, set[str]] = {
    360: {"routing", "route"},
    361: {"authority", "ranking", "priority"},
    362: {"citation", "envelope", "cite", "citation envelope"},
    363: {"conflict", "synthesis", "open question", "open questions"},
}


STAGE4_AUDIT_WRAPPER_MARKERS = {
    "task 364", "task 365", "task 366", "task 367", "task 368", "task 369", "task 370", "task 371",
    "verification-task-369", "verification-task-371",
    "evaluation summary", "release recommendation",
    "failure modes and hardening log", "acceptance scenarios", "verification summary",
    "compare-local", "compare-psql", "summary json", "regression pack", "hardening slice", "meta alignment",
}


STAGE4_AUDIT_NOISE_PATH_MARKERS = {
    "verification-task-",
    "continuation-regression-pack",
    "stage-5-1-acceptance-scenarios",
    "stage-5-2-end-to-end-scenario-evaluation",
    "meta-artifact-suppression-hardening-slice",
    "evaluation-summary",
    "release-recommendation",
    "review-handoff-envelope-against-truth-boundary-contract",
}


def stage4_audit_component_task_ids(query: str) -> set[int]:
    query_norm = normalize_text(query)
    matched: set[int] = set()
    for task_id, markers in STAGE4_AUDIT_QUERY_COMPONENT_MARKERS.items():
        if any(marker in query_norm for marker in markers):
            matched.add(task_id)
    return matched


def stage4_audit_item_signals(item: dict[str, Any]) -> dict[str, Any]:
    workspace_path = str(item.get("document", {}).get("workspace_path", ""))
    title = str(item.get("document", {}).get("title", ""))
    section_path = str(item.get("chunk", {}).get("section_path", ""))
    excerpt = str(item.get("excerpt", ""))
    doc_identity = normalize_text(" ".join([workspace_path, title]))
    combined = normalize_text(" ".join([workspace_path, title, section_path, excerpt]))

    proving_task_numbers = {360, 361, 362, 363}
    doc_task_numbers = set(extract_task_numbers(doc_identity))
    item_task_numbers = set(extract_task_numbers(combined))
    proving_doc_match_count = len(doc_task_numbers & proving_task_numbers)
    proving_match_count = len(item_task_numbers & proving_task_numbers)

    component_alignment_task_ids: set[int] = set()
    for task_id, markers in STAGE4_PROVING_TASK_COMPONENT_MARKERS.items():
        if task_id in doc_task_numbers and any(marker in combined for marker in markers):
            component_alignment_task_ids.add(task_id)

    workspace_path_norm = normalize_text(workspace_path)
    is_wrapper = any(marker in combined for marker in STAGE4_AUDIT_WRAPPER_MARKERS)
    is_noise_path = any(marker in workspace_path_norm for marker in STAGE4_AUDIT_NOISE_PATH_MARKERS)
    return {
        "workspace_path": workspace_path,
        "title": title,
        "combined": combined,
        "doc_task_numbers": doc_task_numbers,
        "item_task_numbers": item_task_numbers,
        "proving_doc_match_count": proving_doc_match_count,
        "proving_match_count": proving_match_count,
        "component_alignment_task_ids": component_alignment_task_ids,
        "is_wrapper": is_wrapper,
        "is_noise_path": is_noise_path,
    }


def stage4_trace_priority(item: dict[str, Any], query: str, classification: dict[str, Any]) -> int:
    if not is_stage4_audit_trace_query(query, classification):
        return 9

    signals = stage4_audit_item_signals(item)
    proving_doc_match_count = int(signals["proving_doc_match_count"])
    proving_match_count = int(signals["proving_match_count"])
    component_alignment = len(signals["component_alignment_task_ids"])
    is_wrapper = bool(signals["is_wrapper"])

    if proving_doc_match_count and component_alignment and not is_wrapper:
        return 0
    if proving_doc_match_count and not is_wrapper:
        return 1
    if proving_match_count and not is_wrapper:
        return 2
    if is_wrapper and proving_match_count:
        return 6
    if is_wrapper:
        return 7
    return 4


ARTIFACT_TRACE_WRAPPER_PATH_MARKERS = {
    "verification-",
    ".run.json",
    "outputs/",
    "stage-5-1-acceptance-scenarios",
    "stage-5-2-end-to-end-scenario-evaluation",
    "hardening-slice",
    "evaluation-summary",
    "release-recommendation",
    "regression",
}


ARTIFACT_TRACE_WRAPPER_TEXT_MARKERS = {
    "acceptance scenarios",
    "evaluation summary",
    "verification summary",
    "regression pack",
    "hardening slice",
    "failure modes and hardening log",
    "release recommendation",
}


def artifact_trace_item_signals(query: str, document_path: str, document_title: str, section_path: str, excerpt: str) -> dict[str, Any]:
    query_norm = normalize_text(query)
    doc_norm = normalize_text(" ".join([document_path, document_title]))
    combined = normalize_text(" ".join([document_path, document_title, section_path, excerpt]))
    query_task_numbers = set(extract_task_numbers(query_norm))
    doc_task_numbers = set(extract_task_numbers(doc_norm))
    item_task_numbers = set(extract_task_numbers(combined))

    asks_for_file_or_path = any(marker in query_norm for marker in {
        "which file", "what file", "file contains", "artifact path", "path",
        "какой файл", "каких файлов", "из каких файлов", "покажи файлы", "где файл", "путь",
    })
    asks_for_handoff = any(marker in query_norm for marker in {"handoff", "artifact", "артеф", "handoff artifact"})
    asks_for_status_state = any(marker in query_norm for marker in {"current status", "current state", "task state", "next step", "status", "state", "handoff/status", "статус", "состояние", "следующий шаг"})
    doc_is_handoff_like = is_handoff_like_artifact(document_path, document_title)
    doc_has_exact_task = bool(query_task_numbers & doc_task_numbers)
    chunk_only_task_hit = bool((query_task_numbers & item_task_numbers) and not doc_has_exact_task)
    path_has_filename_shape = document_path.endswith((".md", ".json", ".txt", ".py", ".yaml", ".yml"))
    is_wrapper = any(marker in document_path.lower() for marker in ARTIFACT_TRACE_WRAPPER_PATH_MARKERS) or any(marker in combined for marker in ARTIFACT_TRACE_WRAPPER_TEXT_MARKERS)
    asks_for_exact_task_handoff_file = bool(query_task_numbers) and asks_for_file_or_path and asks_for_handoff

    return {
        "query_task_numbers": query_task_numbers,
        "doc_task_numbers": doc_task_numbers,
        "item_task_numbers": item_task_numbers,
        "asks_for_file_or_path": asks_for_file_or_path,
        "asks_for_handoff": asks_for_handoff,
        "asks_for_status_state": asks_for_status_state,
        "doc_is_handoff_like": doc_is_handoff_like,
        "doc_has_exact_task": doc_has_exact_task,
        "chunk_only_task_hit": chunk_only_task_hit,
        "path_has_filename_shape": path_has_filename_shape,
        "is_wrapper": is_wrapper,
        "asks_for_exact_task_handoff_file": asks_for_exact_task_handoff_file,
    }


def preference_recall_item_signals(query: str, document_path: str, document_title: str, section_path: str, excerpt: str, source_key: str = "") -> dict[str, Any]:
    query_norm = normalize_text(query)
    path_norm = normalize_text(document_path)
    title_norm = normalize_text(document_title)
    combined = normalize_text(" ".join([document_path, document_title, section_path, excerpt]))

    query_mentions_yuriy = any(marker in query_norm for marker in {"юрий", "yuri", "юрии", "юрию"})
    asks_for_answer_style = any(marker in query_norm for marker in {
        "как лучше отвечать", "лучше отвечать", "коротко по делу", "с длинным разбором",
        "how should", "how best to answer", "answer style", "operating style", "prefer", "style",
    })
    is_memory_note = source_key == "openclaw_shared_memory" or path_norm.startswith("memory/")
    is_session_greeting_note = "session-greeting" in path_norm or "new-session" in path_norm
    is_daily_memory_note = is_memory_note and re.search(r"memory/20\d{2}-\d{2}-\d{2}(?:[^/]*)\.md$", document_path.replace('\\', '/')) is not None
    has_explicit_preference_anchor = any(marker in combined for marker in {
        "юрий попросил зафиксировать правило общения",
        "правило общения",
        "не должен соглашаться из вежливости",
        "не идти на поводу",
        "говорить прямо и по делу",
        "спокойно прямо и по делу",
        "спокойный прямой по делу",
        "calibrated confidence",
        "durable preference memory",
    })
    has_style_phrase = any(marker in combined for marker in {
        "коротко",
        "по делу",
        "прямо",
        "без лишней суеты",
        "без лишнего шума",
        "спокойно",
        "не соглашаться",
    })
    looks_like_artifact_or_transcript = any(marker in path_norm for marker in {"task-manager/artifacts/", "outputs/", "handoffs/"})
    title_or_path_preference_hint = any(marker in title_norm or marker in path_norm for marker in {
        "frame architecture",
        "judge gate",
        "new session",
        "session greeting",
        "session-start",
    })
    has_direct_rule_phrases = any(marker in combined for marker in {
        "не должен соглашаться из вежливости",
        "не идти на поводу",
        "говорить прямо и по делу",
    })
    has_compact_style_pair = ("коротко" in combined and "по делу" in combined) or ("спокойно" in combined and "по делу" in combined)

    return {
        "query_mentions_yuriy": query_mentions_yuriy,
        "asks_for_answer_style": asks_for_answer_style,
        "is_memory_note": is_memory_note,
        "is_session_greeting_note": is_session_greeting_note,
        "is_daily_memory_note": is_daily_memory_note,
        "has_explicit_preference_anchor": has_explicit_preference_anchor,
        "has_style_phrase": has_style_phrase,
        "looks_like_artifact_or_transcript": looks_like_artifact_or_transcript,
        "title_or_path_preference_hint": title_or_path_preference_hint,
        "has_direct_rule_phrases": has_direct_rule_phrases,
        "has_compact_style_pair": has_compact_style_pair,
    }


def apply_meta_artifact_suppression(items: list[dict[str, Any]], query: str, classification: dict[str, Any]) -> list[dict[str, Any]]:
    if not items:
        return items
    if is_explicit_meta_query(query, classification):
        return items

    request_class = str(classification.get("request_class", ""))
    all_non_meta_classes = {
        "current_task_execution",
        "resume_reopen_continuation",
        "preference_operating_style_recall",
        "artifact_source_trace_request",
        "policy_decision_lookup",
        "factual_lookup",
        "architecture_design_recall",
    }
    hard_exclude_classes = {
        "current_task_execution",
        "resume_reopen_continuation",
        "preference_operating_style_recall",
        "artifact_source_trace_request",
    }
    strong_demote_classes = {
        "policy_decision_lookup",
        "factual_lookup",
        "architecture_design_recall",
    }

    meta_items: list[dict[str, Any]] = []
    non_meta_items: list[dict[str, Any]] = []
    for item in items:
        workspace_path = str(item.get("document", {}).get("workspace_path", ""))
        title = str(item.get("document", {}).get("title", ""))
        if is_meta_eval_artifact_path(workspace_path, title):
            meta_items.append(item)
        else:
            non_meta_items.append(item)

    if not meta_items:
        return items

    if request_class in hard_exclude_classes and non_meta_items:
        for item in meta_items:
            item["score"] = round(float(item.get("score", 0.0)) - 9999.0, 3)
            item["match_reason"] = ", ".join(unique_preserve([*(item.get("match_reason", "").split(", ") if item.get("match_reason") else []), "meta_artifact_hard_excluded_for_request_class"]))
        items = non_meta_items + meta_items
    elif request_class in strong_demote_classes and non_meta_items:
        for item in meta_items:
            item["score"] = round(float(item.get("score", 0.0)) - 520.0, 3)
            item["match_reason"] = ", ".join(unique_preserve([*(item.get("match_reason", "").split(", ") if item.get("match_reason") else []), "meta_artifact_strong_class_aware_suppression"]))
        items = non_meta_items + meta_items
    elif request_class in all_non_meta_classes and non_meta_items:
        for item in meta_items:
            item["score"] = round(float(item.get("score", 0.0)) - 320.0, 3)
            item["match_reason"] = ", ".join(unique_preserve([*(item.get("match_reason", "").split(", ") if item.get("match_reason") else []), "meta_artifact_general_non_meta_suppression"]))
        items = non_meta_items + meta_items
    elif non_meta_items:
        for item in meta_items:
            item["score"] = round(float(item.get("score", 0.0)) - 260.0, 3)
            item["match_reason"] = ", ".join(unique_preserve([*(item.get("match_reason", "").split(", ") if item.get("match_reason") else []), "meta_artifact_strong_suppression"]))
        items = non_meta_items + meta_items
    else:
        for item in meta_items:
            item["score"] = round(float(item.get("score", 0.0)) - 120.0, 3)
            item["match_reason"] = ", ".join(unique_preserve([*(item.get("match_reason", "").split(", ") if item.get("match_reason") else []), "meta_artifact_soft_fallback_penalty"]))

    items.sort(key=lambda item: (-float(item.get("score", 0.0)), str(item.get("document", {}).get("workspace_path", "")), int(item.get("chunk", {}).get("chunk_ordinal", 0))))
    return items


def apply_lane_candidate_hygiene(items: list[dict[str, Any]], query: str, classification: dict[str, Any]) -> list[dict[str, Any]]:
    if not items:
        return items

    request_class = str(classification.get("request_class", ""))
    explicit_meta_eval = request_class == "meta_evaluation_recall"
    architecture_recall = request_class == "architecture_design_recall"
    if not explicit_meta_eval and not architecture_recall:
        return items

    query_norm = normalize_text(query)
    for item in items:
        workspace_path = str(item.get("document", {}).get("workspace_path", ""))
        title = str(item.get("document", {}).get("title", ""))
        section = str(item.get("chunk", {}).get("section_path", ""))
        combined = normalize_text(" ".join([workspace_path, title, section, str(item.get("excerpt", ""))]))
        reasons = item.get("match_reason", "").split(", ") if item.get("match_reason") else []
        delta = 0.0

        is_verification_wrapper = "verification-task-" in workspace_path or "regression-pack" in workspace_path
        is_memory_handoff_note = workspace_path.startswith("memory/") and "handoff" in combined
        is_task_manager_handoff = workspace_path.startswith("task-manager/handoffs/")
        is_operational_handoff = (workspace_path.startswith("task-manager/artifacts/task-") and "handoff" in combined) or is_task_manager_handoff
        is_status_handoff = "status-handoff" in workspace_path or "status handoff" in combined
        is_direct_task_artifact = workspace_path.startswith("task-manager/artifacts/task-") and not is_operational_handoff
        is_architecture_doc = any(marker in combined for marker in {
            "architecture", "design", "schema and serving policy", "retrieval policy", "policy matrix", "baseline behavior",
            "layered architecture", "serving policy",
        })
        is_meta_eval_doc = any(marker in combined for marker in {
            "evaluation summary", "release recommendation", "hardening slice", "hardening log",
            "acceptance scenarios", "baseline result", "fail/pass", "fail pass", "stage-5", "stage 5",
        }) or is_meta_eval_artifact_path(workspace_path, title)

        if explicit_meta_eval:
            if is_verification_wrapper:
                delta -= 1200.0
                reasons.append("meta_eval_verification_wrapper_demoted")
            if is_memory_handoff_note:
                delta -= 900.0
                reasons.append("meta_eval_memory_handoff_demoted")
            if is_status_handoff:
                delta -= 820.0
                reasons.append("meta_eval_status_handoff_demoted")
            elif is_operational_handoff:
                delta -= 1700.0 if is_task_manager_handoff else 980.0
                reasons.append("meta_eval_operational_handoff_demoted")
            if is_meta_eval_doc and is_direct_task_artifact:
                delta += 220.0
                reasons.append("meta_eval_evidence_boost")
            if workspace_path.startswith("memory/"):
                if re.search(r"memory/20\d{2}-\d{2}-\d{2}(?:[^/]*)\.md$", workspace_path.replace('\\', '/')):
                    delta -= 1100.0
                    reasons.append("meta_eval_daily_memory_demoted")
                else:
                    delta -= 420.0
                    reasons.append("meta_eval_memory_note_support_only_demoted")
            if workspace_path.startswith("memory/") and is_expected_meta_evidence_doc(workspace_path, title):
                delta -= 1400.0
                reasons.append("meta_eval_memory_note_when_expected_evidence_exists_demoted")
            if is_expected_meta_evidence_doc(workspace_path, title) and is_direct_task_artifact:
                delta += 680.0
                reasons.append("meta_eval_expected_evidence_family_boost")

        if architecture_recall:
            if is_verification_wrapper:
                delta -= 1200.0
                reasons.append("architecture_verification_wrapper_demoted")
            if is_memory_handoff_note:
                delta -= 950.0
                reasons.append("architecture_memory_handoff_demoted")
            if is_status_handoff:
                delta -= 850.0
                reasons.append("architecture_status_handoff_demoted")
            elif is_operational_handoff and not is_architecture_doc:
                delta -= 1450.0 if is_task_manager_handoff else 780.0
                reasons.append("architecture_operational_handoff_demoted")
            if is_architecture_doc:
                delta += 260.0
                reasons.append("architecture_design_evidence_boost")
            if is_canonical_architecture_doc(workspace_path, title) and is_direct_task_artifact:
                delta += 860.0
                reasons.append("architecture_canonical_doc_boost")
            if "task-358" in combined or "task 358" in combined or (is_operational_handoff and "policy matrix" in combined):
                delta -= 1200.0
                reasons.append("architecture_handoff_policy_matrix_demoted")
            if workspace_path.startswith("memory/") and not is_canonical_architecture_doc(workspace_path, title):
                delta -= 520.0
                reasons.append("architecture_memory_note_support_only_demoted")
            if "policy" in query_norm and "policy" in combined:
                delta += 80.0
                reasons.append("architecture_policy_query_alignment")

        if delta:
            item["score"] = round(float(item.get("score", 0.0)) + delta, 3)
            item["match_reason"] = ", ".join(unique_preserve(reasons))

    items.sort(key=lambda item: (-float(item.get("score", 0.0)), str(item.get("document", {}).get("workspace_path", "")), int(item.get("chunk", {}).get("chunk_ordinal", 0))))
    return items


def extract_task_numbers(text: str) -> list[int]:
    normalized = text.lower()
    patterns = [
        r"task[-\s#]*(\d{1,5})",
        r"задач[аеиуыёюя]{0,3}[-\s#]*(\d{1,5})",
    ]
    numbers: list[int] = []
    for pattern in patterns:
        numbers.extend(int(match) for match in re.findall(pattern, normalized))
    return unique_preserve([number for number in numbers if number > 0])


def extract_iso_date(text: str) -> str:
    match = re.search(r"(20\d{2}-\d{2}-\d{2})", text)
    return match.group(1) if match else ""


def ymd_to_ordinal(ymd: str) -> int:
    if not ymd:
        return 0
    try:
        year, month, day = [int(part) for part in ymd.split("-")]
    except ValueError:
        return 0
    return year * 372 + month * 31 + day


def score_candidate(query: str, query_tokens: list[str], document: dict[str, Any], chunk: dict[str, Any]) -> dict[str, Any] | None:
    record = document["record"]
    path_norm = normalize_text(record.path)
    title_norm = normalize_text(record.title)
    section_norm = normalize_text(chunk.get("section_path", ""))
    chunk_norm = normalize_text(chunk.get("chunk_text", ""))
    query_norm = normalize_text(query)
    classification = classify_request(query)

    score = 0.0
    reasons: list[str] = []
    is_meta_eval_artifact = is_meta_eval_artifact_path(record.path, record.title)

    if query_norm and query_norm == path_norm:
        score += 180
        reasons.append("exact_path")
    elif query_norm and query_norm in path_norm:
        score += 120
        reasons.append("path_substring")

    if query_norm and query_norm == title_norm:
        score += 170
        reasons.append("exact_title")
    elif query_norm and query_norm in title_norm:
        score += 115
        reasons.append("title_substring")

    token_hits = 0
    title_hits = 0
    path_hits = 0
    section_hits = 0
    chunk_hits = 0
    rare_bonus = 0.0
    milestone_tokens = {"milestone", "milestones"}
    core_query_tokens = [token for token in query_tokens if token not in milestone_tokens]
    title_path_core_tokens = set()

    token_counts = Counter(tokenize(record.title + " " + record.path + " " + chunk.get("section_path", "") + " " + chunk.get("chunk_text", "")))
    for token in query_tokens:
        present = False
        token_in_title = token in title_norm
        token_in_path = token in path_norm
        if token_in_title:
            title_hits += 1
            present = True
        if token_in_path:
            path_hits += 1
            present = True
        if token in section_norm:
            section_hits += 1
            present = True
        if token in chunk_norm:
            chunk_hits += 1
            present = True
        if token in core_query_tokens and (token_in_title or token_in_path):
            title_path_core_tokens.add(token)
        if present:
            token_hits += 1
            rare_bonus += 1.0 / math.sqrt(max(1, token_counts.get(token, 1)))

    if token_hits == 0 and score == 0:
        return None

    if token_hits:
        coverage = token_hits / max(1, len(query_tokens))
        score += coverage * 90
        score += title_hits * 16
        score += path_hits * 14
        score += section_hits * 10
        score += min(chunk_hits, len(query_tokens)) * 8
        score += rare_bonus * 10
        if coverage >= 0.99:
            reasons.append("all_query_tokens_covered")
        elif coverage >= 0.6:
            reasons.append("strong_token_overlap")
        else:
            reasons.append("partial_lexical_overlap")
        if title_hits:
            reasons.append("titleish_match")
        if path_hits:
            reasons.append("path_match")
        if section_hits:
            reasons.append("section_match")
        if chunk_hits:
            reasons.append("chunk_text_match")

    if (
        any(token in milestone_tokens for token in query_tokens)
        and len(core_query_tokens) == 1
        and len(title_path_core_tokens) == 1
    ):
        score += 9
        reasons.append("milestone_single_core_title_path_cover")

    if str(classification.get("request_class", "")) == "meta_evaluation_recall":
        meta_query_markers = {
            "evaluation", "summary", "hardening", "log", "release", "recommendation",
            "baseline", "fail", "pass", "artifacts", "stage", "continuation", "meta",
        }
        core_meta_hits = sum(1 for token in query_tokens if token in meta_query_markers and (token in title_norm or token in path_norm))
        if is_meta_eval_artifact:
            score += 180.0
            reasons.append("meta_eval_direct_artifact_boost")
            if core_meta_hits:
                score += core_meta_hits * 22.0
                reasons.append("meta_eval_title_path_alignment")
        elif any(marker in path_norm or marker in title_norm for marker in {"verification-task-", "regression-pack"}):
            score -= 160.0
            reasons.append("meta_eval_wrapper_candidate_demoted")
        elif "handoff" in path_norm or "handoff" in title_norm:
            score -= 120.0
            reasons.append("meta_eval_handoff_candidate_demoted")

    if is_stage4_audit_trace_query(query, classification):
        stage4_item = {
            "document": {
                "workspace_path": record.path,
                "title": record.title,
            },
            "chunk": {
                "section_path": chunk.get("section_path", ""),
            },
            "excerpt": chunk.get("chunk_text", ""),
        }
        signals = stage4_audit_item_signals(stage4_item)
        requested_component_task_ids = stage4_audit_component_task_ids(query)
        aligned_requested_component_ids = requested_component_task_ids & set(signals["component_alignment_task_ids"])
        doc_task_numbers = set(signals["doc_task_numbers"])
        is_wrapper = bool(signals["is_wrapper"])

        if aligned_requested_component_ids:
            score += 260.0 + (35.0 * len(aligned_requested_component_ids))
            reasons.append("stage4_component_task_alignment")
        elif requested_component_task_ids and (requested_component_task_ids & doc_task_numbers) and not is_wrapper:
            score += 140.0 + (20.0 * len(requested_component_task_ids & doc_task_numbers))
            reasons.append("stage4_component_task_doc_match")
        elif requested_component_task_ids and (requested_component_task_ids & set(signals["item_task_numbers"])) and not is_wrapper:
            score += 75.0
            reasons.append("stage4_component_task_chunk_match")

        if requested_component_task_ids and requested_component_task_ids.issubset(doc_task_numbers) and not is_wrapper:
            score += 110.0
            reasons.append("stage4_full_component_cover")

        if is_wrapper:
            score -= 240.0
            reasons.append("stage4_wrapper_penalty")
        if bool(signals.get("is_noise_path")) and not signals["proving_doc_match_count"]:
            score -= 260.0
            reasons.append("stage4_noise_path_penalty")

    if is_meta_eval_artifact and not is_explicit_meta_query(query):
        score -= 160
        reasons.append("meta_eval_artifact_penalty")

    request_class = str(classification.get("request_class", ""))
    if request_class == "artifact_source_trace_request":
        trace_signals = artifact_trace_item_signals(
            query=query,
            document_path=record.path,
            document_title=record.title,
            section_path=chunk.get("section_path", ""),
            excerpt=chunk.get("chunk_text", ""),
        )
        trace_delta = 0.0
        trace_reasons: list[str] = []

        if trace_signals["asks_for_file_or_path"] and trace_signals["path_has_filename_shape"]:
            trace_delta += 24.0
            trace_reasons.append("artifact_trace_filename_shape")

        if trace_signals["doc_has_exact_task"]:
            trace_delta += 380.0
            trace_reasons.append("artifact_trace_exact_task_doc_match")
            if trace_signals["asks_for_handoff"] and trace_signals["doc_is_handoff_like"]:
                trace_delta += 320.0
                trace_reasons.append("artifact_trace_task_handoff_doc_match")
            if trace_signals["asks_for_exact_task_handoff_file"] and trace_signals["doc_is_handoff_like"]:
                trace_delta += 900.0
                trace_reasons.append("artifact_trace_exact_task_handoff_file_boost")
            if trace_signals["asks_for_status_state"] and trace_signals["doc_is_handoff_like"]:
                trace_delta += 280.0
                trace_reasons.append("artifact_trace_task_status_state_handoff_doc_match")
        elif trace_signals["chunk_only_task_hit"]:
            trace_delta -= 160.0
            trace_reasons.append("artifact_trace_chunk_only_task_mention_demoted")

        if trace_signals["query_task_numbers"] and not trace_signals["doc_has_exact_task"]:
            trace_delta -= 150.0
            trace_reasons.append("artifact_trace_nonmatching_doc_task_demoted")
            if trace_signals["asks_for_status_state"]:
                trace_delta -= 320.0
                trace_reasons.append("artifact_trace_status_state_nonmatching_doc_task_hard_demoted")
            if " path " in f" {normalize_text(record.title)} {normalize_text(record.path)} ":
                trace_delta -= 120.0
                trace_reasons.append("artifact_trace_generic_path_doc_demoted")

        if trace_signals["query_task_numbers"] and trace_signals["doc_is_handoff_like"] and not trace_signals["doc_has_exact_task"]:
            trace_delta -= 90.0
            trace_reasons.append("artifact_trace_wrong_handoff_task_demoted")

        if trace_signals["is_wrapper"] and trace_signals["query_task_numbers"]:
            trace_delta -= 260.0
            trace_reasons.append("artifact_trace_wrapper_file_demoted")

        if trace_delta:
            score += trace_delta
            reasons.extend(trace_reasons)
    elif request_class == "policy_decision_lookup":
        combined_norm = normalize_text(" ".join([
            document["workspace_path"],
            record.title,
            chunk.get("section_path", ""),
            chunk.get("chunk_text", ""),
        ]))
        query_norm = normalize_text(query)
        policy_delta = 0.0
        policy_reasons: list[str] = []
        is_memory_note = str(document.get("source_key", "")) == "openclaw_shared_memory" or document["workspace_path"].startswith("memory/")
        policy_markers = {
            "policy", "rule", "rationale", "why", "decision", "authority priority", "canonical_handoff",
            "routing policy", "preferred over memory notes", "handoff-first", "почему", "политика", "правило", "решение", "обоснование"
        }
        has_policy_markers = any(marker in combined_norm for marker in policy_markers)
        is_memory_core_artifact = "memory core" in combined_norm
        is_task_artifact = document["workspace_path"].startswith("task-manager/artifacts/")
        is_handoff_like_doc = is_handoff_like_artifact(document["workspace_path"], record.title)
        query_task_numbers = set(extract_task_numbers(query))
        doc_task_numbers = set(extract_task_numbers(normalize_text(f"{document['workspace_path']} {record.title}")))

        query_mentions_memory_core = "memory core" in query_norm
        query_mentions_routing_family = any(marker in query_norm for marker in {"routing policy", "authority priority", "canonical_handoff", "handoff-first", "preferred over memory notes"})
        query_mentions_classifier = any(marker in query_norm for marker in {"classifier", "routing enforcement", "routing"})
        doc_mentions_routing_family = any(marker in combined_norm for marker in {"routing policy", "authority priority", "canonical_handoff", "handoff-first", "preferred over memory notes"})
        doc_mentions_classifier = any(marker in combined_norm for marker in {"classifier", "routing enforcement", "routing"})
        targeted_policy_task_ids = {360, 361}
        doc_has_targeted_policy_task = bool(doc_task_numbers & targeted_policy_task_ids)
        query_has_targeted_policy_task = bool(query_task_numbers & targeted_policy_task_ids)

        if is_task_artifact and has_policy_markers:
            policy_delta += 260.0
            policy_reasons.append("policy_artifact_marker_boost")
        if is_handoff_like_doc and has_policy_markers:
            policy_delta += 180.0
            policy_reasons.append("policy_handoff_rule_boost")
        if is_memory_core_artifact and has_policy_markers:
            policy_delta += 110.0
            policy_reasons.append("policy_memory_core_rule_boost")
        if query_mentions_memory_core and is_memory_core_artifact:
            policy_delta += 320.0
            policy_reasons.append("policy_memory_core_query_alignment")
        if query_mentions_routing_family and doc_mentions_routing_family:
            policy_delta += 340.0
            policy_reasons.append("policy_routing_family_alignment")
        if query_mentions_classifier and doc_mentions_classifier:
            policy_delta += 180.0
            policy_reasons.append("policy_classifier_alignment")
        if doc_has_targeted_policy_task and (query_has_targeted_policy_task or query_mentions_routing_family or query_mentions_memory_core):
            policy_delta += 420.0
            policy_reasons.append("policy_targeted_task_family_boost")
        if query_task_numbers and doc_task_numbers and (query_task_numbers & doc_task_numbers):
            policy_delta += 180.0
            policy_reasons.append("policy_task_id_exact_match")
        elif query_task_numbers and doc_task_numbers and not (query_task_numbers & doc_task_numbers):
            policy_delta -= 180.0
            policy_reasons.append("policy_task_id_mismatch_demoted")
        elif (query_mentions_routing_family or query_mentions_memory_core) and is_task_artifact and doc_task_numbers and not doc_has_targeted_policy_task:
            policy_delta -= 280.0
            policy_reasons.append("policy_nontarget_decision_artifact_demoted")

        if is_memory_note and has_policy_markers:
            policy_delta += 40.0
            policy_reasons.append("policy_memory_note_support_only")
        elif is_memory_note and not has_policy_markers:
            policy_delta -= 260.0
            policy_reasons.append("policy_generic_memory_demoted")

        is_verification_wrapper = (
            "verification-task-" in document["workspace_path"]
            or document["workspace_path"].endswith(".json")
            or "regression-pack" in combined_norm
            or "compare-local" in combined_norm
            or "compare-psql" in combined_norm
            or "q1-psql" in combined_norm
            or "q2-psql" in combined_norm
            or "q3-psql" in combined_norm
            or "q4-psql" in combined_norm
            or "q5-psql" in combined_norm
        )

        if is_meta_eval_artifact and not has_policy_markers:
            policy_delta -= 140.0
            policy_reasons.append("policy_meta_artifact_soft_demoted")
        if is_verification_wrapper:
            policy_delta -= 520.0
            policy_reasons.append("policy_verification_wrapper_demoted")

        if policy_delta:
            score += policy_delta
            reasons.extend(policy_reasons)
    elif request_class == "preference_operating_style_recall":
        preference_signals = preference_recall_item_signals(
            query=query,
            document_path=document["workspace_path"],
            document_title=record.title,
            section_path=chunk.get("section_path", ""),
            excerpt=chunk.get("chunk_text", ""),
            source_key=document.get("source_key", ""),
        )
        preference_delta = 0.0
        preference_reasons: list[str] = []

        if preference_signals["is_memory_note"]:
            preference_delta += 120.0
            preference_reasons.append("preference_memory_note_bias")
        else:
            preference_delta -= 90.0
            preference_reasons.append("preference_non_memory_demoted")

        if preference_signals["has_explicit_preference_anchor"]:
            preference_delta += 340.0
            preference_reasons.append("preference_durable_anchor_match")

        if preference_signals["has_direct_rule_phrases"]:
            preference_delta += 220.0
            preference_reasons.append("preference_direct_rule_phrase_boost")

        if preference_signals["is_daily_memory_note"] and preference_signals["has_explicit_preference_anchor"]:
            preference_delta += 180.0
            preference_reasons.append("preference_daily_memory_anchor_boost")

        if preference_signals["title_or_path_preference_hint"] and preference_signals["has_explicit_preference_anchor"]:
            preference_delta += 110.0
            preference_reasons.append("preference_preferred_note_path_boost")

        if preference_signals["is_session_greeting_note"] and preference_signals["has_style_phrase"]:
            preference_delta += 90.0
            preference_reasons.append("preference_session_greeting_support")

        if preference_signals["asks_for_answer_style"] and preference_signals["has_style_phrase"]:
            preference_delta += 80.0
            preference_reasons.append("preference_style_phrase_match")

        if preference_signals["asks_for_answer_style"] and preference_signals["has_compact_style_pair"]:
            preference_delta += 70.0
            preference_reasons.append("preference_compact_style_pair_match")

        if preference_signals["query_mentions_yuriy"] and "юрий" in normalize_text(chunk.get("chunk_text", "")):
            preference_delta += 45.0
            preference_reasons.append("preference_operator_name_match")

        if preference_signals["is_daily_memory_note"] and not preference_signals["has_explicit_preference_anchor"]:
            preference_delta -= 150.0
            preference_reasons.append("preference_generic_daily_memory_demoted")

        if preference_signals["looks_like_artifact_or_transcript"] and not preference_signals["has_explicit_preference_anchor"]:
            preference_delta -= 180.0
            preference_reasons.append("preference_artifact_noise_demoted")

        if is_meta_eval_artifact:
            preference_delta -= 260.0
            preference_reasons.append("preference_meta_artifact_demoted")

        if preference_delta:
            score += preference_delta
            reasons.extend(preference_reasons)

    excerpt = build_excerpt(chunk.get("chunk_text", ""), query_tokens)
    return {
        "score": round(score, 3),
        "reasons": unique_preserve(reasons),
        "excerpt": excerpt,
    }


def apply_continuation_freshness_ranking(items: list[dict[str, Any]], query: str, classification: dict[str, Any]) -> list[dict[str, Any]]:
    if not items or str(classification.get("request_class", "")) != "resume_reopen_continuation":
        return items

    query_norm = normalize_text(query)
    query_task_numbers = extract_task_numbers(query)
    primary_task_ref = explicit_continuation_primary_task_ref(query, classification)
    query_date = extract_iso_date(query)
    query_date_ord = ymd_to_ordinal(query_date)
    memory_core_query = "memory core" in query_norm
    prefers_predecessor = continuation_query_prefers_predecessor(query)
    ambiguous_continuation_query = not query_task_numbers and memory_core_query and any(
        marker in query_norm for marker in ["handoff", "продолж", "continue", "resume", "reopen"]
    )

    adjusted: list[dict[str, Any]] = []
    for item in items:
        workspace_path = str(item.get("document", {}).get("workspace_path", ""))
        title = str(item.get("document", {}).get("title", ""))
        section_path = str(item.get("chunk", {}).get("section_path", ""))
        excerpt = str(item.get("excerpt", ""))
        combined = " ".join([workspace_path, title, section_path, excerpt])
        combined_norm = normalize_text(combined)
        item_task_numbers = extract_task_numbers(combined)
        item_date = extract_iso_date(workspace_path) or extract_iso_date(title) or extract_iso_date(excerpt)
        item_date_ord = ymd_to_ordinal(item_date)
        item_is_generic_timestamp_handoff = is_generic_timestamp_handoff_path(workspace_path, title)
        item_is_handoff_like = is_handoff_like_artifact(workspace_path, title)
        item_is_task_anchored_handoff = item_is_handoff_like and bool(item_task_numbers)
        item_is_verification_artifact = is_continuation_verification_artifact_path(workspace_path, title)

        delta = 0.0
        extra_reasons: list[str] = []

        if query_task_numbers and item_task_numbers:
            exact_matches = [number for number in item_task_numbers if number in query_task_numbers]
            if exact_matches:
                delta += 220.0 + (20.0 * len(exact_matches))
                extra_reasons.append("continuation_task_id_exact_match")
                if primary_task_ref is not None and primary_task_ref in item_task_numbers:
                    delta += 48.0
                    extra_reasons.append("continuation_primary_task_ref_boost")
                nearest_gap = 0
            else:
                nearest_gap = min(abs(item_number - query_number) for item_number in item_task_numbers for query_number in query_task_numbers)
                if nearest_gap <= 3:
                    delta += max(0.0, 130.0 - (nearest_gap * 28.0))
                    extra_reasons.append("continuation_task_id_near_predecessor")
                elif nearest_gap >= 25:
                    delta -= 55.0
                    extra_reasons.append("continuation_task_id_far_demoted")
        else:
            nearest_gap = None

        if memory_core_query and "memory core" in combined_norm:
            delta += 45.0
            extra_reasons.append("continuation_same_project_boost")
        elif memory_core_query and item_is_generic_timestamp_handoff:
            delta -= 120.0
            extra_reasons.append("continuation_projectless_generic_handoff_demoted")

        if prefers_predecessor:
            if item_is_task_anchored_handoff and query_task_numbers and any(number in query_task_numbers for number in item_task_numbers):
                delta += 120.0
                extra_reasons.append("continuation_immediate_predecessor_handoff_boost")
            elif item_is_generic_timestamp_handoff:
                delta -= 180.0
                extra_reasons.append("continuation_predecessor_generic_timestamp_demoted")

        if item_is_task_anchored_handoff and not item_is_verification_artifact:
            if workspace_path.startswith("task-manager/artifacts/"):
                delta += 95.0
                extra_reasons.append("continuation_task_scoped_artifact_handoff_boost")
            elif workspace_path.startswith("task-manager/handoffs/"):
                delta += 35.0
                extra_reasons.append("continuation_task_scoped_timestamp_handoff_boost")

        if not query_task_numbers and item_is_task_anchored_handoff and any(marker in combined_norm for marker in {
            "conflict/open-question synthesis",
            "conflict open question synthesis",
            "citation envelope",
            "authority priority",
            "routing policy",
        }):
            delta += 110.0
            extra_reasons.append("continuation_stage4_named_handoff_boost")
        if not query_task_numbers and item_is_task_anchored_handoff and "memory core" in combined_norm and not item_is_verification_artifact:
            delta += 240.0
            extra_reasons.append("continuation_ambiguous_memory_core_handoff_boost")

        if item_date_ord:
            if query_date_ord:
                day_gap = abs(item_date_ord - query_date_ord)
                if day_gap <= 2:
                    delta += max(0.0, 90.0 - (day_gap * 24.0))
                    extra_reasons.append("continuation_date_near_query")
                elif day_gap >= 10:
                    delta -= 25.0
                    extra_reasons.append("continuation_date_far_from_query")
            else:
                delta += min(36.0, max(0.0, (item_date_ord - 752000) / 25.0))
                extra_reasons.append("continuation_recency_boost")

        generic_handoff_markers = {
            "operator note",
            "what the next session should do first",
            "task #4",
            "watchdog",
            "triad production rerun",
            "human3 handoff",
        }
        if query_task_numbers and item_is_generic_timestamp_handoff and not any(number in query_task_numbers for number in item_task_numbers):
            delta -= 140.0
            extra_reasons.append("continuation_self_hit_generic_timestamp_handoff_demoted")
        elif ambiguous_continuation_query and item_is_generic_timestamp_handoff and "memory core" not in combined_norm:
            delta -= 90.0
            extra_reasons.append("continuation_ambiguous_self_hit_demoted")
        if not query_task_numbers and item_is_generic_timestamp_handoff:
            delta -= 95.0
            extra_reasons.append("continuation_unnumbered_generic_timestamp_handoff_demoted")
        if not query_task_numbers and item_is_verification_artifact:
            delta -= 260.0
            extra_reasons.append("continuation_unnumbered_verification_artifact_demoted")
        if not query_task_numbers and any(marker in combined_norm for marker in generic_handoff_markers):
            delta -= 28.0
            extra_reasons.append("continuation_generic_handoff_demoted")
        elif query_task_numbers and nearest_gap is not None and nearest_gap > 10 and any(marker in combined_norm for marker in generic_handoff_markers):
            delta -= 46.0
            extra_reasons.append("continuation_stale_generic_handoff_demoted")

        if item_is_verification_artifact and not is_explicit_meta_query(query, classification):
            delta -= 420.0 if prefers_predecessor or memory_core_query else 220.0
            extra_reasons.append("continuation_verification_artifact_demoted")

        if not is_explicit_meta_query(query, classification):
            if is_continuation_meta_artifact_path(workspace_path, title) and not item_is_handoff_like:
                if not query_task_numbers:
                    delta -= 320.0
                    extra_reasons.append("continuation_meta_artifact_demoted")
                else:
                    delta -= 180.0
                    extra_reasons.append("continuation_meta_artifact_soft_demoted")
            elif item_is_handoff_like and not item_is_verification_artifact:
                delta += 32.0
                extra_reasons.append("continuation_handoff_authority_boost")

        if delta:
            item["score"] = round(float(item.get("score", 0.0)) + delta, 3)
            item["match_reason"] = ", ".join(unique_preserve([*(item.get("match_reason", "").split(", ") if item.get("match_reason") else []), *extra_reasons]))
        adjusted.append(item)

    adjusted.sort(key=lambda item: (-float(item.get("score", 0.0)), str(item.get("document", {}).get("workspace_path", "")), int(item.get("chunk", {}).get("chunk_ordinal", 0))))
    return adjusted


def current_execution_query_signals(query: str) -> dict[str, Any]:
    query_norm = normalize_text(query)
    wants_now = any(marker in query_norm for marker in {
        "where are we now", "where are we at", "current status", "where do we stand", "status now",
        "где сейчас", "текущий статус", "где мы сейчас", "на каком этапе", "что уже готово", "что дальше", "что next",
    })
    wants_done = any(marker in query_norm for marker in {
        "already done", "what is done", "what's done", "completed", "ready", "готово", "уже сделано", "что уже готово",
    })
    wants_next = any(marker in query_norm for marker in {
        "what next", "next step", "next steps", "what should we do next", "what to do next",
        "что дальше", "следующий шаг", "следующие шаги", "что делать дальше",
    })
    mentions_handoff = any(marker in query_norm for marker in {
        "handoff", "current-state", "current state", "task state", "task-state", "run state",
        "handoff-first", "статус", "состояние", "передача", "хэндофф",
    })
    memory_core_query = "memory core" in query_norm
    mentions_stage_chain = any(marker in query_norm for marker in {
        "stage chain", "after stage", "post stage", "stage 4", "stage4", "stage 5", "stage5",
        "после stage", "после этапа", "stage chain", "по stage chain", "после stage 4", "после этапа 4",
    })
    query_task_numbers = extract_task_numbers(query)
    query_date = extract_iso_date(query)
    return {
        "query_norm": query_norm,
        "wants_now": wants_now,
        "wants_done": wants_done,
        "wants_next": wants_next,
        "mentions_handoff": mentions_handoff,
        "memory_core_query": memory_core_query,
        "mentions_stage_chain": mentions_stage_chain,
        "query_task_numbers": query_task_numbers,
        "query_date_ord": ymd_to_ordinal(query_date),
        "status_like": wants_now or wants_done or wants_next or mentions_handoff,
    }


def current_execution_shape_priority(item: dict[str, Any], query: str, classification: dict[str, Any]) -> int:
    if str(classification.get("request_class", "")) != "current_task_execution":
        return 9
    signals = current_execution_item_signals(item)
    if signals["is_task_state_like"] and signals["is_task_anchored"]:
        return 0
    if signals["is_handoff_like"] and signals["is_task_anchored"]:
        return 1
    if signals["is_handoff_like"]:
        return 2
    if signals["is_memory_status_note"]:
        return 3
    if signals["is_evidence_record"]:
        return 4
    if signals["is_memory_note"]:
        return 5
    return 6


def current_execution_item_signals(item: dict[str, Any]) -> dict[str, Any]:
    workspace_path = str(item.get("document", {}).get("workspace_path", ""))
    title = str(item.get("document", {}).get("title", ""))
    section_path = str(item.get("chunk", {}).get("section_path", ""))
    excerpt = str(item.get("excerpt", ""))
    document_identity_norm = normalize_text(" ".join([workspace_path, title]))
    combined_norm = normalize_text(" ".join([workspace_path, title, section_path, excerpt]))
    authority = str(item.get("authority", {}).get("layer", ""))
    document_task_numbers = extract_task_numbers(document_identity_norm)
    item_task_numbers = extract_task_numbers(combined_norm)
    item_date_ord = ymd_to_ordinal(extract_iso_date(workspace_path) or extract_iso_date(title) or extract_iso_date(excerpt))
    handoff_markers = {
        "handoff", "next session", "current state", "current-state", "task state", "task-state",
        "status", "next step", "what landed", "close-ready", "close ready", "done", "remaining", "next",
        "итог", "статус", "готово", "что landed", "что дальше", "verdict", "bounded verdict", "partial-success", "pass", "fail",
    }
    memory_status_markers = {
        "status", "итог", "what landed", "next step", "next steps", "verdict = done", "close-ready", "close ready",
        "done", "готово", "already", "следующий", "дальше",
    }
    stage_chain_markers = {
        "stage 4", "stage4", "stage 5", "stage5", "routing policy", "authority priority",
        "citation envelope", "conflict open question", "conflict/open-question", "close-ready", "what landed",
    }
    status_noise_markers = {
        "noise suppression", "anti-wrapper", "closeout", "runtime boundary map",
        "policy synthesis", "bounded slice", "rerun note", "reconciliation",
    }
    is_handoff_like = is_handoff_like_artifact(workspace_path, title)
    is_status_noise_wrapper = workspace_path.startswith("task-manager/artifacts/") and any(marker in combined_norm for marker in status_noise_markers)
    is_task_state_like = (
        workspace_path.startswith("task-manager/artifacts/")
        and any(marker in combined_norm for marker in handoff_markers)
        and not is_status_noise_wrapper
    ) or (
        authority == "task_state"
        and any(marker in combined_norm for marker in handoff_markers)
        and not is_status_noise_wrapper
    )
    is_memory_status_note = authority == "memory_note" and any(marker in combined_norm for marker in memory_status_markers)
    is_memory_note = authority == "memory_note"
    is_evidence_record = authority == "evidence_record"
    is_task_anchored = bool(item_task_numbers)
    is_generic_timestamp_handoff = is_generic_timestamp_handoff_path(workspace_path, title)
    is_meta_eval = is_meta_eval_artifact_path(workspace_path, title)
    is_verification_artifact = (
        workspace_path.startswith("task-manager/artifacts/verification-")
        or "/verification-" in workspace_path
        or workspace_path.endswith(".run.json")
    )
    is_self_referential_verdict_note = (
        workspace_path.startswith("task-manager/notes/")
        and any(marker in combined_norm for marker in {"verdict", "bounded fix applied", "verifier drift", "verifier sync"})
    )
    is_memory_core_handoff_chain = (
        workspace_path.startswith("task-manager/artifacts/task-36")
        and "memory core v1" in combined_norm
        and any(marker in combined_norm for marker in stage_chain_markers)
    )
    return {
        "workspace_path": workspace_path,
        "title": title,
        "combined_norm": combined_norm,
        "authority": authority,
        "document_task_numbers": document_task_numbers,
        "item_task_numbers": item_task_numbers,
        "item_date_ord": item_date_ord,
        "is_handoff_like": is_handoff_like,
        "is_status_noise_wrapper": is_status_noise_wrapper,
        "is_task_state_like": is_task_state_like,
        "is_memory_status_note": is_memory_status_note,
        "is_memory_note": is_memory_note,
        "is_evidence_record": is_evidence_record,
        "is_task_anchored": is_task_anchored,
        "is_generic_timestamp_handoff": is_generic_timestamp_handoff,
        "is_meta_eval": is_meta_eval,
        "is_verification_artifact": is_verification_artifact,
        "is_self_referential_verdict_note": is_self_referential_verdict_note,
        "is_memory_core_handoff_chain": is_memory_core_handoff_chain,
    }


def apply_current_execution_freshness_ranking(items: list[dict[str, Any]], query: str, classification: dict[str, Any]) -> list[dict[str, Any]]:
    if not items or str(classification.get("request_class", "")) != "current_task_execution":
        return items

    query_signals = current_execution_query_signals(query)
    adjusted: list[dict[str, Any]] = []
    for item in items:
        signals = current_execution_item_signals(item)
        delta = 0.0
        extra_reasons: list[str] = []

        if signals["is_task_state_like"] and signals["is_task_anchored"]:
            delta += 260.0
            extra_reasons.append("current_execution_task_state_handoff_boost")
        elif signals["is_handoff_like"] and signals["is_task_anchored"]:
            delta += 220.0
            extra_reasons.append("current_execution_task_anchored_handoff_boost")
        elif signals["is_handoff_like"]:
            delta += 125.0
            extra_reasons.append("current_execution_handoff_boost")
        elif signals["is_memory_status_note"]:
            delta += 40.0
            extra_reasons.append("current_execution_memory_status_support")

        if query_signals["memory_core_query"] and "memory core" in signals["combined_norm"]:
            delta += 70.0
            extra_reasons.append("current_execution_same_project_boost")

        if query_signals["memory_core_query"] and query_signals["mentions_stage_chain"] and signals["is_memory_core_handoff_chain"]:
            delta += 320.0
            extra_reasons.append("current_execution_stage_chain_handoff_preferred")

        if query_signals["query_task_numbers"] and signals["item_task_numbers"]:
            exact_matches = [number for number in signals["item_task_numbers"] if number in query_signals["query_task_numbers"]]
            document_exact_matches = [number for number in signals["document_task_numbers"] if number in query_signals["query_task_numbers"]]
            if exact_matches:
                delta += 260.0 + (24.0 * len(exact_matches))
                extra_reasons.append("current_execution_task_id_exact_match")
                if document_exact_matches:
                    delta += 230.0 + (18.0 * len(document_exact_matches))
                    extra_reasons.append("current_execution_doc_level_task_id_exact_match")
                elif query_signals["wants_now"] or query_signals["wants_done"] or query_signals["wants_next"]:
                    delta -= 360.0
                    extra_reasons.append("current_execution_chunk_only_task_mention_demoted")
            else:
                nearest_gap = min(abs(item_number - query_number) for item_number in signals["item_task_numbers"] for query_number in query_signals["query_task_numbers"])
                if nearest_gap <= 1:
                    delta -= 120.0
                    extra_reasons.append("current_execution_task_id_adjacent_demoted")
                elif nearest_gap <= 3:
                    delta -= 170.0
                    extra_reasons.append("current_execution_task_id_nearby_demoted")
                elif nearest_gap >= 25:
                    delta -= 220.0
                    extra_reasons.append("current_execution_task_id_far_demoted")
                else:
                    delta -= 160.0
                    extra_reasons.append("current_execution_task_id_mismatch_demoted")

        elif query_signals["query_task_numbers"] and signals["is_task_anchored"]:
            delta -= 170.0
            extra_reasons.append("current_execution_missing_exact_task_id_demoted")

        if query_signals["wants_now"] or query_signals["wants_done"] or query_signals["wants_next"]:
            if signals["is_memory_note"] and not signals["is_memory_status_note"]:
                delta -= 150.0
                extra_reasons.append("current_execution_generic_memory_demoted")
            if signals["is_status_noise_wrapper"]:
                delta -= 420.0 if (query_signals["wants_done"] or query_signals["wants_next"]) else 320.0
                extra_reasons.append("current_execution_status_noise_wrapper_demoted")
            if signals["is_evidence_record"] and not (signals["is_handoff_like"] or signals["is_task_state_like"] or signals["is_memory_core_handoff_chain"]):
                delta -= 110.0
                extra_reasons.append("current_execution_generic_artifact_demoted")
            if query_signals["query_task_numbers"] and signals["document_task_numbers"] and not any(number in query_signals["query_task_numbers"] for number in signals["document_task_numbers"]):
                delta -= 320.0 if (query_signals["wants_done"] or query_signals["wants_next"]) else 180.0
                extra_reasons.append("current_execution_doc_level_task_mismatch_demoted")
            if query_signals["query_task_numbers"] and signals["document_task_numbers"] and any(number in query_signals["query_task_numbers"] for number in signals["document_task_numbers"]) and not (signals["is_handoff_like"] or signals["is_task_state_like"] or signals["is_memory_core_handoff_chain"]):
                delta -= 260.0 if (query_signals["wants_done"] or query_signals["wants_next"]) else 180.0
                extra_reasons.append("current_execution_exact_task_nonstatus_doc_demoted")

        if query_signals["status_like"] and query_signals["mentions_stage_chain"] and signals["is_memory_note"] and not signals["is_memory_status_note"]:
            delta -= 110.0
            extra_reasons.append("current_execution_history_over_current_state_demoted")

        if signals["is_generic_timestamp_handoff"] and not signals["is_task_anchored"]:
            delta -= 95.0
            extra_reasons.append("current_execution_generic_timestamp_handoff_demoted")

        if signals["is_meta_eval"] and not is_explicit_meta_query(query, classification):
            delta -= 240.0
            extra_reasons.append("current_execution_meta_artifact_demoted")

        if query_signals["query_task_numbers"] and signals["is_verification_artifact"]:
            delta -= 420.0 if (query_signals["wants_done"] or query_signals["wants_next"]) else 320.0
            extra_reasons.append("current_execution_verification_artifact_demoted")

        if query_signals["query_task_numbers"] and signals["is_self_referential_verdict_note"]:
            delta -= 260.0
            extra_reasons.append("current_execution_self_verdict_note_demoted")

        if signals["item_date_ord"]:
            if query_signals["query_date_ord"]:
                day_gap = abs(signals["item_date_ord"] - query_signals["query_date_ord"])
                if day_gap <= 2:
                    delta += max(0.0, 80.0 - (day_gap * 24.0))
                    extra_reasons.append("current_execution_date_near_query")
                elif day_gap >= 10:
                    delta -= 20.0
                    extra_reasons.append("current_execution_date_far_from_query")
            else:
                delta += min(42.0, max(0.0, (signals["item_date_ord"] - 752000) / 22.0))
                extra_reasons.append("current_execution_recency_boost")

        if delta:
            item["score"] = round(float(item.get("score", 0.0)) + delta, 3)
            item["match_reason"] = ", ".join(unique_preserve([*(item.get("match_reason", "").split(", ") if item.get("match_reason") else []), *extra_reasons]))
        adjusted.append(item)

    adjusted.sort(key=lambda item: (-float(item.get("score", 0.0)), str(item.get("document", {}).get("workspace_path", "")), int(item.get("chunk", {}).get("chunk_ordinal", 0))))
    return adjusted


def build_excerpt(text: str, query_tokens: list[str], window: int = 320) -> str:
    compact = " ".join(text.split())
    if not compact:
        return ""
    lower = compact.lower()
    best_index = -1
    for token in query_tokens:
        idx = lower.find(token.lower())
        if idx != -1 and (best_index == -1 or idx < best_index):
            best_index = idx
    if best_index == -1:
        return compact[:window]
    start = max(0, best_index - window // 3)
    end = min(len(compact), start + window)
    snippet = compact[start:end]
    if start > 0:
        snippet = "…" + snippet
    if end < len(compact):
        snippet = snippet + "…"
    return snippet


def unique_preserve(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def apply_stage4_audit_score_boosts(items: list[dict[str, Any]], query: str, classification: dict[str, Any]) -> list[dict[str, Any]]:
    if not items or not is_stage4_audit_trace_query(query, classification):
        return items

    requested_component_task_ids = stage4_audit_component_task_ids(query)
    if not requested_component_task_ids:
        return items

    adjusted: list[dict[str, Any]] = []
    for item in items:
        signals = stage4_audit_item_signals(item)
        doc_task_numbers = set(signals["doc_task_numbers"])
        item_task_numbers = set(signals["item_task_numbers"])
        aligned_requested_component_ids = requested_component_task_ids & set(signals["component_alignment_task_ids"])
        is_wrapper = bool(signals["is_wrapper"])

        delta = 0.0
        extra_reasons: list[str] = []
        if aligned_requested_component_ids:
            delta += 520.0 + (80.0 * len(aligned_requested_component_ids))
            extra_reasons.append("stage4_component_task_alignment")
        elif requested_component_task_ids & doc_task_numbers and not is_wrapper:
            delta += 260.0 + (40.0 * len(requested_component_task_ids & doc_task_numbers))
            extra_reasons.append("stage4_component_task_doc_match")
        elif requested_component_task_ids & item_task_numbers and not is_wrapper:
            delta += 110.0
            extra_reasons.append("stage4_component_task_chunk_match")

        if requested_component_task_ids.issubset(doc_task_numbers) and not is_wrapper:
            delta += 220.0
            extra_reasons.append("stage4_full_component_cover")

        if is_wrapper:
            delta -= 280.0
            extra_reasons.append("stage4_wrapper_penalty")
        if bool(signals.get("is_noise_path")) and not signals["proving_doc_match_count"]:
            delta -= 320.0
            extra_reasons.append("stage4_noise_path_penalty")

        if delta:
            item["score"] = round(float(item.get("score", 0.0)) + delta, 3)
            item["match_reason"] = ", ".join(unique_preserve([*(item.get("match_reason", "").split(", ") if item.get("match_reason") else []), *extra_reasons]))
        adjusted.append(item)

    adjusted.sort(key=lambda item: (-float(item.get("score", 0.0)), str(item.get("document", {}).get("workspace_path", "")), int(item.get("chunk", {}).get("chunk_ordinal", 0))))
    return adjusted


def apply_document_diversity_shaping(items: list[dict[str, Any]], max_items: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not items:
        return items, {
            "applied": False,
            "reason": "no_items",
            "duplicate_documents_in_topn_before": 0,
            "duplicate_documents_in_topn_after": 0,
            "topn_before": [],
            "topn_after": [],
        }

    topn_before = [str(item.get("document", {}).get("workspace_path", "")) for item in items[:max_items]]
    duplicate_documents_in_topn_before = sum(max(0, count - 1) for count in Counter(topn_before).values())
    if duplicate_documents_in_topn_before == 0:
        return items, {
            "applied": False,
            "reason": "already_diverse",
            "duplicate_documents_in_topn_before": 0,
            "duplicate_documents_in_topn_after": 0,
            "topn_before": topn_before,
            "topn_after": topn_before,
        }

    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    order: list[str] = []
    for item in items:
        workspace_path = str(item.get("document", {}).get("workspace_path", ""))
        if workspace_path not in groups:
            order.append(workspace_path)
        groups[workspace_path].append(item)

    shaped: list[dict[str, Any]] = []
    for workspace_path in order:
        queue = groups[workspace_path]
        if queue:
            shaped.append(queue.pop(0))

    while len(shaped) < len(items):
        progressed = False
        for workspace_path in order:
            queue = groups[workspace_path]
            if not queue:
                continue
            shaped.append(queue.pop(0))
            progressed = True
        if not progressed:
            break

    topn_after = [str(item.get("document", {}).get("workspace_path", "")) for item in shaped[:max_items]]
    duplicate_documents_in_topn_after = sum(max(0, count - 1) for count in Counter(topn_after).values())
    return shaped, {
        "applied": True,
        "reason": "round_robin_by_document_after_authority_ranking",
        "duplicate_documents_in_topn_before": duplicate_documents_in_topn_before,
        "duplicate_documents_in_topn_after": duplicate_documents_in_topn_after,
        "topn_before": topn_before,
        "topn_after": topn_after,
    }


def parse_authority_priority_focus(text: str) -> list[str]:
    raw_parts = [part.strip() for part in str(text or "").split(">")]
    result: list[str] = []
    for part in raw_parts:
        composite = COMPOSITE_AUTHORITY_PARTS.get(part)
        if composite:
            for alias in composite:
                if alias not in result:
                    result.append(alias)
            continue
        alias = AUTHORITY_ALIASES.get(part)
        if alias and alias not in result:
            result.append(alias)
    if "retrieval_document" not in result:
        result.append("retrieval_document")
    return result


def lane_allows_typed_authority(request_class: str, authority: str) -> bool:
    allowed = LANE_ALLOWED_TYPED_AUTHORITIES.get(request_class, set())
    return authority in allowed


def infer_typed_scope_refs(item: dict[str, Any]) -> set[str]:
    values = [
        str(item.get("document", {}).get("workspace_path", "")),
        str(item.get("document", {}).get("title", "")),
        str(item.get("chunk", {}).get("section_path", "")),
        str(item.get("excerpt", "")),
    ]
    normalized = normalize_text(" ".join(values))
    refs: set[str] = set()
    for match in re.findall(r"task[-\s#]*(\d{1,5})", normalized):
        refs.add(f"task-{match}")
    return refs


def typed_candidate_eligibility(item: dict[str, Any], authority: str, classification: dict[str, Any], query: str = "") -> dict[str, Any]:
    request_class = str((classification or {}).get("request_class", ""))
    if authority not in TYPED_AUTHORITY_LAYERS:
        return {
            "is_typed_candidate": False,
            "eligible": False,
            "reasons": ["not_typed_candidate"],
            "typed_authority": authority,
            "lane": request_class,
        }

    reasons: list[str] = []
    eligible = True
    normalized = normalize_text(
        " ".join([
            str(item.get("document", {}).get("workspace_path", "")),
            str(item.get("document", {}).get("title", "")),
            str(item.get("chunk", {}).get("section_path", "")),
            str(item.get("excerpt", "")),
        ])
    )

    if not lane_allows_typed_authority(request_class, authority):
        eligible = False
        reasons.append("lane_disallows_typed_authority")

    stale_markers = {"stale", "superseded", "expired", "archived", "deprecated", "obsolete"}
    matched_stale_markers = [marker for marker in stale_markers if marker in normalized]
    if matched_stale_markers:
        eligible = False
        reasons.append("stale_or_superseded_markers_detected")

    has_provenance_anchor = bool(item.get("provenance", {}).get("source_locator")) and bool(item.get("provenance", {}).get("chunk_locator"))
    if not has_provenance_anchor:
        eligible = False
        reasons.append("missing_provenance_anchor")

    scope_refs = infer_typed_scope_refs(item)
    query_scope_refs = set(f"task-{match}" for match in re.findall(r"task[-\s#]*(\d{1,5})", normalize_text(query)))
    if authority == "session_capsule" and not query_scope_refs:
        eligible = False
        reasons.append("session_capsule_requires_explicit_scope")
    elif authority == "session_capsule" and scope_refs and query_scope_refs and scope_refs.isdisjoint(query_scope_refs):
        eligible = False
        reasons.append("session_capsule_scope_mismatch")
    elif request_class in {"resume_reopen_continuation", "current_task_execution"} and query_scope_refs and scope_refs and scope_refs.isdisjoint(query_scope_refs):
        eligible = False
        reasons.append("typed_scope_mismatch")

    if eligible:
        reasons.append("typed_lane_eligible")

    return {
        "is_typed_candidate": True,
        "eligible": eligible,
        "reasons": reasons,
        "typed_authority": authority,
        "lane": request_class,
        "scope_refs": sorted(scope_refs),
        "query_scope_refs": sorted(query_scope_refs),
        "has_provenance_anchor": has_provenance_anchor,
        "matched_stale_markers": matched_stale_markers,
    }


def apply_typed_serving_precedence(items: list[dict[str, Any]], classification: dict[str, Any], query: str = "") -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not items:
        return items, {
            "typed_serving": {
                "applied": False,
                "reason": "no_items",
            }
        }

    annotated: list[dict[str, Any]] = []
    typed_trace: list[dict[str, Any]] = []
    for item in items:
        authority = str(item.get("authority", {}).get("layer", ""))
        eligibility = typed_candidate_eligibility(item, authority, classification, query=query)
        item.setdefault("authority", {})["typed_candidate"] = eligibility.get("is_typed_candidate", False)
        item["authority"]["typed_eligible"] = eligibility.get("eligible", False)
        item["authority"]["typed_eligibility_reasons"] = list(eligibility.get("reasons", []))
        item["authority"]["typed_scope_refs"] = list(eligibility.get("scope_refs", []))
        annotated.append(item)
        if eligibility.get("is_typed_candidate"):
            typed_trace.append({
                "path": str(item.get("document", {}).get("workspace_path", "")),
                "authority": authority,
                "eligible": bool(eligibility.get("eligible")),
                "reasons": list(eligibility.get("reasons", [])),
            })

    request_class = str((classification or {}).get("request_class", ""))

    def typed_precedence_bucket(item: dict[str, Any]) -> int:
        authority = str(item.get("authority", {}).get("layer", ""))
        typed_eligible = bool(item.get("authority", {}).get("typed_eligible"))
        typed_candidate = bool(item.get("authority", {}).get("typed_candidate"))

        if request_class == "resume_reopen_continuation" and authority in {"canonical_handoff", "task_state"}:
            return 0
        if typed_eligible:
            return 1
        if request_class == "resume_reopen_continuation" and authority == "evidence_record":
            return 2
        if typed_candidate and lane_allows_typed_authority(request_class, authority):
            return 3
        return 4

    reordered = sorted(
        annotated,
        key=lambda item: (
            typed_precedence_bucket(item),
            item.get("authority", {}).get("priority_index", 999),
            lane_basis_priority(item, query, classification),
            item.get("authority", {}).get("current_execution_shape_priority", 9),
            stage4_trace_priority(item, query, classification),
            meta_eval_subfamily_priority(item, query, classification),
            item.get("authority", {}).get("continuation_shape_priority", 9),
            -float(item.get("score", 0.0)),
            str(item.get("document", {}).get("workspace_path", "")),
            int(item.get("chunk", {}).get("chunk_ordinal", 0)),
        )
    )

    return reordered, {
        "typed_serving": {
            "applied": True,
            "lane": str((classification or {}).get("request_class", "")),
            "eligible_typed_count": sum(1 for item in reordered if item.get("authority", {}).get("typed_eligible")),
            "ineligible_typed_count": sum(1 for item in reordered if item.get("authority", {}).get("typed_candidate") and not item.get("authority", {}).get("typed_eligible")),
            "trace": typed_trace[:8],
        }
    }


def infer_item_authority(item: dict[str, Any], source_tags: set[str], classification: dict[str, Any] | None = None, query: str = "") -> str:
    source_key = str(item.get("source", {}).get("key", ""))
    workspace_path = str(item.get("document", {}).get("workspace_path", "")).lower()
    title = str(item.get("document", {}).get("title", ""))
    normalized_identity = normalize_text(f"{workspace_path} {title}")
    item_is_handoff_like = is_handoff_like_artifact(workspace_path, title)
    item_is_task_anchored_handoff = item_is_handoff_like and bool(extract_task_numbers(normalized_identity))
    item_is_memory_handoff = workspace_path.startswith("memory/") and "handoff" in normalized_identity

    request_class = str((classification or {}).get("request_class", ""))
    if item_is_memory_handoff and request_class not in {"resume_reopen_continuation", "current_task_execution"}:
        return "memory_note"

    lane_blocks_canonical_handoff = request_class in {"meta_evaluation_recall", "architecture_design_recall"}
    item_is_verification_wrapper = "verification-task-" in workspace_path or "regression-pack" in workspace_path
    item_is_non_task_handoff = item_is_handoff_like and not item_is_task_anchored_handoff

    if request_class == "meta_evaluation_recall":
        if item_is_verification_wrapper:
            if any(tag in source_tags for tag in {"memory_note", "task-scoped memory notes", "verified preference notes"}) or source_key == "openclaw_shared_memory":
                return "memory_note"
            if "wiki/" in workspace_path or workspace_path.startswith("wiki/"):
                return "wiki_page"
            return "retrieval_document"
        if item_is_handoff_like:
            return "canonical_handoff"
        if source_key == "task_manager_artifacts" and is_meta_eval_artifact_path(workspace_path, title):
            return "evidence_record"

    if lane_blocks_canonical_handoff and (item_is_verification_wrapper or item_is_non_task_handoff):
        if any(tag in source_tags for tag in {"memory_note", "task-scoped memory notes", "verified preference notes"}) or source_key == "openclaw_shared_memory":
            return "memory_note"
        if "wiki/" in workspace_path or workspace_path.startswith("wiki/"):
            return "wiki_page"
        if "evidence_record" in source_tags or source_key == "task_manager_artifacts":
            return "evidence_record"
        if "wiki_page" in source_tags:
            return "wiki_page"
        return "retrieval_document"

    query_scope_refs = set(f"task-{match}" for match in re.findall(r"task[-\s#]*(\d{1,5})", normalize_text(query)))
    item_scope_refs = set(f"task-{match}" for match in extract_task_numbers(normalized_identity))

    if item_is_task_anchored_handoff:
        if request_class == "artifact_source_trace_request":
            query_norm = normalize_text(query)
            asks_for_handoff = any(marker in query_norm for marker in {"handoff", "artifact", "артеф", "artifact path", "handoff path"})
            if asks_for_handoff and query_scope_refs and (query_scope_refs & item_scope_refs):
                return "canonical_handoff"
        return "canonical_handoff"
    if request_class == "meta_evaluation_recall" and is_expected_meta_evidence_doc(workspace_path, title):
        return "evidence_record"
    if request_class == "architecture_design_recall" and is_canonical_architecture_doc(workspace_path, title):
        return "evidence_record"
    if request_class == "artifact_source_trace_request" and source_key == "task_manager_artifacts":
        return "evidence_record"
    if any(tag in source_tags for tag in {"task-manager state", "fresh task state"}) and any(
        marker in normalized_identity for marker in {"status", "handoff", "current state", "task state", "next step", "close-ready", "what landed", "итог", "статус", "готово"}
    ):
        return "task_state"
    if "canonical handoff" in source_tags or source_key == "task_manager_handoffs" or item_is_handoff_like:
        return "canonical_handoff"
    if any(tag in source_tags for tag in {"memory_note", "task-scoped memory notes", "verified preference notes"}) or source_key == "openclaw_shared_memory":
        return "memory_note"
    if "wiki/" in workspace_path or workspace_path.startswith("wiki/"):
        return "wiki_page"
    if "evidence_record" in source_tags or source_key == "task_manager_artifacts":
        return "evidence_record"
    if "wiki_page" in source_tags:
        return "wiki_page"
    return "retrieval_document"


def apply_authority_priority(items: list[dict[str, Any]], classification: dict[str, Any], routing: dict[str, Any] | None = None, query: str = "") -> tuple[list[dict[str, Any]], dict[str, Any]]:
    authority_order = parse_authority_priority_focus(str(classification.get("authority_priority_focus", "")))
    request_class = str(classification.get("request_class", ""))
    if request_class == "resume_reopen_continuation":
        continuation_order = ["canonical_handoff", "task_state", "evidence_record", "wiki_page", "retrieval_document", "memory_note", "session_capsule"]
        authority_order = unique_preserve([*continuation_order, *authority_order])
    elif request_class == "current_task_execution":
        current_execution_order = ["task_state", "canonical_handoff", "memory_note", "wiki_page", "evidence_record", "retrieval_document", "session_capsule"]
        authority_order = unique_preserve([*current_execution_order, *authority_order])
    elif request_class == "meta_evaluation_recall":
        authority_order = unique_preserve(["evidence_record", "canonical_handoff", "memory_note", "wiki_page", "retrieval_document", *authority_order])
    elif request_class == "architecture_design_recall":
        authority_order = unique_preserve(["evidence_record", "memory_note", "wiki_page", "canonical_handoff", "retrieval_document", *authority_order])
    elif request_class == "artifact_source_trace_request":
        query_norm = normalize_text(query)
        query_scope_refs = set(f"task-{match}" for match in re.findall(r"task[-\s#]*(\d{1,5})", query_norm))
        asks_for_handoff = any(marker in query_norm for marker in {"handoff", "artifact", "артеф", "artifact path", "handoff path"})
        if query_scope_refs and asks_for_handoff:
            authority_order = unique_preserve(["canonical_handoff", "evidence_record", "task_state", "retrieval_document", *authority_order])
    elif detect_targeted_history_assisted_continuation_anchor(query, classification):
        authority_order = unique_preserve(["canonical_handoff", "task_state", "evidence_record", "retrieval_document", "wiki_page", "memory_note", *authority_order])
    elif is_stage4_audit_trace_query(query, classification):
        authority_order = unique_preserve(["canonical_handoff", "evidence_record", "retrieval_document", *authority_order])
    elif request_class == "policy_decision_lookup":
        authority_order = unique_preserve(["evidence_record", "canonical_handoff", "memory_note", "wiki_page", "retrieval_document", *authority_order])
    elif request_class == "preference_operating_style_recall":
        authority_order = unique_preserve(["memory_note", "evidence_record", "retrieval_document", *authority_order])
    authority_rank = {name: idx for idx, name in enumerate(authority_order)}
    authority_counts: dict[str, int] = defaultdict(int)
    baseline_order = [str(item.get("document", {}).get("workspace_path", "")) for item in items]

    annotated: list[dict[str, Any]] = []
    for item in items:
        source_key = str(item.get("source", {}).get("key", ""))
        source_tags = set()
        if routing:
            source_tags = set((routing.get("source_domain_tags", {}) or {}).get(source_key, []))
        authority = infer_item_authority(item, source_tags, classification, query=query)
        authority_index = authority_rank.get(authority, len(authority_order))
        authority_counts[authority] += 1
        item["authority"] = {
            "layer": authority,
            "priority_index": authority_index,
            "matched_from": sorted(source_tags) if source_tags else ["retrieval_document"],
            "focus_order": authority_order,
        }
        item["authority"]["continuation_shape_priority"] = continuation_shape_priority(item, query, classification)
        item["authority"]["current_execution_shape_priority"] = current_execution_shape_priority(item, query, classification)
        annotated.append(item)

    annotated.sort(
        key=lambda item: (
            item.get("authority", {}).get("priority_index", len(authority_order)),
            lane_basis_priority(item, query, classification),
            item.get("authority", {}).get("current_execution_shape_priority", 9),
            stage4_trace_priority(item, query, classification),
            meta_eval_subfamily_priority(item, query, classification),
            item.get("authority", {}).get("continuation_shape_priority", 9),
            -float(item.get("score", 0.0)),
            str(item.get("document", {}).get("workspace_path", "")),
            int(item.get("chunk", {}).get("chunk_ordinal", 0)),
        )
    )
    typed_precedence_ranked, typed_pack = apply_typed_serving_precedence(annotated, classification, query=query)
    reordered = [str(item.get("document", {}).get("workspace_path", "")) for item in typed_precedence_ranked]
    return typed_precedence_ranked, {
        "authority_priority_focus": str(classification.get("authority_priority_focus", "")),
        "authority_order": authority_order,
        "applied": True,
        "counts_by_layer": dict(sorted(authority_counts.items(), key=lambda pair: pair[0])),
        "changed_order": baseline_order != reordered,
        "baseline_top_paths": baseline_order[: min(5, len(baseline_order))],
        "final_top_paths": reordered[: min(5, len(reordered))],
        "meta_eval_source_normalized": request_class == "meta_evaluation_recall" or (request_class == "architecture_design_recall" and is_explicit_meta_eval_query(query, classification)),
        "meta_subfamily": classification.get("meta_subfamily") if request_class == "meta_evaluation_recall" else None,
        "canonical_continuation_shape": "task_anchored_artifact_handoff" if request_class == "resume_reopen_continuation" else "n/a",
        "stage4_trace_boost_active": request_class == "artifact_source_trace_request" and ("stage 4" in normalize_text(query) or "stage4" in normalize_text(query)),
        "history_assisted_continuation_anchor": detect_targeted_history_assisted_continuation_anchor(query, classification) or None,
        **typed_pack,
    }


def build_summary(query: str, items: list[dict[str, Any]]) -> str:
    if not items:
        return f"По запросу '{query}' в доступном retrieval state ничего релевантного не найдено."

    source_counts: dict[str, int] = defaultdict(int)
    titles: list[str] = []
    signals: list[str] = []
    seen_titles: set[str] = set()
    for item in items[:4]:
        source_counts[item["source"]["key"]] += 1
        title = item["document"]["title"]
        if title not in seen_titles:
            seen_titles.add(title)
            titles.append(title)
        signals.extend(item["match_reason"].split(", "))

    top_sources = ", ".join(f"{key}×{count}" for key, count in sorted(source_counts.items(), key=lambda pair: (-pair[1], pair[0]))) or "(не указано)"
    signal_counts = Counter(signals)
    top_signals = ", ".join(name for name, _count in signal_counts.most_common(3)) or "lexical_match"
    joined_titles = "; ".join(titles[:3]) or "(не указано)"
    return (
        f"Найдено {len(items)} bounded evidence items по запросу '{query}'. "
        f"Это top-{len(items)} после ранжирования и дедупликации. "
        f"Доминирующие источники: {top_sources}. "
        f"Основные сигналы матчинга: {top_signals}. "
        f"Верхние документы: {joined_titles}."
    )


def build_locators(title: str, workspace_path: str, section_path: str, chunk_ordinal: int | None = None) -> dict[str, str]:
    section_label = section_path or "(root)"
    chunk_suffix = f"#chunk-{chunk_ordinal}" if chunk_ordinal is not None else ""
    return {
        "document_locator": f"{title} ({workspace_path})",
        "source_locator": workspace_path,
        "chunk_locator": f"{workspace_path}::{section_label}{chunk_suffix}",
    }



def ensure_psql_env(env_file: Path) -> dict[str, str]:
    env = load_env_file(env_file)
    required = ["PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD"]
    missing = [name for name in required if not env.get(name)]
    if missing:
        raise RuntimeError(f"Missing PostgreSQL env vars: {', '.join(missing)}")
    return env


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def build_source_key_case(selected_sources: list[dict[str, Any]]) -> str:
    clauses: list[str] = []
    for source in selected_sources:
        key = str(source.get("key", "")).strip()
        if not key:
            continue
        clauses.append(f"WHEN s.config_json ->> 'key' = {sql_quote(key)} THEN {sql_quote(key)}")
    return "CASE " + " ".join(clauses) + " ELSE coalesce(s.config_json ->> 'key', s.root_path, s.source_id) END"


def stage4_psql_row_delta(row: dict[str, Any], query: str, classification: dict[str, Any]) -> tuple[float, list[str]]:
    if not is_stage4_audit_trace_query(query, classification):
        return 0.0, []

    pseudo_item = {
        "document": {
            "workspace_path": str(Path(str(row.get("root_path", ""))) / str(row.get("path", ""))),
            "title": str(row.get("title", "")),
        },
        "chunk": {
            "section_path": str(row.get("section_path", "")),
        },
        "excerpt": str(row.get("chunk_text", "")),
    }
    signals = stage4_audit_item_signals(pseudo_item)
    requested_component_task_ids = stage4_audit_component_task_ids(query)
    if not requested_component_task_ids:
        return 0.0, []

    doc_task_numbers = set(signals["doc_task_numbers"])
    item_task_numbers = set(signals["item_task_numbers"])
    aligned_requested_component_ids = requested_component_task_ids & set(signals["component_alignment_task_ids"])
    is_wrapper = bool(signals["is_wrapper"])

    delta = 0.0
    reasons: list[str] = []
    if aligned_requested_component_ids:
        delta += 780.0 + (115.0 * len(aligned_requested_component_ids))
        reasons.append("stage4_component_task_alignment")
    elif requested_component_task_ids & doc_task_numbers and not is_wrapper:
        delta += 400.0 + (60.0 * len(requested_component_task_ids & doc_task_numbers))
        reasons.append("stage4_component_task_doc_match")
    elif requested_component_task_ids & item_task_numbers and not is_wrapper:
        delta += 185.0
        reasons.append("stage4_component_task_chunk_match")

    if requested_component_task_ids.issubset(doc_task_numbers) and not is_wrapper:
        delta += 330.0
        reasons.append("stage4_full_component_cover")

    if is_wrapper:
        delta -= 520.0
        reasons.append("stage4_wrapper_penalty")
    if bool(signals.get("is_noise_path")) and not signals["proving_doc_match_count"]:
        delta -= 420.0
        reasons.append("stage4_noise_path_penalty")

    return delta, reasons


def build_reasons(row: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if row.get("query_task_exact_match"):
        reasons.append("continuation_task_id_exact_match")
    if row.get("memory_core_project_match"):
        reasons.append("continuation_same_project_boost")
    if row.get("title_exact"):
        reasons.append("exact_title")
    if row.get("path_exact"):
        reasons.append("exact_path")
    if row.get("filename_exact"):
        reasons.append("exact_filename")
    if row.get("artifact_slug_exact"):
        reasons.append("artifact_slug_exact")
    if row.get("basename_slug_exact"):
        reasons.append("basename_slug_exact")
    if row.get("milestone_core_title_path_cover"):
        reasons.append("milestone_core_title_path_cover")
    if row.get("milestone_single_core_title_path_cover"):
        reasons.append("milestone_single_core_title_path_cover")
    if row.get("milestone_context_match"):
        reasons.append("milestone_context_match")
    if row.get("fts_hit"):
        reasons.append("fts_search_vector")
    if row.get("title_all_tokens"):
        reasons.append("all_tokens_in_title")
    if row.get("path_all_tokens"):
        reasons.append("all_tokens_in_path")
    if int(row.get("token_hit_count") or 0) > 0:
        reasons.append("token_overlap")
    if row.get("title_substring"):
        reasons.append("title_substring")
    if row.get("path_substring"):
        reasons.append("path_substring")
    if row.get("filename_substring"):
        reasons.append("filename_substring")
    if row.get("artifact_slug_substring"):
        reasons.append("artifact_slug_substring")
    if row.get("section_substring"):
        reasons.append("section_substring")
    if row.get("chunk_substring"):
        reasons.append("chunk_substring")
    if row.get("section_similarity", 0.0) >= 0.25:
        reasons.append("section_trgm")
    if row.get("path_similarity", 0.0) >= 0.25:
        reasons.append("path_trgm")
    if row.get("title_similarity", 0.0) >= 0.25:
        reasons.append("title_trgm")
    if row.get("chunk_similarity", 0.0) >= 0.18:
        reasons.append("chunk_trgm")
    return unique_preserve(reasons) or ["lexical_match"]


def format_ref(item: dict[str, Any], style: str) -> str:
    provenance = item.get("provenance", {}) or {}
    if style == "document_locator":
        return str(provenance.get("document_locator") or provenance.get("source_locator") or "")
    if style == "chunk_locator":
        return str(provenance.get("chunk_locator") or provenance.get("source_locator") or "")
    if style == "source_locator":
        return str(provenance.get("source_locator") or provenance.get("file_path") or "")
    return str(provenance.get("source_locator") or "")


def extract_item_dates(items: list[dict[str, Any]]) -> list[str]:
    dates: list[str] = []
    for item in items:
        path = str(item.get("document", {}).get("workspace_path", ""))
        title = str(item.get("document", {}).get("title", ""))
        match = re.search(r"(20\d{2}-\d{2}-\d{2})", path) or re.search(r"(20\d{2})[ _-](\d{2})[ _-](\d{2})", title)
        if not match:
            continue
        if len(match.groups()) == 1:
            date_text = match.group(1)
        else:
            date_text = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        if date_text not in dates:
            dates.append(date_text)
    return dates


def synthesize_conflicts_open_questions(
    query: str,
    items: list[dict[str, Any]],
    classification: dict[str, Any],
    envelope: dict[str, Any],
    serve_pack: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[str], dict[str, Any]]:
    def synthesis_item_norm(item: dict[str, Any]) -> str:
        return normalize_text(" ".join([
            str(item.get("document", {}).get("workspace_path", "")),
            str(item.get("document", {}).get("title", "")),
            str(item.get("chunk", {}).get("section_path", "")),
            str(item.get("excerpt", "")),
        ]))

    def is_policy_verification_tail(item: dict[str, Any]) -> bool:
        workspace_path = str(item.get("document", {}).get("workspace_path", ""))
        combined_norm = synthesis_item_norm(item)
        return (
            "verification-task-" in workspace_path
            or workspace_path.endswith(".json")
            or "regression-pack" in combined_norm
            or "compare-local" in combined_norm
            or "compare-psql" in combined_norm
            or "q1-psql" in combined_norm
            or "q2-psql" in combined_norm
            or "q3-psql" in combined_norm
            or "q4-psql" in combined_norm
            or "q5-psql" in combined_norm
        )

    request_class = str(classification.get("request_class", ""))
    top_items = items[: max(3, int(envelope.get("min_cited_facts", 1)))]
    synthesis_items = list(top_items)
    policy_canonical_markers = {"task-360", "task-361", "routing policy", "authority priority", "memory core", "canonical handoff", "preferred over memory notes", "routing enforcement"}
    if request_class == "policy_decision_lookup":
        canonical_policy_items = [
            item for item in top_items
            if str(item.get("authority", {}).get("layer", "")) == "canonical_handoff"
            and any(marker in synthesis_item_norm(item) for marker in policy_canonical_markers)
        ]
        non_verification_tail = [item for item in top_items if not is_policy_verification_tail(item)]
        if len(canonical_policy_items) >= int(envelope.get("min_cited_facts", 1)) and len(non_verification_tail) >= int(envelope.get("min_cited_facts", 1)):
            synthesis_items = non_verification_tail

    top_layers = [str(item.get("authority", {}).get("layer", "")) for item in synthesis_items if item.get("authority", {}).get("layer")]
    unique_layers = unique_preserve(top_layers)
    dates = extract_item_dates(synthesis_items)
    conflicts: list[dict[str, Any]] = []
    open_questions: list[str] = []

    if len(unique_layers) >= 2:
        conflicts.append({
            "type": "authority_layer_disagreement",
            "summary": f"Top evidence for '{query}' spans multiple authority layers ({', '.join(unique_layers)}) instead of a single clean winner.",
            "layers": unique_layers,
            "refs": unique_preserve([format_ref(item, "source_locator") for item in synthesis_items if format_ref(item, "source_locator")])[:4],
        })
        open_questions.append("Should the answer rely only on the highest-priority layer, or should lower-layer artifacts be surfaced explicitly as competing evidence?")

    counts_by_layer = dict((serve_pack or {}).get("counts_by_layer") or {})
    nonzero_layers = [layer for layer, count in counts_by_layer.items() if count]
    if not conflicts and bool((serve_pack or {}).get("changed_order")) and len(nonzero_layers) >= 2:
        conflicts.append({
            "type": "authority_override_ambiguity",
            "summary": f"Authority ranking reordered results for '{query}', but multiple populated layers remain in contention ({', '.join(nonzero_layers)}).",
            "layers": nonzero_layers,
            "baseline_top_paths": list((serve_pack or {}).get("baseline_top_paths") or [])[:3],
            "final_top_paths": list((serve_pack or {}).get("final_top_paths") or [])[:3],
        })
        open_questions.append("Should the answer rely only on the highest-priority layer, or should lower-layer artifacts be surfaced explicitly as competing evidence?")

    if len(dates) >= 2:
        conflicts.append({
            "type": "freshness_ambiguity",
            "summary": f"Top evidence for '{query}' points to multiple candidate freshness dates ({', '.join(dates[:4])}).",
            "dates": dates,
            "refs": unique_preserve([format_ref(item, "source_locator") for item in synthesis_items if format_ref(item, "source_locator")])[:4],
        })
        open_questions.append(f"Which dated artifact should be treated as the freshest authority for '{query}'? Candidates: {', '.join(dates[:4])}.")

    if not synthesis_items:
        open_questions.append("No bounded evidence items found.")
    elif len(envelope.get("cited_facts", [])) < int(envelope.get("min_cited_facts", 1)):
        open_questions.append(
            f"Only {len(envelope.get('cited_facts', []))} cited fact(s) were available, below the {envelope.get('min_cited_facts')} needed for a clean {classification.get('request_class', 'answer')} answer."
        )
    elif len(unique_preserve([format_ref(item, "source_locator") for item in synthesis_items if format_ref(item, "source_locator")])) == 1 and len(synthesis_items) >= 2:
        open_questions.append("Top evidence comes from a single artifact path, so corroboration is still thin.")

    synthesis_trace = {
        "top_layers_considered": unique_layers,
        "top_dates_considered": dates,
        "conflict_count": len(conflicts),
        "open_question_count": len(open_questions),
        "authority_trace_changed_order": bool((serve_pack or {}).get("changed_order")),
        "policy_tail_suppressed": request_class == "policy_decision_lookup" and synthesis_items != top_items,
        "raw_top_item_count": len(top_items),
        "effective_synthesis_item_count": len(synthesis_items),
    }
    return conflicts, unique_preserve(open_questions), synthesis_trace


def select_envelope_top_items(items: list[dict[str, Any]], classification: dict[str, Any], query: str = "") -> tuple[list[dict[str, Any]], dict[str, Any]]:
    request_class = str(classification.get("request_class", ""))
    if not items:
        return items[:3], {"applied": False, "reason": "no_items"}

    if request_class == "artifact_source_trace_request":
        query_norm = normalize_text(query)
        query_task_refs = set(f"task-{match}" for match in re.findall(r"task[-\s#]*(\d{1,5})", query_norm))
        asks_for_handoff_artifact = any(marker in query_norm for marker in {"handoff artifact", "handoff path", "artifact path"})
        asks_for_status_state_artifact = any(marker in query_norm for marker in {"current status", "current state", "task state", "next step", "status", "state", "handoff/status", "статус", "состояние", "следующий шаг"}) and any(marker in query_norm for marker in {"which file", "what file", "file", "path", "artifact", "stored at", "путь", "файл"})
        if query_task_refs and (asks_for_handoff_artifact or asks_for_status_state_artifact):
            canonical = [
                item for item in items
                if str(item.get("authority", {}).get("layer", "")) == "canonical_handoff"
                and any(ref in normalize_text(str(item.get("document", {}).get("workspace_path", ""))) for ref in query_task_refs)
            ]
            if canonical:
                canonical = sorted(
                    canonical,
                    key=lambda item: (
                        0 if any(ref in normalize_text(str(item.get("document", {}).get("workspace_path", ""))) for ref in query_task_refs) else 1,
                        -float(item.get("score", 0.0)),
                    ),
                )
                locked = canonical[:3]
                extras = [item for item in items if item not in locked]
                return [*locked, *extras][:3], {
                    "applied": True,
                    "reason": "artifact_trace_task_handoff_lock" if asks_for_handoff_artifact else "artifact_trace_task_status_state_lock",
                    "locked_paths": [str(item.get("document", {}).get("workspace_path", "")) for item in locked[:3]],
                }

    if request_class == "meta_evaluation_recall":
        canonical = [
            item for item in items
            if is_expected_meta_evidence_doc(
                str(item.get("document", {}).get("workspace_path", "")),
                str(item.get("document", {}).get("title", "")),
            ) and str(item.get("authority", {}).get("layer", "")) == "evidence_record"
        ]
        if canonical:
            locked = canonical[:3]
            extras = [item for item in items if item not in locked]
            return [*locked, *extras][:3], {
                "applied": True,
                "reason": "meta_expected_evidence_lock",
                "locked_paths": [str(item.get("document", {}).get("workspace_path", "")) for item in locked[:3]],
            }

    if request_class == "architecture_design_recall":
        canonical = [
            item for item in items
            if is_canonical_architecture_doc(
                str(item.get("document", {}).get("workspace_path", "")),
                str(item.get("document", {}).get("title", "")),
            ) and str(item.get("authority", {}).get("layer", "")) == "evidence_record"
        ]
        if canonical:
            locked = canonical[:3]
            extras = [item for item in items if item not in locked]
            return [*locked, *extras][:3], {
                "applied": True,
                "reason": "architecture_canonical_doc_lock",
                "locked_paths": [str(item.get("document", {}).get("workspace_path", "")) for item in locked[:3]],
            }

    if request_class == "policy_decision_lookup":
        query_norm = normalize_text(query)
        policy_markers = {"routing policy", "authority priority", "canonical_handoff", "preferred over memory notes", "handoff-first", "policy", "rule", "rationale", "decision"}
        targeted_task_ids = set(extract_task_numbers(query_norm))
        if any(marker in query_norm for marker in {"routing policy", "authority priority", "memory core", "classifier", "routing enforcement"}):
            targeted_task_ids = set(unique_preserve([*targeted_task_ids, 360, 361]))
        canonical = [
            item for item in items
            if str(item.get("authority", {}).get("layer", "")) in {"evidence_record", "canonical_handoff", "task_state"}
            and not (
                "verification-task-" in str(item.get("document", {}).get("workspace_path", ""))
                or str(item.get("document", {}).get("workspace_path", "")).endswith(".json")
                or "regression-pack" in normalize_text(" ".join([
                    str(item.get("document", {}).get("workspace_path", "")),
                    str(item.get("document", {}).get("title", "")),
                ]))
            )
            and any(marker in normalize_text(" ".join([
                str(item.get("document", {}).get("workspace_path", "")),
                str(item.get("document", {}).get("title", "")),
                str(item.get("chunk", {}).get("section_path", "")),
                str(item.get("excerpt", "")),
            ])) for marker in policy_markers)
            and (
                any(marker in query_norm for marker in policy_markers)
                or bool(targeted_task_ids)
            )
            and (
                not targeted_task_ids
                or bool(targeted_task_ids & set(extract_task_numbers(normalize_text(" ".join([
                    str(item.get("document", {}).get("workspace_path", "")),
                    str(item.get("document", {}).get("title", "")),
                    str(item.get("chunk", {}).get("section_path", "")),
                    str(item.get("excerpt", "")),
                ])))))
            )
        ]
        if canonical:
            locked = canonical[:3]
            extras = [item for item in items if item not in locked]
            return [*locked, *extras][:3], {
                "applied": True,
                "reason": "policy_decision_canonical_lock",
                "locked_paths": [str(item.get("document", {}).get("workspace_path", "")) for item in locked[:3]],
            }

    return items[:3], {"applied": False, "reason": "default_top_items"}


def build_answer_envelope(query: str, items: list[dict[str, Any]], classification: dict[str, Any], serve_pack: dict[str, Any] | None = None) -> dict[str, Any]:
    request_class = str(classification.get("request_class", ""))
    expected_citation = str(classification.get("expected_citation", ""))
    authority_focus = str(classification.get("authority_priority_focus", ""))
    top_items, top_item_lock_trace = select_envelope_top_items(items, classification, query=query)

    envelope_by_class: dict[str, dict[str, Any]] = {
        "current_task_execution": {
            "purpose": "answer+execution",
            "citation_mode": "task_handoff_note",
            "answer_shape": "resume_nucleus",
            "fact_ref_style": "document_locator",
            "supporting_ref_style": "source_locator",
            "min_cited_facts": 1,
            "include_next_action_hints": True,
        },
        "resume_reopen_continuation": {
            "purpose": "resume",
            "citation_mode": "handoff_task_refs",
            "answer_shape": "resume_nucleus",
            "fact_ref_style": "document_locator",
            "supporting_ref_style": "source_locator",
            "min_cited_facts": 1,
            "include_next_action_hints": True,
        },
        "architecture_design_recall": {
            "purpose": "answer",
            "citation_mode": "memory_wiki_backing",
            "answer_shape": "memory_wiki_synthesis",
            "fact_ref_style": "document_locator",
            "supporting_ref_style": "source_locator",
            "min_cited_facts": 2,
            "include_next_action_hints": False,
        },
        "meta_evaluation_recall": {
            "purpose": "answer",
            "citation_mode": "direct_artifact_file_refs",
            "answer_shape": "artifact_trace",
            "fact_ref_style": "source_locator",
            "supporting_ref_style": "chunk_locator",
            "min_cited_facts": 2,
            "include_next_action_hints": False,
        },
        "factual_lookup": {
            "purpose": "answer",
            "citation_mode": "direct_source_path_section",
            "answer_shape": "fact_trace",
            "fact_ref_style": "chunk_locator",
            "supporting_ref_style": "source_locator",
            "min_cited_facts": 2,
            "include_next_action_hints": False,
        },
        "policy_decision_lookup": {
            "purpose": "answer",
            "citation_mode": "note_plus_supporting_evidence",
            "answer_shape": "policy_rationale",
            "fact_ref_style": "document_locator",
            "supporting_ref_style": "chunk_locator",
            "min_cited_facts": 2,
            "include_next_action_hints": False,
        },
        "preference_operating_style_recall": {
            "purpose": "answer",
            "citation_mode": "note_plus_supporting_ref",
            "answer_shape": "preference_recall",
            "fact_ref_style": "document_locator",
            "supporting_ref_style": "source_locator",
            "min_cited_facts": 1,
            "include_next_action_hints": False,
        },
        "artifact_source_trace_request": {
            "purpose": "answer",
            "citation_mode": "direct_artifact_file_refs",
            "answer_shape": "artifact_trace",
            "fact_ref_style": "source_locator",
            "supporting_ref_style": "chunk_locator",
            "min_cited_facts": 2,
            "include_next_action_hints": False,
        },
    }
    envelope = envelope_by_class.get(request_class, envelope_by_class["factual_lookup"])

    policy_primary_markers = {"routing policy", "authority priority", "canonical_handoff", "handoff-first", "preferred over memory notes", "classifier", "routing enforcement", "memory core"}

    def item_combined_norm(item: dict[str, Any]) -> str:
        return normalize_text(" ".join([
            str(item.get("document", {}).get("workspace_path", "")),
            str(item.get("document", {}).get("title", "")),
            str(item.get("chunk", {}).get("section_path", "")),
            str(item.get("excerpt", "")),
        ]))

    envelope_items = list(top_items)
    if request_class == "policy_decision_lookup":
        primary_policy_items = [
            item for item in top_items
            if any(marker in item_combined_norm(item) for marker in policy_primary_markers)
        ]
        support_policy_items = [item for item in top_items if item not in primary_policy_items]
        envelope_items = [*primary_policy_items, *support_policy_items]

    cited_facts: list[dict[str, Any]] = []
    for item in envelope_items[: max(envelope["min_cited_facts"], 1)]:
        cited_facts.append({
            "claim": item.get("excerpt", ""),
            "refs": [format_ref(item, envelope["fact_ref_style"])],
            "authority": item.get("authority", {}).get("layer"),
            "document_title": item.get("document", {}).get("title"),
        })

    def is_policy_verification_wrapper(item: dict[str, Any]) -> bool:
        workspace_path = str(item.get("document", {}).get("workspace_path", ""))
        combined_norm = normalize_text(" ".join([
            workspace_path,
            str(item.get("document", {}).get("title", "")),
            str(item.get("chunk", {}).get("section_path", "")),
            str(item.get("excerpt", "")),
        ]))
        return (
            "verification-task-" in workspace_path
            or workspace_path.endswith(".json")
            or "regression-pack" in combined_norm
            or "compare-local" in combined_norm
            or "compare-psql" in combined_norm
            or "q1-psql" in combined_norm
            or "q2-psql" in combined_norm
            or "q3-psql" in combined_norm
            or "q4-psql" in combined_norm
            or "q5-psql" in combined_norm
        )

    supporting_refs = unique_preserve([
        format_ref(item, envelope["supporting_ref_style"])
        for item in envelope_items
        if format_ref(item, envelope["supporting_ref_style"])
        and not (request_class == "policy_decision_lookup" and is_policy_verification_wrapper(item))
    ])

    authority_notes = []
    for item in envelope_items:
        authority = item.get("authority", {}) or {}
        authority_notes.append({
            "ref": format_ref(item, "source_locator"),
            "authority": authority.get("layer"),
            "matched_from": authority.get("matched_from", []),
            "priority_index": authority.get("priority_index"),
        })

    next_action_hints: list[str] = []
    if envelope["include_next_action_hints"]:
        for item in envelope_items:
            section_path = str(item.get("chunk", {}).get("section_path", ""))
            title = str(item.get("document", {}).get("title", ""))
            if section_path:
                next_action_hints.append(f"Review {section_path} in {title}")
        next_action_hints = unique_preserve(next_action_hints)[:3]

    conflicts, open_questions, synthesis_trace = synthesize_conflicts_open_questions(
        query=query,
        items=items,
        classification=classification,
        envelope={
            **envelope,
            "cited_facts": cited_facts,
        },
        serve_pack=serve_pack,
    )

    applied = {
        "request_class": request_class,
        "meta_subfamily": classification.get("meta_subfamily") if request_class == "meta_evaluation_recall" else None,
        "expected_citation": expected_citation,
        "citation_mode": envelope["citation_mode"],
        "answer_shape": envelope["answer_shape"],
        "purpose": envelope["purpose"],
        "min_cited_facts": envelope["min_cited_facts"],
        "fact_ref_style": envelope["fact_ref_style"],
        "supporting_ref_style": envelope["supporting_ref_style"],
    }
    trace = {
        "authority_priority_focus": authority_focus,
        "meta_subfamily": classification.get("meta_subfamily") if request_class == "meta_evaluation_recall" else None,
        "serve_pack_changed_order": bool((serve_pack or {}).get("changed_order")),
        "top_item_lock": top_item_lock_trace,
        "top_authority_layers": [item.get("authority", {}).get("layer") for item in envelope_items],
        "selected_item_paths": [str(item.get("document", {}).get("workspace_path", "")) for item in envelope_items],
    }
    trace_payload = {
        **trace,
        "synthesis": synthesis_trace,
    }
    trace_summary = {
        "request_class": request_class,
        "purpose": envelope["purpose"],
        "citation_mode": envelope["citation_mode"],
        "authority_priority_focus": authority_focus,
        "top_authority_layers": trace["top_authority_layers"],
        "selected_phase": str(classification.get("selected_phase") or "") or str((classification.get("routing") or {}).get("selected_phase") or ""),
        "selected_item_paths": trace["selected_item_paths"],
        "selected_source_refs": unique_preserve([
            format_ref(item, "source_locator")
            for item in envelope_items
            if format_ref(item, "source_locator")
        ]),
        "selected_chunk_refs": unique_preserve([
            format_ref(item, "chunk_locator")
            for item in envelope_items
            if format_ref(item, "chunk_locator")
        ]),
        "selected_source_keys": unique_preserve([
            str(item.get("source", {}).get("key", ""))
            for item in envelope_items
            if str(item.get("source", {}).get("key", ""))
        ]),
        "fallback_used": bool((serve_pack or {}).get("fallback_used")),
        "fallback_reason": str((serve_pack or {}).get("fallback_reason") or ""),
        "history_assisted_continuation_anchor": (serve_pack or {}).get("history_assisted_continuation_anchor"),
        "typed_serving_applied": bool((serve_pack or {}).get("typed_serving", {}).get("applied")),
        "typed_serving_eligible_count": int((serve_pack or {}).get("typed_serving", {}).get("eligible_typed_count", 0) or 0),
        "typed_serving_ineligible_count": int((serve_pack or {}).get("typed_serving", {}).get("ineligible_typed_count", 0) or 0),
        "changed_order": bool((serve_pack or {}).get("changed_order")),
        "conflict_count": len(conflicts),
        "open_question_count": len(open_questions),
    }

    return {
        "purpose": envelope["purpose"],
        "answer_nucleus": build_summary(query, envelope_items),
        "cited_facts": cited_facts,
        "supporting_refs": supporting_refs,
        "authority_notes": authority_notes,
        "conflicts": conflicts,
        "open_questions": open_questions,
        "next_action_hints": next_action_hints,
        "citation_policy": applied,
        "trace": trace_payload,
        "trace_summary": trace_summary,
    }


def finalize_payload(query: str, mode: str, items: list[dict[str, Any]], provenance: dict[str, Any], routing: dict[str, Any] | None = None, serve_pack: dict[str, Any] | None = None) -> dict[str, Any]:
    for idx, item in enumerate(items, start=1):
        item["rank"] = idx
    classification = dict((routing or {}).get("classification", {}) if routing else {})
    if routing:
        classification["routing"] = routing
        classification["selected_phase"] = routing.get("selected_phase")
    answer_envelope = build_answer_envelope(query, items, classification, serve_pack)
    merged_serve_pack = {
        **(serve_pack or {}),
        **answer_envelope,
    }
    return {
        "query": query,
        "mode": mode,
        "contract_version": CONTRACT_VERSION,
        "item_count": len(items),
        "summary": build_summary(query, items),
        "items": items,
        "provenance": provenance,
        "routing": routing or {},
        "request_classification": classification,
        "serve_pack": merged_serve_pack,
        "answer_envelope": merged_serve_pack,
    }


def apply_canonical_winner_lock(items: list[dict[str, Any]], classification: dict[str, Any], max_items: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    request_class = str(classification.get("request_class", ""))
    if not items:
        return items, {"applied": False, "reason": "no_items"}

    locked: list[dict[str, Any]] = []
    reason = "default"
    if request_class == "meta_evaluation_recall":
        locked = [
            item for item in items
            if is_expected_meta_evidence_doc(
                str(item.get("document", {}).get("workspace_path", "")),
                str(item.get("document", {}).get("title", "")),
            )
        ]
        reason = "meta_expected_evidence_prebounded_lock"
    elif request_class == "architecture_design_recall":
        locked = [
            item for item in items
            if is_canonical_architecture_doc(
                str(item.get("document", {}).get("workspace_path", "")),
                str(item.get("document", {}).get("title", "")),
            )
        ]
        reason = "architecture_canonical_doc_prebounded_lock"
    elif request_class == "resume_reopen_continuation":
        locked = [
            item for item in items
            if str(item.get("authority", {}).get("layer", "")) in {"canonical_handoff", "task_state"}
        ]
        reason = "continuation_handoff_task_state_prebounded_lock"
    elif request_class == "artifact_source_trace_request":
        locked = [
            item for item in items
            if str(item.get("authority", {}).get("layer", "")) == "canonical_handoff"
        ]
        reason = "artifact_trace_canonical_handoff_prebounded_lock"

    if not locked:
        return items, {"applied": False, "reason": "no_canonical_candidates_found"}

    locked = locked[:max_items]
    extras = [item for item in items if item not in locked]
    reordered = [*locked, *extras]
    return reordered, {
        "applied": True,
        "reason": reason,
        "locked_paths": [str(item.get("document", {}).get("workspace_path", "")) for item in locked],
    }


def retrieve_local(query: str, workspace_root: Path, selected_sources: list[dict[str, Any]], max_items: int, include_disabled: bool, registry_path: Path, routing: dict[str, Any]) -> dict[str, Any]:
    documents = load_documents(workspace_root, selected_sources)
    query_tokens = unique_preserve(tokenize(query))
    classification = routing.get("classification", {})
    request_class = str(classification.get("request_class", ""))

    candidates: list[dict[str, Any]] = []
    for document in documents:
        record = document["record"]
        workspace_path = str(document.get("workspace_path", ""))
        title = str(record.title)
        combined_identity = normalize_text(f"{workspace_path} {title}")
        is_memory_handoff_note = workspace_path.startswith("memory/") and "handoff" in combined_identity
        is_task_manager_handoff_doc = workspace_path.startswith("task-manager/handoffs/")
        is_operational_handoff_artifact = workspace_path.startswith("task-manager/artifacts/") and "handoff" in combined_identity
        is_verification_wrapper = "verification-task-" in workspace_path or "regression-pack" in workspace_path

        if request_class == "meta_evaluation_recall":
            if not is_expected_meta_evidence_doc(workspace_path, title):
                continue
            if not is_memory_core_meta_project_doc(workspace_path, title):
                continue
            if is_memory_handoff_note or is_task_manager_handoff_doc or is_operational_handoff_artifact or is_verification_wrapper:
                continue
        elif request_class == "architecture_design_recall" and (
            is_memory_handoff_note or is_task_manager_handoff_doc or is_operational_handoff_artifact or is_verification_wrapper
        ):
            if request_class == "architecture_design_recall":
                architecture_target_markers = {
                    "task-333", "task 333", "task-334", "task 334",
                    "layered architecture", "schema and serving policy",
                    "retrieval policy", "policy matrix",
                }
                if not any(marker in combined_identity for marker in architecture_target_markers):
                    continue

        for chunk in record.chunks:
            scored = score_candidate(query, query_tokens, document, chunk)
            if not scored:
                continue
            locators = build_locators(
                title=record.title,
                workspace_path=document["workspace_path"],
                section_path=chunk["section_path"],
                chunk_ordinal=chunk["chunk_ordinal"],
            )
            item = {
                "score": scored["score"],
                "match_reason": ", ".join(scored["reasons"]),
                "source": {
                    "key": document["source_key"],
                    "root_path": document["source"]["root_path"],
                    "retrieval_scope": document["source"].get("retrieval_scope", "global"),
                    "owner": document["source"].get("owner", ""),
                },
                "document": {
                    "document_id": record.document_id,
                    "title": record.title,
                    "path": record.path,
                    "workspace_path": document["workspace_path"],
                    "document_type": record.document_type,
                    "content_hash": record.content_hash,
                },
                "chunk": {
                    "chunk_id": chunk["chunk_id"],
                    "chunk_ordinal": chunk["chunk_ordinal"],
                    "section_path": chunk["section_path"],
                    "char_count": chunk["char_count"],
                },
                "excerpt": scored["excerpt"],
                "provenance": {
                    "file_path": document["workspace_path"],
                    "source_root": document["source"]["root_path"],
                    "section_path": chunk["section_path"],
                    **locators,
                    "db": None,
                },
            }
            candidates.append(item)

    candidates.sort(key=lambda item: (-item["score"], item["document"]["workspace_path"], item["chunk"]["chunk_ordinal"]))

    deduped: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for candidate in candidates:
        key = (candidate["document"]["document_id"], candidate["chunk"]["chunk_id"])
        if key in seen_pairs:
            continue
        seen_pairs.add(key)
        deduped.append(candidate)

    suppressed = apply_meta_artifact_suppression(deduped, query, classification)
    lane_hygiene_ranked = apply_lane_candidate_hygiene(suppressed, query, classification)
    stage4_boosted = apply_stage4_audit_score_boosts(lane_hygiene_ranked, query, classification)
    continuation_ranked = apply_continuation_freshness_ranking(stage4_boosted, query, classification)
    freshness_ranked = apply_current_execution_freshness_ranking(continuation_ranked, query, classification)
    history_assisted_ranked, history_assisted_trace = apply_history_assisted_continuation_tiebreak(
        freshness_ranked,
        query,
        classification,
    )
    authority_ranked, serve_pack = apply_authority_priority(history_assisted_ranked, classification, routing, query=query)
    canonical_locked_ranked, canonical_lock_pack = apply_canonical_winner_lock(authority_ranked, classification, max_items)
    diversity_ranked, diversity_pack = apply_document_diversity_shaping(canonical_locked_ranked, max_items)
    bounded_items = diversity_ranked[:max_items]

    return finalize_payload(
        query=query,
        mode="phase1-local-baseline",
        items=bounded_items,
        provenance={
            "registry": str(registry_path),
            "workspace_root": str(workspace_root),
            "backend": "local-filesystem",
            "sources_considered": [str(source.get("key", "")) for source in selected_sources],
            "include_disabled": include_disabled,
        },
        routing=routing,
        serve_pack={
            **serve_pack,
            "canonical_winner_lock": canonical_lock_pack,
            "document_diversity": diversity_pack,
            "history_assisted_continuation_tiebreak": history_assisted_trace,
        },
    )


def retrieve_psql(query: str, registry_path: Path, selected_sources: list[dict[str, Any]], max_items: int, include_disabled: bool, env_file: Path, routing: dict[str, Any]) -> dict[str, Any]:
    env = ensure_psql_env(env_file)
    classification = routing.get("classification", {})
    fetch_limit = candidate_fetch_limit(classification, max_items)
    source_keys = [str(source.get("key", "")).strip() for source in selected_sources if str(source.get("key", "")).strip()]
    source_keys_sql = "ARRAY[" + ", ".join(sql_quote(key) for key in source_keys) + "]::text[]" if source_keys else "ARRAY[]::text[]"
    source_key_case = build_source_key_case(selected_sources)
    stage4_trace_active = is_stage4_audit_trace_query(query, classification)
    requested_component_task_ids = stage4_audit_component_task_ids(query)
    explicit_meta_eval = str(classification.get("request_class", "")) == "meta_evaluation_recall"
    architecture_recall = str(classification.get("request_class", "")) == "architecture_design_recall"
    policy_decision_lookup = str(classification.get("request_class", "")) == "policy_decision_lookup"
    query_norm = normalize_text(query)
    policy_family_active = policy_decision_lookup and any(marker in query_norm for marker in {"routing policy", "authority priority", "memory core", "canonical_handoff", "handoff-first", "preferred over memory notes", "classifier", "routing enforcement"})
    meta_project_required = explicit_meta_eval
    memory_core_meta_query = explicit_meta_eval and is_memory_core_meta_project_doc(query)
    include_disabled_sql = "TRUE" if include_disabled else "s.enabled = TRUE"
    stage4_requested_task_ids_sql = "ARRAY[" + ", ".join(str(task_id) for task_id in sorted(requested_component_task_ids)) + "]::int[]" if requested_component_task_ids else "ARRAY[]::int[]"
    policy_requested_task_ids = ({360, 361} | set(extract_task_numbers(query))) if policy_family_active else set(extract_task_numbers(query))
    policy_requested_task_ids_sql = "ARRAY[" + ", ".join(str(task_id) for task_id in sorted(policy_requested_task_ids)) + "]::int[]" if policy_requested_task_ids else "ARRAY[]::int[]"
    sql = fr"""
WITH params AS (
    SELECT
        {sql_quote(query)}::text AS query_text,
        lower({sql_quote(query)})::text AS query_text_lower,
        regexp_replace(lower({sql_quote(query)}), E'[^a-z0-9а-яё]+', '-', 'g')::text AS query_slug,
        regexp_replace(regexp_replace(lower({sql_quote(query)}), E'[^a-z0-9а-яё]+', '-', 'g'), E'^-+|-+$', '', 'g')::text AS query_slug_trimmed,
        regexp_replace(lower({sql_quote(query)}), E'[^a-z0-9а-яё]+', '', 'g')::text AS query_slug_compact,
        plainto_tsquery('simple', {sql_quote(query)}) AS tsq,
        regexp_split_to_array(lower({sql_quote(query)}), E'[^a-z0-9а-яё]+')::text[] AS query_tokens,
        ARRAY['milestone', 'milestones']::text[] AS milestone_tokens,
        {source_keys_sql} AS source_keys,
        regexp_match(lower({sql_quote(query)}), 'task[-\\s#]*(\\d{{1,5}})') AS query_task_match,
        position('memory core' in lower({sql_quote(query)})) > 0 AS query_mentions_memory_core,
        {'TRUE' if explicit_meta_eval else 'FALSE'} AS explicit_meta_eval,
        {'TRUE' if architecture_recall else 'FALSE'} AS architecture_recall,
        {'TRUE' if policy_decision_lookup else 'FALSE'} AS policy_decision_lookup,
        {'TRUE' if policy_family_active else 'FALSE'} AS policy_family_active,
        {'TRUE' if stage4_trace_active else 'FALSE'} AS stage4_trace_active,
        {'TRUE' if meta_project_required else 'FALSE'} AS meta_project_required,
        {'TRUE' if memory_core_meta_query else 'FALSE'} AS memory_core_meta_query,
        {stage4_requested_task_ids_sql} AS stage4_requested_task_ids,
        {policy_requested_task_ids_sql} AS policy_requested_task_ids
), candidates AS (
    SELECT
        {source_key_case} AS source_key,
        s.root_path,
        s.retrieval_scope,
        s.owner,
        d.document_id,
        d.title,
        d.path,
        d.document_type,
        d.content_hash,
        c.chunk_id,
        c.chunk_ordinal,
        c.section_path,
        c.char_count,
        c.chunk_text,
        p.explicit_meta_eval,
        p.architecture_recall,
        p.policy_decision_lookup,
        p.policy_family_active,
        p.stage4_trace_active,
        p.meta_project_required,
        p.memory_core_meta_query,
        ts_rank_cd(c.search_vector, p.tsq) AS chunk_rank,
        ts_rank_cd(d.search_vector, p.tsq) AS document_rank,
        similarity(d.title, p.query_text) AS title_similarity,
        similarity(d.path, p.query_text) AS path_similarity,
        similarity(c.section_path, p.query_text) AS section_similarity,
        similarity(c.chunk_text, p.query_text) AS chunk_similarity,
        lower(d.title) = p.query_text_lower AS title_exact,
        lower(d.path) = p.query_text_lower AS path_exact,
        regexp_replace(lower(regexp_replace(d.path, '^.*/', '')), E'\.[a-z0-9]+$', '', 'g') = p.query_slug AS filename_exact,
        regexp_replace(regexp_replace(lower(d.path), E'\.[a-z0-9]+$', '', 'g'), E'[^a-z0-9а-яё]+', '-', 'g') = p.query_slug_trimmed AS artifact_slug_exact,
        regexp_replace(regexp_replace(lower(regexp_replace(d.path, '^.*/', '')), E'\.[a-z0-9]+$', '', 'g'), E'[^a-z0-9а-яё]+', '', 'g') = p.query_slug_compact AS basename_slug_exact,
        position(p.query_text_lower in lower(d.title)) > 0 AS title_substring,
        position(p.query_text_lower in lower(d.path)) > 0 AS path_substring,
        position(p.query_slug in regexp_replace(lower(regexp_replace(d.path, '^.*/', '')), E'\.[a-z0-9]+$', '', 'g')) > 0 AS filename_substring,
        position(p.query_slug_trimmed in regexp_replace(regexp_replace(lower(d.path), E'\.[a-z0-9]+$', '', 'g'), E'[^a-z0-9а-яё]+', '-', 'g')) > 0 AS artifact_slug_substring,
        position(p.query_text_lower in lower(c.section_path)) > 0 AS section_substring,
        position(p.query_text_lower in lower(c.chunk_text)) > 0 AS chunk_substring,
        EXISTS (
            SELECT 1
            FROM unnest(p.query_tokens) AS token
            WHERE length(token) >= 2
              AND (
                    position(token in lower(d.title)) > 0
                 OR position(token in lower(d.path)) > 0
                 OR position(token in lower(c.section_path)) > 0
                 OR position(token in lower(c.chunk_text)) > 0
              )
        ) AS token_overlap,
        (
            SELECT count(*)
            FROM unnest(p.query_tokens) AS token
            WHERE length(token) >= 2
              AND (
                    position(token in lower(d.title)) > 0
                 OR position(token in lower(d.path)) > 0
                 OR position(token in lower(c.section_path)) > 0
                 OR position(token in lower(c.chunk_text)) > 0
              )
        ) AS token_hit_count,
        NOT EXISTS (
            SELECT 1
            FROM unnest(p.query_tokens) AS token
            WHERE length(token) >= 2
              AND position(token in lower(d.title)) = 0
        ) AS title_all_tokens,
        NOT EXISTS (
            SELECT 1
            FROM unnest(p.query_tokens) AS token
            WHERE length(token) >= 2
              AND position(token in lower(d.path)) = 0
        ) AS path_all_tokens,
        (
            array_position(p.query_tokens, 'milestone') IS NOT NULL
            OR array_position(p.query_tokens, 'milestones') IS NOT NULL
        ) AS query_has_milestone,
        (
            SELECT count(*)
            FROM unnest(p.query_tokens) AS token
            WHERE length(token) >= 2
              AND token <> ALL(p.milestone_tokens)
              AND (
                    position(token in lower(d.title)) > 0
                 OR position(token in lower(d.path)) > 0
              )
        ) AS title_path_core_token_hit_count,
        (
            SELECT count(*)
            FROM unnest(p.query_tokens) AS token
            WHERE length(token) >= 2
              AND token <> ALL(p.milestone_tokens)
        ) AS core_query_token_count,
        (
            (array_position(p.query_tokens, 'milestone') IS NOT NULL OR array_position(p.query_tokens, 'milestones') IS NOT NULL)
            AND (
                SELECT count(*)
                FROM unnest(p.query_tokens) AS token
                WHERE length(token) >= 2
                  AND token <> ALL(p.milestone_tokens)
            ) >= 2
            AND (
                SELECT count(*)
                FROM unnest(p.query_tokens) AS token
                WHERE length(token) >= 2
                  AND token <> ALL(p.milestone_tokens)
                  AND (
                        position(token in lower(d.title)) > 0
                     OR position(token in lower(d.path)) > 0
                  )
            ) = (
                SELECT count(*)
                FROM unnest(p.query_tokens) AS token
                WHERE length(token) >= 2
                  AND token <> ALL(p.milestone_tokens)
            )
        ) AS milestone_core_title_path_cover,
        (
            (array_position(p.query_tokens, 'milestone') IS NOT NULL OR array_position(p.query_tokens, 'milestones') IS NOT NULL)
            AND (
                SELECT count(*)
                FROM unnest(p.query_tokens) AS token
                WHERE length(token) >= 2
                  AND token <> ALL(p.milestone_tokens)
            ) = 1
            AND (
                SELECT count(*)
                FROM unnest(p.query_tokens) AS token
                WHERE length(token) >= 2
                  AND token <> ALL(p.milestone_tokens)
                  AND (
                        position(token in lower(d.title)) > 0
                     OR position(token in lower(d.path)) > 0
                  )
            ) = 1
        ) AS milestone_single_core_title_path_cover,
        (
            (array_position(p.query_tokens, 'milestone') IS NOT NULL OR array_position(p.query_tokens, 'milestones') IS NOT NULL)
            AND (
                position('milestone' in lower(c.section_path)) > 0
                OR position('milestone' in lower(c.chunk_text)) > 0
                OR position('milestones' in lower(c.section_path)) > 0
                OR position('milestones' in lower(c.chunk_text)) > 0
            )
        ) AS milestone_context_match,
        (c.search_vector @@ p.tsq OR d.search_vector @@ p.tsq) AS fts_hit,
        (p.query_task_match IS NOT NULL) AS query_has_task_number,
        CASE
            WHEN p.query_task_match IS NULL THEN NULL
            ELSE (p.query_task_match)[1]
        END AS query_task_number,
        (
            CASE
                WHEN p.query_task_match IS NULL THEN FALSE
                ELSE position(('task-' || (p.query_task_match)[1]) in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                    OR position(('task ' || (p.query_task_match)[1]) in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                    OR position(('task#' || (p.query_task_match)[1]) in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
            END
        ) AS query_task_exact_match,
        (
            p.query_mentions_memory_core
            AND position('memory core' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
        ) AS memory_core_project_match,
        (
            p.stage4_trace_active
            AND (
                position('task-360' in lower(d.path || ' ' || d.title)) > 0
                OR position('task 360' in lower(d.path || ' ' || d.title)) > 0
                OR position('task-361' in lower(d.path || ' ' || d.title)) > 0
                OR position('task 361' in lower(d.path || ' ' || d.title)) > 0
                OR position('task-362' in lower(d.path || ' ' || d.title)) > 0
                OR position('task 362' in lower(d.path || ' ' || d.title)) > 0
                OR position('task-363' in lower(d.path || ' ' || d.title)) > 0
                OR position('task 363' in lower(d.path || ' ' || d.title)) > 0
            )
        ) AS stage4_proving_doc_match,
        (
            p.stage4_trace_active
            AND (
                (position('task-360' in lower(d.path || ' ' || d.title)) > 0 OR position('task 360' in lower(d.path || ' ' || d.title)) > 0)
                AND (position('routing' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('route' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0)
            )
        ) AS stage4_task360_component_match,
        (
            p.stage4_trace_active
            AND (
                (position('task-361' in lower(d.path || ' ' || d.title)) > 0 OR position('task 361' in lower(d.path || ' ' || d.title)) > 0)
                AND (position('authority' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('ranking' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('priority' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0)
            )
        ) AS stage4_task361_component_match,
        (
            p.stage4_trace_active
            AND (
                (position('task-362' in lower(d.path || ' ' || d.title)) > 0 OR position('task 362' in lower(d.path || ' ' || d.title)) > 0)
                AND (position('citation' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('envelope' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('cite' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0)
            )
        ) AS stage4_task362_component_match,
        (
            p.stage4_trace_active
            AND (
                (position('task-363' in lower(d.path || ' ' || d.title)) > 0 OR position('task 363' in lower(d.path || ' ' || d.title)) > 0)
                AND (position('conflict' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('synthesis' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('open question' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0)
            )
        ) AS stage4_task363_component_match,
        (
            p.stage4_trace_active
            AND (
                position('task-364' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task 364' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task-365' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task 365' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task-366' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task 366' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task-367' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task 367' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('acceptance scenarios' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('evaluation summary' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('release recommendation' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('failure modes and hardening log' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
            )
        ) AS stage4_wrapper_like,
        (
            p.explicit_meta_eval
            AND position('task-manager/handoffs/' in lower(s.root_path || '/' || d.path)) > 0
        ) AS meta_eval_handoff_candidate,
        (
            p.explicit_meta_eval
            AND (
                position('verification-task-' in lower(d.path)) > 0
                OR position('regression-pack' in lower(d.path)) > 0
            )
        ) AS meta_eval_wrapper_candidate,
        (
            p.explicit_meta_eval
            AND position('task-manager/artifacts/task-' in lower(s.root_path || '/' || d.path)) > 0
            AND NOT (
                position('verification-task-' in lower(d.path)) > 0
                OR position('regression-pack' in lower(d.path)) > 0
                OR position('contract-and-regression-pack' in lower(d.path)) > 0
                OR position('handoff' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('/summary.json' in lower(s.root_path || '/' || d.path)) > 0
                OR position('compare-local.json' in lower(d.path)) > 0
                OR position('compare-psql.json' in lower(d.path)) > 0
                OR position('q1-psql.json' in lower(d.path)) > 0
                OR position('q2-psql.json' in lower(d.path)) > 0
                OR position('q3-psql.json' in lower(d.path)) > 0
                OR position('q4-psql.json' in lower(d.path)) > 0
                OR position('q5-psql.json' in lower(d.path)) > 0
                OR position('natural_continue-psql.json' in lower(d.path)) > 0
                OR position('explicit_resume-psql.json' in lower(d.path)) > 0
                OR position('reopen_chain-psql.json' in lower(d.path)) > 0
            )
            AND (
                position('task-364' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task 364' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task-365' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task 365' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task-366' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task 366' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task-367' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task 367' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task-368' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task 368' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task-369' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task 369' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task-370' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task 370' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task-376' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task 376' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('acceptance scenarios' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('scenario evaluation' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('evaluation summary' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('release recommendation' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('failure modes and hardening log' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('hardening log' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('hardening slice' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('meta artifact suppression' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('continuation freshness' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('continuation meta alignment' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('bounded reeval summary' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('fail/pass' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('fail pass' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('baseline result' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
            )
        ) AS meta_eval_direct_artifact_candidate,
        (
            p.explicit_meta_eval
            AND position('task-manager/artifacts/task-' in lower(s.root_path || '/' || d.path)) > 0
            AND NOT (
                position('verification-task-' in lower(d.path)) > 0
                OR position('regression-pack' in lower(d.path)) > 0
                OR position('contract-and-regression-pack' in lower(d.path)) > 0
                OR position('handoff' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
            )
        ) AS meta_eval_task_artifact_candidate,
        (
            p.policy_family_active
            AND (
                position('task-360' in lower(d.path || ' ' || d.title)) > 0
                OR position('task 360' in lower(d.path || ' ' || d.title)) > 0
                OR position('task-361' in lower(d.path || ' ' || d.title)) > 0
                OR position('task 361' in lower(d.path || ' ' || d.title)) > 0
            )
        ) AS policy_targeted_task_match,
        (
            p.policy_family_active
            AND (
                position('routing policy' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('authority priority' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('canonical_handoff' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('handoff-first' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('preferred over memory notes' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('classifier' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('routing enforcement' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('memory core' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
            )
        ) AS policy_family_marker_match,
        (
            ts_rank_cd(c.search_vector, p.tsq) * 135.0 +
            ts_rank_cd(d.search_vector, p.tsq) * 72.0 +
            similarity(d.title, p.query_text) * 58.0 +
            similarity(d.path, p.query_text) * 44.0 +
            similarity(c.section_path, p.query_text) * 20.0 +
            similarity(c.chunk_text, p.query_text) * 14.0 +
            (
                SELECT count(*) * 24.0
                FROM unnest(p.query_tokens) AS token
                WHERE length(token) >= 2
                  AND (
                        position(token in lower(d.title)) > 0
                     OR position(token in lower(d.path)) > 0
                     OR position(token in lower(c.section_path)) > 0
                     OR position(token in lower(c.chunk_text)) > 0
                  )
            ) +
            CASE WHEN lower(d.title) = p.query_text_lower THEN 230.0 ELSE 0.0 END +
            CASE WHEN lower(d.path) = p.query_text_lower THEN 240.0 ELSE 0.0 END +
            CASE WHEN regexp_replace(lower(regexp_replace(d.path, '^.*/', '')), E'\.[a-z0-9]+$', '', 'g') = p.query_slug THEN 220.0 ELSE 0.0 END +
            CASE WHEN regexp_replace(regexp_replace(lower(d.path), E'\.[a-z0-9]+$', '', 'g'), E'[^a-z0-9а-яё]+', '-', 'g') = p.query_slug_trimmed THEN 340.0 ELSE 0.0 END +
            CASE WHEN regexp_replace(regexp_replace(lower(regexp_replace(d.path, '^.*/', '')), E'\.[a-z0-9]+$', '', 'g'), E'[^a-z0-9а-яё]+', '', 'g') = p.query_slug_compact THEN 260.0 ELSE 0.0 END +
            CASE WHEN position(p.query_text_lower in lower(d.title)) > 0 THEN 130.0 ELSE 0.0 END +
            CASE WHEN position(p.query_text_lower in lower(d.path)) > 0 THEN 140.0 ELSE 0.0 END +
            CASE WHEN position(p.query_slug in regexp_replace(lower(regexp_replace(d.path, '^.*/', '')), E'\.[a-z0-9]+$', '', 'g')) > 0 THEN 110.0 ELSE 0.0 END +
            CASE WHEN position(p.query_slug_trimmed in regexp_replace(regexp_replace(lower(d.path), E'\.[a-z0-9]+$', '', 'g'), E'[^a-z0-9а-яё]+', '-', 'g')) > 0 THEN 210.0 ELSE 0.0 END +
            CASE WHEN NOT EXISTS (
                SELECT 1
                FROM unnest(p.query_tokens) AS token
                WHERE length(token) >= 2
                  AND position(token in lower(d.title)) = 0
            ) THEN 95.0 ELSE 0.0 END +
            CASE WHEN NOT EXISTS (
                SELECT 1
                FROM unnest(p.query_tokens) AS token
                WHERE length(token) >= 2
                  AND position(token in lower(d.path)) = 0
            ) THEN 85.0 ELSE 0.0 END +
            CASE WHEN position(p.query_text_lower in lower(c.section_path)) > 0 THEN 24.0 ELSE 0.0 END +
            CASE WHEN position(p.query_text_lower in lower(c.chunk_text)) > 0 THEN 14.0 ELSE 0.0 END +
            CASE WHEN (p.query_task_match IS NOT NULL) AND (
                position(('task-' || (p.query_task_match)[1]) in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position(('task ' || (p.query_task_match)[1]) in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position(('task#' || (p.query_task_match)[1]) in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
            ) THEN 320.0 ELSE 0.0 END +
            CASE WHEN (p.query_task_match IS NOT NULL)
                AND position('task-manager/handoffs/' in lower(s.root_path || '/' || d.path)) > 0
                AND position('task-' in lower(d.path || ' ' || d.title)) = 0
            THEN -220.0 ELSE 0.0 END +
            CASE WHEN (p.explicit_meta_eval OR p.architecture_recall)
                AND position('task-manager/handoffs/' in lower(s.root_path || '/' || d.path)) > 0
            THEN -2600.0 ELSE 0.0 END +
            CASE WHEN p.explicit_meta_eval
                AND (
                    position('verification-task-' in lower(d.path)) > 0
                    OR position('regression-pack' in lower(d.path)) > 0
                )
            THEN -2400.0 ELSE 0.0 END +
            CASE WHEN p.architecture_recall
                AND (
                    position('verification-task-' in lower(d.path)) > 0
                    OR position('regression-pack' in lower(d.path)) > 0
                )
            THEN -2400.0 ELSE 0.0 END +
            CASE WHEN p.query_mentions_memory_core
                AND position('memory core' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
            THEN 55.0 ELSE 0.0 END +
            CASE WHEN p.query_task_match IS NULL
                AND p.query_mentions_memory_core
                AND (
                    position('resume' in p.query_text_lower) > 0
                    OR position('reopen' in p.query_text_lower) > 0
                    OR position('continue' in p.query_text_lower) > 0
                    OR position('handoff' in p.query_text_lower) > 0
                    OR position('продолж' in p.query_text_lower) > 0
                )
                AND position('verification-task-' in lower(d.path)) > 0
            THEN -6200.0 ELSE 0.0 END +
            CASE WHEN p.query_task_match IS NULL
                AND p.query_mentions_memory_core
                AND (
                    position('resume' in p.query_text_lower) > 0
                    OR position('reopen' in p.query_text_lower) > 0
                    OR position('continue' in p.query_text_lower) > 0
                    OR position('handoff' in p.query_text_lower) > 0
                    OR position('продолж' in p.query_text_lower) > 0
                )
                AND position('regression-pack' in lower(d.path)) > 0
            THEN -6200.0 ELSE 0.0 END +
            CASE WHEN p.query_task_match IS NULL
                AND p.query_mentions_memory_core
                AND (
                    position('resume' in p.query_text_lower) > 0
                    OR position('reopen' in p.query_text_lower) > 0
                    OR position('continue' in p.query_text_lower) > 0
                    OR position('handoff' in p.query_text_lower) > 0
                    OR position('продолж' in p.query_text_lower) > 0
                )
                AND position('task-manager/artifacts/task-' in lower(s.root_path || '/' || d.path)) > 0
                AND position('handoff' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                AND position('memory core' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
            THEN 2600.0 ELSE 0.0 END +
            CASE WHEN p.query_task_match IS NULL
                AND p.query_mentions_memory_core
                AND (
                    position('resume' in p.query_text_lower) > 0
                    OR position('reopen' in p.query_text_lower) > 0
                    OR position('continue' in p.query_text_lower) > 0
                    OR position('handoff' in p.query_text_lower) > 0
                    OR position('продолж' in p.query_text_lower) > 0
                )
                AND (
                    position('conflict/open-question synthesis' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                    OR position('conflict open question synthesis' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                )
            THEN 1400.0 ELSE 0.0 END +
            CASE WHEN p.policy_family_active AND (
                position('task-360' in lower(d.path || ' ' || d.title)) > 0
                OR position('task 360' in lower(d.path || ' ' || d.title)) > 0
                OR position('task-361' in lower(d.path || ' ' || d.title)) > 0
                OR position('task 361' in lower(d.path || ' ' || d.title)) > 0
            ) THEN 1400.0 ELSE 0.0 END +
            CASE WHEN p.policy_family_active AND (
                position('routing policy' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('authority priority' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('canonical_handoff' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('handoff-first' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('preferred over memory notes' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('classifier' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('routing enforcement' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
            ) THEN 900.0 ELSE 0.0 END +
            CASE WHEN p.policy_family_active AND cardinality(p.policy_requested_task_ids) > 0 AND NOT (
                (array_position(p.policy_requested_task_ids, 360) IS NOT NULL AND (position('task-360' in lower(d.path || ' ' || d.title)) > 0 OR position('task 360' in lower(d.path || ' ' || d.title)) > 0))
                OR (array_position(p.policy_requested_task_ids, 361) IS NOT NULL AND (position('task-361' in lower(d.path || ' ' || d.title)) > 0 OR position('task 361' in lower(d.path || ' ' || d.title)) > 0))
            ) AND (
                position('decision' in lower(d.title || ' ' || c.section_path)) > 0
                OR position('policy' in lower(d.title || ' ' || c.section_path)) > 0
                OR position('why' in lower(d.title || ' ' || c.section_path)) > 0
                OR position('rationale' in lower(d.title || ' ' || c.section_path)) > 0
            ) THEN -1100.0 ELSE 0.0 END +
            CASE WHEN p.query_mentions_memory_core
                AND position('task-manager/handoffs/' in lower(s.root_path || '/' || d.path)) > 0
                AND position('memory core' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) = 0
                AND position('task-' in lower(d.path || ' ' || d.title)) = 0
            THEN -130.0 ELSE 0.0 END +
            CASE WHEN (
                (array_position(p.query_tokens, 'milestone') IS NOT NULL OR array_position(p.query_tokens, 'milestones') IS NOT NULL)
                AND (
                    SELECT count(*)
                    FROM unnest(p.query_tokens) AS token
                    WHERE length(token) >= 2
                      AND token <> ALL(p.milestone_tokens)
                ) >= 2
                AND (
                    SELECT count(*)
                    FROM unnest(p.query_tokens) AS token
                    WHERE length(token) >= 2
                      AND token <> ALL(p.milestone_tokens)
                      AND (
                            position(token in lower(d.title)) > 0
                         OR position(token in lower(d.path)) > 0
                      )
                ) = (
                    SELECT count(*)
                    FROM unnest(p.query_tokens) AS token
                    WHERE length(token) >= 2
                      AND token <> ALL(p.milestone_tokens)
                )
            ) THEN 360.0 ELSE 0.0 END +
            CASE WHEN (
                (array_position(p.query_tokens, 'milestone') IS NOT NULL OR array_position(p.query_tokens, 'milestones') IS NOT NULL)
                AND (
                    SELECT count(*)
                    FROM unnest(p.query_tokens) AS token
                    WHERE length(token) >= 2
                      AND token <> ALL(p.milestone_tokens)
                ) = 1
                AND (
                    SELECT count(*)
                    FROM unnest(p.query_tokens) AS token
                    WHERE length(token) >= 2
                      AND token <> ALL(p.milestone_tokens)
                      AND (
                            position(token in lower(d.title)) > 0
                         OR position(token in lower(d.path)) > 0
                      )
                ) = 1
            ) THEN 320.0 ELSE 0.0 END +
            CASE WHEN (
                (array_position(p.query_tokens, 'milestone') IS NOT NULL OR array_position(p.query_tokens, 'milestones') IS NOT NULL)
                AND (
                    position('milestone' in lower(c.section_path)) > 0
                    OR position('milestone' in lower(c.chunk_text)) > 0
                    OR position('milestones' in lower(c.section_path)) > 0
                    OR position('milestones' in lower(c.chunk_text)) > 0
                )
            ) THEN 28.0 ELSE 0.0 END +
            CASE WHEN p.stage4_trace_active AND (
                (
                    (position('task-360' in lower(d.path || ' ' || d.title)) > 0 OR position('task 360' in lower(d.path || ' ' || d.title)) > 0)
                    AND (position('routing' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('route' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0)
                )
                OR (
                    (position('task-361' in lower(d.path || ' ' || d.title)) > 0 OR position('task 361' in lower(d.path || ' ' || d.title)) > 0)
                    AND (position('authority' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('ranking' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('priority' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0)
                )
                OR (
                    (position('task-362' in lower(d.path || ' ' || d.title)) > 0 OR position('task 362' in lower(d.path || ' ' || d.title)) > 0)
                    AND (position('citation' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('envelope' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('cite' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0)
                )
                OR (
                    (position('task-363' in lower(d.path || ' ' || d.title)) > 0 OR position('task 363' in lower(d.path || ' ' || d.title)) > 0)
                    AND (position('conflict' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('synthesis' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('open question' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0)
                )
            ) THEN 980.0 ELSE 0.0 END +
            CASE WHEN p.stage4_trace_active AND (
                position('task-360' in lower(d.path || ' ' || d.title)) > 0
                OR position('task 360' in lower(d.path || ' ' || d.title)) > 0
                OR position('task-361' in lower(d.path || ' ' || d.title)) > 0
                OR position('task 361' in lower(d.path || ' ' || d.title)) > 0
                OR position('task-362' in lower(d.path || ' ' || d.title)) > 0
                OR position('task 362' in lower(d.path || ' ' || d.title)) > 0
                OR position('task-363' in lower(d.path || ' ' || d.title)) > 0
                OR position('task 363' in lower(d.path || ' ' || d.title)) > 0
            ) THEN 420.0 ELSE 0.0 END +
            CASE WHEN p.stage4_trace_active AND cardinality(p.stage4_requested_task_ids) > 0 AND (
                (array_position(p.stage4_requested_task_ids, 360) IS NOT NULL AND ((position('task-360' in lower(d.path || ' ' || d.title)) > 0 OR position('task 360' in lower(d.path || ' ' || d.title)) > 0) AND (position('routing' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('route' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0)))
                OR (array_position(p.stage4_requested_task_ids, 361) IS NOT NULL AND ((position('task-361' in lower(d.path || ' ' || d.title)) > 0 OR position('task 361' in lower(d.path || ' ' || d.title)) > 0) AND (position('authority' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('ranking' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('priority' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0)))
                OR (array_position(p.stage4_requested_task_ids, 362) IS NOT NULL AND ((position('task-362' in lower(d.path || ' ' || d.title)) > 0 OR position('task 362' in lower(d.path || ' ' || d.title)) > 0) AND (position('citation' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('envelope' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('cite' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0)))
                OR (array_position(p.stage4_requested_task_ids, 363) IS NOT NULL AND ((position('task-363' in lower(d.path || ' ' || d.title)) > 0 OR position('task 363' in lower(d.path || ' ' || d.title)) > 0) AND (position('conflict' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('synthesis' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0 OR position('open question' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0)))
            ) THEN 520.0 ELSE 0.0 END +
            CASE WHEN p.stage4_trace_active AND (
                position('task-364' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task 364' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task-365' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task 365' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task-366' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task 366' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task-367' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('task 367' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('acceptance scenarios' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('evaluation summary' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('release recommendation' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
                OR position('failure modes and hardening log' in lower(d.path || ' ' || d.title || ' ' || c.section_path || ' ' || c.chunk_text)) > 0
            ) AND NOT (
                position('task-360' in lower(d.path || ' ' || d.title)) > 0
                OR position('task 360' in lower(d.path || ' ' || d.title)) > 0
                OR position('task-361' in lower(d.path || ' ' || d.title)) > 0
                OR position('task 361' in lower(d.path || ' ' || d.title)) > 0
                OR position('task-362' in lower(d.path || ' ' || d.title)) > 0
                OR position('task 362' in lower(d.path || ' ' || d.title)) > 0
                OR position('task-363' in lower(d.path || ' ' || d.title)) > 0
                OR position('task 363' in lower(d.path || ' ' || d.title)) > 0
            ) THEN -680.0 ELSE 0.0 END
        ) AS blended_score
    FROM params p
    JOIN sources s ON TRUE
    JOIN documents d ON d.source_id = s.source_id AND d.is_deleted = FALSE
    JOIN chunks c ON c.document_id = d.document_id
    WHERE ({include_disabled_sql})
      AND (cardinality(p.source_keys) = 0 OR (s.config_json ->> 'key') = ANY(p.source_keys))
      AND (
            c.search_vector @@ p.tsq
         OR d.search_vector @@ p.tsq
         OR d.title % p.query_text
         OR d.path % p.query_text
         OR c.section_path % p.query_text
         OR c.chunk_text % p.query_text
         OR position(p.query_text_lower in lower(d.title)) > 0
         OR position(p.query_text_lower in lower(d.path)) > 0
         OR position(p.query_slug in regexp_replace(lower(regexp_replace(d.path, '^.*/', '')), E'\.[a-z0-9]+$', '', 'g')) > 0
         OR position(p.query_slug_trimmed in regexp_replace(regexp_replace(lower(d.path), E'\.[a-z0-9]+$', '', 'g'), E'[^a-z0-9а-яё]+', '-', 'g')) > 0
         OR regexp_replace(regexp_replace(lower(regexp_replace(d.path, '^.*/', '')), E'\.[a-z0-9]+$', '', 'g'), E'[^a-z0-9а-яё]+', '', 'g') = p.query_slug_compact
         OR position(p.query_text_lower in lower(c.section_path)) > 0
         OR position(p.query_text_lower in lower(c.chunk_text)) > 0
         OR EXISTS (
                SELECT 1
                FROM unnest(p.query_tokens) AS token
                WHERE length(token) >= 2
                  AND (
                        position(token in lower(d.title)) > 0
                     OR position(token in lower(d.path)) > 0
                     OR position(token in lower(c.section_path)) > 0
                     OR position(token in lower(c.chunk_text)) > 0
                  )
            )
      )
), ranked AS (
    SELECT
        *,
        row_number() OVER (PARTITION BY document_id ORDER BY blended_score DESC, chunk_ordinal ASC) AS doc_best_rank
    FROM candidates
), meta_eval_admission AS (
    SELECT
        ranked.*,
        max(CASE WHEN ranked.meta_eval_direct_artifact_candidate THEN 1 ELSE 0 END) OVER () AS any_meta_eval_direct_artifact,
        max(CASE WHEN ranked.meta_eval_task_artifact_candidate THEN 1 ELSE 0 END) OVER () AS any_meta_eval_task_artifact
    FROM ranked
)
SELECT row_to_json(t)
FROM (
    SELECT *
    FROM meta_eval_admission
    WHERE doc_best_rank = 1
      AND (
            NOT explicit_meta_eval
         OR (
                any_meta_eval_direct_artifact::boolean
            AND meta_eval_direct_artifact_candidate
            )
         OR (
                NOT any_meta_eval_direct_artifact::boolean
            AND any_meta_eval_task_artifact::boolean
            AND meta_eval_task_artifact_candidate
            AND (
                position('task-364' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('task 364' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('task-365' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('task 365' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('task-366' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('task 366' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('task-367' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('task 367' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('task-368' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('task 368' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('task-369' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('task 369' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('task-370' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('task 370' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('task-376' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('task 376' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('acceptance scenarios' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('scenario evaluation' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('evaluation summary' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('release recommendation' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('failure modes and hardening log' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('hardening log' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('hardening slice' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('meta artifact suppression' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('continuation freshness' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('continuation meta alignment' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
                OR position('bounded reeval summary' in lower(path || ' ' || title || ' ' || section_path || ' ' || chunk_text)) > 0
            )
            )
         OR (
                NOT any_meta_eval_direct_artifact::boolean
            AND NOT any_meta_eval_task_artifact::boolean
            AND NOT meta_eval_handoff_candidate
            AND NOT meta_eval_wrapper_candidate
            )
      )
    ORDER BY
        CASE
            WHEN explicit_meta_eval AND any_meta_eval_direct_artifact::boolean AND meta_eval_direct_artifact_candidate THEN 0
            WHEN explicit_meta_eval AND NOT any_meta_eval_direct_artifact::boolean AND any_meta_eval_task_artifact::boolean AND meta_eval_task_artifact_candidate THEN 1
            WHEN explicit_meta_eval AND any_meta_eval_direct_artifact::boolean AND meta_eval_handoff_candidate THEN 4
            WHEN explicit_meta_eval AND any_meta_eval_direct_artifact::boolean AND meta_eval_wrapper_candidate THEN 5
            ELSE 2
        END,
        blended_score DESC,
        path ASC,
        chunk_ordinal ASC
    LIMIT {fetch_limit}
) AS t;
""".strip()
    run_env = {**env}
    result = subprocess.run(
        [
            "psql", "-X", "-t", "-A", "-v", "ON_ERROR_STOP=1",
            "-h", env["PGHOST"], "-p", env["PGPORT"], "-U", env["PGUSER"], "-d", env["PGDATABASE"],
            "-c", sql,
        ],
        env=run_env,
        capture_output=True,
        text=True,
        check=True,
    )
    items: list[dict[str, Any]] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        source_root = row["root_path"]
        workspace_path = str(Path(source_root) / row["path"])
        reasons = build_reasons(row)
        stage4_delta, stage4_reasons = stage4_psql_row_delta(row, query, routing.get("classification", {}))
        reasons = unique_preserve([*reasons, *stage4_reasons])
        locators = build_locators(
            title=row["title"],
            workspace_path=workspace_path,
            section_path=row["section_path"],
            chunk_ordinal=row["chunk_ordinal"],
        )
        items.append({
            "score": round(float(row["blended_score"]) + stage4_delta, 3),
            "match_reason": ", ".join(reasons),
            "source": {
                "key": row["source_key"],
                "root_path": row["root_path"],
                "retrieval_scope": row["retrieval_scope"],
                "owner": row["owner"],
            },
            "document": {
                "document_id": row["document_id"],
                "title": row["title"],
                "path": row["path"],
                "workspace_path": workspace_path,
                "document_type": row["document_type"],
                "content_hash": row["content_hash"],
            },
            "chunk": {
                "chunk_id": row["chunk_id"],
                "chunk_ordinal": row["chunk_ordinal"],
                "section_path": row["section_path"],
                "char_count": row["char_count"],
            },
            "excerpt": build_excerpt(row.get("chunk_text", ""), unique_preserve(tokenize(query))),
            "provenance": {
                "file_path": workspace_path,
                "source_root": source_root,
                "section_path": row["section_path"],
                **locators,
                "db": {
                    "document_rank": round(float(row.get("document_rank", 0.0)), 6),
                    "chunk_rank": round(float(row.get("chunk_rank", 0.0)), 6),
                    "title_similarity": round(float(row.get("title_similarity", 0.0)), 6),
                    "path_similarity": round(float(row.get("path_similarity", 0.0)), 6),
                    "section_similarity": round(float(row.get("section_similarity", 0.0)), 6),
                    "chunk_similarity": round(float(row.get("chunk_similarity", 0.0)), 6),
                    "token_hit_count": int(row.get("token_hit_count") or 0),
                    "title_exact": bool(row.get("title_exact")),
                    "path_exact": bool(row.get("path_exact")),
                    "filename_exact": bool(row.get("filename_exact")),
                    "artifact_slug_exact": bool(row.get("artifact_slug_exact")),
                    "basename_slug_exact": bool(row.get("basename_slug_exact")),
                    "artifact_slug_substring": bool(row.get("artifact_slug_substring")),
                    "title_all_tokens": bool(row.get("title_all_tokens")),
                    "path_all_tokens": bool(row.get("path_all_tokens")),
                    "query_has_milestone": bool(row.get("query_has_milestone")),
                    "title_path_core_token_hit_count": int(row.get("title_path_core_token_hit_count") or 0),
                    "core_query_token_count": int(row.get("core_query_token_count") or 0),
                    "milestone_core_title_path_cover": bool(row.get("milestone_core_title_path_cover")),
                    "milestone_single_core_title_path_cover": bool(row.get("milestone_single_core_title_path_cover")),
                    "milestone_context_match": bool(row.get("milestone_context_match")),
                    "fts_hit": bool(row.get("fts_hit")),
                },
            },
        })

    suppressed = apply_meta_artifact_suppression(items, query, routing.get("classification", {}))
    lane_hygiene_ranked = apply_lane_candidate_hygiene(suppressed, query, routing.get("classification", {}))
    stage4_boosted = apply_stage4_audit_score_boosts(lane_hygiene_ranked, query, routing.get("classification", {}))
    continuation_ranked = apply_continuation_freshness_ranking(stage4_boosted, query, routing.get("classification", {}))
    freshness_ranked = apply_current_execution_freshness_ranking(continuation_ranked, query, routing.get("classification", {}))
    history_assisted_ranked, history_assisted_trace = apply_history_assisted_continuation_tiebreak(
        freshness_ranked,
        query,
        routing.get("classification", {}),
    )
    authority_ranked, serve_pack = apply_authority_priority(history_assisted_ranked, routing.get("classification", {}), routing, query=query)
    canonical_locked_ranked, canonical_lock_pack = apply_canonical_winner_lock(authority_ranked, routing.get("classification", {}), max_items)
    diversity_ranked, diversity_pack = apply_document_diversity_shaping(canonical_locked_ranked, max_items)
    bounded_items = diversity_ranked[:max_items]

    return finalize_payload(
        query=query,
        mode="phase1-postgres-lexical",
        items=bounded_items,
        provenance={
            "registry": str(registry_path),
            "env_file": str(env_file),
            "backend": "postgresql",
            "sources_considered": source_keys,
            "include_disabled": include_disabled,
        },
        routing=routing,
        serve_pack={
            **serve_pack,
            "canonical_winner_lock": canonical_lock_pack,
            "document_diversity": diversity_pack,
            "history_assisted_continuation_tiebreak": history_assisted_trace,
        },
    )


def retrieve(query: str, workspace_root: Path, registry_path: Path, max_items: int, include_disabled: bool, source_keys: list[str], mode: str, env_file: Path, classification: dict[str, Any]) -> dict[str, Any]:
    registry = load_registry(registry_path)
    selected_sources = select_sources(registry, set(source_keys) if source_keys else None, include_disabled)
    routed_sources, routing = route_sources(selected_sources, classification, query)
    bounded_max_items = budget_item_limit(str(classification.get("budget", "medium")), max_items)
    if mode == "local":
        return retrieve_local(query, workspace_root, routed_sources, bounded_max_items, include_disabled, registry_path, routing)
    if mode == "psql":
        return retrieve_psql(query, registry_path, routed_sources, bounded_max_items, include_disabled, env_file, routing)
    try:
        return retrieve_psql(query, registry_path, routed_sources, bounded_max_items, include_disabled, env_file, routing)
    except Exception as exc:
        payload = retrieve_local(query, workspace_root, routed_sources, bounded_max_items, include_disabled, registry_path, routing)
        payload["mode"] = "phase1-local-baseline-fallback"
        payload.setdefault("provenance", {})["fallback_reason"] = str(exc)
        payload["provenance"]["requested_mode"] = "auto"
        payload.setdefault("serve_pack", {})["fallback_used"] = True
        payload["serve_pack"]["fallback_reason"] = str(exc)
        return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase-1 retrieval with PostgreSQL lexical path and local fallback")
    parser.add_argument("query", help="Natural-language or exact/path/title-ish lookup query")
    parser.add_argument("--registry", default=str(ROOT / "config" / "source_registry.seed.yaml"))
    parser.add_argument("--workspace-root", default=str(ROOT.parent))
    parser.add_argument("--env-file", default=str(ROOT / "config" / "memory.env"))
    parser.add_argument("--mode", choices=["auto", "local", "psql"], default="auto")
    parser.add_argument("--max-items", type=int, default=6, help="Bounded evidence-pack size; clamped to 4..8")
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument("--source-key", action="append", default=[], help="Limit retrieval to one or more registry source keys")
    parser.add_argument("--output", help="Optional path to write the JSON evidence pack")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    classification = classify_request(args.query)
    payload = retrieve(
        query=args.query,
        workspace_root=Path(args.workspace_root).resolve(),
        registry_path=Path(args.registry).resolve(),
        max_items=clamp_items(args.max_items),
        include_disabled=args.include_disabled,
        source_keys=args.source_key,
        mode=args.mode,
        env_file=Path(args.env_file).resolve(),
        classification=classification,
    )
    payload["request_classification"] = classification
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
