from __future__ import annotations

import re
from typing import Any

REQUEST_CLASS_SPECS: dict[str, dict[str, Any]] = {
    "current_task_execution": {
        "serve_class": "always_on_candidate+on_demand",
        "budget": "small",
        "primary_domains": ["task-manager state", "canonical handoff", "task-scoped memory notes"],
        "fallback_domains": ["wiki_page", "evidence_record", "retrieval_document"],
        "forbidden_default_domains": ["unrelated project history", "transcript tails", "stale session capsules from other runs"],
        "authority_priority_focus": "task state/handoff > memory_note > wiki/evidence > retrieval_document",
        "expected_citation": "task id, handoff artifact path, note refs",
    },
    "resume_reopen_continuation": {
        "serve_class": "always_on_candidate+on_demand",
        "budget": "small",
        "primary_domains": ["canonical handoff", "fresh task state", "state summaries for same run"],
        "fallback_domains": ["evidence_record", "wiki_page"],
        "forbidden_default_domains": ["stale capsules from other runs", "long chat replay", "transcript-first reconstruction"],
        "authority_priority_focus": "handoff/task state > evidence_record > wiki_page > retrieval_document > owning active capsule only if needed",
        "expected_citation": "handoff/task refs",
    },
    "architecture_design_recall": {
        "serve_class": "on_demand",
        "budget": "small",
        "primary_domains": ["evidence_record", "memory_note", "wiki_page"],
        "fallback_domains": ["retrieval_document"],
        "forbidden_default_domains": ["raw transcripts by default", "session capsules"],
        "authority_priority_focus": "evidence_record > memory_note > wiki_page > retrieval_document",
        "expected_citation": "canonical architecture doc refs first, then supporting note refs",
    },
    "meta_evaluation_recall": {
        "serve_class": "on_demand",
        "budget": "small",
        "primary_domains": ["evidence_record"],
        "fallback_domains": ["memory_note", "wiki_page", "retrieval_document"],
        "forbidden_default_domains": ["continuation handoff substitution", "transcript-only recall", "memory-only answer with no cited artifact basis"],
        "authority_priority_focus": "evidence_record > canonical_handoff > memory_note > wiki_page > retrieval_document",
        "expected_citation": "explicit artifact path(s), evidence-bearing file refs, fail/pass summary sources",
    },
    "factual_lookup": {
        "serve_class": "on_demand",
        "budget": "medium",
        "primary_domains": ["evidence_record"],
        "fallback_domains": ["retrieval_document", "wiki_page for orientation only"],
        "forbidden_default_domains": ["session_capsule", "unsupported summaries", "transcript recollection"],
        "authority_priority_focus": "evidence_record > retrieval_document > wiki_page",
        "expected_citation": "direct source path/section refs",
    },
    "policy_decision_lookup": {
        "serve_class": "on_demand",
        "budget": "small",
        "primary_domains": ["memory_note"],
        "fallback_domains": ["wiki_page", "evidence_record"],
        "forbidden_default_domains": ["generic chunk dumps", "transcript-tail summaries"],
        "authority_priority_focus": "memory_note > wiki_page > evidence_record > canonical_handoff > retrieval_document",
        "expected_citation": "policy note refs first, then supporting artifact refs",
    },
    "preference_operating_style_recall": {
        "serve_class": "always_on_candidate+on_demand",
        "budget": "tiny",
        "primary_domains": ["verified preference notes"],
        "fallback_domains": ["evidence_record"],
        "forbidden_default_domains": ["speculative notes", "old transcript recollections"],
        "authority_priority_focus": "memory_note > evidence_record",
        "expected_citation": "note refs + supporting ref",
    },
    "artifact_source_trace_request": {
        "serve_class": "on_demand",
        "budget": "medium",
        "primary_domains": ["evidence_record"],
        "fallback_domains": ["retrieval_document"],
        "forbidden_default_domains": ["memory-only answer with no source"],
        "authority_priority_focus": "evidence_record > retrieval_document",
        "expected_citation": "direct artifact/file refs",
    },
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9а-яё/_\-. ]+", " ", text.lower(), flags=re.IGNORECASE)).strip()


