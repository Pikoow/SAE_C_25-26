SET SCHEMA 'sae';

--Extension pgvector
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA sae;

-- Table supplémentaire pour stocker les vecteurs
DROP TABLE IF EXISTS temporal_features_vectors CASCADE;

CREATE TABLE temporal_features_vectors (
    tfv_id SERIAL PRIMARY KEY,
    track_id INT UNIQUE REFERENCES tracks(track_id) ON DELETE CASCADE,
    audio_vector vector(224) NOT NULL
);

-- Index HNSW pour la recherche rapide
CREATE INDEX IF NOT EXISTS idx_vectors_cosine 
ON temporal_features_vectors 
USING hnsw (audio_vector vector_cosine_ops);

DO $$
BEGIN
    RAISE NOTICE 'Table temporal_features_vectors et Index HNSW prêts.';
END $$;