import os
import re
import unicodedata
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

pd.set_option('future.no_silent_downcasting', True)

# ============================================================
# BASE DIR → dossier où se trouve ce script
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def file(path):
    """Construit un chemin absolu vers le fichier dans script_peuplement"""
    return os.path.join(BASE_DIR, path)


# ============================================================
# 1) CLEAN RAW ALBUMS
# ============================================================

def clean_raw_albums():
    EXPECTED_COLUMNS = 19

    input_file = file("raw_albums.csv")
    output_file = file("raw_albums_cleaned.csv")

    df = pd.read_csv(input_file, sep=",", on_bad_lines="warn")
    new_df = pd.DataFrame(df)

    pattern_clean = re.compile(
        r"<\s*/?\s*(p|br|div|span|b|i|u|em|strong|ul|a|li|font|table|tbody|tr|thead|td|font-face|center|iframe|col|img|h4|h3|h2|ol|sup|blockquote|hr|w|m|xml)\b[^>]*>|[\t\n\]+]|[\*]|",
        flags=re.IGNORECASE
    )

    new_df["album_information"] = (
        new_df["album_information"]
        .fillna("")
        .astype(str)
        .str.replace(pattern_clean, "", regex=True)
    )

    new_df["album_information"] = new_df["album_information"].str.replace(
        r"</?p[^>]*>", "", regex=True
    )

    def ligne_valide(row):
        if (
            isinstance(row['album_comments'], int) or 
            isinstance(row['album_listens'], int) or 
            isinstance(row['album_id'], str)
        ):
            return False
        return True

    new_df.drop(df[df.apply(ligne_valide, axis=1)].index, inplace=True)
    new_df.to_csv(output_file, sep=",", index=False, encoding="utf-8")


# ============================================================
# 2) CLEAN GENRES + RAW_GENRES
# ============================================================

def load_clean(filename):
    path = file(filename)
    df = pd.read_csv(path, sep=",", encoding="utf-8", engine="python")
    df.columns = df.columns.str.strip().str.replace("\ufeff", "", regex=False)
    return df

def clean_genres():
    df_g = load_clean("genres.csv")
    df_r = load_clean("raw_genres.csv")

    if "genre_id" not in df_g.columns or "genre_id" not in df_r.columns:
        raise KeyError("genre_id manquant dans un des fichiers")

    df = df_g.merge(df_r, on="genre_id", how="left")
    df.to_csv(file("genre_clean.csv"), index=False)


# ============================================================
# 3) CLEAN TRACKS (header fusionné)
# ============================================================

def clean_tracks():
    CSV_INPUT = file("tracks.csv")
    CSV_OUTPUT = file("tracks_clean.csv")

    df_raw = pd.read_csv(CSV_INPUT, header=None)

    header1 = df_raw.iloc[0].fillna("")
    header2 = df_raw.iloc[1].fillna("")
    header3 = df_raw.iloc[2].fillna("")

    new_cols = []
    for a, b, c in zip(header1, header2, header3):
        combined = f"{a}_{b}_{c}".strip("_")
        combined = re.sub(r"_+", "_", combined).lower()
        new_cols.append(combined)

    df = df_raw.iloc[3:].reset_index(drop=True)
    df.columns = [
        re.sub(r"^_+|_+$", "", c.replace("unnamed", "").lower())
        for c in new_cols
    ]

    track_cols = [c for c in df.columns if c.startswith("track_") or c == "track_id"]
    df_track = df[track_cols].copy()

    def clean_value(v):
        if pd.isna(v):
            return None
        if isinstance(v, str) and v.startswith("[") and v.endswith("]"):
            return ",".join(x.strip().strip("'").strip('"') for x in v[1:-1].split(","))
        return v.strip() if isinstance(v, str) else v

    df_track = df_track.applymap(clean_value)
    df_track = df_track[df_track["track_id"].notna()]
    df_track["track_id"] = df_track["track_id"].astype(int)

    df_track.to_csv(CSV_OUTPUT, index=False, encoding="utf-8")


# ============================================================
# 4) CLEAN QUESTIONNAIRE
# ============================================================

