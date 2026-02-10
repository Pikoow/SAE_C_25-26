import psycopg2
from dotenv import load_dotenv
import os
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from psycopg2.extras import RealDictCursor

load_dotenv()

DB_CONFIG = {
    'dbname': os.getenv("POSTGRES_DBNAME"),
    'user': os.getenv("POSTGRES_USER"),
    'password': os.getenv("POSTGRES_PASSWORD"),
    'host': 'localhost',
    'port': os.getenv("POSTGRES_PORT", '5432')
}

_TRACK_CACHE = None
_FEATURE_MATRIX = None
_TRACK_INDEX_MAP = {}

def db_connect():
    return psycopg2.connect(**DB_CONFIG)

def create_track_feature_vector(track):
    # track index: 0:id, 1:title, 2:duration, 3:genre, 4:bitrate
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

def load_data_into_cache():
    global _TRACK_CACHE, _FEATURE_MATRIX, _TRACK_INDEX_MAP
    query = """
    SELECT DISTINCT t.track_id, t.track_title, t.track_duration, t.track_genre_top, t.track_bit_rate, 
           aat.artist_id, a.artist_name
    FROM sae.tracks t
    LEFT JOIN sae.artist_album_track aat ON t.track_id = aat.track_id
    LEFT JOIN sae.artist a ON aat.artist_id = a.artist_id;
    """
    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(query)
        _TRACK_CACHE = cur.fetchall()
        cur.close()
        conn.close()

        all_features = []
        for idx, track in enumerate(_TRACK_CACHE):
            vec = create_track_feature_vector(track)
            all_features.append(vec)
            _TRACK_INDEX_MAP[track[0]] = idx
        
        _FEATURE_MATRIX = np.array(all_features)
    except Exception as e:
        print(f"Error loading cache: {e}")

def recommend_similar_tracks(track_ids, top_n=10):
    """
    Unified function: Accepts a single int or a list of ints.
    """
    global _TRACK_CACHE, _FEATURE_MATRIX, _TRACK_INDEX_MAP

    if _TRACK_CACHE is None:
        load_data_into_cache()

    # Convert single ID to list for uniform processing
    if isinstance(track_ids, int):
        track_ids = [track_ids]

    target_vectors = []
    existing_ids = set(track_ids)
    
    for tid in track_ids:
        if tid in _TRACK_INDEX_MAP:
            idx = _TRACK_INDEX_MAP[tid]
            target_vectors.append(_FEATURE_MATRIX[idx])

    if not target_vectors:
        return []

    # Calculate mean profile vector (works for 1 or many tracks)
    profile_vec = np.mean(target_vectors, axis=0).reshape(1, -1)
    similarities = cosine_similarity(profile_vec, _FEATURE_MATRIX)[0]
    related_indices = np.argsort(similarities)[::-1]

    results = []
    for idx in related_indices:
        track = _TRACK_CACHE[idx]
        tid = track[0]
        
        if tid in existing_ids:
            continue
            
        results.append({
            "track_id": tid,
            "track_title": track[1],
            "artist_id": track[5],
            "artist_name": track[6],
            "similarity": round(float(similarities[idx]), 4)
        })

        if len(results) >= top_n:
            break

    return results