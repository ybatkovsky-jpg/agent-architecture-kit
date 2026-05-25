ALTER TABLE sources
    ADD COLUMN IF NOT EXISTS enabled BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS retrieval_scope TEXT NOT NULL DEFAULT 'global',
    ADD COLUMN IF NOT EXISTS owner TEXT NOT NULL DEFAULT '';

CREATE INDEX IF NOT EXISTS idx_documents_path_trgm
    ON documents USING GIN (path gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_entities_canonical_name_trgm
    ON entities USING GIN (canonical_name gin_trgm_ops);
