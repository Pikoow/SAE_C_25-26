import psycopg2
import pandas as pd
import numpy as np
import json
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

DB_CONFIG = {
    'dbname': os.getenv("POSTGRES_DBNAME"),
    'user': os.getenv("POSTGRES_USER"),
    'password': os.getenv("POSTGRES_PASSWORD"),
    'host': 'localhost',
    'port': os.getenv("POSTGRES_PORT", '5432')
}

def db_connect():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print("Erreur lors de la connexion à la base de données :", e)
        return None

def fetch_artists():
    conn = db_connect()
    if conn is None:
        return pd.DataFrame()
    # Ensure we only fetch artists that HAVE embeddings for the API
    data = pd.read_sql("SELECT artist_id, artist_name, artist_embedding FROM sae.artist WHERE artist_embedding IS NOT NULL;", conn)
    conn.close()
    return data

def recommend_artists(artist_id: int, top_k: int):
    """
    Modified for API usage: Returns a list of dicts instead of a DataFrame
    """
    data = fetch_artists()
    
    if data.empty or "artist_embedding" not in data.columns:
        return []

    # Convert PostgreSQL array (list) or JSON string to numpy array
    def parse_embedding(x):
        if isinstance(x, list):
            return np.array(x)
        if isinstance(x, str):
            return np.array(json.loads(x))
        return None

    data["embedding_np"] = data["artist_embedding"].apply(parse_embedding)
    
    # Filter out any rows where embedding failed to parse
    data = data.dropna(subset=["embedding_np"])

    if artist_id not in data["artist_id"].values:
        return []

    # Extract target embedding
    target_emb = data.loc[data["artist_id"] == artist_id, "embedding_np"].values[0]
    all_embs = np.stack(data["embedding_np"].values)
    
    # Calculate Similarity
    sims = cosine_similarity([target_emb], all_embs)[0]
    data["similarity"] = sims

    # Format results
    recommendations = (
        data[data["artist_id"] != artist_id]
        .sort_values("similarity", ascending=False)
        .head(top_k)
    )

    # Convert to standard Python types for FastAPI JSON serialization
    return recommendations[["artist_id", "artist_name", "similarity"]].to_dict(orient="records")

# --- UTILITY FUNCTIONS (Kept for manual maintenance/updates) ---

def add_embedding_column():
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='artist' AND column_name='artist_embedding';")
    if not cur.fetchone():
        cur.execute("ALTER TABLE sae.artist ADD COLUMN artist_embedding FLOAT8[];")
        conn.commit()
    cur.close()
    conn.close()

def update_artist_embedding(artist_id, embedding):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("UPDATE sae.artist SET artist_embedding = %s WHERE artist_id = %s", (embedding.tolist(), artist_id))
    conn.commit()
    cur.close()
    conn.close()

# Only runs if you run this file directly (python item_based_stanislas.py)
if __name__ == "__main__":
    # Your original CLI logic for testing
    add_embedding_column()
    model = SentenceTransformer("all-MiniLM-L6-v2")
    # ... rest of your testing logic ...
    print("Script run in standalone mode.")