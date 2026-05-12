#!/usr/bin/env python3
"""Markdown-first promotion gate heuristics v0.1.

Evaluates markdown artifacts for possible promotion into a product-facing repo
and emits a machine-readable verdict aligned to promotion_gate_verdict/v1.

Usage:
    python3 scripts/promotion_gate.py path/to/candidate.md
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = "promotion_gate_verdict/v1"
TOOL_VERSION = "0.1.1"
POLICY_VERSION = "promotion-gate-spec-v0.1"
DEFAULT_REPO = "product-repos/agent-architecture-kit"
WEIGHTS = {
    "reusable": 0.30,
    "public_safe": 0.30,
    "generic_enough": 0.15,
    "stable_enough": 0.10,
    "repo_fit": 0.15,
}
POSITIVE_PATTERNS = {
    "reusable": [
        r"\b(purpose|scope|acceptance criteria|contract|schema|policy|mapping|workflow|architecture|roadmap|design constraints)\b",
        r"^#{1,3}\s+",
    ],
    "generic_enough": [
        r"\b(pattern|reference|general|reusable|architecture|contract|policy|example|template)\b",
    ],
    "stable_enough": [
        r"\b(status:\s*(bounded completion|planning artifact|draft|complete|done))\b",
        r"\b(summary|conclusion|acceptance criteria)\b",
    ],
}
NEGATIVE_PATTERNS = {
    "generic_enough": [
        r"\b(this one run only|for this run only|operator chatter|raw transcript|chat dump)\b",
    ],
    "stable_enough": [
        r"\bTODO\b",
        r"\bTBD\b",
        r"\bplaceholder\b",
    ],
}
TOPIC_PATTERNS = {
    "architecture": r"\barchitecture\b",
    "policy": r"\bpolicy\b",
    "schema": r"\bschema\b",
    "workflow": r"\bworkflow\b",
    "memory": r"\bmemory\b",
    "evaluation": r"\bevaluation\b",
}
BLOCKER_PATTERNS = [
    ("secret_assignment", r"(?im)\b(api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*\S+"),
    ("private_key_block", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("private_endpoint", r"(?i)\b(ssh|postgres|mongodb|redis):\/\/\S+"),
    ("private_chat_identifier", r"-100\d{6,}"),
    ("ipv4_address", r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    ("internal_host_path", r"/(home|Users|var|etc)/[^\s`]+"),
]
SANITIZABLE_CODES = {"private_chat_identifier", "ipv4_address", "internal_host_path", "private_endpoint"}
INTERNAL_ONLY_PATTERNS = [
    ("raw_log", r"(?i)\b(raw log|trace dump|session dump)\b"),
    ("credential_note", r"(?i)\b(credentials?\s+note|ssh access|access secret)\b"),
]
BUCKET_RULES = [
    {
        "bucket": "docs/schemas",
        "patterns": [r"\bschema\b", r"\bjson schema\b", r"\bobject model\b", r"\bcontract fields?\b", r"\bverdict schema\b"],
        "path_prefix": "promotion-gates",
        "reason": "schema/contract language aligns with reusable verdict or interface documentation",
    },
    {
        "bucket": "docs/policies",
        "patterns": [r"\bpolicy\b", r"\bguardrail\b", r"\bserving class\b", r"\bownership\b", r"\bdecision posture\b"],
        "path_prefix": "governance",
        "reason": "policy/guardrail framing aligns with governance-oriented documentation",
    },
    {
        "bucket": "docs/evaluation",
        "patterns": [r"\bevaluation\b", r"\bverification\b", r"\bregression\b", r"\bacceptance scenario\b", r"\bfixture\b"],
        "path_prefix": "promotion-gates",
        "reason": "verification/evaluation framing aligns with quality and acceptance documentation",
    },
    {
        "bucket": "docs/examples",
        "patterns": [r"\bexample\b", r"\bworked example\b", r"\btemplate\b", r"\bfixture\b"],
        "path_prefix": "promotion-gates",
        "reason": "example/template framing aligns with reusable example material",
    },
    {
        "bucket": "docs/architecture",
        "patterns": [r"\barchitecture\b", r"\bmapping\b", r"\bworkflow\b", r"\bcontinuation\b", r"\bruntime surface\b", r"\bpromotion gate\b"],
        "path_prefix": "promotion-gates",
        "reason": "architecture/workflow framing aligns with reusable system design documentation",
    },
]
TITLE_DESTINATION_HINTS = [
    (r"\bspec\b", "specs"),
    (r"\bschema\b", "schemas"),
    (r"\bheuristics?\b", "heuristics"),
    (r"\bpolicy\b", "policies"),
    (r"\bexample\b", "examples"),
    (r"\bverification\b", "verification"),
]


@dataclass
class CandidateDoc:
    path: Path
    rel_path: str
    text: str
    title: str | None
    size_bytes: int
    modified_at: str
    content_hash: str


def clamp(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "artifact"


def load_candidate(raw_path: str) -> CandidateDoc:
    path = Path(raw_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Candidate not found: {raw_path}")
    if path.suffix.lower() not in {".md", ".markdown"}:
        raise ValueError(f"Unsupported artifact type in v0.1: {path.suffix or '<none>'}")
    text = path.read_text(encoding="utf-8")
    rel_path = str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
    stat = path.stat()
    title = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            break
    content_hash = "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
    modified_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
    return CandidateDoc(
        path=path,
        rel_path=rel_path,
        text=text,
        title=title,
        size_bytes=stat.st_size,
        modified_at=modified_at,
        content_hash=content_hash,
    )


def count_matches(patterns: list[str], text: str) -> int:
    return sum(len(re.findall(pattern, text, flags=re.MULTILINE)) for pattern in patterns)


def find_messages(pattern_specs: list[tuple[str, str]], text: str, severity: str, prefix: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for code, pattern in pattern_specs:
        matches = re.findall(pattern, text)
        if not matches:
            continue
        sample = matches[:3]
        evidence = [str(m) if not isinstance(m, tuple) else " ".join(str(x) for x in m) for m in sample]
        items.append(
            {
                "code": code,
                "message": f"{prefix}: {code.replace('_', ' ')}",
                "severity": severity,
                "evidence": evidence,
            }
        )
    return items


def score_reusable(text: str) -> tuple[float, list[str]]:
    reasons: list[str] = []
    section_count = len(re.findall(r"^#{1,3}\s+", text, flags=re.MULTILINE))
    keyword_hits = count_matches(POSITIVE_PATTERNS["reusable"], text.lower())
    score = 0.20 + min(section_count, 10) * 0.04 + min(keyword_hits, 12) * 0.035
    if section_count >= 3:
        reasons.append("document is structured into reusable sections")
    if keyword_hits >= 4:
        reasons.append("document uses contract/policy/schema-oriented language")
    if re.search(r"\b(run log|diary|scratchpad)\b", text, flags=re.IGNORECASE):
        score -= 0.25
    return clamp(score), reasons


def score_public_safe(doc: CandidateDoc, blockers: list[dict[str, Any]]) -> tuple[float, list[str], list[str]]:
    reasons: list[str] = []
    warnings: list[str] = []
    score = 0.95
    if not blockers:
        reasons.append("no obvious sensitive publication blockers detected")
    for blocker in blockers:
        code = blocker["code"]
        if code in SANITIZABLE_CODES:
            score -= 0.18
            warnings.append(f"contains sanitizable sensitive detail: {code}")
        else:
            score -= 0.45
            warnings.append(f"contains stronger sensitive signal: {code}")
    if doc.size_bytes > 50_000:
        score -= 0.05
        warnings.append("large document size may hide local operational residue")
    return clamp(score), reasons, warnings


def score_generic(text: str) -> tuple[float, list[str], list[str]]:
    reasons: list[str] = []
    warnings: list[str] = []
    positive_hits = count_matches(POSITIVE_PATTERNS["generic_enough"], text.lower())
    negative_hits = count_matches(NEGATIVE_PATTERNS["generic_enough"], text.lower())
    local_hits = len(re.findall(r"\b(task-\d+|session|operator|workspace)\b", text, flags=re.IGNORECASE))
    score = 0.42 + min(positive_hits, 10) * 0.05 - min(negative_hits, 3) * 0.18 - min(local_hits, 6) * 0.025
    if positive_hits >= 3:
        reasons.append("language is framed as patterns/reference material")
    if local_hits >= 6:
        warnings.append("contains notable local task/session framing")
    return clamp(score), reasons, warnings


def score_stable(text: str) -> tuple[float, list[str], list[str]]:
    reasons: list[str] = []
    warnings: list[str] = []
    heading_count = len(re.findall(r"^#{1,3}\s+", text, flags=re.MULTILINE))
    positive_hits = count_matches(POSITIVE_PATTERNS["stable_enough"], text.lower())
    negative_hits = count_matches(NEGATIVE_PATTERNS["stable_enough"], text)
    score = 0.30 + min(heading_count, 10) * 0.04 + min(positive_hits, 6) * 0.06 - min(negative_hits, 5) * 0.12
    if positive_hits >= 2:
        reasons.append("document includes bounded completion or acceptance framing")
    if negative_hits:
        warnings.append("document still contains unresolved TODO/TBD markers")
    return clamp(score), reasons, warnings


def infer_destination_subdir(doc: CandidateDoc, bucket: str) -> str | None:
    source = (doc.title or doc.path.stem).lower()
    for pattern, subdir in TITLE_DESTINATION_HINTS:
        if re.search(pattern, source, flags=re.IGNORECASE):
            return f"{bucket}/{subdir}"
    if "promotion gate" in source:
        return f"{bucket}/promotion-gates"
    return None


def suggest_destination(doc: CandidateDoc, text: str) -> tuple[dict[str, Any], float, list[str], list[str]]:
    lowered = text.lower()
    reasons: list[str] = []
    warnings: list[str] = []
    scored: list[tuple[int, str, str, str | None]] = []

    for rule in BUCKET_RULES:
        hits = sum(len(re.findall(pattern, lowered, flags=re.IGNORECASE)) for pattern in rule["patterns"])
        if hits:
            scored.append((hits, rule["bucket"], rule["reason"], rule["path_prefix"]))

    scored.sort(key=lambda item: item[0], reverse=True)
    if not scored:
        return {
            "repo": DEFAULT_REPO,
            "bucket": None,
            "path": None,
            "rationale": "no clear destination bucket inferred from bounded v0.1 heuristics",
        }, 0.2, ["destination bucket is ambiguous"], []

    best_hits, best_bucket, best_reason, best_prefix = scored[0]
    second_hits = scored[1][0] if len(scored) > 1 else 0
    slug_source = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "", doc.title or doc.path.stem)
    clean_slug = slugify(slug_source)

    subdir = infer_destination_subdir(doc, best_bucket)
    if subdir:
        destination_path = f"{subdir}/{clean_slug}.md"
    elif best_prefix:
        destination_path = f"{best_bucket}/{best_prefix}/{clean_slug}.md"
    else:
        destination_path = f"{best_bucket}/{clean_slug}.md"

    reasons.append(f"maps most strongly to {best_bucket}")
    reasons.append(best_reason)

    if second_hits and best_hits - second_hits <= 1:
        warnings.append("multiple destination buckets scored similarly")
        reasons.append("best bucket selected conservatively from competing repo-fit signals")

    score = 0.48 + min(best_hits, 8) * 0.06
    if second_hits and best_hits - second_hits <= 1:
        score -= 0.08
    score = clamp(score)

    rationale = f"best bucket is {best_bucket} based on bounded topic and title heuristics"
    if warnings:
        rationale += "; competing buckets remain plausible"

    return {
        "repo": DEFAULT_REPO,
        "bucket": best_bucket,
        "path": destination_path,
        "rationale": rationale,
    }, score, reasons, warnings


def detect_topics(text: str) -> list[str]:
    lowered = text.lower()
    return [topic for topic, pattern in TOPIC_PATTERNS.items() if re.search(pattern, lowered, flags=re.IGNORECASE)]


def build_message(code: str, message: str, severity: str = "info", evidence: list[str] | None = None, suggested_fix: str | None = None) -> dict[str, Any]:
    item: dict[str, Any] = {"code": code, "message": message, "severity": severity, "evidence": evidence or []}
    if suggested_fix:
        item["suggested_fix"] = suggested_fix
    return item


def choose_next_action(verdict: str, *, hard_block_present: bool, sanitizable_only: bool, suggested_destination: dict[str, Any], internal_only: list[dict[str, Any]], ambiguity_flags: list[str]) -> dict[str, Any]:
    destination_path = suggested_destination.get("path")
    bucket = suggested_destination.get("bucket")

    if verdict == "promote":
        action = {
            "code": "copy_or_rewrite_for_product_repo",
            "summary": "Prepare this artifact for product-repo placement with light editorial cleanup.",
            "owner_hint": "architecture-owner",
            "prerequisites": ["perform product-repo wording cleanup if needed"],
        }
        if destination_path:
            action["target_path"] = destination_path
            action["summary"] = f"Prepare this artifact for direct placement into {destination_path} after light editorial cleanup."
        return action

    if verdict == "sanitize_then_promote":
        prerequisites = ["remove environment-specific identifiers/paths/addresses"] if sanitizable_only or hard_block_present else []
        action = {
            "code": "sanitize_then_rerun_gate",
            "summary": "Create a sanitized derivative, then rerun the gate before any product-repo promotion.",
            "owner_hint": "architecture-owner",
            "prerequisites": prerequisites,
        }
        if destination_path:
            action["target_path_after_sanitization"] = destination_path
            action["summary"] = f"Create a sanitized derivative targeted at {destination_path}, then rerun the gate before promotion."
        if bucket:
            action["rewrite_scope"] = f"generalize content for {bucket}"
        return action

    if verdict == "hold_internal":
        action = {
            "code": "retain_internal_reference",
            "summary": "Keep the artifact internal; do not prepare product-repo promotion in this contour.",
            "owner_hint": "task-owner",
        }
        if internal_only:
            action["rationale"] = "internal-only or operational evidence signals outweigh reuse value"
        return action

    action = {
        "code": "request_architecture_review",
        "summary": "Escalate for architecture review before promotion or rewrite work proceeds.",
        "owner_hint": "architecture-owner",
    }
    questions: list[str] = []
    if "destination_competing_buckets" in ambiguity_flags:
        questions.append("Which destination bucket should own the promoted derivative?")
    if "sanitize_scope_unclear" in ambiguity_flags:
        questions.append("Can the sensitive details be removed without losing the reusable core?")
    if "quality_threshold_mix" in ambiguity_flags:
        questions.append("Should this be rewritten further before any promotion attempt?")
    if questions:
        action["review_questions"] = questions
    if destination_path:
        action["proposed_target_path"] = destination_path
    return action


def evaluate_candidate(doc: CandidateDoc) -> dict[str, Any]:
    text = doc.text
    blockers = find_messages(BLOCKER_PATTERNS, text, "high", "sensitive signal detected")
    internal_only = find_messages(INTERNAL_ONLY_PATTERNS, text, "medium", "internal-only signal detected")
    if re.search(r"(?i)(backup|credentials?)", doc.rel_path):
        internal_only.append(build_message("internal_path_signal", "internal-only signal detected from artifact path/name", severity="medium", evidence=[doc.rel_path]))

    reusable, reusable_reasons = score_reusable(text)
    public_safe, public_reasons, public_warnings = score_public_safe(doc, blockers)
    generic_enough, generic_reasons, generic_warnings = score_generic(text)
    stable_enough, stable_reasons, stable_warnings = score_stable(text)
    suggested_destination, repo_fit, repo_reasons, repo_warnings = suggest_destination(doc, text)

    dimensions = {
        "reusable": reusable,
        "public_safe": public_safe,
        "generic_enough": generic_enough,
        "stable_enough": stable_enough,
        "repo_fit": repo_fit,
    }
    aggregate = clamp(sum(dimensions[key] * WEIGHTS[key] for key in WEIGHTS))

    reasons = [build_message("reusable_structure", msg) for msg in reusable_reasons]
    reasons += [build_message("public_safe_clean", msg) for msg in public_reasons]
    reasons += [build_message("generic_framing", msg) for msg in generic_reasons]
    reasons += [build_message("stable_framing", msg) for msg in stable_reasons]
    reasons += [build_message("repo_fit", msg) for msg in repo_reasons]
    if not reasons:
        reasons.append(build_message("bounded_heuristic_summary", "bounded heuristics completed with mixed signals"))

    warnings = [build_message("public_safe_warning", msg, severity="medium") for msg in public_warnings]
    warnings += [build_message("generic_warning", msg, severity="medium") for msg in generic_warnings]
    warnings += [build_message("stable_warning", msg, severity="medium") for msg in stable_warnings]
    warnings += [build_message("repo_fit_warning", msg, severity="medium") for msg in repo_warnings]

    hard_block_present = bool(blockers)
    sanitizable_only = hard_block_present and all(item["code"] in SANITIZABLE_CODES for item in blockers)
    inherently_internal = bool(internal_only) or reusable < 0.45 or repo_fit < 0.35

    ambiguity_flags: list[str] = []
    review_needed = False
    review_reason_codes: list[str] = []
    review_questions: list[str] = []

    if suggested_destination["path"] is None:
        ambiguity_flags.append("destination_unclear")
    if any(item["code"] == "repo_fit_warning" for item in warnings):
        ambiguity_flags.append("destination_competing_buckets")
    if hard_block_present and not sanitizable_only and reusable >= 0.7 and repo_fit >= 0.6:
        ambiguity_flags.append("sanitize_scope_unclear")
    verdict_mix = reusable >= 0.70 and repo_fit >= 0.60 and (generic_enough < 0.60 or stable_enough < 0.55)
    if not inherently_internal and verdict_mix:
        ambiguity_flags.append("quality_threshold_mix")

    if hard_block_present and reusable >= 0.7 and repo_fit >= 0.6 and sanitizable_only:
        verdict = "sanitize_then_promote"
    elif hard_block_present and reusable >= 0.7 and repo_fit >= 0.6:
        verdict = "needs_review"
        review_needed = True
        review_reason_codes.append("non_sanitizable_or_unclear_blockers")
        review_questions.append("Can the sensitive or environment-bound details be removed without losing the reusable core?")
    elif hard_block_present and inherently_internal:
        verdict = "hold_internal"
    elif reusable >= 0.70 and public_safe >= 0.85 and repo_fit >= 0.60 and generic_enough >= 0.60 and stable_enough >= 0.55 and aggregate >= 0.72:
        verdict = "promote"
    elif reusable >= 0.70 and repo_fit >= 0.60 and public_safe < 0.85 and sanitizable_only:
        verdict = "sanitize_then_promote"
    elif reusable < 0.45 or repo_fit < 0.35:
        verdict = "hold_internal"
    else:
        verdict = "needs_review"
        review_needed = True
        review_reason_codes.append("mixed_dimension_scores")
        review_questions.append("Should this be generalized further before any promotion decision?")

    if suggested_destination["path"] is None and verdict == "promote":
        verdict = "needs_review"
        review_needed = True
        review_reason_codes.append("destination_unclear")
        review_questions.append("Which product-repo bucket should own this artifact?")

    if "destination_competing_buckets" in ambiguity_flags and verdict in {"promote", "sanitize_then_promote"}:
        verdict = "needs_review"
        review_needed = True
        review_reason_codes.append("competing_destination_buckets")
        review_questions.append("Which competing destination bucket should own the promoted derivative?")

    next_action = choose_next_action(
        verdict,
        hard_block_present=hard_block_present,
        sanitizable_only=sanitizable_only,
        suggested_destination=suggested_destination,
        internal_only=internal_only,
        ambiguity_flags=ambiguity_flags,
    )

    confidence_value = aggregate
    if hard_block_present:
        confidence_value = min(confidence_value, 0.78)
    if verdict == "needs_review":
        confidence_value = min(confidence_value, 0.66)
    if verdict == "hold_internal" and inherently_internal:
        confidence_value = max(confidence_value, 0.62)
    confidence_level = "high" if confidence_value >= 0.8 else "medium" if confidence_value >= 0.55 else "low"

    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "candidate": {
            "path": doc.rel_path,
            "artifact_type": "markdown",
            "title": doc.title,
            "content_hash": doc.content_hash,
            "size_bytes": doc.size_bytes,
            "modified_at": doc.modified_at,
        },
        "verdict": verdict,
        "score": {
            "aggregate": aggregate,
            "dimensions": dimensions,
            "weights": WEIGHTS,
            "hard_block_present": hard_block_present,
            "threshold_profile": "promotion-gate-v0.1-markdown",
        },
        "reasons": reasons,
        "warnings": warnings,
        "blockers": blockers,
        "suggested_destination": suggested_destination,
        "next_action": next_action,
        "confidence": {
            "level": confidence_level,
            "value": clamp(confidence_value),
            "ambiguity_flags": sorted(set(ambiguity_flags)),
            "notes": "Deterministic markdown-first heuristic pass.",
        },
        "review": {
            "needed": review_needed,
            "reason_codes": sorted(set(review_reason_codes)),
            "questions": review_questions,
        },
        "provenance": {
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "tool_name": "scripts/architecture/promotion_gate.py",
            "tool_version": TOOL_VERSION,
            "policy_version": POLICY_VERSION,
        },
        "source_signals": sorted({item["code"] for item in blockers + internal_only}),
        "detected_topics": detect_topics(text),
        "normalization_notes": ["Input treated as markdown text without semantic rewrite."],
        "sanitization_hints": [
            "Replace exact internal paths with generic placeholders.",
            "Remove internal identifiers, private addresses, and environment-specific values.",
            "Rewrite repo-targeted language so the derivative reads as a product-facing reference.",
        ] if sanitizable_only else [],
        "internal_only_notes": [item["message"] for item in internal_only],
    }
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate markdown artifacts for promotion readiness")
    parser.add_argument("candidates", nargs="+", help="Markdown file path(s) to evaluate")
    parser.add_argument("--output", help="Optional output path. For multiple candidates, writes a JSON array.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        results = [evaluate_candidate(load_candidate(candidate)) for candidate in args.candidates]
    except (FileNotFoundError, ValueError, UnicodeDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    payload: Any = results[0] if len(results) == 1 else results
    rendered = json.dumps(payload, ensure_ascii=False, indent=2 if args.pretty or args.output else None)
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = (ROOT / output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered + "\n", encoding="utf-8")
        print(str(output_path.relative_to(ROOT)) if output_path.is_relative_to(ROOT) else str(output_path))
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