def normalize_accents(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')

def clean_questionnaire():
    in_path = file("Questionnaire.csv")
    out_path = file("questionnaire_cleaned.csv")

    if not os.path.exists(in_path):
        raise FileNotFoundError(f"Fichier introuvable : {in_path}")

    x = pd.read_csv(in_path)

    # Suppressions colonnes inutiles
    x = x.drop(x.columns[:2], axis=1)
    x = x.drop(x.columns[14], axis=1)
    x = x.drop(x.columns[-1], axis=1)

    new_names = [
        "use_platforms", "platforms", "daily_time", "styles", "devices",
        "listening_moments", "listening_frequency", "listening_slots",
        "preferred_languages", "follows_latest_releases",
        "discovers_artists_regularly", "discovers_styles_regularly",
        "preferred_duration", "preferred_lyrics", "age_group",
        "gender", "professional_status", "professional_sector"
    ]
    x.columns = new_names

    x.fillna("no_answer", inplace=True)

    for col in x:
        x[col] = x[col].astype(str).str.strip().str.lower()
        x[col] = x[col].apply(normalize_accents)

    # (Ici tu remets tes règles custom si tu en as)

    if os.path.exists(out_path):
        os.remove(out_path)
    x.to_csv(out_path, index=False)


# ============================================================
# 5) CLEAN RAW_ECHONEST
# ============================================================

def clean_echonest():
    raw_path = file("raw_echonest.csv")
    raw = pd.read_csv(raw_path, header=None, low_memory=False)

    track_id_row = None
    for i in range(10):
        if raw.iloc[i].astype(str).str.contains("track_id", case=False, na=False).any():
            track_id_row = i
            break

    if track_id_row is None:
        raise ValueError("track_id introuvable")

    header_rows = raw.iloc[:track_id_row+1].fillna("").astype(str)

    def make_colname(col_idx):
        parts = [header_rows.iat[r, col_idx].strip() for r in range(header_rows.shape[0])]
        parts = [p for p in parts if p and p.lower() != "nan"]
        return "_".join(parts).replace("__", "_").strip("_")

    colnames = [make_colname(c) for c in range(raw.shape[1])]

    data = raw.iloc[track_id_row+1:].copy().reset_index(drop=True)
    data.columns = colnames
    data.to_csv(file("clean_echonest.csv"), index=False)

def clean_echonest_vectors():
    input_path = file("echonest.csv")
    output_path = file("echonest_vectors_cleaned.csv")

    if not os.path.exists(input_path):
        print(f"⚠️ Fichier introuvable : {input_path}")
        return

    print("Traitement des vecteurs Echonest (Patience...)...")

    # Lecture header complexe (lignes 0, 1, 2)
    # index_col=0 car la première colonne est track_id
    try:
        df = pd.read_csv(input_path, index_col=0, header=[0, 1, 2], low_memory=False)
    except Exception as e:
        print(f"Erreur lecture echonest.csv : {e}")
        return

    # On ne garde que les musiques qui ont des features audio valides
    audio_cols = ['acousticness', 'danceability', 'energy', 'instrumentalness', 
                  'liveness', 'speechiness', 'tempo', 'valence']
    
    # On cible la section ('echonest', 'audio_features')
    df_clean = df['echonest']['audio_features'][audio_cols].copy()
    
    # On supprime les lignes vides
    df_clean.dropna(inplace=True)

    # Récupération des données vectorielles (temporal_features : colonnes 0 à 223)
    # On utilise .loc pour s'assurer qu'on prend les mêmes IDs que ceux filtrés ci-dessus
    temporal_df = df['echonest']['temporal_features'].loc[df_clean.index]

    # Fusion des 224 colonnes en une seule string formatée pour pgvector
    # Format attendu : "[0.123,0.456,0.789...]"
    df_clean['audio_vector_str'] = temporal_df.apply(
        lambda row: "[" + ",".join(row.astype(float).astype(str)) + "]", axis=1
    )

    # Remise en forme finale
    df_clean.reset_index(inplace=True) # track_id redevient une colonne
    
    # Renommage explicite de la colonne index si nécessaire
    if 'index' in df_clean.columns:
        df_clean.rename(columns={'index': 'track_id'}, inplace=True)
    elif df_clean.index.name == 'track_id':
            pass 

    # Sauvegarde
    df_clean.to_csv(output_path, index=False, encoding="utf-8")
    print(f"✅ {output_path} généré ({len(df_clean)} vecteurs).")



# ============================================================
# MAIN
# ============================================================

def main():
    print("\n=== CLEAN RAW ALBUMS ===")
    clean_raw_albums()

    print("\n=== CLEAN GENRES ===")
    clean_genres()

    print("\n=== CLEAN TRACKS ===")
    clean_tracks()

    print("\n=== CLEAN QUESTIONNAIRE ===")
    clean_questionnaire()

    print("\n=== CLEAN ECHONEST ===")
    clean_echonest()

    print("\n=== CLEAN ECHONEST VECTORS ===")
    clean_echonest_vectors()

    print("\n✅ Tous les CSV ont été nettoyés avec succès !")


if __name__ == "__main__":
    main()
