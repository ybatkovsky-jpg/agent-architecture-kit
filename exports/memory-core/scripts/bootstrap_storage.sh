#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${MEMORY_ENV_FILE:-$ROOT_DIR/config/memory.env}"
EXAMPLE_ENV="$ROOT_DIR/config/memory.env.example"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE"
  echo "Copy $EXAMPLE_ENV to ${ENV_FILE##*/} and fill credentials first."
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

PSQL=(psql -v ON_ERROR_STOP=1)

run_psql() {
  PGPASSWORD="$PGPASSWORD" "${PSQL[@]}" \
    -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" "$@"
}

if [[ -n "${PGBOOTSTRAP_USER:-}" ]]; then
  BOOTSTRAP_DB="${PGBOOTSTRAP_DB:-postgres}"
  echo "Ensuring database exists: $PGDATABASE"
  set +e
  PGPASSWORD="${PGBOOTSTRAP_PASSWORD:-}" psql -v ON_ERROR_STOP=1 \
    -h "$PGHOST" -p "$PGPORT" -U "$PGBOOTSTRAP_USER" -d "$BOOTSTRAP_DB" \
    -tAc "SELECT 1 FROM pg_database WHERE datname = '$PGDATABASE'" | grep -q 1
  DB_EXISTS=$?
  set -e
  if [[ $DB_EXISTS -ne 0 ]]; then
    PGPASSWORD="${PGBOOTSTRAP_PASSWORD:-}" psql -v ON_ERROR_STOP=1 \
      -h "$PGHOST" -p "$PGPORT" -U "$PGBOOTSTRAP_USER" -d "$BOOTSTRAP_DB" \
      -c "CREATE DATABASE \"$PGDATABASE\""
  fi
fi

echo "Applying extensions"
run_psql -f "$ROOT_DIR/sql/001_extensions.sql"

echo "Applying schema"
run_psql -f "$ROOT_DIR/sql/010_schema.sql"

if [[ -f "$ROOT_DIR/sql/020_phase1_backbone_refinements.sql" ]]; then
  echo "Applying phase-1 backbone refinements"
  run_psql -f "$ROOT_DIR/sql/020_phase1_backbone_refinements.sql"
fi

if [[ -f "$ROOT_DIR/sql/030_drop_chunk_content_hash_uniqueness.sql" ]]; then
  echo "Applying chunk uniqueness compatibility refinement"
  run_psql -f "$ROOT_DIR/sql/030_drop_chunk_content_hash_uniqueness.sql"
fi

if [[ -f "$ROOT_DIR/sql/040_memory_core_v1_baseline.sql" ]]; then
  echo "Applying Memory Core v1 baseline schema"
  run_psql -f "$ROOT_DIR/sql/040_memory_core_v1_baseline.sql"
fi

echo "Bootstrap complete"
