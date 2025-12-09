import psycopg2
import pandas as pd

from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import hstack, csr_matrix

DB_CONFIG = {
    'dbname': 'mydb',
    'user': 'admin',
    'password': 'admin',
    'host': 'localhost',
    'port': '5432'
}

def db_connect():
    """
    Retourne une connexion PostgreSQL via psycopg2
    """
    return psycopg2.connect(**DB_CONFIG)


def fetch_artist_features():
    conn = db_connect()
    query = """
            SELECT 
                artist_id,
                artist_name,
                COALESCE(artist_tags, '') AS artist_tags,
                COALESCE(artist_location, '') AS artist_location,
                COALESCE(artist_associated_label, '') AS artist_associated_label,
                artist_active_year_begin,
                artist_active_year_end,
                artist_favorites,
                avg_artist_discovery,
                avg_artist_familiarity,
                avg_sa_artist_hottness,
                avg_artist_discovery_rank,
                avg_artist_familiarity_rank,
                avg_ar_artist_hottness,
                num_tracks_associated
            FROM artist_features;
            """
    datas = pd.read_sql(query, conn)
    conn.close()
    return datas


def vectorize_artist_features(df):
    """
    Vectorisation complète TF-IDF + scaling numéraire
    """
    tfidf_tags = TfidfVectorizer()
    tags_matrix = tfidf_tags.fit_transform(df["artist_tags"])

    tfidf_location = TfidfVectorizer()
    loc_matrix = tfidf_location.fit_transform(df["artist_location"])

    tfidf_label = TfidfVectorizer()
    label_matrix = tfidf_label.fit_transform(df["artist_associated_label"])

    numeric_cols = [
        "artist_active_year_begin",
        "artist_active_year_end",
        "artist_favorites",
        "avg_artist_discovery",
        "avg_artist_familiarity",
        "avg_sa_artist_hottness",
        "avg_artist_discovery_rank",
        "avg_artist_familiarity_rank",
        "avg_ar_artist_hottness",
        "num_tracks_associated",
    ]

    numeric_features = df[numeric_cols].fillna(0)

    scaler = StandardScaler()
    numeric_scaled = scaler.fit_transform(numeric_features)

    numeric_sparse = csr_matrix(numeric_scaled)

    full_matrix = hstack([
        tags_matrix,
        loc_matrix,
        label_matrix,
        numeric_sparse,
    ])

    return full_matrix


def get_similar_artists(artist_id, top_k):
    df = fetch_artist_features()
    matrix = vectorize_artist_features(df)

    idx_list = df.index[df.artist_id == artist_id].tolist()
    if not idx_list:
        return []
    idx = idx_list[0]

    sims = cosine_similarity(matrix[idx], matrix)[0]

    df["similarity"] = sims

    result = df[df.artist_id != artist_id]

    return (
        result.sort_values("similarity", ascending=False)
              .head(top_k)[["artist_id", "artist_name", "similarity"]]
              .to_dict(orient="records")
    )

similaires = get_similar_artists(artist_id=12, top_k=5)
print(similaires)
