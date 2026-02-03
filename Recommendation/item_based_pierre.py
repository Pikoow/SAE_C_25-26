import psycopg2
from dotenv import load_dotenv
import os
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

load_dotenv()

DB_CONFIG = {
    'dbname': os.getenv("POSTGRES_DBNAME"),
    'user': os.getenv("POSTGRES_USER"),
    'password': os.getenv("POSTGRES_PASSWORD"),
    'host': 'localhost',
    'port': os.getenv("POSTGRES_PORT", '5432')
}

# Global cache for performance
_TRACK_CACHE = None
_FEATURE_MATRIX = None
_TRACK_INDEX_MAP = {} # Maps track_id to row index in matrix

def db_connect():
    return psycopg2.connect(**DB_CONFIG)

def load_data_into_cache():
    """Fetches all tracks and prepares a global feature matrix."""
    global _TRACK_CACHE, _FEATURE_MATRIX, _TRACK_INDEX_MAP
    
    query = """
    SELECT track_id, track_title, track_duration, track_genre_top, track_bit_rate
    FROM sae.tracks;
    """
    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(query)
        _TRACK_CACHE = cur.fetchall()
        cur.close()
        conn.close()

        # Build Matrix
        all_features = []
        for idx, track in enumerate(_TRACK_CACHE):
            vec = create_track_feature_vector(track)
            all_features.append(vec)
            _TRACK_INDEX_MAP[track[0]] = idx
        
        _FEATURE_MATRIX = np.array(all_features)
        print(f"Cache loaded: {len(_TRACK_CACHE)} tracks processed.")
    except Exception as e:
        print("Erreur SQL (load_data_into_cache):", e)

def create_track_feature_vector(track):
    # track indices: 0:id, 1:title, 2:duration, 3:genre, 4:bitrate
    duration = track[2] or 0
    bitrate = track[4] or 0

    features = [
        min(duration / 600, 1.0),
        min(bitrate / 320, 1.0)
    ]

    genres_text = f"{track[3] or ''}".lower()
    genres = genres_text.replace(",", " ").split()

    genre_vec = np.zeros(16)
    for g in genres:
        genre_vec[abs(hash(g)) % 16] = 1

    return np.concatenate([features, genre_vec])

def recommend_similar_tracks(target_track_id, top_n=5):
    """
    Uses the vectorized feature matrix for lightning-fast recommendations.
    """
    global _TRACK_CACHE, _FEATURE_MATRIX, _TRACK_INDEX_MAP

    # Initialize cache if empty
    if _TRACK_CACHE is None:
        load_data_into_cache()

    if target_track_id not in _TRACK_INDEX_MAP:
        return []

    target_idx = _TRACK_INDEX_MAP[target_track_id]
    target_vec = _FEATURE_MATRIX[target_idx].reshape(1, -1)

    # Calculate all similarities at once (Vectorized)
    similarities = cosine_similarity(target_vec, _FEATURE_MATRIX)[0]

    # Get indices of top_n + 1 (to exclude itself)
    # argsort gives indices of sorted values; we take the last ones
    related_indices = np.argsort(similarities)[-(top_n + 1):][::-1]

    results = []
    for idx in related_indices:
        track = _TRACK_CACHE[idx]
        tid = track[0]
        
        if tid == target_track_id:
            continue
            
        results.append({
            "track_id": tid,
            "track_title": track[1],
            "similarity": round(float(similarities[idx]), 4)
        })

    return results[:top_n]