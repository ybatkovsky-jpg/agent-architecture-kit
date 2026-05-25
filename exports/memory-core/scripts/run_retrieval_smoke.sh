#!/usr/bin/env bash
set -euo pipefail

WORKSPACE_ROOT="${1:-/home/openclaw/.openclaw/workspace}"
PKM_ROOT="$WORKSPACE_ROOT/pkm-memory"
ARTIFACT_DIR="$PKM_ROOT/artifacts"

mkdir -p "$ARTIFACT_DIR"
chmod +x "$PKM_ROOT/retrieve_memory.py" "$PKM_ROOT/scripts/prepare_live_activation_bundle.sh"

python3 "$PKM_ROOT/retrieve_memory.py" "memory rollout plan" \
  --workspace-root "$WORKSPACE_ROOT" \
  --max-items 6 \
  --output "$ARTIFACT_DIR/retrieval-smoke-memory-rollout-plan-2026-04-26.json"

python3 "$PKM_ROOT/retrieve_memory.py" "task 105 db path status" \
  --workspace-root "$WORKSPACE_ROOT" \
  --max-items 6 \
  --output "$ARTIFACT_DIR/retrieval-smoke-task-105-db-path-status-2026-04-26.json"

bash "$PKM_ROOT/scripts/prepare_live_activation_bundle.sh"
