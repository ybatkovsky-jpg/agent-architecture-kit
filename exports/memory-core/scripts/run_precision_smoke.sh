#!/usr/bin/env bash
set -euo pipefail

OUTDIR="pkm-memory/outputs/smoke-db-retrieval-precision-2026-04-26"
mkdir -p "$OUTDIR"

python3 pkm-memory/retrieve_memory.py "task-107-postgres-activation-and-first-live-ingest" --mode psql --env-file pkm-memory/config/memory.env --output "$OUTDIR/query-task-107-db.json"
python3 pkm-memory/retrieve_memory.py "task-107-postgres-activation-and-first-live-ingest" --mode local --output "$OUTDIR/query-task-107-local.json"
python3 pkm-memory/retrieve_memory.py "postgres activation milestone" --mode psql --env-file pkm-memory/config/memory.env --output "$OUTDIR/query-postgres-activation-milestone-db.json"
python3 pkm-memory/retrieve_memory.py "postgres activation milestone" --mode local --output "$OUTDIR/query-postgres-activation-milestone-local.json"
python3 pkm-memory/retrieve_memory.py "task-108-db-backed-retrieval-baseline" --mode psql --env-file pkm-memory/config/memory.env --output "$OUTDIR/query-task-108-db.json"
python3 pkm-memory/retrieve_memory.py "task-108-db-backed-retrieval-baseline" --mode local --output "$OUTDIR/query-task-108-local.json"
python3 pkm-memory/retrieve_memory.py "memory rollout plan" --mode psql --env-file pkm-memory/config/memory.env --output "$OUTDIR/query-memory-rollout-plan-db.json"
python3 pkm-memory/retrieve_memory.py "memory rollout plan" --mode local --output "$OUTDIR/query-memory-rollout-plan-local.json"
python3 pkm-memory/scripts/compare_precision_smoke.py
