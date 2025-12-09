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
    """
    Charge toutes les tracks complètes.
    Utilisé pour le calcul de similarité globale.
    """
    query = """
    SELECT 
        t.track_id,
        t.track_title,
        t.track_duration,
        t.track_genre_top,
        t.track_genre,
        t.track_listens,
        t.track_favorite,
        t.track_interest,
        t.track_date_recorded,
        t.track_composer,
        t.track_lyricist,
        t.track_bit_rate,
        a.artist_name,
        a.artist_id,
        al.album_title,
        al.album_id
    FROM sae.tracks t
    LEFT JOIN sae.album_artist_track aat ON t.track_id = aat.track_id
    LEFT JOIN sae.artist a ON a.artist_id = aat.artist_id
    LEFT JOIN sae.album al ON al.album_id = aat.album_id;
    """

    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(query)
        data = cur.fetchall()
        cur.close()
        conn.close()
        return data

    except psycopg2.Error as e:
        print("Erreur SQL (load_all_tracks) :", e)
        return []


##########################################################
# RECHERCHE DE TRACK
##########################################################

def search_track_by_name_and_artist(track_name, artist_name):
    """
    Recherche une track par titre et artiste (approximation via LIKE).
    Retourne jusqu'à 10 résultats classés par nombre d'écoutes décroissant.
    """
    query = """
    SELECT 
        t.track_id,
        t.track_title,
        t.track_duration,
        t.track_genre_top,
        t.track_genre,
        t.track_listens,
        t.track_favorite,
        t.track_interest,
        t.track_date_recorded,
        t.track_composer,
        t.track_lyricist,
        t.track_bit_rate,
        a.artist_name,
        a.artist_id,
        al.album_title,
        al.album_id
    FROM sae.tracks t
    LEFT JOIN sae.album_artist_track aat ON t.track_id = aat.track_id
    LEFT JOIN sae.artist a ON a.artist_id = aat.artist_id
    LEFT JOIN sae.album al ON al.album_id = aat.album_id
    WHERE LOWER(t.track_title) LIKE LOWER(%s)
      AND LOWER(a.artist_name) LIKE LOWER(%s)
    ORDER BY t.track_listens DESC
    LIMIT 10;
    """

    try:
        conn = db_connect()
        cur = conn.cursor()
        cur.execute(query, (f"%{track_name}%", f"%{artist_name}%"))
        results = cur.fetchall()
        cur.close()
        conn.close()
        return results

    except psycopg2.Error as e:
        print("Erreur SQL (search) :", e)
        return []


##########################################################
# CONSTRUCTION VECTEUR DE CARACTÉRISTIQUES
##########################################################

def create_track_feature_vector(track):
    """
    Crée un vecteur numérique représentant une track.
    Inclut :
      - durée normalisée
      - bitrate normalisé
      - encodage simple des genres (multi-hash → vector 16D)
    """
    # 1) Durée normalisée (max 10 minutes)
    duration = track[2] if track[2] else 0
    features = [min(duration / 600, 1.0)]

    # 2) Bitrate normalisé (max 320 kbps)
    bitrate = track[11] if track[11] else 0
    features.append(min(bitrate / 320, 1.0))

    # 2) Extraction des genres
    genres_text = f"{track[3] or ''} {track[4] or ''}".lower().replace(",", " ")
    genres = [g for g in genres_text.split() if g]

    # 3) Encodage multi-hot par hash (16 dimensions)
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
    """Recherche d’une track, puis proposition de recommandations similaires."""
    print("\n=== RECHERCHE & RECOMMANDATION ===")

    tname = input("Nom de la track : ").strip()
    aname = input("Artiste (optionnel) : ").strip()

    matches = search_track_by_name_and_artist(tname, aname)
    if not matches:
        print("Aucune track trouvée.")
        return

    # Affichage des résultats
    print("\nSélectionnez une track :")
    for i, tr in enumerate(matches, 1):
        print(f"{i}. {tr[1]} - {tr[12] or 'Artiste inconnu'}")

    try:
        choice = int(input("\nNuméro du choix : "))
        selected = matches[choice - 1]
    except:
        print("Choix invalide.")
        return

    print(f"\nTrack sélectionnée : {selected[1]} ({selected[12]})")

    # Charger tout le catalogue pour les recommandations
    all_tracks = load_all_tracks()
    recos = recommend_similar_tracks(selected[0], all_tracks, top_n=5)

    print("\n=== TRACKS RECOMMANDÉES ===")
    for i, (_, sim, tr) in enumerate(recos, 1):
        print(f"{i}. {tr[1]} - {tr[12]}  | Similarité : {sim:.2%}")


##########################################################
# MENU PRINCIPAL
##########################################################

def main():
    while True:
        print("\n--- MENU ---")
        print("1. Recommandations")
        print("2. Quitter")

        choice = input("Votre choix : ").strip()

        if choice == '1':
            add_recommendation_to_search()

        elif choice == '2':
            print("Fermeture")
            break

        else:
            print("Choix invalide.")

if __name__ == "__main__":
    main()