-- Task #348 — Memory Core V1 baseline migration
-- Date: 2026-05-06
-- Scope: Stage 2 storage only. No ingest, backfill, triggers, or retrieval logic.

CREATE TABLE IF NOT EXISTS mc_source_records (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL DEFAULT 'source_record' CHECK (kind = 'source_record'),
  status TEXT NOT NULL CHECK (status IN ('draft','active','stale','superseded','archived')),
  scope TEXT NOT NULL CHECK (scope IN ('global','project','task','run','agent','operator')),
  authority_class TEXT NOT NULL CHECK (authority_class = 'source_of_truth'),
  serving_class TEXT NOT NULL CHECK (serving_class = 'never_ambient'),
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  source_type TEXT NOT NULL CHECK (source_type IN ('workspace_dir','artifact_bundle','transcript_store','handoff_store','wiki_root')),
  path TEXT NOT NULL,
  owner_scope TEXT NOT NULL CHECK (owner_scope IN ('global','project','agent','explicit_only')),
  retrieval_scope TEXT NOT NULL CHECK (retrieval_scope IN ('phase1_default','project_only','explicit_only','blocked')),
  enabled BOOLEAN NOT NULL,
  created_by TEXT NOT NULL,
  UNIQUE (path)
);

CREATE INDEX IF NOT EXISTS mc_source_records_enabled_idx ON mc_source_records (enabled, retrieval_scope);

CREATE TABLE IF NOT EXISTS mc_evidence_records (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL DEFAULT 'evidence_record' CHECK (kind = 'evidence_record'),
  status TEXT NOT NULL CHECK (status IN ('draft','active','stale','superseded','archived')),
  scope TEXT NOT NULL CHECK (scope IN ('global','project','task','run','agent','operator')),
  authority_class TEXT NOT NULL CHECK (authority_class = 'source_of_truth'),
  serving_class TEXT NOT NULL CHECK (serving_class = 'on_demand'),
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  source_id TEXT NOT NULL REFERENCES mc_source_records(id) ON DELETE RESTRICT,
  artifact_ref TEXT NOT NULL,
  evidence_type TEXT NOT NULL CHECK (evidence_type IN ('artifact','transcript','run_log','handoff','note','spec')),
  title TEXT NOT NULL,
  provenance_path TEXT,
  provenance_locator TEXT,
  captured_from TEXT,
  created_by TEXT NOT NULL,
  UNIQUE (source_id, artifact_ref)
);

CREATE INDEX IF NOT EXISTS mc_evidence_source_idx ON mc_evidence_records (source_id, evidence_type);
CREATE INDEX IF NOT EXISTS mc_evidence_artifact_idx ON mc_evidence_records (artifact_ref);

