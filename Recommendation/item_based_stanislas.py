import psycopg2
import pandas as pd
import numpy as np
import json
import time
import psutil
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

# ==============================================================
# CONFIGURATION DES PARAMÈTRES DE CONNEXION À LA BASE DE DONNÉES
# ==============================================================
DB_CONFIG = {
    'dbname': os.getenv("POSTGRES_DBNAME"),
    'user': os.getenv("POSTGRES_USER"),
    'password': os.getenv("POSTGRES_PASSWORD"),
    'host': 'localhost',
    'port': os.getenv("POSTGRES_PORT", '5432')
}}


# ========================================================
# FONCTION PERMETTANT DE SE CONNECTER À LA BASE DE DONNÉES
# ========================================================
def db_connect():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print("Erreur lors de la connexion à la base de données :", e)


# ===================================================================================
# FONCTION PERMETTANT DE RÉCUPÉRER LES DONNÉES DES ARTISTES DEPUIS LA BASE DE DONNÉES
# ===================================================================================
def fetch_artists():
    conn = db_connect()
    data = pd.read_sql("SELECT * FROM sae.artist;", conn)
    conn.close()
    return data


# ==================================================================================
# FONCTION PERMETTANT D'AJOUTER UNE COLONNE POUR STOCKER LES EMBEDDINGS DES ARTISTES
# ==================================================================================
def add_embedding_column():
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='artist' AND column_name='artist_embedding';")
    exists = cur.fetchone()
    if not exists:
        cur.execute("ALTER TABLE sae.artist ADD COLUMN artist_embedding FLOAT8[];")
        conn.commit()
    cur.close()
    conn.close()


# =============================================================
# FONCTION PERMETTANT DE METTRE À JOUR L'EMBEDDING D'UN ARTISTE
# =============================================================
def update_artist_embedding(artist_id, embedding):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("UPDATE sae.artist SET artist_embedding = %s WHERE artist_id = %s", (embedding.tolist(), artist_id))
    conn.commit()
    cur.close()
    conn.close()


# =======================================================
# FONCTION PERMETTANT DE CONSTRUIRE LE TEXTE D'UN ARTISTE
# =======================================================
def build_artist_text(row):
    fields = [
        row.get("artist_bio", ""),
        row.get("artist_related_project", ""),
        row.get("artist_location", ""),
        row.get("artist_associated_label", "")
    ]
    return " ".join(str(field) for field in fields if pd.notnull(field))


# ======================================================================
# FONCTION PERMETTANT DE CALCULER ET STOCKER LES EMBEDDINGS DES ARTISTES
# ======================================================================
def compute_and_store_embeddings(data, model):
    data_to_compute = data[data["artist_embedding"].isnull()]
    if data_to_compute.empty:
        return data
    else :
        data_to_compute["artist_text"] = data_to_compute.apply(build_artist_text, axis=1)
        embeddings = model.encode(data_to_compute["artist_text"].tolist(), show_progress_bar=True)
        data_to_compute["embedding"] = list(embeddings)
        for index, row in data_to_compute.iterrows():
            update_artist_embedding(row["artist_id"], row["embedding"])
        return data


# ==============================================================================
# FONCTION PERMETTANT DE RECOMMANDER DES ARTISTES PAR RAPPORT À UN ARTISTE DONNÉ
# ==============================================================================
def recommend_artists(artist_id, top_k):
    data = fetch_artists()
    if (("artist_embedding" not in data.columns) or (data["artist_embedding"].isnull().all())):
        return []
    else :
        # Convert FLOAT8[] en numpy array
        data["embedding_np"] = data["artist_embedding"].apply(lambda x: np.array(x) if isinstance(x, list) else np.array(json.loads(x)))
        if artist_id not in data["artist_id"].values:
            print(f"Artist_id {artist_id} inconnu")
            return []
        else :
            target_emb = data.loc[data["artist_id"] == artist_id, "embedding_np"].values[0]
            all_embs = np.stack(data["embedding_np"].values)
            sims = cosine_similarity([target_emb], all_embs)[0]
            data["similarity"] = sims
            recommendations = (
                data[data["artist_id"] != artist_id]
                .sort_values("similarity", ascending=False)
                .head(top_k)
            )
            return recommendations[["artist_id", "artist_name", "similarity"]]


# ===================
# FONCTION PRINCIPALE 
# ===================
def main():
    add_embedding_column()
    data = fetch_artists()
    if data is None or data.empty:
        print("Impossible de récupérer les données des artistes")
        return
    model = SentenceTransformer("all-MiniLM-L6-v2")
    data = compute_and_store_embeddings(data, model)
    print("\n" + "="*60)
    artist_id = int(input("Saisissez un ID d'artiste : "))
    top_k = int(input("Combien d'artistes similaires voulez-vous voir : "))

    process = psutil.Process(os.getpid())
    start_time = time.perf_counter()
    cpu_start = process.cpu_times()
    mem_start = process.memory_info().rss

    artist_row = data[data.artist_id == artist_id]
    artist_name = artist_row.iloc[0]["artist_name"]
    top_artists = recommend_artists(artist_id, top_k)
    print("="*60)
    print(f"Top {top_k} des artistes similaires à {artist_name} (ID {artist_id})")
    print("="*60, "\n", top_artists.to_string(index=False))

    end_time = time.perf_counter()
    cpu_end = process.cpu_times()
    mem_end = process.memory_info().rss
    elapsed_time = end_time - start_time
    cpu_used = (cpu_end.user + cpu_end.system) - (cpu_start.user + cpu_start.system)
    ram_used = (mem_end - mem_start) / 1024 / 1024
    print(f"{"="*60}\nTemps d'exécution : {elapsed_time:.3f} sec")
    print(f"CPU utilisé : {cpu_used:.3f} sec")
    print(f"RAM utilisée : {ram_used:.2f} MB")


if __name__ == "__main__":
    main()