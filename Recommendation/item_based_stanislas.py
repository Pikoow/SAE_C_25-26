import psycopg2
import pandas as pd
import numpy as np
import json
import os
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()

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
# ENSURE EMBEDDING COLUMN
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

# ==================================================
# PUBLIC API FUNCTION
# ==================================================
def recommend_artists(artist_id: int, top_k: int = 5):
    """
    Returns a list of similar artists (API friendly)
    """

    ensure_embedding_column()

    df = fetch_artists()
    if df.empty:
        return []

    model = SentenceTransformer("all-MiniLM-L6-v2")
    df = compute_missing_embeddings(df, model)

    if artist_id not in df["artist_id"].values:
        return []

    # Convert embeddings
    df["embedding_np"] = df["artist_embedding"].apply(
        lambda x: np.array(x) if isinstance(x, list) else np.array(json.loads(x))
    )

    target_emb = df.loc[df.artist_id == artist_id, "embedding_np"].values[0]
    all_embs = np.stack(df["embedding_np"].values)

    similarities = cosine_similarity([target_emb], all_embs)[0]
    df["similarity"] = similarities

    reco = (
        df[df.artist_id != artist_id]
        .sort_values("similarity", ascending=False)
        .head(top_k)
    )

    return [
        {
            "artist_id": int(row.artist_id),
            "artist_name": row.artist_name,
            "similarity": float(round(row.similarity, 4))
        }
        for _, row in reco.iterrows()
    ]