CREATE TABLE IF NOT EXISTS mc_memory_notes (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL DEFAULT 'memory_note' CHECK (kind = 'memory_note'),
  status TEXT NOT NULL CHECK (status IN ('draft','active','stale','superseded','archived')),
  scope TEXT NOT NULL CHECK (scope IN ('global','project','task','run','agent','operator')),
  authority_class TEXT NOT NULL CHECK (authority_class = 'canonical_reusable'),
  serving_class TEXT NOT NULL CHECK (serving_class IN ('always_on_candidate','on_demand','never_ambient')),
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  created_by TEXT NOT NULL,
  subtype TEXT NOT NULL CHECK (subtype IN ('decision','pattern','anti_pattern','blocker','durable_ref','preference','state_summary')),
  title TEXT NOT NULL,
  statement TEXT NOT NULL,
  rationale TEXT,
  why_it_matters TEXT NOT NULL,
  source_of_truth_ref TEXT NOT NULL,
  effective_scope TEXT CHECK (effective_scope IN ('global','project','task','run','agent','operator')),
  confidence TEXT NOT NULL CHECK (confidence IN ('verified','accepted','tentative')),
  expires_at TIMESTAMPTZ,
  superseded_by TEXT REFERENCES mc_memory_notes(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS mc_memory_notes_scope_idx ON mc_memory_notes (scope, subtype, status);
CREATE INDEX IF NOT EXISTS mc_memory_notes_serving_idx ON mc_memory_notes (serving_class, status);
CREATE INDEX IF NOT EXISTS mc_memory_notes_expiry_idx ON mc_memory_notes (expires_at) WHERE expires_at IS NOT NULL;

CREATE TABLE IF NOT EXISTS mc_wiki_pages (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL DEFAULT 'wiki_page' CHECK (kind = 'wiki_page'),
  status TEXT NOT NULL CHECK (status IN ('draft','active','stale','superseded','archived')),
  scope TEXT NOT NULL CHECK (scope IN ('global','project','task','run','agent','operator')),
  authority_class TEXT NOT NULL CHECK (authority_class = 'canonical_synthesis'),
  serving_class TEXT NOT NULL CHECK (serving_class IN ('always_on_candidate','on_demand')),
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  created_by TEXT NOT NULL,
  topic TEXT NOT NULL,
  summary TEXT NOT NULL,
  UNIQUE (topic)
);

CREATE INDEX IF NOT EXISTS mc_wiki_pages_serving_idx ON mc_wiki_pages (serving_class, status);

CREATE TABLE IF NOT EXISTS mc_retrieval_documents (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL DEFAULT 'retrieval_document' CHECK (kind = 'retrieval_document'),
  status TEXT NOT NULL CHECK (status IN ('draft','active','stale','superseded','archived')),
  scope TEXT NOT NULL CHECK (scope IN ('global','project','task','run','agent','operator')),
  authority_class TEXT NOT NULL CHECK (authority_class = 'derived_operational'),
  serving_class TEXT NOT NULL CHECK (serving_class = 'on_demand'),
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  created_by TEXT NOT NULL,
  source_id TEXT NOT NULL REFERENCES mc_source_records(id) ON DELETE RESTRICT,
  doc_ref TEXT NOT NULL,
  index_status TEXT NOT NULL CHECK (index_status IN ('active','stale','superseded')),
  UNIQUE (source_id, doc_ref)
);

CREATE INDEX IF NOT EXISTS mc_retrieval_documents_source_idx ON mc_retrieval_documents (source_id, index_status);

CREATE TABLE IF NOT EXISTS mc_session_capsules (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL DEFAULT 'session_capsule' CHECK (kind = 'session_capsule'),
  status TEXT NOT NULL CHECK (status IN ('draft','active','stale','superseded','archived')),
  scope TEXT NOT NULL CHECK (scope IN ('global','project','task','run','agent','operator')),
  authority_class TEXT NOT NULL CHECK (authority_class = 'ephemeral_projection'),
  serving_class TEXT NOT NULL CHECK (serving_class = 'never_ambient'),
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  created_by TEXT NOT NULL,
  owner TEXT NOT NULL,
  scope_ref TEXT NOT NULL,
  goal TEXT NOT NULL,
  current_status TEXT NOT NULL CHECK (current_status IN ('ack','active','blocked','waiting','done')),
  handoff_ref TEXT,
  expires_at TIMESTAMPTZ,
  superseded_by TEXT REFERENCES mc_session_capsules(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS mc_session_capsules_scope_idx ON mc_session_capsules (scope_ref, current_status, status);
CREATE INDEX IF NOT EXISTS mc_session_capsules_expiry_idx ON mc_session_capsules (expires_at) WHERE expires_at IS NOT NULL;

CREATE TABLE IF NOT EXISTS mc_typed_links (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL DEFAULT 'typed_link' CHECK (kind = 'typed_link'),
  status TEXT NOT NULL CHECK (status IN ('draft','active','stale','superseded','archived')),
  scope TEXT NOT NULL CHECK (scope IN ('global','project','task','run','agent','operator')),
  authority_class TEXT NOT NULL CHECK (authority_class = 'derived_operational'),
  serving_class TEXT NOT NULL CHECK (serving_class = 'never_ambient'),
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  created_by TEXT NOT NULL,
  link_type TEXT NOT NULL CHECK (link_type IN ('provenance','scope','lifecycle','semantic','supersession','dependency')),
  from_ref TEXT NOT NULL,
  to_ref TEXT NOT NULL,
  statement TEXT,
  CHECK (from_ref <> to_ref)
);

CREATE UNIQUE INDEX IF NOT EXISTS mc_typed_links_unique_idx
  ON mc_typed_links (link_type, from_ref, to_ref, COALESCE(statement, ''));
CREATE INDEX IF NOT EXISTS mc_typed_links_from_idx ON mc_typed_links (from_ref, link_type);
CREATE INDEX IF NOT EXISTS mc_typed_links_to_idx ON mc_typed_links (to_ref, link_type);

CREATE TABLE IF NOT EXISTS mc_object_sources (
  object_id TEXT NOT NULL,
  source_ref TEXT NOT NULL,
  position INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (object_id, source_ref)
);

CREATE INDEX IF NOT EXISTS mc_object_sources_ref_idx ON mc_object_sources (source_ref);

CREATE TABLE IF NOT EXISTS mc_object_evidence (
  object_id TEXT NOT NULL,
  evidence_id TEXT NOT NULL REFERENCES mc_evidence_records(id) ON DELETE CASCADE,
  position INTEGER NOT NULL DEFAULT 0,
  relation_role TEXT NOT NULL DEFAULT 'supporting',
  PRIMARY KEY (object_id, evidence_id)
);

CREATE INDEX IF NOT EXISTS mc_object_evidence_evidence_idx ON mc_object_evidence (evidence_id, relation_role);

CREATE TABLE IF NOT EXISTS mc_memory_note_supersedes (
  memory_note_id TEXT NOT NULL REFERENCES mc_memory_notes(id) ON DELETE CASCADE,
  supersedes_id TEXT NOT NULL REFERENCES mc_memory_notes(id) ON DELETE RESTRICT,
  PRIMARY KEY (memory_note_id, supersedes_id),
  CHECK (memory_note_id <> supersedes_id)
);

CREATE TABLE IF NOT EXISTS mc_memory_note_related_refs (
  memory_note_id TEXT NOT NULL REFERENCES mc_memory_notes(id) ON DELETE CASCADE,
  related_ref TEXT NOT NULL,
  relation_role TEXT NOT NULL DEFAULT 'supporting' CHECK (relation_role IN ('supporting','context','scope','supersedes')),
  position INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (memory_note_id, related_ref, relation_role)
);

CREATE INDEX IF NOT EXISTS mc_memory_note_related_refs_ref_idx ON mc_memory_note_related_refs (related_ref, relation_role);

CREATE TABLE IF NOT EXISTS mc_wiki_backing_memory (
  wiki_page_id TEXT NOT NULL REFERENCES mc_wiki_pages(id) ON DELETE CASCADE,
  memory_note_id TEXT NOT NULL REFERENCES mc_memory_notes(id) ON DELETE RESTRICT,
  role TEXT NOT NULL CHECK (role IN ('facts_from','rules_from','context_from')),
  position INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (wiki_page_id, memory_note_id, role)
);

CREATE INDEX IF NOT EXISTS mc_wiki_backing_memory_note_idx ON mc_wiki_backing_memory (memory_note_id, role);

CREATE TABLE IF NOT EXISTS mc_wiki_backing_evidence (
  wiki_page_id TEXT NOT NULL REFERENCES mc_wiki_pages(id) ON DELETE CASCADE,
  evidence_id TEXT NOT NULL REFERENCES mc_evidence_records(id) ON DELETE RESTRICT,
  role TEXT NOT NULL CHECK (role IN ('facts_from','rules_from')),
  position INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (wiki_page_id, evidence_id, role)
);

CREATE TABLE IF NOT EXISTS mc_retrieval_document_evidence (
  retrieval_document_id TEXT NOT NULL REFERENCES mc_retrieval_documents(id) ON DELETE CASCADE,
  evidence_id TEXT NOT NULL REFERENCES mc_evidence_records(id) ON DELETE RESTRICT,
  position INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (retrieval_document_id, evidence_id)
);

CREATE TABLE IF NOT EXISTS mc_retrieval_document_chunks (
  retrieval_document_id TEXT NOT NULL REFERENCES mc_retrieval_documents(id) ON DELETE CASCADE,
  chunk_ref TEXT NOT NULL,
  position INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (retrieval_document_id, chunk_ref)
);

CREATE TABLE IF NOT EXISTS mc_session_capsule_memory_refs (
  session_capsule_id TEXT NOT NULL REFERENCES mc_session_capsules(id) ON DELETE CASCADE,
  memory_note_id TEXT NOT NULL REFERENCES mc_memory_notes(id) ON DELETE RESTRICT,
  position INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (session_capsule_id, memory_note_id)
);
