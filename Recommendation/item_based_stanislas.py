import psycopg2
import psycopg2.extras
import pandas as pd
import numpy as np
import os
from sentence_transformers import SentenceTransformer
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
# IN-MEMORY CACHE
# Cache invalidé uniquement si de nouveaux embeddings sont écrits en DB.
# ==================================================
_cache: dict = {
    "ids": None,       # np.ndarray (N,)
    "names": None,     # np.ndarray (N,)
    "matrix": None,    # np.ndarray (N, D) — lignes L2-normalisées
}
_embedding_col_checked: bool = False

# ==================================================
# DB CONNECTION
# ==================================================
def db_connect():
    return psycopg2.connect(**DB_CONFIG)

# ==================================================
# COLONNE EMBEDDING (vérifiée une seule fois par process)
# ==================================================
def ensure_embedding_column():
    global _embedding_col_checked
    if _embedding_col_checked:
        return
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'sae'
          AND table_name   = 'artist'
          AND column_name  = 'artist_embedding';
    """)
    if not cur.fetchone():
        cur.execute("ALTER TABLE sae.artist ADD COLUMN artist_embedding FLOAT8[];")
        conn.commit()
    cur.close()
    conn.close()
    _embedding_col_checked = True

# ==================================================
# BUILD ARTIST TEXT
# ==================================================
_TEXT_FIELDS = (
    "artist_bio",
    "artist_related_project",
    "artist_location",
    "artist_associated_label",
    "artist_tags",
)

def build_artist_text(row) -> str:
    return " ".join(
        str(row[f]) for f in _TEXT_FIELDS
        if row.get(f) is not None and pd.notnull(row[f])
    )

# ==================================================
# COMPUTE MISSING EMBEDDINGS  (batch UPDATE)
# ==================================================
def compute_missing_embeddings(df: pd.DataFrame, model: SentenceTransformer) -> None:
    missing = df[df["artist_embedding"].isnull()]
    if missing.empty:
        return

    texts = missing.apply(build_artist_text, axis=1).tolist()
    embeddings = model.encode(texts, show_progress_bar=False, batch_size=64)

    # Un seul UPDATE batch via execute_values
    rows = [
        (emb.tolist(), int(aid))
        for emb, aid in zip(embeddings, missing["artist_id"])
    ]
    conn = db_connect()
    cur = conn.cursor()
    psycopg2.extras.execute_values(
        cur,
        "UPDATE sae.artist SET artist_embedding = data.emb "
        "FROM (VALUES %s) AS data(emb, artist_id) "
        "WHERE sae.artist.artist_id = data.artist_id",
        rows,
        template="(%s::float8[], %s)",
    )
    conn.commit()
    cur.close()
    conn.close()

# ==================================================
# CACHE : chargement et normalisation L2
# ==================================================
def _load_cache() -> None:
    """Charge la matrice d'embeddings en mémoire et la normalise (dot product = cosine)."""
    conn = db_connect()
    df = pd.read_sql(
        "SELECT artist_id, artist_name, artist_embedding "
        "FROM sae.artist WHERE artist_embedding IS NOT NULL;",
        conn,
    )
    conn.close()

    if df.empty:
        _cache["ids"] = np.array([], dtype=np.int64)
        _cache["names"] = np.array([], dtype=object)
        _cache["matrix"] = np.empty((0, 0), dtype=np.float32)
        return

    ids   = df["artist_id"].values.astype(np.int64)
    names = df["artist_name"].values
    matrix = np.vstack(df["artist_embedding"].values).astype(np.float32)

    # Normalisation L2 → cosine similarity = simple dot product
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)   # évite division par zéro
    matrix /= norms

    _cache["ids"]    = ids
    _cache["names"]  = names
    _cache["matrix"] = matrix

def _get_cache():
    """Retourne le cache, le charge si nécessaire."""
    if _cache["ids"] is None:
        _load_cache()
    return _cache

def invalidate_cache() -> None:
    """À appeler si la DB est modifiée en dehors du process."""
    _cache["ids"] = None

# ==================================================
# INITIALIZE
# ==================================================
def initialize_artist_system() -> None:
    """
    Vérifie le schéma DB, calcule les embeddings manquants, précharge le cache.
    """
    print("Création des embeddings d'artistes...")
    ensure_embedding_column()

    conn = db_connect()
    df = pd.read_sql("SELECT * FROM sae.artist;", conn)
    conn.close()

    compute_missing_embeddings(df, MODEL)
    _load_cache()   # préchauffe le cache
    print("Recommendation d'artistes prête.")

# ==================================================
# PUBLIC API
# ==================================================
def recommend_artists(artist_ids, top_k: int = 5) -> list[dict]:
    """
    Recommande des artistes similaires.
    Accepte un artist_id (int) ou une liste d'artist_ids.
    """
    ensure_embedding_column()

    if isinstance(artist_ids, int):
        artist_ids = [artist_ids]
    input_ids_set = set(artist_ids)

    cache = _get_cache()
    ids    = cache["ids"]
    names  = cache["names"]
    matrix = cache["matrix"]

    if ids.size == 0:
        return []

    # Masque booléen des artistes en entrée
    input_mask = np.isin(ids, list(input_ids_set))
    if not input_mask.any():
        return []

    # Profil cible = moyenne des embeddings normalisés → re-normalisation
    target_emb = matrix[input_mask].mean(axis=0)
    norm = np.linalg.norm(target_emb)
    if norm > 0:
        target_emb /= norm

    # Cosine similarity via dot product (matrice déjà normalisée)
    similarities = matrix @ target_emb   # (N,)

    # Exclure les artistes en entrée avant de chercher le top-k
    similarities[input_mask] = -1.0

    # np.argpartition : O(N) au lieu de O(N log N) pour le tri complet
    n_candidates = min(top_k, ids.size - input_mask.sum())
    if n_candidates <= 0:
        return []

    top_indices = np.argpartition(similarities, -n_candidates)[-n_candidates:]
    top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]

    return [
        {
            "artist_id":   int(ids[i]),
            "artist_name": str(names[i]),
            "similarity":  float(round(float(similarities[i]), 4)),
        }
        for i in top_indices
    ]