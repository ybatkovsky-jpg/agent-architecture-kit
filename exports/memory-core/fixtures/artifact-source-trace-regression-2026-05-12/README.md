# Artifact/source-trace regression pack

Single-purpose regression pack for explicit artifact/source-trace lookup behavior.

## What it covers

- factual task-id artifact lookup

## What it checks

- `artifact_source_trace_request` classification
- expected artifact/source-trace evidence in top-N

## Run

```bash
python3 pkm-memory/scripts/verify_artifact_source_trace_regression.py
```