def tokenize(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-z0-9а-яё][a-z0-9а-яё_\-/\.]{1,}", text.lower(), flags=re.IGNORECASE) if len(token) >= 2]


def detect_meta_evaluation_subfamily(query: str) -> str:
    query_norm = normalize_text(query)
    release_markers = {
        "release recommendation", "release rec", "release", "verdict", "recommend", "recommendation",
        "ship", "ready to release", "go no go", "go/no-go", "exec verdict",
    }
    hardening_markers = {
        "hardening", "hardening slice", "slice", "suppression", "alignment", "freshness",
        "failure mode", "failure modes", "blocker", "bounded fix", "next hardening",
    }
    evaluation_markers = {
        "evaluation", "evaluation summary", "summary", "scenario", "scenarios", "acceptance",
        "baseline", "fail/pass", "fail pass", "audit",
    }

    if any(marker in query_norm for marker in release_markers):
        return "release_recommendation"
    if any(marker in query_norm for marker in hardening_markers):
        return "hardening_slice"
    if any(marker in query_norm for marker in evaluation_markers):
        return "evaluation_summary"
    return "evaluation_summary"


def is_short_meta_evaluation_query(query: str) -> bool:
    query_norm = normalize_text(query)
    query_tokens = tokenize(query)
    if len(query_tokens) > 4:
        return False
    anchor_markers = {
        "memory core", "stage 5", "meta", "evaluation", "hardening", "summary", "release", "verdict", "recommend",
        "мета", "оцен", "слайс", "релиз",
    }
    short_markers = {
        "verdict", "release rec", "recommend", "recommendation", "meta evaluation", "hardening slice",
        "evaluation summary", "stage 5 verdict", "memory core verdict", "release recommendation",
        "summary for stage 5", "hardening for stage 5", "go no go", "go/no-go",
    }
    return any(marker in query_norm for marker in short_markers) or sum(1 for marker in anchor_markers if marker in query_norm) >= 2


def is_explicit_meta_query(query: str) -> bool:
    query_norm = normalize_text(query)
    strong_meta_markers = {
        "acceptance scenario", "acceptance scenarios", "scenario pack", "evaluation summary",
        "release recommendation", "failure modes and hardening log", "hardening log", "hardening slice",
        "task 364", "task 365", "task 366", "task 367", "task 368", "task 369", "task 370",
        "stage 5", "stage 5 1", "stage 5 2", "stage 5 3", "stage 5 4", "stage 5 5", "stage 5 6",
        "baseline fail", "baseline pass", "fail/pass summary", "continuation/meta alignment",
        "сценар", "мета", "аудит оцен", "baseline", "харден", "слайс",
    }
    return any(token in query_norm for token in strong_meta_markers)


