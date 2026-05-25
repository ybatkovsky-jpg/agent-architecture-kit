CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    root_path TEXT NOT NULL UNIQUE,
    parser_type TEXT NOT NULL,
    trust_level TEXT NOT NULL DEFAULT 'normal',
    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
    parent_document_id TEXT REFERENCES documents(document_id) ON DELETE SET NULL,
    external_ref TEXT NOT NULL DEFAULT '',
    title TEXT NOT NULL,
    path TEXT NOT NULL,
    mime_type TEXT NOT NULL DEFAULT 'text/plain',
    document_type TEXT NOT NULL,
    language_code TEXT NOT NULL DEFAULT 'und',
    author TEXT NOT NULL DEFAULT '',
    created_at_source TIMESTAMPTZ,
    updated_at_source TIMESTAMPTZ,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    content_hash TEXT NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    raw_text TEXT NOT NULL DEFAULT '',
    search_vector TSVECTOR,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (source_id, path)
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    chunk_ordinal INTEGER NOT NULL,
    section_path TEXT NOT NULL DEFAULT '',
    token_count INTEGER NOT NULL DEFAULT 0,
    char_count INTEGER NOT NULL DEFAULT 0,
    content_hash TEXT NOT NULL,
    chunk_text TEXT NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    search_vector TSVECTOR,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, chunk_ordinal)
);

CREATE TABLE IF NOT EXISTS entities (
    entity_id TEXT PRIMARY KEY,
    canonical_name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    source_confidence REAL NOT NULL DEFAULT 0.0,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (entity_type, canonical_name)
);

CREATE TABLE IF NOT EXISTS document_links (
    link_id TEXT PRIMARY KEY,
    from_document_id TEXT NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
    to_document_id TEXT REFERENCES documents(document_id) ON DELETE CASCADE,
    entity_id TEXT REFERENCES entities(entity_id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 1.0,
    evidence_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK ((to_document_id IS NOT NULL) OR (entity_id IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    run_id TEXT PRIMARY KEY,
    source_id TEXT REFERENCES sources(source_id) ON DELETE SET NULL,
    trigger_type TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    docs_seen INTEGER NOT NULL DEFAULT 0,
    docs_changed INTEGER NOT NULL DEFAULT 0,
    docs_failed INTEGER NOT NULL DEFAULT 0,
    chunks_upserted INTEGER NOT NULL DEFAULT 0,
    error_summary TEXT NOT NULL DEFAULT '',
    details_json JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_sources_type ON sources(source_type);
CREATE INDEX IF NOT EXISTS idx_documents_source_path ON documents(source_id, path);
CREATE INDEX IF NOT EXISTS idx_documents_updated_at_source ON documents(updated_at_source DESC);
CREATE INDEX IF NOT EXISTS idx_documents_search_vector ON documents USING GIN (search_vector);
CREATE INDEX IF NOT EXISTS idx_documents_title_trgm ON documents USING GIN (title gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_chunks_document_ordinal ON chunks(document_id, chunk_ordinal);
CREATE INDEX IF NOT EXISTS idx_chunks_search_vector ON chunks USING GIN (search_vector);
CREATE INDEX IF NOT EXISTS idx_chunks_section_path_trgm ON chunks USING GIN (section_path gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_entities_type_name ON entities(entity_type, canonical_name);
CREATE INDEX IF NOT EXISTS idx_links_from_doc ON document_links(from_document_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_links_to_doc ON document_links(to_document_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_links_entity ON document_links(entity_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_ingestion_runs_source_started ON ingestion_runs(source_id, started_at DESC);

CREATE OR REPLACE FUNCTION set_updated_at_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sources_updated_at ON sources;
CREATE TRIGGER trg_sources_updated_at
BEFORE UPDATE ON sources
FOR EACH ROW EXECUTE FUNCTION set_updated_at_timestamp();

DROP TRIGGER IF EXISTS trg_chunks_updated_at ON chunks;
CREATE TRIGGER trg_chunks_updated_at
BEFORE UPDATE ON chunks
FOR EACH ROW EXECUTE FUNCTION set_updated_at_timestamp();

DROP TRIGGER IF EXISTS trg_entities_updated_at ON entities;
CREATE TRIGGER trg_entities_updated_at
BEFORE UPDATE ON entities
FOR EACH ROW EXECUTE FUNCTION set_updated_at_timestamp();

CREATE OR REPLACE FUNCTION refresh_document_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('simple', coalesce(NEW.title, '')), 'A') ||
        setweight(to_tsvector('simple', coalesce(NEW.path, '')), 'B') ||
        setweight(to_tsvector('simple', coalesce(NEW.raw_text, '')), 'C');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_documents_search_vector ON documents;
CREATE TRIGGER trg_documents_search_vector
BEFORE INSERT OR UPDATE OF title, path, raw_text ON documents
FOR EACH ROW EXECUTE FUNCTION refresh_document_search_vector();

CREATE OR REPLACE FUNCTION refresh_chunk_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('simple', coalesce(NEW.section_path, '')), 'A') ||
        setweight(to_tsvector('simple', coalesce(NEW.chunk_text, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_chunks_search_vector ON chunks;
CREATE TRIGGER trg_chunks_search_vector
BEFORE INSERT OR UPDATE OF section_path, chunk_text ON chunks
FOR EACH ROW EXECUTE FUNCTION refresh_chunk_search_vector();
