# track_search.py
import psycopg2
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

DB_CONFIG = {
    'dbname': 'mydb',
    'user': 'admin',
    'password': 'admin',
    'host': 'localhost',
    'port': '5432'
}

##########################################################
# FONCTIONS GÉNÉRALES BASE DE DONNÉES
##########################################################

def db_connect():
    """Retourne une connexion PostgreSQL."""
    return psycopg2.connect(**DB_CONFIG)


##########################################################
# CHARGEMENT DE TOUTES LES TRACKS
##########################################################

def load_all_tracks():
    query = """
    SELECT
        track_id,
        track_title,
        track_duration,
        track_genre_top,
        track_listens
    FROM sae.tracks
    GROUP BY track_id;
    """
    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(query)
        data = cur.fetchall()
        cur.close()
        conn.close()
        return data
    except Exception as e:
        print("Erreur SQL (load_all_tracks):", e)
        return []


##########################################################
# RECHERCHE DE TRACK
##########################################################

def search_track_by_name(track_name):
    base_query = """
    SELECT
        track_id,
        track_title,
        track_duration,
        track_genre_top,
        track_listens
    FROM sae.tracks
    WHERE LOWER(track_title) LIKE LOWER(%s)
    ORDER BY track_listens DESC
    LIMIT 10;
    """

    params = [f"%{track_name}%"]

    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(base_query, params)
        results = cur.fetchall()
        cur.close()
        conn.close()
        return results
    except Exception as e:
        print("Erreur SQL (search):", e)
        return []


##########################################################
# CONSTRUCTION VECTEUR DE CARACTÉRISTIQUES
##########################################################

def create_track_feature_vector(track):
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


##########################################################
# RECOMMANDATION PAR SIMILARITÉ
##########################################################

def recommend_similar_tracks(target_track_id, all_tracks, top_n=5):
    """
    Retourne les N tracks les plus similaires à une track donnée.
    Similarité : cosine similarity sur vecteurs de features.
    """
    tracks = {t[0]: t for t in all_tracks}

    if target_track_id not in tracks:
        return []

    target_vec = create_track_feature_vector(tracks[target_track_id])

    similarities = []
    for tid, track in tracks.items():
        if tid == target_track_id:
            continue
        sim = cosine_similarity([target_vec], [create_track_feature_vector(track)])[0][0]
        similarities.append((tid, sim, track))

    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_n]


##########################################################
# INTERFACE UTILISATEUR : RECOMMANDATION
##########################################################

def add_recommendation_to_search():
    """Recherche d'une track, puis proposition de recommandations similaires."""
    print("\n=== RECOMMENDATION ===")

    tname = input("Nom de la track : ").strip()

    matches = search_track_by_name(tname)
    if not matches:
        print("Aucune track trouvée.")
        return

    # Affichage des résultats
    print("\nSélectionnez une track :")
    for i, tr in enumerate(matches, 1):
        print(f"{i}. {tr[1]}")

    try:
        choice = int(input("\nNuméro du choix : "))
        selected = matches[choice - 1]
    except:
        print("Choix invalide.")
        return

    print(f"\nTrack sélectionnée : {selected[1]}")

    # Charger tout le catalogue pour les recommandations
    all_tracks = load_all_tracks()
    recos = recommend_similar_tracks(selected[0], all_tracks, top_n=5)

    print("\n=== TRACKS RECOMMANDÉES ===")
    for i, (_, sim, tr) in enumerate(recos, 1):
        print(f"{i}. {tr[1]} | Similarité : {sim:.2%}")


##########################################################
# MENU PRINCIPAL
##########################################################

def main():
    while True:
        add_recommendation_to_search()

if __name__ == "__main__":
    main()