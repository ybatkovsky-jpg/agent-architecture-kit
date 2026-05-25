#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_EXAMPLE="$ROOT_DIR/config/memory.env.example"
ENV_TARGET="$ROOT_DIR/config/memory.env"
CHECKLIST_TARGET="$ROOT_DIR/artifacts/live-postgres-activation-checklist-2026-04-26.md"

mkdir -p "$ROOT_DIR/artifacts"

if [[ ! -f "$ENV_TARGET" ]]; then
  cp "$ENV_EXAMPLE" "$ENV_TARGET"
  echo "Created env template: $ENV_TARGET"
else
  echo "Env file already exists: $ENV_TARGET"
fi

cat > "$CHECKLIST_TARGET" <<'EOF'
# Live Postgres activation checklist — 2026-04-26

## Goal

Activate the already-prepared DB-backed PKM memory path without changing ingest logic.

## Inputs expected

- `pkm-memory/config/memory.env`
- reachable PostgreSQL target
- `psql` installed on the host

## Short activation sequence

1. Fill real values into `pkm-memory/config/memory.env`:
   - `PGHOST`
   - `PGPORT`
   - `PGDATABASE`
   - `PGUSER`
   - `PGPASSWORD`
2. Bootstrap schema:
   - `bash pkm-memory/scripts/bootstrap_storage.sh`
3. Validate schema/extensions:
   - `bash pkm-memory/scripts/validate_storage.sh`
4. Run first live ingest:
   - `python3 pkm-memory/ingest_sources.py --registry pkm-memory/config/source_registry.seed.yaml --workspace-root . --persist-mode psql --env-file pkm-memory/config/memory.env`
5. Run bounded retrieval smoke:
   - `python3 pkm-memory/retrieve_memory.py "memory rollout plan" --workspace-root . --max-items 6`

## Success criteria

- bootstrap succeeds
- validation prints `Validation passed`
- ingest returns `status: ok` for enabled roots
- retrieval returns a bounded evidence pack with 4–8 items (or fewer only when genuinely little matches)

## Notes

- no new Python DB driver is required for activation; live ingest already uses `psql`
- this checklist intentionally avoids any fake live run without real credentials
EOF

echo "Wrote checklist: $CHECKLIST_TARGET"
