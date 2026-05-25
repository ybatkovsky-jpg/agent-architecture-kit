#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${MEMORY_ENV_FILE:-$ROOT_DIR/config/memory.env}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_ROOT="$ROOT_DIR/backups"
PG_BACKUP_DIR="$BACKUP_ROOT/postgres"
SRC_BACKUP_DIR="$BACKUP_ROOT/sources"
MANIFEST_DIR="$BACKUP_ROOT/manifests"
MANIFEST_PATH="$MANIFEST_DIR/${TIMESTAMP}.json"

mkdir -p "$PG_BACKUP_DIR" "$SRC_BACKUP_DIR" "$MANIFEST_DIR"

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

if ! command -v pg_dump >/dev/null 2>&1; then
  echo "pg_dump is not installed or not on PATH"
  exit 1
fi

PG_DUMP_PATH="$PG_BACKUP_DIR/${TIMESTAMP}_${PGDATABASE}.dump"
SRC_ARCHIVE_PATH="$SRC_BACKUP_DIR/${TIMESTAMP}_sources.tar.gz"

PGPASSWORD="$PGPASSWORD" pg_dump \
  -h "$PGHOST" -p "$PGPORT" -U "$PGUSER" -d "$PGDATABASE" \
  -Fc -f "$PG_DUMP_PATH"

tar -czf "$SRC_ARCHIVE_PATH" -C "$ROOT_DIR" sources

cat > "$MANIFEST_PATH" <<EOF
{
  "timestamp": "$TIMESTAMP",
  "postgres_dump": "${PG_DUMP_PATH#$ROOT_DIR/}",
  "sources_archive": "${SRC_ARCHIVE_PATH#$ROOT_DIR/}",
  "database": "$PGDATABASE",
  "host": "$PGHOST",
  "port": "$PGPORT"
}
EOF

echo "$MANIFEST_PATH"
