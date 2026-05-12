from __future__ import annotations

TRUTH_HINTS = {
    "task_status": "task_registry",
    "task_existence": "task_registry",
    "task_next_action": "task_registry",
    "user_preference": "curated_memory",
    "identity": "curated_memory",
    "deep_context": "artifact_layer",
    "implementation_detail": "artifact_layer",
    "general_history": "memory_then_artifacts",
}


def resolve_truth_source(question_type: str) -> str:
    return TRUTH_HINTS.get(question_type, "memory_then_artifacts")
