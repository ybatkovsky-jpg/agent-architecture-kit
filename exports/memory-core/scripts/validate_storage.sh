#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${MEMORY_ENV_FILE:-$ROOT_DIR/config/memory.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE"
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

: "${PGHOST:?PGHOST is required}"
: "${PGPORT:?PGPORT is required}"
: "${PGDATABASE:?PGDATABASE is required}"
: "${PGUSER:?PGUSER is required}"
: "${PGPASSWORD:?PGPASSWORD is required}"

if ! command -v psql >/dev/null 2>&1; then
  echo "psql is not installed or not on PATH"
  exit 1
fi

run_psql() {
  PGPASSWORD="$PGPASSWORD" psql -v ON_ERROR_STOP=1 -X -A -t \
    -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" "$@"
}

echo "== extensions =="
run_psql -c "SELECT extname FROM pg_extension WHERE extname IN ('vector', 'pg_trgm') ORDER BY extname;"

echo "== mandatory extension check =="
run_psql -c "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm');"

echo "== tables =="
run_psql -c "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename IN ('sources','documents','chunks','entities','document_links','ingestion_runs') ORDER BY tablename;"

echo "== memory core tables =="
run_psql -c "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename IN ('mc_source_records','mc_evidence_records','mc_memory_notes','mc_wiki_pages','mc_retrieval_documents','mc_session_capsules','mc_typed_links','mc_object_sources','mc_object_evidence','mc_memory_note_supersedes','mc_memory_note_related_refs','mc_wiki_backing_memory','mc_wiki_backing_evidence','mc_retrieval_document_evidence','mc_retrieval_document_chunks','mc_session_capsule_memory_refs') ORDER BY tablename;"

echo "== vector column (optional in phase 1) =="
run_psql -c "SELECT COALESCE(string_agg(table_name || '.' || column_name || ':' || udt_name, E'\n'), 'chunks.embedding:absent') FROM information_schema.columns WHERE table_schema='public' AND table_name='chunks' AND column_name='embedding';"

echo "== trigger check =="
run_psql -c "SELECT trigger_name FROM information_schema.triggers WHERE event_object_table IN ('sources','documents','chunks','entities') ORDER BY event_object_table, trigger_name;"

echo "== index check =="
run_psql -c "SELECT indexname FROM pg_indexes WHERE schemaname='public' AND tablename IN ('documents','chunks','entities','document_links','ingestion_runs') ORDER BY tablename, indexname;"

echo "== memory core index check =="
run_psql -c "SELECT indexname FROM pg_indexes WHERE schemaname='public' AND tablename IN ('mc_source_records','mc_evidence_records','mc_memory_notes','mc_wiki_pages','mc_retrieval_documents','mc_session_capsules','mc_typed_links','mc_object_sources','mc_object_evidence','mc_memory_note_related_refs','mc_wiki_backing_memory') ORDER BY tablename, indexname;"

echo "== phase-1 source policy columns =="
run_psql -c "SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='sources' AND column_name IN ('enabled','retrieval_scope','owner') ORDER BY column_name;"

echo "Validation passed"
