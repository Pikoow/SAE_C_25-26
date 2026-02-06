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

def recommend_similar_tracks_multi(target_track_ids, top_n=5):
    """
    Prend une LISTE d'IDs et trouve les musiques similaires à l'ensemble.
    """
    global _TRACK_CACHE, _FEATURE_MATRIX, _TRACK_INDEX_MAP

    if isinstance(target_track_ids, int):
        target_track_ids = [target_track_ids]

    if _TRACK_CACHE is None:
        load_data_into_cache()

    target_vectors = []
    existing_target_ids = []

    for tid in target_track_ids:
        if tid in _TRACK_INDEX_MAP:
            idx = _TRACK_INDEX_MAP[tid]
            target_vectors.append(_FEATURE_MATRIX[idx])
            existing_target_ids.append(tid)

    if not target_vectors:
        return []

    profile_vec = np.mean(target_vectors, axis=0).reshape(1, -1)
    similarities = cosine_similarity(profile_vec, _FEATURE_MATRIX)[0]
    related_indices = np.argsort(similarities)[::-1]

    results = []
    for idx in related_indices:
        track = _TRACK_CACHE[idx]
        tid = track[0]
        
        # On ignore les musiques qui sont déjà dans la sélection de départ
        if tid in existing_target_ids:
            continue
            
        results.append({
            "track_id": tid,
            "track_title": track[1],
            "similarity": round(float(similarities[idx]), 4)
        })

        if len(results) >= top_n:
            break

    return results

if __name__ == "__main__":
    print("Initialisation du système...")
    load_data_into_cache()

    test_ids = [69170,95976, 59546] 

    print(f"Recherche de musiques similaires à : {test_ids}")
    resultats = recommend_similar_tracks_multi(test_ids, top_n=5)

    if resultats:
        print("\n--- RECOMMANDATIONS TROUVÉES ---")
        for i, reco in enumerate(resultats, 1):
            print(f"{i}. {reco['track_title']} (ID: {reco['track_id']}) - Score: {reco['similarity']}")
    else:
        print("Aucun résultat trouvé. Vérifie tes IDs ou ton cache.")