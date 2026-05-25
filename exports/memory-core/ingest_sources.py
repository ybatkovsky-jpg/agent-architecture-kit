#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_STATE = ROOT / "state" / "ingestion_state.json"
DEFAULT_REGISTRY = ROOT / "config" / "source_registry.seed.yaml"
DEFAULT_ENV_FILE = ROOT / "config" / "memory.env"

TEXT_EXTS = {".md", ".txt", ".rst"}
CODE_EXTS = {".py", ".js", ".ts", ".tsx", ".jsx", ".sh"}
CHAT_EXTS = {".json"}
DOC_EXTS = {".pdf", ".docx"}


@dataclass
class DocumentRecord:
    document_id: str
    source_id: str
    path: str
    document_type: str
    title: str
    content_hash: str
    raw_text: str
    chunks: list[dict[str, Any]]
    metadata: dict[str, Any]


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def stable_id(prefix: str, seed: str) -> str:
    return f"{prefix}_{sha1_text(seed)[:16]}"


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"documents": {}, "runs": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value.strip("\"'")


def load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def load_registry(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Registry file not found: {path}")

    lines = path.read_text(encoding="utf-8").splitlines()
    sources: list[dict[str, Any]] = []
    top: dict[str, Any] = {}
    current: dict[str, Any] | None = None
    current_multiline_key: str | None = None
    current_multiline_indent = 0
    multiline_buffer: list[str] = []

    def flush_multiline() -> None:
        nonlocal current_multiline_key, current_multiline_indent, multiline_buffer
        if current_multiline_key is None or current is None:
            return
        current[current_multiline_key] = "\n".join(multiline_buffer).strip()
        current_multiline_key = None
        current_multiline_indent = 0
        multiline_buffer = []

    for raw_line in lines:
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = raw_line.strip()

        if current_multiline_key is not None:
            if indent > current_multiline_indent:
                multiline_buffer.append(raw_line[current_multiline_indent:].rstrip())
                continue
            flush_multiline()

        if stripped == "sources:":
            continue

        if stripped.startswith("- "):
            flush_multiline()
            current = {}
            sources.append(current)
            stripped = stripped[2:]
            if stripped:
                key, value = stripped.split(":", 1)
                current[key.strip()] = parse_scalar(value)
            continue

        if ":" not in stripped:
            continue

        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        target = current if current is not None and indent >= 2 else top

        if value in {">-", "|", ">"}:
            if target is top:
                top[key] = ""
                current = None
            else:
                current_multiline_key = key
                current_multiline_indent = indent + 2
                multiline_buffer = []
            continue

        target[key] = parse_scalar(value)

    flush_multiline()
    top["sources"] = sources
    return top


def infer_document_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTS:
        return "markdown" if suffix == ".md" else "text"
    if suffix in CODE_EXTS:
        return "code"
    if suffix in CHAT_EXTS and "chat" in {part.lower() for part in path.parts}:
        return "chat"
    if suffix in DOC_EXTS:
        return "binary_document"
    return "text"


def parse_chat_json(text: str) -> list[dict[str, Any]]:
    payload = json.loads(text)
    chunks = []
    buffer: list[str] = []
    start = None
    end = None
    for idx, row in enumerate(payload, start=1):
        speaker = row.get("speaker", "unknown")
        timestamp = row.get("timestamp", "")
        body = row.get("text", "")
        if start is None:
            start = timestamp
        end = timestamp
        buffer.append(f"[{timestamp}] {speaker}: {body}".strip())
        if len(buffer) >= 2 or idx == len(payload):
            chunk_text = "\n".join(buffer).strip()
            chunks.append({
                "section_path": f"messages:{idx-len(buffer)+1}-{idx}",
                "chunk_text": chunk_text,
                "metadata": {"window_start": start or "", "window_end": end or "", "message_count": len(buffer)},
            })
            buffer = []
            start = None
    return chunks


def parse_text_sections(text: str) -> list[dict[str, Any]]:
    sections: list[dict[str, Any]] = []
    current_title = "body"
    current_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            if current_lines:
                sections.append({"section_path": current_title, "chunk_text": "\n".join(current_lines).strip(), "metadata": {}})
            current_title = line.lstrip("# ").strip() or "section"
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_lines:
        sections.append({"section_path": current_title, "chunk_text": "\n".join(current_lines).strip(), "metadata": {}})
    return [s for s in sections if s["chunk_text"].strip()]


def parse_code_chunks(text: str) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current_name = "module"
    current_lines: list[str] = []
    pattern = re.compile(r"^(def|class)\s+([A-Za-z_][A-Za-z0-9_]*)")
    for line in text.splitlines():
        match = pattern.match(line)
        if match and current_lines:
            chunks.append({"section_path": current_name, "chunk_text": "\n".join(current_lines).strip(), "metadata": {"symbol": current_name}})
            current_name = match.group(2)
            current_lines = [line]
        else:
            if match:
                current_name = match.group(2)
            current_lines.append(line)
    if current_lines:
        chunks.append({"section_path": current_name, "chunk_text": "\n".join(current_lines).strip(), "metadata": {"symbol": current_name}})
    return [c for c in chunks if c["chunk_text"].strip()]


def build_document(path: Path, source_root: Path, source_id: str) -> DocumentRecord:
    rel_path = str(path.relative_to(source_root))
    text = path.read_text(encoding="utf-8")
    document_type = infer_document_type(path)
    if document_type == "chat":
        raw_chunks = parse_chat_json(text)
    elif document_type == "code":
        raw_chunks = parse_code_chunks(text)
    else:
        raw_chunks = parse_text_sections(text)
    chunks = []
    for ordinal, raw in enumerate(raw_chunks, start=1):
        chunk_text = raw["chunk_text"].strip()
        chunks.append({
            "chunk_id": stable_id("chk", f"{source_id}:{rel_path}:{ordinal}:{chunk_text}"),
            "chunk_ordinal": ordinal,
            "section_path": raw["section_path"],
            "chunk_text": chunk_text,
            "content_hash": sha1_text(chunk_text),
            "char_count": len(chunk_text),
            "token_count": max(1, len(chunk_text.split())),
            "metadata": raw.get("metadata") or {},
        })
    title = path.stem.replace("-", " ").replace("_", " ").strip() or path.name
    return DocumentRecord(
        document_id=stable_id("doc", f"{source_id}:{rel_path}"),
        source_id=source_id,
        path=rel_path,
        document_type=document_type,
        title=title,
        content_hash=sha1_text(text),
        raw_text=text,
        chunks=chunks,
        metadata={"suffix": path.suffix.lower()},
    )


def should_include_path(path: Path) -> bool:
    if path.name.startswith("."):
        return False
    return path.suffix.lower() in TEXT_EXTS | CODE_EXTS | CHAT_EXTS


def sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("'", "''")
    return f"'{text}'"


def sql_json(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False).replace("'", "''")
    return f"'{payload}'::jsonb"


def ensure_psql_env(env_file: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(load_env_file(env_file))
    required = ["PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD"]
    missing = [name for name in required if not env.get(name)]
    if missing:
        raise RuntimeError(f"Missing PostgreSQL env vars: {', '.join(missing)}")
    return env


def fetch_existing_document_ids_for_source(source_id: str, env_file: Path) -> set[str]:
    env = ensure_psql_env(env_file)
    result = subprocess.run(
        [
            "psql", "-X", "-A", "-t",
            "-h", env["PGHOST"], "-p", env["PGPORT"], "-U", env["PGUSER"], "-d", env["PGDATABASE"],
            "-c", "SELECT document_id FROM documents WHERE source_id = "
            f"'{source_id.replace(chr(39), chr(39) * 2)}' AND is_deleted = FALSE;",
        ],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def build_source_upsert_sql(source: dict[str, Any]) -> str:
    source_id = stable_id("src", str(source.get("key", source.get("root_path", "unknown"))))
    return f"""
INSERT INTO sources (
    source_id, source_type, root_path, parser_type, trust_level, config_json,
    enabled, retrieval_scope, owner, last_seen_at
) VALUES (
    {sql_literal(source_id)},
    {sql_literal(source.get('source_type', 'project_knowledge'))},
    {sql_literal(source.get('root_path', ''))},
    {sql_literal(source.get('parser_type', 'mixed_tree'))},
    {sql_literal(source.get('trust_level', 'normal'))},
    {sql_json({'key': source.get('key', ''), 'notes': source.get('notes', ''), 'include_glob': source.get('include_glob', '')})},
    {sql_literal(bool(source.get('enabled', False)))},
    {sql_literal(source.get('retrieval_scope', 'global'))},
    {sql_literal(source.get('owner', ''))},
    NOW()
)
ON CONFLICT (source_id) DO UPDATE SET
    source_type = EXCLUDED.source_type,
    root_path = EXCLUDED.root_path,
    parser_type = EXCLUDED.parser_type,
    trust_level = EXCLUDED.trust_level,
    config_json = EXCLUDED.config_json,
    enabled = EXCLUDED.enabled,
    retrieval_scope = EXCLUDED.retrieval_scope,
    owner = EXCLUDED.owner,
    last_seen_at = NOW();
""".strip()


def build_document_upsert_sql(record: DocumentRecord) -> str:
    return f"""
INSERT INTO documents (
    document_id, source_id, title, path, document_type,
    content_hash, metadata_json, raw_text, mime_type, is_deleted, ingested_at
) VALUES (
    {sql_literal(record.document_id)},
    {sql_literal(record.source_id)},
    {sql_literal(record.title)},
    {sql_literal(record.path)},
    {sql_literal(record.document_type)},
    {sql_literal(record.content_hash)},
    {sql_json(record.metadata)},
    {sql_literal(record.raw_text)},
    'text/plain',
    FALSE,
    NOW()
)
ON CONFLICT (document_id) DO UPDATE SET
    source_id = EXCLUDED.source_id,
    title = EXCLUDED.title,
    path = EXCLUDED.path,
    document_type = EXCLUDED.document_type,
    content_hash = EXCLUDED.content_hash,
    metadata_json = EXCLUDED.metadata_json,
    raw_text = EXCLUDED.raw_text,
    mime_type = EXCLUDED.mime_type,
    is_deleted = FALSE,
    ingested_at = NOW();
""".strip()


def build_chunk_replace_sql(record: DocumentRecord) -> str:
    statements = [f"DELETE FROM chunks WHERE document_id = {sql_literal(record.document_id)};"]
    for chunk in record.chunks:
        statements.append(
            f"""
INSERT INTO chunks (
    chunk_id, document_id, chunk_ordinal, section_path,
    token_count, char_count, content_hash, chunk_text, metadata_json
) VALUES (
    {sql_literal(chunk['chunk_id'])},
    {sql_literal(record.document_id)},
    {sql_literal(chunk['chunk_ordinal'])},
    {sql_literal(chunk['section_path'])},
    {sql_literal(chunk['token_count'])},
    {sql_literal(chunk['char_count'])},
    {sql_literal(chunk['content_hash'])},
    {sql_literal(chunk['chunk_text'])},
    {sql_json(chunk.get('metadata') or {})}
);
""".strip()
        )
    return "\n".join(statements)


def build_ingestion_run_sql(run: dict[str, Any]) -> str:
    details = {
        'changed_paths': run.get('changed_paths', []),
        'skipped_paths': run.get('skipped_paths', []),
        'source_root': run.get('source_root', ''),
        'source_key': run.get('source_key', ''),
    }
    return f"""
INSERT INTO ingestion_runs (
    run_id, source_id, trigger_type, started_at, finished_at, status,
    docs_seen, docs_changed, docs_failed, chunks_upserted, error_summary, details_json
) VALUES (
    {sql_literal(run['run_id'])},
    {sql_literal(run['source_id'])},
    'manual_registry_ingest',
    NOW(),
    NOW(),
    {sql_literal(run.get('status', 'ok'))},
    {sql_literal(run.get('docs_seen', 0))},
    {sql_literal(run.get('docs_changed', 0))},
    0,
    {sql_literal(run.get('chunks_upserted', 0))},
    '',
    {sql_json(details)}
)
ON CONFLICT (run_id) DO UPDATE SET
    finished_at = EXCLUDED.finished_at,
    status = EXCLUDED.status,
    docs_seen = EXCLUDED.docs_seen,
    docs_changed = EXCLUDED.docs_changed,
    docs_failed = EXCLUDED.docs_failed,
    chunks_upserted = EXCLUDED.chunks_upserted,
    error_summary = EXCLUDED.error_summary,
    details_json = EXCLUDED.details_json;
""".strip()


def persist_run_to_postgres(run: dict[str, Any], source: dict[str, Any], changed_records: list[DocumentRecord], env_file: Path, dry_run_sql: Path | None = None) -> dict[str, Any]:
    sql_parts = ["BEGIN;", build_source_upsert_sql(source)]
    for record in changed_records:
        sql_parts.append(build_document_upsert_sql(record))
        sql_parts.append(build_chunk_replace_sql(record))
    sql_parts.append(build_ingestion_run_sql(run))
    sql_parts.append("COMMIT;")
    sql_script = "\n\n".join(sql_parts) + "\n"

    if dry_run_sql is not None:
        dry_run_sql.parent.mkdir(parents=True, exist_ok=True)
        dry_run_sql.write_text(sql_script, encoding="utf-8")
        return {"mode": "sql_dump", "path": str(dry_run_sql)}

    env = ensure_psql_env(env_file)

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".sql", delete=False) as handle:
        handle.write(sql_script)
        sql_path = Path(handle.name)

    try:
        result = subprocess.run(
            [
                "psql", "-v", "ON_ERROR_STOP=1", "-X",
                "-h", env["PGHOST"], "-p", env["PGPORT"], "-U", env["PGUSER"], "-d", env["PGDATABASE"],
                "-f", str(sql_path),
            ],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        return {"mode": "postgres", "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "Postgres persistence failed\n"
            f"SQL file: {sql_path}\n"
            f"STDOUT:\n{exc.stdout}\n"
            f"STDERR:\n{exc.stderr}"
        ) from exc
    finally:
        sql_path.unlink(missing_ok=True)


def ingest_source(
    source_root: Path,
    source_key: str,
    state: dict[str, Any],
    repair_missing_document_ids: set[str] | None = None,
) -> tuple[dict[str, Any], list[DocumentRecord]]:
    source_id = stable_id("src", source_key)
    docs_seen = 0
    docs_changed = 0
    docs_skipped = 0
    chunks_upserted = 0
    repaired_missing_docs = 0
    changed_paths: list[str] = []
    skipped_paths: list[str] = []
    repaired_paths: list[str] = []
    changed_records: list[DocumentRecord] = []

    documents_state = state.setdefault("documents", {})
    for path in sorted(source_root.rglob("*")):
        if not path.is_file() or not should_include_path(path):
            continue
        docs_seen += 1
        record = build_document(path, source_root, source_id)
        previous = documents_state.get(record.document_id)
        previous_hash = (previous or {}).get("content_hash")
        previous_chunk_hashes = [chunk.get("content_hash") for chunk in (previous or {}).get("chunks", [])]
        current_chunk_hashes = [chunk.get("content_hash") for chunk in record.chunks]
        state_unchanged = previous_hash == record.content_hash and previous_chunk_hashes == current_chunk_hashes
        db_missing = repair_missing_document_ids is not None and record.document_id in repair_missing_document_ids
        if state_unchanged and not db_missing:
            docs_skipped += 1
            skipped_paths.append(record.path)
            continue
        docs_changed += 1
        chunks_upserted += len(record.chunks)
        changed_paths.append(record.path)
        changed_records.append(record)
        if db_missing:
            repaired_missing_docs += 1
            repaired_paths.append(record.path)
        documents_state[record.document_id] = {
            "source_id": record.source_id,
            "source_key": source_key,
            "path": record.path,
            "title": record.title,
            "document_type": record.document_type,
            "content_hash": record.content_hash,
            "metadata": record.metadata,
            "chunks": record.chunks,
        }

    run = {
        "run_id": stable_id("run", f"{source_id}:{docs_seen}:{docs_changed}:{chunks_upserted}:{len(state.get('runs', []))}"),
        "source_id": source_id,
        "source_key": source_key,
        "source_root": str(source_root),
        "docs_seen": docs_seen,
        "docs_changed": docs_changed,
        "docs_skipped": docs_skipped,
        "chunks_upserted": chunks_upserted,
        "changed_paths": changed_paths,
        "skipped_paths": skipped_paths,
        "repaired_missing_docs": repaired_missing_docs,
        "repaired_paths": repaired_paths,
    }
    state.setdefault("runs", []).append(run)
    return run, changed_records


PHASE1_ALLOWED_SOURCE_TYPES = {"shared_memory", "project_knowledge"}
PHASE1_ALLOWED_RETRIEVAL_SCOPES = {"global"}


def phase1_policy_status(source: dict[str, Any], include_disabled: bool, allow_nonphase1_policy: bool) -> str:
    enabled = bool(source.get("enabled", False))
    if not enabled and not include_disabled:
        return "excluded_disabled"
    if allow_nonphase1_policy:
        return "allowed"

    source_type = str(source.get("source_type", "")).strip()
    retrieval_scope = str(source.get("retrieval_scope", "")).strip()

    if source_type not in PHASE1_ALLOWED_SOURCE_TYPES:
        return f"excluded_source_type:{source_type or 'unspecified'}"
    if retrieval_scope not in PHASE1_ALLOWED_RETRIEVAL_SCOPES:
        return f"excluded_retrieval_scope:{retrieval_scope or 'unspecified'}"
    return "allowed"


def ingest_registry_sources(
    workspace_root: Path,
    registry: dict[str, Any],
    state: dict[str, Any],
    include_disabled: bool = False,
    persist_mode: str = "state",
    env_file: Path | None = None,
    sql_dump_dir: Path | None = None,
    allow_nonphase1_policy: bool = False,
) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for source in registry.get("sources", []):
        root_value = str(source.get("root_path", "")).strip()
        source_key = str(source.get("key", root_value))
        source_id = stable_id("src", source_key)
        policy_status = phase1_policy_status(source, include_disabled, allow_nonphase1_policy)
        if policy_status == "excluded_disabled":
            continue
        if policy_status != "allowed":
            runs.append({
                "run_id": stable_id("run", f"policy:{source_key}:{policy_status}"),
                "source_id": source_id,
                "source_key": source_key,
                "source_root": str((workspace_root / root_value).resolve()) if root_value else "",
                "status": policy_status,
                "docs_seen": 0,
                "docs_changed": 0,
                "docs_skipped": 0,
                "chunks_upserted": 0,
                "changed_paths": [],
                "skipped_paths": [],
            })
            continue
        if not root_value or "*" in root_value:
            runs.append({
                "run_id": stable_id("run", f"unsupported:{source_key}"),
                "source_id": source_id,
                "source_key": source_key,
                "source_root": root_value,
                "status": "unsupported_root_path_pattern",
                "docs_seen": 0,
                "docs_changed": 0,
                "docs_skipped": 0,
                "chunks_upserted": 0,
                "changed_paths": [],
                "skipped_paths": [],
            })
            continue
        source_root = (workspace_root / root_value).resolve()
        if not source_root.exists() or not source_root.is_dir():
            runs.append({
                "run_id": stable_id("run", f"missing:{source_key}"),
                "source_id": source_id,
                "source_key": source_key,
                "source_root": str(source_root),
                "status": "missing_source_root",
                "docs_seen": 0,
                "docs_changed": 0,
                "docs_skipped": 0,
                "chunks_upserted": 0,
                "changed_paths": [],
                "skipped_paths": [],
            })
            continue
        repair_missing_document_ids = None
        if persist_mode == "psql":
            existing_document_ids = fetch_existing_document_ids_for_source(source_id, env_file or DEFAULT_ENV_FILE)
            source_document_ids = {
                document_id
                for document_id, doc_state in state.get("documents", {}).items()
                if doc_state.get("source_id") == source_id
            }
            repair_missing_document_ids = source_document_ids - existing_document_ids
        run, changed_records = ingest_source(source_root, source_key, state, repair_missing_document_ids=repair_missing_document_ids)
        run["status"] = "ok"
        if persist_mode == "psql":
            persist_result = persist_run_to_postgres(run, source, changed_records, env_file or DEFAULT_ENV_FILE)
            run["persist_result"] = persist_result
        elif persist_mode == "sql-dump":
            target_dir = sql_dump_dir or (ROOT / "state" / "sql-dumps")
            dump_path = target_dir / f"{run['source_key']}-{run['run_id']}.sql"
            persist_result = persist_run_to_postgres(run, source, changed_records, env_file or DEFAULT_ENV_FILE, dry_run_sql=dump_path)
            run["persist_result"] = persist_result
        else:
            run["persist_result"] = {"mode": "state"}
        runs.append(run)
    return runs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Incremental PKM ingestion prototype for approved local sources")
    parser.add_argument("source_root", nargs="?", help="Single source root to ingest directly (legacy mode)")
    parser.add_argument("--state-file", default=str(DEFAULT_STATE))
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY), help="Registry YAML describing approved source roots")
    parser.add_argument("--workspace-root", default=str(ROOT.parent), help="Workspace root against which registry root_path values are resolved")
    parser.add_argument("--include-disabled", action="store_true", help="Also surface disabled registry roots during audit, but phase-1 policy still excludes non-global/non-approved source classes unless explicitly overridden")
    parser.add_argument("--allow-nonphase1-policy", action="store_true", help="Override the phase-1 safeguard and permit non-global or non-approved source classes to ingest explicitly")
    parser.add_argument("--persist-mode", choices=["state", "sql-dump", "psql"], default="state")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE), help="Path to PostgreSQL env file for psql persistence")
    parser.add_argument("--sql-dump-dir", default=str(ROOT / "state" / "sql-dumps"), help="Where to write generated SQL when persist-mode=sql-dump")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    state_file = Path(args.state_file).resolve()
    state = load_state(state_file)

    if args.source_root:
        source_root = Path(args.source_root).resolve()
        run, _changed_records = ingest_source(source_root, str(source_root), state)
        run["status"] = "ok"
        run["persist_result"] = {"mode": "state"}
        save_state(state_file, state)
        print(json.dumps(run, ensure_ascii=False, indent=2))
        return 0

    registry = load_registry(Path(args.registry).resolve())
    workspace_root = Path(args.workspace_root).resolve()
    runs = ingest_registry_sources(
        workspace_root,
        registry,
        state,
        include_disabled=args.include_disabled,
        persist_mode=args.persist_mode,
        env_file=Path(args.env_file).resolve(),
        sql_dump_dir=Path(args.sql_dump_dir).resolve(),
        allow_nonphase1_policy=args.allow_nonphase1_policy,
    )
    save_state(state_file, state)
    print(json.dumps({"runs": runs}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
