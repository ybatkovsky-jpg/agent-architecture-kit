# PKM Memory Storage Foundation

Phase-1 storage foundation for the PKM/RAG stack from Task #86.

## Layout

- `sources/` — representative file-based source of truth roots for local prototype data
- `config/memory.env.example` — environment template for local PostgreSQL
- `config/source_registry.seed.yaml` — approved phase-1 source registry seed
- `sql/001_extensions.sql` — required phase-1 extensions (`pg_trgm` mandatory, `vector` optional)
- `sql/010_schema.sql` — minimal storage schema
- `sql/020_phase1_backbone_refinements.sql` — additive phase-1 refinements for source policy + trigram coverage
- `sql/030_drop_chunk_content_hash_uniqueness.sql` — compatibility refinement for chunk uniqueness
- `sql/040_memory_core_v1_baseline.sql` — Memory Core v1 baseline schema bootstrap from task #348
- `scripts/bootstrap_storage.sh` — idempotent bootstrap script for the database schema
- `scripts/validate_storage.sh` — bounded validation script for extensions/tables/indexes
- `scripts/backup_storage.sh` — backup helper for PostgreSQL dump + source snapshot manifest
- `retrieve_memory.py` — phase-1 local retrieval baseline with bounded evidence-pack JSON output
- `memory_core_registry.py` — minimal registry-facing writer for Memory Core object families into `mc_*` tables
- `memory_core_decisions_sessions.py` — domain-level writer that expands decisions/session-capsule payloads onto the registry surface
- `memory_core_typed_links.py` — domain-level writer that expands `typed_links[]` payloads into registry-backed `mc_typed_links` writes
- `memory_core_task_metadata.py` — Stage-3.2 task-ingest adapter that supports single-task ingest plus batch/reingest projection of Task Manager task metadata into source/evidence/retrieval/link objects without moving authority out of the task system
- `scripts/verify_memory_core_schema_conformance.py` — contract-level verifier for registry/runtime assumptions against the Memory Core baseline SQL
- `scripts/verify_memory_core_decisions_sessions.py` — bounded verifier for the task-351 decision/session-capsule write path
- `scripts/verify_memory_core_typed_links.py` — bounded verifier for the task-350 typed-link write path
- `scripts/prepare_live_activation_bundle.sh` — creates a ready-to-fill env template + live activation checklist
- `scripts/verify_conflict_open_questions_task_363.py` — bounded verifier for serve-pack conflict/open-question synthesis from task #363

## Source-of-truth policy

Original data lives in files/git under `pkm-memory/sources/`. PostgreSQL is an index and retrieval cache layer, not the only durable source of truth.

## Canonical identifiers

- `source_id` — stable root/source identifier
- `document_id` — stable document identifier
- `chunk_id` — stable chunk identifier
- `entity_id` — stable extracted entity identifier
- `link_id` — stable relationship identifier
- `run_id` — ingestion run identifier
- `content_hash` — content checksum used for incremental skip/dedupe decisions

Recommended format: deterministic prefixed IDs such as `src_*`, `doc_*`, `chk_*`, `ent_*`, `lnk_*`, `run_*`.

## Bootstrap

The bootstrap chain now applies both the legacy PKM retrieval schema and the Memory Core v1 baseline relational schema.


```bash
cp pkm-memory/config/memory.env.example pkm-memory/config/memory.env
# edit credentials as needed
bash pkm-memory/scripts/bootstrap_storage.sh
bash pkm-memory/scripts/validate_storage.sh
```

## Validation contract

Phase-1 validation should pass with `pg_trgm` available. `pgvector` is optional for now and should not block lexical rollout. Validation also checks that the Memory Core v1 baseline tables/indexes are present after bootstrap.

The retrieval serve-pack now also carries bounded answer-packaging policy layers: request-class-specific citation envelopes from task #362 plus conflict/open-question synthesis from task #363 so mixed-authority or insufficiently corroborated results are surfaced explicitly in output JSON.

## Registry-driven ingestion prototype

The ingestion prototype can now read approved roots from `config/source_registry.seed.yaml`.

Examples:

```bash
python3 pkm-memory/ingest_sources.py \
  --registry pkm-memory/config/source_registry.seed.yaml \
  --workspace-root .
```

Generate DB-ready SQL without live Postgres writes:

```bash
python3 pkm-memory/ingest_sources.py \
  --registry pkm-memory/config/source_registry.seed.yaml \
  --workspace-root . \
  --persist-mode sql-dump
```

Write directly through `psql` once `config/memory.env` is present:

```bash
python3 pkm-memory/ingest_sources.py \
  --registry pkm-memory/config/source_registry.seed.yaml \
  --workspace-root . \
  --persist-mode psql \
  --env-file pkm-memory/config/memory.env
```

## Memory Core registry write surface

A minimal registry-facing write surface now exists for Memory Core object persistence.
It accepts a JSON payload with `objects[]`, where each object declares a `family`, a top-level `record`, and optional mapping-table rows for supported relations.

For task-351 there is also a narrower domain write path for durable decisions and ephemeral session capsules. It accepts `decisions[]` and `session_capsules[]`, validates their task-specific assumptions, then expands them onto the registry payload shape before generating SQL or writing through `psql`.

For the Stage-3.3 decision path, decision records can now also carry bounded `rationale` and `effective_scope` fields, while `supporting_object_refs[]` materialize into `mc_memory_note_related_refs` so create/update/supersede flows can keep non-evidence supporting links attached without pulling in retrieval or serve-pack work.

For Stage 3.4 there is now a bounded session capsule distiller: it accepts either explicit session context JSON or a `task-manager/tasks.db` task id, distills a compact capsule contract (`capsule_text`, `open_questions`, `active_entities`, `next_steps`) with provenance refs, and emits a `session_capsules[]` payload compatible with the existing decisions/session writer.

Examples:

```bash
python3 pkm-memory/memory_core_registry.py \
  pkm-memory/fixtures/memory_core_registry_payload.sample.json
```

Generate SQL only:

```bash
python3 pkm-memory/memory_core_registry.py \
  pkm-memory/fixtures/memory_core_registry_payload.sample.json \
  --persist-mode sql-dump \
  --sql-dump-path pkm-memory/state/sql-dumps/memory-core-sample.sql
```

Write directly through `psql` once `config/memory.env` is present:

```bash
python3 pkm-memory/memory_core_registry.py \
  pkm-memory/fixtures/memory_core_registry_payload.sample.json \
  --persist-mode psql \
  --env-file pkm-memory/config/memory.env
```

Supported object families in this foundation step:
- `source_record`
- `evidence_record`
- `memory_note`
- `wiki_page`
- `retrieval_document`
- `session_capsule`
- `typed_link`

Stage-3.2 task metadata ingest examples:

Single task:

```bash
python3 pkm-memory/memory_core_task_metadata.py 353 \
  --persist-mode sql-dump \
  --sql-dump-path pkm-memory/state/sql-dumps/task353-memory-core-task-metadata-sample.sql \
  --related-object-ref mem_task_353_decision_a \
  --related-object-ref wiki_memory_core_stage3
```

Batch ingest of representative tasks:

```bash
python3 pkm-memory/memory_core_task_metadata.py \
  --task-id 347 \
  --task-id 353 \
  --task-id 371 \
  --persist-mode sql-dump \
  --sql-dump-path pkm-memory/state/sql-dumps/task354-memory-core-task-metadata-batch-sample.sql \
  --task-related-object-refs-json '{"347":["wiki_memory_core_stage2"],"353":["mem_task_353_decision_a","wiki_memory_core_stage3"],"371":["mem_agent_arch_split_boundary","wiki_agent_architecture_plan"]}'
```

Reingest/update an existing task projection with a changed link set:

```bash
python3 pkm-memory/memory_core_task_metadata.py 371 \
  --persist-mode sql-dump \
  --sql-dump-path pkm-memory/state/sql-dumps/task354-memory-core-task-metadata-reingest-sample.sql \
  --task-related-object-refs-json '{"371":["wiki_agent_architecture_plan"]}'
```

This adapter keeps task truth in `task-manager/tasks.db`, emits one task snapshot JSON per ingested task under `pkm-memory/state/task-ingest/`, and writes an indexed Memory Core projection as:
- one shared `source_record` for the task system source
- one `evidence_record` per specific task snapshot
- one `retrieval_document` keyed by `doc_ref=task:<id>` so state changes can upsert cleanly
- optional `typed_link` rows from each task document to related memory objects
- relation-table replacement semantics on reingest so stale task links/chunks are removed instead of duplicated

Task-350 typed-link write-path examples:

```bash
python3 pkm-memory/memory_core_typed_links.py \
  pkm-memory/fixtures/memory_core_typed_links_payload.sample.json
```

Generate SQL only:

```bash
python3 pkm-memory/memory_core_typed_links.py \
  pkm-memory/fixtures/memory_core_typed_links_payload.sample.json \
  --persist-mode sql-dump \
  --sql-dump-path pkm-memory/state/sql-dumps/memory-core-typed-links-sample.sql
```

Task-351 domain write-path examples:

```bash
python3 pkm-memory/memory_core_decisions_sessions.py \
  pkm-memory/fixtures/memory_core_decisions_sessions_payload.sample.json
```

Generate SQL only:

```bash
python3 pkm-memory/memory_core_decisions_sessions.py \
  pkm-memory/fixtures/memory_core_decisions_sessions_payload.sample.json \
  --persist-mode sql-dump \
  --sql-dump-path pkm-memory/state/sql-dumps/memory-core-decisions-sessions-sample.sql
```

Task-356 bounded session-capsule distiller examples:

```bash
python3 pkm-memory/memory_core_session_capsule_distiller.py \
  --input pkm-memory/fixtures/memory_core_session_capsule_distiller_input.sample.json \
  --output pkm-memory/state/sql-dumps/task356-memory-core-session-capsule-distilled.json
```

Or distill directly from task-manager state:

```bash
python3 pkm-memory/memory_core_session_capsule_distiller.py \
  --task-id 356 \
  --expires-at 2026-05-07T12:30:00Z
```

The distiller emits a bounded `session_capsules[]` payload plus normalized registry-compatible `objects[]` metadata for verification. Persisting the resulting capsule still flows through `memory_core_decisions_sessions.py`, keeping Stage 3.4 strictly inside the existing write surface instead of creating a second persistence path.

This is intentionally a write-only foundation layer for canonical object persistence and relation-table replacement; it does not implement ingest/promotion orchestration or retrieval/runtime serving.

Run the bounded schema/runtime conformance verifier:

```bash
python3 pkm-memory/scripts/verify_memory_core_schema_conformance.py
```

Run the bounded decision/session-capsule write-path verifier:

```bash
python3 pkm-memory/scripts/verify_memory_core_decisions_sessions.py
```

Run the bounded typed-link write-path verifier:

```bash
python3 pkm-memory/scripts/verify_memory_core_typed_links.py
```

Run the bounded batch/reingest task-metadata ingest verifier:

```bash
python3 pkm-memory/scripts/verify_memory_core_task_metadata.py
```

Run the bounded session-capsule distiller verifier:

```bash
python3 pkm-memory/scripts/verify_memory_core_session_capsule_distiller.py
```

Run the end-to-end Stage-2 storage smoke suite (schema checks + SQL-dump checks + live Postgres bootstrap/validation + registry/typed-link/decision writes + row-count assertions):

```bash
python3 pkm-memory/scripts/run_memory_core_storage_smoke.py
```

This smoke suite assumes `pkm-memory/config/memory.env` points at a safe validation database because it runs the bootstrap chain and writes the sample Memory Core fixtures through `psql`.

## Retrieval baseline

Run phase-1 retrieval over approved local operational state/artifacts:

```bash
python3 pkm-memory/retrieve_memory.py "memory rollout plan" \
  --workspace-root . \
  --max-items 6
```

Output contract:
- bounded evidence pack JSON
- `summary`
- `items[4..8]` when enough matches exist
- per-item `provenance`, `match_reason`, `score`, excerpt, document/chunk metadata

Prepare a later live-Postgres activation bundle:

```bash
bash pkm-memory/scripts/prepare_live_activation_bundle.sh
```

Legacy single-root mode still works:

```bash
python3 pkm-memory/ingest_sources.py pkm-memory/sources/representative
```

Current registry-first phase-1 ingest set:
- `memory/`
- `task-manager/artifacts/`
- `task-manager/handoffs/`

Disabled roots remain registered but excluded by default.

## Backups

```bash
bash pkm-memory/scripts/backup_storage.sh
```

This creates:
- a PostgreSQL custom dump in `pkm-memory/backups/postgres/`
- a tarball snapshot of `pkm-memory/sources/` in `pkm-memory/backups/sources/`
- a timestamped manifest in `pkm-memory/backups/manifests/`