def classify_request(query: str) -> dict[str, Any]:
    normalized = normalize_text(query)
    tokens = set(tokenize(query))

    def has_any(*needles: str) -> bool:
        return any(needle in normalized for needle in needles)

    explicit_meta_like = is_explicit_meta_query(query)
    meta_subfamily = detect_meta_evaluation_subfamily(query)
    strong_continuation_like = has_any(
        "resume", "reopen", "pick back up", "continue from handoff",
        "продолжи", "продолжить", "с места после", "следующим bounded шагом"
    )
    explicit_trace_like = has_any(
        "trace", "citation", "cite", "where in", "which file", "what file", "file contains", "handoff file", "artifact", "path",
        "из каких именно файлов", "из каких файлов", "каких именно файлов", "покажи файлы", "в каких файлах", "где видно", "какой файл", "файл handoff"
    ) or (
        has_any("source")
        and not has_any("source of truth")
    ) or (
        has_any("handoff") and has_any("file", "path", "stored at", "какой файл", "путь", "файл")
    )
    short_meta_eval_like = is_short_meta_evaluation_query(query)
    status_file_trace_like = (
        has_any("file", "which file", "what file", "file contains", "artifact", "path", "stored at", "какой файл", "путь", "файл")
        and has_any("current status", "current state", "task state", "next step", "status", "state", "handoff/status", "текущий статус", "состояние", "следующий шаг")
    )
    decision_rationale_like = has_any(
        "why", "rationale", "what decision", "which decision", "decision led", "why preferred", "why did we choose",
        "policy", "rule", "reason", "объясни почему", "почему", "почему решили", "зачем решили", "объясни rationale", "какое решение", "политика", "правило", "причина"
    )

    if status_file_trace_like:
        request_class = "artifact_source_trace_request"
        confidence = "high"
        reasons = ["matched file/path-shaped status trace override before current-task execution lane"]
    elif decision_rationale_like and not explicit_trace_like and not strong_continuation_like:
        request_class = "policy_decision_lookup"
        confidence = "high"
        reasons = ["matched decision/rationale/policy cues before continuation lane"]
    elif has_any(
        "current task", "active task", "next task", "continue task", "continue working",
        "where are we now", "where are we at", "where do we stand", "where is task", "where is the task", "where is current task",
        "current status", "status now",
        "what is already done", "already done", "what's already done", "what is done",
        "what next", "next step", "next steps", "based on current handoff", "based on current state",
        "где сейчас", "где задача", "где сейчас задача", "что уже готово", "на каком этапе", "текущий статус", "что готово",
        "уже сделано", "что дальше", "следующий шаг", "следующие шаги", "что делать дальше",
    ):
        request_class = "current_task_execution"
        confidence = "high"
        reasons = ["matched current-task execution cues"]
    elif (explicit_meta_like or short_meta_eval_like) and not strong_continuation_like and has_any(
        "evaluation", "hardening", "hardening slice", "scenario", "release recommendation", "release", "summary", "meta",
        "оцен", "сценар", "мета", "аудит", "slice", "stage 5", "fail/pass", "fail pass", "verdict", "recommend",
        "go no go", "go/no-go",
    ):
        request_class = "meta_evaluation_recall"
        confidence = "high"
        reasons = ["matched explicit meta/evaluation cues before continuation lane"]
        if short_meta_eval_like and not explicit_meta_like:
            reasons.append("short meta/evaluation anti-fallthrough override")
    elif explicit_trace_like:
        request_class = "artifact_source_trace_request"
        confidence = "high"
        reasons = ["matched source-trace / provenance cues before continuation lane"]
    elif has_any(
        "resume", "reopen", "pick back up", "continue from handoff", "handoff",
        "продолжи", "продолжить", "с места после", "что делать следующим bounded шагом", "следующим bounded шагом",
    ):
        request_class = "resume_reopen_continuation"
        confidence = "high"
        reasons = ["matched resume/reopen continuity cues"]
    elif has_any("architecture", "design", "spec", "contract", "policy matrix", "baseline"):
        request_class = "architecture_design_recall"
        confidence = "medium"
        reasons = ["matched architecture/design recall cues"]
    elif has_any(
        "preference", "prefer", "style", "operating style", "how should i answer", "answer yuriy", "answer yuri",
        "как лучше отвечать", "лучше отвечать", "коротко по делу", "с длинным разбором", "как лучше говорить", "стиль ответа",
        "предпочт", "предпочтения по стилю", "предпочтения по стилю ответа", "reply style",
    ):
        request_class = "preference_operating_style_recall"
        confidence = "medium"
        reasons = ["matched preference/operating-style cues"]
    elif has_any(
        "why", "decision", "policy", "rule", "rationale",
        "почему", "почему решили", "зачем решили", "объясни почему", "объясни rationale",
    ):
        request_class = "policy_decision_lookup"
        confidence = "medium"
        reasons = ["matched policy/decision lookup cues"]
    else:
        pathish_tokens = {"md", "py", "json", "yaml", "yml", "txt", "sql", "task", "tasks", "artifact", "file", "path"}
        if "/" in query or "#" in query or any(token in tokens for token in pathish_tokens):
            request_class = "factual_lookup"
            confidence = "medium"
            reasons = ["defaulted to factual lookup due to artifact/path-like tokens"]
        else:
            request_class = "factual_lookup"
            confidence = "low"
            reasons = ["fell back to factual lookup as safest default"]

    spec = REQUEST_CLASS_SPECS[request_class]
    result = {
        "request_class": request_class,
        "confidence": confidence,
        "reasons": reasons,
        **spec,
    }
    if request_class == "meta_evaluation_recall":
        result["meta_subfamily"] = meta_subfamily
    return result
