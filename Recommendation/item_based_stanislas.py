import psycopg2
import pandas as pd
import numpy as np
import json
import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()

MODEL = SentenceTransformer("all-MiniLM-L6-v2")

# ==================================================
# DB CONFIG
# ==================================================
DB_CONFIG = {
    'dbname': os.getenv("POSTGRES_DBNAME"),
    'user': os.getenv("POSTGRES_USER"),
    'password': os.getenv("POSTGRES_PASSWORD"),
    'host': 'localhost',
    'port': os.getenv("POSTGRES_PORT", '5432')
}

# ==================================================
# DB CONNECTION
# ==================================================
def db_connect():
    return psycopg2.connect(**DB_CONFIG)

# ==================================================
# FETCH ARTISTS
# ==================================================
def fetch_artists():
    conn = db_connect()
    df = pd.read_sql("SELECT * FROM sae.artist;", conn)
    conn.close()
    return df

# ==================================================
# COLONNE EMBEDDING
# ==================================================
def ensure_embedding_column():
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='artist'
        AND column_name='artist_embedding';
    """)
    if not cur.fetchone():
        cur.execute("ALTER TABLE sae.artist ADD COLUMN artist_embedding FLOAT8[];")
        conn.commit()
    cur.close()
    conn.close()

# ==================================================
# BUILD ARTIST TEXT
# ==================================================
def build_artist_text(row):
    fields = [
        row.get("artist_bio", ""),
        row.get("artist_related_project", ""),
        row.get("artist_location", ""),
        row.get("artist_associated_label", ""),
        row.get("artist_tags", "")
    ]
    return " ".join(str(f) for f in fields if pd.notnull(f))

# ==================================================
# COMPUTE MISSING EMBEDDINGS
# ==================================================
def compute_missing_embeddings(df, model):
    missing = df[df["artist_embedding"].isnull()]
    if missing.empty:
        return df

    texts = missing.apply(build_artist_text, axis=1).tolist()
    embeddings = model.encode(texts, show_progress_bar=False)

    conn = db_connect()
    cur = conn.cursor()

    for artist_id, emb in zip(missing["artist_id"], embeddings):
        cur.execute(
            "UPDATE sae.artist SET artist_embedding = %s WHERE artist_id = %s",
            (emb.tolist(), artist_id)
        )

    conn.commit()
    cur.close()
    conn.close()

    return df

def initialize_artist_system():
    """
    Checks database schema and populates missing embeddings.
    """
    print("Création des embeddings d'artistes...")
    ensure_embedding_column()
    df = fetch_artists()

    compute_missing_embeddings(df, MODEL)
    print("Recommendation d'artistes prête.")

# ==================================================
# PUBLIC API FUNCTION (UPDATED)
# ==================================================
def recommend_artists(artist_ids, top_k: int = 5):
    """
    Unified recommendation: Accepts a single artist_id (int) or a list of artist_ids.
    """
    ensure_embedding_column()

    conn = db_connect()
    try:
        # Load all artists with embeddings
        df = pd.read_sql("SELECT artist_id, artist_name, artist_embedding FROM sae.artist WHERE artist_embedding IS NOT NULL;", conn)
        
        if df.empty:
            return []

        # Convert single ID to list for uniform processing
        if isinstance(artist_ids, int):
            artist_ids = [artist_ids]
            
        # Extract embeddings for the input artists
        input_artists_df = df[df['artist_id'].isin(artist_ids)]
        
        if input_artists_df.empty:
            return []

        # Calculate the target profile (mean of all input embeddings)
        input_embeddings = np.array(input_artists_df["artist_embedding"].tolist())
        target_emb = np.mean(input_embeddings, axis=0).reshape(1, -1)
        
        # Prepare the matrix for comparison
        all_ids = df["artist_id"].values
        all_names = df["artist_name"].values
        matrix = np.array(df["artist_embedding"].tolist())

        # Calculate similarities
        similarities = cosine_similarity(target_emb, matrix)[0]
        indices = np.argsort(similarities)[::-1]
        
        results = []
        input_ids_set = set(artist_ids)
        
        for idx in indices:
            # Exclude the artists already in the input list
            if all_ids[idx] in input_ids_set:
                continue
                
            results.append({
                "artist_id": int(all_ids[idx]),
                "artist_name": str(all_names[idx]),
                "similarity": float(round(similarities[idx], 4))
            })
            if len(results) >= top_k:
                break
                
        return results
    finally:
        conn.close()