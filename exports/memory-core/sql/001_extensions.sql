CREATE EXTENSION IF NOT EXISTS pg_trgm;

DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS vector;
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'pgvector extension not available yet; continuing without vector for phase-1 lexical rollout';
END
$$;
