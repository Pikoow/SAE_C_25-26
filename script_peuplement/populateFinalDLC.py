import os
import pandas as pd
import psycopg2
import sys
import re

# ============================================================
# ===================== CONFIG GLOBAL ========================
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "port": "5432",
    "database": "postgres",
    "user": "postgres",
    "password": "PASSWORD_HERE",
    "options": "-c search_path=sae,public"
}


pd.set_option('future.no_silent_downcasting', True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ECHONEST_CSV = os.path.join(BASE_DIR, "clean_echonest.csv")

def get_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Erreur connexion BDD : {e}")
        sys.exit(1)

# Peuplement table vecteurs
def populate_vectors(conn):
    print(f"\nDébut peuplement vecteurs")

    target_csv = ECHONEST_CSV
    if not os.path.exists(target_csv):
        alt_vec = os.path.join(BASE_DIR, "echonest_vectors_cleaned.csv")
        if os.path.exists(alt_vec):
            target_csv = alt_vec
        else:
            print(f"ERREUR : Fichier de vecteurs introuvable ({ECHONEST_CSV}).")
            return

    print(f"Lecture de {os.path.basename(target_csv)}...")
    try:
        df = pd.read_csv(target_csv, low_memory=False)
        df.columns = [c.lower().strip() for c in df.columns]
    except Exception as e:
        print(f"Erreur lecture CSV : {e}")
        return

    # Identification des 224 colonnes temporelles pour construire le vecteur
    vector_cols = sorted(
        [c for c in df.columns if c.startswith("echonest_temporal_features_")],
        key=lambda x: int(re.findall(r"\d+", x)[0]) if re.findall(r"\d+", x) else 0
    )

    use_precomputed = False
    if not vector_cols:
        if 'audio_vector_str' in df.columns:
            print("Colonne 'audio_vector_str' détectée (vecteurs déjà calculés).")
            use_precomputed = True
        else:
            print("Aucune colonne de données vectorielles trouvée.")
            return
    else:
        print(f"{len(vector_cols)} dimensions identifiées pour la vectorisation.")

    cur = conn.cursor()
    
    # On récupère les IDs valides pour ne pas planter sur les clés étrangères
    cur.execute("SELECT track_id FROM sae.tracks")
    valid_ids = {row[0] for row in cur.fetchall()}
    
    # Requête d'insertion
    sql = """
        INSERT INTO sae.temporal_features_vectors (track_id, audio_vector)
        VALUES (%s, %s::vector)
        ON CONFLICT (track_id) DO UPDATE 
        SET audio_vector = EXCLUDED.audio_vector;
    """

    inserted = 0
    skipped = 0
    
    for _, row in df.iterrows():
        try:
            # Récupération de l'ID
            tid_raw = row.get("track_id")
            if pd.isna(tid_raw) or str(tid_raw).strip() == "": 
                continue
            
            tid = int(float(tid_raw))
            
            # Si le track n'est pas dans la table 'tracks', on l'ignore
            if tid not in valid_ids:
                skipped += 1
                continue

            # Construction de la chaîne vecteur
            if use_precomputed:
                vector_str = row['audio_vector_str']
            else:
                # On force la conversion numérique et on remplace les vides par 0.0
                vals = row[vector_cols].apply(pd.to_numeric, errors='coerce').fillna(0.0).tolist()
                vector_str = str(vals).replace(" ", "")

            cur.execute(sql, (tid, vector_str))
            inserted += 1
            
            if inserted % 1000 == 0: 
                print(f"   -> {inserted} vecteurs insérés...", end='\r')

        except Exception:
            continue

    conn.commit()
    print(f"\n{inserted} vecteurs insérés dans la base.")
    if skipped > 0:
        print(f"Info : {skipped} vecteurs ignorés (car track_id absent de la table principale).")
    cur.close()

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    conn = get_connection()
    
    # Lancement uniquement du peuplement vectoriel
    populate_vectors(conn)
    
    conn.close()
    print("\nOPÉRATION TERMINÉE.")